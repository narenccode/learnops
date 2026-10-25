#!/usr/bin/env python3
"""Full pull-request review on the guide's behalf.

Flow (one run per pull_request / pull_request_review event):
  1. Rule checks (pr_rules.py). Any problem here ends the run: no AI tokens are spent.
  2. If the rules pass, wait for ONE approval from a path owner other than the author
     (label `awaiting-peer`, commit status `guide-bot` = pending).
  3. After that approval, an AI review of the diff runs (DeepSeek, OpenAI-compatible API).
  4. Verdict -> one comment, one label and the commit status `guide-bot`:
     success = ready to merge (the author squash-merges); failure/pending = not yet.

The bot never approves, merges or closes anything. The model has no tools and PR code is never run.
The model only reports findings; this script decides the verdict.

Local use (no posting, no network unless --approvers is given and DEEPSEEK_* are set):
    python .github/scripts/pr_review.py --event event.json --base origin/main --head HEAD --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pr_rules as rules_mod
from pr_rules import Finding, git, gh

STATUS_CONTEXT = "guide-bot"
MAX_AI_RUNS = 8  # per pull request: the cost cap
DIFF_LIMIT = 60_000  # characters sent to the model
ITEM_LIMIT = 10
TEXT_LIMIT = 300
AI_RUNS = re.compile(r"<!-- ai-runs:(\d+) -->")
CHAPTER = {"studio": "C1", "checker": "C2", "grading": "C3", "video": "C4"}
RUBRIC = Path(__file__).resolve().parents[1] / "review" / "rubric.md"


class AIError(Exception):
    pass


# ------------------------------------------------------------------ reviews


def latest_reviews(lines: list[dict]) -> dict[str, str]:
    """Latest meaningful review state per user, in order (COMMENTED is ignored, DISMISSED resets)."""
    state: dict[str, str] = {}
    for item in lines:
        user = (item.get("user") or "").lower()
        review = item.get("state", "")
        if not user or review in ("COMMENTED", "PENDING"):
            continue
        if review == "DISMISSED":
            state.pop(user, None)
        else:
            state[user] = review
    return state


def reviewers(
    state: dict[str, str], ctx: rules_mod.Context
) -> tuple[set[str], set[str]]:
    """(approvers, requesters) among owners of the changed paths, never the author.

    Like GitHub's code-owner rule, every changed path needs an approval from one of its owners;
    until that holds, `approvers` is empty.
    """
    parsed = rules_mod.parse_codeowners(ctx.codeowners)
    author = ctx.author.lower()
    owners = {o for p in ctx.files for o in rules_mod.owners_of(parsed, p)}
    owners.discard(author)
    approved = {u for u, s in state.items() if s == "APPROVED"}
    covered = all(
        approved & (set(rules_mod.owners_of(parsed, p)) - {author}) for p in ctx.files
    )
    approvers = {u for u in approved if u in owners} if covered else set()
    requesters = {
        u for u, s in state.items() if s == "CHANGES_REQUESTED" and u in owners
    }
    return approvers, requesters


def fetch_reviews(repo: str, number: int) -> list[dict]:
    out = gh(
        "api",
        "--paginate",
        f"repos/{repo}/pulls/{number}/reviews",
        "--jq",
        ".[] | {user: .user.login, state: .state}",
    )
    return [json.loads(line) for line in out.splitlines() if line.strip()]


# --------------------------------------------------------------- AI prompt


def prd_section(prd: str, code: str) -> str:
    """The text of `## <code>. …` up to the next heading of level 1 or 2."""
    lines = prd.splitlines()
    for i, line in enumerate(lines):
        if re.match(rf"##\s+{re.escape(code)}[.\s]", line):
            end = next(
                (
                    j
                    for j in range(i + 1, len(lines))
                    if re.match(r"#{1,2}\s", lines[j])
                ),
                len(lines),
            )
            return "\n".join(lines[i:end])
    return ""


def prd_excerpt(prd: str, paths: list[str]) -> str:
    codes = ["A7", "A9"]
    modules = sorted({rules_mod.module_of(p) for p in paths if rules_mod.module_of(p)})
    design = [p for p in paths if p.startswith("docs/design/") and "TEMPLATE" not in p]
    modules += [Path(p).stem for p in design if Path(p).stem in CHAPTER]
    codes += [CHAPTER[m] for m in sorted(set(modules)) if m in CHAPTER]
    if any(p.startswith(("contracts/", "libs/contracts/")) for p in paths):
        codes.append("B.0")
    if design:
        codes.append("D1")
    return "\n\n".join(s for s in (prd_section(prd, c) for c in codes) if s)


def neutralise(text: str, limit: int = TEXT_LIMIT) -> str:
    """Make model/PR text safe to put in a comment: no pings, no HTML comments, no control chars."""
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", str(text))
    text = text.replace("<!--", "").replace("-->", "").replace("@", "@​")
    return text.strip()[:limit]


def build_prompt(
    ctx: rules_mod.Context, notes: str, diff: str, prd: str, template: str
) -> tuple[str, str]:
    rubric = RUBRIC.read_text(encoding="utf-8")
    untrusted = (
        f"Title: {ctx.title}\nAuthor: {ctx.author}\nDescription:\n{ctx.body}\n\n"
        f"Rule-check notes (already reported separately):\n{notes or 'none'}\n\nDiff:\n{diff}"
    ).replace("</untrusted_pr>", "")
    parts = ["PRD EXCERPTS (trusted):\n" + (prd or "(none available)")]
    if template:
        parts.append("DESIGN-DOCUMENT TEMPLATE (trusted):\n" + template)
    parts.append(
        f"<untrusted_pr>\n{untrusted}\n</untrusted_pr>\n\nReturn the JSON object only."
    )
    return rubric, "\n\n".join(parts)


def read_diff(base: str, head: str) -> tuple[str, bool]:
    exclude = [f":(exclude)**/{name}" for name in rules_mod.LOCKFILES]
    text = git(
        "diff",
        "-U3",
        "--no-color",
        "--no-renames",
        f"{base}...{head}",
        "--",
        ".",
        *exclude,
    )
    return text[:DIFF_LIMIT], len(text) > DIFF_LIMIT


# ---------------------------------------------------------------- model API


def ask_model(
    system: str, user: str, env: dict[str, str] | None = None
) -> tuple[dict, dict]:
    env = os.environ if env is None else env
    key, model = env.get("DEEPSEEK_API_KEY", ""), env.get("DEEPSEEK_MODEL", "")
    if not key:
        raise AIError("DEEPSEEK_API_KEY is not set")
    if not model:
        raise AIError("DEEPSEEK_MODEL is not set")
    url = (
        env.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
        + "/chat/completions"
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
        "max_tokens": 6000,
        "response_format": {"type": "json_object"},
    }
    last = "no attempt"
    for attempt, delay in enumerate((0, 3, 10)):
        time.sleep(delay)
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                data = json.load(response)
            choice = data["choices"][0]
            text = (choice.get("message") or {}).get("content") or ""
            usage = data.get("usage", {})
            reason = choice.get("finish_reason", "?")
            detail = (
                f"finish_reason={reason}, {usage.get('completion_tokens', '?')} output "
                f"tokens, {len(text)} characters"
            )
            if not text.strip():
                last = f"empty answer ({detail})"
                payload.pop("response_format", None)  # JSON mode can return nothing
                continue
            try:
                return parse_json(text), usage
            except ValueError:
                last = f"unreadable answer ({detail})"
                if reason == "length":
                    break  # cut off by the limit: asking again gives the same answer
                continue
        except urllib.error.HTTPError as error:
            last = f"HTTP {error.code}"
            if error.code == 400 and "response_format" in payload:
                del payload["response_format"]  # some models do not support JSON mode
            elif error.code not in (429, 500, 502, 503, 504):
                break
        except (
            urllib.error.URLError,
            TimeoutError,
            KeyError,
            IndexError,
            TypeError,
            AttributeError,
            ValueError,
        ) as error:
            last = type(error).__name__
    raise AIError(f"model call failed ({last})")


def parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object")
    value = json.loads(text[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("not an object")
    return value


def findings_from_ai(result: dict) -> list[Finding]:
    """Validate the model's answer; anything unexpected is dropped, never trusted."""
    out: list[Finding] = []

    def items(key: str) -> list[dict]:
        value = result.get(key, [])
        return (
            [i for i in value if isinstance(i, dict)][:ITEM_LIMIT]
            if isinstance(value, list)
            else []
        )

    for item in items("blocking"):
        where = (
            f"`{neutralise(item.get('file', ''), 120)}`: " if item.get("file") else ""
        )
        out.append(
            Finding(
                "rework",
                where + neutralise(item.get("issue", "")),
                neutralise(item.get("ref", ""), 80),
            )
        )
    for item in items("advice"):
        where = (
            f"`{neutralise(item.get('file', ''), 120)}`: " if item.get("file") else ""
        )
        out.append(Finding("advice", where + neutralise(item.get("issue", ""))))
    for item in items("judgement"):
        out.append(Finding("judgement", neutralise(item.get("issue", ""))))
    for item in items("unverified"):
        out.append(Finding("unverified", neutralise(item.get("issue", ""))))
    return [f for f in out if f.message.strip(" `:")]


# ----------------------------------------------------------------- decision


def decide(
    rule_findings: list[Finding],
    approvers: set[str],
    requesters: set[str],
    run_ai,
    ai_runs: int,
) -> tuple[str, str, str, list[Finding], bool]:
    """-> (label, commit-status state, status text, findings, ai_called). Pure: no network."""
    findings = list(rule_findings)
    label = rules_mod.verdict_of(findings)
    if requesters:
        findings.append(
            Finding(
                "rework", "A peer requested changes: " + ", ".join(sorted(requesters))
            )
        )
        label = rules_mod.verdict_of(findings)
    if label != "ready-to-merge":
        return label, "failure", VERDICT_TEXT[label], findings, False
    if not approvers:
        return (
            "awaiting-peer",
            "pending",
            VERDICT_TEXT["awaiting-peer"],
            findings,
            False,
        )
    if ai_runs >= MAX_AI_RUNS:
        findings.append(
            Finding(
                "judgement",
                f"AI review limit ({MAX_AI_RUNS} runs) reached for this PR; the guide decides.",
            )
        )
        return (
            "needs-judgement",
            "failure",
            VERDICT_TEXT["needs-judgement"],
            findings,
            False,
        )
    try:
        findings += run_ai()
    except (
        Exception
    ) as error:  # any failure of the AI step must reach the guide, not crash the run
        findings.append(
            Finding(
                "judgement",
                f"AI review unavailable ({neutralise(error, 220)}); the guide decides.",
            )
        )
        return (
            "needs-judgement",
            "failure",
            VERDICT_TEXT["needs-judgement"],
            findings,
            False,
        )
    label = rules_mod.verdict_of(findings)
    state = "success" if label == "ready-to-merge" else "failure"
    return label, state, VERDICT_TEXT[label], findings, True


VERDICT_TEXT = {
    "rule-violation": "Rule violation: the guide decides",
    "needs-rework": "Needs rework: see the bot comment",
    "needs-judgement": "Needs the guide's judgement",
    "awaiting-peer": "Waiting for one peer approval",
    "ready-to-merge": "Peer approved, bot review passed: may merge",
}


def event_from_pr(repo: str, number: int) -> dict:
    """Build the same event shape from the API, for a manual re-run (after an outage, say)."""
    pr = json.loads(gh("api", f"repos/{repo}/pulls/{number}"))
    return {"pull_request": pr, "repository": {"full_name": repo}}


def notification(
    label: str, author: str, peer: str, guide: str, others: tuple[str, ...] = ()
) -> str:
    """The short comment that actually notifies people when the verdict changes."""
    title = rules_mod.VERDICTS[label][0]
    text = (
        f"@{author} the review status is now **{title}**. {rules_mod.next_step(label)}"
    )
    if label == "awaiting-peer" and peer:
        text = f"@{author} the rule checks passed. @{peer}, please review this pull request."
        if others:
            names = ", ".join("@​" + o for o in others)
            text += f" If you are busy, any one of {names} can approve instead."
        text += " The AI review runs right after one approval."
    if label in ("rule-violation", "needs-judgement") and guide:
        text += f" @{guide}: your decision is needed."
    return text + " Details are in the bot comment above."


def set_status(repo: str, sha: str, state: str, text: str, url: str) -> None:
    gh(
        "api", f"repos/{repo}/statuses/{sha}",
        "-f", f"state={state}", "-f", f"context={STATUS_CONTEXT}",
        "-f", f"description={text[:140]}", "-f", f"target_url={url}",
    )  # fmt: skip


# --------------------------------------------------------------------- main


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--event", help="GitHub event JSON (pull_request)")
    parser.add_argument(
        "--pr", type=int, help="re-run the review for this PR number (manual run)"
    )
    parser.add_argument("--base")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument(
        "--dry-run", action="store_true", help="print only; post nothing"
    )
    parser.add_argument(
        "--approvers", help="dry-run only: pretend these users approved"
    )
    args = parser.parse_args()

    if args.pr:
        repo_name = os.environ.get("GITHUB_REPOSITORY", "")
        event = event_from_pr(repo_name, args.pr)
    elif args.event:
        with open(args.event, encoding="utf-8") as handle:
            event = json.load(handle)
    else:
        parser.error("give --event or --pr")
    pr = event["pull_request"]
    repo, number, sha = (
        event["repository"]["full_name"],
        pr["number"],
        pr["head"]["sha"],
    )
    base = args.base or f"origin/{pr['base']['ref']}"
    page = f"https://github.com/{repo}/pull/{number}"
    if pr.get("draft"):
        print("Draft: skipped.")
        return 0
    try:
        ctx = rules_mod.collect(event, base, args.head)
        guide = rules_mod.guide_of(rules_mod.parse_codeowners(ctx.codeowners))
        if ctx.author.lower() == guide:
            if not args.dry_run:
                set_status(repo, sha, "success", "Guide's own pull request", page)
            print("Guide's own PR: status success, no comment.")
            return 0
        if args.approvers is not None:
            state = {
                u.strip().lower(): "APPROVED"
                for u in args.approvers.split(",")
                if u.strip()
            }
        elif args.dry_run:
            state = {}
        else:
            state = latest_reviews(fetch_reviews(repo, number))
        approvers, requesters = reviewers(state, ctx)
        rule_findings = rules_mod.evaluate(ctx)
        _, old_body = (
            ("", "") if args.dry_run else rules_mod.find_bot_comment(repo, number)
        )
        found = AI_RUNS.search(old_body)
        runs = int(found.group(1)) if found else 0
        usage: dict = {}
        attempted = (
            False  # a failed call still costs money, so it counts toward the cap
        )
        model = os.environ.get("DEEPSEEK_MODEL", "?")

        def run_ai() -> list[Finding]:
            nonlocal usage, attempted
            attempted = True
            diff, cut = read_diff(base, args.head)
            prd = git("show", f"{base}:docs/PRD.md", check=False)
            design = any(p.startswith("docs/design/") for p in ctx.files)
            template = (
                git("show", f"{base}:docs/design/TEMPLATE.md", check=False)
                if design
                else ""
            )
            notes = "\n".join(f"- {f.message}" for f in rule_findings)
            system, user = build_prompt(
                ctx, notes, diff, prd_excerpt(prd, sorted(ctx.files)), template
            )
            result, usage = ask_model(system, user)
            found_items = findings_from_ai(result)
            if cut:
                found_items.append(
                    Finding(
                        "unverified",
                        f"The AI saw only the first {DIFF_LIMIT} characters of the diff.",
                    )
                )
            return found_items

        label, state_name, text, findings, ai_called = decide(
            rule_findings, approvers, requesters, run_ai, runs
        )
        footer = (
            f"AI review: {model}, {usage.get('prompt_tokens', '?')} in / {usage.get('completion_tokens', '?')} out tokens. "
            "It reports findings only; a person stays responsible."
            if ai_called
            else "The AI review did not run (see above). Peer review is always required."
            if approvers
            else "No AI review yet: it runs after one peer approval. Peer review is always required."
        )
        parsed_rules = rules_mod.parse_codeowners(ctx.codeowners)
        peer = rules_mod.peer_of(parsed_rules, ctx.author)
        eligible = rules_mod.eligible_reviewers(
            parsed_rules, sorted(ctx.files), ctx.author, guide
        )
        others = tuple(o for o in eligible if o != peer)
        previous = rules_mod.VERDICT_MARK.search(old_body)
        intro = ""
        if approvers:
            intro = (
                "Peer approval from "
                + ", ".join(f"@​{u}" for u in sorted(approvers))
                + "."
            )
        body = rules_mod.render(
            label,
            findings,
            sha,
            intro=intro,
            footer=footer,
            step=rules_mod.next_step(label, peer, others),
            help_url=f"https://github.com/{repo}/blob/main/docs/REVIEW-PROCESS.md",
        )
        if attempted or found:
            body += f"\n<!-- ai-runs:{runs + (1 if attempted else 0)} -->"
    except (
        Exception
    ) as error:  # a checker bug must not block merging forever: the guide can bypass
        print(f"::warning::pr_review failed: {error}")
        if not args.dry_run:
            try:  # say so on the PR: a silent failure would leave the students stuck and confused
                who = rules_mod.guide_of(
                    rules_mod.parse_codeowners(
                        git("show", f"{base}:.github/CODEOWNERS", check=False)
                    )
                )
                apology = (
                    f"{rules_mod.MARKER}\n### Automated review: **Needs your judgement**\n\n"
                    "**Next step:** Do not wait on the bot. It hit an internal error, and the guide has "
                    "been told. Keep working; the guide will reply or approve this pull request by hand.\n\n"
                    f"<!-- verdict:needs-judgement -->"
                )
                rules_mod.post(repo, number, "needs-judgement", apology)
                if who:
                    gh(
                        "api",
                        f"repos/{repo}/issues/{number}/comments",
                        "-f",
                        f"body=@{who} the review bot failed on this pull request ({type(error).__name__}). "
                        "Your decision is needed.",
                    )
            except Exception as inner:
                print(f"::warning::could not explain the failure on the PR: {inner}")
            try:
                set_status(repo, sha, "failure", "Bot error: the guide decides", page)
            except Exception as inner:
                print(f"::warning::status failed too: {inner}")
        return 0
    print(body)
    print(f"\nlabel: {label}   status: {state_name} ({text})")
    if not args.dry_run:
        try:
            rules_mod.post(repo, number, label, body)
        except Exception as error:
            print(f"::warning::could not post comment/label: {error}")
        try:
            set_status(repo, sha, state_name, text, page)
        except Exception as error:
            print(f"::warning::could not set status: {error}")
        if not previous or previous.group(1) != label:
            try:  # edits to the main comment send no email, so a changed verdict gets its own short ping
                gh(
                    "api",
                    f"repos/{repo}/issues/{number}/comments",
                    "-f",
                    f"body={notification(label, ctx.author, peer, guide, others)}",
                )
            except Exception as error:
                print(f"::warning::could not notify: {error}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

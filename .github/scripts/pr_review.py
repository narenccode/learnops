#!/usr/bin/env python3
"""Advice on a pull request: rule checks and an AI read, posted as one comment.

Flow (one run per pull_request event or manual run):
  1. Rule checks (pr_rules.py).
  2. An AI read of the diff (DeepSeek, OpenAI-compatible API), at most MAX_AI_RUNS times per pull request.
     If the AI is unavailable, the comment says so; nothing waits for it.
  3. One comment, updated in place, with the findings and the next step.

The bot sets no label and no commit status, pings nobody and never blocks a merge. CI (`checks`) and one
approval are the gate. The bot never approves, merges or closes anything. The model has no tools and PR
code is never run.

Local use (prints only, posts nothing; the AI step runs only if DEEPSEEK_* are set):
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

MAX_AI_RUNS = 5  # per pull request: the cost cap
DIFF_LIMIT = 60_000  # characters sent to the model
ITEM_LIMIT = 10
TEXT_LIMIT = 300
AI_RUNS = re.compile(r"<!-- ai-runs:(\d+) -->")
CHAPTER = {"studio": "C1", "checker": "C2", "grading": "C3", "video": "C4"}
RUBRIC = Path(__file__).resolve().parents[1] / "review" / "rubric.md"


class AIError(Exception):
    pass


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
    ctx: rules_mod.Context,
    notes: str,
    diff: str,
    prd: str,
    template: str,
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
    # DeepSeek's flash model "thinks" by default and the hidden reasoning eats max_tokens, which cut
    # real answers off (seen on PR 6). Switch it off; DEEPSEEK_EXTRA_BODY overrides or empties this.
    extra = json.loads(
        env.get("DEEPSEEK_EXTRA_BODY", '{"thinking": {"type": "disabled"}}') or "{}"
    )
    payload.update(extra)
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
            if error.code == 400 and (
                extra.keys() & payload.keys() or "response_format" in payload
            ):
                # an option the provider rejects: drop the extras first, then JSON mode, then ask plainly
                for name in list(extra) or ["response_format"]:
                    payload.pop(name, None)
                extra = {}
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


def event_from_pr(repo: str, number: int) -> dict:
    """Build the same event shape from the API, for a manual re-run (after an outage, say)."""
    pr = json.loads(gh("api", f"repos/{repo}/pulls/{number}"))
    return {"pull_request": pr, "repository": {"full_name": repo}}


def advise(
    rule_findings: list[Finding], run_ai, ai_runs: int
) -> tuple[list[Finding], bool]:
    """-> (findings to show, ai_called). Pure: no network. Nothing returned here can block a merge."""
    findings = list(rule_findings)
    if ai_runs >= MAX_AI_RUNS:
        findings.append(
            Finding(
                "unverified",
                f"AI advice limit ({MAX_AI_RUNS} runs) reached for this pull request; "
                "the rule checks still run.",
            )
        )
        return findings, False
    try:
        result = run_ai()
    except Exception as error:  # an AI failure is advice, never a block
        findings.append(
            Finding(
                "unverified",
                f"AI advice is unavailable right now ({neutralise(error, 220)}). "
                "It runs again on your next push.",
            )
        )
        return findings, False
    findings += result[0] if isinstance(result, tuple) else result
    return findings, True


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
    if pr.get("draft"):
        print("Draft: skipped.")
        return 0
    try:
        ctx = rules_mod.collect(event, base, args.head)
        guide = rules_mod.guide_of(rules_mod.parse_codeowners(ctx.codeowners))
        if ctx.author.lower() == guide:
            print("Guide's own pull request: no advice comment.")
            return 0
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
                ctx,
                notes,
                diff,
                prd_excerpt(prd, sorted(ctx.files)),
                template,
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

        parsed_rules = rules_mod.parse_codeowners(ctx.codeowners)
        findings, ai_called = advise(rule_findings, run_ai, runs)
        footer = (
            f"AI advice: {model}, {usage.get('prompt_tokens', '?')} in / "
            f"{usage.get('completion_tokens', '?')} out tokens. "
            "The AI can be wrong; your reviewer decides."
            if ai_called
            else "Rule checks only this time."
        )
        peer = rules_mod.peer_of(parsed_rules, ctx.author)
        eligible = rules_mod.eligible_reviewers(
            parsed_rules, sorted(ctx.files), ctx.author, guide
        )
        others = tuple(o for o in eligible if o != peer)
        body = rules_mod.render(
            findings,
            sha,
            step=rules_mod.next_step(peer, others),
            footer=footer,
            help_url=f"https://github.com/{repo}/blob/main/docs/REVIEW-PROCESS.md",
        )
        if attempted or found:
            body += f"\n<!-- ai-runs:{runs + (1 if attempted else 0)} -->"
    except (
        Exception
    ) as error:  # a bot bug must never leave the students without an answer
        print(f"::warning::pr_review failed: {error}")
        if not args.dry_run:
            try:  # say so on the PR: a silent failure would leave the students stuck and confused
                rules_mod.post(
                    repo,
                    number,
                    f"{rules_mod.MARKER}\n### Automated advice\n\n"
                    "The advice bot hit an internal error on this pull request. "
                    "Nothing is blocked: ask your reviewer to review as usual.",
                )
            except Exception as inner:
                print(f"::warning::could not explain the failure on the PR: {inner}")
        return 0
    print(body)
    if not args.dry_run:
        try:
            rules_mod.post(repo, number, body)
        except Exception as error:
            print(f"::warning::could not post the comment: {error}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

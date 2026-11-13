#!/usr/bin/env python3
"""Guide inbox: one issue that is always ready when the guide chooses to look.

No AI and no tokens. It reads pull requests from the GitHub CLI and rewrites ONE open issue in place
(created once and assigned to the guide; later edits send no email). Sections, in this order: what
needs the guide's decision, what only waits for the guide's merge, questions addressed to the guide,
what waits on students, and what merged recently.

    python .github/scripts/inbox.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone

import digest as digest_mod
import pr_rules as rules_mod
from pr_rules import gh

TITLE = "Guide inbox"
DECISION_LABELS = ("rule-violation", "needs-judgement")
# `awaiting-owners` is not a decision label, but the inbox still tracks it: when the owners have approved and
# the checks are green it moves to the merge list (the guide merges last).
TRACKED_LABELS = (*DECISION_LABELS, "awaiting-owners")
WAITING_LABELS = ("awaiting-peer", "needs-rework", "awaiting-ai")
IST = timezone(timedelta(hours=5, minutes=30))
REASON = re.compile(
    r"\*\*(?:Rule violations[^*]*|Needs the guide's judgement|Waiting for the owners' reviews)\*\*\s*\n((?:- .*(?:\n|$))+)"
)
MAX_REASONS = 2
# The bot raises this line on EVERY contract change. It is the standing process rule (all affected owners
# review, then the guide), not a question for the guide. Any other reason, or a missing reason, is a
# real decision: when in doubt the PR is shown to the guide.
STANDING = re.compile(r"^Contract change: every affected owner", re.IGNORECASE)


def labels(pr: dict) -> set[str]:
    return digest_mod.labels(pr)


def latest_states(reviews: list[dict]) -> dict[str, str]:
    """Each reviewer's newest review state (GitHub lists them oldest first)."""
    state: dict[str, str] = {}
    for item in reviews:
        who = str(item.get("author", {}).get("login", "")).lower()
        if who and item.get("state") in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            state[who] = item["state"]
    return state


def checks_green(pr: dict, ignore: str = "guide-bot") -> bool:
    """Every check except the bot's own status has finished without failing."""
    for item in pr.get("statusCheckRollup") or []:
        if (item.get("name") or item.get("context")) == ignore:
            continue
        result = (item.get("conclusion") or item.get("state") or "").upper()
        if result not in ("SUCCESS", "SKIPPED", "NEUTRAL"):
            return False
    return True


def owners_for(pr: dict, rules: list, guide: str) -> list[str]:
    """Everyone who owns a changed path, except the author and the guide."""
    author = pr.get("author", {}).get("login", "").lower()
    found = {
        o.lstrip("@").lower()
        for f in pr.get("files") or []
        for o in rules_mod.owners_of(rules, f["path"])
    }
    return sorted(found - {author, guide})


def all_reasons(comment: str) -> list[str]:
    """Every bullet point under the bot's guide-facing headings, citation removed."""
    out: list[str] = []
    for block in REASON.findall(comment or ""):
        out += [ln[2:].strip() for ln in block.splitlines() if ln.startswith("- ")]
    return [re.sub(r"\s*_\([^)]*\)_$", "", x)[:220] for x in out]


def reasons_from(comment: str) -> list[str]:
    """The reasons that are a real question for the guide (the standing contract rule is left out)."""
    return [x for x in all_reasons(comment) if not STANDING.match(x)][:MAX_REASONS]


def classify(pr: dict, bot_text: str, guide: str) -> tuple[str, list[str]]:
    """Whose turn is it? -> ("decision" | "merge" | "waiting", approvers or the reason it waits).

    A PR carrying a guide label is the guide's turn only when there is a real question for him, or
    when the standing contract rule is satisfied: a reviewer approved and the checks are green.
    Otherwise it waits on the reviewers or the author.
    """
    reasons = all_reasons(bot_text)
    states = latest_states(pr.get("reviews") or [])
    approved = sorted(u for u, s in states.items() if s == "APPROVED" and u != guide)
    requested = sorted(
        u for u, s in states.items() if s == "CHANGES_REQUESTED" and u != guide
    )
    real_question = (
        "rule-violation" in labels(pr)
        or not reasons
        or any(not STANDING.match(x) for x in reasons)
    )
    if real_question:
        return "decision", approved
    if requested:
        return "waiting", [f"changes requested by {', '.join(requested)}"]
    if pr.get("mergeable") == "CONFLICTING":
        return "waiting", ["merge conflicts: the author must update the branch"]
    if not checks_green(pr):
        return "waiting", ["checks are failing or still running"]
    if not approved:
        return "waiting", ["no reviewer has approved yet"]
    return "merge", approved


def mentions_guide(text: str, guide: str) -> bool:
    return re.search(rf"@{re.escape(guide)}\b", text or "", re.IGNORECASE) is not None


def waiting_questions(
    pr: dict, comments: list[dict], guide: str
) -> list[tuple[str, str]]:
    """(who, date) of the mentions of the guide that he has not answered since."""
    answered = max(
        [c["createdAt"] for c in comments if c["user"].lower() == guide], default=""
    )
    author = pr.get("author", {}).get("login", "")
    items = [(author, pr.get("createdAt", ""), pr.get("body", ""))] + [
        (c["user"], c["createdAt"], c["body"]) for c in comments
    ]
    return [
        (who, when[:10])
        for who, when, text in items
        if who.lower() not in (guide, rules_mod.BOT.lower(), "github-actions")
        and mentions_guide(text, guide)
        and when > answered
    ]


def link(pr: dict) -> str:
    who = pr.get("author", {}).get("login", "?")
    return f"[#{pr['number']}]({pr['url']}) {pr['title']} (@​{who})"


def build(
    open_prs: list[dict],
    merged: list[dict],
    comments: dict[int, list[dict]],
    bot_text: dict[int, str],
    now: datetime,
    guide: str,
    rules: list,
    issues: list[dict] | None = None,
    issue_comments: dict[int, list[dict]] | None = None,
) -> str:
    ready = [p for p in open_prs if not p.get("isDraft")]
    decide = [p for p in ready if labels(p) & set(TRACKED_LABELS)]
    mergeable, undecided, held = [], [], []
    for p in decide:
        where, detail = classify(p, bot_text.get(p["number"], ""), guide)
        if where == "merge":
            mergeable.append((p, detail))
        elif where == "decision":
            undecided.append(p)
        else:
            held.append((p, detail))

    questions = []
    for p in ready:
        for who, when in waiting_questions(p, comments.get(p["number"], []), guide):
            questions.append(f"- {link(p)}: @​{who} asked you on {when}")
    for issue in issues or []:
        for who, when in waiting_questions(
            issue, (issue_comments or {}).get(issue["number"], []), guide
        ):
            questions.append(f"- Issue {link(issue)}: @​{who} asked you on {when}")

    out = [f"## {TITLE}", ""]
    if not (undecided or mergeable or questions):
        out += ["**Nothing needs you right now.**", ""]

    out.append("### 1. Needs your decision")
    for p in undecided:
        why = reasons_from(bot_text.get(p["number"], ""))
        what = (
            f" `{sorted(labels(p) & set(TRACKED_LABELS))[0]}`"
            + (f". {' '.join(why)}" if why else ". See the bot comment on the PR.")
            + ("" if checks_green(p) else " Checks are not green yet.")
        )
        out.append(f"- {link(p)}{what}")
    if not undecided:
        out.append("Nothing.")

    out += [
        "",
        "### 2. Approved by a reviewer, checks green (merge once the owners named have reviewed)",
    ]
    for p, approved in mergeable:
        owners = owners_for(p, rules, guide)
        missing = [o for o in owners if o not in approved]
        note = f" Not yet reviewed by: {', '.join(missing)}." if missing else ""
        out.append(
            f"- {link(p)}: approved by {', '.join(approved)}.{note} "
            "Then merge with the bypass box, or tell Claude `merge it`."
        )
    if not mergeable:
        out.append("Nothing.")

    out += ["", "### 3. Questions waiting for you", *(questions or ["Nothing."])]

    waiting = []
    for p, why in held:
        approved = latest_states(p.get("reviews") or [])
        todo = [o for o in owners_for(p, rules, guide) if approved.get(o) != "APPROVED"]
        who = f" Reviewers still to approve: {', '.join(todo)}." if todo else ""
        waiting.append(f"- {link(p)} contract change: {why[0]}.{who}")
    for p in ready:
        hit = sorted(labels(p) & set(WAITING_LABELS))
        if hit and p not in decide:
            days = digest_mod.age_days(p["updatedAt"], now)
            waiting.append(f"- {link(p)} `{hit[0]}` for {days} day(s)")
    out += [
        "",
        "### 4. Waiting on students (nothing to do)",
        *(waiting or ["Nothing."]),
    ]

    others = [
        p for p in merged if p.get("author", {}).get("login", "").lower() != guide
    ]
    out += ["", f"### 5. Merged in the last 3 days ({len(others)})"]
    for p in others:
        flag = (
            ""
            if "ready-to-merge" in labels(p)
            else " **merged without a green bot verdict: look at this one**"
        )
        if p.get("risk") == "high":
            flag += " `high risk`"
        out.append(f"- {link(p)}{flag}")
    if not others:
        out.append("Nothing merged.")

    drafts = sum(1 for p in open_prs if p.get("isDraft"))
    out += [
        "",
        f"Open: {len(ready)} ready, {drafts} draft. Updated {now.astimezone(IST):%Y-%m-%d %H:%M} IST.",
    ]
    return "\n".join(out)


def fetch_open(repo: str) -> list[dict]:
    fields = (
        "number,title,author,labels,url,isDraft,updatedAt,createdAt,body,"
        "reviews,files,statusCheckRollup,mergeable"
    )
    return json.loads(
        gh(
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "open",
            "--limit",
            "100",
            "--json",
            fields,
        )  # fmt: skip
    )


def fetch_issues(repo: str) -> list[dict]:
    """Open issues written by people (not the bot's own: the inbox and the weekly digest)."""
    fields = "number,title,author,url,createdAt,body"
    out = json.loads(
        gh(
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            "open",
            "--limit",
            "100",
            "--json",
            fields,
        )
    )
    return [
        i
        for i in out
        if i["title"] != TITLE and "github-actions" not in i["author"]["login"]
    ]


def fetch_comments(repo: str, number: int) -> list[dict]:
    out = gh(
        "api",
        "--paginate",
        f"repos/{repo}/issues/{number}/comments?per_page=100",
        "--jq",
        ".[] | {user: .user.login, createdAt: .created_at, body: .body}",
    )
    return [json.loads(ln) for ln in out.splitlines() if ln.strip()]


def find_issue(repo: str) -> tuple[str, str]:
    """(number, body) of the open inbox issue, or ("", "")."""
    out = gh(
        "issue", "list", "--repo", repo, "--state", "open",
        "--search", f'"{TITLE}" in:title', "--json", "number,title,body",
    )  # fmt: skip
    for item in json.loads(out):
        if item["title"] == TITLE:
            return str(item["number"]), item["body"]
    return "", ""


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--repo", default="")
    parser.add_argument("--post", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    repo = (
        args.repo
        or gh(
            "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"
        ).strip()
    )
    rules = rules_mod.parse_codeowners(
        rules_mod.git("show", "HEAD:.github/CODEOWNERS", check=False)
    )
    guide = rules_mod.guide_of(rules)
    open_prs = fetch_open(repo)
    _, merged = digest_mod.fetch(repo, now - timedelta(days=3))
    comments = {
        p["number"]: fetch_comments(repo, p["number"])
        for p in open_prs
        if not p.get("isDraft")
    }
    bot_text = {
        number: next(
            (
                c["body"]
                for c in reversed(items)
                if c["user"] == rules_mod.BOT and "learnops-pr-review" in c["body"]
            ),
            "",
        )
        for number, items in comments.items()
    }
    issues = fetch_issues(repo)
    issue_comments = {i["number"]: fetch_comments(repo, i["number"]) for i in issues}
    body = build(
        open_prs, merged, comments, bot_text, now, guide, rules, issues, issue_comments
    )
    print(body)
    if args.post and not args.dry_run:
        number, old = find_issue(repo)
        # the timestamp line changes every run; compare the rest so an idle inbox is not rewritten
        strip = lambda text: re.sub(r"Updated .* IST\.", "", text)  # noqa: E731
        if not number:
            gh(
                "issue", "create", "--repo", repo, "--title", TITLE,
                "--body", body, "--assignee", guide,
            )  # fmt: skip
        elif strip(old) != strip(body):
            gh("issue", "edit", number, "--repo", repo, "--body", body)
    return 0


if __name__ == "__main__":
    sys.exit(main())

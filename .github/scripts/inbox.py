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
WAITING_LABELS = ("awaiting-peer", "needs-rework", "awaiting-ai")
IST = timezone(timedelta(hours=5, minutes=30))
REASON = re.compile(
    r"\*\*(?:Rule violations[^*]*|Needs the guide's judgement)\*\*\s*\n((?:- .*(?:\n|$))+)"
)
MAX_REASONS = 2


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


def reasons_from(comment: str) -> list[str]:
    """The bullet points under the bot's guide-facing headings."""
    out: list[str] = []
    for block in REASON.findall(comment or ""):
        out += [ln[2:].strip() for ln in block.splitlines() if ln.startswith("- ")]
    return [re.sub(r"\s*_\([^)]*\)_$", "", x)[:220] for x in out][:MAX_REASONS]


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
) -> str:
    ready = [p for p in open_prs if not p.get("isDraft")]
    decide = [p for p in ready if labels(p) & set(DECISION_LABELS)]
    mergeable, undecided = [], []
    for p in decide:
        reviews = latest_states(p.get("reviews") or [])
        approved = sorted(
            u for u, s in reviews.items() if s == "APPROVED" and u != guide
        )
        if approved and checks_green(p):
            mergeable.append((p, approved))
        else:
            undecided.append(p)

    questions = []
    for p in ready:
        for who, when in waiting_questions(p, comments.get(p["number"], []), guide):
            questions.append(f"- {link(p)}: @​{who} asked you on {when}")

    out = [f"## {TITLE}", ""]
    if not (decide or questions):
        out += ["**Nothing needs you right now.**", ""]

    out.append("### 1. Needs your decision")
    for p in undecided:
        why = reasons_from(bot_text.get(p["number"], ""))
        what = (
            f" `{sorted(labels(p) & set(DECISION_LABELS))[0]}`"
            + (f". {' '.join(why)}" if why else "")
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
        "reviews,files,statusCheckRollup"
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
    body = build(open_prs, merged, comments, bot_text, now, guide, rules)
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

#!/usr/bin/env python3
"""Weekly digest for the guide: what needs a decision, what is stuck, what merged (for spot-checks).

No AI and no tokens: it only lists pull requests from the GitHub CLI. With --post it opens an issue
assigned to the guide (GitHub then sends the email) and closes last week's digest.

    python .github/scripts/digest.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone

import pr_rules as rules_mod
from pr_rules import gh

GUIDE_LABELS = ("rule-violation", "needs-judgement")
STUCK_DAYS = {"awaiting-peer": 2, "needs-rework": 4}
TITLE = "Weekly digest"


def labels(pr: dict) -> set[str]:
    return {item["name"] for item in pr.get("labels", [])}


def age_days(stamp: str, now: datetime) -> int:
    return (now - datetime.fromisoformat(stamp.replace("Z", "+00:00"))).days


def line(pr: dict, extra: str = "") -> str:
    who = pr.get("author", {}).get("login", "?")
    return f"- [#{pr['number']}]({pr['url']}) {pr['title']} (@​{who}){extra}"


def build(
    open_prs: list[dict], merged: list[dict], now: datetime, guide: str = ""
) -> str:
    ready = [p for p in open_prs if not p.get("isDraft")]
    # the guide's own PRs are not reviewed by the bot, so they are not part of the spot-check
    merged = [
        p for p in merged if p.get("author", {}).get("login", "").lower() != guide
    ]
    out = [f"## {TITLE}: week ending {now:%Y-%m-%d}", ""]

    need = [p for p in ready if labels(p) & set(GUIDE_LABELS)]
    out += [
        "### Needs your decision",
        *(line(p, f" `{sorted(labels(p) & set(GUIDE_LABELS))[0]}`") for p in need),
    ]
    if not need:
        out.append("Nothing.")

    stuck = []
    for label, days in STUCK_DAYS.items():
        for p in ready:
            if label in labels(p) and age_days(p["updatedAt"], now) >= days:
                stuck.append(
                    line(p, f" `{label}` for {age_days(p['updatedAt'], now)} days")
                )
    out += ["", "### Stuck (nudge the team)", *(stuck or ["Nothing."])]

    out += ["", f"### Merged in the last 7 days: spot-check {len(merged)} PR(s)"]
    for p in merged:
        flag = (
            ""
            if "ready-to-merge" in labels(p)
            else " **merged without a green bot verdict: look at this one**"
        )
        out.append(line(p, flag))
    if not merged:
        out.append("Nothing merged.")

    drafts = sum(1 for p in open_prs if p.get("isDraft"))
    out += ["", f"Open: {len(ready)} ready, {drafts} draft."]
    return "\n".join(out)


def fetch(repo: str, since: datetime) -> tuple[list[dict], list[dict]]:
    fields = "number,title,author,labels,url,isDraft,updatedAt,mergedAt"
    open_prs = json.loads(
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
        )
    )
    merged = json.loads(
        gh(
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "merged",
            "--limit",
            "100",
            "--search",
            f"merged:>={since:%Y-%m-%d}",
            "--json",
            fields,
        )
    )
    return open_prs, merged


def post(repo: str, guide: str, body: str, now: datetime) -> None:
    old = gh(
        "issue",
        "list",
        "--repo",
        repo,
        "--state",
        "open",
        "--search",
        f'"{TITLE}" in:title',
        "--json",
        "number",
        "--jq",
        ".[].number",
    )
    gh(
        "issue",
        "create",
        "--repo",
        repo,
        "--title",
        f"{TITLE} {now:%Y-%m-%d}",
        "--body",
        body,
        "--assignee",
        guide,
    )
    for number in old.split():
        gh("issue", "close", number, "--repo", repo, check=False)


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
    guide = rules_mod.guide_of(
        rules_mod.parse_codeowners(
            rules_mod.git("show", "HEAD:.github/CODEOWNERS", check=False)
        )
    )
    open_prs, merged = fetch(repo, now - timedelta(days=7))
    body = build(open_prs, merged, now, guide)
    print(body)
    if args.post and not args.dry_run:
        post(repo, guide, body, now)
    return 0


if __name__ == "__main__":
    sys.exit(main())

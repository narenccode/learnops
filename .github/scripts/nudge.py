#!/usr/bin/env python3
"""Daily nudge for stuck pull requests, so the guide never has to chase anyone.

No AI. For each open, non-draft PR whose bot label has not changed for a while, post one short
comment that @mentions the person who must act. At most one nudge per PR every 3 days.

    python .github/scripts/nudge.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone

import pr_rules as rules_mod
from pr_rules import gh

MARKER = "<!-- learnops-nudge -->"
WAIT_DAYS = {"awaiting-peer": 2, "needs-rework": 4, "ready-to-merge": 2}
REPEAT_DAYS = 3


def parse_time(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def message(label: str, author: str, peer: str, days: int) -> str:
    if label == "awaiting-peer":
        who = f"@{peer} " if peer else ""
        return (
            f"{who}a review from you has been waiting here for {days} days. "
            f"@{author} please remind them if something blocks it."
        )
    if label == "needs-rework":
        return (
            f"@{author} this pull request has waited {days} days for your fixes. "
            "Do what the bot comment says, or write here what blocks you."
        )
    return f"@{author} this pull request has been ready to merge for {days} days. Squash and merge it."


def plan(
    items: list[dict], rules: list[tuple[str, list[str]]], now: datetime
) -> list[tuple[int, str]]:
    """items: number, author, labels, label_since, last_nudge (ISO strings or ''). Pure: no network."""
    out = []
    for item in items:
        label = next((lab for lab in WAIT_DAYS if lab in item["labels"]), "")
        if not label or not item["label_since"]:
            continue
        days = (now - parse_time(item["label_since"])).days
        if days < WAIT_DAYS[label]:
            continue
        if item["last_nudge"] and now - parse_time(item["last_nudge"]) < timedelta(
            days=REPEAT_DAYS
        ):
            continue
        peer = rules_mod.peer_of(rules, item["author"])
        out.append(
            (item["number"], message(label, item["author"], peer, days) + "\n" + MARKER)
        )
    return out


def collect(repo: str) -> list[dict]:
    raw = gh(
        "pr",
        "list",
        "--repo",
        repo,
        "--state",
        "open",
        "--limit",
        "100",
        "--json",
        "number,author,labels,isDraft",
    )
    items = []
    for pr in json.loads(raw):
        if pr["isDraft"]:
            continue
        number = pr["number"]
        names = [label["name"] for label in pr["labels"]]
        current = next((lab for lab in WAIT_DAYS if lab in names), "")
        since = ""
        if current:
            events = gh(
                "api", "--paginate", f"repos/{repo}/issues/{number}/events", "--jq",
                f'.[] | select(.event == "labeled" and .label.name == "{current}") | .created_at',
            ).split()  # fmt: skip
            since = events[-1] if events else ""
        comments = gh(
            "api", "--paginate", f"repos/{repo}/issues/{number}/comments", "--jq",
            f'.[] | select(.user.login == "{rules_mod.BOT}" and (.body | contains("{MARKER}"))) | .created_at',
        ).split()  # fmt: skip
        items.append(
            {
                "number": number,
                "author": pr["author"]["login"].lower(),
                "labels": names,
                "label_since": since,
                "last_nudge": comments[-1] if comments else "",
            }
        )
    return items


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--repo", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    repo = (
        args.repo
        or gh(
            "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"
        ).strip()
    )
    codeowners = rules_mod.git("show", "HEAD:.github/CODEOWNERS", check=False)
    rules = rules_mod.parse_codeowners(codeowners)
    nudges = plan(collect(repo), rules, datetime.now(timezone.utc))
    for number, text in nudges:
        print(f"#{number}: {re.sub(MARKER, '', text).strip()}")
        if not args.dry_run:
            try:
                gh(
                    "api",
                    f"repos/{repo}/issues/{number}/comments",
                    "-f",
                    f"body={text}",
                )
            except Exception as error:  # one failed comment must not stop the others
                print(f"::warning::nudge for #{number} failed: {error}")
    if not nudges:
        print("Nothing is stuck.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

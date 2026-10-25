import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import nudge as n  # noqa: E402
import pr_rules as r  # noqa: E402

NOW = datetime(2026, 11, 10, 4, 0, tzinfo=timezone.utc)
RULES = r.parse_codeowners("/modules/studio/ @s1 @s2 @guide\n/CLAUDE.md @guide\n")


def item(label, since, author="s1", last=""):
    return {
        "number": 1,
        "author": author,
        "labels": [label],
        "label_since": since,
        "last_nudge": last,
    }


def test_waiting_peer_pings_peer_after_two_days():
    ((number, text),) = n.plan(
        [item("awaiting-peer", "2026-11-07T00:00:00Z")], RULES, NOW
    )
    assert number == 1 and "@s2" in text and "@s1" in text and n.MARKER in text


def test_not_old_enough_means_no_nudge():
    assert n.plan([item("awaiting-peer", "2026-11-09T00:00:00Z")], RULES, NOW) == []
    assert n.plan([item("needs-rework", "2026-11-08T00:00:00Z")], RULES, NOW) == []


def test_needs_rework_pings_author_after_four_days():
    ((_, text),) = n.plan([item("needs-rework", "2026-11-05T00:00:00Z")], RULES, NOW)
    assert text.startswith("@s1") and "@s2" not in text


def test_ready_to_merge_reminds_the_author():
    ((_, text),) = n.plan([item("ready-to-merge", "2026-11-05T00:00:00Z")], RULES, NOW)
    assert "ready to merge" in text


def test_repeat_nudge_waits_three_days():
    recent = item("needs-rework", "2026-11-01T00:00:00Z", last="2026-11-08T12:00:00Z")
    assert n.plan([recent], RULES, NOW) == []
    old = item("needs-rework", "2026-11-01T00:00:00Z", last="2026-11-06T00:00:00Z")
    assert len(n.plan([old], RULES, NOW)) == 1


def test_guide_labels_and_unlabelled_prs_are_never_nudged():
    items = [
        item("rule-violation", "2026-10-01T00:00:00Z"),
        item("needs-judgement", "2026-10-01T00:00:00Z"),
    ]
    assert n.plan(items, RULES, NOW) == []

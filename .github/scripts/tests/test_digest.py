import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import digest as d  # noqa: E402

NOW = datetime(2026, 11, 2, 4, 0, tzinfo=timezone.utc)


def pr(number, labels=(), updated="2026-11-01T00:00:00Z", draft=False, title="t"):
    return {
        "number": number,
        "title": title,
        "url": f"https://x/{number}",
        "author": {"login": "s1"},
        "labels": [{"name": n} for n in labels],
        "isDraft": draft,
        "updatedAt": updated,
    }


def test_sections_and_flags():
    open_prs = [
        pr(1, ["rule-violation"]),
        pr(2, ["awaiting-peer"], updated="2026-10-28T00:00:00Z"),
        pr(3, ["awaiting-peer"]),
        pr(4, draft=True),
    ]
    merged = [pr(5, ["ready-to-merge"]), pr(6, ["needs-rework"])]
    text = d.build(open_prs, merged, NOW)
    assert "#1" in text.split("### Stuck")[0]
    stuck = text.split("### Stuck")[1].split("### Merged")[0]
    assert "#2" in stuck and "#3" not in stuck
    merged_part = text.split("### Merged")[1]
    assert "spot-check 2" in merged_part
    assert merged_part.count("without a green bot verdict") == 1
    assert "1 draft" in text


def test_empty_week_says_nothing():
    text = d.build([], [], NOW)
    assert text.count("Nothing") == 3


def test_guides_own_merged_prs_are_not_in_the_spot_check():
    mine = pr(7)
    mine["author"] = {"login": "Guide"}
    text = d.build([], [mine, pr(8, ["ready-to-merge"])], NOW, guide="guide")
    assert "spot-check 1" in text and "#7" not in text

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import inbox as i  # noqa: E402
import pr_rules as r  # noqa: E402

NOW = datetime(2026, 11, 2, 4, 0, tzinfo=timezone.utc)
RULES = r.parse_codeowners(
    "* @s1 @s2 @guide\n/contracts/ @s1 @s2 @s3 @guide\n/CLAUDE.md @guide\n"
)
BOT_TEXT = (
    "### Automated review: **Needs your judgement**\n\n"
    "**Needs the guide's judgement**\n"
    "- Contract change: every affected owner must review. _(PRD §B.0)_\n\n"
    "**Better ways**\n- advice\n"
)


def pr(
    n,
    labels=(),
    draft=False,
    reviews=(),
    checks=("SUCCESS",),
    author="s4",
    body="",
    files=("contracts/x.json",),
):
    return {
        "number": n,
        "title": f"t{n}",
        "url": f"https://x/{n}",
        "author": {"login": author},
        "labels": [{"name": x} for x in labels],
        "isDraft": draft,
        "updatedAt": "2026-10-30T00:00:00Z",
        "createdAt": "2026-10-30T00:00:00Z",
        "body": body,
        "reviews": [{"author": {"login": u}, "state": s} for u, s in reviews],
        "files": [{"path": f} for f in files],
        "statusCheckRollup": [{"name": "checks", "conclusion": c} for c in checks]
        + [{"context": "guide-bot", "state": "FAILURE"}],
    }


def make(open_prs, merged=(), comments=None, bot=None):
    return i.build(
        open_prs, list(merged), comments or {}, bot or {}, NOW, "guide", RULES
    )


def section(text, n):
    return text.split(f"### {n}.")[1].split("\n### ")[0]


def test_empty_inbox_says_nothing_needs_you():
    assert "Nothing needs you right now" in make([pr(1, ["awaiting-peer"])])


def test_decision_pr_shows_the_bots_reason_without_the_citation():
    text = make([pr(1, ["needs-judgement"])], bot={1: BOT_TEXT})
    s = section(text, 1)
    assert "#1" in s and "every affected owner must review" in s and "PRD" not in s
    assert "Nothing needs you" not in text


def test_approved_and_green_goes_to_merge_with_missing_owners_named():
    p = pr(2, ["needs-judgement"], reviews=[("s1", "APPROVED")])
    text = make([p])
    assert "#2" not in section(text, 1)
    s = section(text, 2)
    assert "approved by s1" in s and "s2, s3" in s and "bypass" in s


def test_red_or_pending_checks_keep_it_under_decision():
    p = pr(3, ["rule-violation"], reviews=[("s1", "APPROVED")], checks=("FAILURE",))
    text = make([p])
    assert "#3" in section(text, 1) and "Checks are not green" in section(text, 1)
    assert "#3" not in section(text, 2)


def test_the_guides_own_approval_and_a_later_changes_request_do_not_count():
    own = pr(4, ["needs-judgement"], reviews=[("guide", "APPROVED")])
    assert "#4" in section(make([own]), 1)
    flip = pr(
        5,
        ["needs-judgement"],
        reviews=[("s1", "APPROVED"), ("s1", "CHANGES_REQUESTED")],
    )
    assert "#5" in section(make([flip]), 1)


def test_question_waits_until_the_guide_answers_after_it():
    p = pr(6, ["awaiting-peer"], body="Hi @guide, please confirm")
    assert "#6" in section(make([p]), 3)
    answered = {
        6: [{"user": "guide", "createdAt": "2026-10-31T00:00:00Z", "body": "ok"}]
    }
    assert "#6" not in section(make([p], comments=answered), 3)
    again = {
        6: answered[6]
        + [
            {
                "user": "s4",
                "createdAt": "2026-11-01T00:00:00Z",
                "body": "@guide one more",
            }
        ]
    }
    assert "one more" not in section(make([p], comments=again), 3)
    assert "#6" in section(make([p], comments=again), 3)


def test_bot_and_guide_mentions_are_not_questions():
    c = {
        7: [
            {
                "user": "github-actions[bot]",
                "createdAt": "2026-11-01T00:00:00Z",
                "body": "@guide: your decision is needed.",
            }
        ]
    }
    assert "#7" not in section(make([pr(7, ["needs-judgement"])], comments=c), 3)


def test_waiting_students_and_drafts_and_merged_flags():
    open_prs = [pr(8, ["awaiting-peer"]), pr(9, ["needs-rework"], draft=True)]
    merged = [
        pr(10, ["ready-to-merge"]),
        pr(11, ["needs-rework"]),
        pr(12, [], author="guide"),
    ]
    text = make(open_prs, merged)
    assert "#8" in section(text, 4) and "#9" not in text.split("### 5.")[0]
    s5 = text.split("### 5.")[1]
    assert (
        "(2)" in s5 and s5.count("without a green bot verdict") == 1 and "#12" not in s5
    )
    assert "1 ready, 1 draft" in text and "IST" in text


def test_checks_green_ignores_the_bots_own_status():
    assert i.checks_green(pr(1))
    assert not i.checks_green(pr(1, checks=("SUCCESS", "")))

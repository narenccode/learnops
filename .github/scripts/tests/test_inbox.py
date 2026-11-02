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
STANDING_LINE = (
    "- Contract change: every affected owner and the guide must review "
    "(GitHub only enforces one). _(PRD §B.0)_\n"
)
HEAD = "### Automated review: **Needs your judgement**\n\n**Needs the guide's judgement**\n"
STANDING_ONLY = HEAD + STANDING_LINE
REAL_QUESTION = (
    HEAD
    + STANDING_LINE
    + "- The schema renames a field that Studio already reads; confirm the break. _(PRD A9)_\n\n"
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


# --- whose turn is it: the permanent rules -------------------------------------------------------


def test_contract_pr_without_approval_waits_for_reviewers_not_for_the_guide():
    text = make([pr(1, ["needs-judgement"])], bot={1: STANDING_ONLY})
    assert "#1" not in section(text, 1) and "#1" not in section(text, 2)
    waiting = section(text, 4)
    assert "#1" in waiting and "no reviewer has approved yet" in waiting
    assert "s1, s2, s3" in waiting  # the owners who still have to review
    assert "Nothing needs you right now" in text


def test_approved_and_green_goes_to_merge_with_missing_owners_named():
    p = pr(2, ["needs-judgement"], reviews=[("s1", "APPROVED")])
    text = make([p], bot={2: STANDING_ONLY})
    s = section(text, 2)
    assert "#2" in s and "approved by s1" in s and "s2, s3" in s and "bypass" in s
    assert "#2" not in section(text, 1) and "Nothing needs you" not in text


def test_red_or_pending_checks_wait_on_the_author_not_the_guide():
    p = pr(3, ["needs-judgement"], reviews=[("s1", "APPROVED")], checks=("FAILURE",))
    text = make([p], bot={3: STANDING_ONLY})
    assert "#3" in section(text, 4) and "checks are failing" in section(text, 4)
    assert "#3" not in section(text, 1) and "#3" not in section(text, 2)


def test_changes_requested_waits_on_the_author():
    p = pr(
        4,
        ["needs-judgement"],
        reviews=[("s1", "APPROVED"), ("s2", "CHANGES_REQUESTED")],
    )
    text = make([p], bot={4: STANDING_ONLY})
    assert "changes requested by s2" in section(text, 4)
    assert "#4" not in section(text, 2)


def test_the_guides_own_approval_does_not_count_as_a_reviewer():
    p = pr(5, ["needs-judgement"], reviews=[("guide", "APPROVED")])
    text = make([p], bot={5: STANDING_ONLY})
    assert "no reviewer has approved yet" in section(text, 4)


def test_a_real_question_goes_to_the_guide_even_without_approval():
    text = make([pr(6, ["needs-judgement"])], bot={6: REAL_QUESTION})
    s = section(text, 1)
    assert "#6" in s and "confirm the break" in s
    assert (
        "every affected owner" not in s
    )  # the standing line is not shown as a question
    assert "Nothing needs you" not in text


def test_a_rule_violation_always_goes_to_the_guide():
    text = make([pr(7, ["rule-violation"])], bot={7: STANDING_ONLY})
    assert "#7" in section(text, 1)


def test_missing_or_unreadable_bot_text_fails_safe_to_the_guide():
    text = make([pr(8, ["needs-judgement"])])  # no bot comment found
    assert "#8" in section(text, 1) and "See the bot comment" in section(text, 1)
    odd = make([pr(9, ["needs-judgement"])], bot={9: "something else entirely"})
    assert "#9" in section(odd, 1)


# --- questions, waiting, merged ------------------------------------------------------------------


def test_question_waits_until_the_guide_answers_after_it():
    p = pr(10, ["awaiting-peer"], body="Hi @guide, please confirm")
    assert "#10" in section(make([p]), 3)
    answered = {
        10: [{"user": "guide", "createdAt": "2026-10-31T00:00:00Z", "body": "ok"}]
    }
    assert "#10" not in section(make([p], comments=answered), 3)
    again = {
        10: answered[10]
        + [
            {
                "user": "s4",
                "createdAt": "2026-11-01T00:00:00Z",
                "body": "@guide one more",
            }
        ]
    }
    assert "#10" in section(make([p], comments=again), 3)


def test_bot_mentions_are_not_questions():
    c = {
        11: [
            {
                "user": "github-actions[bot]",
                "createdAt": "2026-11-01T00:00:00Z",
                "body": "@guide: your decision is needed.",
            }
        ]
    }
    assert "#11" not in section(
        make([pr(11, ["needs-judgement"])], comments=c, bot={11: STANDING_ONLY}), 3
    )


def test_waiting_students_and_drafts_and_merged_flags():
    open_prs = [pr(12, ["awaiting-peer"]), pr(13, ["needs-rework"], draft=True)]
    merged = [
        pr(14, ["ready-to-merge"]),
        pr(15, ["needs-rework"]),
        pr(16, [], author="guide"),
    ]
    text = make(open_prs, merged)
    assert "#12" in section(text, 4) and "#13" not in text.split("### 5.")[0]
    s5 = text.split("### 5.")[1]
    assert "(2)" in s5 and s5.count("without a green bot verdict") == 1
    assert "#16" not in s5
    assert "1 ready, 1 draft" in text and "IST" in text


def test_checks_green_ignores_the_bots_own_status():
    assert i.checks_green(pr(1))
    assert not i.checks_green(pr(1, checks=("SUCCESS", "")))

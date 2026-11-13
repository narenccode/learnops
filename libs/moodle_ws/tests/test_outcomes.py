"""Outcomes and pure checks for a draft-grade write (B4 §3a, §3b). No transport is involved.

The guarded write helper that uses them is added in a later pull request.
"""

from __future__ import annotations

from typing import Any

import pytest

from moodle_ws import (
    Outcome,
    grading_status,
    result_for,
    stored_grade_matches,
)
from moodle_ws.grade_write import (
    LOCKED_STATES,
    WORKFLOW_OFF_STATES,
    WRITABLE_STATES,
    _refusal_for_state,
    _result,
)

# Test values only (the same as tests/source_fake.py once it exists).
ASSIGNMENT = 7
LEARNER = 42


# --- R2 and §3b: the stored grade must match learner, attempt and value ----------------------


def test_r2_the_read_back_must_match_the_attempt_sent() -> None:
    answer = {
        "assignments": [
            {
                "assignmentid": ASSIGNMENT,
                "grades": [
                    {"userid": LEARNER, "attemptnumber": 1, "grade": "84.50000"}
                ],
            }
        ],
        "warnings": [],
    }
    assert stored_grade_matches(answer, ASSIGNMENT, LEARNER, 1, 84.5)
    assert not stored_grade_matches(answer, ASSIGNMENT, LEARNER, 0, 84.5)


def grades_answer(**row_change: Any) -> dict[str, Any]:
    row = {"userid": LEARNER, "attemptnumber": 0, "grade": "84.50000", **row_change}
    return {
        "assignments": [{"assignmentid": ASSIGNMENT, "grades": [row]}],
        "warnings": [],
    }


@pytest.mark.parametrize(
    "answer",
    [
        pytest.param(None, id="no answer"),
        pytest.param(
            {**grades_answer(), "warnings": [{"warningcode": "1"}]}, id="a warning"
        ),
        pytest.param({"assignments": [], "warnings": []}, id="no assignment"),
        pytest.param(
            {"assignments": grades_answer()["assignments"] * 2, "warnings": []},
            id="assignment twice",
        ),
        pytest.param(
            {
                "assignments": [
                    {
                        "assignmentid": ASSIGNMENT,
                        "grades": grades_answer()["assignments"][0]["grades"] * 2,
                    }
                ],
                "warnings": [],
            },
            id="learner twice",
        ),
        pytest.param(grades_answer(userid=43), id="other learner"),
        pytest.param(grades_answer(grade="-1.00000"), id="negative stored grade"),
        pytest.param(grades_answer(grade=None), id="no grade"),
        pytest.param(grades_answer(attemptnumber=True), id="bool attempt"),
        pytest.param(
            {"assignments": [{"assignmentid": True, "grades": []}], "warnings": []},
            id="bool assignment id",
        ),
    ],
)
def test_3b_anything_unexpected_is_not_verified(answer: Any) -> None:
    assert not stored_grade_matches(answer, ASSIGNMENT, LEARNER, 0, 84.5)


def test_3b_the_expected_answer_matches() -> None:
    assert stored_grade_matches(grades_answer(), ASSIGNMENT, LEARNER, 0, 84.5)


# --- R3 and fail-closed proposals: which states may be written over --------------------------


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ("notmarked", None),
        ("inmarking", None),
        ("readyforreview", None),
        ("inreview", None),
        ("readyforrelease", Outcome.REFUSED_LOCKED),
        ("released", Outcome.REFUSED_LOCKED),
        ("graded", Outcome.REFUSED_WORKFLOW_OFF),
        ("notgraded", Outcome.REFUSED_WORKFLOW_OFF),
        (None, Outcome.REFUSED_STATE_UNKNOWN),
        ("", Outcome.REFUSED_STATE_UNKNOWN),
        ("NotMarked", Outcome.REFUSED_STATE_UNKNOWN),
        ("inmarking ", Outcome.REFUSED_STATE_UNKNOWN),
        ("marked", Outcome.REFUSED_STATE_UNKNOWN),
    ],
)
def test_only_an_unlocked_marking_workflow_state_may_be_written_over(
    state: str | None, expected: Outcome | None
) -> None:
    """R3 and the fail-closed proposals (B4 §6): locked, marking workflow off and unknown states
    are refused; matching is exact."""
    assert _refusal_for_state(state) is expected


def test_the_state_sets_do_not_overlap() -> None:
    assert not WRITABLE_STATES & LOCKED_STATES
    assert not WRITABLE_STATES & WORKFLOW_OFF_STATES
    assert not LOCKED_STATES & WORKFLOW_OFF_STATES


# --- R6: lastattempt missing -----------------------------------------------------------------


@pytest.mark.parametrize(
    "answer",
    [
        None,
        {},
        {"lastattempt": None},
        {"lastattempt": {}},
        {"lastattempt": {"gradingstatus": 1}},
    ],
)
def test_r6_grading_status_is_none_unless_present_as_text(answer: Any) -> None:
    assert grading_status(answer) is None


# --- R5, R10, R11: outcomes are separate; only VERIFIED is success ----------------------------


@pytest.mark.parametrize(
    "outcome", [Outcome.NO_SUBMISSION, Outcome.NO_GRADE, Outcome.SKIPPED_SUSPENDED]
)
def test_r5_r10_caller_outcomes_are_separate_and_never_success(
    outcome: Outcome,
) -> None:
    result = result_for(outcome)
    assert result.outcome is outcome
    assert not result.succeeded and not result.write_sent


def test_r5_a_suspended_learner_is_reported_as_skipped() -> None:
    result = result_for(Outcome.SKIPPED_SUSPENDED)
    assert "skipped" in result.message


@pytest.mark.parametrize(
    "outcome",
    [
        o
        for o in Outcome
        if o.name not in ("NO_SUBMISSION", "NO_GRADE", "SKIPPED_SUSPENDED")
    ],
)
def test_r10_a_caller_cannot_claim_a_write_outcome(outcome: Outcome) -> None:
    with pytest.raises(ValueError):
        result_for(outcome)


def test_r10_every_outcome_is_distinct_with_its_own_message() -> None:
    assert len({o.value for o in Outcome}) == len(Outcome)
    caller = (Outcome.NO_SUBMISSION, Outcome.NO_GRADE, Outcome.SKIPPED_SUSPENDED)
    assert len({result_for(o).message for o in caller}) == len(caller)


@pytest.mark.parametrize("outcome", list(Outcome))
def test_r10_no_outcome_but_verified_is_success(outcome: Outcome) -> None:
    result = _result(outcome)
    assert result.succeeded is (outcome is Outcome.VERIFIED)


def test_r11_an_uncertain_result_tells_the_mentor_to_decide() -> None:
    lost = _result(Outcome.NOT_VERIFIED, write_sent=True, uncertain=True)
    assert "decide what to do next" in lost.message
    matched = _result(
        Outcome.NEEDS_MENTOR_CONFIRMATION, write_sent=True, uncertain=True
    )
    assert not matched.succeeded and "confirm" in matched.message

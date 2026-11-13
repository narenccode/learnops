"""Outcomes and pure checks for one draft-grade write (B4 §3, §3a rules R1 to R11, §3b).

Nothing here contacts Moodle or sends a grade write: these are the values and checks the guarded
write helper uses, added in a later pull request. Only VERIFIED is success. Outcomes the caller
decides itself (no submission, no grade, suspended) have their own values so they are never mixed up
with success (R5, R10); `result_for()` builds them.

Fail-closed choices on questions the guide has not decided yet (B4 §6; proposed decisions,
documented in README.md and the contract's open questions):
* marking workflow off (state `graded` / `notgraded`): REFUSED_WORKFLOW_OFF;
* a state that cannot be read, or one this library does not know: REFUSED_STATE_UNKNOWN;
* a write whose answer was lost but whose read-back matches: NEEDS_MENTOR_CONFIRMATION, not
  success, until the guide says it may count as VERIFIED (R11: the mentor decides).

The response fields read here (`lastattempt.gradingstatus`; `assignments[].grades[]` with
`userid`, `attemptnumber`, `grade`; `warnings[]`) come from the Moodle 4.5 and 5.3 source (B4 §6a,
§7). They are NOT verified on a lab site (lab checks 4, 12 and 13).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Final

from . import messages
from .client import (
    READY_FOR_RELEASE,
    RELEASED,
)
from .grades import parse_grade

# R3: a learner already in one of these states is never written to.
LOCKED_STATES: Final = frozenset({READY_FOR_RELEASE, RELEASED})
# Marking-workflow states a draft may be written over (Moodle source, B4 §7: the workflow state
# when marking workflow is on, `notmarked` when empty). Not lab-verified (lab check 4).
WRITABLE_STATES: Final = frozenset(
    {"notmarked", "inmarking", "readyforreview", "inreview"}
)
# What gradingstatus is when marking workflow is off (B4 §7). Fail closed: never written to.
WORKFLOW_OFF_STATES: Final = frozenset({"graded", "notgraded"})


class Outcome(StrEnum):
    """What happened to one learner. Only VERIFIED is success (R10)."""

    VERIFIED = "verified"
    NOT_VERIFIED = "not_verified"  # R8, R11: written or maybe written, not confirmed
    REFUSED_LOCKED = "refused_locked"  # R3: nothing sent
    REFUSED_OUT_OF_RANGE = "refused_out_of_range"  # R9: nothing sent
    # Proposed, fail closed, pending the guide (B4 §6): nothing sent.
    REFUSED_STATE_UNKNOWN = "refused_state_unknown"
    REFUSED_WORKFLOW_OFF = "refused_workflow_off"
    # Proposed, fail closed, pending the guide (R11): the answer was lost, the read-back matches.
    NEEDS_MENTOR_CONFIRMATION = "needs_mentor_confirmation"
    ACCESS_DENIED = "access_denied"  # R10
    NO_SUBMISSION = "no_submission"  # R10, decided by the caller
    NO_GRADE = "no_grade"  # R10, decided by the caller
    SKIPPED_SUSPENDED = "skipped_suspended"  # R5, decided by the caller


_MESSAGES: Final = {
    Outcome.VERIFIED: messages.OUTCOME_VERIFIED,
    Outcome.NOT_VERIFIED: messages.OUTCOME_NOT_VERIFIED,
    Outcome.REFUSED_LOCKED: messages.OUTCOME_REFUSED_LOCKED,
    Outcome.REFUSED_OUT_OF_RANGE: messages.OUTCOME_REFUSED_OUT_OF_RANGE,
    Outcome.REFUSED_STATE_UNKNOWN: messages.OUTCOME_REFUSED_STATE_UNKNOWN,
    Outcome.REFUSED_WORKFLOW_OFF: messages.OUTCOME_REFUSED_WORKFLOW_OFF,
    Outcome.NEEDS_MENTOR_CONFIRMATION: messages.OUTCOME_NEEDS_MENTOR_CONFIRMATION,
    Outcome.ACCESS_DENIED: messages.OUTCOME_ACCESS_DENIED,
    Outcome.NO_SUBMISSION: messages.OUTCOME_NO_SUBMISSION,
    Outcome.NO_GRADE: messages.OUTCOME_NO_GRADE,
    Outcome.SKIPPED_SUSPENDED: messages.OUTCOME_SKIPPED_SUSPENDED,
}
_CALLER_OUTCOMES: Final = frozenset(
    {Outcome.NO_SUBMISSION, Outcome.NO_GRADE, Outcome.SKIPPED_SUSPENDED}
)


@dataclass(frozen=True)
class WriteResult:
    outcome: Outcome
    message: str
    # True once mod_assign_save_grade was handed to the transport, whatever came back.
    write_sent: bool = False
    # True if Moodle's answer to the write was lost or failed (R11): the mentor decides next.
    uncertain: bool = False

    @property
    def succeeded(self) -> bool:
        return self.outcome is Outcome.VERIFIED


def _result(
    outcome: Outcome, *, write_sent: bool = False, uncertain: bool = False
) -> WriteResult:
    text = (
        messages.OUTCOME_UNCERTAIN
        if uncertain and outcome is Outcome.NOT_VERIFIED
        else None
    )
    return WriteResult(outcome, text or _MESSAGES[outcome], write_sent, uncertain)


def result_for(outcome: Outcome) -> WriteResult:
    """A result for an outcome the caller decides without writing (R5, R10)."""
    if outcome not in _CALLER_OUTCOMES:
        raise ValueError(
            "only no_submission, no_grade and skipped_suspended are set by callers"
        )
    return _result(outcome)


def grading_status(answer: object) -> str | None:
    """`lastattempt.gradingstatus` from a mod_assign_get_submission_status answer, or None.

    Moodle leaves `lastattempt` out when the learner lacks viewownsubmissionsummary (R6)."""
    if not isinstance(answer, Mapping):
        return None
    last = answer.get("lastattempt")
    if not isinstance(last, Mapping):
        return None
    status = last.get("gradingstatus")
    return status if isinstance(status, str) else None


def _rows(value: object) -> list[Mapping[str, Any]] | None:
    if not isinstance(value, list) or not all(
        isinstance(row, Mapping) for row in value
    ):
        return None
    return value


def stored_grade_matches(
    answer: object, assignmentid: int, userid: int, attemptnumber: int, grade: object
) -> bool:
    """B4 §3b, on a mod_assign_get_grades answer. Anything unexpected is False (not verified).

    Stricter than §3b in one place, on purpose: any warning at all fails the check, because a
    warning's link to an assignment is not verified."""
    if not isinstance(answer, Mapping):
        return False
    warnings = answer.get("warnings", [])
    if not isinstance(warnings, list) or warnings:
        return False
    assignments = _rows(answer.get("assignments"))
    if assignments is None:
        return False
    entries = [a for a in assignments if _same_id(a.get("assignmentid"), assignmentid)]
    if len(entries) != 1:
        return False
    grades = _rows(entries[0].get("grades"))
    if grades is None:
        return False
    rows = [g for g in grades if _same_id(g.get("userid"), userid)]
    if len(rows) != 1:
        return False
    row = rows[0]
    if (
        type(row.get("attemptnumber")) is not int
        or row["attemptnumber"] != attemptnumber
    ):
        return False
    stored = parse_grade(row.get("grade"))
    sent = parse_grade(grade)
    return stored is not None and sent is not None and stored >= 0 and stored == sent


def _same_id(value: object, expected: int) -> bool:
    # type() and not isinstance(): True == 1 in Python, but True is not an id.
    return type(value) is int and value == expected


def _refusal_for_state(state: str | None) -> Outcome | None:
    """None if a draft may be written over this state; otherwise why not (fail closed)."""
    if state in WRITABLE_STATES:
        return None
    if state in LOCKED_STATES:
        return Outcome.REFUSED_LOCKED
    if state in WORKFLOW_OFF_STATES:
        return Outcome.REFUSED_WORKFLOW_OFF
    return Outcome.REFUSED_STATE_UNKNOWN

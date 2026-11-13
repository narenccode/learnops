"""One draft-grade write with its checks and read-back (B4 §3, §3a rules R1 to R11, §3b).

This is the single-learner building block. Looping over learners, the mentor's approval and what
happens after a NOT_VERIFIED result belong to the grading module (FR-G-01, FR-G-06, Release 4), not
here. Outcomes the caller decides itself (no submission, no grade, suspended) have their own values
so they are never mixed up with success (R5, R10); `result_for()` builds them.

Every grade write goes through write_draft_grade: MoodleClient.call() refuses
mod_assign_save_grade, and only a WriteReceipt issued here after all checks can send one.

Fail-closed choices on questions the guide has not decided yet (B4 §6; proposed decisions,
documented in README.md and the contract's open questions):
* marking workflow off (state `graded` / `notgraded`): REFUSED_WORKFLOW_OFF, nothing sent, because
  the grade could reach the gradebook and the learner at once (PRD B4 draft rule; lab check 4);
* a state that cannot be read, or one this library does not know: REFUSED_STATE_UNKNOWN;
* a write whose answer was lost but whose read-back matches: NEEDS_MENTOR_CONFIRMATION, not
  success, until the guide says it may count as VERIFIED (R11: the mentor decides).

The response fields read here (`lastattempt.gradingstatus`; `assignments[].grades[]` with
`userid`, `attemptnumber`, `grade`; `warnings[]`) come from the Moodle 4.5 and 5.3 source (B4 §6a,
§7). They are NOT verified on a lab site (lab checks 12 and 13).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Final

from . import messages
from .client import (
    ATTEMPT_PARAMETER,
    GRADE_PARAMETER,
    READY_FOR_RELEASE,
    RELEASED,
    MoodleClient,
    _copy_params,
    _issue_receipt,
    is_explicit_attempt,
)
from .errors import (
    InvalidParameters,
    MoodleError,
    MoodleUnreachable,
    NotSupported,
    PermissionDenied,
    TokenInvalid,
    UnexpectedResponse,
)
from .grades import grade_in_range, parse_grade

GET_SUBMISSION_STATUS: Final = "mod_assign_get_submission_status"
GET_GRADES: Final = "mod_assign_get_grades"
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


def _is_id(value: object) -> bool:
    return type(value) is int and value > 0


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


def _read_back(
    client: MoodleClient,
    assignmentid: int,
    userid: int,
    attemptnumber: int,
    grade: object,
) -> bool:
    """§3 conditions 1 and 2. Any failure to read is False (R8); nothing is written here."""
    try:
        status = client.call(
            GET_SUBMISSION_STATUS, {"assignid": assignmentid, "userid": userid}
        )
        grades = client.call(GET_GRADES, {"assignmentids": [assignmentid]})
    except MoodleError:
        return False
    return grading_status(status) == READY_FOR_RELEASE and stored_grade_matches(
        grades, assignmentid, userid, attemptnumber, grade
    )


def write_draft_grade(
    client: MoodleClient, params: Mapping[str, Any], max_grade: object
) -> WriteResult:
    """Write one mentor-approved draft grade, at most once, and read it back.

    `params` are the mod_assign_save_grade parameters (PRD B4 table). They are copied once, and
    every check below and the write itself use that copy. `max_grade` is the assignment's maximum
    grade, which the caller reads from the assignment (lab check 2). The write is never repeated
    (R8, R11).
    """
    values = _copy_params(params)
    assignmentid = values.get("assignmentid")
    userid = values.get("userid")
    attemptnumber = values.get(ATTEMPT_PARAMETER)
    grade = values.get(GRADE_PARAMETER)
    if not (
        _is_id(assignmentid) and _is_id(userid) and is_explicit_attempt(attemptnumber)
    ):
        raise InvalidParameters(messages.INVALID_PARAMETERS)
    assert isinstance(assignmentid, int) and isinstance(userid, int)  # for mypy
    assert isinstance(attemptnumber, int)

    # R9: before anything is sent. Moodle would silently ignore an out-of-range grade.
    if not grade_in_range(grade, max_grade):
        return _result(Outcome.REFUSED_OUT_OF_RANGE)

    # R3 and marking workflow: read the current state first; only a known, unlocked
    # marking-workflow state is written to.
    try:
        before = client.call(
            GET_SUBMISSION_STATUS, {"assignid": assignmentid, "userid": userid}
        )
    except PermissionDenied:
        return _result(Outcome.ACCESS_DENIED)
    except MoodleError:
        return _result(Outcome.REFUSED_STATE_UNKNOWN)
    refusal = _refusal_for_state(grading_status(before))
    if refusal is not None:
        return _result(refusal)

    receipt = _issue_receipt(client, values)
    try:
        client._send_checked_write(receipt)
    except (PermissionDenied, TokenInvalid):
        # Moodle answered and refused; the write is not repeated.
        return _result(Outcome.ACCESS_DENIED, write_sent=True)
    except MoodleError as error:
        if not _reached_transport(error):
            raise  # a pre-send guard refused it: nothing was sent
        # R11: the outcome is unknown. Read back once, never write again; the mentor decides.
        matched = _read_back(client, assignmentid, userid, attemptnumber, grade)
        outcome = Outcome.NEEDS_MENTOR_CONFIRMATION if matched else Outcome.NOT_VERIFIED
        return _result(outcome, write_sent=True, uncertain=True)

    # R3 still applies after the write: the state can change between the check and the write.
    verified = _read_back(client, assignmentid, userid, attemptnumber, grade)
    return _result(
        Outcome.VERIFIED if verified else Outcome.NOT_VERIFIED, write_sent=True
    )


def _refusal_for_state(state: str | None) -> Outcome | None:
    """None if a draft may be written over this state; otherwise why not (fail closed)."""
    if state in WRITABLE_STATES:
        return None
    if state in LOCKED_STATES:
        return Outcome.REFUSED_LOCKED
    if state in WORKFLOW_OFF_STATES:
        return Outcome.REFUSED_WORKFLOW_OFF
    return Outcome.REFUSED_STATE_UNKNOWN


def _reached_transport(error: MoodleError) -> bool:
    """The classes call() raises for a failure at or after the transport (client.py), apart from
    the two handled as access failures. Every other class is a pre-send guard."""
    return isinstance(error, MoodleUnreachable | UnexpectedResponse | NotSupported)

"""The guide's B4 decisions R1 to R11 (contracts/moodle-ws.v1.md §3a, PR #64) in write_draft_grade.

Shown here, with a fake that follows the Moodle SOURCE (source_fake.py): each check runs before
anything is sent, the write is sent at most once, only a matching read-back is success, and a direct
call cannot get around any of it. NOT shown here: how a real Moodle 4.5 or 5.3 behaves (lab checks 4
and 12 to 16 are open). R4 and R7 are capability rules for the service role; they have no library code
and are tested in the contract.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import replace
from decimal import Decimal
from typing import Any

import pytest

from moodle_ws import (
    GradeWriteNotAllowed,
    InvalidParameters,
    MoodleClient,
    MoodleError,
    MoodleUnreachable,
    Outcome,
    PermissionDenied,
    Site,
    SiteSettings,
    UnexpectedResponse,
    load_allowlist,
    write_draft_grade,
)
from moodle_ws.client import _copy_params
from moodle_ws.messages import WRITE_NEEDS_HELPER

from .conftest import VALID_WRITE
from .source_fake import ASSIGNMENT, LEARNER, SourceFakeMoodle

SAVE = "mod_assign_save_grade"


STATUS = "mod_assign_get_submission_status"


GRADES = "mod_assign_get_grades"


VERSIONS = ["4.5", "5.3"]


WRITE: dict[str, Any] = {**VALID_WRITE, "assignmentid": ASSIGNMENT, "userid": LEARNER}


def client_for(moodle: SourceFakeMoodle, settings: SiteSettings) -> MoodleClient:
    if moodle.version == "5.3":
        settings = replace(settings, site=Site.MOODLE53, moodle_version="5.3")
    return MoodleClient(settings, moodle)


def write(
    moodle: SourceFakeMoodle,
    settings: SiteSettings,
    max_grade: object = 100,
    **change: Any,
) -> Any:
    return write_draft_grade(
        client_for(moodle, settings), {**WRITE, **change}, max_grade
    )


# --- the normal case, on both versions --------------------------------------------------------


@pytest.mark.parametrize("version", VERSIONS)
def test_a_write_that_reads_back_the_same_value_is_verified(
    version: str, settings: SiteSettings
) -> None:
    moodle = SourceFakeMoodle(version)
    result = write(moodle, settings)
    assert result.outcome is Outcome.VERIFIED
    assert result.succeeded and result.write_sent and not result.uncertain
    assert [name for name, _ in moodle.calls] == [STATUS, SAVE, STATUS, GRADES]


# --- every grade write goes through write_draft_grade -----------------------------------------


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize(
    "change",
    [
        pytest.param({}, id="valid in every other way"),
        pytest.param({"grade": 1000}, id="above any maximum"),
        pytest.param({"grade": 0}, id="zero"),
    ],
)
def test_a_direct_call_never_writes_over_a_locked_learner(
    version: str, change: dict[str, Any], settings: SiteSettings
) -> None:
    moodle = SourceFakeMoodle(
        version, state="readyforrelease"
    )  # locked: must never be written
    with pytest.raises(GradeWriteNotAllowed) as caught:
        client_for(moodle, settings).call(SAVE, {**WRITE, **change})
    assert str(caught.value) == WRITE_NEEDS_HELPER
    assert moodle.calls == []


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize("state", ["graded", "notgraded"])
def test_a_direct_call_cannot_write_with_marking_workflow_off(
    version: str, state: str, settings: SiteSettings
) -> None:
    moodle = SourceFakeMoodle(version, state=state)
    with pytest.raises(GradeWriteNotAllowed):
        client_for(moodle, settings).call(SAVE, WRITE)
    assert moodle.grade is None and moodle.calls == []


# --- R1: mod_assign_get_grades is the stored-grade read-back ----------------------------------


def test_r1_the_contract_allow_list_has_the_read_back() -> None:
    """The merged B4 contract lists mod_assign_get_grades, so the default client can read back."""
    assert GRADES in load_allowlist().functions


def test_r1_the_read_back_asks_for_exactly_the_assignment_written(
    settings: SiteSettings,
) -> None:
    moodle = SourceFakeMoodle("4.5")
    write(moodle, settings)
    assert (GRADES, {"assignmentids": [ASSIGNMENT]}) in moodle.calls


def test_r1_the_state_alone_is_never_enough(settings: SiteSettings) -> None:
    """The state reads readyforrelease, but no grade row comes back."""
    moodle = SourceFakeMoodle("4.5")
    client = client_for(moodle, settings)
    moodle.failures[GRADES] = UnexpectedResponse("lost")
    result = write_draft_grade(client, WRITE, 100)
    assert moodle.state == "readyforrelease"
    assert result.outcome is Outcome.NOT_VERIFIED


# --- R2: explicit attempt, never -1 -----------------------------------------------------------


def test_r2_write_draft_grade_refuses_minus_one_before_reading(
    settings: SiteSettings,
) -> None:
    moodle = SourceFakeMoodle("4.5")
    with pytest.raises(InvalidParameters):
        write(moodle, settings, attemptnumber=-1)
    assert moodle.calls == []


# --- R3: locked states refused before sending; still verified after ----------------------------


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize("state", ["readyforrelease", "released"])
def test_r3_a_locked_state_is_refused_before_anything_is_sent(
    version: str, state: str, settings: SiteSettings
) -> None:
    moodle = SourceFakeMoodle(version, state=state, grade="70.00000")
    result = write(moodle, settings)
    assert result.outcome is Outcome.REFUSED_LOCKED
    assert not result.write_sent
    assert moodle.count(SAVE) == 0
    assert moodle.grade == "70.00000"


def lock_it(moodle: SourceFakeMoodle) -> None:
    """Another grader saves a grade and sets readyforrelease between the check and the write."""
    moodle.state = "readyforrelease"
    moodle.grade = "70.00000"


def test_r3_on_5_3_a_lock_after_the_check_keeps_the_old_grade_and_is_not_verified(
    settings: SiteSettings,
) -> None:
    moodle = SourceFakeMoodle("5.3", between_check_and_write=lock_it)
    result = write(moodle, settings)
    assert moodle.grade == "70.00000"  # Moodle kept it while the call looked successful
    assert result.outcome is Outcome.NOT_VERIFIED
    assert moodle.count(SAVE) == 1


def test_r3_on_4_5_only_the_pre_write_check_protects_a_locked_grade(
    settings: SiteSettings,
) -> None:
    """4.5 overwrites a locked grade (read from the code, lab check 16), so the read-back cannot
    catch a lock that happens after the check. The pre-write refusal is the protection."""
    raced = SourceFakeMoodle("4.5", between_check_and_write=lock_it)
    assert write(raced, settings).outcome is Outcome.VERIFIED
    assert raced.grade == "84.50000"
    already = SourceFakeMoodle("4.5", state="readyforrelease", grade="70.00000")
    assert write(already, settings).outcome is Outcome.REFUSED_LOCKED
    assert already.grade == "70.00000"


# --- marking workflow and state, fail closed (B4 §6) -------------------------------------------


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize("state", ["graded", "notgraded"])
def test_marking_workflow_off_is_refused_before_anything_is_sent(
    version: str, state: str, settings: SiteSettings
) -> None:
    """Proposed, fail closed (B4 §6): with marking workflow off the grade could reach the learner
    at once (PRD B4 draft rule), so it is never written."""
    moodle = SourceFakeMoodle(version, state=state)
    result = write_draft_grade(client_for(moodle, settings), WRITE, 100)
    assert result.outcome is Outcome.REFUSED_WORKFLOW_OFF
    assert not result.write_sent and moodle.count(SAVE) == 0


@pytest.mark.parametrize("state", ["", "NotMarked", "inmarking ", "marked", "unknown"])
def test_an_unknown_state_is_refused(state: str, settings: SiteSettings) -> None:
    moodle = SourceFakeMoodle("5.3", state=state)
    result = write_draft_grade(client_for(moodle, settings), WRITE, 100)
    assert result.outcome is Outcome.REFUSED_STATE_UNKNOWN
    assert moodle.count(SAVE) == 0


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize(
    "state", ["notmarked", "inmarking", "readyforreview", "inreview"]
)
def test_each_unlocked_marking_workflow_state_may_be_written(
    version: str, state: str, settings: SiteSettings
) -> None:
    moodle = SourceFakeMoodle(version, state=state)
    result = write_draft_grade(client_for(moodle, settings), WRITE, 100)
    assert result.outcome is Outcome.VERIFIED
    assert moodle.count(SAVE) == 1


# --- R6: lastattempt missing --------------------------------------------------------------------


@pytest.mark.parametrize("version", VERSIONS)
def test_r6_an_unreadable_state_before_writing_sends_nothing(
    version: str, settings: SiteSettings
) -> None:
    """Open question for the guide (B4 §6): until decided, no write without a readable state."""
    moodle = SourceFakeMoodle(version, show_lastattempt=False)
    result = write(moodle, settings)
    assert result.outcome is Outcome.REFUSED_STATE_UNKNOWN
    assert moodle.count(SAVE) == 0


def test_r6_a_state_hidden_after_the_write_is_not_verified(
    settings: SiteSettings,
) -> None:
    def hide(moodle: SourceFakeMoodle) -> None:
        moodle.show_lastattempt = False

    moodle = SourceFakeMoodle("5.3", between_check_and_write=hide)
    assert write(moodle, settings).outcome is Outcome.NOT_VERIFIED


# --- R8: a failed read-back is NOT_VERIFIED; the write is never repeated ------------------------


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize("failing", [STATUS, GRADES])
def test_r8_a_failed_read_back_is_not_verified_and_writes_once(
    version: str, failing: str, settings: SiteSettings
) -> None:
    def fail_from_now_on(m: SourceFakeMoodle) -> None:
        m.failures[failing] = MoodleUnreachable("timeout")

    # The first status read (the R3 check) works; the failure starts after it.
    moodle = SourceFakeMoodle(version, between_check_and_write=fail_from_now_on)
    result = write(moodle, settings)
    assert moodle.grade == "84.50000"  # Moodle did store it
    assert result.outcome is Outcome.NOT_VERIFIED
    assert result.write_sent and not result.succeeded
    assert moodle.count(SAVE) == 1


# --- R9: range checked before writing; a silently ignored grade is caught ----------------------


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize("grade", [-0.5, 100.00001, 101])
def test_r9_a_grade_out_of_range_is_refused_before_anything_is_sent(
    version: str, grade: float, settings: SiteSettings
) -> None:
    moodle = SourceFakeMoodle(version)
    result = write(moodle, settings, grade=grade)
    assert result.outcome is Outcome.REFUSED_OUT_OF_RANGE
    assert moodle.calls == []


@pytest.mark.parametrize("version", VERSIONS)
def test_r9_moodle_silently_ignoring_a_grade_is_caught_by_the_read_back(
    version: str, settings: SiteSettings
) -> None:
    """The caller's maximum was wrong (100); Moodle's is 50, so Moodle ignores 84.5 with no
    error. Only the read-back shows it."""
    moodle = SourceFakeMoodle(version, max_grade=Decimal(50))
    result = write(moodle, settings, max_grade=100)
    assert moodle.grade is None
    assert result.outcome is Outcome.NOT_VERIFIED


# --- R10: access failures are their own outcome; the next learner continues -------------------


@pytest.mark.parametrize("version", VERSIONS)
def test_r10_an_access_failure_before_writing_is_its_own_outcome(
    version: str, settings: SiteSettings
) -> None:
    moodle = SourceFakeMoodle(version, failures={STATUS: PermissionDenied("no")})
    result = write(moodle, settings)
    assert result.outcome is Outcome.ACCESS_DENIED
    assert moodle.count(SAVE) == 0


def test_r10_one_learner_failing_does_not_stop_the_next(settings: SiteSettings) -> None:
    """Results are values, not exceptions, so a caller's loop simply continues."""
    first = SourceFakeMoodle("5.3", failures={STATUS: PermissionDenied("no")})
    second = SourceFakeMoodle("5.3")
    outcomes = [write(m, settings).outcome for m in (first, second)]
    assert outcomes == [Outcome.ACCESS_DENIED, Outcome.VERIFIED]


# --- R11: an uncertain write is read back, never retried ---------------------------------------


@pytest.mark.parametrize("version", VERSIONS)
def test_r11_a_lost_answer_is_read_back_once_and_never_rewritten(
    version: str, settings: SiteSettings
) -> None:
    """Moodle stored the grade but the answer was lost. The read-back matches, but fail closed
    (proposed, pending the guide): it is not success until the mentor confirms it."""
    moodle = SourceFakeMoodle(version, lose_save_answer=MoodleUnreachable("timeout"))
    result = write(moodle, settings)
    assert result.outcome is Outcome.NEEDS_MENTOR_CONFIRMATION
    assert not result.succeeded
    assert result.uncertain and result.write_sent
    assert "confirm" in result.message
    assert moodle.count(SAVE) == 1


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize(
    "error", [MoodleUnreachable("timeout"), UnexpectedResponse("garbled")]
)
def test_r11_a_write_with_no_answer_is_not_retried_and_the_mentor_decides(
    version: str, error: MoodleError, settings: SiteSettings
) -> None:
    moodle = SourceFakeMoodle(version, failures={SAVE: error})
    result = write(moodle, settings)
    assert result.outcome is Outcome.NOT_VERIFIED
    assert result.uncertain
    assert moodle.count(SAVE) == 1
    assert "decide what to do next" in result.message


def test_r11_a_refused_write_is_not_retried(settings: SiteSettings) -> None:
    moodle = SourceFakeMoodle("5.3", failures={SAVE: PermissionDenied("no")})
    result = write(moodle, settings)
    assert result.outcome is Outcome.ACCESS_DENIED
    assert moodle.count(SAVE) == 1


# --- the parameters are read once ----------------------------------------------------------------


class ChangesAfterFirstRead(Mapping[str, Any]):
    """A valid write whose grade reads 50 the first time and 1000 afterwards."""

    def __init__(self) -> None:
        self.reads = 0

    def __getitem__(self, key: str) -> Any:
        if key != "grade":
            return WRITE[key]
        self.reads += 1
        return 50 if self.reads == 1 else 1000

    def __iter__(self) -> Iterator[str]:
        return iter(WRITE)

    def __len__(self) -> int:
        return len(WRITE)


def test_write_draft_grade_reads_the_parameters_once(settings: SiteSettings) -> None:
    """The range check and the write see the same value: the parameters are copied once."""
    moodle = SourceFakeMoodle("5.3")
    result = write_draft_grade(
        client_for(moodle, settings), ChangesAfterFirstRead(), 100
    )
    sent = [params for name, params in moodle.calls if name == SAVE]
    assert sent == [{**WRITE, "grade": 50}]
    assert result.outcome is Outcome.VERIFIED


def test_assignment_and_learner_ids_match_the_fake() -> None:
    """Guards the fixtures above: WRITE targets the fake's assignment and learner."""
    assert (WRITE["assignmentid"], WRITE["userid"]) == (ASSIGNMENT, LEARNER)
    assert _copy_params(WRITE) == WRITE

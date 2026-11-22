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
from typing import Any

import pytest

from moodle_ws import (
    GradeWriteNotAllowed,
    InvalidParameters,
    MoodleClient,
    Outcome,
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

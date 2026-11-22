"""Shared fixtures. Opening a socket fails the test, so nothing here can reach a network."""

from __future__ import annotations

import socket
from typing import Any, Final

import pytest

from moodle_ws import (
    GradeWriteNotAllowed,
    MoodleClient,
    MoodleError,
    Site,
    SiteSettings,
    Token,
)
from moodle_ws.messages import WRITE_NEEDS_HELPER

FAKE_TOKEN: Final = (
    "fakevalue4tests2only"  # letters and digits, as a real token could be
)
FAKE_URL: Final = "https://moodle45.lab.invalid"
# A grade write that passes every pre-send guard (B4 §3, R2, R9). Test values only.
VALID_WRITE: Final = {
    "assignmentid": 7,
    "userid": 42,
    "grade": 84.5,
    "attemptnumber": 0,
    "addattempt": 0,
    "workflowstate": "readyforrelease",
    "applytoall": 0,
}


def refused_as_direct_write(client: MoodleClient, params: Any) -> MoodleError:
    """Call mod_assign_save_grade directly. It must pass every client guard and still be refused
    as a direct grade write: the exact class and message, not a guard's reason."""
    with pytest.raises(GradeWriteNotAllowed) as caught:
        client.call("mod_assign_save_grade", params)
    assert type(caught.value) is GradeWriteNotAllowed
    assert str(caught.value) == WRITE_NEEDS_HELPER
    return caught.value


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("a test tried to open a socket")

    monkeypatch.setattr(socket, "socket", refuse)


@pytest.fixture
def settings() -> SiteSettings:
    return SiteSettings(Site.MOODLE45, "4.5", FAKE_URL, Token(FAKE_TOKEN))

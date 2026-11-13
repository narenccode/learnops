"""Shared fixtures. Opening a socket fails the test, so nothing here can reach a network."""

from __future__ import annotations

import socket
from typing import Any, Final

import pytest

from moodle_ws import MoodleClient, Site, SiteSettings, Token
from moodle_ws.client import _copy_params, _issue_receipt

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


def send_checked(client: MoodleClient, params: Any) -> Any:
    """Send a grade write the way write_draft_grade does after its own checks pass: one copy of
    the parameters, a receipt, the client's guarded write. Only for tests of the client's guards,
    which still run on this path."""
    return client._send_checked_write(_issue_receipt(client, _copy_params(params)))


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("a test tried to open a socket")

    monkeypatch.setattr(socket, "socket", refuse)


@pytest.fixture
def settings() -> SiteSettings:
    return SiteSettings(Site.MOODLE45, "4.5", FAKE_URL, Token(FAKE_TOKEN))

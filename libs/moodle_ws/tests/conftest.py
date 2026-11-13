"""Shared fixtures. Opening a socket fails the test, so nothing here can reach a network."""

from __future__ import annotations

import socket
from typing import Any, Final

import pytest

from moodle_ws import Site, SiteSettings, Token

FAKE_TOKEN: Final = (
    "fakevalue4tests2only"  # letters and digits, as a real token could be
)
FAKE_URL: Final = "https://moodle45.lab.invalid"


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("a test tried to open a socket")

    monkeypatch.setattr(socket, "socket", refuse)


@pytest.fixture
def settings() -> SiteSettings:
    return SiteSettings(Site.MOODLE45, "4.5", FAKE_URL, Token(FAKE_TOKEN))

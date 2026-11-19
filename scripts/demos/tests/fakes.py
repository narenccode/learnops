"""Test-only variants of the offline fake site (scripts/demos/demo_fake_site.py).

They change nothing in the demo code. They use only the fake's public `post` method: take its
answer and edit it, so a change inside the fake does not break them. Shared by the Tier 2 and
Tier 3 tests.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import parse_qs

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "libs"))
sys.path.insert(0, str(ROOT / "scripts" / "demos"))

from demo_fake_site import FakeSite  # noqa: E402
from demo_live_common import Connection, connect  # noqa: E402
from moodle_ws import MoodleClient  # noqa: E402
from readonly_connection import ReadOnlyTransport  # noqa: E402

STATUS = "mod_assign_get_submission_status"


class NoLastAttemptSite(FakeSite):
    """Moodle leaves `lastattempt` out of the status answer (R6: viewownsubmissionsummary)."""

    def post(self, url: str, body: bytes, timeout: float) -> bytes:
        raw = super().post(url, body, timeout)
        if parse_qs(body.decode("utf-8")).get("wsfunction") == [STATUS]:
            answer = json.loads(raw)
            answer.pop("lastattempt", None)
            raw = json.dumps(answer).encode("utf-8")
        return raw


class NoUsernameSite(FakeSite):
    """Moodle returns `username` only for the service account itself, not for the learners
    (seen on the lab site, 19 Nov). The learners keep their full name and id."""

    def post(self, url: str, body: bytes, timeout: float) -> bytes:
        raw = super().post(url, body, timeout)
        if parse_qs(body.decode("utf-8")).get("wsfunction") == [
            "core_enrol_get_enrolled_users"
        ]:
            users = json.loads(raw)
            for user in users:
                if user["roles"][0]["shortname"] == "student":
                    user.pop("username", None)
            raw = json.dumps(users).encode("utf-8")
        return raw


class DenyingSite(FakeSite):
    """Moodle refuses the named functions, as it does for a missing capability."""

    def __init__(self, denied: Iterable[str]) -> None:
        super().__init__()
        self._denied = frozenset(denied)

    def post(self, url: str, body: bytes, timeout: float) -> bytes:
        if parse_qs(body.decode("utf-8")).get("wsfunction", [""])[0] in self._denied:
            self.functions_called.append(
                parse_qs(body.decode("utf-8"))["wsfunction"][0]
            )
            error = {
                "exception": "moodle_exception",
                "errorcode": "accessexception",
                "message": "Access control exception",
            }
            return json.dumps(error).encode("utf-8")
        return super().post(url, body, timeout)


def connection_for(fake: FakeSite) -> Connection:
    """The offline connection of connect(), but over the given fake site."""
    base = connect(offline=True)
    transport = ReadOnlyTransport(post=fake.post, get=fake.get)
    client = MoodleClient(base.settings, transport)
    return Connection(client, transport, base.settings, True, fake)


def install(
    monkeypatch: "pytest.MonkeyPatch", module: object, fake: FakeSite | None = None
) -> Connection:
    """Make the demo module's main() use one offline connection, so a test can choose the fake and
    look at it afterwards."""
    connection = connection_for(FakeSite() if fake is None else fake)
    monkeypatch.setattr(module, "connect", lambda offline, environ=None: connection)
    return connection

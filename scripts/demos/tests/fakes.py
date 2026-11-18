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

"""How the client reaches Moodle.

Only the Protocol exists. A real transport needs the endpoint, how the token is sent and the response
format, none of which B4 records until the lab checks in contracts/moodle-ws.v1.md §5 are done. A
real transport maps Moodle's answers to the classes in errors.py and alone calls Token.reveal().
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from .config import SiteSettings


class MoodleTransport(Protocol):
    def call(
        self, settings: SiteSettings, function: str, params: Mapping[str, Any]
    ) -> Any: ...

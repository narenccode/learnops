"""How the client reaches Moodle.

http_transport.HttpTransport implements this over Moodle's REST protocol. It is not yet run on a lab
site, so the endpoint, token and response format are unconfirmed (contracts/moodle-ws.v1.md §5, lab
check 1). A transport maps Moodle's answers to the classes in errors.py and alone calls Token.reveal().
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from .config import SiteSettings


class MoodleTransport(Protocol):
    def call(
        self, settings: SiteSettings, function: str, params: Mapping[str, Any]
    ) -> Any: ...

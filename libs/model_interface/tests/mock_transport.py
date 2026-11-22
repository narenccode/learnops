"""The one test double for a local or hosted transport. It never touches a network."""

from __future__ import annotations

from typing import Any

from model_interface.providers import TransportReply


class MockTransport:
    """Answers with a fixed reply or raises a fixed error, and records every call.

    The keyword-only complete() fits both LocalTransport and HostedTransport. A test can assert on
    calls to prove a transport was used, or was never used.
    """

    def __init__(
        self,
        reply: Any = None,
        error: Exception | None = None,
    ) -> None:
        self.reply = reply if reply is not None else TransportReply('{"echo": "ok"}')
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def complete(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.reply

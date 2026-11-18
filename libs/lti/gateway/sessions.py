"""Server-side sessions bound to (iss, sub, context id), ended after two hours idle (B3 §6).

The browser holds only an opaque random token in a cookie. The store keeps a SHA-256 hash of
that token, never the token itself, so the store's contents cannot be replayed as a cookie.

Storage backend: the in-memory store is the only one so far, because session-storage ownership
(ADR 0001, OI-06 and OI-07) is still waiting for the guide. It loses sessions on restart and
must run in one process. A database store implements the same `SessionStore` protocol.
"""

from __future__ import annotations

import hashlib
import secrets
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, Protocol

from lti.gateway.routing import Tool
from lti.gateway.verifier import LaunchResult

IDLE_LIMIT_SECONDS = 2 * 60 * 60  # B3 §6; fixed by the contract, so not configurable


class SessionRefused(Exception):
    """kind: "ended" (missing, unknown or idle too long), "other_course" or "wrong_tool"."""

    def __init__(self, kind: Literal["ended", "other_course", "wrong_tool"]) -> None:
        super().__init__(kind)
        self.kind = kind


@dataclass
class Session:
    launch: LaunchResult
    tool: Tool
    last_seen: float

    @property
    def key(self) -> tuple[str, str, str]:
        return self.launch.session_key


class SessionStore(Protocol):
    def create(self, launch: LaunchResult, tool: Tool) -> str:
        """Store a new session and return the token for the cookie."""
        ...

    def use(self, token: str) -> Session:
        """Return a live session and count this as activity, or raise SessionRefused."""
        ...

    def end(self, token: str) -> None: ...


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("ascii", "replace")).hexdigest()


class InMemorySessionStore:
    def __init__(self, clock: Callable[[], float] = time.time) -> None:
        self._clock = clock
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def create(self, launch: LaunchResult, tool: Tool) -> str:
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._forget_idle()
            self._sessions[_digest(token)] = Session(launch, tool, self._clock())
        return token

    def use(self, token: str) -> Session:
        now = self._clock()
        with self._lock:
            digest = _digest(token)
            session = self._sessions.get(digest)
            if session is None or now - session.last_seen > IDLE_LIMIT_SECONDS:
                self._sessions.pop(digest, None)
                raise SessionRefused("ended")
            session.last_seen = now
            return session

    def end(self, token: str) -> None:
        with self._lock:
            self._sessions.pop(_digest(token), None)

    def _forget_idle(self) -> None:
        now = self._clock()
        for digest in [
            d
            for d, s in self._sessions.items()
            if now - s.last_seen > IDLE_LIMIT_SECONDS
        ]:
            del self._sessions[digest]


def authorise(session: Session, *, tool: Tool | None, context_id: str | None) -> None:
    """SEC-02: a session serves only its own tool and, for a mentor, only its own course.

    Administrators may use any course (PRD A5).
    """
    if tool is not None and tool is not session.tool:
        raise SessionRefused("wrong_tool")
    if (
        context_id is not None
        and session.launch.role == "mentor"
        and context_id != session.launch.context.id
    ):
        raise SessionRefused("other_course")

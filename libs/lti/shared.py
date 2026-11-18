"""Types shared by launch validation (`lti.launch`) and the gateway (`lti.gateway`)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


class LaunchRefused(Exception):
    """A launch is refused; no result and no session exist.

    `kind` picks the message the user sees: "auth", "context" or "role" (B3 §8). `reason` is an
    internal code for the log only (B3 §10.1), for example "role_learner" or "nonce_invalid".
    """

    def __init__(self, kind: Literal["auth", "context", "role"], reason: str) -> None:
        super().__init__(reason)
        self.kind = kind
        self.reason = reason


@dataclass(frozen=True)
class LoginRedirect:
    """Where to send the browser after an OIDC login, and the state it carries.

    The gateway puts `state` in a short-lived cookie (ADR 0001 §8.1), so a launch is accepted
    only in the browser that started the login.
    """

    url: str
    state: str

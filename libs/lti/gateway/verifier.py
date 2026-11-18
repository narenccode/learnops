"""The interface between launch validation (Peer 1) and the gateway (this package).

The gateway never reads an ID token. It hands the login parameters and the posted `id_token`
and `state` to a `LaunchVerifier`, which does every SEC-01 check and returns the normalised B3
result, or raises `LaunchRefused`. The gateway then checks that result against the B3 model
below before it creates a session.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

# B3 §3.1. `fullmatch` with an ASCII-only class also refuses a final newline.
CONTEXT_ID_PATTERN = r"^[1-9][0-9]*$"


class LaunchRefused(Exception):
    """A launch is refused; no result and no session exist.

    `kind` picks the message the user sees: "auth", "context" or "role" (B3 §8). `reason` is an
    internal code for the log only (B3 §10.1), for example "role_learner" or "nonce_invalid".
    """

    def __init__(self, kind: Literal["auth", "context", "role"], reason: str) -> None:
        super().__init__(reason)
        self.kind = kind
        self.reason = reason


class LaunchContext(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    id: str = Field(pattern=CONTEXT_ID_PATTERN)
    title: str | None = Field(default=None, min_length=1)


class ResourceLink(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    id: str = Field(min_length=1)


class LaunchResult(BaseModel):
    """The normalised B3 v1 launch result (contracts/lti-launch.v1.schema.json).

    Unknown fields are ignored (B3 §4, PRD EXT-02). Nothing in it is a raw token or claim set.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    iss: str = Field(min_length=1)
    sub: str = Field(min_length=1)
    deployment_id: str = Field(min_length=1)
    message_type: Literal["LtiResourceLinkRequest"]
    role: Literal["mentor", "administrator"]
    context: LaunchContext
    resource_link: ResourceLink
    name: str | None = Field(default=None, min_length=1)
    email: str | None = Field(default=None, min_length=1)

    @property
    def session_key(self) -> tuple[str, str, str]:
        """The session identity (B3 §6)."""
        return (self.iss, self.sub, self.context.id)


class LaunchVerifier(Protocol):
    """Implemented by the launch validation in `libs/lti` (Peer 1)."""

    def login_redirect(self, params: Mapping[str, str], redirect_uri: str) -> str:
        """Check an OIDC login request from Moodle; return Moodle's auth URL with a fresh state
        and nonce. `redirect_uri` is the gateway's launch URL for the selected tool."""
        ...

    def launch(self, id_token: str, state: str) -> Mapping[str, Any]:
        """Verify the posted launch (SEC-01) and return the normalised B3 result."""
        ...

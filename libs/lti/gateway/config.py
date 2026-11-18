"""Gateway configuration, read only from environment variables (root CLAUDE.md §2.3).

Every variable is listed in `.env.example`. No secret is read here: launches are checked with
Moodle's public keys, the session token is random, and only the tool's *public* key is loaded.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from lti.gateway.routing import Tool

_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})

REQUIRED = (
    "GATEWAY_BASE_URL",
    "LTI_ISSUER",
    "LTI_CLIENT_ID",
    "LTI_DEPLOYMENT_ID",
    "LTI_AUTH_LOGIN_URL",
    "LTI_ACCESS_TOKEN_URL",
    "LTI_PLATFORM_JWKS_URL",
    "VIDEO_APP_URL",
    "GRADING_APP_URL",
)


class GatewayConfigError(Exception):
    """A setting is missing or wrong. The message names it and says what to do."""


@dataclass(frozen=True)
class Platform:
    """The registered Moodle site (B3 §7.1). The issuer is compared exactly as written."""

    issuer: str
    client_id: str
    deployment_ids: frozenset[str]
    auth_login_url: str
    access_token_url: str
    jwks_url: str


@dataclass(frozen=True)
class GatewayConfig:
    base_url: str
    platform: Platform
    destinations: Mapping[Tool, str]
    public_key_path: Path | None = None

    def launch_url(self, tool: Tool) -> str:
        """The redirect URI Moodle posts the launch to; register one per tool in Moodle."""
        return f"{self.base_url}/lti/launch/{tool.value}"

    @property
    def login_url(self) -> str:
        return f"{self.base_url}/lti/login"

    @property
    def jwks_url(self) -> str:
        return f"{self.base_url}/lti/jwks"


def _https_url(name: str, value: str) -> str:
    """HTTPS is required; plain HTTP is allowed only on this machine, for local development."""
    parts = urlsplit(value)
    local_http = parts.scheme == "http" and parts.hostname in _LOCAL_HOSTS
    if not parts.hostname or not (parts.scheme == "https" or local_http):
        raise GatewayConfigError(
            f"{name} must be a full https:// address (http:// only for localhost). "
            f"Fix it in the environment and start the gateway again."
        )
    if parts.query or parts.fragment:
        raise GatewayConfigError(
            f"{name} must not contain '?' or '#'. Remove that part."
        )
    return value.rstrip("/")


def config_from_env(env: Mapping[str, str]) -> GatewayConfig:
    missing = [name for name in REQUIRED if not env.get(name, "").strip()]
    if missing:
        raise GatewayConfigError(
            "Missing setting(s): "
            + ", ".join(missing)
            + ". Copy them from .env.example and fill them in from Moodle's tool "
            "'View configuration details' page."
        )
    deployments = frozenset(
        p.strip() for p in env["LTI_DEPLOYMENT_ID"].split(",") if p.strip()
    )
    platform = Platform(
        # Kept exactly as written: B3 §7.1 matches the issuer with no normalisation.
        issuer=env["LTI_ISSUER"],
        client_id=env["LTI_CLIENT_ID"].strip(),
        deployment_ids=deployments,
        auth_login_url=_https_url(
            "LTI_AUTH_LOGIN_URL", env["LTI_AUTH_LOGIN_URL"].strip()
        ),
        access_token_url=_https_url(
            "LTI_ACCESS_TOKEN_URL", env["LTI_ACCESS_TOKEN_URL"].strip()
        ),
        jwks_url=_https_url(
            "LTI_PLATFORM_JWKS_URL", env["LTI_PLATFORM_JWKS_URL"].strip()
        ),
    )
    destinations = {
        Tool.VIDEO: _https_url("VIDEO_APP_URL", env["VIDEO_APP_URL"].strip()),
        Tool.GRADING: _https_url("GRADING_APP_URL", env["GRADING_APP_URL"].strip()),
    }
    key_path = env.get("LTI_PUBLIC_KEY_PATH", "").strip()
    return GatewayConfig(
        base_url=_https_url("GATEWAY_BASE_URL", env["GATEWAY_BASE_URL"].strip()),
        platform=platform,
        destinations=destinations,
        public_key_path=Path(key_path) if key_path else None,
    )

"""Gateway tests: health, keyset, sessions and tool routing.

The launch verifier is a fake: these tests check the gateway, not JWT validation (Peer 1's
tests cover that). All data is synthetic test data (root CLAUDE.md §2.4).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from lti.gateway import messages
from lti.gateway.app import SESSION_COOKIE, create_app
from lti.gateway.config import GatewayConfig, GatewayConfigError, config_from_env
from lti.gateway.jwks import KeysetError, load_keyset
from lti.gateway.routing import Tool
from lti.gateway.sessions import IDLE_LIMIT_SECONDS, InMemorySessionStore
from lti.gateway.verifier import LaunchRefused

REPO_ROOT = Path(__file__).resolve().parents[4]
EXAMPLES = REPO_ROOT / "contracts" / "examples" / "lti-launch.v1"

ENV = {
    "GATEWAY_BASE_URL": "https://gateway.test",
    "LTI_ISSUER": "https://moodle45.test",
    "LTI_CLIENT_ID": "test-client",
    "LTI_DEPLOYMENT_ID": "1",
    "LTI_AUTH_LOGIN_URL": "https://moodle45.test/mod/lti/auth.php",
    "LTI_ACCESS_TOKEN_URL": "https://moodle45.test/mod/lti/token.php",
    "LTI_PLATFORM_JWKS_URL": "https://moodle45.test/mod/lti/certs.php",
    "VIDEO_APP_URL": "https://gateway.test/video/",
    "GRADING_APP_URL": "https://gateway.test/grading/",
}


def mentor_launch() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(
        (EXAMPLES / "instructor-mentor.json").read_text(encoding="utf-8")
    )
    return loaded


class FakeVerifier:
    """Stands in for Peer 1's verifier: returns a fixed result or raises a fixed refusal."""

    def __init__(
        self,
        result: Mapping[str, Any] | None = None,
        refusal: LaunchRefused | None = None,
    ):
        self.result = result if result is not None else mentor_launch()
        self.refusal = refusal
        self.launch_calls = 0
        self.login_calls: list[str] = []

    def login_redirect(self, params: Mapping[str, str], redirect_uri: str) -> str:
        self.login_calls.append(redirect_uri)
        return "https://moodle45.test/mod/lti/auth.php?state=s"

    def launch(self, id_token: str, state: str) -> Mapping[str, Any]:
        self.launch_calls += 1
        if self.refusal is not None:
            raise self.refusal
        return self.result


class Clock:
    def __init__(self) -> None:
        self.now = 1_000_000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def config() -> GatewayConfig:
    return config_from_env(ENV)


def client_for(
    config: GatewayConfig, verifier: FakeVerifier | None, clock: Clock | None = None
) -> TestClient:
    clock = clock or Clock()
    app = create_app(
        config, verifier=verifier, store=InMemorySessionStore(clock), clock=clock
    )
    # base_url https so the Secure cookie is sent back, as a browser would over HTTPS.
    return TestClient(app, base_url="https://gateway.test", follow_redirects=False)


def launch(client: TestClient, tool: str) -> Any:
    return client.post(f"/lti/launch/{tool}", data={"id_token": "x.y.z", "state": "s"})


# --- start-up and health ----------------------------------------------------------------


def test_health_responds(config: GatewayConfig) -> None:
    response = client_for(config, FakeVerifier()).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_missing_settings_are_named() -> None:
    env = {k: v for k, v in ENV.items() if k != "VIDEO_APP_URL"}
    with pytest.raises(GatewayConfigError, match="VIDEO_APP_URL"):
        config_from_env(env)


@pytest.mark.parametrize(
    "value", ["http://video.test/", "javascript:alert(1)", "/video/"]
)
def test_destination_must_be_https(value: str) -> None:
    with pytest.raises(GatewayConfigError, match="VIDEO_APP_URL"):
        config_from_env({**ENV, "VIDEO_APP_URL": value})


def test_http_is_allowed_on_localhost_only() -> None:
    config = config_from_env({**ENV, "VIDEO_APP_URL": "http://localhost:5173/"})
    assert config.destinations[Tool.VIDEO] == "http://localhost:5173"


# --- keyset -----------------------------------------------------------------------------


def test_jwks_is_empty_without_a_key(config: GatewayConfig) -> None:
    assert client_for(config, FakeVerifier()).get("/lti/jwks").json() == {"keys": []}


def test_jwks_publishes_only_the_public_key(
    config: GatewayConfig, tmp_path: Path
) -> None:
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    path = tmp_path / "tool_public.pem"
    path.write_bytes(
        private.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
    )
    cfg = GatewayConfig(config.base_url, config.platform, config.destinations, path)
    keys = client_for(cfg, FakeVerifier()).get("/lti/jwks").json()["keys"]
    assert len(keys) == 1
    assert keys[0]["kty"] == "RSA" and keys[0]["alg"] == "RS256" and keys[0]["kid"]
    assert keys[0]["e"] == "AQAB"
    assert not {"d", "p", "q", "dp", "dq", "qi"} & keys[0].keys()


def test_unreadable_key_fails_at_start_up(tmp_path: Path) -> None:
    with pytest.raises(KeysetError, match="LTI_PUBLIC_KEY_PATH"):
        load_keyset(tmp_path / "missing.pem")


# --- routing ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("tool", "destination"),
    [
        ("video", "https://gateway.test/video"),
        ("grading", "https://gateway.test/grading"),
    ],
)
def test_valid_launch_routes_to_its_tool(
    config: GatewayConfig, tool: str, destination: str
) -> None:
    client = client_for(config, FakeVerifier())
    response = launch(client, tool)
    assert response.status_code == 303
    assert response.headers["location"] == destination
    cookie = response.headers["set-cookie"]
    assert cookie.startswith(f"{SESSION_COOKIE}=")
    for attribute in (
        "HttpOnly",
        "Secure",
        "SameSite=lax",
        "Path=/",
        f"Max-Age={IDLE_LIMIT_SECONDS}",
    ):
        assert attribute.lower() in cookie.lower()
    assert "x.y.z" not in cookie  # the raw ID token never leaves the gateway


@pytest.mark.parametrize("tool", ["studio", "Video", "video/", "..%2Fvideo"])
def test_unknown_tool_is_refused_before_verification(
    config: GatewayConfig, tool: str
) -> None:
    verifier = FakeVerifier()
    response = launch(client_for(config, verifier), tool)
    assert response.status_code == 404
    assert verifier.launch_calls == 0
    assert "set-cookie" not in response.headers


def test_browser_cannot_choose_the_destination(config: GatewayConfig) -> None:
    client = client_for(config, FakeVerifier())
    response = client.post(
        "/lti/launch/video?redirect=https://evil.test",
        data={"id_token": "x", "state": "s", "redirect_uri": "https://evil.test"},
    )
    assert response.headers["location"] == "https://gateway.test/video"


def test_login_uses_the_launch_url_of_the_target_tool(config: GatewayConfig) -> None:
    verifier = FakeVerifier()
    client = client_for(config, verifier)
    response = client.get(
        "/lti/login",
        params={
            "iss": ENV["LTI_ISSUER"],
            "target_link_uri": "https://gateway.test/lti/launch/grading",
        },
    )
    assert response.status_code == 302
    assert verifier.login_calls == ["https://gateway.test/lti/launch/grading"]


def test_login_for_an_unknown_target_is_refused(config: GatewayConfig) -> None:
    verifier = FakeVerifier()
    response = client_for(config, verifier).get(
        "/lti/login", params={"target_link_uri": "https://evil.test/lti/launch/video"}
    )
    assert response.status_code == 404
    assert verifier.login_calls == []


# --- refusals ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("refusal", "status", "message"),
    [
        (LaunchRefused("auth", "nonce_invalid"), 401, messages.AUTH_FAILED),
        (LaunchRefused("context", "context_invalid"), 400, messages.CONTEXT_INVALID),
        (LaunchRefused("role", "role_learner"), 403, messages.ROLE_REFUSED),
    ],
)
def test_refused_launch_creates_no_session(
    config: GatewayConfig, refusal: LaunchRefused, status: int, message: str
) -> None:
    response = launch(client_for(config, FakeVerifier(refusal=refusal)), "video")
    assert response.status_code == status
    assert response.json()["message"] == message
    assert "set-cookie" not in response.headers


def test_result_that_breaks_the_contract_is_refused(config: GatewayConfig) -> None:
    learner_result = {**mentor_launch(), "role": "learner"}
    response = launch(client_for(config, FakeVerifier(result=learner_result)), "video")
    assert response.status_code == 401
    assert "set-cookie" not in response.headers


def test_launch_without_verifier_is_not_accepted(config: GatewayConfig) -> None:
    response = launch(client_for(config, None), "video")
    assert response.status_code == 503
    assert "set-cookie" not in response.headers


def test_missing_form_fields_are_refused(config: GatewayConfig) -> None:
    verifier = FakeVerifier()
    response = client_for(config, verifier).post(
        "/lti/launch/video", data={"state": "s"}
    )
    assert response.status_code == 401
    assert verifier.launch_calls == 0


# --- sessions ---------------------------------------------------------------------------


def test_session_returns_the_launch_without_any_token(config: GatewayConfig) -> None:
    client = client_for(config, FakeVerifier())
    launch(client, "video")
    response = client.get("/lti/session", params={"tool": "video", "context_id": "42"})
    assert response.status_code == 200
    body = response.json()
    assert body["tool"] == "video"
    assert body["launch"]["role"] == "mentor"
    assert (
        body["launch"]["iss"],
        body["launch"]["sub"],
        body["launch"]["context"]["id"],
    ) == (
        "https://moodle.example.org",
        mentor_launch()["sub"],
        "42",
    )
    assert "id_token" not in response.text and "nonce" not in response.text


@pytest.mark.parametrize("cookie", [None, "not-a-real-session"])
def test_missing_or_invalid_session_is_refused(
    config: GatewayConfig, cookie: str | None
) -> None:
    client = client_for(config, FakeVerifier())
    if cookie is not None:
        client.cookies.set(SESSION_COOKIE, cookie)
    response = client.get("/lti/session")
    assert response.status_code == 401
    assert response.json()["message"] == messages.SESSION_ENDED


def test_session_ends_after_two_hours_idle(config: GatewayConfig) -> None:
    clock = Clock()
    client = client_for(config, FakeVerifier(), clock)
    launch(client, "video")
    clock.now += IDLE_LIMIT_SECONDS - 1
    assert (
        client.get("/lti/session").status_code == 200
    )  # activity resets the idle time
    clock.now += IDLE_LIMIT_SECONDS - 1
    assert client.get("/lti/session").status_code == 200
    clock.now += IDLE_LIMIT_SECONDS + 1
    assert client.get("/lti/session").status_code == 401


def test_session_is_refused_for_the_other_tool(config: GatewayConfig) -> None:
    client = client_for(config, FakeVerifier())
    launch(client, "video")
    response = client.get("/lti/session", params={"tool": "grading"})
    assert response.status_code == 403
    assert response.json()["message"] == messages.WRONG_TOOL


def test_mentor_is_refused_another_course(config: GatewayConfig) -> None:
    client = client_for(config, FakeVerifier())
    launch(client, "grading")
    response = client.get("/lti/session", params={"context_id": "43"})
    assert response.status_code == 403
    assert response.json()["message"] == messages.OTHER_COURSE


def test_administrator_may_use_any_course(config: GatewayConfig) -> None:
    admin = json.loads(
        (EXAMPLES / "institution-administrator.json").read_text(encoding="utf-8")
    )
    client = client_for(config, FakeVerifier(result=admin))
    launch(client, "grading")
    assert client.get("/lti/session", params={"context_id": "999"}).status_code == 200


def test_new_launch_replaces_the_earlier_session(config: GatewayConfig) -> None:
    client = client_for(config, FakeVerifier())
    launch(client, "video")
    first = client.cookies.get(SESSION_COOKIE)
    launch(client, "grading")
    assert client.cookies.get(SESSION_COOKIE) != first
    client.cookies.set(SESSION_COOKIE, str(first))
    assert client.get("/lti/session").status_code == 401

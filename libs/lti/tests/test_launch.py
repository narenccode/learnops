"""Login initiation and launch validation (PRD SEC-01, B3).

Tokens are real RS256 JWTs signed with a key made for each test run; the key resolver returns
its public half, so no network is used. Every result is checked against the B3 schema. All
data is synthetic test data (root CLAUDE.md §2.4).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jsonschema import Draft202012Validator

from lti.launch import (
    CLAIM,
    LOGIN_TTL_SECONDS,
    ROLE_ADMINISTRATOR,
    ROLE_INSTRUCTOR,
    ROLE_LEARNER,
    WHITE_SPACE,
    LaunchValidator,
    Registration,
)
from lti.shared import LaunchRefused

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA = json.loads(
    (REPO_ROOT / "contracts" / "lti-launch.v1.schema.json").read_text(encoding="utf-8")
)
VECTORS = json.loads(
    (
        REPO_ROOT / "contracts" / "test-vectors" / "lti-launch-optional-claims.v1.json"
    ).read_text(encoding="utf-8")
)

ISS = "https://moodle45.test"
CLIENT_ID = "test-client"
LAUNCH_URL = "https://gateway.test/lti/launch/video"
REGISTRATION = Registration(
    issuer=ISS,
    client_id=CLIENT_ID,
    deployment_ids=frozenset({"1"}),
    auth_login_url="https://moodle45.test/mod/lti/auth.php",
    jwks_url="https://moodle45.test/mod/lti/certs.php",
)
SYSTEM_ADMIN = "http://purl.imsglobal.org/vocab/lis/v2/system/person#Administrator"

PLATFORM_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class Clock:
    def __init__(self) -> None:
        self.now = time.time()

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def validator(clock: Clock) -> LaunchValidator:
    return LaunchValidator(
        [REGISTRATION],
        resolve_key=lambda _r, _t: PLATFORM_KEY.public_key(),
        clock=clock,
    )


def login(validator: LaunchValidator, **overrides: str) -> tuple[str, str]:
    """Start a login; return (state, nonce)."""
    params = {
        "iss": ISS,
        "login_hint": "hint-1",
        "target_link_uri": LAUNCH_URL,
        "client_id": CLIENT_ID,
        "lti_deployment_id": "1",
        **overrides,
    }
    redirect = validator.login_redirect(params, LAUNCH_URL)
    query = parse_qs(urlsplit(redirect.url).query)
    return redirect.state, query["nonce"][0]


def claims(nonce: str, /, **overrides: Any) -> dict[str, Any]:
    """Valid launch claims; an override of DROP removes that claim."""
    now = int(time.time())
    body: dict[str, Any] = {
        "iss": ISS,
        "aud": CLIENT_ID,
        "sub": "user-1001",
        "exp": now + 300,
        "iat": now,
        "nonce": nonce,
        "name": "Test Mentor",
        "email": "test.mentor@example.org",
        CLAIM + "version": "1.3.0",
        CLAIM + "message_type": "LtiResourceLinkRequest",
        CLAIM + "deployment_id": "1",
        CLAIM + "target_link_uri": LAUNCH_URL,
        CLAIM + "roles": [ROLE_INSTRUCTOR],
        CLAIM + "context": {"id": "42", "title": "Demo course"},
        CLAIM + "resource_link": {"id": "link-7"},
    }
    body.update(overrides)
    return {k: v for k, v in body.items() if v is not DROP}


DROP = object()


def sign(body: dict[str, Any], key: Any = PLATFORM_KEY, alg: str = "RS256") -> str:
    return jwt.encode(body, key, algorithm=alg, headers={"kid": "k1"})


def refused(validator: LaunchValidator, token: str, state: str) -> LaunchRefused:
    with pytest.raises(LaunchRefused) as info:
        validator.launch(token, state)
    return info.value


def assert_schema_valid(result: dict[str, Any]) -> None:
    errors = list(Draft202012Validator(SCHEMA).iter_errors(result))
    assert not errors, errors


# --- login initiation ------------------------------------------------------------------------


def test_login_redirects_to_moodle_with_a_fresh_state_and_nonce(
    validator: LaunchValidator,
) -> None:
    redirect = validator.login_redirect(
        {"iss": ISS, "login_hint": "hint-1", "target_link_uri": LAUNCH_URL,
         "lti_message_hint": "msg-9"},
        LAUNCH_URL,
    )  # fmt: skip
    parts = urlsplit(redirect.url)
    assert f"{parts.scheme}://{parts.netloc}{parts.path}" == REGISTRATION.auth_login_url
    query = {k: v[0] for k, v in parse_qs(parts.query).items()}
    assert query["state"] == redirect.state
    assert query | {"state": "", "nonce": ""} == {
        "scope": "openid",
        "response_type": "id_token",
        "response_mode": "form_post",
        "prompt": "none",
        "client_id": CLIENT_ID,
        "redirect_uri": LAUNCH_URL,
        "login_hint": "hint-1",
        "lti_message_hint": "msg-9",
        "state": "",
        "nonce": "",
    }
    assert len(query["state"]) >= 43 and len(query["nonce"]) >= 43  # 32 random bytes
    second, _ = login(validator)
    assert second != redirect.state


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        (
            {"iss": "https://moodle45.test/"},
            "iss_unknown",
        ),  # exact match, no normalising
        ({"iss": "https://evil.test"}, "iss_unknown"),
        ({"client_id": "someone-else"}, "client_id_unknown"),
        ({"lti_deployment_id": "2"}, "deployment_unknown"),
        ({"login_hint": ""}, "login_hint_missing"),
        ({"target_link_uri": "https://evil.test/"}, "target_link_uri_foreign"),
    ],
)
def test_bad_login_is_refused(
    validator: LaunchValidator, override: dict[str, str], reason: str
) -> None:
    with pytest.raises(LaunchRefused) as info:
        login(validator, **override)
    assert (info.value.kind, info.value.reason) == ("auth", reason)


# --- a valid launch --------------------------------------------------------------------------


def test_valid_launch_returns_the_b3_result(validator: LaunchValidator) -> None:
    state, nonce = login(validator)
    result = validator.launch(sign(claims(nonce)), state)
    assert result == {
        "iss": ISS,
        "sub": "user-1001",
        "deployment_id": "1",
        "message_type": "LtiResourceLinkRequest",
        "role": "mentor",
        "context": {"id": "42", "title": "Demo course"},
        "resource_link": {"id": "link-7"},
        "name": "Test Mentor",
        "email": "test.mentor@example.org",
    }
    assert_schema_valid(result)


def test_result_carries_no_token_nonce_or_state(validator: LaunchValidator) -> None:
    state, nonce = login(validator)
    token = sign(claims(nonce))
    text = json.dumps(validator.launch(token, state))
    assert token not in text and nonce not in text and state not in text


def test_several_registered_platforms_each_use_their_own_settings(clock: Clock) -> None:
    other = Registration(
        issuer="https://moodle53.test",
        client_id="client-53",
        deployment_ids=frozenset({"5"}),
        auth_login_url="https://moodle53.test/mod/lti/auth.php",
        jwks_url="https://moodle53.test/mod/lti/certs.php",
    )
    validator = LaunchValidator(
        [REGISTRATION, other],
        resolve_key=lambda _r, _t: PLATFORM_KEY.public_key(),
        clock=clock,
    )
    state, nonce = login(
        validator, iss=other.issuer, client_id=other.client_id, lti_deployment_id="5"
    )
    token = sign(
        claims(
            nonce,
            iss=other.issuer,
            aud=other.client_id,
            **{CLAIM + "deployment_id": "5"},
        )
    )
    assert validator.launch(token, state)["iss"] == other.issuer


# --- refusals: token -------------------------------------------------------------------------


def test_invalid_jwt_is_refused(validator: LaunchValidator) -> None:
    state, _ = login(validator)
    assert refused(validator, "not.a.jwt", state).reason == "token_invalid"


def test_signature_from_another_key_is_refused(validator: LaunchValidator) -> None:
    state, nonce = login(validator)
    assert (
        refused(validator, sign(claims(nonce), OTHER_KEY), state).reason
        == "token_invalid"
    )


@pytest.mark.parametrize("alg", ["HS256", "none"])
def test_algorithm_other_than_rs256_is_refused(
    validator: LaunchValidator, alg: str
) -> None:
    state, nonce = login(validator)
    key: Any = None if alg == "none" else "a-shared-test-value-of-at-least-32-bytes!"
    token = jwt.encode(claims(nonce), key, algorithm=alg)
    assert refused(validator, token, state).reason == "alg_unsupported"


def test_expired_launch_is_refused(validator: LaunchValidator) -> None:
    state, nonce = login(validator)
    old = int(time.time()) - 3600
    token = sign(claims(nonce, exp=old, iat=old - 60))
    assert refused(validator, token, state).reason == "token_expired"


def test_wrong_issuer_is_refused(validator: LaunchValidator) -> None:
    state, nonce = login(validator)
    token = sign(claims(nonce, iss="https://evil.test"))
    assert refused(validator, token, state).reason == "iss_invalid"


def test_wrong_audience_is_refused(validator: LaunchValidator) -> None:
    state, nonce = login(validator)
    assert (
        refused(validator, sign(claims(nonce, aud="other")), state).reason
        == "aud_invalid"
    )


@pytest.mark.parametrize("azp", [DROP, "other"])
def test_several_audiences_need_our_azp(
    validator: LaunchValidator, azp: object
) -> None:
    state, nonce = login(validator)
    token = sign(claims(nonce, aud=[CLIENT_ID, "other"], azp=azp))
    assert refused(validator, token, state).reason == "azp_invalid"


def test_several_audiences_with_our_azp_are_accepted(
    validator: LaunchValidator,
) -> None:
    state, nonce = login(validator)
    token = sign(claims(nonce, aud=[CLIENT_ID, "other"], azp=CLIENT_ID))
    assert validator.launch(token, state)["role"] == "mentor"


@pytest.mark.parametrize("version", [DROP, "1.3", "1.3.0 ", 1.3])
def test_version_must_be_exactly_1_3_0(
    validator: LaunchValidator, version: object
) -> None:
    state, nonce = login(validator)
    token = sign(claims(nonce, **{CLAIM + "version": version}))
    assert refused(validator, token, state).reason == "version_invalid"


@pytest.mark.parametrize("deployment", [DROP, "2", ""])
def test_invalid_deployment_is_refused(
    validator: LaunchValidator, deployment: object
) -> None:
    state, nonce = login(validator)
    token = sign(claims(nonce, **{CLAIM + "deployment_id": deployment}))
    assert refused(validator, token, state).reason == "deployment_invalid"


@pytest.mark.parametrize(
    ("claim", "reason"),
    [
        ("sub", "token_invalid"),  # required by the decoder
        ("exp", "token_invalid"),
        ("nonce", "token_invalid"),
        (CLAIM + "resource_link", "resource_link_missing"),
    ],
)
def test_missing_required_claim_is_refused(
    validator: LaunchValidator, claim: str, reason: str
) -> None:
    state, nonce = login(validator)
    token = sign(claims(nonce, **{claim: DROP}))
    assert refused(validator, token, state).reason == reason


@pytest.mark.parametrize(
    "context",
    [DROP, {}, {"id": "0"}, {"id": "007"}, {"id": "4.2"}, {"id": "42\n"}, {"id": "٤٢"}],
)
def test_missing_or_invalid_context_is_refused(
    validator: LaunchValidator, context: object
) -> None:
    state, nonce = login(validator)
    token = sign(claims(nonce, **{CLAIM + "context": context}))
    failure = refused(validator, token, state)
    assert (failure.kind, failure.reason) == ("context", "context_invalid")


def test_target_link_uri_must_match_the_login(validator: LaunchValidator) -> None:
    state, nonce = login(validator)
    token = sign(
        claims(nonce, **{CLAIM + "target_link_uri": "https://gateway.test/other"})
    )
    assert refused(validator, token, state).reason == "target_link_uri_mismatch"


# --- refusals: state and nonce ---------------------------------------------------------------


def test_unknown_state_is_refused(validator: LaunchValidator) -> None:
    _, nonce = login(validator)
    assert refused(validator, sign(claims(nonce)), "made-up").reason == "state_invalid"


def test_state_expires_after_ten_minutes(
    validator: LaunchValidator, clock: Clock
) -> None:
    state, nonce = login(validator)
    clock.now += LOGIN_TTL_SECONDS + 1
    assert refused(validator, sign(claims(nonce)), state).reason == "state_invalid"


def test_wrong_nonce_is_refused(validator: LaunchValidator) -> None:
    state, _ = login(validator)
    assert (
        refused(validator, sign(claims("other-nonce")), state).reason == "nonce_invalid"
    )


def test_replayed_launch_is_refused(validator: LaunchValidator) -> None:
    state, nonce = login(validator)
    token = sign(claims(nonce))
    validator.launch(token, state)
    assert refused(validator, token, state).reason == "state_invalid"


def test_nonce_from_another_login_is_refused(validator: LaunchValidator) -> None:
    first_state, first_nonce = login(validator)
    validator.launch(sign(claims(first_nonce)), first_state)
    second_state, _ = login(validator)
    # The first, already used nonce posted with a fresh state.
    assert (
        refused(validator, sign(claims(first_nonce)), second_state).reason
        == "nonce_invalid"
    )


def test_other_message_type_is_refused_without_using_up_the_state(
    validator: LaunchValidator,
) -> None:
    state, nonce = login(validator)
    deep = sign(claims(nonce, **{CLAIM + "message_type": "LtiDeepLinkingRequest"}))
    assert refused(validator, deep, state).reason == "message_type_unsupported"
    assert validator.launch(sign(claims(nonce)), state)["role"] == "mentor"


def test_failed_signature_does_not_use_up_the_state(validator: LaunchValidator) -> None:
    state, nonce = login(validator)
    refused(validator, sign(claims(nonce), OTHER_KEY), state)
    assert validator.launch(sign(claims(nonce)), state)["role"] == "mentor"


# --- roles (B3 §5) ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("roles", "expected"),
    [
        ([ROLE_INSTRUCTOR], "mentor"),
        ([ROLE_ADMINISTRATOR], "administrator"),
        ([ROLE_INSTRUCTOR, ROLE_ADMINISTRATOR], "administrator"),
        ([ROLE_INSTRUCTOR, ROLE_LEARNER], "mentor"),
        ([ROLE_INSTRUCTOR, SYSTEM_ADMIN, "Instructor"], "mentor"),
    ],
)
def test_roles_map_to_the_b3_role(
    validator: LaunchValidator, roles: list[str], expected: str
) -> None:
    state, nonce = login(validator)
    result = validator.launch(sign(claims(nonce, **{CLAIM + "roles": roles})), state)
    assert result["role"] == expected
    assert_schema_valid(result)


@pytest.mark.parametrize(
    ("roles", "reason"),
    [
        ([ROLE_LEARNER], "role_learner"),
        ([ROLE_LEARNER, SYSTEM_ADMIN], "role_learner"),
        ([SYSTEM_ADMIN], "role_none"),
        (["Instructor", ROLE_INSTRUCTOR.upper()], "role_none"),
        ([], "role_none"),
        (DROP, "role_none"),
    ],
)
def test_learner_and_unrecognised_roles_are_refused(
    validator: LaunchValidator, roles: object, reason: str
) -> None:
    state, nonce = login(validator)
    failure = refused(validator, sign(claims(nonce, **{CLAIM + "roles": roles})), state)
    assert (failure.kind, failure.reason) == ("role", reason)


# --- optional claims (B3 §3.2, shared vectors) ------------------------------------------------


def test_white_space_list_is_the_contract_list() -> None:
    assert WHITE_SPACE == {chr(int(code, 16)) for code in VECTORS["white_space"]}


@pytest.mark.parametrize("vector", VECTORS["vectors"], ids=lambda v: v["id"])
def test_optional_claims_follow_the_shared_vectors(
    validator: LaunchValidator, vector: dict[str, Any]
) -> None:
    value = DROP if vector["input"].get("absent") else vector["input"]["value"]
    state, nonce = login(validator)
    context: dict[str, Any] = (
        {"id": "42"} if value is DROP else {"id": "42", "title": value}
    )
    token = sign(claims(nonce, name=value, email=value, **{CLAIM + "context": context}))
    result = validator.launch(token, state)
    if vector["expected"] == "absent":
        assert result["name"] is None and result["email"] is None
        assert "title" not in result["context"]
    else:
        assert result["name"] == result["email"] == result["context"]["title"] == value
    assert_schema_valid(result)

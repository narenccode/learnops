"""LTI 1.3 login initiation and launch validation (PRD SEC-01, contracts/lti-launch.v1.md).

`LaunchValidator` implements the gateway's `LaunchVerifier` interface (`lti.gateway.verifier`):

1. Moodle sends the browser to the gateway's `/lti/login`. `login_redirect()` checks the
   registered platform and the login parameters, stores a fresh state and nonce on the server,
   and returns Moodle's authorisation URL (`LoginRedirect`).
2. Moodle posts a signed ID token and the state to the gateway's launch URL. `launch()` checks
   the state, verifies the signature with the platform's public keyset, checks every claim,
   uses up the state and nonce, and returns the normalised B3 result, or raises
   `LaunchRefused`.

The result is the only thing that leaves this module: never the ID token, the claims, the nonce
or the state (B3 §10).

JWT handling uses PyJWT (signature, `exp`, `iat`, `iss`, `aud`). ADR 0001 prefers PyLTI1p3Next,
which is not approved yet (Stage 1); this module needs no LTI-specific library, and swapping one
in later changes only this file.
"""

from __future__ import annotations

import re
import secrets
import threading
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import jwt

from lti.shared import LaunchRefused, LoginRedirect

CLAIM = "https://purl.imsglobal.org/spec/lti/claim/"
ROLE_INSTRUCTOR = "http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor"
ROLE_ADMINISTRATOR = (
    "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Administrator"
)
ROLE_LEARNER = "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"

LOGIN_TTL_SECONDS = (
    600  # a login must finish within ten minutes (the state cookie's lifetime)
)
NONCE_MEMORY_SECONDS = 2 * 60 * 60  # longer than any ID token Moodle issues is valid
CLOCK_LEEWAY_SECONDS = 60

# B3 §3.1. [0-9] is ASCII-only in Python's re, and fullmatch also refuses a final newline.
CONTEXT_ID = re.compile(r"[1-9][0-9]*")

# B3 §3.2: Unicode 15.0.0 White_Space, the same list as
# contracts/test-vectors/lti-launch-optional-claims.v1.json. Deliberately not str.isspace().
WHITE_SPACE = frozenset(
    chr(int(code, 16))
    for code in (
        "0009", "000A", "000B", "000C", "000D", "0020", "0085", "00A0", "1680",
        "2000", "2001", "2002", "2003", "2004", "2005", "2006", "2007", "2008", "2009", "200A",
        "2028", "2029", "202F", "205F", "3000",
    )
)  # fmt: skip


@dataclass(frozen=True)
class Registration:
    """One registered Moodle site (B3 §7.1). The issuer is compared exactly as written."""

    issuer: str
    client_id: str
    deployment_ids: frozenset[str]
    auth_login_url: str
    jwks_url: str


# (registration, id_token) -> the platform's public key for that token's `kid`
KeyResolver = Callable[[Registration, str], Any]


def keyset_resolver(timeout_seconds: int = 10) -> KeyResolver:
    """Fetch signing keys from each platform's keyset URL, cached per platform."""
    clients: dict[str, jwt.PyJWKClient] = {}
    lock = threading.Lock()

    def resolve(registration: Registration, token: str) -> Any:
        with lock:
            client = clients.get(registration.issuer)
            if client is None:
                client = jwt.PyJWKClient(
                    registration.jwks_url, cache_keys=True, timeout=timeout_seconds
                )
                clients[registration.issuer] = client
        return client.get_signing_key_from_jwt(token).key

    return resolve


@dataclass(frozen=True)
class _PendingLogin:
    issuer: str
    nonce: str
    redirect_uri: str
    created: float


class LaunchValidator:
    """State and nonce live in memory: run the gateway as one process until the guide decides
    the storage backend (ADR 0001 OI-06, OI-07)."""

    def __init__(
        self,
        registrations: Iterable[Registration],
        *,
        resolve_key: KeyResolver | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._registrations = {r.issuer: r for r in registrations}
        if not self._registrations:
            raise ValueError("At least one Moodle registration is needed.")
        self._resolve_key = (
            resolve_key if resolve_key is not None else keyset_resolver()
        )
        self._clock = clock
        self._pending: dict[str, _PendingLogin] = {}
        self._used_nonces: dict[str, float] = {}
        self._lock = threading.Lock()

    # --- login initiation ------------------------------------------------------------------

    def login_redirect(
        self, params: Mapping[str, str], redirect_uri: str
    ) -> LoginRedirect:
        registration = self._registrations.get(params.get("iss", ""))
        if registration is None:
            raise LaunchRefused("auth", "iss_unknown")
        client_id = params.get("client_id")
        if client_id is not None and client_id != registration.client_id:
            raise LaunchRefused("auth", "client_id_unknown")
        deployment = params.get("lti_deployment_id")
        if deployment is not None and deployment not in registration.deployment_ids:
            raise LaunchRefused("auth", "deployment_unknown")
        login_hint = params.get("login_hint")
        if not login_hint:
            raise LaunchRefused("auth", "login_hint_missing")
        if params.get("target_link_uri") != redirect_uri:
            raise LaunchRefused("auth", "target_link_uri_foreign")

        state, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        with self._lock:
            self._forget_old()
            self._pending[state] = _PendingLogin(
                registration.issuer, nonce, redirect_uri, self._clock()
            )

        query = {
            "scope": "openid",
            "response_type": "id_token",
            "response_mode": "form_post",
            "prompt": "none",
            "client_id": registration.client_id,
            "redirect_uri": redirect_uri,
            "login_hint": login_hint,
            "state": state,
            "nonce": nonce,
        }
        if params.get("lti_message_hint"):
            query["lti_message_hint"] = params["lti_message_hint"]
        separator = "&" if "?" in registration.auth_login_url else "?"
        return LoginRedirect(
            registration.auth_login_url + separator + urlencode(query), state
        )

    # --- launch ----------------------------------------------------------------------------

    def launch(self, id_token: str, state: str) -> dict[str, Any]:
        with self._lock:
            self._forget_old()
            pending = self._pending.get(state)
        if pending is None or not id_token:
            raise LaunchRefused("auth", "state_invalid")
        # B3 §7.1: the platform comes from our own login record, never from the untrusted token.
        registration = self._registrations[pending.issuer]
        claims = self._verified_claims(registration, id_token)

        # B3 §2: another message type is refused before the state or nonce is used up.
        if claims.get(CLAIM + "message_type") != "LtiResourceLinkRequest":
            raise LaunchRefused("auth", "message_type_unsupported")

        # Use up the state and the nonce in one step, so a replayed post fails (ADR 0001 §6.7).
        with self._lock:
            if self._pending.pop(state, None) is None:
                raise LaunchRefused("auth", "state_invalid")
            nonce = claims.get("nonce")
            if (
                not isinstance(nonce, str)
                or not secrets.compare_digest(nonce, pending.nonce)
                or nonce in self._used_nonces
            ):
                raise LaunchRefused("auth", "nonce_invalid")
            self._used_nonces[nonce] = self._clock()

        if claims.get(CLAIM + "target_link_uri") != pending.redirect_uri:
            raise LaunchRefused("auth", "target_link_uri_mismatch")
        return normalised_result(registration, claims)

    def _verified_claims(
        self, registration: Registration, id_token: str
    ) -> dict[str, Any]:
        try:
            if jwt.get_unverified_header(id_token).get("alg") != "RS256":
                raise LaunchRefused("auth", "alg_unsupported")
            key = self._resolve_key(registration, id_token)
            claims: dict[str, Any] = jwt.decode(
                id_token,
                key,
                algorithms=["RS256"],
                audience=registration.client_id,
                issuer=registration.issuer,
                leeway=CLOCK_LEEWAY_SECONDS,
                options={"require": ["exp", "iat", "iss", "aud", "sub", "nonce"]},
            )
        except LaunchRefused:
            raise
        except jwt.ExpiredSignatureError as error:
            raise LaunchRefused("auth", "token_expired") from error
        except jwt.InvalidIssuerError as error:
            raise LaunchRefused("auth", "iss_invalid") from error
        except jwt.InvalidAudienceError as error:
            raise LaunchRefused("auth", "aud_invalid") from error
        except (jwt.PyJWTError, ValueError, KeyError) as error:
            raise LaunchRefused("auth", "token_invalid") from error
        audience = claims.get("aud")
        several = isinstance(audience, list) and len(audience) > 1
        if (several or "azp" in claims) and claims.get("azp") != registration.client_id:
            raise LaunchRefused("auth", "azp_invalid")
        return claims

    def _forget_old(self) -> None:
        now = self._clock()
        for state in [
            s for s, p in self._pending.items() if now - p.created > LOGIN_TTL_SECONDS
        ]:
            del self._pending[state]
        for nonce in [
            n for n, t in self._used_nonces.items() if now - t > NONCE_MEMORY_SECONDS
        ]:
            del self._used_nonces[nonce]


def normalised_result(
    registration: Registration, claims: Mapping[str, Any]
) -> dict[str, Any]:
    """Build the B3 §4 result from claims whose signature has been verified."""
    if claims.get(CLAIM + "version") != "1.3.0":
        raise LaunchRefused("auth", "version_invalid")
    deployment = _as_id(claims.get(CLAIM + "deployment_id"))
    if deployment is None or deployment not in registration.deployment_ids:
        raise LaunchRefused("auth", "deployment_invalid")
    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub:
        raise LaunchRefused("auth", "sub_missing")
    link = claims.get(CLAIM + "resource_link")
    link_id = _as_id(link.get("id")) if isinstance(link, dict) else None
    if not link_id:
        raise LaunchRefused("auth", "resource_link_missing")
    context = claims.get(CLAIM + "context")
    context = context if isinstance(context, dict) else {}
    context_id = _as_id(context.get("id"))
    if context_id is None or not CONTEXT_ID.fullmatch(context_id):
        raise LaunchRefused("context", "context_invalid")
    role = resolve_role(claims.get(CLAIM + "roles"))

    result: dict[str, Any] = {
        "iss": registration.issuer,
        "sub": sub,
        "deployment_id": deployment,
        "message_type": "LtiResourceLinkRequest",
        "role": role,
        "context": {"id": context_id},
        "resource_link": {"id": link_id},
        "name": optional_text(claims.get("name")),
        "email": optional_text(claims.get("email")),
    }
    title = optional_text(context.get("title"))
    if title is not None:
        result["context"]["title"] = title
    return result


def resolve_role(roles: object) -> str:
    """B3 §5: exact URIs only; Administrator wins over Instructor; Instructor + Learner is a
    mentor; Learner alone, or no recognised role, is refused."""
    uris = (
        {r for r in roles if isinstance(r, str)} if isinstance(roles, list) else set()
    )
    if ROLE_ADMINISTRATOR in uris:
        return "administrator"
    if ROLE_INSTRUCTOR in uris:
        return "mentor"
    if ROLE_LEARNER in uris:
        raise LaunchRefused(
            "role", "role_learner"
        )  # PRD EXT-07: never remove this check
    raise LaunchRefused("role", "role_none")


def optional_text(value: object) -> str | None:
    """B3 §3.2: absent, null, empty, white-space-only or not text becomes None; any other
    string is returned unchanged (no trimming)."""
    if not isinstance(value, str) or all(ch in WHITE_SPACE for ch in value):
        return None
    return value


def _as_id(value: object) -> str | None:
    """LTI ids are strings; a positive whole number is accepted and written as text."""
    if isinstance(value, str):
        return value
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return str(value)
    return None

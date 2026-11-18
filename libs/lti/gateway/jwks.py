"""The gateway's public keyset (`GET /lti/jwks`).

Moodle reads it when the tool registration uses "Keyset URL" as its public key type. Only the
public key is read here; the private key stays outside the repository and this process.
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key


class KeysetError(Exception):
    """The public key file cannot be used. The message says why and what to do."""


def _b64url_uint(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def rsa_jwk(pem: bytes) -> dict[str, str]:
    try:
        key = load_pem_public_key(pem)
    except ValueError as error:
        raise KeysetError(
            "LTI_PUBLIC_KEY_PATH is not a PEM public key. Export the public half of the tool "
            "key pair (openssl rsa -pubout) and point the setting at it."
        ) from error
    if not isinstance(key, RSAPublicKey):
        raise KeysetError(
            "LTI_PUBLIC_KEY_PATH must hold an RSA public key (LTI 1.3 uses RS256)."
        )
    numbers = key.public_numbers()
    n, e = _b64url_uint(numbers.n), _b64url_uint(numbers.e)
    # RFC 7638 thumbprint as the key id, so the id changes whenever the key does.
    canonical = json.dumps({"e": e, "kty": "RSA", "n": n}, separators=(",", ":"))
    kid = (
        base64.urlsafe_b64encode(hashlib.sha256(canonical.encode()).digest())
        .rstrip(b"=")
        .decode("ascii")
    )
    return {"kty": "RSA", "alg": "RS256", "use": "sig", "kid": kid, "n": n, "e": e}


def load_keyset(public_key_path: Path | None) -> dict[str, Any]:
    if public_key_path is None:
        return {"keys": []}
    try:
        pem = public_key_path.read_bytes()
    except OSError as error:
        raise KeysetError(
            "LTI_PUBLIC_KEY_PATH cannot be read. Check that the file exists and the gateway "
            "may read it, or leave the setting empty if Moodle does not need a keyset."
        ) from error
    return {"keys": [rsa_jwk(pem)]}

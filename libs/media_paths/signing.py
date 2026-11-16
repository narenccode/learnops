import os
from collections.abc import Mapping
from typing import Protocol, runtime_checkable
from urllib.parse import quote, urlsplit

from media_paths.validation import require_positive_int, validate_relative_path

DEFAULT_TTL_SECONDS = 3600

# PRD B6.4 names three implementations; only "none" is required for the
# baseline (Release 0), so "hmac" and "s3" are recognised but not built yet.
SUPPORTED_SIGNING_MODES = frozenset({"none"})
PLANNED_SIGNING_MODES = frozenset({"hmac", "s3"})


class MediaSigningConfigError(ValueError):
    """Raised when the media-signing configuration is missing or invalid."""


@runtime_checkable
class MediaSigner(Protocol):
    """PRD B6.4: ``url = media_signing.sign(relative_path, ttl_seconds=3600)``."""

    def sign(self, relative_path: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
        """Return a URL for a relative media path, valid for ``ttl_seconds``."""
        ...


def _check_media_base_url(media_base_url: object) -> str:
    """Return the base URL without trailing slashes, or raise a clear error.

    Error messages never echo the URL itself, in case it carries credentials.
    """
    if not isinstance(media_base_url, str):
        raise TypeError(
            f"media_base_url must be a string, got {type(media_base_url).__name__}"
        )
    if any(char.isspace() or not char.isprintable() for char in media_base_url):
        raise ValueError(
            "media_base_url must not contain whitespace or control characters"
        )
    # Checked on the raw string: urlsplit reports "https://host/?" as an empty
    # query, which would still leave a "?" before the appended media path.
    if "?" in media_base_url or "#" in media_base_url:
        raise ValueError(
            "media_base_url must not contain a query string or fragment; "
            "set it to the plain base, e.g. https://media.example.com/media"
        )

    try:
        parsed = urlsplit(media_base_url)
    except ValueError:
        # urlsplit's own messages (e.g. "Invalid IPv6 URL") can quote part of
        # the URL, so a fixed message is raised instead.
        raise ValueError(
            "media_base_url is not a valid URL (check the brackets around an "
            "IPv6 address); use e.g. https://media.example.com/media"
        ) from None
    if parsed.scheme not in ("http", "https"):
        raise ValueError("media_base_url must start with http:// or https://")
    if not parsed.hostname:
        raise ValueError("media_base_url must include a host name")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError(
            "media_base_url must not contain a user name or password; "
            "secrets belong in separate environment variables"
        )
    try:
        parsed.port
    except ValueError:
        raise ValueError("media_base_url has an invalid port") from None

    return media_base_url.rstrip("/")


class NoneSigner:
    """The ``none`` implementation of PRD B6.4, for the lab.

    It builds a plain URL from the media base URL. It adds no signature and no
    expiry, so it provides no access control: anyone with the URL can fetch the
    file for as long as the media store serves it.
    """

    def __init__(self, media_base_url: str) -> None:
        self.media_base_url = _check_media_base_url(media_base_url)

    def sign(self, relative_path: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
        """Return a plain media URL; ``ttl_seconds`` is validated but not applied."""
        if not validate_relative_path(relative_path):
            raise ValueError(
                "relative_path must be a safe relative media path, "
                "e.g. 'courses/python/01-basics/01-intro/720p.mp4' (PRD C-08)"
            )
        require_positive_int(ttl_seconds, "ttl_seconds")

        encoded_path = quote(relative_path, safe="/")
        return f"{self.media_base_url}/{encoded_path}"


def create_media_signer(environ: Mapping[str, str] | None = None) -> MediaSigner:
    """Select the media signer from MEDIA_SIGNING and MEDIA_BASE_URL.

    ``environ`` defaults to ``os.environ``; tests pass a plain dict.
    """
    env = os.environ if environ is None else environ

    mode = env.get("MEDIA_SIGNING")
    if mode is None:
        raise MediaSigningConfigError(
            "MEDIA_SIGNING is not set. Set it to 'none' for the lab (see .env.example)."
        )
    if mode in PLANNED_SIGNING_MODES:
        raise MediaSigningConfigError(
            f"MEDIA_SIGNING={mode!r} is defined in PRD B6.4 but not implemented yet. "
            "Use 'none'."
        )
    if mode not in SUPPORTED_SIGNING_MODES:
        raise MediaSigningConfigError(
            f"MEDIA_SIGNING={mode!r} is not a known signing mode. Use 'none'."
        )

    media_base_url = env.get("MEDIA_BASE_URL")
    if not media_base_url:
        raise MediaSigningConfigError(
            "MEDIA_BASE_URL is not set. Set it to the media store's base URL "
            "(see .env.example)."
        )
    try:
        return NoneSigner(media_base_url)
    except ValueError as error:
        raise MediaSigningConfigError(f"MEDIA_BASE_URL is invalid: {error}") from None

"""Per-site settings from environment variables (B4 §1, guide on Q24, PR #27).

One token per site. The token lives in the environment only and is held in a Token, so a printed
SiteSettings never shows it.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final
from urllib.parse import urlsplit

from . import messages
from .errors import MoodleConfigError
from .secrets import Token

PLACEHOLDER: Final = "CHANGE_ME"  # the value .env.example ships with


class Site(StrEnum):
    MOODLE45 = "moodle45"
    MOODLE53 = "moodle53"


@dataclass(frozen=True)
class _SiteSpec:
    moodle_version: str
    url_variable: str
    token_variable: str


_SPECS: Final[Mapping[Site, _SiteSpec]] = {
    Site.MOODLE45: _SiteSpec("4.5", "MOODLE45_URL", "MOODLE45_WS_TOKEN"),
    Site.MOODLE53: _SiteSpec("5.3", "MOODLE53_URL", "MOODLE53_WS_TOKEN"),
}


@dataclass(frozen=True)
class SiteSettings:
    site: Site
    moodle_version: str
    url: str = field(repr=False)  # repr() must not show a mistaken credential or path
    token: Token

    def __post_init__(self) -> None:
        """The same checks as load_site(), so settings built by hand cannot skip them."""
        if not isinstance(self.site, Site):
            raise _invalid("site")
        if self.moodle_version != _SPECS[self.site].moodle_version:
            raise _invalid("moodle_version")
        if not _is_site_address(self.url):
            raise _invalid("url")
        if not isinstance(self.token, Token):
            raise _invalid("token")
        if self.token.reveal().strip() in ("", PLACEHOLDER):
            raise _invalid("token")


def _invalid(name: str) -> MoodleConfigError:
    return MoodleConfigError(messages.INVALID_SITE_SETTING.format(field=name))


def _is_site_address(url: object) -> bool:
    """http(s) with a host, and nothing that could carry a secret."""
    if not isinstance(url, str) or any(c.isspace() for c in url):
        return False
    if "?" in url or "#" in url:
        return False
    try:
        parts = urlsplit(url)
        parts.port  # noqa: B018  # raises on a malformed port
        host = parts.hostname
    except ValueError:
        return False
    return (
        parts.scheme in ("http", "https")
        and bool(host)
        and parts.username is None
        and parts.password is None
    )


def _required(variable: str, environ: Mapping[str, str]) -> str:
    value = environ.get(variable, "").strip()
    if not value:
        raise MoodleConfigError(messages.MISSING_SETTING.format(variable=variable))
    if value == PLACEHOLDER:
        raise MoodleConfigError(messages.PLACEHOLDER_SETTING.format(variable=variable))
    return value


def load_site(
    site: Site | str, environ: Mapping[str, str] | None = None
) -> SiteSettings:
    source = os.environ if environ is None else environ
    chosen = next((item for item in Site if item.value == site), None)
    if chosen is None:
        allowed = ", ".join(Site)
        raise MoodleConfigError(messages.UNKNOWN_SITE.format(allowed=allowed))
    spec = _SPECS[chosen]
    return SiteSettings(
        site=chosen,
        moodle_version=spec.moodle_version,
        url=_required(spec.url_variable, source),
        token=Token(_required(spec.token_variable, source)),
    )

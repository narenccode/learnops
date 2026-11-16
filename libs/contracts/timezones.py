"""The site time zone of a package-derived course model (PRD B2, decision 0003 #20).

A JSON Schema cannot check a time-zone name, so the schema only requires a non-empty string for a
package model and null for a `.mbz` model. This module holds the run-time check: a name is valid
when Python's `zoneinfo.ZoneInfo` resolves it, so `Asia/Kolkata`, the alias `Asia/Calcutta`,
`UTC` and `Etc/GMT-5` pass, and `UTC+5:30` and `Mars/olympus` do not. The public entry point is
`validate_course_model(doc)` in `validate.py`, which runs the B2 schema and then
`timezone_issues()`; `timezone_issues()` is the helper it uses, not the entry point.

The library reads no environment variables (root CLAUDE.md §2.3). A caller reads `SITE_TIMEZONE`
and passes the mapping in: `site_timezone(os.environ)`. There is no default. A missing or invalid
value raises `ConfigError`, so a build fails closed instead of guessing a zone.

Not here: the model builder (FR-C-01, Release 1) does not exist yet. When it does, it must call
`site_timezone(os.environ)` for a course package, store the result in `source.timezone`, and
validate the finished model with `validate_course_model()`. For a `.mbz` it stores null and
needs no zone.
"""

from __future__ import annotations

from collections.abc import Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from . import messages
from .config import ConfigError
from .report import Issue, Location

SITE_TIMEZONE_VARIABLE = "SITE_TIMEZONE"
SOURCE_TIMEZONE: Location = ("source", "timezone")


def is_known_timezone(name: object) -> bool:
    """True when `zoneinfo` resolves `name`. A value that is not text is never known."""
    if not isinstance(name, str):
        return False
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        # ValueError: an empty or malformed key. OSError: a name that points at a directory.
        return False
    return True


def site_timezone(environ: Mapping[str, str]) -> str:
    """The configured site time zone, read from `SITE_TIMEZONE` in the mapping given.

    Raises ConfigError when it is missing, blank or not a name `zoneinfo` knows. The value is
    returned exactly as set, never trimmed or replaced by a default.
    """
    value = environ.get(SITE_TIMEZONE_VARIABLE)
    if value is None or not value.strip():
        raise ConfigError(
            f"{messages.SITE_TIMEZONE_MISSING} {messages.SITE_TIMEZONE_HINT}"
        )
    if not is_known_timezone(value):
        raise ConfigError(
            f"{messages.SITE_TIMEZONE_INVALID.format(value=value)} "
            f"{messages.SITE_TIMEZONE_HINT}"
        )
    return value


def timezone_issues(model: object) -> list[Issue]:
    """Run-time check of `source.timezone` in a B2 course model.

    A null timezone (a `.mbz` source) is not judged here: the schema decides when null is
    allowed. A model that does not have the expected shape gives no issue either, because the
    schema reports that.
    """
    source = model.get("source") if isinstance(model, dict) else None
    if not isinstance(source, dict) or "timezone" not in source:
        return []
    value = source["timezone"]
    if value is None or is_known_timezone(value):
        return []
    return [
        Issue(
            code="timezone_unknown",
            rule="B2",
            message=messages.TIMEZONE_UNKNOWN.format(
                where=messages.where(SOURCE_TIMEZONE), value=value
            ),
            fix_hint=messages.SITE_TIMEZONE_HINT,
            location=SOURCE_TIMEZONE,
        )
    ]

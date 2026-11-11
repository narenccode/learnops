"""Settings a caller passes to the validator.

The library reads no environment variables (root CLAUDE.md §2.3). Course Studio and the checker
read their own settings and hand the values in here.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass

from . import messages
from .schema import identifier_pattern


class ConfigError(ValueError):
    """A setting passed to the validator is not valid."""


@dataclass(frozen=True)
class ValidationConfig:
    """Settings for `validate_course_document`.

    `protected_idnumbers` are the idnumbers a site adds to the two defaults, final-project and
    course-feedback (PRD B1.4). The defaults are fixed in the schema and are always rejected, so
    this set adds to them and never replaces them.

    Any collection of strings is accepted (a set, list or tuple). It is copied into a frozenset,
    so later changes to the caller's collection do not reach the validator. A single string is
    refused: it would be read as one idnumber per character.
    """

    protected_idnumbers: Collection[str] = frozenset()

    def __post_init__(self) -> None:
        # The frozen dataclass blocks normal assignment; this is the one place that stores the
        # normalised value.
        object.__setattr__(
            self, "protected_idnumbers", _checked_idnumbers(self.protected_idnumbers)
        )


def _checked_idnumbers(raw: object) -> frozenset[str]:
    # A string would be read one character at a time, and a mapping one key at a time.
    if isinstance(raw, str | bytes | Mapping) or not isinstance(raw, Iterable):
        raise ConfigError(
            messages.CONFIG_PROTECTED_NOT_A_LIST.format(found=_describe(raw))
        )
    # Copied once, so a generator works and the caller's own list is not kept.
    values = list(raw)
    for value in values:
        if not isinstance(value, str):
            raise ConfigError(messages.CONFIG_PROTECTED_NOT_TEXT.format(value=value))
    pattern = identifier_pattern()
    # Sorted, so that the first bad value named in the message is always the same one.
    for text in sorted(set(values)):
        if not pattern.match(text):
            raise ConfigError(messages.CONFIG_BAD_PROTECTED_IDNUMBER.format(value=text))
    return frozenset(values)


def _describe(raw: object) -> str:
    if raw is None:
        return "None"
    if isinstance(raw, str | bytes):
        return "a single string"
    return f"a value of type {type(raw).__name__}"

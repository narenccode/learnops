"""Settings a caller passes to the validator. The library reads no environment variables:
Course Studio and the checker read their own settings and hand the values in here."""

from __future__ import annotations

from dataclasses import dataclass

from .schema import identifier_pattern


class ConfigError(ValueError):
    """A setting passed to the validator is not valid."""


@dataclass(frozen=True)
class ValidationConfig:
    # Protected idnumbers a site adds to the two defaults, final-project and course-feedback,
    # which the schema always rejects (PRD B1.4).
    protected_idnumbers: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        pattern = identifier_pattern()
        for value in sorted(self.protected_idnumbers):
            if not pattern.match(value):
                raise ConfigError(
                    f"Protected idnumber {value!r} is not a valid idnumber: use lowercase "
                    "ASCII letters and digits separated by single hyphens."
                )

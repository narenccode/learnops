"""What a validation run returns: errors found, and rules that did not run."""

from __future__ import annotations

from dataclasses import dataclass

Location = tuple[str | int, ...]


@dataclass(frozen=True)
class Issue:
    """One problem, or one rule that could not be checked.

    `code` is a stable short name for tests and callers. `rule` points at the PRD text the issue
    comes from. These are not the checker's CK-xx ids: that catalogue belongs to Module 2.
    """

    code: str
    rule: str
    message: str  # what happened, naming the place (PRD UI-05)
    fix_hint: str  # what to do next
    location: Location = ()  # path inside course.yaml; empty for the whole document
    idnumber: str | None = None


@dataclass(frozen=True)
class ValidationReport:
    """Errors block a build. `not_checked` lists rules that did not run, so that "no errors"
    is never read as "everything was checked"."""

    errors: tuple[Issue, ...] = ()
    not_checked: tuple[Issue, ...] = ()

    @property
    def ok(self) -> bool:
        """True when no error was found. It says nothing about `not_checked` rules."""
        return not self.errors

"""Shared helpers for the package-validator tests (not for the schema tests, which stay as they are)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from contracts.report import Issue, ValidationReport

ROOT = Path(__file__).resolve().parents[3]
EXAMPLE_DIR = ROOT / "contracts" / "examples" / "course-package.v1"

Doc = dict[str, Any]

# Section and activity places in the example package.
WEEK1: tuple[str | int, ...] = ("sections", 0)
WEEK2: tuple[str | int, ...] = ("sections", 1)
WEEK1_GUIDE = WEEK1 + ("activities", 0)

# Rules that are deliberately not implemented yet because their ownership or details are still
# undecided. The validator must say so in `not_checked`, never skip them silently.
HELD_RULE_CODES = frozenset(
    {
        "week_structure_not_checked",
        "unlock_chain_not_checked",
        "marking_table_not_checked",
        "check_vocabulary_not_checked",
        "protected_section_not_checked",
    }
)


def error_codes(report: ValidationReport) -> list[str]:
    return [issue.code for issue in report.errors]


def not_checked_codes(report: ValidationReport) -> set[str]:
    return {issue.code for issue in report.not_checked}


def only(issues: tuple[Issue, ...]) -> Issue:
    """The single issue in `issues`; fails with a readable message when there are 0 or more."""
    assert len(issues) == 1, [(i.code, i.location) for i in issues]
    return issues[0]

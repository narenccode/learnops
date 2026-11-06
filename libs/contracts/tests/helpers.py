"""Shared helpers for the package-validator tests (not for the schema tests, which stay as they are)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from contracts.report import Issue, ValidationReport

ROOT = Path(__file__).resolve().parents[3]
EXAMPLE_DIR = ROOT / "contracts" / "examples" / "course-package.v1"

Doc = dict[str, Any]

# Section and activity places in the example package.
WEEK1: tuple[str | int, ...] = ("sections", 0)
WEEK2: tuple[str | int, ...] = ("sections", 1)
WEEK1_GUIDE = WEEK1 + ("activities", 0)
WEEK1_TASK = WEEK1 + ("activities", 1)
WEEK2_GUIDE = WEEK2 + ("activities", 0)
WEEK2_TASK = WEEK2 + ("activities", 1)

# Rules that are deliberately not implemented yet because their ownership or details are still
# undecided. The validator must say so in `not_checked`, never skip them silently.
HELD_RULE_CODES = frozenset(
    {
        "week_structure_not_checked",
        "unlock_chain_not_checked",
        "points_total_not_checked",
        "unlock_completion_not_checked",
        "idnumber_reuse_not_checked",
        "body_files_not_checked",
        "marking_table_not_checked",
        "check_vocabulary_not_checked",
        "protected_section_not_checked",
        "h5p_files_not_checked",
    }
)

# A package report lists the same rules except the body files, which it has checked.
PACKAGE_HELD_RULE_CODES = HELD_RULE_CODES - {"body_files_not_checked"}


def write_course(package_dir: Path, doc: Doc) -> None:
    text = yaml.safe_dump(doc, allow_unicode=True, sort_keys=False)
    (package_dir / "course.yaml").write_bytes(text.encode("utf-8"))


def link_or_skip(link: Path, target: Path) -> None:
    """Make a symbolic link, or skip the test where the system does not allow it."""
    try:
        os.symlink(target, link)
    except (OSError, NotImplementedError):
        pytest.skip(
            "symbolic links are not available here (Windows without developer mode)"
        )


def error_codes(report: ValidationReport) -> list[str]:
    return [issue.code for issue in report.errors]


def not_checked_codes(report: ValidationReport) -> set[str]:
    return {issue.code for issue in report.not_checked}


def only(issues: tuple[Issue, ...]) -> Issue:
    """The single issue in `issues`; fails with a readable message when there are 0 or more."""
    assert len(issues) == 1, [(i.code, i.location) for i in issues]
    return issues[0]

"""Whole-course validation of a B1 course package (PRD B.0 rule 4, B1.1 to B1.4).

Order: the schema first. The course-level rules run only when the structure is valid, because
they rely on it; otherwise they are reported as not checked. Rules that are not implemented yet
are always listed in `not_checked`, so "no errors" is never read as "fully checked".
"""

from __future__ import annotations

from typing import Any

import yaml

from . import messages
from .body_files import check_body_files
from .config import ValidationConfig
from .course_rules import (
    Doc,
    check_extra_protected_idnumbers,
    check_points_total,
    check_unique_idnumbers,
)
from .report import Issue, ValidationReport
from .schema import schema_issues
from .source import PackageSource

COURSE_YAML = "course.yaml"


def validate_course_document(
    doc: object, *, config: ValidationConfig | None = None
) -> ValidationReport:
    """Validate a parsed course.yaml. Reads no files, so body files are not checked."""
    return _run(doc, None, config or ValidationConfig())


def validate_package(
    source: PackageSource, *, config: ValidationConfig | None = None
) -> ValidationReport:
    """Validate a package: read its course.yaml, apply every rule, and check body files."""
    config = config or ValidationConfig()
    try:
        text = source.read_text(COURSE_YAML)
    except FileNotFoundError:
        return _finish(
            [_course_yaml_issue("course_yaml_missing", messages.COURSE_YAML_MISSING)],
            doc=None,
        )
    except (OSError, UnicodeDecodeError) as exc:
        return _finish([_unreadable(str(exc))], doc=None)
    try:
        doc: Any = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return _finish([_unreadable(str(exc))], doc=None)
    return _run(doc, source, config)


def _run(
    doc: object, source: PackageSource | None, config: ValidationConfig
) -> ValidationReport:
    errors = schema_issues(doc)
    if errors:
        return _finish(errors, doc=None)
    assert isinstance(doc, dict)  # the schema requires an object
    errors = check_unique_idnumbers(doc)
    errors += check_extra_protected_idnumbers(doc, config.protected_idnumbers)
    if doc["course"]["mode"] == "full":
        # Open question for the guide: how the total applies to sections-only (not checked).
        errors += check_points_total(doc)
    if source is not None:
        errors += check_body_files(doc, source)
    return _finish(errors, doc=doc)


def _finish(errors: list[Issue], doc: Doc | None) -> ValidationReport:
    """Add the "not checked" entries that depend on how far the run got."""
    not_checked: list[Issue] = []
    if doc is None:
        not_checked.append(
            Issue(
                code="cross_rules_not_checked",
                rule="B1.2",
                message=messages.CROSS_RULES_NOT_CHECKED,
                fix_hint=messages.CROSS_RULES_NOT_CHECKED_HINT,
            )
        )
    elif doc["course"]["mode"] == "sections-only":
        not_checked.append(
            Issue(
                code="points_total_not_checked_sections_only",
                rule="B1.2 rule 3",
                message=messages.POINTS_NOT_CHECKED_SECTIONS_ONLY,
                fix_hint=messages.NOT_CHECKED_HINT,
            )
        )
    not_checked += [
        Issue(code=code, rule=rule, message=text, fix_hint=messages.NOT_CHECKED_HINT)
        for code, rule, text in messages.HELD_RULES
    ]
    return ValidationReport(errors=tuple(errors), not_checked=tuple(not_checked))


def _course_yaml_issue(code: str, message: str) -> Issue:
    return Issue(
        code=code,
        rule="B1.1",
        message=message,
        fix_hint=messages.COURSE_YAML_MISSING_HINT,
    )


def _unreadable(reason: str) -> Issue:
    return Issue(
        code="course_yaml_unreadable",
        rule="B1.1",
        message=messages.COURSE_YAML_UNREADABLE.format(reason=reason),
        fix_hint=messages.COURSE_YAML_UNREADABLE_HINT,
    )

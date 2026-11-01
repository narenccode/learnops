"""Whole-course validation of a B1 course package (PRD B.0 rule 4, B1.1).

Order: the schema first. Rules that are not implemented yet are always listed in `not_checked`,
so "no errors" is never read as "fully checked".
"""

from __future__ import annotations

from . import messages
from .report import Issue, ValidationReport
from .schema import schema_issues


def validate_course_document(doc: object) -> ValidationReport:
    """Validate a parsed course.yaml against the B1 schema. Reads no files."""
    return _finish(schema_issues(doc))


def _finish(errors: list[Issue]) -> ValidationReport:
    """Add the "not checked" entries: the rules this validator does not implement yet."""
    not_checked = [
        Issue(code=code, rule=rule, message=text, fix_hint=messages.NOT_CHECKED_HINT)
        for code, rule, text in messages.HELD_RULES
    ]
    return ValidationReport(errors=tuple(errors), not_checked=tuple(not_checked))

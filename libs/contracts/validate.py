"""Whole-course validation of a B1 course package (PRD B.0 rule 4, B1.1, B1.2 rule 6, B1.4).

Order: the schema first. The course-level rules run only when the structure is valid, because
they rely on it; otherwise a `cross_rules_not_checked` entry says they did not run. Rules that
are not implemented yet are always listed in `not_checked`, so "no errors" is never read as
"fully checked". For B1.2 rule 6 this validator checks uniqueness within the one package it is
given; that an idnumber is never reused across package versions is listed as not checked.

Errors come in a fixed order: schema errors by place (see `schema.schema_issues`); otherwise
duplicate idnumbers in document order, then configured protected idnumbers in document order.
"""

from __future__ import annotations

from . import messages
from .config import ConfigError, ValidationConfig
from .course_rules import check_extra_protected_idnumbers, check_unique_idnumbers
from .report import Issue, ValidationReport
from .schema import schema_issues


def validate_course_document(
    doc: object, *, config: ValidationConfig | None = None
) -> ValidationReport:
    """Validate a parsed course.yaml. Reads no files and no environment variables.

    `config` carries the settings of the caller, for example the protected idnumbers a site adds
    to the two defaults. Without it only the defaults apply. Anything else than a
    `ValidationConfig` (a dict, for example) raises `ConfigError` before the document is read.
    """
    if config is None:
        config = ValidationConfig()
    elif not isinstance(config, ValidationConfig):
        found = getattr(
            config, "__name__", type(config).__name__
        )  # a class, or an object
        raise ConfigError(messages.CONFIG_WRONG_TYPE.format(found=found))
    errors = schema_issues(doc)
    if errors or not isinstance(doc, dict):
        return _finish(errors, rules_ran=False)
    errors = check_unique_idnumbers(doc)
    errors += check_extra_protected_idnumbers(doc, config.protected_idnumbers)
    return _finish(errors, rules_ran=True)


def _finish(errors: list[Issue], *, rules_ran: bool) -> ValidationReport:
    """Add the "not checked" entries: rules that did not run, and rules not implemented yet."""
    not_checked: list[Issue] = []
    if not rules_ran:
        not_checked.append(
            Issue(
                code="cross_rules_not_checked",
                rule="B1.2, B1.4",
                message=messages.CROSS_RULES_NOT_CHECKED,
                fix_hint=messages.CROSS_RULES_NOT_CHECKED_HINT,
            )
        )
    not_checked += [
        Issue(code=code, rule=rule, message=text, fix_hint=messages.NOT_CHECKED_HINT)
        for code, rule, text in messages.HELD_RULES
    ]
    return ValidationReport(errors=tuple(errors), not_checked=tuple(not_checked))

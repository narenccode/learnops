"""Whole-course validation of a B1 course package (PRD B.0 rule 4, B1.1, B1.2 rule 6, B1.4).

Two entry points share one run. `validate_course_document` takes a parsed course.yaml and reads
no files. `validate_package` reads course.yaml from a package source and also checks that the
files named by `body` exist.

Order: the schema first. The course-level rules and the body files run only when the document
is valid, because they rely on it; otherwise a `cross_rules_not_checked` entry says they did not
run. Rules that are not implemented yet are always listed in `not_checked`, so "no errors" is
never read as "fully checked". `body_files_not_checked` leaves the list only for a run that
really checked the body files. For B1.2 rule 6 this validator checks uniqueness within the one
package it is given; that an idnumber is never reused across package versions is not checked.

Errors come in a fixed order: schema errors by place (see `schema.schema_issues`); otherwise
duplicate idnumbers in document order, then configured protected idnumbers in document order,
then missing body files in document order.
"""

from __future__ import annotations

from typing import Any

import yaml

from . import messages
from .body_files import check_body_files
from .config import ConfigError, ValidationConfig
from .course_rules import check_extra_protected_idnumbers, check_unique_idnumbers
from .report import Issue, ValidationReport
from .schema import schema_issues
from .source import PackageSource

COURSE_YAML = "course.yaml"


def validate_course_document(
    doc: object, *, config: ValidationConfig | None = None
) -> ValidationReport:
    """Validate a parsed course.yaml. Reads no files and no environment variables, so the
    body files are listed as not checked.

    `config` carries the settings of the caller, for example the protected idnumbers a site adds
    to the two defaults. Without it only the defaults apply. Anything else than a
    `ValidationConfig` (a dict, for example) raises `ConfigError` before the document is read.
    """
    return _run(doc, None, _checked_config(config))


def validate_package(
    source: PackageSource, *, config: ValidationConfig | None = None
) -> ValidationReport:
    """Validate a package: read its course.yaml from `source`, apply every implemented rule and
    check that each `body` names a file inside the package. Reads no environment variables and
    never reads a body file; `config` is as for `validate_course_document`."""
    config = _checked_config(config)
    try:
        text = source.read_text(COURSE_YAML)
        doc: Any = yaml.safe_load(text)
    except FileNotFoundError:
        issue = _course_yaml_issue(
            "course_yaml_missing",
            messages.COURSE_YAML_MISSING,
            messages.COURSE_YAML_MISSING_HINT,
        )
    except (OSError, UnicodeDecodeError, yaml.YAMLError, ValueError) as exc:
        # ValueError: PyYAML raises it, not a YAMLError, for an unquoted date like 2026-02-31.
        reason = " ".join(str(exc).split())
        issue = _course_yaml_issue(
            "course_yaml_unreadable",
            messages.COURSE_YAML_UNREADABLE.format(reason=reason),
            messages.COURSE_YAML_UNREADABLE_HINT,
        )
    else:
        return _run(doc, source, config)
    return _finish([issue], rules_ran=False, with_folder=True)


def _checked_config(config: object) -> ValidationConfig:
    if config is None:
        return ValidationConfig()
    if not isinstance(config, ValidationConfig):
        found = (
            f"the class {config.__name__} itself"
            if isinstance(config, type)
            else f"a value of type {type(config).__name__}"
        )
        raise ConfigError(messages.CONFIG_WRONG_TYPE.format(found=found))
    return config


def _run(
    doc: object, source: PackageSource | None, config: ValidationConfig
) -> ValidationReport:
    errors = schema_issues(doc)
    if errors or not isinstance(doc, dict):
        return _finish(errors, rules_ran=False, with_folder=source is not None)
    errors = check_unique_idnumbers(doc)
    errors += check_extra_protected_idnumbers(doc, config.protected_idnumbers)
    if source is not None:
        errors += check_body_files(doc, source)
    return _finish(errors, rules_ran=True, with_folder=source is not None)


def _finish(
    errors: list[Issue], *, rules_ran: bool, with_folder: bool
) -> ValidationReport:
    """Add the "not checked" entries: rules that did not run, and rules not implemented yet.

    The body files were checked only when the rules ran on a package.
    """
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
    for code, rule, text in messages.HELD_RULES:
        if code == "body_files_not_checked":
            if rules_ran and with_folder:
                continue
            if with_folder:
                text = messages.BODY_FILES_NOT_CHECKED_YET
        not_checked.append(
            Issue(
                code=code, rule=rule, message=text, fix_hint=messages.NOT_CHECKED_HINT
            )
        )
    return ValidationReport(errors=tuple(errors), not_checked=tuple(not_checked))


def _course_yaml_issue(code: str, message: str, hint: str) -> Issue:
    return Issue(code=code, rule="B1.1", message=message, fix_hint=hint)

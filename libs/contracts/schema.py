"""The B1 JSON Schema, loaded once, and its errors turned into issues (PRD B1.1)."""

from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

from . import messages
from .report import Issue

# The schema lives in the repository folder `contracts/`, two levels above this package.
SCHEMA_PATH = (
    Path(__file__).resolve().parents[2] / "contracts" / "course-package.v1.schema.json"
)
RULE = "B1.1"


@functools.cache
def load_schema() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return loaded


@functools.cache
def _validator() -> Draft202012Validator:
    # The format checker is on so that impossible calendar dates are rejected.
    return Draft202012Validator(load_schema(), format_checker=FormatChecker())


def schema_issues(document: object) -> list[Issue]:
    """Every schema error, ordered by place so the result is the same on every run."""
    errors = sorted(
        _validator().iter_errors(document),
        key=lambda e: ([str(p) for p in e.absolute_path], e.message),
    )
    return [_to_issue(error) for error in errors]


def _to_issue(error: ValidationError) -> Issue:
    location = tuple(error.absolute_path)
    place = messages.where(location)
    if error.validator == "not" and location and location[-1] == "idnumber":
        # The only `not` in the schema is the list of default protected idnumbers.
        return Issue(
            code="schema_not",
            rule=RULE,
            message=messages.PROTECTED_DEFAULT.format(
                where=place, value=error.instance
            ),
            fix_hint=messages.PROTECTED_DEFAULT_HINT,
            location=location,
        )
    return Issue(
        code=f"schema_{error.validator}",
        rule=RULE,
        message=messages.SCHEMA_ERROR.format(where=place, detail=error.message),
        fix_hint=messages.SCHEMA_HINT,
        location=location,
    )

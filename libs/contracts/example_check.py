"""Check the examples of one contract schema (PRD B.0 rule 1, E1 "Contract" level).

This is the engine of the repository-wide validator, `validate_examples.py` (a separate pull
request, so nothing runs this module yet). It loads one JSON Schema and checks a list of example
files against it. It only reads files and never raises for bad content: every problem is returned
as a `Problem` with a message and a hint. Finding the schemas and their examples, the report and
the command line are not here.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from jsonschema.protocols import Validator
from jsonschema.validators import validator_for
from referencing.exceptions import Unresolvable

from . import messages
from .schema import error_order

EXAMPLE_SUFFIXES = frozenset({".json", ".yaml", ".yml"})
YAML_SUFFIXES = frozenset({".yaml", ".yml"})
# A schema error can repeat a whole document; keep the report readable.
MAX_DETAIL = 300


@dataclass(frozen=True)
class Problem:
    """One thing that is wrong. `example` and `schema` are repository-relative paths."""

    code: str
    message: str
    hint: str
    example: str | None = None
    schema: str | None = None


@dataclass(frozen=True)
class SchemaCheck:
    """The outcome for one schema. `passed` and `failed` hold the example paths the caller gave.
    An example in neither was not validated, because its schema could not be used."""

    problems: tuple[Problem, ...] = ()
    passed: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()


def check_schema_examples(
    schema_path: Path, schema_rel: str, examples: Sequence[tuple[Path, str]]
) -> SchemaCheck:
    """Check each example, given as (file, repository-relative path), against the schema."""
    validator, schema_problem = load_validator(schema_path, schema_rel)
    problems = [schema_problem] if schema_problem else []
    outcomes: list[tuple[str, list[Problem]]] = []
    for path, example_rel in examples:
        if validator is None:
            break
        found = check_example(path, example_rel, schema_rel, validator)
        if found and found[0].code == "unresolvable_reference":
            # The schema cannot be used at all: drop what the earlier examples of this schema
            # reported, so that none is left as passed or failed.
            problems.append(found[0])
            validator = None
            break
        outcomes.append((example_rel, found))
    if validator is None:
        problems += [
            Problem(
                "example_not_validated",
                messages.EX_NOT_VALIDATED,
                messages.EX_NOT_VALIDATED_HINT,
                example=example_rel,
                schema=schema_rel,
            )
            for _, example_rel in examples
        ]
        return SchemaCheck(tuple(problems))
    passed: list[str] = []
    failed: list[str] = []
    for example_rel, found in outcomes:
        if found:
            problems += found
            failed.append(example_rel)
        else:
            passed.append(example_rel)
    return SchemaCheck(tuple(problems), tuple(passed), tuple(failed))


def load_validator(
    path: Path, schema_rel: str
) -> tuple[Validator | None, Problem | None]:
    try:
        schema: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return None, Problem(
            "unreadable_schema",
            messages.EX_UNREADABLE_SCHEMA.format(reason=_one_line(exc)),
            messages.EX_UNREADABLE_SCHEMA_HINT,
            schema=schema_rel,
        )
    try:
        if not isinstance(schema, dict):
            raise SchemaError("the top level is not a JSON object")
        cls = validator_for(schema, default=Draft202012Validator)
        cls.check_schema(schema)
    except SchemaError as exc:
        return None, Problem(
            "invalid_schema",
            messages.EX_INVALID_SCHEMA.format(reason=_short(exc.message)),
            messages.EX_INVALID_SCHEMA_HINT,
            schema=schema_rel,
        )
    # The format checker is on so that impossible dates are rejected, as in the B1 tests.
    return cls(schema, format_checker=FormatChecker()), None


def check_example(
    path: Path, example_rel: str, schema_rel: str, validator: Validator
) -> list[Problem]:
    try:
        document = _parse(path)
    except (OSError, UnicodeDecodeError, ValueError, yaml.YAMLError) as exc:
        # ValueError: JSON syntax and PyYAML's impossible dates.
        return [
            Problem(
                "unreadable_example",
                messages.EX_UNREADABLE_EXAMPLE.format(reason=_one_line(exc)),
                messages.EX_UNREADABLE_EXAMPLE_HINT,
                example=example_rel,
                schema=schema_rel,
            )
        ]
    try:
        errors = sorted(validator.iter_errors(document), key=error_order)
    except Unresolvable as exc:
        # Lazy: a reference is only resolved when an example reaches it, so this can appear on
        # any example of the schema, not only the first.
        return [
            Problem(
                "unresolvable_reference",
                messages.EX_UNRESOLVABLE_REFERENCE.format(reason=_one_line(exc)),
                messages.EX_UNRESOLVABLE_REFERENCE_HINT,
                schema=schema_rel,
            )
        ]
    return [
        Problem(
            "schema_violation",
            messages.EX_SCHEMA_VIOLATION.format(
                where=_place(tuple(error.absolute_path)),
                detail=_short(error.message),
                keyword=error.validator,
            ),
            messages.EX_SCHEMA_VIOLATION_HINT,
            example=example_rel,
            schema=schema_rel,
        )
        for error in errors
    ]


def _parse(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in YAML_SUFFIXES:
        # The value is used exactly as parsed: an unquoted date stays a date, and B1 rejects it.
        return yaml.safe_load(text)
    return json.loads(text)


def _place(location: tuple[str | int, ...]) -> str:
    return messages.where(location) if location else messages.EX_PLACE_DOCUMENT


def _one_line(exc: BaseException) -> str:
    return _short(" ".join(str(exc).split()))


def _short(text: str) -> str:
    return text if len(text) <= MAX_DETAIL else text[: MAX_DETAIL - 1] + "…"

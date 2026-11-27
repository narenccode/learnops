"""Check the examples of one contract schema (PRD B.0 rule 1, E1 "Contract" level).

This is the engine of the repository-wide validator, `validate_examples.py` (a separate pull
request, so nothing runs this module yet). It loads one JSON Schema and checks a list of example
files against it. It only reads files. Content it cannot use is returned as a `Problem` with a
message and a hint instead of being raised: bad JSON or YAML (including a key repeated in one
object, and NaN, Infinity or -Infinity in JSON), a file that is not UTF-8, a schema
that is not valid (including a non-string `$schema`), content nested too deeply, and a `$ref` that
cannot be resolved. What it does not promise:

- A `$ref` is resolved only when an example reaches it, so a dangling reference in a branch that no
  example uses (an optional property, one arm of `oneOf`) is not found.
- Only the formats listed in `CHECKED_FORMATS` are checked, whatever optional packages are
  installed (see the README); others, such as `date-time`, `uri` and `idn-hostname`, are
  accepted without validation.
- Time and memory are not bounded: a huge file or a pathological regular expression can exhaust
  them.

Finding the schemas and their examples, the report and the command line are not here.
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
# The formats we assert. An explicit list, because the default `FormatChecker()` also checks
# whatever optional packages happen to be installed (for example `idn-hostname` with `idna`),
# which would make the result depend on the environment.
CHECKED_FORMATS = frozenset(
    {"date", "email", "idn-email", "ipv4", "ipv6", "regex", "time", "uuid"}
)


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
    """Check each example, given as (file, repository-relative path), against the schema.

    A `$ref` that cannot be resolved makes the whole schema unusable, but only when an example
    reaches it: a dangling reference in a branch no example uses is not found. When the schema is
    unusable, every example is reported as not validated."""
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
    except (OSError, UnicodeDecodeError, ValueError, RecursionError) as exc:
        return None, Problem(
            "unreadable_schema",
            messages.EX_UNREADABLE_SCHEMA.format(reason=_reason(exc)),
            messages.EX_UNREADABLE_SCHEMA_HINT,
            schema=schema_rel,
        )
    try:
        if not isinstance(schema, dict):
            raise SchemaError("the top level is not a JSON object")
        # validator_for() looks `$schema` up in a dictionary of URIs: a number, a list or an
        # object would raise AttributeError or TypeError there instead of SchemaError.
        if not isinstance(schema.get("$schema", ""), str):
            raise SchemaError(messages.EX_SCHEMA_KEYWORD_NOT_TEXT)
        cls = validator_for(schema, default=Draft202012Validator)
        cls.check_schema(schema)
    except (SchemaError, RecursionError) as exc:
        return None, Problem(
            "invalid_schema",
            messages.EX_INVALID_SCHEMA.format(reason=_reason(exc)),
            messages.EX_INVALID_SCHEMA_HINT,
            schema=schema_rel,
        )
    # The format checker is on so that impossible dates are rejected, as in the B1 tests.
    return cls(schema, format_checker=FormatChecker(formats=CHECKED_FORMATS)), None


def check_example(
    path: Path, example_rel: str, schema_rel: str, validator: Validator
) -> list[Problem]:
    try:
        document = _parse(path)
    except (
        OSError,
        UnicodeDecodeError,
        ValueError,
        yaml.YAMLError,
        RecursionError,
    ) as exc:
        # ValueError: JSON syntax and PyYAML's impossible dates.
        return [_unreadable_example(example_rel, schema_rel, _reason(exc))]
    try:
        errors = sorted(validator.iter_errors(document), key=error_order)
    except RecursionError:
        # A deeply nested document, or a schema whose references loop (`{"$ref": "#"}`).
        reason = messages.EX_TOO_DEEP_TO_VALIDATE
        return [_unreadable_example(example_rel, schema_rel, reason)]
    except Unresolvable as exc:
        # Lazy: a reference is only resolved when an example reaches it, so this can appear on
        # any example of the schema, not only the first. A dangling reference in a branch that
        # no example reaches is never found: this check is not exhaustive.
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


def _unreadable_example(example_rel: str, schema_rel: str, reason: str) -> Problem:
    return Problem(
        "unreadable_example",
        messages.EX_UNREADABLE_EXAMPLE.format(reason=reason),
        messages.EX_UNREADABLE_EXAMPLE_HINT,
        example=example_rel,
        schema=schema_rel,
    )


def _reason(exc: BaseException) -> str:
    """Why a file could not be used, in words for the report."""
    if isinstance(exc, RecursionError):
        return messages.EX_NESTED_TOO_DEEP
    if isinstance(exc, SchemaError):
        return _short(exc.message)
    if (
        isinstance(exc, yaml.constructor.ConstructorError)
        and exc.context is None
        and exc.problem_mark is not None
    ):
        # A repeated key: say where, without PyYAML's "<unicode string>" and echoed source line.
        mark = exc.problem_mark
        return f"{exc.problem} (line {mark.line + 1}, column {mark.column + 1})"
    return _one_line(exc)


def _parse(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in YAML_SUFFIXES:
        # The value is used exactly as parsed: an unquoted date stays a date, and B1 rejects it.
        return yaml.load(text, Loader=_UniqueKeyLoader)  # noqa: S506  (a SafeLoader subclass)
    return json.loads(
        text, object_pairs_hook=_unique_keys, parse_constant=_refuse_constant
    )


def _unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """JSON objects: a repeated key would silently keep only its last value, so refuse it."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(messages.EX_DUPLICATE_KEY.format(key=key))
        result[key] = value
    return result


def _refuse_constant(name: str) -> Any:
    """`NaN`, `Infinity` and `-Infinity` are accepted by Python's parser but are not JSON."""
    raise ValueError(messages.EX_NOT_STRICT_JSON.format(value=name))


class _UniqueKeyLoader(yaml.SafeLoader):
    """A SafeLoader that refuses a key repeated in one mapping (PyYAML keeps the last silently)."""


def _construct_unique_mapping(
    loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    seen: set[Any] = set()
    for key_node, _ in node.value:
        if key_node.tag == "tag:yaml.org,2002:merge":
            continue  # `<<: *anchor` merges are not repeated keys
        key = loader.construct_object(key_node, deep=deep)
        try:
            repeated = key in seen
            seen.add(key)
        except TypeError:
            continue  # an unhashable key: the base constructor reports it
        if repeated:
            raise yaml.constructor.ConstructorError(
                None,
                None,
                messages.EX_DUPLICATE_KEY.format(key=key),
                key_node.start_mark,
            )
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


def _place(location: tuple[str | int, ...]) -> str:
    return messages.where(location) if location else messages.EX_PLACE_DOCUMENT


def _one_line(exc: BaseException) -> str:
    return _short(" ".join(str(exc).split()))


def _short(text: str) -> str:
    return text if len(text) <= MAX_DETAIL else text[: MAX_DETAIL - 1] + "…"

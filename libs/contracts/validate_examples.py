"""Validate every contract example against its schema (PRD B.0 rule 1, E1 "Contract" level).

Run from the repository root:  python libs/contracts/validate_examples.py

`contracts/<name>.v<N>.schema.json` is matched with the folder `contracts/examples/<name>.v<N>/`,
whose top-level JSON and YAML files are its examples. Exit codes: 0 when every example passes,
1 when any problem is found, 2 for a usage error or a missing contracts folder. Read-only:
`--check` and `--dry-run` behave the same. What is and is not checked: libs/contracts/README.md.

This is not the B1 package validator (`validate.py`), which also checks course-level rules.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __name__ == "__main__" and not __package__:
    # Run as a script, Python puts this folder first on sys.path. Its files (schema.py,
    # config.py, ...) could then shadow other modules, and the `contracts` package could not be
    # imported. Replace that entry with `libs/` so imports work as they do under pytest and mypy.
    _HERE = Path(__file__).resolve().parent
    sys.path[:] = [p for p in sys.path if p and Path(p).resolve() != _HERE]
    sys.path.insert(0, str(_HERE.parent))

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from collections.abc import Sequence  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from typing import Any  # noqa: E402

import yaml  # noqa: E402
from jsonschema import Draft202012Validator, FormatChecker  # noqa: E402
from jsonschema.exceptions import SchemaError  # noqa: E402
from jsonschema.protocols import Validator  # noqa: E402
from jsonschema.validators import validator_for  # noqa: E402

from contracts import messages  # noqa: E402
from contracts.schema import _order as error_order  # noqa: E402

DEFAULT_CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts"
SCHEMA_NAME = re.compile(
    r"^(?P<stem>[a-z0-9]+(?:-[a-z0-9]+)*\.v[1-9][0-9]*)\.schema\.json$"
)
SCHEMA_GLOB = "*.schema.json"
EXAMPLE_SUFFIXES = frozenset({".json", ".yaml", ".yml"})
YAML_SUFFIXES = frozenset({".yaml", ".yml"})
# A schema error can repeat a whole document; keep the report readable.
MAX_DETAIL = 300


@dataclass(frozen=True)
class ContractCase:
    """One versioned schema and the folder where its examples must be."""

    schema_path: Path
    example_dir: Path


@dataclass(frozen=True)
class Problem:
    """One thing that is wrong. `example` and `schema` are repository-relative paths."""

    code: str
    message: str
    hint: str
    example: str | None = None
    schema: str | None = None


@dataclass(frozen=True)
class ExampleReport:
    problems: tuple[Problem, ...] = ()
    passed: tuple[tuple[str, str], ...] = ()  # (example, schema)
    failed: tuple[str, ...] = ()  # examples that were read or validated and failed
    schema_count: int = 0
    # Every top-level example found, including those not validated because their schema could
    # not be loaded; those are in neither `passed` nor `failed`.
    example_count: int = 0

    @property
    def ok(self) -> bool:
        return not self.problems


def discover(contracts_dir: Path) -> list[ContractCase]:
    """The correctly named schemas in `contracts_dir`, each with its example folder."""
    cases = []
    for path in sorted(contracts_dir.glob(SCHEMA_GLOB)):
        match = SCHEMA_NAME.match(path.name)
        if match:
            folder = contracts_dir / "examples" / match["stem"]
            cases.append(ContractCase(schema_path=path, example_dir=folder))
    return cases


def validate_all(contracts_dir: Path) -> ExampleReport:
    """Check every schema and example in `contracts_dir`. Never raises for bad content."""
    root = contracts_dir.parent
    problems: list[Problem] = []
    passed: list[tuple[str, str]] = []
    failed: list[str] = []
    example_count = 0

    def rel(path: Path) -> str:
        return path.relative_to(root).as_posix()

    if not any(contracts_dir.glob(SCHEMA_GLOB)):
        problems.append(
            Problem(
                "no_schemas",
                messages.EX_NO_SCHEMAS.format(folder=rel(contracts_dir)),
                messages.EX_NO_SCHEMAS_HINT,
            )
        )

    cases = discover(contracts_dir)
    for case in cases:
        schema_rel = rel(case.schema_path)
        validator, schema_problem = _load_validator(case.schema_path, schema_rel)
        if schema_problem:
            problems.append(schema_problem)
        examples = _list_examples(case.example_dir)
        example_count += len(examples)
        if not examples:
            problems.append(
                Problem(
                    "missing_example",
                    messages.EX_MISSING_EXAMPLE.format(folder=rel(case.example_dir)),
                    messages.EX_MISSING_EXAMPLE_HINT,
                    schema=schema_rel,
                )
            )
        for path in examples:
            example_rel = rel(path)
            if validator is None:
                problems.append(
                    Problem(
                        "example_not_validated",
                        messages.EX_NOT_VALIDATED,
                        messages.EX_NOT_VALIDATED_HINT,
                        example=example_rel,
                        schema=schema_rel,
                    )
                )
                continue
            found = _check_example(path, example_rel, schema_rel, validator)
            if found:
                problems += found
                failed.append(example_rel)
            else:
                passed.append((example_rel, schema_rel))

    return ExampleReport(
        problems=tuple(problems),
        passed=tuple(passed),
        failed=tuple(failed),
        schema_count=len(cases),
        example_count=example_count,
    )


def _load_validator(
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


def _list_examples(folder: Path) -> list[Path]:
    """The top-level JSON/YAML entries in `folder`, sorted. Subfolders hold supporting files
    (B1's body files, checked by `validate_package`) and are ignored by design."""
    if not folder.is_dir():
        return []
    # Not `is_file()`: a broken link named *.json must be reported as unreadable, not skipped.
    return sorted(
        p
        for p in folder.iterdir()
        if not p.is_dir() and p.suffix.lower() in EXAMPLE_SUFFIXES
    )


def _check_example(
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
    errors = sorted(validator.iter_errors(document), key=error_order)
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


def _print_report(report: ExampleReport) -> None:
    for example, schema in report.passed:
        print(messages.EX_LINE_OK.format(example=example, schema=schema))
    for problem in report.problems:
        target = problem.example or problem.schema or "contracts"
        if problem.example and problem.schema:
            line = messages.EX_LINE_WITH_SCHEMA.format(
                target=target, schema=problem.schema, message=problem.message
            )
        else:
            line = messages.EX_LINE.format(target=target, message=problem.message)
        print(line, file=sys.stderr)
        print(messages.EX_LINE_HINT.format(hint=problem.hint), file=sys.stderr)
    # Found but neither passed nor failed: their schema could not be loaded.
    not_validated = report.example_count - len(report.passed) - len(report.failed)
    print(
        messages.EX_SUMMARY.format(
            examples=report.example_count,
            schemas=report.schema_count,
            passed=len(report.passed),
            failed=len(report.failed),
            not_validated=not_validated,
            problems=len(report.problems),
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate every contract example against its schema (PRD B.0, E1).",
        epilog="Exit codes: 0 all examples pass, 1 problems found, 2 usage error. "
        "Read-only: there is nothing to undo.",
    )
    parser.add_argument(
        "--contracts-dir",
        type=Path,
        default=DEFAULT_CONTRACTS_DIR,
        help="the contracts folder (default: the repository's contracts/)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="validate only (the default; nothing is written)",
    )
    mode.add_argument(
        "--dry-run", action="store_true", help="same as --check: this tool never writes"
    )
    args = parser.parse_args(argv)

    contracts_dir: Path = args.contracts_dir.resolve()
    if not contracts_dir.is_dir():
        missing = messages.EX_CONTRACTS_DIR_MISSING.format(folder=args.contracts_dir)
        line = messages.EX_LINE.format(target=args.contracts_dir, message=missing)
        hint = messages.EX_LINE_HINT.format(hint=messages.EX_CONTRACTS_DIR_MISSING_HINT)
        print(line, hint, sep="\n", file=sys.stderr)
        return 2
    report = validate_all(contracts_dir)
    _print_report(report)
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())

"""Validate every contract example against its schema (PRD B.0 rule 1, E1 "Contract" level).

Run from the repository root:  python libs/contracts/validate_examples.py

`contracts/<name>.v<N>.schema.json` is matched with the folder `contracts/examples/<name>.v<N>/`.
Every top-level file in that folder is an example and must be JSON or YAML. Files in subfolders
(B1's body files, for example) are supporting files: listed in the output, never validated here.
Nothing is skipped silently: a schema without an example, an example without a schema, a badly
named schema and an unsupported file are all errors.

Exit codes: 0 when every example passes, 1 when any problem is found, 2 for a usage error or a
missing contracts folder. The tool only reads files, so `--check` and `--dry-run` behave the same
and there is nothing to undo.

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
from collections.abc import Callable, Hashable, Sequence  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from typing import Any, NoReturn  # noqa: E402

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
    supporting: tuple[str, ...] = ()  # files in example subfolders, not validated here
    schema_count: int = 0
    # Every example found: each top-level example in an example folder, and each example file
    # placed directly in `contracts/examples/`. It includes those not validated because their
    # schema could not be loaded or no schema matches them (orphans); those are in neither
    # `passed` nor `failed`.
    example_count: int = 0

    @property
    def ok(self) -> bool:
        return not self.problems


class _UniqueKeyLoader(yaml.SafeLoader):
    """PyYAML's safe loader, but a key used twice in one mapping is an error, not overwritten."""

    def construct_mapping(
        self, node: yaml.MappingNode, deep: bool = False
    ) -> dict[Hashable, Any]:
        self.flatten_mapping(node)
        seen: set[Any] = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                duplicate = key in seen
            except TypeError:
                continue  # unhashable key: the base class reports it
            if duplicate:
                raise yaml.constructor.ConstructorError(
                    None,
                    None,
                    messages.EX_DUPLICATE_KEY.format(key=key),
                    key_node.start_mark,
                )
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


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
    supporting: list[str] = []
    example_count = 0

    def rel(path: Path) -> str:
        return path.relative_to(root).as_posix()

    schema_files = sorted(contracts_dir.glob(SCHEMA_GLOB))
    if not schema_files:
        problems.append(
            Problem(
                "no_schemas",
                messages.EX_NO_SCHEMAS.format(folder=rel(contracts_dir)),
                messages.EX_NO_SCHEMAS_HINT,
            )
        )
    for path in schema_files:
        if not SCHEMA_NAME.match(path.name):
            problems.append(
                Problem(
                    "unversioned_schema",
                    messages.EX_UNVERSIONED_SCHEMA,
                    messages.EX_UNVERSIONED_SCHEMA_HINT,
                    schema=rel(path),
                )
            )

    cases = discover(contracts_dir)
    for case in cases:
        schema_rel = rel(case.schema_path)
        validator, schema_problem = _load_validator(case.schema_path, schema_rel)
        if schema_problem:
            problems.append(schema_problem)
        examples, others, nested = _list_example_folder(case.example_dir)
        example_count += len(examples)
        supporting += [rel(p) for p in nested]
        for path in others:
            problems.append(
                Problem(
                    "unsupported_example",
                    messages.EX_UNSUPPORTED_EXAMPLE,
                    messages.EX_UNSUPPORTED_EXAMPLE_HINT,
                    example=rel(path),
                    schema=schema_rel,
                )
            )
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

    expected = {c.example_dir.name for c in cases}
    problems += _orphans(contracts_dir, expected, rel)
    # Orphan folders are not validated, but their examples were found, so they are counted.
    for folder in _orphan_folders(contracts_dir, expected):
        example_count += len(_list_example_folder(folder)[0])
    example_count += len(_loose_examples(contracts_dir))
    return ExampleReport(
        problems=tuple(problems),
        passed=tuple(passed),
        failed=tuple(failed),
        supporting=tuple(sorted(supporting)),
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


def _list_example_folder(folder: Path) -> tuple[list[Path], list[Path], list[Path]]:
    """(examples, unsupported top-level files, files in subfolders), each sorted."""
    if not folder.is_dir():
        return [], [], []
    examples: list[Path] = []
    others: list[Path] = []
    nested: list[Path] = []
    for path in sorted(folder.iterdir()):
        if path.is_dir():
            nested += sorted(p for p in path.rglob("*") if p.is_file())
        elif path.suffix.lower() in EXAMPLE_SUFFIXES:
            examples.append(path)
        else:
            others.append(path)
    return examples, others, nested


def _check_example(
    path: Path, example_rel: str, schema_rel: str, validator: Validator
) -> list[Problem]:
    try:
        document = _parse(path)
    except (OSError, UnicodeDecodeError, ValueError, yaml.YAMLError) as exc:
        # ValueError: JSON syntax, duplicate JSON keys, and PyYAML's impossible dates.
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
        return yaml.load(
            text, Loader=_UniqueKeyLoader
        )  # a SafeLoader subclass: no arbitrary objects
    return json.loads(
        text, object_pairs_hook=_unique_json_object, parse_constant=_reject_constant
    )


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(messages.EX_DUPLICATE_KEY.format(key=key))
        result[key] = value
    return result


def _reject_constant(constant: str) -> NoReturn:
    # Python's json module accepts NaN, Infinity and -Infinity by default; JSON (RFC 8259) does
    # not, so another reader of the contract could reject an example this tool let through.
    raise ValueError(messages.EX_NON_STANDARD_JSON.format(constant=constant))


def _orphans(
    contracts_dir: Path, expected: set[str], rel: Callable[[Path], str]
) -> list[Problem]:
    examples_dir = contracts_dir / "examples"
    if not examples_dir.is_dir():
        return []
    problems = []
    for path in sorted(examples_dir.iterdir()):
        if path.is_dir() and path.name in expected:
            continue
        stem = path.name if path.is_dir() else path.stem
        problems.append(
            Problem(
                "orphan_example",
                messages.EX_ORPHAN_EXAMPLE.format(
                    schema=f"{rel(contracts_dir)}/{stem}.schema.json"
                ),
                messages.EX_ORPHAN_EXAMPLE_HINT,
                example=rel(path),
            )
        )
    return problems


def _orphan_folders(contracts_dir: Path, expected: set[str]) -> list[Path]:
    """The folders in `contracts/examples/` that no schema matches, sorted."""
    examples_dir = contracts_dir / "examples"
    if not examples_dir.is_dir():
        return []
    return [
        path
        for path in sorted(examples_dir.iterdir())
        if path.is_dir() and path.name not in expected
    ]


def _loose_examples(contracts_dir: Path) -> list[Path]:
    """Example files placed directly in `contracts/examples/` (always orphans), sorted."""
    examples_dir = contracts_dir / "examples"
    if not examples_dir.is_dir():
        return []
    return [
        path
        for path in sorted(examples_dir.iterdir())
        if path.is_file() and path.suffix.lower() in EXAMPLE_SUFFIXES
    ]


def _place(location: tuple[str | int, ...]) -> str:
    return messages.where(location) if location else messages.EX_PLACE_DOCUMENT


def _one_line(exc: BaseException) -> str:
    return _short(" ".join(str(exc).split()))


def _short(text: str) -> str:
    return text if len(text) <= MAX_DETAIL else text[: MAX_DETAIL - 1] + "…"


def _print_report(report: ExampleReport) -> None:
    for example, schema in report.passed:
        print(messages.EX_LINE_OK.format(example=example, schema=schema))
    if report.supporting:
        print(messages.EX_SUPPORTING.format(count=len(report.supporting)))
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
    # Found but neither passed nor failed: a broken schema, or no schema (orphans).
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
        print(
            messages.EX_LINE.format(
                target=args.contracts_dir,
                message=messages.EX_CONTRACTS_DIR_MISSING.format(
                    folder=args.contracts_dir
                ),
            ),
            file=sys.stderr,
        )
        print(
            messages.EX_LINE_HINT.format(hint=messages.EX_CONTRACTS_DIR_MISSING_HINT),
            file=sys.stderr,
        )
        return 2
    report = validate_all(contracts_dir)
    _print_report(report)
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())

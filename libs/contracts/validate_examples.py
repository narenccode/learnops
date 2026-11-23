"""Validate every contract example against its schema (PRD B.0 rule 1, E1 "Contract" level).

Run from the repository root:  python libs/contracts/validate_examples.py

`contracts/<name>.v<N>.schema.json` is matched with the top-level JSON and YAML files of
`contracts/examples/<name>.v<N>/` and with the flat files
`contracts/examples/<name>.v<N>.<suffix>.json` (or .yaml, .yml). Each schema and its examples are
checked by the engine, `example_check.py`. Exit codes: 0 when every example passes, 1 when any
problem is found (including an example no schema takes, and a file that is not an example), 2 for a usage error or a missing contracts folder. Read-only: `--check` and
`--dry-run` behave the same. What is and is not checked: libs/contracts/README.md.

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
import re  # noqa: E402
from collections.abc import Callable, Sequence  # noqa: E402
from dataclasses import dataclass  # noqa: E402

from contracts import messages  # noqa: E402
from contracts.example_check import (  # noqa: E402
    EXAMPLE_SUFFIXES,
    Problem,
    check_schema_examples,
)

DEFAULT_CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts"
SCHEMA_NAME = re.compile(
    r"^(?P<stem>[a-z0-9]+(?:-[a-z0-9]+)*\.v[1-9][0-9]*)\.schema\.json$"
)
SCHEMA_GLOB = "*.schema.json"
# A flat example sits directly in contracts/examples/: `<name>.v<N>.<suffix>.<json|yaml|yml>`.
# The suffix is one segment, so the stem is always the first two dot-separated parts and a
# file of `x.v10` can never be read as an example of `x.v1`. The extension is matched in any case
# (like the folder layout); the stem and the suffix word stay lower case.
FLAT_EXAMPLE_NAME = re.compile(
    r"^(?P<stem>[a-z0-9]+(?:-[a-z0-9]+)*\.v[1-9][0-9]*)\.[a-z0-9]+(?:-[a-z0-9]+)*"
    r"\.(?i:json|yaml|yml)$"
)


@dataclass(frozen=True)
class ContractCase:
    """One versioned schema, its example folder and the stem that flat examples start with."""

    schema_path: Path
    example_dir: Path
    stem: str


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
            cases.append(ContractCase(path, folder, match["stem"]))
    return cases


def misnamed_schemas(contracts_dir: Path) -> list[Path]:
    """The `*.schema.json` files that do not follow `<name>.v<N>.schema.json`."""
    return [
        path
        for path in sorted(contracts_dir.glob(SCHEMA_GLOB))
        if not SCHEMA_NAME.match(path.name)
    ]


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

    for path in misnamed_schemas(contracts_dir):
        problems.append(
            Problem(
                "misnamed_schema",
                messages.EX_MISNAMED_SCHEMA.format(name=path.name),
                messages.EX_MISNAMED_SCHEMA_HINT,
                schema=rel(path),
            )
        )

    cases = discover(contracts_dir)
    for case in cases:
        schema_rel = rel(case.schema_path)
        examples = _list_examples(case)
        example_count += len(examples)
        problems += _unsupported_in_folder(case, rel)
        check = check_schema_examples(
            case.schema_path, schema_rel, [(path, rel(path)) for path in examples]
        )
        problems += check.problems
        if not examples:
            problems.append(
                Problem(
                    "missing_example",
                    messages.EX_MISSING_EXAMPLE.format(
                        folder=rel(case.example_dir), stem=case.stem
                    ),
                    messages.EX_MISSING_EXAMPLE_HINT,
                    schema=schema_rel,
                )
            )
        passed += [(example, schema_rel) for example in check.passed]
        failed += check.failed

    problems += _unmatched_entries(contracts_dir, cases, rel)

    return ExampleReport(
        problems=tuple(problems),
        passed=tuple(passed),
        failed=tuple(failed),
        schema_count=len(cases),
        example_count=example_count,
    )


def _list_examples(case: ContractCase) -> list[Path]:
    """The examples of one schema: the top-level JSON/YAML entries of its folder, then the flat
    files `<stem>.<suffix>.<ext>` next to the folder. Each group is sorted. Subfolders hold
    supporting files (B1's body files, checked by `validate_package`) and are ignored by design."""
    found: list[Path] = []
    folder = case.example_dir
    if folder.is_dir():
        # Not `is_file()`: a broken link named *.json must be reported as unreadable, not skipped.
        found += sorted(
            p
            for p in folder.iterdir()
            if not p.is_dir() and p.suffix.lower() in EXAMPLE_SUFFIXES
        )
    flat_dir = folder.parent
    if flat_dir.is_dir():
        found += sorted(
            p
            for p in flat_dir.iterdir()
            if not p.is_dir()
            and (m := FLAT_EXAMPLE_NAME.match(p.name))
            and m["stem"] == case.stem
        )
    return found


def _unsupported_in_folder(
    case: ContractCase, rel: Callable[[Path], str]
) -> list[Problem]:
    """Top-level files of a schema's example folder that are not .json, .yaml or .yml.

    Subfolders (B1's weeks/) and hidden files (.gitkeep) are not examples and are not reported."""
    if not case.example_dir.is_dir():
        return []
    return [
        Problem(
            "unsupported_file",
            messages.EX_UNSUPPORTED_FILE,
            messages.EX_UNSUPPORTED_FILE_HINT,
            example=rel(path),
            schema=rel(case.schema_path),
        )
        for path in sorted(case.example_dir.iterdir())
        if not path.is_dir()
        and not path.name.startswith(".")
        and path.suffix.lower() not in EXAMPLE_SUFFIXES
    ]


def _unmatched_entries(
    contracts_dir: Path, cases: Sequence[ContractCase], rel: Callable[[Path], str]
) -> list[Problem]:
    """What sits directly in contracts/examples/ and belongs to no schema: a folder with no
    schema of that name, a JSON or YAML file that is not `<stem>.<suffix>.<ext>` of a schema,
    and any other file. Each is reported, so no example is skipped without a word."""
    examples_dir = contracts_dir / "examples"
    if not examples_dir.is_dir():
        return []
    stems = {case.stem for case in cases}
    problems: list[Problem] = []
    for entry in sorted(examples_dir.iterdir()):
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            if entry.name not in stems:
                problems.append(
                    Problem(
                        "orphan_example_folder",
                        messages.EX_ORPHAN_FOLDER.format(name=entry.name),
                        messages.EX_ORPHAN_FOLDER_HINT,
                        example=rel(entry),
                    )
                )
        elif entry.suffix.lower() in EXAMPLE_SUFFIXES:
            match = FLAT_EXAMPLE_NAME.match(entry.name)
            if not (match and match["stem"] in stems):
                problems.append(
                    Problem(
                        "orphan_example",
                        messages.EX_ORPHAN_EXAMPLE,
                        messages.EX_ORPHAN_EXAMPLE_HINT,
                        example=rel(entry),
                    )
                )
        else:
            problems.append(
                Problem(
                    "unsupported_file",
                    messages.EX_UNSUPPORTED_FILE,
                    messages.EX_UNSUPPORTED_FILE_HINT,
                    example=rel(entry),
                )
            )
    return problems


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

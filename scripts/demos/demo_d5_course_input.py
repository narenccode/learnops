"""D5 demo: course input. The B8.2 sample course passes the B1 validator, and broken copies fail.

Run from the repository root:

    python scripts/demos/demo_d5_course_input.py            # the demo
    python scripts/demos/demo_d5_course_input.py --dry-run  # say what it would do; do nothing
    python scripts/demos/demo_d5_course_input.py --check    # run quietly; exit 0 = as expected

Steps:
  1. Validate the B8.2 sample course (or the package named in --config): no errors expected.
  2. Make broken copies in a temporary folder, one planted error each, and validate them: each must
     be rejected with the expected error code. The temporary folder is always removed.
  3. Validate every contract example (libs/contracts/validate_examples.py).

Undo: nothing to undo. The demo reads the repository and writes only to a temporary folder outside
it, which is removed when the demo ends, also after an error.

Exit codes (PRD OPS-05): 0 = everything as expected; 1 = a result was not as expected;
2 = the demo could not run (for example, a missing package or a bad --config file).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
# The repository has a data folder named contracts/ at its root. Put libs/ first so that
# `import contracts` finds the validator library, not that folder.
sys.path.insert(0, str(ROOT / "libs"))

from contracts import DirectorySource, validate_package  # noqa: E402

DEFAULT_PACKAGE = ROOT / "testdata" / "b8-2-sample-course" / "package"
EXAMPLES_VALIDATOR = ROOT / "libs" / "contracts" / "validate_examples.py"
LONG_MESSAGE = 240  # characters; longer messages are shortened on screen, and say so

Doc = dict[str, Any]

# --- all user-facing text in one place (root CLAUDE.md §6) ---------------------------------

TITLE = "LearnOps D5 demo: course input (B1 course package validator)"
STEP_VALID = "Step 1. Validate the course package: no errors expected"
STEP_PLANTED = "Step 2. Planted errors: each broken copy must be rejected"
STEP_EXAMPLES = "Step 3. Validate every contract example"
DRY_RUN_NOTE = "Dry run: nothing is created, validated or deleted."
DRY_RUN_PLAN = (
    "Would validate {package}; copy it to a temporary folder outside the repository once per "
    "planted error ({count} copies), validate each copy, then remove the folder; and run "
    "{examples}."
)
OK_VALID = "  RESULT: OK, no errors in the B1 checks that ran ({errors} errors)."
NOT_CHECKED = "  Rules not checked yet (listed, never hidden): {codes}"
BAD_VALID = (
    "  NOT AS EXPECTED: the package has {errors} error(s); the first is: {message}"
)
REJECTED = "  REJECTED as expected: {code} ({rule}) at {where}"
NOT_REJECTED = "  NOT AS EXPECTED: {result}; expected the error code {expected}."
MESSAGE = "    message: {message}"
FIX = "    fix:     {fix}"
SHORTENED = " … (shortened on screen)"
EXAMPLES_DONE = "  {summary}"
SUMMARY_OK = "D5 demo: everything as expected."
SUMMARY_BAD = (
    "D5 demo: {count} result(s) not as expected; see the lines marked NOT AS EXPECTED."
)
ERR_NO_PACKAGE = (
    "The package folder {path} does not exist. Run the demo from the repository root, or name "
    "an existing package in the --config file."
)
ERR_CONFIG = (
    "The --config file {path} could not be read: {reason}. Use a YAML file with one key, "
    "package, giving a package folder relative to the repository root."
)


# --- the planted errors ----------------------------------------------------------------------


@dataclass(frozen=True)
class Planted:
    title: str
    expected_code: str
    plant: Callable[[Doc, Path], None]


def _first_task(doc: Doc) -> Doc:
    """The first Assignment of the first week."""
    task: Doc = next(
        a for a in doc["sections"][0]["activities"] if a["type"] == "assignment"
    )
    return task


def _remove_task_body(doc: Doc, package: Path) -> None:
    (package / _first_task(doc)["body"]).unlink()


def _duplicate_idnumber(doc: Doc, package: Path) -> None:
    doc["sections"][1]["activities"][1]["idnumber"] = _first_task(doc)["idnumber"]


def _protected_idnumber(doc: Doc, package: Path) -> None:
    _first_task(doc)["idnumber"] = "final-project"


def _unknown_mode(doc: Doc, package: Path) -> None:
    doc["course"]["mode"] = "everything"


def _full_url_body(doc: Doc, package: Path) -> None:
    doc["sections"][0]["activities"][0]["body"] = (
        "https://example.org/weeks/01-guide.md"
    )


PLANTED = (
    Planted("A week's task file is missing", "body_file_missing", _remove_task_body),
    Planted(
        "Two activities share one idnumber", "duplicate_idnumber", _duplicate_idnumber
    ),
    Planted(
        "The package includes the protected final project (PRD B1.4)",
        "schema_not",
        _protected_idnumber,
    ),
    Planted("An unknown build mode", "schema_enum", _unknown_mode),
    Planted(
        "Media named by a full URL, not a relative path (PRD C-08)",
        "schema_pattern",
        _full_url_body,
    ),
)


# --- the steps ---------------------------------------------------------------------------------


def _say(quiet: bool, text: str = "") -> None:
    if not quiet:
        print(text)


def _short(text: str) -> str:
    return text if len(text) <= LONG_MESSAGE else text[:LONG_MESSAGE] + SHORTENED


def _validate_valid(package: Path, quiet: bool) -> int:
    report = validate_package(DirectorySource(package))
    if report.ok:
        _say(quiet, OK_VALID.format(errors=len(report.errors)))
        codes = ", ".join(i.code for i in report.not_checked) or "none"
        _say(quiet, NOT_CHECKED.format(codes=codes))
        return 0
    _say(
        quiet,
        BAD_VALID.format(errors=len(report.errors), message=report.errors[0].message),
    )
    return 1


def _validate_planted(package: Path, quiet: bool) -> int:
    failures = 0
    with tempfile.TemporaryDirectory(prefix="learnops-d5-") as tmp:
        for number, case in enumerate(PLANTED, start=1):
            copy = Path(tmp) / f"case-{number}"
            shutil.copytree(package, copy)
            course = copy / "course.yaml"
            doc: Doc = yaml.safe_load(course.read_text(encoding="utf-8"))
            case.plant(doc, copy)
            course.write_text(
                yaml.safe_dump(doc, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
            report = validate_package(DirectorySource(copy))
            codes = [e.code for e in report.errors]
            _say(quiet, f"\n{number}. {case.title}")
            if case.expected_code not in codes:
                failures += 1
                result = f"error codes {codes}" if codes else "the copy was accepted"
                _say(
                    quiet,
                    NOT_REJECTED.format(result=result, expected=case.expected_code),
                )
                continue
            error = report.errors[codes.index(case.expected_code)]
            where = ".".join(str(part) for part in error.location) or "(package)"
            _say(quiet, REJECTED.format(code=error.code, rule=error.rule, where=where))
            _say(quiet, MESSAGE.format(message=_short(error.message)))
            _say(quiet, FIX.format(fix=_short(error.fix_hint)))
    return failures


def _validate_examples(quiet: bool) -> int:
    done = subprocess.run(
        [sys.executable, str(EXAMPLES_VALIDATOR)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    lines = done.stdout.strip().splitlines()
    _say(
        quiet, EXAMPLES_DONE.format(summary=lines[-1] if lines else done.stderr.strip())
    )
    return 0 if done.returncode == 0 else 1


# --- command line ------------------------------------------------------------------------------


def _package_from_config(path: Path | None) -> Path:
    if path is None:
        return DEFAULT_PACKAGE
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        return ROOT / str(loaded["package"])
    except (OSError, yaml.YAMLError, KeyError, TypeError) as error:
        raise SystemExit(_error(ERR_CONFIG.format(path=path, reason=error)))


def _error(text: str) -> int:
    print(text, file=sys.stderr)
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="demo_d5_course_input",
        description="D5 demo: the B1 course package validator on the B8.2 sample course.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="print what the demo would do; change nothing",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="run quietly; exit 0 when every result is as expected, 1 when not",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="YAML file with one key, package: a package folder relative to the repository root",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    package = _package_from_config(args.config)
    if not (package / "course.yaml").is_file():
        return _error(ERR_NO_PACKAGE.format(path=package))
    quiet = bool(args.check)
    _say(quiet, TITLE)
    _say(quiet, "=" * len(TITLE))
    if args.dry_run:
        print(DRY_RUN_NOTE)
        print(
            DRY_RUN_PLAN.format(
                package=(
                    package.relative_to(ROOT)
                    if package.is_relative_to(ROOT)
                    else package
                ).as_posix(),
                count=len(PLANTED),
                examples=EXAMPLES_VALIDATOR.relative_to(ROOT).as_posix(),
            )
        )
        return 0
    _say(quiet, f"\n{STEP_VALID}")
    failures = _validate_valid(package, quiet)
    _say(quiet, f"\n{STEP_PLANTED}")
    failures += _validate_planted(package, quiet)
    _say(quiet, f"\n{STEP_EXAMPLES}")
    failures += _validate_examples(quiet)
    _say(quiet)
    _say(quiet, SUMMARY_OK if failures == 0 else SUMMARY_BAD.format(count=failures))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

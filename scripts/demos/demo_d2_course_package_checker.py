"""D2 demo: course-package checker. It runs the shared B1 validator on a course package.

Run from the repository root:

    python scripts/demos/demo_d2_course_package_checker.py check <package> --json
    python scripts/demos/demo_d2_course_package_checker.py check <package>            # plain text
    python scripts/demos/demo_d2_course_package_checker.py check <package> --dry-run  # plan only
    python scripts/demos/demo_d2_course_package_checker.py check <package> --check    # quiet

This is the `checker check <package> --json` command of the interim D2 demo (checker design §6.2),
written as demo code under scripts/demos/, like D5. It is NOT the Course Checker: it runs only the
B1 validator in libs/contracts. The CK-01 to CK-13 rules (FR-C-03) are Release 1 work and are
listed in the report as `not checked`, never as passed.

Options (PRD C-05, OPS-05; decision 0020 for --config):
  --json        print the report as JSON (the default is plain text)
  --dry-run     say what would be done; read nothing, validate nothing
  --check       run quietly; print nothing; the exit code is the answer
  --config F    YAML file whose keys are option names: package, json, dry-run, check.
                Precedence, strongest first: command-line flag, config file, environment
                variable, default. D2 reads no environment variable, so that step has nothing
                to apply.

Undo: nothing to undo. The command only reads the package folder and writes to standard output.

Exit codes (PRD OPS-05): 0 = no error finding; 1 = at least one error finding;
2 = the command could not run (missing package, bad option, unreadable or invalid --config).
`not checked` entries never change the exit code.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
# The repository has a data folder named contracts/ at its root. Put libs/ first so that
# `import contracts` finds the validator library, not that folder.
sys.path.insert(0, str(ROOT / "libs"))

from contracts import (  # noqa: E402
    DirectorySource,
    Issue,
    ValidationReport,
    validate_package,
)

CHECKER_VERSION = "0.1.0-d2-demo"
CK_RULES = tuple(f"CK-{number:02d}" for number in range(1, 14))
# The keys of a --config file are the option names. `package` is the one that takes a value.
CONFIG_KEYS: dict[str, type] = {
    "package": str,
    "json": bool,
    "dry-run": bool,
    "check": bool,
}

Doc = dict[str, Any]

# --- all user-facing text in one place (root CLAUDE.md §6) ---------------------------------

TITLE = "LearnOps D2 demo: course-package checker (B1 validator only)"
SCOPE_NOTE = (
    "Scope: the B1 validator only. The CK-01 to CK-13 rules are Release 1 and are listed as "
    "not checked."
)
DRY_RUN_PLAN = (
    "Dry run: nothing is read, validated or written. Would validate the package folder "
    "{package} with the B1 validator (libs/contracts) and print the report as {form}."
)
LINE_PACKAGE = "Package: {name}"
LINE_ERRORS = "Errors ({count}):"
LINE_NO_ERRORS = "Errors: none found by the B1 checks that ran."
LINE_ERROR = "  {number}. {code} ({rule}) at {where}"
LINE_MESSAGE = "     message: {message}"
LINE_FIX = "     fix:     {fix}"
LINE_NOT_CHECKED = (
    "Not checked ({count}; listed, never hidden): {rules} B1 rules and {ck} CK rules."
)
LINE_NOT_CHECKED_CODES = "  B1 rules not checked yet: {codes}"
LINE_SUMMARY = "Result: {errors} {error_word}, {not_checked} not checked"
WHERE_PACKAGE = "(whole package)"
REASON_B1_FAILED = "The package failed B1 validation, so no CK rule ran."
REASON_NOT_BUILT = (
    "D2 runs the B1 validator only; the CK rule engine is Release 1 (FR-C-03)."
)
ERR_NO_PACKAGE_ARG = (
    "No package folder was named. Give one, for example: check testdata/b8-2-sample-course/"
    "package --json (or set package: in the --config file)."
)
ERR_NO_PACKAGE = (
    "The package folder {path} does not exist or is not a folder. Name an existing course "
    "package folder."
)
ERR_CONFIG_READ = (
    "The --config file {path} could not be read: {reason}. Use a YAML file whose keys are "
    "option names ({keys})."
)
ERR_CONFIG_SHAPE = (
    "The --config file {path} must be a YAML mapping of option names ({keys}) to values, "
    "not {found}."
)
ERR_CONFIG_UNKNOWN = (
    "The --config file {path} has an unknown key: {key}. Allowed keys: {keys}."
)
ERR_CONFIG_TYPE = (
    "The --config file {path}: the key {key} must be {expected}, not {found}."
)
ERR_BOTH_MODES = (
    "--dry-run and --check cannot be used together (also when one of them comes from the "
    "--config file). Use one of them."
)


class UsageError(Exception):
    """The command cannot run; `main` prints the text and exits with code 2."""


# --- configuration ---------------------------------------------------------------------------


def load_config(path: Path) -> Doc:
    """Read a --config file. Unknown keys and wrong types are refused (exit code 2)."""
    keys = ", ".join(CONFIG_KEYS)
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        raise UsageError(
            ERR_CONFIG_READ.format(path=path, reason=error, keys=keys)
        ) from error
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise UsageError(
            ERR_CONFIG_SHAPE.format(path=path, keys=keys, found=type(loaded).__name__)
        )
    for key, value in loaded.items():
        if key not in CONFIG_KEYS:
            raise UsageError(ERR_CONFIG_UNKNOWN.format(path=path, key=key, keys=keys))
        expected = CONFIG_KEYS[key]
        if not isinstance(value, expected):
            raise UsageError(
                ERR_CONFIG_TYPE.format(
                    path=path,
                    key=key,
                    expected="true or false" if expected is bool else "text",
                    found=type(value).__name__,
                )
            )
    config: Doc = loaded
    return config


# --- the report ------------------------------------------------------------------------------


def _where(location: Sequence[str | int]) -> str:
    """A path inside course.yaml, written like the validator's own messages."""
    if not location:
        return WHERE_PACKAGE
    text = ""
    for part in location:
        text += f"[{part}]" if isinstance(part, int) else f".{part}" if text else part
    return text


def _issue(issue: Issue, layer: str) -> Doc:
    return {
        "layer": layer,
        "code": issue.code,
        "rule": issue.rule,
        "location": list(issue.location),
        "item": {"idnumber": issue.idnumber},
        "message": issue.message,
        "fix_hint": issue.fix_hint,
    }


def build_report(name: str, report: ValidationReport) -> Doc:
    """The JSON report, in the shape of checker design §3.6 as far as the B1 validator allows.

    `findings` are the validator's errors (severity `error`). `not_checked` holds, one entry per
    rule, the rules the validator did not run and the thirteen CK rules, which D2 does not run.
    One state only, named `not checked`. `summary` counts both lists, so a report is never
    read as "everything was checked".
    """
    findings: list[Doc] = []
    for issue in report.errors:
        entry = _issue(issue, "B1")
        entry["severity"] = "error"
        findings.append(entry)
    not_checked: list[Doc] = []
    for issue in report.not_checked:
        entry = _issue(issue, "B1")
        entry["reason"] = issue.message
        not_checked.append(entry)
    reason = REASON_B1_FAILED if report.errors else REASON_NOT_BUILT
    for rule in CK_RULES:
        not_checked.append(
            {
                "layer": "CK",
                "rule": rule,
                "location": [],
                "item": {"idnumber": None},
                "reason": reason,
            }
        )
    return {
        "checker_version": CHECKER_VERSION,
        "input": {"kind": "package", "name": name},
        "summary": {
            "errors": len(findings),
            "warnings": 0,
            "not_checked": len(not_checked),
        },
        "findings": findings,
        "not_checked": not_checked,
    }


def summary_line(report: Doc) -> str:
    """Always both counts; never the word "clean" (checker design §3.6, §12 item 20)."""
    errors = report["summary"]["errors"]
    return LINE_SUMMARY.format(
        errors=errors,
        error_word="error" if errors == 1 else "errors",
        not_checked=report["summary"]["not_checked"],
    )


def format_text(report: Doc) -> str:
    lines = [TITLE, SCOPE_NOTE, "", LINE_PACKAGE.format(name=report["input"]["name"])]
    findings: list[Doc] = report["findings"]
    if findings:
        lines.append(LINE_ERRORS.format(count=len(findings)))
        for number, finding in enumerate(findings, start=1):
            lines.append(
                LINE_ERROR.format(
                    number=number,
                    code=finding["code"],
                    rule=finding["rule"],
                    where=_where(finding["location"]),
                )
            )
            lines.append(LINE_MESSAGE.format(message=finding["message"]))
            lines.append(LINE_FIX.format(fix=finding["fix_hint"]))
    else:
        lines.append(LINE_NO_ERRORS)
    unchecked: list[Doc] = report["not_checked"]
    b1 = [entry["code"] for entry in unchecked if entry["layer"] == "B1"]
    lines.append(
        LINE_NOT_CHECKED.format(
            count=len(unchecked), rules=len(b1), ck=len(unchecked) - len(b1)
        )
    )
    if b1:
        lines.append(LINE_NOT_CHECKED_CODES.format(codes=", ".join(b1)))
    lines.extend(["", summary_line(report)])
    return "\n".join(lines)


# --- command line ------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="checker",
        description="D2 demo: the B1 course package validator as `checker check`.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser(
        "check", help="validate a course package folder with the B1 validator"
    )
    check.add_argument(
        "package",
        nargs="?",
        type=Path,
        help="the course package folder (or set package: in the --config file)",
    )
    check.add_argument("--json", action="store_true", help="print the report as JSON")
    check.add_argument(
        "--dry-run",
        action="store_true",
        help="print what would be done; read and validate nothing",
    )
    check.add_argument(
        "--check",
        action="store_true",
        help="run quietly; exit 0 when no error was found, 1 when one was",
    )
    check.add_argument(
        "--config",
        type=Path,
        help="YAML file whose keys are option names: package, json, dry-run, check",
    )
    return parser


def _resolve(args: argparse.Namespace) -> tuple[Path, bool, bool, bool]:
    """Apply the precedence: command-line flag, then --config, then the default.

    No environment variable is read. Flags only switch an option on, so a flag that is absent
    leaves the config value (or the default, false) in place.
    """
    config: Doc = load_config(args.config) if args.config else {}
    as_json = bool(args.json or config.get("json", False))
    dry_run = bool(args.dry_run or config.get("dry-run", False))
    quiet = bool(args.check or config.get("check", False))
    if dry_run and quiet:
        raise UsageError(ERR_BOTH_MODES)
    package: Path | None = args.package
    if package is None and "package" in config:
        package = ROOT / str(
            config["package"]
        )  # a config path is relative to the repository
    if package is None:
        raise UsageError(ERR_NO_PACKAGE_ARG)
    return package, as_json, dry_run, quiet


def _display_name(package: Path) -> str:
    """The package path relative to the repository when it is inside it, else the folder name.
    Never an absolute path: a report is meant to be shared."""
    resolved = package.resolve()
    if resolved.is_relative_to(ROOT):
        return resolved.relative_to(ROOT).as_posix()
    return resolved.name


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        package, as_json, dry_run, quiet = _resolve(args)
        if not package.is_dir():
            raise UsageError(ERR_NO_PACKAGE.format(path=package))
    except UsageError as error:
        print(error, file=sys.stderr)
        return 2
    if dry_run:
        form = "JSON" if as_json else "text"
        print(DRY_RUN_PLAN.format(package=package.as_posix(), form=form))
        return 0
    report = build_report(
        _display_name(package), validate_package(DirectorySource(package))
    )
    if not quiet:
        print(json.dumps(report, indent=2) if as_json else format_text(report))
    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

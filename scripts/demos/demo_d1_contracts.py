"""D1 demo: contract examples are checked against their JSON Schemas (PRD EXT-09, E1 "Contract").

Run from the repository root:

    python scripts/demos/demo_d1_contracts.py            # the demo
    python scripts/demos/demo_d1_contracts.py --dry-run  # say what it would do; do nothing
    python scripts/demos/demo_d1_contracts.py --check    # run quietly; exit 0 = as expected

Steps:
  1. Validate every contract example in the repository: all must pass.
  2. Copy the contracts folder to a temporary folder, break one example there, and validate the
     copy: the validator must reject it with a `[const]` schema violation.

Configuration: --config FILE (YAML). Accepted keys:

    contracts_dir: contracts   # the contracts folder; relative paths start at the repository root

Precedence: command-line option > YAML file > environment variable > default. The environment
variable is LEARNOPS_D1_CONTRACTS_DIR. No secrets belong in the YAML file.

Undo: nothing to undo. The demo never writes into the repository. The planted error is made in a
temporary copy, which is removed when the demo ends, also after an error.

Exit codes (PRD OPS-05): 0 = everything as expected; 1 = a result was not as expected;
2 = the demo could not run (for example, a bad --config file or a missing contracts folder).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_VALIDATOR = ROOT / "libs" / "contracts" / "validate_examples.py"

ENV_CONTRACTS_DIR = "LEARNOPS_D1_CONTRACTS_DIR"
DEFAULT_CONTRACTS_DIR = "contracts"
CONFIG_KEYS = {"contracts_dir": str}  # accepted keys and their types

# The example that gets the planted error, relative to the contracts folder, and the value that
# breaks it: the schema fixes `schema` to one constant, so any other value violates `const`.
PLANTED_EXAMPLE = Path("examples") / "lesson-manifest.v1" / "single-track.json"
PLANTED_VALUE = "learnops.lesson/v999"
EXPECTED_MARKERS = (PLANTED_EXAMPLE.name, "[const]")

# --- all user-facing text in one place (root CLAUDE.md §6) ---------------------------------

TITLE = "LearnOps D1 demo: contract examples checked against their schemas"
STEP_REAL = "Step 1. Validate the real repository examples: all must pass (exit 0)"
STEP_PLANTED = (
    "Step 2. Validate a copy with one planted error: must be rejected (exit 1)"
)
DRY_RUN_NOTE = "Dry run: nothing is created, validated or deleted."
DRY_RUN_PLAN = (
    "Would validate every contract example in {contracts} with {validator}; copy {contracts} "
    "to a temporary folder, set `schema` to {value} in the copy of {example}, validate the "
    "copy and expect exit 1 with a [const] violation; then remove the temporary folder."
)
REAL_OK = "  RESULT: OK, every real example passed (exit 0)."
REAL_BAD = (
    "  NOT AS EXPECTED: the real examples ended with exit {code}, expected 0. Fix the "
    "problems listed above, or run the validator directly to see them."
)
PLANTED_OK = (
    "  RESULT: REJECTED as expected (exit 1), and the [const] violation was reported."
)
PLANTED_BAD_CODE = (
    "  NOT AS EXPECTED: the planted copy ended with exit {code}, expected 1."
)
PLANTED_BAD_MARKER = (
    "  NOT AS EXPECTED: the validator output does not mention {marker}. The planted error "
    "was not reported the way this demo expects."
)
SUMMARY_OK = "D1 demo: everything as expected. Repository contracts were not modified."
SUMMARY_BAD = (
    "D1 demo: {count} result(s) not as expected; see the lines marked NOT AS EXPECTED."
)
ERR_NO_CONTRACTS = (
    "The contracts folder {path} does not exist. Run the demo from the repository root, or "
    "name an existing folder with --contracts-dir, the config file or {env}."
)
ERR_NO_PLANTED = (
    "The example {path} is not in the contracts folder, so the planted error cannot be made. "
    "Use a contracts folder that has it, such as the repository's contracts/."
)
ERR_CONFIG = (
    "The --config file {path} could not be used: {reason}. Use a YAML file with the optional "
    "key contracts_dir (a folder name, text)."
)
ERR_CONFIG_READ = "{error}"
ERR_CONFIG_NOT_MAPPING = (
    "the file must hold key: value lines, not a list or a single value"
)
ERR_CONFIG_UNKNOWN = "unknown key(s) {keys}; accepted keys: {accepted}"
ERR_CONFIG_TYPE = "the key {key} must be {expected}, found {found}"
ERR_CONFIG_EMPTY = "the key {key} must not be empty"
ERR_NO_YAML = (
    "PyYAML is not installed, and --config needs it. Run: python -m pip install -r "
    "requirements-dev.txt"
)
ERR_NO_VALIDATOR = "The validator {path} was not found. Run the demo from a full copy of the repository."
ERR_TEMP = (
    "Could not create a temporary folder: {reason}. Check that the system temporary "
    "folder (TMPDIR) exists, is writable and has free space."
)
ERR_COPY = (
    "Could not copy {source} to the temporary folder: {reason}. Check that every file in it "
    "is readable (including links) and that the temporary folder has free space."
)
ERR_PLANT = (
    "Could not plant the error in the copy of {example}: {reason}. Check that the file is "
    "valid JSON holding one object, and that the temporary folder is writable."
)
ERR_PLANT_NOT_OBJECT = "the file does not hold one JSON object"
ERR_VALIDATOR_START = (
    "Could not start the validator with {python}: {reason}. Check that this Python "
    "installation works."
)
ERR_VALIDATOR_CRASH = (
    "The validator could not run (exit {code}) on {folder}: {detail}. If a module is "
    "missing, run: python -m pip install -r requirements-dev.txt"
)
WARN_TEMP_LEFT = (
    "Warning: the temporary folder {path} could not be removed. It holds only a copy of "
    "the contracts; delete it by hand."
)
ERR_ENV_EMPTY = "{env} is set but empty. Unset it, or give it a folder name."


class DemoError(Exception):
    """The demo could not run (not a validation result); it exits with code 2."""


class ConfigError(DemoError):
    """A configuration problem the user can fix; the demo exits with code 2."""


# --- configuration -------------------------------------------------------------------------------


def load_config(path: Path) -> dict[str, Any]:
    """Read a YAML config file. Rejects unknown keys and wrong value types."""
    try:
        import yaml  # needed only with --config, so a missing PyYAML is reported, not a crash
    except ImportError as error:
        raise ConfigError(ERR_NO_YAML) from error
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        raise ConfigError(
            ERR_CONFIG.format(
                path=path, reason=ERR_CONFIG_READ.format(error=_one_line(error))
            )
        ) from error
    if loaded is None:  # an empty file means "no settings"
        return {}
    if not isinstance(loaded, dict):
        raise ConfigError(ERR_CONFIG.format(path=path, reason=ERR_CONFIG_NOT_MAPPING))
    unknown = sorted(str(key) for key in loaded if key not in CONFIG_KEYS)
    if unknown:
        reason = ERR_CONFIG_UNKNOWN.format(
            keys=", ".join(unknown), accepted=", ".join(CONFIG_KEYS)
        )
        raise ConfigError(ERR_CONFIG.format(path=path, reason=reason))
    for key, expected in CONFIG_KEYS.items():
        if key not in loaded:
            continue
        value = loaded[key]
        if not isinstance(value, expected):
            reason = ERR_CONFIG_TYPE.format(
                key=key, expected="text", found=type(value).__name__
            )
            raise ConfigError(ERR_CONFIG.format(path=path, reason=reason))
        if not value.strip():
            reason = ERR_CONFIG_EMPTY.format(key=key)
            raise ConfigError(ERR_CONFIG.format(path=path, reason=reason))
    return loaded


def resolve_contracts_dir(
    cli_value: str | None, config: dict[str, Any], env: dict[str, str]
) -> Path:
    """Precedence: command-line option > YAML > environment variable > default."""
    if cli_value is not None:
        chosen = cli_value
    elif "contracts_dir" in config:
        chosen = config["contracts_dir"]
    elif ENV_CONTRACTS_DIR in env:
        chosen = env[ENV_CONTRACTS_DIR]
        if not chosen.strip():
            raise ConfigError(ERR_ENV_EMPTY.format(env=ENV_CONTRACTS_DIR))
    else:
        chosen = DEFAULT_CONTRACTS_DIR
    path = Path(chosen)
    return path if path.is_absolute() else ROOT / path


# --- the steps -----------------------------------------------------------------------------------


def _one_line(error: object) -> str:
    return " ".join(str(error).split())


def _short(text: str, limit: int = 300) -> str:
    return text if len(text) <= limit else text[:limit] + " …"


def _say(quiet: bool, text: str = "") -> None:
    if not quiet:
        print(text)


def _run_validator(contracts_dir: Path) -> tuple[int, str]:
    """Run the examples validator on `contracts_dir`. It is read-only (`--check`).

    Returns (exit code, output) for 0 (all pass) and 1 (problems found): those are results the
    demo judges. Anything else means the validator itself did not run, which raises DemoError.
    """
    try:
        done = subprocess.run(
            [
                sys.executable,
                str(EXAMPLES_VALIDATOR),
                "--contracts-dir",
                str(contracts_dir),
                "--check",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as error:
        reason = _one_line(error)
        raise DemoError(
            ERR_VALIDATOR_START.format(python=sys.executable, reason=reason)
        ) from error
    output = done.stdout + done.stderr
    # Exit 2 is the validator's usage error; a negative code is a signal; a Python traceback
    # also exits 1, which must not pass for "problems found".
    if done.returncode not in (0, 1) or "Traceback (most recent call last)" in output:
        lines = [line for line in output.splitlines() if line.strip()]
        detail = _one_line(lines[-1]) if lines else "no output"
        raise DemoError(
            ERR_VALIDATOR_CRASH.format(
                code=done.returncode, folder=_display(contracts_dir), detail=detail
            )
        )
    return done.returncode, output


def _step_real(contracts_dir: Path, quiet: bool) -> int:
    code, output = _run_validator(contracts_dir)
    _say(quiet, output.rstrip())
    if code == 0:
        _say(quiet, REAL_OK)
        return 0
    # Failures are always shown, also under --check: the output explains the exit code.
    if quiet:
        lines = [line for line in output.splitlines() if not line.startswith("OK ")]
        print("\n".join(lines), file=sys.stderr)
    print(REAL_BAD.format(code=code), file=sys.stderr if quiet else sys.stdout)
    return 1


def _plant_error(copy: Path) -> None:
    path = copy / PLANTED_EXAMPLE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise TypeError(ERR_PLANT_NOT_OBJECT)
        data["schema"] = PLANTED_VALUE
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, TypeError) as error:  # ValueError: bad JSON or UTF-8
        reason = _one_line(error)
        raise DemoError(
            ERR_PLANT.format(example=PLANTED_EXAMPLE.as_posix(), reason=reason)
        ) from error


def _step_planted(contracts_dir: Path, quiet: bool) -> int:
    # The temporary folder is removed on exit, also after an error. If removing it fails, the
    # result of the demo still counts and a warning says where the folder is.
    try:
        temp = tempfile.TemporaryDirectory(
            prefix="learnops-d1-", ignore_cleanup_errors=True
        )
    except OSError as error:
        raise DemoError(ERR_TEMP.format(reason=_one_line(error))) from error
    with temp as tmp:
        copy = Path(tmp) / contracts_dir.name
        try:
            shutil.copytree(contracts_dir, copy)  # shutil.Error is an OSError
        except OSError as error:
            raise DemoError(
                ERR_COPY.format(
                    source=_display(contracts_dir), reason=_short(_one_line(error))
                )
            ) from error
        _plant_error(copy)
        code, output = _run_validator(copy)
    if Path(tmp).exists():
        print(WARN_TEMP_LEFT.format(path=tmp), file=sys.stderr)
    # Quote the validator's lines, without the passing ones, to keep the screen short.
    shown = [line for line in output.splitlines() if not line.startswith("OK ")]
    _say(quiet, "\n".join(shown))
    problems = []
    if code != 1:
        problems.append(PLANTED_BAD_CODE.format(code=code))
    problems += [
        PLANTED_BAD_MARKER.format(marker=marker)
        for marker in EXPECTED_MARKERS
        if marker not in output
    ]
    if not problems:
        _say(quiet, PLANTED_OK)
        return 0
    stream = sys.stderr if quiet else sys.stdout
    for line in problems:
        print(line, file=stream)
    return len(problems)


# --- command line --------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="demo_d1_contracts",
        description="D1 demo: contract examples checked against their JSON Schemas.",
        epilog="Exit codes: 0 as expected, 1 a result was not as expected, 2 the demo could "
        "not run. Nothing to undo: the planted error lives in a temporary copy that is "
        "removed when the demo ends.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="print what the demo would do; create, validate and delete nothing",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="run quietly; exit 0 when every result is as expected, 1 when not",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="YAML file; accepted key: contracts_dir (a contracts folder)",
    )
    parser.add_argument(
        "--contracts-dir",
        help=f"the contracts folder (default {DEFAULT_CONTRACTS_DIR}/; also the config key "
        f"contracts_dir or {ENV_CONTRACTS_DIR}); relative paths start at the repository root",
    )
    return parser


def _error(text: str) -> int:
    print(text, file=sys.stderr)
    return 2


def _display(path: Path) -> str:
    return (path.relative_to(ROOT) if path.is_relative_to(ROOT) else path).as_posix()


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config) if args.config else {}
        contracts_dir = resolve_contracts_dir(
            args.contracts_dir, config, dict(os.environ)
        )
    except ConfigError as error:
        return _error(str(error))
    if not contracts_dir.is_dir():
        return _error(
            ERR_NO_CONTRACTS.format(path=_display(contracts_dir), env=ENV_CONTRACTS_DIR)
        )
    if not (contracts_dir / PLANTED_EXAMPLE).is_file():
        return _error(ERR_NO_PLANTED.format(path=PLANTED_EXAMPLE.as_posix()))

    if not EXAMPLES_VALIDATOR.is_file():
        return _error(ERR_NO_VALIDATOR.format(path=_display(EXAMPLES_VALIDATOR)))

    quiet = bool(args.check)
    _say(quiet, TITLE)
    _say(quiet, "=" * len(TITLE))
    if args.dry_run:
        print(DRY_RUN_NOTE)
        print(
            DRY_RUN_PLAN.format(
                contracts=_display(contracts_dir) + "/",
                validator=_display(EXAMPLES_VALIDATOR),
                value=PLANTED_VALUE,
                example=PLANTED_EXAMPLE.as_posix(),
            )
        )
        return 0
    failures = 0
    try:
        _say(quiet, f"\n{STEP_REAL}")
        failures = _step_real(contracts_dir, quiet)
        _say(quiet, f"\n{STEP_PLANTED}")
        failures += _step_planted(contracts_dir, quiet)
    except DemoError as error:
        print(error, file=sys.stderr)
        # A result already marked NOT AS EXPECTED is a genuine failure: keep exit 1 for it.
        # Exit 2 means the demo could not run at all.
        return 1 if failures else 2
    _say(quiet)
    _say(quiet, SUMMARY_OK if failures == 0 else SUMMARY_BAD.format(count=failures))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

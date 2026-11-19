"""H2 demo, Tier 1: the draft-grade write checks, run offline against a fake Moodle 5.3.

Run from the repository root:

    python scripts/demos/demo_h2_grading_tier1.py            # the demo
    python scripts/demos/demo_h2_grading_tier1.py --dry-run  # say what it would do; run nothing
    python scripts/demos/demo_h2_grading_tier1.py --check    # run quietly; exit 0 = as expected

This is NOT a live run. It runs the real libs/moodle_ws code (write_draft_grade) against the
offline fake in libs/moodle_ws/tests/source_fake.py, which behaves as the Moodle source says. It
never opens a network connection, reads no token and writes no grade to any Moodle.

The six cases (each prints the outcome and the rule behind it):
  1. The learner's state is `released`: refused (R3).
  2. The learner's state is `readyforrelease`: refused (R3).
  3. The state cannot be read (Moodle leaves `lastattempt` out): refused (R6).
  4. Marking workflow is off: refused.
  5. The write is silently ignored, so the read-back differs: NOT_VERIFIED (R1).
  6. A normal write: VERIFIED (R1).

Undo: nothing to undo. The demo keeps everything in memory and writes no file.

--config: a YAML file with one key, `moodle_version`, which must be "5.3" (Tier 1 is defined
against the Moodle 5.3 fake).

Exit codes (PRD OPS-05): 0 = every case as expected; 1 = a case was not as expected;
2 = the demo could not run (for example, a bad --config file).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
# The repository has a data folder named contracts/ at its root. Put libs/ first so that imports
# find the libraries, not that folder.
sys.path.insert(0, str(ROOT / "libs"))

from moodle_ws import (  # noqa: E402
    MoodleClient,
    Outcome,
    Site,
    SiteSettings,
    Token,
    write_draft_grade,
)
from moodle_ws.tests.source_fake import (  # noqa: E402
    ASSIGNMENT,
    LEARNER,
    SourceFakeMoodle,
)

SUPPORTED_VERSION = "5.3"
# Fake values only. The fake never sends anything, so this opens no connection (PRD C-06 is not
# touched: no real token is read).
DEMO_URL = "https://moodle53.demo.invalid"
DEMO_TOKEN = "demo0offline0only"
# A grade write that passes the library's own parameter checks (B4 §3). Test values only.
WRITE: dict[str, Any] = {
    "assignmentid": ASSIGNMENT,
    "userid": LEARNER,
    "grade": 84.5,
    "attemptnumber": 0,
    "addattempt": 0,
    "workflowstate": "readyforrelease",
    "applytoall": 0,
}
LONG_MESSAGE = 240  # characters; longer messages are shortened on screen, and say so

# --- all user-facing text in one place (root CLAUDE.md §6) ---------------------------------

TITLE = "LearnOps H2 demo, Tier 1: the draft-grade write checks (offline)"
LAST_LINE = "OFFLINE: against the Moodle 5.3 fake, not a live run"
DRY_RUN_NOTE = "Dry run: no case is run and nothing is sent."
DRY_RUN_PLAN = (
    "Would run {count} cases of write_draft_grade against the offline Moodle {version} fake, "
    "print each outcome with its rule, and send nothing to any Moodle."
)
DRY_RUN_CASE = "  {number}. {title}"
CASE_LINE = "Case {number}: {title} -> {outcome} ({rule}) write_sent={sent}"
MESSAGE = "    library says: {message}"
NOT_EXPECTED = "  NOT AS EXPECTED: wanted {wanted}, got {got}."
SHORTENED = " ... (shortened on screen)"
SUMMARY_OK = "Tier 1: all {count} cases as expected."
SUMMARY_BAD = (
    "Tier 1: {count} case(s) not as expected; see the lines marked NOT AS EXPECTED."
)
ERR_CONFIG = (
    "The --config file {path} could not be used: {reason}. Use a YAML file with one key, "
    'moodle_version, set to "5.3".'
)
REASON_VERSION = "moodle_version must be 5.3"

# --- the six cases -------------------------------------------------------------------------


@dataclass(frozen=True)
class Case:
    title: str
    rule: str
    expected: Outcome
    fake: Callable[[str], SourceFakeMoodle]
    # What the caller tells the library the assignment's maximum grade is, and the grade sent.
    max_grade: int = 100
    grade: float = 84.5


def _locked(state: str) -> Callable[[str], SourceFakeMoodle]:
    return lambda version: SourceFakeMoodle(version, state=state, grade="70.00000")


CASES = (
    Case(
        "learner already in state `released`",
        "R3",
        Outcome.REFUSED_LOCKED,
        _locked("released"),
    ),
    Case(
        "learner already in state `readyforrelease`",
        "R3",
        Outcome.REFUSED_LOCKED,
        _locked("readyforrelease"),
    ),
    Case(
        "state cannot be read (`lastattempt` missing)",
        "R6",
        Outcome.REFUSED_STATE_UNKNOWN,
        lambda version: SourceFakeMoodle(version, show_lastattempt=False),
    ),
    Case(
        "marking workflow is off (state `notgraded`)",
        "workflow off",
        Outcome.REFUSED_WORKFLOW_OFF,
        lambda version: SourceFakeMoodle(version, state="notgraded"),
    ),
    # The caller says the maximum is 100 while the fake's assignment maximum is 10. The library
    # accepts 50, the fake silently ignores it (as the Moodle source does, lab check 15), and the
    # read-back then does not match. In real use the caller reads the real maximum (lab check 2).
    Case(
        "write silently ignored, so the read-back differs",
        "R1",
        Outcome.NOT_VERIFIED,
        lambda version: SourceFakeMoodle(version, max_grade=Decimal(10)),
        grade=50,
    ),
    Case(
        "normal write, read back and matched",
        "R1",
        Outcome.VERIFIED,
        lambda version: SourceFakeMoodle(version),
    ),
)

# --- the steps -----------------------------------------------------------------------------


def _say(quiet: bool, text: str = "") -> None:
    if not quiet:
        print(text)


def _short(text: str) -> str:
    return text if len(text) <= LONG_MESSAGE else text[:LONG_MESSAGE] + SHORTENED


def _settings() -> SiteSettings:
    return SiteSettings(Site.MOODLE53, SUPPORTED_VERSION, DEMO_URL, Token(DEMO_TOKEN))


def _run_cases(quiet: bool) -> int:
    failures = 0
    for number, case in enumerate(CASES, start=1):
        client = MoodleClient(_settings(), case.fake(SUPPORTED_VERSION))
        result = write_draft_grade(
            client, {**WRITE, "grade": case.grade}, case.max_grade
        )
        _say(
            quiet,
            CASE_LINE.format(
                number=number,
                title=case.title,
                outcome=result.outcome.name,
                rule=case.rule,
                sent=result.write_sent,
            ),
        )
        _say(quiet, MESSAGE.format(message=_short(result.message)))
        if result.outcome is not case.expected:
            failures += 1
            _say(
                quiet,
                NOT_EXPECTED.format(wanted=case.expected.name, got=result.outcome.name),
            )
    return failures


# --- command line --------------------------------------------------------------------------


def _error(text: str) -> int:
    print(text, file=sys.stderr)
    return 2


def _check_config(path: Path | None) -> None:
    if path is None:
        return
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        if str(loaded["moodle_version"]) != SUPPORTED_VERSION:
            raise ValueError(REASON_VERSION)
    except (OSError, yaml.YAMLError, KeyError, TypeError, ValueError) as error:
        raise SystemExit(_error(ERR_CONFIG.format(path=path, reason=error)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="demo_h2_grading_tier1",
        description="H2 demo, Tier 1: the draft-grade write checks against an offline fake.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="print what the demo would do; run no case",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="run quietly; exit 0 when every case is as expected, 1 when not",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help='YAML file with one key, moodle_version: "5.3"',
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _check_config(args.config)
    quiet = bool(args.check)
    _say(quiet, TITLE)
    _say(quiet, "=" * len(TITLE))
    if args.dry_run:
        print(DRY_RUN_NOTE)
        print(DRY_RUN_PLAN.format(count=len(CASES), version=SUPPORTED_VERSION))
        for number, case in enumerate(CASES, start=1):
            print(DRY_RUN_CASE.format(number=number, title=case.title))
        return 0
    _say(quiet)
    failures = _run_cases(quiet)
    _say(quiet)
    _say(
        quiet,
        (
            SUMMARY_OK.format(count=len(CASES))
            if failures == 0
            else SUMMARY_BAD.format(count=failures)
        ),
    )
    _say(quiet, LAST_LINE)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

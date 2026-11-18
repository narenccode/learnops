"""H6 demo, Tier 3: the library's own checks on the site's answers. A dry run: nothing is sent.

Run from the repository root:

    python scripts/demos/demo_h6_dry_run.py --offline                  # against the built-in fake
    python scripts/demos/demo_h6_dry_run.py --config h6.yaml --out D:/notes/h6.json   # the lab
    python scripts/demos/demo_h6_dry_run.py --dry-run                  # list the cases; make no call
    python scripts/demos/demo_h6_dry_run.py --offline --check          # quiet; exit 0 = as expected

For each test learner it runs the library's write_draft_grade (libs/moodle_ws) on the real answers.
The library does all its pre-write checks. If they all pass, the library tries the write and the
demo's read-only connection (scripts/demos/readonly_connection.py) refuses it BEFORE anything is
sent. "WOULD WRITE" is printed only when a write attempt really reached, and was stopped by, that
connection. Nothing can write to Moodle, and the library is not changed.

Live mode needs MOODLE53_URL and MOODLE53_WS_TOKEN in the environment (B4 §1) and `course_id` in
the --config file. The token is never printed, logged or saved.

--config: a YAML file with `course_id` (a whole number) and optionally `learners`, a mapping from
A, B, C, D to usernames (default learner-a to learner-d). --out PATH: save the full output as JSON;
the path must be OUTSIDE the repository.

Undo: nothing to undo. It only reads, and writes only the file named by --out.

Exit codes (PRD OPS-05): 0 = every expected result matched (in live mode a difference is a FINDING,
not a failure); 1 = a result was not as expected, a case could not run, or the stop was not what it
seemed; 2 = the demo could not run (missing settings, bad --config, an --out path inside the
repository).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

ROOT = Path(__file__).resolve().parents[2]
# The repository has a data folder named contracts/ at its root. Put libs/ first so that imports
# find the libraries, not that folder.
sys.path.insert(0, str(ROOT / "libs"))

from demo_fake_site import COURSE_ID as OFFLINE_COURSE_ID  # noqa: E402
from demo_live_common import (  # noqa: E402
    ERR_CONFIG,
    Connection,
    DemoError,
    Recorder,
    check_output_path,
    connect,
    course_id_from,
    describe,
    read_config,
)
from moodle_ws import (  # noqa: E402
    FunctionNotAllowed,
    MoodleClient,
    MoodleError,
    Outcome,
    write_draft_grade,
)

SAVE_GRADE: Final = "mod_assign_save_grade"
WOULD_WRITE: Final = "would_write"  # not a library outcome: the stop was reached

# --- all user-facing text in one place (root CLAUDE.md §6) ---------------------------------

TITLE = "LearnOps H6 demo, Tier 3: the library's checks on the site's answers (dry run)"
DRY_RUN_NOTE = "Dry run: no call is made and nothing is sent."
DRY_RUN_PLAN = (
    "Would read course {course} on {site}, run the library's write checks for these learners, "
    "and stop every write before it is sent:"
)
DRY_RUN_LINE = "  Learner {letter} ({username}): {what}"
COURSE_UNSET = "(set course_id in the --config file)"
CASE_LINE = "Case {letter}: {what} -> {verdict}"
CASE_LINE_OPEN = "Case {letter}: {what} -> library says: {verdict}"
DETAIL_STATE = "    submission status: {submission}, grading status: {grading}"
DETAIL_GRADE = "    placeholder grade {grade} of {maximum} (only to pass the library's checks; never sent)"
DETAIL_STOPPED = "    write attempt: stopped by the read-only connection"
DETAIL_NOT_REACHED = "    write attempt: none (refused by the library first)"
NOT_RUN = "NOT RUN: {reason}"
NOT_AS_EXPECTED = "  NOT AS EXPECTED: wanted {wanted}, got {got}."
FINDING = "  FINDING: {text}"
F_DIFFERS = "case {letter}: wanted {wanted}, got {got} (the plan's expected result differs here)"
F_GAP = (
    "the library allowed a write for a learner who has not submitted (submission status: "
    "{submission}): it decides from the grading state only, and a missing submission is the "
    "caller's decision (R10)"
)
UNEXPECTED = (
    "UNEXPECTED: the library refused the write without a write attempt reaching the read-only "
    "connection, so this is not shown as allowed"
)
SENT = "UNEXPECTED: a write was reported as sent. Stop and tell the guide."
SAVED = "Saved the full output to {path}"
NOT_SAVED = (
    "The output was not saved. Use --out PATH, outside the repository, to keep it."
)
SUMMARY_OK = "Tier 3: all expected results matched. Findings: {findings}."
SUMMARY_BAD = (
    "Tier 3: {count} case(s) not as expected or not run; see the lines marked NOT AS EXPECTED, "
    "NOT RUN or UNEXPECTED. Findings: {findings}."
)
COULD_NOT_START = "Tier 3 could not start: {reason}"
LAST_OFFLINE = "OFFLINE: built-in fake, not a live run. Nothing was sent and nothing was written to Moodle."
LAST_LIVE = "LIVE: reads only. Every write was stopped before sending; nothing was written to Moodle."
ERR_NO_COURSE = (
    "Live mode needs the course id. Put course_id in the --config file (the id from the "
    "'Test course ready' post in #112)."
)
REASON_LEARNERS = "learners must map A, B, C or D to a username"
NO_LEARNER = "learner {username!r} is not among the enrolled users"
NO_ASSIGNMENT = "no assignment with marking workflow {workflow} was found"

# How the library's outcomes read on screen.
VERDICTS: Final = {
    WOULD_WRITE: "WOULD WRITE readyforrelease: allowed",
    Outcome.REFUSED_LOCKED: "REFUSED: locked (R3)",
    Outcome.REFUSED_WORKFLOW_OFF: "REFUSED: workflow off",
    Outcome.REFUSED_STATE_UNKNOWN: "REFUSED: state unreadable (R6)",
    Outcome.REFUSED_OUT_OF_RANGE: "REFUSED: grade out of range (R9)",
    Outcome.ACCESS_DENIED: "REFUSED: access denied",
}


@dataclass(frozen=True)
class Case:
    letter: str
    what: str
    workflow: bool  # which assignment: marking workflow on or off
    expected: object | None  # None: the plan says to print what the library says


# The plan's table (H6), in its order.
CASES: Final = (
    Case("A", "Assignment 1, submitted, no grade yet, workflow on", True, WOULD_WRITE),
    Case(
        "B",
        "Assignment 1, submitted, already Ready for release with a grade",
        True,
        Outcome.REFUSED_LOCKED,
    ),
    Case(
        "D",
        "Assignment 2, marking workflow off, submitted",
        False,
        Outcome.REFUSED_WORKFLOW_OFF,
    ),
    Case("C", "Assignment 1, a draft, not submitted", True, None),
)


class _Watch:
    """Counts the write attempts that reach the transport. It sends nothing itself."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.save_attempts = 0

    def call(self, settings: Any, function: str, params: Mapping[str, Any]) -> Any:
        if function == SAVE_GRADE:
            self.save_attempts += 1
        return self._inner.call(settings, function, params)


@dataclass
class Session:
    recorder: Recorder
    quiet: bool
    offline: bool
    failures: int = 0
    findings: int = 0

    def say(self, text: str) -> None:
        self.recorder.line(text)
        if not self.quiet:
            print(text)

    def finding(self, text: str) -> None:
        self.findings += 1
        self.say(FINDING.format(text=text))


def _rows(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _verdict_text(verdict: object) -> str:
    return VERDICTS.get(verdict, str(getattr(verdict, "name", verdict)))  # type: ignore[arg-type]


def _read_site(
    client: MoodleClient, session: Session, course: int
) -> tuple[list[Any], dict[str, int]]:
    answer = client.call("mod_assign_get_assignments", {"courseids": [course]})
    session.recorder.note("mod_assign_get_assignments", answer)
    courses = _rows(answer.get("courses") if isinstance(answer, Mapping) else None)
    assignments = [a for c in courses for a in _rows(c.get("assignments"))]
    users = _rows(client.call("core_enrol_get_enrolled_users", {"courseid": course}))
    session.recorder.note("core_enrol_get_enrolled_users", users)
    return assignments, {u.get("username"): u.get("id") for u in users}


def _pick(assignments: list[Any], workflow: bool) -> dict[str, Any] | None:
    for row in assignments:
        if "markingworkflow" in row and bool(row["markingworkflow"]) == workflow:
            return dict(row)
    return None


def _state(client: MoodleClient, assign: int, user: int) -> tuple[str, str, int]:
    answer = client.call(
        "mod_assign_get_submission_status", {"assignid": assign, "userid": user}
    )
    last = answer.get("lastattempt") if isinstance(answer, Mapping) else None
    last = last if isinstance(last, Mapping) else {}
    submission = (
        last.get("submission") if isinstance(last.get("submission"), Mapping) else {}
    )
    attempt = submission.get("attemptnumber")
    return (
        str(submission.get("status") or "none"),
        str(last.get("gradingstatus", "unknown")),
        attempt if type(attempt) is int else 0,
    )


def _run_case(
    client: MoodleClient,
    watch: _Watch,
    session: Session,
    case: Case,
    assignment: dict[str, Any],
    user: int,
) -> object:
    """One learner: the library's checks, then the stop. Returns what the library said."""
    assign, maximum = assignment["id"], assignment.get("grade")
    submission, grading, attempt = _state(client, assign, user)
    session.say(DETAIL_STATE.format(submission=submission, grading=grading))
    grade = max(0, int(maximum // 2)) if isinstance(maximum, int | float) else 0
    params = {
        "assignmentid": assign,
        "userid": user,
        "grade": grade,
        "attemptnumber": attempt,
        "addattempt": 0,
        "workflowstate": "readyforrelease",
        "applytoall": 0,
    }
    before = watch.save_attempts
    verdict: object
    try:
        result = write_draft_grade(client, params, maximum)
    except FunctionNotAllowed:
        reached = watch.save_attempts > before
        verdict = WOULD_WRITE if reached else "unexpected"
    except MoodleError as error:
        verdict, reached = f"error: {error}", watch.save_attempts > before
    else:
        reached = False
        verdict = result.outcome
        if result.write_sent:
            session.say(SENT)
            session.failures += 1
    if verdict == WOULD_WRITE:
        session.say(DETAIL_GRADE.format(grade=grade, maximum=maximum))
    session.say(DETAIL_STOPPED if reached else DETAIL_NOT_REACHED)
    if verdict == "unexpected":
        session.say(UNEXPECTED)
        session.failures += 1
    if verdict == WOULD_WRITE and case.expected is None and submission != "submitted":
        session.finding(F_GAP.format(submission=submission))
    return verdict


def _case_lines(session: Session, case: Case, verdict: object) -> None:
    text = _verdict_text(verdict)
    template = CASE_LINE_OPEN if case.expected is None else CASE_LINE
    session.say(template.format(letter=case.letter, what=case.what, verdict=text))


def run_cases(
    client: MoodleClient,
    watch: _Watch,
    session: Session,
    course: int,
    learners: Mapping[str, str],
) -> None:
    assignments, users = _read_site(client, session, course)
    for case in CASES:
        username = learners.get(case.letter, f"learner-{case.letter.lower()}")
        assignment = _pick(assignments, case.workflow)
        reason = None
        if username not in users:
            reason = NO_LEARNER.format(username=username)
        elif assignment is None:
            reason = NO_ASSIGNMENT.format(workflow="on" if case.workflow else "off")
        if reason is not None or assignment is None:
            session.say(
                CASE_LINE.format(
                    letter=case.letter,
                    what=case.what,
                    verdict=NOT_RUN.format(reason=reason),
                )
            )
            session.failures += 1
            continue
        buffered = Session(Recorder(), True, session.offline)
        verdict = _run_case(client, watch, buffered, case, assignment, users[username])
        # The case line first, then its detail lines, as the screen should read.
        _case_lines(session, case, verdict)
        for line in buffered.recorder.lines:
            session.say(line)
        session.failures += buffered.failures
        session.findings += buffered.findings
        session.recorder.note(
            f"case {case.letter}", {"verdict": _verdict_text(verdict)}
        )
        _compare(session, case, verdict)


def _compare(session: Session, case: Case, verdict: object) -> None:
    if case.expected is None or verdict == case.expected:
        return
    wanted, got = _verdict_text(case.expected), _verdict_text(verdict)
    if session.offline:  # offline a difference is a bug in the demo or the library
        session.failures += 1
        session.say(NOT_AS_EXPECTED.format(wanted=wanted, got=got))
    else:  # live a difference is a finding (plan section 5)
        session.finding(F_DIFFERS.format(letter=case.letter, wanted=wanted, got=got))


# --- command line ------------------------------------------------------------------------------


def _error(text: str) -> int:
    print(text, file=sys.stderr)
    return 2


def _learners_from(config: Mapping[str, Any]) -> dict[str, str]:
    value = config.get("learners")
    if value is None:
        return {}
    ok = isinstance(value, dict) and all(
        k in ("A", "B", "C", "D") and isinstance(v, str) and v.strip()
        for k, v in value.items()
    )
    if not ok:
        raise DemoError(ERR_CONFIG.format(path="", reason=REASON_LEARNERS))
    return dict(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="demo_h6_dry_run",
        description="H6 demo, Tier 3: the library's write checks on the site's answers; nothing is sent.",
    )
    parser.add_argument(
        "--offline", action="store_true", help="use the built-in fake, not the lab"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="list the cases; make no call"
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="run quietly; exit 0 when as expected, 1 when not",
    )
    parser.add_argument(
        "--config", type=Path, help="YAML file: course_id, optionally learners"
    )
    parser.add_argument(
        "--out", type=Path, help="save the full output here (outside the repository)"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _main(args)
    except DemoError as error:
        return _error(str(error))


def _main(args: argparse.Namespace) -> int:
    config = read_config(args.config)
    course = course_id_from(config)
    learners = _learners_from(config)
    check_output_path(args.out)
    connection: Connection = connect(offline=args.offline)
    if course is None and args.offline:
        course = OFFLINE_COURSE_ID
    if args.dry_run:
        print(DRY_RUN_NOTE)
        print(
            DRY_RUN_PLAN.format(
                course=course if course is not None else COURSE_UNSET,
                site=describe(connection),
            )
        )
        for case in CASES:
            username = learners.get(case.letter, f"learner-{case.letter.lower()}")
            print(
                DRY_RUN_LINE.format(
                    letter=case.letter, username=username, what=case.what
                )
            )
        return 0
    if course is None:
        raise DemoError(ERR_NO_COURSE)
    session = Session(Recorder(), bool(args.check), connection.offline)
    session.say(TITLE)
    session.say("=" * len(TITLE))
    session.say(f"Connection: {describe(connection)}")
    session.say("")
    watch = _Watch(connection.transport)
    client = MoodleClient(connection.settings, watch)  # type: ignore[arg-type]
    try:
        run_cases(client, watch, session, course, learners)
    except MoodleError as error:
        session.say(COULD_NOT_START.format(reason=error))
        session.failures += 1
    summary = (
        SUMMARY_OK.format(findings=session.findings)
        if session.failures == 0
        else SUMMARY_BAD.format(count=session.failures, findings=session.findings)
    )
    last = LAST_OFFLINE if connection.offline else LAST_LIVE
    session.say("")
    if args.out is not None:
        session.recorder.lines += [summary, last]
        session.recorder.save(args.out)
        session.say(SAVED.format(path=args.out))
    else:
        session.say(NOT_SAVED)
    if not session.quiet:
        print(summary)
        print(last)
    return 0 if session.failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

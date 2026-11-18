"""H4 demo, Tier 2: the live read. Moodle 5.3's answers to our service account, read-only.

Run from the repository root:

    python scripts/demos/demo_h4_live_read.py --offline                 # against the built-in fake
    python scripts/demos/demo_h4_live_read.py --config h4.yaml --out D:/notes/h4.json   # the lab
    python scripts/demos/demo_h4_live_read.py --dry-run                 # list the calls; make none
    python scripts/demos/demo_h4_live_read.py --offline --check         # quiet; exit 0 = as expected

Live mode needs MOODLE53_URL and MOODLE53_WS_TOKEN in the environment (B4 §1) and `course_id` in the
--config file. The token is never printed, logged or saved. Everything goes through the library's
client and the demo's read-only connection (scripts/demos/readonly_connection.py), which sends only
the six read functions of PRD B4 §2: nothing in this script can write to Moodle.

Steps (plan H4): 1. a call with the token works and a function outside the six is refused;
2. course contents; 3. enrolled users; 4. assignment settings; 5. submissions and each learner's
status; 6. one submitted file. A live answer that differs from what the fake assumed is a FINDING,
not a failure. A step that fails is shown, and the others still run.

--config: a YAML file with one key, `course_id` (a whole number). --out PATH: save the full output as
JSON; the path must be OUTSIDE the repository.

Undo: nothing to undo. It only reads, and writes only the file named by --out.

Exit codes (PRD OPS-05): 0 = every step ran (findings do not count); 1 = a step failed;
2 = the demo could not run (missing settings, bad --config, an --out path inside the repository).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

import yaml

ROOT = Path(__file__).resolve().parents[2]
# The repository has a data folder named contracts/ at its root. Put libs/ first so that imports
# find the libraries, not that folder.
sys.path.insert(0, str(ROOT / "libs"))

from demo_fake_site import COURSE_ID as OFFLINE_COURSE_ID  # noqa: E402
from demo_live_common import (  # noqa: E402
    OUTPUT_INSIDE_REPOSITORY,
    Connection,
    DemoError,
    Recorder,
    connect,
    describe,
)
from moodle_ws import MoodleError  # noqa: E402

MAX_FILE_BYTES: Final = 1_000_000  # a safety limit on the one downloaded file

# The six read functions, in the order the steps use them (PRD B4 §2).
PLAN: Final = (
    ("core_course_get_courses_by_field", "find the course"),
    ("core_course_get_contents", "course contents"),
    ("core_enrol_get_enrolled_users", "enrolled users"),
    ("mod_assign_get_assignments", "assignment settings, including marking workflow"),
    ("mod_assign_get_submissions", "submissions"),
    (
        "mod_assign_get_submission_status",
        "each learner's submission and grading status",
    ),
)

# --- all user-facing text in one place (root CLAUDE.md §6) ---------------------------------

TITLE = "LearnOps H4 demo, Tier 2: the live read (read-only)"
DRY_RUN_NOTE = "Dry run: no call is made and nothing is sent."
DRY_RUN_PLAN = (
    "Would read course {course} on {site}, with these functions, and file one download:"
)
DRY_RUN_LINE = "  {function}: {purpose}"
COURSE_UNSET = "(set course_id in the --config file)"
STEP = "Step {number}. {title}"
STEP_FAILED = "  STEP {number} FAILED: {reason}"
FINDING = "  FINDING: {text}"
SAVED = "Saved the full output to {path}"
NOT_SAVED = (
    "The output was not saved. Use --out PATH, outside the repository, to keep it."
)
RESULTS = "RESULTS (function, what came back, what was missing from our assumption):"
RESULT_ROW = "  {function}: {text}"
NOT_CALLED = "not called"
SUMMARY_OK = "Tier 2: all six steps ran. Findings: {findings}."
SUMMARY_BAD = "Tier 2: {count} step(s) failed; see the lines marked STEP n FAILED. Findings: {findings}."
LAST_OFFLINE = "OFFLINE: built-in fake, not a live run. Nothing was written to Moodle."
LAST_LIVE = "LIVE: read-only run. Nothing was written to Moodle."
ERR_CONFIG = (
    "The --config file {path} could not be used: {reason}. Use a YAML file with one key, "
    "course_id, a whole number."
)
ERR_NO_COURSE = (
    "Live mode needs the course id. Put course_id in the --config file (the id from the "
    "'Test course ready' post in #112)."
)

S1_OK = "  OK: a call with the token succeeded (core_course_get_courses_by_field): course {name!r}"
S1_REFUSED = "  REFUSED: mod_assign_save_grade is not one of the six read functions; nothing was sent."
S1_NOT_REFUSED = (
    "  NOT REFUSED: a grade write was not refused. Stop and tell the guide."
)
S1_NO_COURSE = "course {course} was not found"
S2_LINE = "  The course has {sections} section(s) and {count} assignment(s): {names}"
S3_LINE = "  {total} enrolled user(s): {students} student(s), {others} other"
S4_LINE = (
    "  Assignment {id} {name!r}: grading type {kind}, maximum grade {grade}, "
    "marking workflow {workflow}"
)
S5_LINE = "  Assignment {id}, {user}: submission {submission}, grading status {grading}"
S6_OK = "  Downloaded {name}: {size} bytes"
S6_NONE = "no submitted file was found in the submissions"
F_NO_WORKFLOW = (
    "assignment {id} has no markingworkflow field (the fake assumes it is there)"
)
F_NO_LASTATTEMPT = (
    "no lastattempt for {user} on assignment {id}: Moodle leaves it out when the learner lacks "
    "mod/assign:viewownsubmissionsummary (R6), so the grading state cannot be read"
)
F_NO_GRADE_FIELD = "assignment {id} has no maximum grade field `grade`"


@dataclass
class Run:
    connection: Connection
    recorder: Recorder
    quiet: bool
    course_id: int
    results: dict[str, list[str]] = field(default_factory=dict)
    failures: int = 0
    findings: int = 0

    def say(self, text: str) -> None:
        self.recorder.line(text)
        if not self.quiet:
            print(text)

    def ok(self, function: str, text: str) -> None:
        self.results.setdefault(function, []).append(f"OK, {text}")

    def finding(self, function: str, text: str) -> None:
        self.findings += 1
        self.say(FINDING.format(text=text))
        self.results.setdefault(function, []).append(
            f"missing from our assumption: {text}"
        )

    def call(self, function: str, params: Mapping[str, Any]) -> Any:
        try:
            answer = self.connection.client.call(function, params)
        except MoodleError as error:
            self.results.setdefault(function, []).append(f"FAILED: {error}")
            raise
        name = (
            function
            if function not in self.recorder.answers
            else f"{function}#{len(self.recorder.answers)}"
        )
        self.recorder.note(name, answer)
        return answer


# --- the steps -------------------------------------------------------------------------------


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _step1(run: Run) -> None:
    function = "core_course_get_courses_by_field"
    answer = run.call(function, {"field": "id", "value": run.course_id})
    courses = _as_list(answer.get("courses") if isinstance(answer, Mapping) else None)
    if not courses:
        raise MoodleError(S1_NO_COURSE.format(course=run.course_id))
    name = courses[0].get("fullname", "?")
    run.say(S1_OK.format(name=name))
    run.ok(function, f"course {name!r}")
    try:
        run.connection.client.call("mod_assign_save_grade", {})
    except MoodleError:
        run.say(S1_REFUSED)
    else:
        raise MoodleError(S1_NOT_REFUSED.strip())


def _step2(run: Run) -> None:
    function = "core_course_get_contents"
    sections = _as_list(run.call(function, {"courseid": run.course_id}))
    names = [
        m.get("name", "?")
        for s in sections
        for m in _as_list(s.get("modules"))
        if m.get("modname") == "assign"
    ]
    run.say(
        S2_LINE.format(sections=len(sections), count=len(names), names=", ".join(names))
    )
    run.ok(function, f"{len(sections)} section(s), {len(names)} assignment(s)")


def _students(run: Run) -> list[dict[str, Any]]:
    function = "core_enrol_get_enrolled_users"
    users = _as_list(run.call(function, {"courseid": run.course_id}))
    students = [
        u
        for u in users
        if "student" in [r.get("shortname") for r in _as_list(u.get("roles"))]
    ]
    run.say(
        S3_LINE.format(
            total=len(users), students=len(students), others=len(users) - len(students)
        )
    )
    run.ok(function, f"{len(users)} user(s)")
    return students


def _assignments(run: Run) -> list[dict[str, Any]]:
    function = "mod_assign_get_assignments"
    answer = run.call(function, {"courseids": [run.course_id]})
    courses = _as_list(answer.get("courses") if isinstance(answer, Mapping) else None)
    rows = [a for c in courses for a in _as_list(c.get("assignments"))]
    for row in rows:
        grade = row.get("grade")
        if grade is None:
            run.finding(function, F_NO_GRADE_FIELD.format(id=row.get("id")))
        kind = (
            "point"
            if isinstance(grade, int | float) and grade > 0
            else ("scale" if isinstance(grade, int | float) and grade < 0 else "none")
        )
        if "markingworkflow" not in row:
            run.finding(function, F_NO_WORKFLOW.format(id=row.get("id")))
        workflow = "ON" if row.get("markingworkflow") else "OFF"
        run.say(
            S4_LINE.format(
                id=row.get("id"),
                name=row.get("name"),
                kind=kind,
                grade=grade,
                workflow=workflow,
            )
        )
    run.ok(function, f"{len(rows)} assignment(s)")
    return rows


def _step5(
    run: Run, assignments: list[dict[str, Any]], students: list[dict[str, Any]]
) -> tuple[str, str] | None:
    """Submissions and each learner's state. Returns the first submitted file (name, address)."""
    first_file: tuple[str, str] | None = None
    calls = 0
    for assignment in assignments:
        assign = assignment["id"]
        answer = run.call("mod_assign_get_submissions", {"assignmentids": [assign]})
        blocks = _as_list(
            answer.get("assignments") if isinstance(answer, Mapping) else None
        )
        submissions = [s for b in blocks for s in _as_list(b.get("submissions"))]
        run.ok(
            "mod_assign_get_submissions",
            f"assignment {assign}: {len(submissions)} submission(s)",
        )
        first_file = first_file or _first_file(submissions)
        listed = {s.get("userid"): s.get("status") for s in submissions}
        people = students or [{"id": u, "username": f"user {u}"} for u in listed]
        for person in people:
            _status_line(run, assign, person, listed)
            calls += 1
    # One short row for the results table; the per-learner lines are printed above.
    run.ok("mod_assign_get_submission_status", f"{calls} call(s)")
    return first_file


def _status_line(
    run: Run, assign: int, person: dict[str, Any], listed: Mapping[Any, Any]
) -> None:
    function = "mod_assign_get_submission_status"
    answer = run.call(function, {"assignid": assign, "userid": person["id"]})
    last = answer.get("lastattempt") if isinstance(answer, Mapping) else None
    user = person.get("username", "?")
    if not isinstance(last, Mapping):
        run.finding(function, F_NO_LASTATTEMPT.format(user=user, id=assign))
        last = {}
    submission = (
        (last.get("submission") or {}).get("status")
        or listed.get(person["id"])
        or "none"
    )
    run.say(
        S5_LINE.format(
            id=assign,
            user=user,
            submission=submission,
            grading=last.get("gradingstatus", "unknown"),
        )
    )


def _first_file(submissions: list[dict[str, Any]]) -> tuple[str, str] | None:
    for sub in submissions:
        for plugin in _as_list(sub.get("plugins")):
            for area in _as_list(plugin.get("fileareas")):
                for file in _as_list(area.get("files")):
                    if file.get("fileurl"):
                        return str(file.get("filename", "file")), str(file["fileurl"])
    return None


def _step6(run: Run, found: tuple[str, str] | None) -> None:
    if found is None:
        run.finding("mod_assign_get_submissions", S6_NONE)
        return
    name, address = found
    data = run.connection.transport.download_file(
        run.connection.settings, address, MAX_FILE_BYTES
    )
    run.say(S6_OK.format(name=name, size=len(data)))
    run.recorder.note(
        "download", {"filename": name, "bytes": len(data)}
    )  # never the address


def _guard(run: Run, number: int, action: Any) -> Any:
    """Run one step. A failing step is shown and counted; the other steps still run."""
    try:
        return action()
    except MoodleError as error:
        run.failures += 1
        run.say(STEP_FAILED.format(number=number, reason=error))
        return None


def run_steps(run: Run) -> None:
    titles = [
        "A call with the token works; a function outside the six is refused",
        "Course contents",
        "Enrolled users",
        "Assignment settings: grading type, maximum grade, marking workflow",
        "Submissions and each learner's submission and grading status",
        "Download one submitted file",
    ]

    def head(number: int) -> None:
        run.say(STEP.format(number=number, title=titles[number - 1]))

    head(1)
    _guard(run, 1, lambda: _step1(run))
    head(2)
    _guard(run, 2, lambda: _step2(run))
    head(3)
    students = _guard(run, 3, lambda: _students(run)) or []
    head(4)
    assignments = _guard(run, 4, lambda: _assignments(run)) or []
    head(5)
    found = _guard(run, 5, lambda: _step5(run, assignments, students))
    head(6)
    _guard(run, 6, lambda: _step6(run, found))


# --- command line ------------------------------------------------------------------------------


def _error(text: str) -> int:
    print(text, file=sys.stderr)
    return 2


def _course_from_config(path: Path | None) -> int | None:
    if path is None:
        return None
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        course = loaded["course_id"]
        if type(course) is not int or course <= 0:
            raise ValueError("course_id must be a whole number above zero")
    except (OSError, yaml.YAMLError, KeyError, TypeError, ValueError) as error:
        raise DemoError(
            ERR_CONFIG.format(path=path, reason=type(error).__name__)
        ) from None
    return course


def _check_output_path(out: Path | None) -> None:
    if out is not None and Path(out).resolve().is_relative_to(ROOT.resolve()):
        raise DemoError(OUTPUT_INSIDE_REPOSITORY.format(path=out))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="demo_h4_live_read",
        description="H4 demo, Tier 2: the live read of the lab Moodle 5.3, read-only.",
    )
    parser.add_argument(
        "--offline", action="store_true", help="use the built-in fake, not the lab"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="list the calls it would make; make none"
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="run quietly; exit 0 when every step ran, 1 when not",
    )
    parser.add_argument("--config", type=Path, help="YAML file with one key, course_id")
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
    course = _course_from_config(args.config)
    _check_output_path(args.out)
    connection = connect(offline=args.offline)
    if course is None and args.offline:
        course = OFFLINE_COURSE_ID
    quiet = bool(args.check)
    if args.dry_run:
        print(DRY_RUN_NOTE)
        site = describe(connection)
        print(
            DRY_RUN_PLAN.format(
                course=course if course is not None else COURSE_UNSET, site=site
            )
        )
        for function, purpose in PLAN:
            print(DRY_RUN_LINE.format(function=function, purpose=purpose))
        return 0
    if course is None:
        raise DemoError(ERR_NO_COURSE)
    run = Run(connection, Recorder(), quiet, course)
    run.say(TITLE)
    run.say("=" * len(TITLE))
    run.say(f"Connection: {describe(connection)}")
    run_steps(run)
    run.say("")
    run.say(RESULTS)
    for function, _ in PLAN:
        run.say(
            RESULT_ROW.format(
                function=function,
                text="; ".join(run.results.get(function, [NOT_CALLED])),
            )
        )
    summary = (
        SUMMARY_OK.format(findings=run.findings)
        if run.failures == 0
        else SUMMARY_BAD.format(count=run.failures, findings=run.findings)
    )
    last = LAST_OFFLINE if connection.offline else LAST_LIVE
    if args.out is not None:
        run.recorder.lines += [summary, last]
        run.recorder.save(args.out)
        run.say(SAVED.format(path=args.out))
    else:
        run.say(NOT_SAVED)
    if not quiet:
        print(summary)
        print(last)
    return 0 if run.failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Build the B8.3 course-model variants (PRD B8.3, B2). Standard library only.

Each variant is the clean baseline model of the B8.2 course, merged into a simplified B8.1 template,
with exactly ONE planted change. The files are B2 course models (contracts/course-model.v1), the
input the checker rules run on. They are hand-built and fictional: not produced from, and not
verified against, a real Moodle backup (decision 0003 section 4). The Moodle `.mbz` variants stay
PENDING MOODLE LAB.

    python make_models.py            write models/*.model.json
    python make_models.py --dry-run  list what would be written; write nothing
    python make_models.py --check    exit 1 if a committed file differs from what this builds

Undo: delete the `models/` folder (nothing else is touched).
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Callable

Model = dict[str, Any]
HERE = Path(__file__).resolve().parent
OUT = HERE / "models"

NOTE = (
    "B8.3 test data (PRD B8.3). Hand-built, fictional B2 course model derived from the B8.2 sample "
    "course merged into a simplified B8.1 template. Not produced from a real Moodle backup."
)
PAST_DATE = 1577836800  # 2020-01-01T00:00:00Z: already in the past, so "until" this date has closed
MISSING_CMID = 999  # no activity has this cmid


def _completion(cm: int) -> dict[str, Any]:
    return {"op": "&", "c": [{"type": "completion", "cm": cm, "e": 1}], "showc": [True]}


def _act(
    kind: str, idnumber: str, cmid: int, title: str, **extra: Any
) -> dict[str, Any]:
    activity: dict[str, Any] = {
        "type": kind,
        "idnumber": idnumber,
        "cmid": cmid,
        "title": title,
        "visible": True,
        "availability": None,
        "completion": {"tracking": "none"},
        "grade_item": None,
    }
    activity.update(extra)
    return activity


def _task(idnumber: str, cmid: int, title: str, points: int) -> dict[str, Any]:
    return _act(
        "assignment",
        idnumber,
        cmid,
        title,
        completion={"tracking": "automatic", "submit": True},
        grade_item={"max_grade": points},
        marking_workflow=True,
        marking_table={"present": True, "points_total": points},
    )


def _section(
    number: int, title: str, activities: list[dict[str, Any]], availability: Any = None
) -> dict[str, Any]:
    return {
        "number": number,
        "idnumber": None,
        "title": title,
        "visible": True,
        "availability": availability,
        "activities": activities,
    }


def baseline() -> Model:
    """The clean model. A checker must report zero findings on it."""
    protected = [
        {"type": "activity", "cmid": 103, "idnumber": "final-project"},
        {"type": "activity", "cmid": 104, "idnumber": "course-feedback"},
    ]
    return {
        "_note": NOTE,
        "schema": "learnops.course-model/v1",
        "source": {"kind": "mbz", "mode": "full", "timezone": None},
        "course": {
            "shortname": "b8-3-model",
            "fullname": "Build a Document Question Assistant (B8.3 model)",
            "completion_enabled": True,
            # Independent target (decision 0003 #25): four 25-point tasks plus the 100-point
            # final project. Never derived from the grade items being checked.
            "total_points": 200,
        },
        "sections": [
            _section(0, None, []),
            _section(1, "Orientation", [_act("page", "tpl-welcome", 101, "Welcome")]),
            _section(
                2,
                "Sample week",
                [_act("page", "tpl-sample-guide", 102, "Sample guide")],
            ),
            _section(
                3,
                "Final project",
                [
                    _task("final-project", 103, "Final project", 100),
                    _act(
                        "feedback",
                        "course-feedback",
                        104,
                        "Course feedback",
                        completion={"tracking": "automatic", "submit": True},
                    ),
                ],
            ),
            _section(
                4,
                "Week 1 - Publish a starter assistant",
                [
                    _act(
                        "page",
                        "wk-01-guide",
                        111,
                        "Week 1 guide",
                        media_refs=["build-document-assistant/wk-01/diagram.png"],
                    ),
                    _act("h5p", "wk-01-practice", 113, "Week 1 practice"),
                    _task("wk-01-task", 112, "Week 1 task", 25),
                ],
            ),
            _section(
                5,
                "Week 2 - Answer from a document",
                [
                    _act("page", "wk-02-guide", 121, "Week 2 guide"),
                    _task("wk-02-task", 122, "Week 2 task", 25),
                ],
                _completion(112),
            ),
            _section(
                6,
                "Week 3 - Test it and fix weak answers",
                [
                    _act("page", "wk-03-guide", 131, "Week 3 guide"),
                    _task("wk-03-task", 132, "Week 3 task", 25),
                ],
                _completion(122),
            ),
            _section(
                7,
                "Week 4 - Write it up and share it",
                [
                    _act("page", "wk-04-guide", 141, "Week 4 guide"),
                    _task("wk-04-task", 142, "Week 4 task", 25),
                ],
                _completion(132),
            ),
        ],
        "course_completion": {"criteria": copy.deepcopy(protected)},
        "badges": [
            {"name": "Template course badge", "criteria": copy.deepcopy(protected)}
        ],
    }


def _find(model: Model, idnumber: str) -> dict[str, Any]:
    for section in model["sections"]:
        for activity in section["activities"]:
            if activity["idnumber"] == idnumber:
                return activity  # type: ignore[no-any-return]
    raise KeyError(idnumber)


def _section_no(model: Model, number: int) -> dict[str, Any]:
    return next(s for s in model["sections"] if s["number"] == number)


def ck01(m: Model) -> None:
    _find(m, "wk-03-guide")["availability"] = {
        "op": "&",
        "c": [{"type": "date", "d": "<", "t": PAST_DATE}],
        "showc": [True],
    }


def ck04(m: Model) -> None:
    _section_no(m, 6)["availability"] = _completion(MISSING_CMID)


def ck05(m: Model) -> None:
    _section_no(m, 5)["availability"] = _completion(
        132
    )  # week 2 waits for the week 3 task
    _section_no(m, 6)["availability"] = _completion(
        122
    )  # week 3 waits for the week 2 task


def ck06_duplicate(m: Model) -> None:
    _find(m, "wk-02-task")["idnumber"] = "wk-01-task"


def ck06_invalid(m: Model) -> None:
    _find(m, "wk-01-task")["idnumber"] = "Week 1 Task"


def ck07(m: Model) -> None:
    final = _find(m, "final-project")
    final["grade_item"] = {"max_grade": 80}
    final["marking_table"] = {"present": True, "points_total": 80}


def ck08(m: Model) -> None:
    m["course_completion"]["criteria"].append(
        {"type": "activity", "cmid": MISSING_CMID, "idnumber": "wk-02-bonus"}
    )


def ck10(m: Model) -> None:
    _find(m, "wk-01-task")["marking_workflow"] = False


def ck11(m: Model) -> None:
    _find(m, "wk-01-practice")["grade_item"] = {"max_grade": 10}


def ck12(m: Model) -> None:
    _find(m, "wk-01-guide")["media_refs"] = ["https://example.invalid/diagram.png"]


def ck13(m: Model) -> None:
    _find(m, "wk-01-task")["completion"] = {"tracking": "none"}


VARIANTS: dict[str, Callable[[Model], None]] = {
    "ck-01-unreachable-by-past-date-model": ck01,
    "ck-04-unlock-missing-activity-model": ck04,
    "ck-05-circular-unlock-model": ck05,
    "ck-06-duplicate-idnumber-model": ck06_duplicate,
    "ck-06-invalid-idnumber-model": ck06_invalid,
    "ck-07-protected-item-changed-model": ck07,
    "ck-08-completion-criteria-missing-item-model": ck08,
    "ck-10-no-marking-workflow-model": ck10,
    "ck-11-graded-practice-h5p-model": ck11,
    "ck-12-full-url-media-model": ck12,
    "ck-13-unlock-without-completion-model": ck13,
}


def build_all() -> dict[str, Model]:
    files: dict[str, Model] = {"baseline": baseline()}
    for name, plant in VARIANTS.items():
        model = copy.deepcopy(files["baseline"])
        plant(model)
        files[name] = model
    return files


def render(model: Model) -> str:
    # Sorted keys and no indent: a stable one-line file. Review the code above, not the JSON;
    # `--check` proves the committed files are exactly what this code builds.
    return json.dumps(model, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--dry-run", action="store_true", help="list files; write nothing"
    )
    parser.add_argument("--check", action="store_true", help="exit 1 if a file differs")
    args = parser.parse_args(argv)
    files = {f"{name}.model.json": render(m) for name, m in build_all().items()}
    if args.check:
        stale = [
            n
            for n, text in files.items()
            if not (OUT / n).is_file() or (OUT / n).read_bytes() != text.encode("utf-8")
        ]
        for n in stale:
            print(f"differs or missing: models/{n}", file=sys.stderr)
        return 1 if stale else 0
    for n in files:
        print(f"{'would write' if args.dry_run else 'write'} models/{n}")
    if not args.dry_run:
        OUT.mkdir(exist_ok=True)
        for n, text in files.items():
            (OUT / n).write_bytes(text.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

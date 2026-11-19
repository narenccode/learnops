"""An offline fake of the lab Moodle 5.3, for the live demo scripts (PLAN-demo-grading.md, H3).

It mirrors the test course the plan asks for (one course, two assignments, learners A to D) and
answers the six read functions of PRD B4 §2. It sits at the HTTP level (post and get), so the
read-only connection's own code runs in offline mode too.

NOT a recording and NOT lab-verified. The answer shapes come from the Moodle source and docs. A
live answer that differs is a finding for the results table, not a failure. Test data only: made-up
names, no real learner data (PRD C-07), and a made-up token that opens nothing.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, Final
from urllib.parse import parse_qs, urlsplit

FAKE_URL: Final = "https://moodle53.demo.invalid"
FAKE_TOKEN: Final = "demo0offline0only"
COURSE_ID: Final = 2
ASSIGNMENT_WORKFLOW_ON: Final = 1
ASSIGNMENT_WORKFLOW_OFF: Final = 2
SERVICE_ACCOUNT_ID: Final = 100
LEARNERS: Final = {"A": 101, "B": 102, "C": 103, "D": 104}
FILE_TEXT: Final = b"Test submission text for the demo.\n"

_FILE_PATH: Final = "/webservice/pluginfile.php/"
_FILE_NAME: Final = "note.txt"

# (assignment, learner) -> (submission id, submission status, grading status, stored grade).
# A: submitted, no grade. B: submitted, grade 7, ready for release. C: a draft. D: Assignment 2
# (marking workflow off), where the grading status is graded or notgraded (B4 §7).
_STATES: Final[dict[tuple[int, str], tuple[int, str, str, str | None]]] = {
    (ASSIGNMENT_WORKFLOW_ON, "A"): (9001, "submitted", "notmarked", None),
    (ASSIGNMENT_WORKFLOW_ON, "B"): (9002, "submitted", "readyforrelease", "7.00000"),
    (ASSIGNMENT_WORKFLOW_ON, "C"): (9003, "draft", "notmarked", None),
    (ASSIGNMENT_WORKFLOW_OFF, "D"): (9004, "submitted", "notgraded", None),
}
_LEARNER_BY_ID: Final = {user: name for name, user in LEARNERS.items()}
_ASSIGNMENTS: Final = {
    ASSIGNMENT_WORKFLOW_ON: ("Week 1 task", 11, 1),
    ASSIGNMENT_WORKFLOW_OFF: ("Week 1 task (workflow off)", 12, 0),
}


def _error(code: str, message: str) -> dict[str, str]:
    return {"exception": "moodle_exception", "errorcode": code, "message": message}


class FakeSite:
    """Answers like the lab Moodle 5.3 would. `functions_called` lists every function asked."""

    def __init__(self, token: str = FAKE_TOKEN, base_url: str = FAKE_URL) -> None:
        self._token = token
        self._base = base_url
        self.functions_called: list[str] = []
        self.downloads = 0
        self._handlers: dict[str, Callable[[dict[str, str]], Any]] = {
            "core_course_get_courses_by_field": self._courses,
            "core_course_get_contents": self._contents,
            "core_enrol_get_enrolled_users": self._users,
            "mod_assign_get_assignments": self._assignments,
            "mod_assign_get_submissions": self._submissions,
            "mod_assign_get_submission_status": self._status,
        }

    # --- the two HTTP functions the read-only connection takes ---------------------------------

    def post(self, url: str, body: bytes, timeout: float) -> bytes:
        fields = {k: v[0] for k, v in parse_qs(body.decode("utf-8")).items()}
        function = fields.get("wsfunction", "")
        self.functions_called.append(function)
        if fields.get("wstoken") != self._token:
            return _dump(_error("invalidtoken", "Invalid token"))
        handler = self._handlers.get(function)
        if handler is None:  # not in the external service: Moodle refuses it
            return _dump(_error("accessexception", "Access control exception"))
        try:
            return _dump(handler(fields))
        except (KeyError, ValueError):
            return _dump(_error("invalidparameter", "Invalid parameter value detected"))

    def get(self, url: str, timeout: float, max_bytes: int) -> bytes:
        parts = urlsplit(url)
        token = parse_qs(parts.query).get("token", [""])[0]
        if token != self._token or not parts.path.startswith(_FILE_PATH):
            raise OSError("not allowed")
        self.downloads += 1
        return FILE_TEXT[: max_bytes + 1]

    # --- the six functions ---------------------------------------------------------------------

    def _courses(self, p: dict[str, str]) -> Any:
        found = p["field"] == "id" and int(p["value"]) == COURSE_ID
        course = {
            "id": COURSE_ID,
            "shortname": "demo-grading",
            "fullname": "Demo grading test",
            "visible": 1,
        }
        return {"courses": [course] if found else [], "warnings": []}

    def _contents(self, p: dict[str, str]) -> Any:
        _only_course(int(p["courseid"]))
        modules = [
            {"id": cmid, "name": name, "modname": "assign", "instance": assign}
            for assign, (name, cmid, _) in _ASSIGNMENTS.items()
        ]
        return [{"id": 1, "name": "Week 1", "modules": modules}]

    def _users(self, p: dict[str, str]) -> Any:
        _only_course(int(p["courseid"]))
        service = {
            "id": SERVICE_ACCOUNT_ID,
            "username": "learnops-ws",
            "fullname": "LearnOps service account",
            "roles": [{"roleid": 4, "shortname": "teacher"}],
        }
        learners = [
            {
                "id": user,
                "username": f"learner-{name.lower()}",
                "fullname": f"Learner {name}",
                "roles": [{"roleid": 5, "shortname": "student"}],
            }
            for name, user in LEARNERS.items()
        ]
        return [service, *learners]

    def _assignments(self, p: dict[str, str]) -> Any:
        _only_course(int(p["courseids[0]"]))
        rows = [
            {
                "id": assign,
                "cmid": cmid,
                "course": COURSE_ID,
                "name": name,
                "grade": 10,
                "markingworkflow": workflow,
                "configs": [
                    {
                        "plugin": "onlinetext",
                        "subtype": "assignsubmission",
                        "name": "enabled",
                        "value": "1",
                    },
                    {
                        "plugin": "file",
                        "subtype": "assignsubmission",
                        "name": "enabled",
                        "value": "1",
                    },
                ],
            }
            for assign, (name, cmid, workflow) in _ASSIGNMENTS.items()
        ]
        return {"courses": [{"id": COURSE_ID, "assignments": rows}], "warnings": []}

    def _submissions(self, p: dict[str, str]) -> Any:
        assign = int(p["assignmentids[0]"])
        _only_assignment(assign)
        rows = [self._submission(assign, name) for (a, name) in _STATES if a == assign]
        return {
            "assignments": [{"assignmentid": assign, "submissions": rows}],
            "warnings": [],
        }

    def _submission(self, assign: int, name: str) -> dict[str, Any]:
        sub_id, status, _, _ = _STATES[(assign, name)]
        files = []
        if (assign, name) == (ASSIGNMENT_WORKFLOW_ON, "A"):
            url = f"{self._base}{_FILE_PATH}55/assignsubmission_file/submission_files/{sub_id}/{_FILE_NAME}"
            files = [
                {
                    "type": "file",
                    "fileareas": [
                        {
                            "area": "submission_files",
                            "files": [{"filename": _FILE_NAME, "fileurl": url}],
                        }
                    ],
                }
            ]
        return {
            "id": sub_id,
            "userid": LEARNERS[name],
            "attemptnumber": 0,
            "status": status,
            "plugins": files,
        }

    def _status(self, p: dict[str, str]) -> Any:
        assign, user = int(p["assignid"]), int(p["userid"])
        _only_assignment(assign)
        name = _LEARNER_BY_ID[user]
        state = _STATES.get((assign, name))
        if state is None:  # enrolled, but no submission on this assignment
            workflow = _ASSIGNMENTS[assign][2]
            return {
                "lastattempt": {
                    "gradingstatus": "notmarked" if workflow else "notgraded"
                }
            }
        sub_id, status, grading, grade = state
        answer: dict[str, Any] = {
            "lastattempt": {
                "submission": {
                    "id": sub_id,
                    "userid": user,
                    "attemptnumber": 0,
                    "status": status,
                },
                "gradingstatus": grading,
            }
        }
        if grade is not None:
            answer["feedback"] = {"grade": {"userid": user, "grade": grade}}
        return answer


def _only_course(course: int) -> None:
    if course != COURSE_ID:
        raise ValueError("unknown course")


def _only_assignment(assign: int) -> None:
    if assign not in _ASSIGNMENTS:
        raise KeyError(assign)


def _dump(value: Any) -> bytes:
    return json.dumps(value).encode("utf-8")

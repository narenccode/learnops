"""Tests for the demo's offline fake site (scripts/demos/demo_fake_site.py).

The fake plays the lab Moodle 5.3 for the live scripts: it mirrors the test course of PLAN-demo-grading.md
(one course, two assignments, learners A to D) and answers the six read functions. Its answer shapes
come from the Moodle source and are NOT verified on a lab site. It sits at the HTTP level, so the
read-only connection's own code runs in offline mode too.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "libs"))
sys.path.insert(0, str(ROOT / "scripts" / "demos"))

from demo_fake_site import (  # noqa: E402
    ASSIGNMENT_WORKFLOW_OFF,
    ASSIGNMENT_WORKFLOW_ON,
    COURSE_ID,
    FAKE_TOKEN,
    FAKE_URL,
    LEARNERS,
    FakeSite,
)

REST = f"{FAKE_URL}/webservice/rest/server.php"


def ask(site: FakeSite, function: str, token: str = FAKE_TOKEN, **params: Any) -> Any:
    body = urlencode(
        [("wstoken", token), ("wsfunction", function), ("moodlewsrestformat", "json")]
        + [(k, str(v)) for k, v in params.items()]
    )
    return json.loads(site.post(REST, body.encode(), 30.0))


def test_the_course_is_found_by_id() -> None:
    answer = ask(
        FakeSite(), "core_course_get_courses_by_field", field="id", value=COURSE_ID
    )
    assert [c["id"] for c in answer["courses"]] == [COURSE_ID]
    assert answer["warnings"] == []


def test_the_course_contents_list_both_assignments() -> None:
    sections = ask(FakeSite(), "core_course_get_contents", courseid=COURSE_ID)
    modules = [m for s in sections for m in s["modules"] if m["modname"] == "assign"]
    assert sorted(m["instance"] for m in modules) == [
        ASSIGNMENT_WORKFLOW_ON,
        ASSIGNMENT_WORKFLOW_OFF,
    ]


def test_the_enrolled_users_are_four_learners_and_the_service_account() -> None:
    users = ask(FakeSite(), "core_enrol_get_enrolled_users", courseid=COURSE_ID)
    students = [u for u in users if u["roles"][0]["shortname"] == "student"]
    assert sorted(u["id"] for u in students) == sorted(LEARNERS.values())
    others = [u for u in users if u["roles"][0]["shortname"] == "teacher"]
    assert len(others) == 1  # the service account, a non-editing teacher


def test_the_assignment_settings_show_marking_workflow_on_and_off() -> None:
    answer = ask(
        FakeSite(), "mod_assign_get_assignments", **{"courseids[0]": COURSE_ID}
    )
    assignments = {a["id"]: a for a in answer["courses"][0]["assignments"]}
    assert assignments[ASSIGNMENT_WORKFLOW_ON]["markingworkflow"] == 1
    assert assignments[ASSIGNMENT_WORKFLOW_OFF]["markingworkflow"] == 0
    assert all(a["grade"] == 10 for a in assignments.values())


def test_the_submissions_match_the_planned_states() -> None:
    site = FakeSite()
    one = ask(
        site,
        "mod_assign_get_submissions",
        **{"assignmentids[0]": ASSIGNMENT_WORKFLOW_ON},
    )
    rows = {s["userid"]: s["status"] for s in one["assignments"][0]["submissions"]}
    assert rows == {
        LEARNERS["A"]: "submitted",
        LEARNERS["B"]: "submitted",
        LEARNERS["C"]: "draft",
    }
    two = ask(
        site,
        "mod_assign_get_submissions",
        **{"assignmentids[0]": ASSIGNMENT_WORKFLOW_OFF},
    )
    assert [s["userid"] for s in two["assignments"][0]["submissions"]] == [
        LEARNERS["D"]
    ]


def test_each_learners_state_is_as_planned() -> None:
    site = FakeSite()

    def state(assign: int, learner: str) -> dict[str, Any]:
        return ask(
            site,
            "mod_assign_get_submission_status",
            assignid=assign,
            userid=LEARNERS[learner],
        )

    a = state(ASSIGNMENT_WORKFLOW_ON, "A")
    assert a["lastattempt"]["gradingstatus"] == "notmarked"
    assert a["lastattempt"]["submission"]["status"] == "submitted"

    b = state(ASSIGNMENT_WORKFLOW_ON, "B")
    assert b["lastattempt"]["gradingstatus"] == "readyforrelease"
    assert b["feedback"]["grade"]["grade"] == "7.00000"

    c = state(ASSIGNMENT_WORKFLOW_ON, "C")
    assert c["lastattempt"]["submission"]["status"] == "draft"

    d = state(ASSIGNMENT_WORKFLOW_OFF, "D")
    assert d["lastattempt"]["gradingstatus"] == "notgraded"  # marking workflow off


def test_a_submitted_file_can_be_downloaded_from_the_sites_pluginfile() -> None:
    site = FakeSite()
    one = ask(
        site,
        "mod_assign_get_submissions",
        **{"assignmentids[0]": ASSIGNMENT_WORKFLOW_ON},
    )
    submission = next(
        s for s in one["assignments"][0]["submissions"] if s["userid"] == LEARNERS["A"]
    )
    file = submission["plugins"][0]["fileareas"][0]["files"][0]
    assert file["fileurl"].startswith(f"{FAKE_URL}/webservice/pluginfile.php/")
    data = site.get(f"{file['fileurl']}?token={FAKE_TOKEN}", 30.0, 1000)
    assert data and len(data) <= 1000


def test_a_wrong_token_is_rejected_like_moodle_does() -> None:
    answer = ask(
        FakeSite(), "core_course_get_contents", token="wrongvalue", courseid=COURSE_ID
    )
    assert answer["errorcode"] == "invalidtoken"


def test_a_function_outside_the_service_is_refused_like_moodle_does() -> None:
    answer = ask(FakeSite(), "mod_assign_save_grade")
    assert answer["errorcode"] == "accessexception"


def test_the_fake_site_records_which_functions_were_asked() -> None:
    site = FakeSite()
    ask(site, "core_course_get_contents", courseid=COURSE_ID)
    ask(site, "mod_assign_get_assignments", **{"courseids[0]": COURSE_ID})
    assert site.functions_called == [
        "core_course_get_contents",
        "mod_assign_get_assignments",
    ]

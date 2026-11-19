"""Tests for the H5 read-only connection (scripts/demos/readonly_connection.py).

The demo's connection to Moodle may call only the six read functions of PRD B4 §2. Anything else,
above all mod_assign_save_grade, must be refused before anything is sent. These tests inject fake
HTTP functions, so no network is used, and they check that a refused call never reaches them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

import pytest

ROOT = Path(__file__).resolve().parents[3]
# libs/ first: the repository also has a data folder named contracts/ at its root.
sys.path.insert(0, str(ROOT / "libs"))
sys.path.insert(0, str(ROOT / "scripts" / "demos"))

from moodle_ws import (  # noqa: E402
    FunctionNotAllowed,
    InvalidParameters,
    MoodleClient,
    MoodleError,
    MoodleUnreachable,
    PermissionDenied,
    Site,
    SiteSettings,
    Token,
    TokenInvalid,
    UnexpectedResponse,
    load_allowlist,
)
from readonly_connection import ALLOWED_FUNCTIONS, ReadOnlyTransport  # noqa: E402

FAKE_TOKEN = (
    "fakevalue4tests2only"  # made up; letters and digits, as a real token could be
)
SITE = "https://moodle53.lab.invalid"
SETTINGS = SiteSettings(Site.MOODLE53, "5.3", SITE, Token(FAKE_TOKEN))

SIX = {
    "core_course_get_courses_by_field",
    "core_course_get_contents",
    "core_enrol_get_enrolled_users",
    "mod_assign_get_assignments",
    "mod_assign_get_submissions",
    "mod_assign_get_submission_status",
}


class FakeHttp:
    """Records every request and answers from a script. Nothing here opens a socket."""

    def __init__(self, answer: Any = None, failure: Exception | None = None) -> None:
        self.answer = [] if answer is None else answer
        self.failure = failure
        self.posts: list[tuple[str, dict[str, list[str]]]] = []
        self.gets: list[tuple[str, int]] = []
        self.file_bytes = b"a small test file"

    def post(self, url: str, body: bytes, timeout: float) -> bytes:
        self.posts.append((url, parse_qs(body.decode("utf-8"))))
        if self.failure is not None:
            raise self.failure
        if isinstance(self.answer, bytes):
            return self.answer
        return json.dumps(self.answer).encode("utf-8")

    def get(self, url: str, timeout: float, max_bytes: int) -> bytes:
        self.gets.append((url, max_bytes))
        if self.failure is not None:
            raise self.failure
        return self.file_bytes


def make(
    answer: Any = None, failure: Exception | None = None
) -> tuple[ReadOnlyTransport, FakeHttp]:
    http = FakeHttp(answer, failure)
    return ReadOnlyTransport(post=http.post, get=http.get), http


# --- the allowed list -----------------------------------------------------------------------


def test_the_allowed_functions_are_exactly_the_six_read_functions() -> None:
    assert set(ALLOWED_FUNCTIONS) == SIX


def test_the_allowed_functions_are_in_the_contract_allow_list() -> None:
    # So this helper cannot drift away from contracts/examples/moodle-ws.v1.functions.json.
    assert SIX <= set(load_allowlist().functions)


@pytest.mark.parametrize("function", sorted(SIX))
def test_each_read_function_is_sent_once_with_the_token_in_the_body(
    function: str,
) -> None:
    transport, http = make([])
    transport.call(SETTINGS, function, {"assignid": 7})
    assert len(http.posts) == 1
    url, body = http.posts[0]
    assert url == f"{SITE}/webservice/rest/server.php"
    assert body["wsfunction"] == [function]
    assert body["moodlewsrestformat"] == ["json"]
    assert body["wstoken"] == [FAKE_TOKEN]  # in the POST body, never in the address
    assert FAKE_TOKEN not in url


# --- refusals: nothing is sent --------------------------------------------------------------


@pytest.mark.parametrize(
    "function",
    [
        "mod_assign_save_grade",
        "mod_assign_set_user_flags",
        "mod_assign_get_grades",  # a read, but not one of the six
        "core_webservice_get_site_info",
        "MOD_ASSIGN_GET_ASSIGNMENTS",  # a near miss: different case
        " mod_assign_get_assignments",
        "mod_assign_get_assignments ",
        "mod_assign_get_assignments_extra",
        "mod_assign_get_assignment",  # one letter short
        "",
    ],
)
def test_any_other_function_is_refused_before_anything_is_sent(function: str) -> None:
    transport, http = make()
    with pytest.raises(FunctionNotAllowed):
        transport.call(SETTINGS, function, {})
    assert http.posts == [] and http.gets == []


@pytest.mark.parametrize("function", [None, 7, b"mod_assign_get_assignments", ["x"]])
def test_a_function_name_that_is_not_text_is_refused(function: Any) -> None:
    transport, http = make()
    with pytest.raises(FunctionNotAllowed):
        transport.call(SETTINGS, function, {})
    assert http.posts == []


@pytest.mark.parametrize("key", ["wstoken", "wsfunction", "moodlewsrestformat"])
def test_a_parameter_cannot_replace_the_function_the_token_or_the_format(
    key: str,
) -> None:
    transport, http = make()
    with pytest.raises(InvalidParameters):
        transport.call(
            SETTINGS, "mod_assign_get_assignments", {key: "mod_assign_save_grade"}
        )
    assert http.posts == []


# --- how parameters are sent ----------------------------------------------------------------


def test_lists_and_mappings_are_sent_in_moodle_rest_form() -> None:
    transport, http = make([])
    transport.call(
        SETTINGS,
        "core_course_get_contents",
        {"courseid": 3, "options": [{"name": "excludemodules", "value": 0}]},
    )
    body = http.posts[0][1]
    assert body["courseid"] == ["3"]
    assert body["options[0][name]"] == ["excludemodules"]
    assert body["options[0][value]"] == ["0"]


# --- Moodle's answers -----------------------------------------------------------------------


def test_a_good_answer_is_returned_unchanged() -> None:
    answer = {"assignments": [], "warnings": []}
    transport, _ = make(answer)
    assert transport.call(SETTINGS, "mod_assign_get_assignments", {}) == answer


@pytest.mark.parametrize(
    ("errorcode", "expected"),
    [
        ("invalidtoken", TokenInvalid),
        ("accessexception", PermissionDenied),
        ("nopermissions", PermissionDenied),
        ("somethingelse", UnexpectedResponse),
    ],
)
def test_moodle_errors_become_the_librarys_own_errors(
    errorcode: str, expected: type[MoodleError]
) -> None:
    answer = {
        "exception": "moodle_exception",
        "errorcode": errorcode,
        "message": "text",
    }
    transport, _ = make(answer)
    with pytest.raises(expected):
        transport.call(SETTINGS, "mod_assign_get_assignments", {})


def test_an_answer_that_is_not_json_is_unexpected() -> None:
    transport, _ = make(b"<html>not json</html>")
    with pytest.raises(UnexpectedResponse):
        transport.call(SETTINGS, "mod_assign_get_assignments", {})


def test_a_network_failure_is_unreachable() -> None:
    transport, _ = make(failure=ConnectionError("boom"))
    with pytest.raises(MoodleUnreachable):
        transport.call(SETTINGS, "mod_assign_get_assignments", {})


def test_the_token_never_appears_in_an_error_or_in_repr() -> None:
    # Moodle's own message may echo what was sent, so it is never passed on.
    answer = {
        "exception": "moodle_exception",
        "errorcode": "invalidtoken",
        "message": f"bad token {FAKE_TOKEN} at {SITE}/webservice/rest/server.php",
    }
    transport, _ = make(answer)
    with pytest.raises(TokenInvalid) as caught:
        transport.call(SETTINGS, "mod_assign_get_assignments", {})
    text = f"{caught.value} {caught.value!r} {transport!r}"
    assert FAKE_TOKEN not in text and "lab.invalid" not in text

    unreachable, _ = make(failure=OSError(f"failed to reach {SITE} with {FAKE_TOKEN}"))
    with pytest.raises(MoodleUnreachable) as caught2:
        unreachable.call(SETTINGS, "mod_assign_get_assignments", {})
    assert FAKE_TOKEN not in f"{caught2.value} {caught2.value!r}"
    assert "lab.invalid" not in f"{caught2.value}"


# --- the file download (plan H4 step 6) -----------------------------------------------------


def test_a_file_under_pluginfile_on_the_same_site_is_downloaded_with_the_token() -> (
    None
):
    transport, http = make()
    url = f"{SITE}/webservice/pluginfile.php/55/assignsubmission_file/submission_files/9/note.txt"
    data = transport.download_file(SETTINGS, url, max_bytes=1000)
    assert data == http.file_bytes
    sent, limit = http.gets[0]
    assert sent.startswith(url) and f"token={FAKE_TOKEN}" in sent
    assert limit == 1000


@pytest.mark.parametrize(
    "url",
    [
        "https://other.lab.invalid/webservice/pluginfile.php/1/a.txt",  # another host
        f"{SITE}/login/index.php",  # another path
        f"{SITE}/webservice/pluginfile.phpx/1/a.txt",  # a lookalike path
        f"{SITE}/webservice/pluginfile.php/../../admin/index.php",  # path traversal
        "http://moodle53.lab.invalid/webservice/pluginfile.php/1/a.txt",  # another scheme
        "https://user@moodle53.lab.invalid/webservice/pluginfile.php/1/a.txt",  # credentials
        f"{SITE}/webservice/pluginfile.php/1/a.txt?token=other",  # carries its own token
        "file:///etc/passwd",
        "",
    ],
)
def test_a_download_outside_the_sites_pluginfile_is_refused_and_nothing_is_sent(
    url: str,
) -> None:
    transport, http = make()
    with pytest.raises(MoodleError):
        transport.download_file(SETTINGS, url, max_bytes=1000)
    assert http.gets == []


def test_a_file_over_the_size_limit_is_refused() -> None:
    transport, http = make()
    http.file_bytes = b"x" * 2001
    with pytest.raises(UnexpectedResponse):
        transport.download_file(
            SETTINGS, f"{SITE}/webservice/pluginfile.php/1/a.txt", max_bytes=2000
        )


# --- with the library: a grade write cannot get through ------------------------------------


def test_the_library_refuses_a_direct_grade_write_and_nothing_is_sent() -> None:
    transport, http = make()
    client = MoodleClient(SETTINGS, transport)
    with pytest.raises(MoodleError):
        client.call("mod_assign_save_grade", {"assignmentid": 7, "userid": 42})
    assert http.posts == []


def test_a_draft_grade_write_stops_at_the_transport_and_save_grade_is_never_sent() -> (
    None
):
    # The library's own checks run and read the state (a read, allowed); at the write itself the
    # read-only connection refuses, so Moodle never receives mod_assign_save_grade (plan H6).
    status = {"lastattempt": {"gradingstatus": "notmarked"}}
    transport, http = make(status)
    client = MoodleClient(SETTINGS, transport)
    params = {
        "assignmentid": 7,
        "userid": 42,
        "grade": 5,
        "attemptnumber": 0,
        "addattempt": 0,
        "workflowstate": "readyforrelease",
        "applytoall": 0,
    }
    with pytest.raises(MoodleError):
        client.write_draft_grade(params, 10)
    sent = [body["wsfunction"][0] for _, body in http.posts]
    assert sent == ["mod_assign_get_submission_status"]

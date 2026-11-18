"""Tests for the shared helpers of the live demo scripts (scripts/demos/demo_live_common.py)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "libs"))
sys.path.insert(0, str(ROOT / "scripts" / "demos"))

from demo_fake_site import COURSE_ID, FAKE_TOKEN  # noqa: E402
from demo_live_common import (  # noqa: E402
    Connection,
    DemoError,
    Recorder,
    connect,
    describe,
)
from moodle_ws import MoodleError  # noqa: E402
from readonly_connection import ReadOnlyTransport  # noqa: E402

LIVE_TOKEN = "livelooking0value0for0tests"  # made up
LIVE_ENV = {
    "MOODLE53_URL": "https://moodle53.lab.invalid",
    "MOODLE53_WS_TOKEN": LIVE_TOKEN,
}


# --- connecting ------------------------------------------------------------------------------


def test_offline_runs_the_six_reads_through_the_read_only_connection() -> None:
    connection = connect(offline=True)
    assert isinstance(connection, Connection) and connection.offline
    assert isinstance(connection.transport, ReadOnlyTransport)
    answer = connection.client.call(
        "core_course_get_courses_by_field", {"field": "id", "value": COURSE_ID}
    )
    assert answer["courses"][0]["id"] == COURSE_ID
    assert connection.fake is not None
    assert connection.fake.functions_called == ["core_course_get_courses_by_field"]


def test_offline_a_grade_write_is_refused_and_nothing_reaches_the_fake_site() -> None:
    connection = connect(offline=True)
    with pytest.raises(MoodleError):
        connection.client.call(
            "mod_assign_save_grade", {"assignmentid": 1, "userid": 101}
        )
    assert connection.fake is not None and connection.fake.functions_called == []


def test_live_without_settings_stops_with_a_clear_message_and_no_token() -> None:
    with pytest.raises(DemoError) as caught:
        connect(offline=False, environ={})
    text = str(caught.value)
    assert "MOODLE53_URL" in text and "MOODLE53_WS_TOKEN" in text
    assert "--offline" in text  # says how to run without a lab


def test_live_with_settings_builds_a_read_only_client_and_calls_nothing() -> None:
    connection = connect(
        offline=False, environ=LIVE_ENV
    )  # building must not touch the network
    assert not connection.offline and connection.fake is None
    assert isinstance(connection.transport, ReadOnlyTransport)


def test_the_description_never_shows_the_token_or_the_address() -> None:
    for connection in (connect(offline=True), connect(offline=False, environ=LIVE_ENV)):
        text = describe(connection)
        assert LIVE_TOKEN not in text and FAKE_TOKEN not in text
        assert "lab.invalid" not in text and "demo.invalid" not in text
    assert "offline" in describe(connect(offline=True)).lower()
    assert "live" in describe(connect(offline=False, environ=LIVE_ENV)).lower()


# --- saving the full output ------------------------------------------------------------------


def test_the_output_is_saved_outside_the_repository(tmp_path: Path) -> None:
    recorder = Recorder()
    recorder.note("course", {"id": COURSE_ID})
    recorder.line("Step 1: ok")
    target = tmp_path / "out" / "h4-output.json"
    recorder.save(target)
    saved = json.loads(target.read_text(encoding="utf-8"))
    assert saved["answers"]["course"] == {"id": COURSE_ID}
    assert saved["lines"] == ["Step 1: ok"]
    assert FAKE_TOKEN not in target.read_text(encoding="utf-8")


def test_a_path_inside_the_repository_is_refused_and_nothing_is_written() -> None:
    inside = ROOT / "docs" / "should-not-exist" / "h4.json"
    with pytest.raises(DemoError):
        Recorder().save(inside)
    assert not inside.exists() and not inside.parent.exists()


def test_a_path_that_climbs_into_the_repository_is_refused(tmp_path: Path) -> None:
    sneaky = ROOT.parent / ROOT.name / "scripts" / ".." / "docs" / "h4.json"
    with pytest.raises(DemoError):
        Recorder().save(sneaky)

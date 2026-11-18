"""Tests for the H4 Tier 2 demo: the live read (scripts/demos/demo_h4_live_read.py).

Run offline against the built-in fake site. The live path itself cannot be tested here (no lab, no
network); what is tested is that it needs its settings, makes no call in a dry run, and never shows
the token. A live answer that differs from the fake's is a FINDING, not a failure (plan, section 5).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "libs"))
sys.path.insert(0, str(ROOT / "scripts" / "demos"))

import demo_h4_live_read as demo  # noqa: E402
from demo_fake_site import FAKE_TOKEN, FILE_TEXT, FakeSite  # noqa: E402
from demo_live_common import Connection  # noqa: E402
from fakes import DenyingSite, NoLastAttemptSite, connection_for  # noqa: E402

SCRIPT = ROOT / "scripts" / "demos" / "demo_h4_live_read.py"
SIX = [
    "core_course_get_courses_by_field",
    "core_course_get_contents",
    "core_enrol_get_enrolled_users",
    "mod_assign_get_assignments",
    "mod_assign_get_submissions",
    "mod_assign_get_submission_status",
]
LIVE_TOKEN = "livelooking0value0for0tests"  # made up
LIVE_ENV = {
    "MOODLE53_URL": "https://moodle53.lab.invalid",
    "MOODLE53_WS_TOKEN": LIVE_TOKEN,
}


def run(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = demo.main(argv)
    out = capsys.readouterr()
    return code, out.out, out.err


def with_site(
    monkeypatch: pytest.MonkeyPatch, fake: FakeSite | None = None
) -> Connection:
    """Make main() use one connection, so a test can choose the fake and look at it afterwards."""
    connection = connection_for(FakeSite() if fake is None else fake)
    monkeypatch.setattr(demo, "connect", lambda offline, environ=None: connection)
    return connection


# --- the six steps -------------------------------------------------------------------------------


def test_every_step_runs_and_the_facts_are_printed(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, _ = run(["--offline"], capsys)
    assert code == 0, out
    for number in range(1, 7):
        assert f"Step {number}." in out
    assert "FAILED" not in out and "FINDING" not in out
    # 1. a call with the token works; a function outside the six is refused
    assert "a call with the token succeeded" in out
    assert "REFUSED: mod_assign_save_grade" in out and "nothing was sent" in out
    # 4. grading type, maximum grade, marking workflow
    assert "Assignment 1" in out and "marking workflow ON" in out
    assert "Assignment 2" in out and "marking workflow OFF" in out
    assert "maximum grade 10" in out and "grading type point" in out
    # 5. each learner's state
    assert "learner-a" in out and "notmarked" in out
    assert "learner-b" in out and "readyforrelease" in out
    assert "learner-c" in out and "draft" in out
    assert "learner-d" in out and "notgraded" in out
    # 6. one file, named and counted, never its address
    assert f"Downloaded note.txt: {len(FILE_TEXT)} bytes" in out
    assert "pluginfile" not in out


def test_only_the_six_read_functions_are_ever_sent(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    connection = with_site(monkeypatch)
    assert run(["--offline"], capsys)[0] == 0
    assert connection.fake is not None
    assert set(connection.fake.functions_called) == set(SIX)
    assert "mod_assign_save_grade" not in connection.fake.functions_called


def test_a_results_table_lists_every_function(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, out, _ = run(["--offline"], capsys)
    table = out.split("RESULTS", 1)[1]
    for function in SIX:
        assert function in table


def test_the_last_line_says_this_is_not_a_live_run(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, out, _ = run(["--offline"], capsys)
    assert out.rstrip("\n").splitlines()[-1] == (
        "OFFLINE: built-in fake, not a live run. Nothing was written to Moodle."
    )


# --- when the answer differs, or a step fails ----------------------------------------------------


def test_a_missing_field_is_a_finding_not_a_failure(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    with_site(monkeypatch, NoLastAttemptSite())  # R6: Moodle leaves lastattempt out
    code, out, _ = run(["--offline"], capsys)
    assert code == 0
    assert "FINDING" in out and "lastattempt" in out and "R6" in out


def test_a_failing_step_is_shown_and_the_others_still_run(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    with_site(monkeypatch, DenyingSite({"core_enrol_get_enrolled_users"}))
    code, out, _ = run(["--offline"], capsys)
    assert code == 1
    assert "STEP 3 FAILED" in out
    assert "Step 4." in out and "Step 6." in out  # the rest still ran
    assert "FAILED" in out.split("RESULTS", 1)[1]


# --- options -------------------------------------------------------------------------------------


def test_check_is_quiet_and_exits_0(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = run(["--offline", "--check"], capsys)
    assert code == 0 and out == "" and err == ""


def test_dry_run_makes_no_call_and_lists_the_plan(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    connection = with_site(monkeypatch)
    code, out, _ = run(["--offline", "--dry-run"], capsys)
    assert code == 0
    assert "Dry run: no call is made and nothing is sent." in out
    for function in SIX:
        assert function in out
    assert "Step 1." not in out
    assert connection.fake is not None and connection.fake.functions_called == []


def test_a_bad_config_is_an_error_with_exit_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = tmp_path / "h4.yaml"
    config.write_text("course_id: not-a-number\n", encoding="utf-8")
    code, _, err = run(["--offline", "--config", str(config)], capsys)
    assert code == 2 and "--config" in err


def test_a_config_can_name_the_course(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = tmp_path / "h4.yaml"
    config.write_text("course_id: 2\n", encoding="utf-8")
    assert run(["--offline", "--check", "--config", str(config)], capsys)[0] == 0


# --- saving the full output ----------------------------------------------------------------------


def test_the_full_output_is_saved_outside_the_repository(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "h4-output.json"
    code, out, _ = run(["--offline", "--out", str(target)], capsys)
    assert code == 0
    saved = json.loads(target.read_text(encoding="utf-8"))
    assert set(SIX) <= set(saved["answers"])
    assert FAKE_TOKEN not in target.read_text(encoding="utf-8")
    assert "Saved the full output" in out


def test_an_output_path_inside_the_repository_is_refused(
    capsys: pytest.CaptureFixture[str],
) -> None:
    inside = ROOT / "docs" / "should-not-exist" / "h4.json"
    code, _, err = run(["--offline", "--out", str(inside)], capsys)
    assert code == 2 and "inside the repository" in err
    assert not inside.exists() and not inside.parent.exists()


# --- live mode: no lab here, so only what can be checked without one -----------------------------


def _script(*args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env=env,
    )


def _env_without_moodle() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith("MOODLE")}


def test_live_without_settings_exits_2_and_says_what_to_set() -> None:
    done = _script(env=_env_without_moodle())
    assert done.returncode == 2
    assert "MOODLE53_URL" in done.stderr and "--offline" in done.stderr


def test_a_live_dry_run_makes_no_call_and_never_shows_the_token() -> None:
    done = _script("--dry-run", env={**_env_without_moodle(), **LIVE_ENV})
    assert done.returncode == 0, done.stderr
    assert "Dry run: no call is made and nothing is sent." in done.stdout
    assert LIVE_TOKEN not in done.stdout + done.stderr
    assert "lab.invalid" not in done.stdout + done.stderr


def test_the_script_writes_nothing_into_the_repository() -> None:
    def state() -> str:
        done = subprocess.run(
            ["git", "status", "--porcelain", "--ignored", "--untracked-files=all"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return "\n".join(
            line for line in done.stdout.splitlines() if "__pycache__" not in line
        )

    before = state()
    assert _script("--offline", "--check", env=_env_without_moodle()).returncode == 0
    assert state() == before

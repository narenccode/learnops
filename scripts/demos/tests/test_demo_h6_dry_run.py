"""Tests for the H6 Tier 3 demo: the dry run (scripts/demos/demo_h6_dry_run.py).

The library's own checks (write_draft_grade) run on the answers of the site; at the write the
read-only connection stops it, so nothing is sent. Run offline against the built-in fake. What is
tested: the plan's expected results, that no write ever reaches the site, that the verdict "would
write" is shown only when a write attempt really reached (and was stopped by) the read-only
connection, and the options. The live path cannot be tested here (no lab, no network).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "libs"))
sys.path.insert(0, str(ROOT / "scripts" / "demos"))

import demo_h6_dry_run as demo  # noqa: E402
from demo_fake_site import FAKE_TOKEN  # noqa: E402
from fakes import NoLastAttemptSite, NoUsernameSite, install  # noqa: E402
from moodle_ws import FunctionNotAllowed  # noqa: E402

SCRIPT = ROOT / "scripts" / "demos" / "demo_h6_dry_run.py"
LIVE_TOKEN = "livelooking0value0for0tests"  # made up
LIVE_ENV = {
    "MOODLE53_URL": "https://moodle53.lab.invalid",
    "MOODLE53_WS_TOKEN": LIVE_TOKEN,
}
STOPPED = "write attempt: stopped by the read-only connection"
NOT_REACHED = "write attempt: none (refused by the library first)"


def run(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = demo.main(argv)
    out = capsys.readouterr()
    return code, out.out, out.err


def case_block(out: str, letter: str) -> str:
    """The lines of one case: its 'Case X:' line and the indented lines under it."""
    lines = out.splitlines()
    start = next(
        i for i, line in enumerate(lines) if line.startswith(f"Case {letter}:")
    )
    block = [lines[start]]
    for line in lines[start + 1 :]:
        if not line.startswith("    "):
            break
        block.append(line)
    return "\n".join(block)


# --- the plan's expected results -----------------------------------------------------------------


def test_the_four_cases_give_the_expected_results(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, _ = run(["--offline"], capsys)
    assert code == 0, out
    assert "WOULD WRITE readyforrelease: allowed" in case_block(out, "A")
    assert "REFUSED: locked (R3)" in case_block(out, "B")
    assert "REFUSED: workflow off" in case_block(out, "D")
    assert "NOT AS EXPECTED" not in out


def test_learner_c_prints_what_the_library_says_with_the_submission_status(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, out, _ = run(["--offline"], capsys)
    block = case_block(out, "C")
    assert "library says:" in block  # whatever it says; the plan says not to predict it
    assert "submission status: draft" in block
    # The library decides from the grading state only; shown, not hidden.
    assert "FINDING" in out and "grading state only" in out


def test_a_write_attempt_is_shown_only_where_the_library_got_that_far(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, out, _ = run(["--offline"], capsys)
    assert STOPPED in case_block(out, "A")
    assert NOT_REACHED in case_block(out, "B")
    assert NOT_REACHED in case_block(out, "D")
    assert out.count(STOPPED) == 2 and out.count(NOT_REACHED) == 2  # A and C; B and D


def test_no_write_ever_reaches_the_site(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    connection = install(monkeypatch, demo)
    assert run(["--offline"], capsys)[0] == 0
    assert connection.fake is not None
    called = connection.fake.functions_called
    assert "mod_assign_save_grade" not in called
    assert set(called) <= {
        "mod_assign_get_assignments",
        "core_enrol_get_enrolled_users",
        "mod_assign_get_submission_status",
    }
    assert (
        called.count("mod_assign_get_submission_status") >= 4
    )  # one state read per case


def test_the_last_line_says_nothing_was_sent(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, out, _ = run(["--offline"], capsys)
    assert out.rstrip("\n").splitlines()[-1] == (
        "OFFLINE: built-in fake, not a live run. Nothing was sent and nothing was "
        "written to Moodle."
    )


# --- when a result differs, or the stop is not what it seems -------------------------------------


def test_a_different_result_offline_is_not_as_expected_and_exits_1(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    install(monkeypatch, demo, NoLastAttemptSite())  # R6: the state cannot be read
    code, out, _ = run(["--offline"], capsys)
    assert code == 1
    assert "REFUSED: state unreadable (R6)" in out
    assert "NOT AS EXPECTED" in out


def test_a_refusal_without_a_write_attempt_is_never_called_allowed(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    install(monkeypatch, demo)

    def refuses_without_asking(*args: object, **kwargs: object) -> None:
        raise FunctionNotAllowed("refused")

    monkeypatch.setattr(demo, "write_draft_grade", refuses_without_asking)
    code, out, _ = run(["--offline"], capsys)
    assert code == 1
    assert "UNEXPECTED" in out
    # No case is shown as allowed. (The 'wanted WOULD WRITE' in a NOT AS EXPECTED line is fine.)
    assert not [line for line in out.splitlines() if "-> WOULD WRITE" in line]


def test_a_missing_learner_is_not_run_and_exits_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = tmp_path / "h6.yaml"
    config.write_text("learners:\n  A: nobody\n", encoding="utf-8")
    code, out, _ = run(["--offline", "--config", str(config)], capsys)
    assert code == 1
    assert "Case A:" in out and "NOT RUN" in out and "nobody" in out


# --- the site hides the learners' usernames (seen on the lab site) -------------------------------


def test_learners_are_found_by_full_name_when_usernames_are_hidden(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    install(monkeypatch, demo, NoUsernameSite())
    code, out, _ = run(["--offline"], capsys)
    assert code == 0, out
    assert "NOT RUN" not in out
    assert "WOULD WRITE readyforrelease: allowed" in case_block(out, "A")
    assert "REFUSED: locked (R3)" in case_block(out, "B")
    assert "REFUSED: workflow off" in case_block(out, "D")


def test_a_learner_can_be_named_by_id_in_the_config(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    install(monkeypatch, demo, NoUsernameSite())
    config = tmp_path / "h6.yaml"
    config.write_text(
        "learners:\n  A: 101\n  B: 102\n  C: 103\n  D: 104\n", encoding="utf-8"
    )
    code, out, _ = run(["--offline", "--config", str(config)], capsys)
    assert code == 0, out


def test_a_username_that_the_site_hides_is_not_run_and_says_what_to_use(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    install(monkeypatch, demo, NoUsernameSite())
    config = tmp_path / "h6.yaml"
    config.write_text("learners:\n  A: learner_a\n", encoding="utf-8")
    code, out, _ = run(["--offline", "--config", str(config)], capsys)
    assert code == 1
    assert "NOT RUN" in case_block(out, "A") and "full name or id" in case_block(
        out, "A"
    )


# --- options -------------------------------------------------------------------------------------


def test_check_is_quiet_and_exits_0(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = run(["--offline", "--check"], capsys)
    assert code == 0 and out == "" and err == ""


def test_dry_run_lists_the_cases_and_makes_no_call(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    connection = install(monkeypatch, demo)
    code, out, _ = run(["--offline", "--dry-run"], capsys)
    assert code == 0
    assert "Dry run: no call is made and nothing is sent." in out
    for letter in "ABCD":
        assert f"Learner {letter}" in out
    assert "Case A:" not in out
    assert connection.fake is not None and connection.fake.functions_called == []


@pytest.mark.parametrize(
    "text",
    [
        "course_id: nope\n",
        "learners: {A: ''}\n",
        "learners: {A: 0}\n",
        "learners: {A: true}\n",
        "learners: [a, b]\n",
        "- not a mapping\n",
    ],
)
def test_a_bad_config_is_an_error_with_exit_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], text: str
) -> None:
    config = tmp_path / "h6.yaml"
    config.write_text(text, encoding="utf-8")
    code, _, err = run(["--offline", "--config", str(config)], capsys)
    assert code == 2 and "--config" in err


def test_the_full_output_is_saved_outside_the_repository(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "h6-output.json"
    code, out, _ = run(["--offline", "--out", str(target)], capsys)
    assert code == 0 and "Saved the full output" in out
    assert FAKE_TOKEN not in target.read_text(encoding="utf-8")


def test_an_output_path_inside_the_repository_is_refused(
    capsys: pytest.CaptureFixture[str],
) -> None:
    inside = ROOT / "docs" / "should-not-exist" / "h6.json"
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

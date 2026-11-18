"""Tests for the H2 grading Tier 1 demo: its six cases, its options, its exit codes, and that it
sends nothing to any network and writes nothing into the repository.

The demo runs the real libs/moodle_ws code against a fake Moodle that follows the Moodle source
(libs/moodle_ws/tests/source_fake.py). It is not a live run, and these tests do not make it one.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "demos" / "demo_h2_grading_tier1.py"
LAST_LINE = "OFFLINE: against the Moodle 5.3 fake, not a live run"
# A made-up value, only used to prove it never reaches the output (PRD C-06).
FAKE_TOKEN = "fakevalue4tests2only"

# (case number, expected outcome name, rule shown, was a write sent?)
EXPECTED = [
    (1, "REFUSED_LOCKED", "R3", False),  # state `released`
    (2, "REFUSED_LOCKED", "R3", False),  # state `readyforrelease`
    (3, "REFUSED_STATE_UNKNOWN", "R6", False),
    (4, "REFUSED_WORKFLOW_OFF", "workflow off", False),
    (5, "NOT_VERIFIED", "R1", True),  # the fake silently ignores the grade
    (6, "VERIFIED", "R1", True),
]


def _run(
    *args: str, extra_env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, **(extra_env or {})}
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env=env,
    )


def _repository_state() -> str:
    # git status lists every new or changed file, so a demo that wrote into the repository would
    # show up here. Ignored files are listed too.
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


def _case_line(output: str, number: int) -> str:
    lines = [line for line in output.splitlines() if line.startswith(f"Case {number}:")]
    assert len(lines) == 1, f"expected one line for case {number}, got {lines}"
    return lines[0]


def test_the_demo_runs_and_every_case_is_as_expected() -> None:
    before = _repository_state()
    done = _run()
    assert done.returncode == 0, done.stdout + done.stderr
    assert "NOT AS EXPECTED" not in done.stdout
    assert _repository_state() == before, "the demo wrote into the repository"


@pytest.mark.parametrize(("number", "outcome", "rule", "sent"), EXPECTED)
def test_each_case_prints_its_outcome_rule_and_whether_a_write_was_sent(
    number: int, outcome: str, rule: str, sent: bool
) -> None:
    line = _case_line(_run().stdout, number)
    assert f"-> {outcome}" in line
    assert f"({rule})" in line
    assert f"write_sent={sent}" in line


def test_cases_1_and_2_are_both_r3_but_start_from_different_states() -> None:
    out = _run().stdout
    assert "released" in _case_line(out, 1)
    assert "readyforrelease" in _case_line(out, 2)


def test_the_last_line_says_it_is_offline() -> None:
    done = _run()
    assert done.stdout.rstrip("\n").splitlines()[-1] == LAST_LINE


def test_check_is_quiet_and_exits_0() -> None:
    done = _run("--check")
    assert done.returncode == 0, done.stderr
    assert done.stdout == ""


def test_dry_run_runs_no_case_and_says_so() -> None:
    before = _repository_state()
    done = _run("--dry-run")
    assert done.returncode == 0
    assert "Dry run: no case is run and nothing is sent." in done.stdout
    assert "Case 1:" not in done.stdout and "-> " not in done.stdout
    assert _repository_state() == before


def test_a_token_in_the_environment_never_appears_in_any_output() -> None:
    env = {"MOODLE53_WS_TOKEN": FAKE_TOKEN}
    for args in ((), ("--dry-run",), ("--check",)):
        done = _run(*args, extra_env=env)
        assert FAKE_TOKEN not in done.stdout + done.stderr


def test_config_with_the_supported_version_runs(tmp_path: Path) -> None:
    config = tmp_path / "h2.yaml"
    config.write_text('moodle_version: "5.3"\n', encoding="utf-8")
    done = _run("--check", "--config", str(config))
    assert done.returncode == 0, done.stderr


@pytest.mark.parametrize(
    "text", ['moodle_version: "4.5"\n', "other: 1\n", "- not a mapping\n"]
)
def test_a_bad_config_is_an_error_with_exit_2(tmp_path: Path, text: str) -> None:
    config = tmp_path / "h2.yaml"
    config.write_text(text, encoding="utf-8")
    done = _run("--config", str(config))
    assert done.returncode == 2
    assert "--config" in done.stderr


def test_a_missing_config_file_is_an_error_with_exit_2(tmp_path: Path) -> None:
    done = _run("--config", str(tmp_path / "no-such-file.yaml"))
    assert done.returncode == 2

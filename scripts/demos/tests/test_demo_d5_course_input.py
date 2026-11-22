"""Tests for the D5 demo script: its options, its exit codes, and that it writes nothing."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "demos" / "demo_d5_course_input.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _tracked_and_untracked() -> str:
    # git status lists every new or changed file, so a demo that wrote into the repository
    # would show up here. Ignored files are listed too, so .mbz-style leftovers are caught.
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


def test_the_demo_runs_and_every_result_is_as_expected() -> None:
    before = _tracked_and_untracked()
    done = _run()
    assert done.returncode == 0, done.stdout + done.stderr
    assert "RESULT: OK" in done.stdout
    assert done.stdout.count("REJECTED as expected") == 5
    assert "NOT AS EXPECTED" not in done.stdout
    assert "0 problems found" in done.stdout
    assert "D5 demo: everything as expected." in done.stdout
    assert _tracked_and_untracked() == before, "the demo wrote into the repository"


def test_check_is_quiet_and_exits_0() -> None:
    done = _run("--check")
    assert done.returncode == 0, done.stderr
    assert done.stdout == ""


def test_dry_run_does_nothing_and_says_so() -> None:
    before = _tracked_and_untracked()
    done = _run("--dry-run")
    assert done.returncode == 0
    assert "Dry run: nothing is created, validated or deleted." in done.stdout
    assert "REJECTED" not in done.stdout and "RESULT" not in done.stdout
    assert _tracked_and_untracked() == before


def test_config_names_another_package(tmp_path: Path) -> None:
    config = tmp_path / "d5.yaml"
    config.write_text(
        "package: contracts/examples/course-package.v1\n", encoding="utf-8"
    )
    done = _run("--check", "--config", str(config))
    assert done.returncode == 0, done.stderr


def test_a_missing_package_is_an_error_with_exit_2(tmp_path: Path) -> None:
    config = tmp_path / "d5.yaml"
    config.write_text("package: testdata/no-such-package\n", encoding="utf-8")
    done = _run("--config", str(config))
    assert done.returncode == 2
    assert "does not exist" in done.stderr


def test_an_unreadable_config_is_an_error_with_exit_2(tmp_path: Path) -> None:
    config = tmp_path / "d5.yaml"
    config.write_text("not-the-package-key: x\n", encoding="utf-8")
    done = _run("--config", str(config))
    assert done.returncode == 2
    assert "could not be read" in done.stderr


def test_a_package_that_is_already_broken_fails_step_1(tmp_path: Path) -> None:
    # Negative control: the demo must report a broken package, not call it OK.
    copy = tmp_path / "broken"
    shutil.copytree(ROOT / "testdata" / "b8-2-sample-course" / "package", copy)
    course = copy / "course.yaml"
    course.write_text(
        course.read_text(encoding="utf-8").replace("mode: full", "mode: everything"),
        encoding="utf-8",
    )
    config = tmp_path / "d5.yaml"
    config.write_text(f"package: {copy.as_posix()}\n", encoding="utf-8")
    done = _run("--config", str(config))
    assert done.returncode == 1
    assert "NOT AS EXPECTED" in done.stdout

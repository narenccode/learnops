"""CI must run the unit tests whenever modules/*/tests OR libs/*/tests exists, and the three
symlink tests must pass there, not skip.

The "Unit tests" step used `ls -d modules/*/tests libs/*/tests`, which fails when either pattern
matches nothing. With only libs/contracts/tests present, pytest never ran and nothing said so.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".github" / "scripts" / "has_tests.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def find_bash() -> str | None:
    """A bash that can read the script. The CI (Linux) uses `bash`. On Windows `bash` can be the
    WSL launcher, which fails with exit code 1: that would make the "no tests" cases pass for
    the wrong reason, so each candidate must first prove it can see the script."""
    candidates = [shutil.which("bash"), r"C:\Program Files\Git\bin\bash.exe"]
    for candidate in candidates:
        if candidate is None or not Path(candidate).exists():
            continue
        probe = subprocess.run(
            [candidate, "-c", f'test -f "{SCRIPT.as_posix()}"'],
            check=False,
            capture_output=True,
        )
        if probe.returncode == 0:
            return candidate
    return None


BASH = find_bash()
needs_bash = pytest.mark.skipif(BASH is None, reason="no usable bash found")


def run_in(folder: Path) -> int:
    # as_posix keeps the path usable by Git Bash on Windows; the CI runs this on Linux.
    assert BASH is not None
    done = subprocess.run([BASH, SCRIPT.as_posix()], cwd=folder, check=False)
    return done.returncode


@needs_bash
@pytest.mark.parametrize(
    ("folders", "expected"),
    [
        ([], 1),
        # Module and library folders exist, but there are no tests inside.
        (["modules/studio", "libs/contracts"], 1),
        # The case that was missed: libs has tests and there is no modules/*/tests at all.
        (["libs/contracts/tests"], 0),
        (["modules/studio/tests"], 0),
        (["modules/studio/tests", "libs/contracts/tests"], 0),
    ],
)
def test_has_tests_finds_either_location(
    tmp_path: Path, folders: list[str], expected: int
) -> None:
    for folder in folders:
        (tmp_path / folder).mkdir(parents=True)
    assert run_in(tmp_path) == expected


@needs_bash
def test_a_file_named_tests_is_not_a_tests_folder(tmp_path: Path) -> None:
    (tmp_path / "libs" / "contracts").mkdir(parents=True)
    (tmp_path / "libs" / "contracts" / "tests").write_text(
        "not a folder", encoding="utf-8"
    )
    assert run_in(tmp_path) == 1


@needs_bash
def test_this_repository_has_tests_to_run() -> None:
    # libs/contracts/tests exists; if this fails the library tests are no longer found.
    assert run_in(ROOT) == 0


def step_run(name: str) -> str:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["checks"]["steps"]
    (step,) = [s for s in steps if s.get("name") == name]
    return str(step["run"])


def test_unit_tests_step_uses_the_discovery_script_and_names_every_test() -> None:
    run = step_run("Unit tests")
    assert "has_tests.sh" in run
    assert "pytest -v -rs" in run
    assert "set -o pipefail" in run  # otherwise tee hides a failing pytest
    assert "ls -d" not in run


PACKAGE_TESTS = "libs/contracts/tests/test_validate_package.py"
REQUIRED = [
    "test_source_refuses_a_link_that_leaves_the_package",
    "test_source_follows_a_link_that_stays_inside_the_package",
    "test_body_that_is_a_link_leaving_the_package_is_an_error",
]


def run_guard(folder: Path, log_lines: list[str], *, tests_file: bool = True) -> int:
    """Run the "Symlink tests must pass" step in `folder` against a fake pytest -v log."""
    if tests_file:
        (folder / PACKAGE_TESTS).parent.mkdir(parents=True)
        (folder / PACKAGE_TESTS).write_text("", encoding="utf-8")
    text = "\n".join(log_lines) + "\n"
    (folder / "unit.log").write_text(text, encoding="utf-8")
    assert BASH is not None
    env = {**os.environ, "RUNNER_TEMP": folder.as_posix()}
    run = step_run("Symlink tests must pass, not skip")
    done = subprocess.run(
        [BASH, "-e", "-c", run], cwd=folder, env=env, check=False, capture_output=True
    )
    return done.returncode


def passed(name: str) -> str:
    return f"{PACKAGE_TESTS}::{name} PASSED [ 50%]"


@needs_bash
def test_guard_accepts_three_passed_even_with_an_unrelated_skip(tmp_path: Path) -> None:
    log = [passed(n) for n in REQUIRED]
    log.append("libs/other/tests/test_x.py::test_needs_gpu SKIPPED [ 90%]")
    assert run_guard(tmp_path, log) == 0


@needs_bash
@pytest.mark.parametrize("which", range(3))
def test_guard_fails_when_a_required_test_is_skipped(
    tmp_path: Path, which: int
) -> None:
    log = [passed(n) for n in REQUIRED]
    log[which] = f"{PACKAGE_TESTS}::{REQUIRED[which]} SKIPPED [ 50%]"
    assert run_guard(tmp_path, log) == 1


@needs_bash
def test_guard_fails_when_a_required_test_is_renamed_or_missing(tmp_path: Path) -> None:
    log = [passed(n) for n in REQUIRED[:2]]
    log.append(passed(REQUIRED[2] + "_renamed"))  # a longer name must not count
    assert run_guard(tmp_path, log) == 1


@needs_bash
def test_guard_does_nothing_before_the_package_tests_exist(tmp_path: Path) -> None:
    # main has no test_validate_package.py until the package-folder PR lands.
    assert run_guard(tmp_path, [], tests_file=False) == 0

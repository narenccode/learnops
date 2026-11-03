"""CI must run the unit tests whenever modules/*/tests OR libs/*/tests exists.

The "Unit tests" step used `ls -d modules/*/tests libs/*/tests`, which fails when either pattern
matches nothing. With only libs/contracts/tests present, pytest never ran and nothing said so.
"""

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


def unit_tests_step() -> str:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["checks"]["steps"]
    (step,) = [s for s in steps if s.get("name") == "Unit tests"]
    return str(step["run"])


def test_workflow_uses_the_discovery_script_and_lists_skips() -> None:
    run = unit_tests_step()
    assert "has_tests.sh" in run
    assert "pytest -q -rs" in run
    assert "ls -d" not in run

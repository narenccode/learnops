"""Tests for the D2 demo (`checker check <package> --json`): the B1-level course-package checker.

They check the script's options, exit codes and JSON, the four planted-error packages and their
answer file, and that the command writes nothing. They do not test the CK-01..CK-13 rules: D2 does
not implement them.
"""

from __future__ import annotations

import filecmp
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "demos" / "demo_d2_course_package_checker.py"
B82 = ROOT / "testdata" / "b8-2-sample-course" / "package"
B83 = ROOT / "testdata" / "b8-3-planted-errors"
ANSWER = yaml.safe_load((B83 / "answer.yaml").read_text(encoding="utf-8"))
CASES: list[dict[str, Any]] = ANSWER["cases"]
CASE_IDS = [case["id"] for case in CASES]


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _check(package: Path, *extra: str) -> tuple[int, dict[str, Any]]:
    done = _run("check", str(package), "--json", *extra)
    return done.returncode, json.loads(done.stdout)


def _status() -> str:
    # Every new or changed file shows up here, ignored files included.
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


# --- the clean sample ------------------------------------------------------------------------


def test_clean_b82_has_no_error_and_exit_code_0() -> None:
    code, report = _check(B82)
    assert code == 0
    assert report["findings"] == []
    assert report["summary"]["errors"] == 0


def test_clean_b82_is_never_presented_as_fully_checked() -> None:
    code, report = _check(B82)
    assert code == 0
    # The B1 validator lists rules it does not run, and the 13 CK rules are not run at all.
    layers = [entry["layer"] for entry in report["not_checked"]]
    assert layers.count("CK") == 13
    assert layers.count("B1") >= 1
    assert report["summary"]["not_checked"] == len(report["not_checked"]) > 0
    text = _run("check", str(B82)).stdout
    assert "Result: 0 errors, " in text and " not checked" in text
    assert "clean" not in (text + json.dumps(report)).lower()


# --- the report shape (checker design §3.6) ----------------------------------------------------


def test_json_shape_and_counts_agree_with_the_lists() -> None:
    _, report = _check(B83 / "missing-body" / "package")
    assert set(report) == {
        "checker_version",
        "input",
        "summary",
        "findings",
        "not_checked",
    }
    assert report["input"] == {
        "kind": "package",
        "name": "testdata/b8-3-planted-errors/missing-body/package",
    }
    assert report["summary"] == {
        "errors": len(report["findings"]),
        "warnings": 0,
        "not_checked": len(report["not_checked"]),
    }
    for finding in report["findings"]:
        assert finding["severity"] == "error"
        assert finding["location"] and finding["message"] and finding["fix_hint"]
    for entry in report["not_checked"]:
        # one state, `not checked`, and every entry names its item (design §3.6, finding 4)
        assert set(entry["item"]) == {"idnumber"}
        assert entry["reason"].strip()
        assert "cannot judge" not in json.dumps(entry)
    assert "ok" not in report


def test_report_has_no_absolute_path() -> None:
    done = _run("check", str(B82), "--json")
    assert str(ROOT) not in done.stdout


def test_ck_rules_say_why_they_did_not_run() -> None:
    _, clean = _check(B82)
    _, broken = _check(B83 / "invalid-mode" / "package")
    ck_clean = [e for e in clean["not_checked"] if e["layer"] == "CK"]
    ck_broken = [e for e in broken["not_checked"] if e["layer"] == "CK"]
    assert [e["rule"] for e in ck_clean] == [f"CK-{n:02d}" for n in range(1, 14)]
    assert all("Release 1" in e["reason"] for e in ck_clean)
    # design §3.4: a package that fails B1 lists every CK rule as not checked, with that reason
    assert all("failed B1 validation" in e["reason"] for e in ck_broken)


# --- each planted-error package ----------------------------------------------------------------


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
def test_planted_package_gives_exactly_the_one_expected_error(
    case: dict[str, Any],
) -> None:
    code, report = _check(B83 / case["package"])
    assert code == case["expected_exit_code"] == 1
    assert report["summary"]["errors"] == case["expected_error_count"] == 1
    assert len(report["findings"]) == 1
    (expected,) = case["errors"]
    (actual,) = report["findings"]
    assert actual["code"] == expected["code"]
    assert actual["rule"] == expected["rule"]
    assert actual["location"] == expected["location"]
    assert actual["item"]["idnumber"] == expected["idnumber"]
    assert actual["message"] == expected["message"]
    assert actual["layer"] == case["layer"] == "B1"


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
def test_planted_package_differs_from_b82_by_exactly_one_change(
    case: dict[str, Any],
) -> None:
    package = B83 / case["package"]
    diff = filecmp.dircmp(B82, package)
    weeks = filecmp.dircmp(B82 / "weeks", package / "weeks")
    changed = [f"{n}" for n in diff.diff_files] + [
        f"weeks/{n}" for n in weeks.diff_files
    ]
    missing = [n for n in diff.left_only] + [f"weeks/{n}" for n in weeks.left_only]
    extra = [n for n in diff.right_only] + [f"weeks/{n}" for n in weeks.right_only]
    assert extra == []
    if case["id"] == "missing-body":
        assert changed == [] and missing == ["weeks/02-task.md"]
        return
    assert missing == [] and changed == ["course.yaml"]
    before = (B82 / "course.yaml").read_text(encoding="utf-8").splitlines()
    after = (package / "course.yaml").read_text(encoding="utf-8").splitlines()
    assert len(before) == len(after)
    assert sum(1 for a, b in zip(before, after, strict=True) if a != b) == 1


def test_answer_file_lists_the_four_cases_and_the_layer() -> None:
    assert CASE_IDS == ["missing-body", "duplicate-id", "protected-id", "invalid-mode"]
    assert all(case["layer"] == "B1" for case in CASES)
    assert ANSWER["baseline"]["expected_exit_code"] == 0
    for case in CASES:
        assert (B83 / case["package"] / "course.yaml").is_file() or case["id"] == (
            "missing-body"
        )


def test_the_old_duplicate_id_defect_is_fixed() -> None:
    # The first version renamed wk-02-task, which broke week 3's `unlock.after` and gave two
    # errors. The fixture must not touch an idnumber that an unlock rule names.
    package = B83 / "duplicate-id" / "package"
    doc = yaml.safe_load((package / "course.yaml").read_text(encoding="utf-8"))
    named_by_unlock = {
        s["unlock"]["after"] for s in doc["sections"] if s["unlock"]["after"]
    }
    renamed = {
        a["idnumber"]
        for s in doc["sections"]
        for a in s["activities"]
        if a["idnumber"] == "wk-01-guide"
    }
    assert renamed == {"wk-01-guide"} and "wk-01-guide" not in named_by_unlock
    assert (
        "wk-02-task" in named_by_unlock
    )  # still present as an activity: nothing dangling


# --- plain text, --check, --dry-run ------------------------------------------------------------


def test_text_output_shows_each_error_with_its_location() -> None:
    done = _run("check", str(B83 / "duplicate-id" / "package"))
    assert done.returncode == 1
    assert (
        "duplicate_idnumber (B1.2 rule 6) at sections[1].activities[0].idnumber"
        in done.stdout
    )
    assert "Result: 1 error, " in done.stdout and "not checked" in done.stdout


def test_check_is_quiet_and_the_exit_code_is_the_answer() -> None:
    ok = _run("check", str(B82), "--check")
    bad = _run("check", str(B83 / "invalid-mode" / "package"), "--check", "--json")
    assert (ok.returncode, ok.stdout, ok.stderr) == (0, "", "")
    assert (bad.returncode, bad.stdout, bad.stderr) == (1, "", "")


def test_dry_run_validates_nothing_and_even_a_broken_package_gives_0() -> None:
    done = _run("check", str(B83 / "invalid-mode" / "package"), "--dry-run")
    assert done.returncode == 0
    assert "Dry run: nothing is read, validated or written" in done.stdout
    assert "Errors" not in done.stdout


def test_dry_run_and_check_together_are_refused() -> None:
    done = _run("check", str(B82), "--dry-run", "--check")
    assert done.returncode == 2
    assert "cannot be used together" in done.stderr


def test_running_writes_nothing_to_the_repository() -> None:
    before = _status()
    _run("check", str(B82), "--json")
    _run("check", str(B83 / "missing-body" / "package"))
    _run("check", str(B82), "--check")
    _run("check", str(B82), "--dry-run")
    assert _status() == before


# --- exit code 2 -----------------------------------------------------------------------------


def test_missing_package_is_exit_code_2(tmp_path: Path) -> None:
    done = _run("check", str(tmp_path / "nope"), "--json")
    assert done.returncode == 2
    assert "does not exist or is not a folder" in done.stderr
    assert done.stdout == ""


def test_a_file_instead_of_a_folder_is_exit_code_2(tmp_path: Path) -> None:
    file = tmp_path / "course.yaml"
    file.write_text("x: 1\n", encoding="utf-8")
    assert _run("check", str(file)).returncode == 2


def test_no_package_at_all_is_exit_code_2() -> None:
    done = _run("check", "--json")
    assert done.returncode == 2
    assert "No package folder was named" in done.stderr


def test_unknown_command_and_option_are_exit_code_2() -> None:
    assert _run("frobnicate").returncode == 2
    assert _run("check", str(B82), "--bogus").returncode == 2
    assert _run().returncode == 2


def test_an_empty_folder_is_an_error_finding_not_a_crash(tmp_path: Path) -> None:
    code, report = _check(tmp_path)
    assert code == 1
    assert report["findings"][0]["code"] == "course_yaml_missing"


# --- --config (decision 0020) ----------------------------------------------------------------


def _config(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "d2.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_config_can_name_the_package_and_ask_for_json(tmp_path: Path) -> None:
    config = _config(
        tmp_path,
        "package: testdata/b8-3-planted-errors/missing-body/package\njson: true\n",
    )
    done = _run("check", "--config", str(config))
    assert done.returncode == 1
    assert json.loads(done.stdout)["summary"]["errors"] == 1


def test_the_command_line_beats_the_config_file(tmp_path: Path) -> None:
    # config names a broken package; the command line names the clean one
    config = _config(
        tmp_path,
        "package: testdata/b8-3-planted-errors/missing-body/package\ncheck: true\n",
    )
    done = _run("check", str(B82), "--config", str(config))
    assert (
        done.returncode == 0
    )  # the argument won, and `check: true` from the file kept it quiet
    assert done.stdout == ""


def test_config_dry_run_key(tmp_path: Path) -> None:
    config = _config(tmp_path, "dry-run: true\n")
    done = _run("check", str(B83 / "invalid-mode" / "package"), "--config", str(config))
    assert done.returncode == 0 and "Dry run" in done.stdout


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("colour: blue\n", "unknown key: colour"),
        ("json: yes please\n", "the key json must be true or false"),
        ("check: 1\n", "the key check must be true or false"),
        ("package: [a, b]\n", "the key package must be text"),
        ("- just\n- a list\n", "must be a YAML mapping"),
        ("key: [unclosed\n", "could not be read"),
        ("dry-run: true\ncheck: true\n", "cannot be used together"),
    ],
)
def test_bad_config_is_refused_with_exit_code_2(
    tmp_path: Path, text: str, message: str
) -> None:
    config = _config(tmp_path, text)
    done = _run("check", str(B82), "--config", str(config))
    assert done.returncode == 2
    assert message in done.stderr
    assert done.stdout == ""


def test_missing_config_file_is_exit_code_2(tmp_path: Path) -> None:
    done = _run("check", str(B82), "--config", str(tmp_path / "absent.yaml"))
    assert done.returncode == 2
    assert "could not be read" in done.stderr


def test_an_empty_config_file_changes_nothing(tmp_path: Path) -> None:
    config = _config(tmp_path, "")
    assert _run("check", str(B82), "--config", str(config), "--check").returncode == 0

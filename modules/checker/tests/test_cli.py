from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
B8_3_ROOT = REPO_ROOT / "testdata" / "b8-3-planted-errors"
B8_2_PACKAGE = REPO_ROOT / "testdata" / "b8-2-sample-course" / "package"


def run_checker(package: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "checker.cli",
            "check",
            str(package),
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_clean_b8_2_package_passes() -> None:
    assert B8_2_PACKAGE.is_dir(), "B8.2 baseline package is missing."

    result = run_checker(B8_2_PACKAGE)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["ok"] is True
    assert report["errors"] == []


@pytest.mark.parametrize(
    ("case", "expected_code", "expected_location"),
    [
        ("missing-body", "body_file_missing", ["sections", 1, "activities", 1, "body"]),
        (
            "duplicate-id",
            "duplicate_idnumber",
            ["sections", 1, "activities", 1, "idnumber"],
        ),
        ("protected-id", "schema_not", ["sections", 3, "activities", 1, "idnumber"]),
        ("invalid-mode", "schema_enum", ["course", "mode"]),
    ],
)
def test_planted_error_is_reported(
    case: str, expected_code: str, expected_location: list[str | int]
) -> None:
    package = B8_3_ROOT / case / "package"
    result = run_checker(package)

    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert report["ok"] is False
    assert len(report["errors"]) == 1
    assert report["errors"][0]["code"] == expected_code
    assert report["errors"][0]["location"] == expected_location


def test_missing_package_returns_usage_error(tmp_path: Path) -> None:
    result = run_checker(tmp_path / "does-not-exist")

    assert result.returncode == 2
    assert "package directory not found" in result.stderr

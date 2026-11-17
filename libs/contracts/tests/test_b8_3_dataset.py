from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from contracts import DirectorySource, validate_package


REPO_ROOT = Path(__file__).resolve().parents[3]
ANSWER_PATH = REPO_ROOT / "testdata" / "b8-3-planted-errors" / "answer.yaml"
CASES = yaml.safe_load(ANSWER_PATH.read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_b8_3_planted_error_is_detected(case: dict) -> None:
    package = REPO_ROOT / "testdata" / "b8-3-planted-errors" / case["package"]
    assert package.is_dir(), f"Missing planted-error package: {package}"

    report = validate_package(DirectorySource(package))

    assert report.ok is case["expected_ok"]
    assert len(report.errors) == case["expected_error_count"]
    assert len(report.errors) == len(case["errors"])

    for actual, expected in zip(report.errors, case["errors"], strict=True):
        assert actual.code == expected["code"]
        assert actual.rule == expected["rule"]
        assert actual.location == tuple(expected["location"])
        assert actual.idnumber == expected["idnumber"]
        assert actual.message == expected["message"]

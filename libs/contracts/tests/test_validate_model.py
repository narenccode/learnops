"""`validate_course_model`: the public entry point for a B2 course model (PRD B.0 rule 4).

It runs the B2 schema and the run-time check of `source.timezone` (decision 0003 #20), and
returns the same `ValidationReport` as the B1 functions.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

import contracts
from contracts import ValidationReport, messages, validate_course_model

ROOT = Path(__file__).resolve().parents[3]
EXAMPLES = ROOT / "contracts" / "examples" / "course-model.v1"
PLACE = ("source", "timezone")

Doc = dict[str, Any]


def model(name: str) -> Doc:
    loaded: Doc = json.loads((EXAMPLES / name).read_text(encoding="utf-8"))
    return copy.deepcopy(loaded)


def codes(report: ValidationReport) -> list[str]:
    return [issue.code for issue in report.errors]


@pytest.mark.parametrize("name", ["from-package.json", "from-mbz.json"])
def test_both_examples_are_valid(name: str) -> None:
    report = validate_course_model(model(name))
    assert isinstance(report, ValidationReport)
    assert report.ok and report.errors == ()


@pytest.mark.parametrize("value", ["Mars/olympus", "UTC+5:30", "Asia/Kolkata ", "Asia"])
def test_an_unknown_timezone_is_rejected_through_the_public_api(value: str) -> None:
    package = model("from-package.json")
    package["source"]["timezone"] = value
    report = validate_course_model(package)
    (issue,) = report.errors
    assert issue.code == "timezone_unknown"
    assert issue.rule == "B2" and issue.location == PLACE
    assert repr(value) in issue.message and "SITE_TIMEZONE" in issue.fix_hint


def test_an_empty_timezone_is_a_schema_error_only() -> None:
    package = model("from-package.json")
    package["source"]["timezone"] = ""
    report = validate_course_model(package)
    assert codes(report) == ["schema_minLength"]
    assert report.errors[0].location == PLACE


@pytest.mark.parametrize("value", [5, 1.5, True, ["Asia/Kolkata"], {"a": 1}])
def test_a_timezone_that_is_not_text_is_a_schema_error_only(value: object) -> None:
    package = model("from-package.json")
    package["source"]["timezone"] = value
    report = validate_course_model(package)
    assert not report.ok and "timezone_unknown" not in codes(report)
    assert all(i.code == "schema_type" and i.location == PLACE for i in report.errors)


def test_an_unknown_timezone_on_an_mbz_model_gets_the_schema_and_the_runtime_error() -> (
    None
):
    mbz = model("from-mbz.json")
    mbz["source"]["timezone"] = "Mars/olympus"
    report = validate_course_model(mbz)
    assert codes(report) == ["schema_type", "timezone_unknown"]
    assert all(i.location == PLACE for i in report.errors)


def test_an_unknown_additional_field_is_accepted() -> None:
    # Decision 0003 #10 (EXT-02, A9): readers ignore fields they do not know.
    for name in ("from-package.json", "from-mbz.json"):
        doc = model(name)
        doc["future_field"] = {"x": 1}
        doc["source"]["future_field"] = True
        section = next(s for s in doc["sections"] if s["activities"])
        section["future_field"] = [1]
        section["activities"][0]["future_field"] = "y"
        assert validate_course_model(doc).ok, name


@pytest.mark.parametrize("name", ["Asia/Kolkata", "Asia/Calcutta", "UTC", "Etc/GMT-5"])
def test_a_known_timezone_is_accepted(name: str) -> None:
    package = model("from-package.json")
    package["source"]["timezone"] = name
    assert validate_course_model(package).ok


def test_a_package_without_a_timezone_is_a_schema_error_only() -> None:
    package = model("from-package.json")
    del package["source"]["timezone"]
    report = validate_course_model(package)
    assert codes(report) == ["schema_required"]
    assert report.errors[0].location == ("source",)


def test_a_package_with_a_null_timezone_is_a_schema_error_only() -> None:
    package = model("from-package.json")
    package["source"]["timezone"] = None
    report = validate_course_model(package)
    assert not report.ok
    assert "timezone_unknown" not in codes(report)
    assert all(i.location == PLACE for i in report.errors)


def test_an_mbz_model_must_keep_a_null_timezone() -> None:
    mbz = model("from-mbz.json")
    assert mbz["source"]["timezone"] is None and validate_course_model(mbz).ok
    mbz["source"]["timezone"] = "Asia/Kolkata"
    report = validate_course_model(mbz)
    assert codes(report) == ["schema_type"] and report.errors[0].location == PLACE


def test_schema_and_timezone_errors_are_combined_in_one_report() -> None:
    package = model("from-package.json")
    package["source"]["timezone"] = "Mars/olympus"
    del package["course"]["shortname"]
    report = validate_course_model(package)
    assert codes(report) == ["schema_required", "timezone_unknown"]
    schema_issue, timezone_issue = report.errors
    assert schema_issue.rule == "B2" and schema_issue.location == ("course",)
    assert timezone_issue.location == PLACE


def test_schema_errors_use_the_b2_schema_and_wording() -> None:
    report = validate_course_model(model("from-package.json") | {"schema": "x"})
    (issue,) = report.errors
    assert (
        issue.code == "schema_const"
        and issue.rule == "B2"
        and issue.location == ("schema",)
    )
    assert "course-model.v1.schema.json" in issue.fix_hint
    assert "course.yaml" not in issue.message + issue.fix_hint


def test_a_b1_document_is_not_a_course_model() -> None:
    report = validate_course_model(
        {"schema": "learnops.course-package/v1", "course": {}}
    )
    found = {(i.code, i.location) for i in report.errors}
    assert found == {
        ("schema_const", ("schema",)),
        (
            "schema_required",
            (),
        ),  # source, sections, course_completion and badges are missing
        (
            "schema_required",
            ("course",),
        ),  # shortname and completion_enabled are missing
    }
    assert all(i.rule == "B2" for i in report.errors)


def test_a_raw_moodle_activity_type_is_rejected() -> None:
    package = model("from-package.json")
    package["sections"][0]["activities"][0]["type"] = "assign"
    report = validate_course_model(package)
    assert "schema_not" in codes(report)


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        "text",
        42,
        {},
        {"source": None},
        {"source": "x"},
        {"source": []},
        {"source": {}},
        {"source": {"kind": "package", "timezone": ["Asia/Kolkata"]}},
        {"source": {"kind": "package", "timezone": 5}},
        {"source": {"kind": "package", "timezone": {"a": 1}}},
        {"sections": "x", "source": {"timezone": "Mars/olympus"}},
    ],
)
def test_malformed_input_gives_a_report_and_never_raises(bad: object) -> None:
    report = validate_course_model(bad)
    assert isinstance(report, ValidationReport) and not report.ok
    assert all(i.rule == "B2" for i in report.errors)


def test_the_whole_document_location_reads_as_the_course_model() -> None:
    (issue, *_) = validate_course_model([]).errors
    assert issue.location == () and issue.message.startswith(messages.MODEL_NAME)


def test_the_report_leaves_not_checked_empty_and_does_not_mutate_the_input() -> None:
    package = model("from-package.json")
    package["source"]["timezone"] = "Mars/olympus"
    before = copy.deepcopy(package)
    report = validate_course_model(package)
    assert report.not_checked == () and package == before


def test_the_name_is_exported_and_b1_functions_are_unchanged() -> None:
    assert "validate_course_model" in contracts.__all__
    assert contracts.validate_course_model is validate_course_model
    for name in ("validate_package", "validate_course_document"):
        assert name in contracts.__all__
    b1 = contracts.validate_course_document(model("from-package.json"))
    assert not b1.ok and "schema_required" in codes(b1)

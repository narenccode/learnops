"""Validating a parsed course.yaml against the B1 schema (PRD B.0 rule 4, B1.1, B1.4 defaults).

Covered here: the schema stage and the report it returns. NOT covered, on purpose, because ownership
or details are still undecided (see HELD_RULE_CODES): one Page and one Assignment per week, the
unlock chain, the marking table, the Check vocabulary and protected_section. The validator must
report those as "not checked".
"""

from __future__ import annotations

from typing import Any

import pytest

from contracts import validate_course_document

from .helpers import (
    HELD_RULE_CODES,
    WEEK1,
    WEEK1_GUIDE,
    WEEK2,
    Doc,
    error_codes,
    not_checked_codes,
    only,
)

# --- the example, and the rules that are held back ------------------------------------------


def test_example_document_has_no_errors(example_doc: Doc) -> None:
    report = validate_course_document(example_doc)
    assert report.errors == ()
    assert report.ok


def test_held_rules_are_reported_as_not_checked_never_skipped_silently(
    example_doc: Doc,
) -> None:
    report = validate_course_document(example_doc)
    assert not_checked_codes(report) == HELD_RULE_CODES
    for issue in report.not_checked:
        assert issue.rule and issue.message and issue.fix_hint


def test_a_document_with_weekly_structure_problems_is_not_judged_here(
    example_doc: Doc,
) -> None:
    # Held: whether a week has exactly one Page and one Assignment is not decided yet, so this
    # validator must not report an error for it (and must not claim to have checked it).
    del example_doc["sections"][0]["activities"][0]  # week 1 has no guide page
    report = validate_course_document(example_doc)
    assert report.errors == ()
    assert "week_structure_not_checked" in not_checked_codes(report)


# --- the schema stage -----------------------------------------------------------------------


def test_schema_errors_are_reported_with_their_place(example_doc: Doc) -> None:
    del example_doc["sections"][0]["title"]
    report = validate_course_document(example_doc)
    issue = only(report.errors)
    assert issue.code == "schema_required"
    assert issue.rule == "B1.1"
    assert issue.location == WEEK1
    assert "sections[0]" in issue.message
    assert issue.fix_hint


def test_every_schema_error_is_reported_not_only_the_first(example_doc: Doc) -> None:
    example_doc["course"]["mode"] = "partial"
    example_doc["sections"][0]["number"] = 0
    codes = error_codes(validate_course_document(example_doc))
    assert sorted(codes) == ["schema_enum", "schema_minimum"]


def test_an_impossible_calendar_date_is_rejected(example_doc: Doc) -> None:
    # Needs the format checker to be switched on in the validator.
    example_doc["sections"][1]["unlock"]["start_date"] = "2026-02-31"
    issue = only(validate_course_document(example_doc).errors)
    assert issue.code == "schema_format"
    assert issue.location == WEEK2 + ("unlock", "start_date")


@pytest.mark.parametrize("value", [[], None, 1, "learnops.course/v1"], ids=repr)
def test_a_document_that_is_not_an_object_is_an_error(value: Any) -> None:
    issue = only(validate_course_document(value).errors)
    assert issue.code == "schema_type"
    assert issue.location == ()


def test_default_protected_idnumbers_are_left_to_the_schema(example_doc: Doc) -> None:
    # The schema already rejects final-project and course-feedback. The validator does not
    # report them a second time.
    example_doc["sections"][0]["activities"][0]["idnumber"] = "final-project"
    report = validate_course_document(example_doc)
    assert [i.code for i in report.errors] == ["schema_not"]
    assert report.errors[0].location == WEEK1_GUIDE + ("idnumber",)


@pytest.mark.parametrize("value", ["final-project", "course-feedback"])
def test_default_protected_idnumber_gets_a_clear_message(
    example_doc: Doc, value: str
) -> None:
    example_doc["sections"][0]["idnumber"] = value
    issue = only(validate_course_document(example_doc).errors)
    assert value in issue.message and "protected" in issue.message
    assert "sections[0].idnumber" in issue.message
    assert "template" in issue.fix_hint

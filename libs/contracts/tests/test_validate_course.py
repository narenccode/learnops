"""Whole-course validation of a parsed course.yaml (PRD B.0 rule 4, B1.2 rules 3 and 6, B1.4).

Covered here: the schema stage, unique idnumbers, extra protected idnumbers from configuration,
and the points total. NOT covered, on purpose, because ownership or details are still undecided
(see HELD_RULE_CODES): one Page and one Assignment per week, the unlock chain, the marking table,
the Check vocabulary and protected_section. The validator must report those as "not checked".
"""

from __future__ import annotations

from typing import Any

import pytest

from contracts import (
    ConfigError,
    ValidationConfig,
    validate_course_document,
)

from .helpers import (
    HELD_RULE_CODES,
    WEEK1,
    WEEK1_GUIDE,
    WEEK1_TASK,
    WEEK2,
    WEEK2_GUIDE,
    WEEK2_TASK,
    Doc,
    error_codes,
    not_checked_codes,
    only,
)


def section_id(doc: Doc, index: int) -> str:
    return str(doc["sections"][index]["idnumber"])


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


def test_rules_that_need_a_sound_structure_wait_for_it(example_doc: Doc) -> None:
    del example_doc["sections"][0]["title"]  # a schema error
    example_doc["sections"][1]["idnumber"] = "wk-01"  # would be a duplicate
    report = validate_course_document(example_doc)
    assert error_codes(report) == ["schema_required"]
    assert "cross_rules_not_checked" in not_checked_codes(report)


# --- unique idnumbers (B1.2 rule 6) ---------------------------------------------------------


@pytest.mark.parametrize(
    ("duplicate_at", "value", "first_text"),
    [
        pytest.param(
            WEEK1_TASK + ("idnumber",),
            "wk-01-guide",
            "sections[0].activities[0].idnumber",
            id="two activities in one week",
        ),
        pytest.param(
            WEEK2_GUIDE + ("idnumber",),
            "wk-01-guide",
            "sections[0].activities[0].idnumber",
            id="activities in different weeks",
        ),
        pytest.param(
            WEEK2 + ("idnumber",),
            "wk-01",
            "sections[0].idnumber",
            id="two sections",
        ),
        pytest.param(
            WEEK2 + ("idnumber",),
            "wk-01-task",
            "sections[0].activities[1].idnumber",
            id="a section and an activity share one namespace",
        ),
    ],
)
def test_duplicate_idnumber_is_an_error_at_the_later_use(
    example_doc: Doc,
    duplicate_at: tuple[str | int, ...],
    value: str,
    first_text: str,
) -> None:
    node: Any = example_doc
    for key in duplicate_at[:-1]:
        node = node[key]
    node[duplicate_at[-1]] = value

    issue = only(validate_course_document(example_doc).errors)
    assert issue.code == "duplicate_idnumber"
    assert issue.rule == "B1.2 rule 6"
    assert issue.location == duplicate_at
    assert issue.idnumber == value
    # The message names the first use so the mentor can find both.
    assert value in issue.message
    assert first_text in issue.message
    assert issue.fix_hint


def test_an_idnumber_used_three_times_is_reported_for_each_extra_use(
    example_doc: Doc,
) -> None:
    for place in (WEEK1_TASK, WEEK2_GUIDE):
        example_doc["sections"][place[1]]["activities"][place[3]]["idnumber"] = (
            "wk-01-guide"
        )
    report = validate_course_document(example_doc)
    assert error_codes(report) == ["duplicate_idnumber", "duplicate_idnumber"]
    assert {i.location for i in report.errors} == {
        WEEK1_TASK + ("idnumber",),
        WEEK2_GUIDE + ("idnumber",),
    }


def test_similar_idnumbers_are_not_duplicates(example_doc: Doc) -> None:
    example_doc["sections"][0]["activities"][0]["idnumber"] = "wk-01-guide-2"
    assert validate_course_document(example_doc).errors == ()


# --- extra protected idnumbers (B1.4), passed in as configuration ---------------------------

CONFIG = ValidationConfig(protected_idnumbers=frozenset({"capstone-gate"}))


@pytest.mark.parametrize("mode", ["full", "sections-only"])
@pytest.mark.parametrize(
    "place",
    [WEEK1 + ("idnumber",), WEEK1_GUIDE + ("idnumber",), WEEK2_TASK + ("idnumber",)],
    ids=["section", "page", "assignment"],
)
def test_configured_protected_idnumber_is_rejected_in_both_modes(
    example_doc: Doc, mode: str, place: tuple[str | int, ...]
) -> None:
    example_doc["course"]["mode"] = mode
    node: Any = example_doc
    for key in place[:-1]:
        node = node[key]
    node[place[-1]] = "capstone-gate"

    issue = only(validate_course_document(example_doc, config=CONFIG).errors)
    assert issue.code == "protected_idnumber"
    assert issue.rule == "B1.4"
    assert issue.location == place
    assert issue.idnumber == "capstone-gate"
    assert "template" in issue.fix_hint


def test_a_configured_protected_idnumber_is_allowed_when_not_configured(
    example_doc: Doc,
) -> None:
    example_doc["sections"][0]["activities"][0]["idnumber"] = "capstone-gate"
    assert validate_course_document(example_doc).errors == ()


def test_only_an_exact_match_is_protected(example_doc: Doc) -> None:
    example_doc["sections"][0]["activities"][0]["idnumber"] = "capstone-gate-draft"
    assert validate_course_document(example_doc, config=CONFIG).errors == ()


def test_protected_and_duplicate_problems_are_both_reported(example_doc: Doc) -> None:
    example_doc["sections"][0]["activities"][0]["idnumber"] = "capstone-gate"
    example_doc["sections"][1]["activities"][0]["idnumber"] = "capstone-gate"
    codes = error_codes(validate_course_document(example_doc, config=CONFIG))
    assert sorted(codes) == [
        "duplicate_idnumber",
        "protected_idnumber",
        "protected_idnumber",
    ]


@pytest.mark.parametrize("bad", ["", "Final Project", "a_b", "-a", "a-", "é", "a\n"])
def test_a_configured_idnumber_must_be_a_valid_idnumber(bad: str) -> None:
    with pytest.raises(ConfigError):
        ValidationConfig(protected_idnumbers=frozenset({bad}))


def test_default_configuration_adds_no_protected_idnumbers() -> None:
    assert ValidationConfig().protected_idnumbers == frozenset()


# --- points total (B1.2 rule 3) -------------------------------------------------------------
# What counts as "graded points" and whether a sections-only package is checked are open
# questions for the guide (design notes D3 and D4). These tests record the narrow rule that is
# implemented: in `full` mode, the sum of `points` on assignments equals course.total_points
# (default 100), and nothing is claimed for `sections-only`.


def test_points_that_add_up_are_accepted(example_doc: Doc) -> None:
    assert validate_course_document(example_doc).errors == ()


def test_points_that_do_not_add_up_are_an_error(example_doc: Doc) -> None:
    example_doc["sections"][1]["activities"][1]["points"] = 40
    issue = only(validate_course_document(example_doc).errors)
    assert issue.code == "points_total_mismatch"
    assert issue.rule == "B1.2 rule 3"
    assert issue.location == ("course", "total_points")
    assert "90" in issue.message and "100" in issue.message
    assert issue.fix_hint


def test_points_above_the_total_are_an_error_too(example_doc: Doc) -> None:
    example_doc["sections"][1]["activities"][1]["points"] = 60
    issue = only(validate_course_document(example_doc).errors)
    assert issue.code == "points_total_mismatch"
    assert "110" in issue.message and "100" in issue.message


def test_total_points_defaults_to_100(example_doc: Doc) -> None:
    del example_doc["course"]["total_points"]
    assert validate_course_document(example_doc).errors == ()
    example_doc["sections"][0]["activities"][1]["points"] = 10
    assert error_codes(validate_course_document(example_doc)) == [
        "points_total_mismatch"
    ]


def test_a_custom_total_is_used(example_doc: Doc) -> None:
    example_doc["course"]["total_points"] = 60
    example_doc["sections"][0]["activities"][1]["points"] = 30
    example_doc["sections"][1]["activities"][1]["points"] = 30
    assert validate_course_document(example_doc).errors == ()


def test_only_assignment_points_are_counted(example_doc: Doc) -> None:
    # A page cannot be graded, so a stray "points" on one does not change the total.
    example_doc["sections"][0]["activities"][0]["points"] = 5
    assert validate_course_document(example_doc).errors == ()


@pytest.mark.parametrize("points", [10, 50], ids=["wrong sum", "right sum"])
def test_sections_only_packages_are_not_checked_for_points(
    example_doc: Doc, points: int
) -> None:
    example_doc["course"]["mode"] = "sections-only"
    example_doc["sections"][1]["activities"][1]["points"] = points
    report = validate_course_document(example_doc)
    assert report.errors == ()
    assert "points_total_not_checked_sections_only" in not_checked_codes(report)


def test_full_packages_are_never_marked_as_not_checked_for_points(
    example_doc: Doc,
) -> None:
    report = validate_course_document(example_doc)
    assert "points_total_not_checked_sections_only" not in not_checked_codes(report)


# --- public API -----------------------------------------------------------------------------


def test_public_names_are_exported_from_the_package() -> None:
    import contracts

    for name in (
        "ConfigError",
        "DirectorySource",
        "FileState",
        "Issue",
        "PackageSource",
        "ValidationConfig",
        "ValidationReport",
        "validate_course_document",
        "validate_package",
    ):
        assert hasattr(contracts, name), name

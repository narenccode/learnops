"""Validating a parsed course.yaml (PRD B.0 rule 4, B1.1, B1.2 rule 6, B1.4).

Covered here: the schema stage, idnumbers unique within one package (B1.2 rule 6, first half)
and the protected idnumbers a site adds to the two defaults (B1.4, passed in as configuration).
NOT covered, on purpose, because ownership or details are still undecided (see
HELD_RULE_CODES): one Page and one Assignment per week, the unlock chain, the points total,
completion on unlock activities, an idnumber never reused across package versions (B1.2 rule 6,
second half), that body files exist (needs the package folder), the marking table, the
Check vocabulary and protected_section. The validator must
report those as "not checked". The settings object is tested in test_config.py.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

from contracts import ConfigError, ValidationConfig, messages, validate_course_document

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


def test_errors_are_ordered_by_number_not_by_text(example_doc: Doc) -> None:
    # sections[2] must come before sections[10]; sorting the places as text gets this wrong.
    week = example_doc["sections"][0]
    example_doc["sections"] = [copy.deepcopy(week) for _ in range(12)]
    for index in (10, 2):  # broken in reverse order, so the input order proves nothing
        del example_doc["sections"][index]["title"]
    report = validate_course_document(example_doc)
    assert [issue.location for issue in report.errors] == [
        ("sections", 2),
        ("sections", 10),
    ]


def test_an_impossible_calendar_date_is_rejected(example_doc: Doc) -> None:
    # Needs the format checker to be switched on in the validator.
    example_doc["sections"][1]["unlock"]["start_date"] = "2026-02-31"
    issue = only(validate_course_document(example_doc).errors)
    assert issue.code == "schema_format"
    assert issue.location == WEEK2 + ("unlock", "start_date")


@pytest.mark.parametrize("value", [[], None, 1, "learnops.course/v1"], ids=repr)
def test_a_document_that_is_not_an_object_is_an_error(value: Any) -> None:
    for config in (None, CONFIG):  # no course-level rule can run on a non-object
        report = validate_course_document(value, config=config)
        issue = only(report.errors)
        assert issue.code == "schema_type"
        assert issue.location == ()
        assert "cross_rules_not_checked" in not_checked_codes(report)


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


# --- the course-level rules wait for a valid structure ---------------------------------------


ID = ("idnumber",)
W1, W1G, W1T, W2, W2G = (
    p + ID for p in (WEEK1, WEEK1_GUIDE, WEEK1_TASK, WEEK2, WEEK2_GUIDE)
)


def set_at(doc: Doc, place: tuple[str | int, ...], value: Any) -> None:
    node: Any = doc
    for key in place[:-1]:
        node = node[key]
    node[place[-1]] = value


def break_the_structure_elsewhere(doc: Doc) -> None:
    """A schema error that has nothing to do with idnumbers."""
    set_at(doc, WEEK1_TASK + ("submission",), ["zip"])


def test_any_schema_error_holds_back_the_idnumber_rules(example_doc: Doc) -> None:
    # The whole document must be valid first, even when the schema error is somewhere else.
    break_the_structure_elsewhere(example_doc)
    set_at(example_doc, W2, "wk-01")  # a duplicate
    set_at(example_doc, W1G, "capstone-gate")  # a configured protected idnumber
    report = validate_course_document(example_doc, config=CONFIG)
    assert error_codes(report) == ["schema_enum"]
    # The report says the rules did not run, in addition to the rules not implemented.
    assert not_checked_codes(report) == HELD_RULE_CODES | {"cross_rules_not_checked"}


def test_the_course_level_notice_names_no_rule(example_doc: Doc) -> None:
    # It must stay true when more course-level rules are implemented, so it lists none of them.
    del example_doc["sections"][0]["title"]
    notices = {i.code: i for i in validate_course_document(example_doc).not_checked}
    notice = notices["cross_rules_not_checked"]
    assert "idnumber" not in notice.message
    assert notice.rule == "B1.2, B1.4"
    assert notice.message and notice.fix_hint


def test_cross_version_reuse_of_idnumbers_is_listed_as_not_checked(
    example_doc: Doc,
) -> None:
    # Only the within-package half of B1.2 rule 6 is implemented. The other half, that an
    # idnumber is never reused for a different activity, needs the previous package version.
    notices = {i.code: i for i in validate_course_document(example_doc).not_checked}
    assert "idnumber_unique_not_checked" not in notices
    assert "extra_protected_idnumbers_not_checked" not in notices
    reuse = notices["idnumber_reuse_not_checked"]
    assert reuse.rule == "B1.2 rule 6"
    assert "never reused" in reuse.message and "previous version" in reuse.message
    assert reuse.fix_hint


def test_body_files_are_listed_as_not_checked_and_never_looked_for(
    example_doc: Doc,
) -> None:
    example_doc["sections"][0]["activities"][0]["body"] = "weeks/no-such-file.md"
    report = validate_course_document(example_doc)
    notice = {i.code: i for i in report.not_checked}["body_files_not_checked"]
    assert report.errors == ()
    assert notice.rule == "B1.1" and "package folder" in notice.message


# --- idnumbers unique within one package (B1.2 rule 6, first half) ----------------------------


# (place edited, new value, place of the error, place of the first use). The error is always the
# use that comes later in the document, whichever place was edited.
DUPLICATES = [
    (W1T, "wk-01-guide", W1T, W1G),  # two activities in one week
    (W2G, "wk-01-guide", W2G, W1G),  # activities in different weeks
    (W2, "wk-01", W2, W1),  # two sections
    (W2, "wk-01-task", W2, W1T),  # a section reuses an earlier activity idnumber
    (W2G, "wk-01", W2G, W1),  # an activity reuses an earlier section idnumber
    (W1G, "wk-02", W2, W1G),  # an activity reuses a later section idnumber
    (W1G, "wk-02-guide", W2G, W1G),  # the earlier activity was the one edited
]


@pytest.mark.parametrize(("edit_at", "value", "error_at", "first_at"), DUPLICATES)
def test_duplicate_idnumber_is_an_error_at_the_later_use(
    example_doc: Doc,
    edit_at: tuple[str | int, ...],
    value: str,
    error_at: tuple[str | int, ...],
    first_at: tuple[str | int, ...],
) -> None:
    set_at(example_doc, edit_at, value)
    issue = only(validate_course_document(example_doc).errors)
    assert issue.code == "duplicate_idnumber"
    assert issue.rule == "B1.2 rule 6"
    assert issue.location == error_at
    assert issue.idnumber == value
    assert issue.fix_hint
    # The message starts with the place of the error and names the first use, so that the
    # mentor can find both.
    first = messages.where(first_at)
    assert issue.message.startswith(f"{messages.where(error_at)}: ")
    assert f"the idnumber '{value}' is already used at {first}." in issue.message


def test_an_idnumber_used_three_times_is_reported_for_each_extra_use(
    example_doc: Doc,
) -> None:
    for place in (WEEK1_TASK, WEEK2_GUIDE):
        set_at(example_doc, place + ("idnumber",), "wk-01-guide")
    report = validate_course_document(example_doc)
    assert error_codes(report) == ["duplicate_idnumber", "duplicate_idnumber"]
    assert [i.location for i in report.errors] == [
        WEEK1_TASK + ("idnumber",),
        WEEK2_GUIDE + ("idnumber",),
    ]
    # Both name the first use, never each other.
    for issue in report.errors:
        assert "already used at sections[0].activities[0].idnumber." in issue.message


def test_two_different_duplicated_ids_are_both_reported_in_document_order(
    example_doc: Doc,
) -> None:
    set_at(example_doc, WEEK2_TASK + ("idnumber",), "wk-01-task")
    set_at(example_doc, WEEK2 + ("idnumber",), "wk-01")
    report = validate_course_document(example_doc)
    assert [(i.idnumber, i.location) for i in report.errors] == [
        ("wk-01", WEEK2 + ("idnumber",)),
        ("wk-01-task", WEEK2_TASK + ("idnumber",)),
    ]


def test_similar_idnumbers_are_not_duplicates(example_doc: Doc) -> None:
    set_at(example_doc, WEEK1_GUIDE + ("idnumber",), "wk-01-guide-2")
    set_at(example_doc, WEEK2 + ("idnumber",), "wk-1")
    assert validate_course_document(example_doc).errors == ()


def test_duplicate_idnumbers_are_an_error_in_sections_only_mode_too(
    example_doc: Doc,
) -> None:
    example_doc["course"]["mode"] = "sections-only"
    set_at(example_doc, WEEK2 + ("idnumber",), "wk-01")
    issue = only(validate_course_document(example_doc).errors)
    assert issue.code == "duplicate_idnumber"
    assert issue.location == WEEK2 + ("idnumber",)


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
    set_at(example_doc, place, "capstone-gate")
    issue = only(validate_course_document(example_doc, config=CONFIG).errors)
    assert issue.code == "protected_idnumber"
    assert issue.rule == "B1.4"
    assert issue.location == place
    assert issue.idnumber == "capstone-gate"
    assert issue.message.startswith(f"{messages.where(place)}: ")
    assert "'capstone-gate' is a protected idnumber" in issue.message
    assert "template" in issue.fix_hint


def test_only_an_exact_match_is_protected(example_doc: Doc) -> None:
    set_at(example_doc, WEEK1_GUIDE + ("idnumber",), "capstone-gate-draft")
    set_at(example_doc, WEEK2_GUIDE + ("idnumber",), "capstone")
    assert validate_course_document(example_doc, config=CONFIG).errors == ()


def test_several_configured_ids_are_each_rejected_in_document_order(
    example_doc: Doc,
) -> None:
    set_at(example_doc, WEEK1_GUIDE + ("idnumber",), "pilot-gate")
    set_at(example_doc, WEEK2_TASK + ("idnumber",), "capstone-gate")
    # Two ways to write the same settings: the result must not depend on the order given.
    for given in (["capstone-gate", "pilot-gate"], ["pilot-gate", "capstone-gate"]):
        config = ValidationConfig(protected_idnumbers=given)
        report = validate_course_document(example_doc, config=config)
        assert [(i.idnumber, i.location) for i in report.errors] == [
            ("pilot-gate", WEEK1_GUIDE + ("idnumber",)),
            ("capstone-gate", WEEK2_TASK + ("idnumber",)),
        ]


def test_protected_and_duplicate_problems_are_both_reported(example_doc: Doc) -> None:
    set_at(example_doc, WEEK1_GUIDE + ("idnumber",), "capstone-gate")
    set_at(example_doc, WEEK2_GUIDE + ("idnumber",), "capstone-gate")
    report = validate_course_document(example_doc, config=CONFIG)
    # Duplicates first, then protected ids, each in document order.
    assert [(i.code, i.location) for i in report.errors] == [
        ("duplicate_idnumber", WEEK2_GUIDE + ("idnumber",)),
        ("protected_idnumber", WEEK1_GUIDE + ("idnumber",)),
        ("protected_idnumber", WEEK2_GUIDE + ("idnumber",)),
    ]


@pytest.mark.parametrize(
    ("config", "value"),
    [
        (CONFIG, "course-feedback"),
        (ValidationConfig(["final-project"]), "final-project"),
    ],
    ids=["configured ids add to the defaults", "a default listed again, reported once"],
)
def test_a_default_protected_id_is_always_rejected_and_reported_once(
    example_doc: Doc, config: ValidationConfig, value: str
) -> None:
    set_at(example_doc, W1G, value)
    assert error_codes(validate_course_document(example_doc, config=config)) == [
        "schema_not"
    ]


def test_the_library_reads_no_environment_variables(
    example_doc: Doc, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Settings arrive only through ValidationConfig (root CLAUDE.md §2.3). The variable name is
    # the one Course Studio plans to read; the library must ignore it.
    monkeypatch.setenv("STUDIO_PROTECTED_IDNUMBERS", "capstone-gate")
    set_at(example_doc, WEEK1_GUIDE + ("idnumber",), "capstone-gate")
    assert validate_course_document(example_doc).errors == ()


def test_the_document_is_not_changed_by_validation(example_doc: Doc) -> None:
    before = copy.deepcopy(example_doc)
    validate_course_document(example_doc, config=CONFIG)
    assert example_doc == before


# --- public API -----------------------------------------------------------------------------


def test_public_names_are_exported_from_the_package() -> None:
    import contracts

    for name in (
        "ConfigError",
        "Issue",
        "ValidationConfig",
        "ValidationReport",
        "validate_course_document",
    ):
        assert hasattr(contracts, name), name


@pytest.mark.parametrize(
    ("config", "named"),
    [
        ({"protected_idnumbers": ["capstone-gate"]}, "dict"),
        (["capstone-gate"], "list"),
        ("capstone-gate", "str"),
        (ValidationConfig, "the class ValidationConfig itself"),  # not an instance
        (object(), "object"),
    ],
    ids=["dict", "list", "str", "the class", "object"],
)
def test_an_unsupported_config_type_is_refused_not_ignored(
    example_doc: Doc, config: Any, named: str
) -> None:
    with pytest.raises(ConfigError) as error:
        validate_course_document(example_doc, config=config)
    message = str(error.value)
    assert named in message and "not ValidationConfig" not in message
    assert "Pass a ValidationConfig instance, e.g. ValidationConfig(...)." in message
    # Refused even when the document is broken: the setting is checked first.
    with pytest.raises(ConfigError):
        validate_course_document([], config=config)

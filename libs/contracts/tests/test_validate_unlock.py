"""Unlock rules by package mode (PRD B1.2 rule 2, guide-confirmed).

full: the first section must have `after` null (any date is allowed); every later section must
have `after` naming the one assignment of the section before it, in document order, and that
section must hold exactly one assignment. `start_date` is optional.
sections-only: every listed section, even a single one, must have `after`. It may name an
activity that only the template course has, which this validator must NOT report: whether it
resolves in the merged course is the checker's CK-04 (a loop is CK-05). It must not name an
activity of a later section of the package. Only the idnumber's shape is judged by the schema.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

from contracts import validate_course_document

from .helpers import (
    WEEK1,
    WEEK1_TASK,
    WEEK2,
    Doc,
    error_codes,
    only,
    to_sections_only,
)

DATE = "2026-02-09"
AFTER = ("unlock", "after")


def set_unlock(doc: Doc, place: tuple[str | int, ...], value: Any) -> None:
    """Set a section's unlock; the string "absent" removes the key altogether."""
    section: Any = doc
    for key in place:
        section = section[key]
    if value == "absent":
        section.pop("unlock", None)
    else:
        section["unlock"] = value


# --- full mode, first section ---------------------------------------------------------------

FIRST_SECTION_VALID = {
    "both null": {"after": None, "start_date": None},
    "absent": "absent",
    "date only": {"after": None, "start_date": DATE},
}
FIRST_SECTION_INVALID: dict[str, Doc] = {
    "completion only": {"after": "wk-01-guide", "start_date": None},
    "completion plus date": {"after": "wk-01-guide", "start_date": DATE},
    "a task of its own week": {"after": "wk-01-task"},
    "a task of the next week": {"after": "wk-02-task"},
    "unknown": {"after": "tpl-sample-task"},
}


@pytest.mark.parametrize("name", list(FIRST_SECTION_VALID))
def test_full_mode_first_section_is_valid_in_every_form(
    example_doc: Doc, name: str
) -> None:
    set_unlock(example_doc, ("sections", 0), FIRST_SECTION_VALID[name])
    assert validate_course_document(example_doc).errors == ()


@pytest.mark.parametrize("name", list(FIRST_SECTION_INVALID))
def test_full_mode_first_section_must_not_have_after(
    example_doc: Doc, name: str
) -> None:
    set_unlock(example_doc, ("sections", 0), FIRST_SECTION_INVALID[name])
    issue = only(validate_course_document(example_doc).errors)
    assert issue.code == "unlock_after_on_first_section"
    assert issue.rule == "B1.2 rule 2"
    assert issue.location == WEEK1 + AFTER
    assert issue.idnumber == FIRST_SECTION_INVALID[name]["after"]
    assert "sections[0].unlock.after" in issue.message and issue.fix_hint


# --- full mode, later sections --------------------------------------------------------------

LATER_VALID = {
    "completion only": {"after": "wk-01-task", "start_date": None},
    "completion without start_date key": {"after": "wk-01-task"},
    "completion plus date": {"after": "wk-01-task", "start_date": DATE},
}
LATER_INVALID = {
    "date only": {"after": None, "start_date": DATE},
    "both null": {"after": None, "start_date": None},
    "absent": "absent",
}


@pytest.mark.parametrize("name", list(LATER_VALID))
def test_full_mode_later_section_with_the_previous_task_is_valid(
    example_doc: Doc, name: str
) -> None:
    set_unlock(example_doc, ("sections", 1), LATER_VALID[name])
    assert validate_course_document(example_doc).errors == ()


@pytest.mark.parametrize("name", list(LATER_INVALID))
def test_full_mode_later_section_without_after_is_rejected(
    example_doc: Doc, name: str
) -> None:
    set_unlock(example_doc, ("sections", 1), LATER_INVALID[name])
    issue = only(validate_course_document(example_doc).errors)
    assert issue.code == "unlock_after_missing"
    assert issue.rule == "B1.2 rule 2"
    assert issue.location == WEEK2 + AFTER
    assert "sections[1].unlock.after" in issue.message and issue.fix_hint


@pytest.mark.parametrize(
    "after",
    ["wk-01-guide", "wk-02-task", "wk-02-guide", "wk-09-task"],
    ids=["a page of the previous week", "its own task", "its own page", "unknown"],
)
def test_full_mode_after_must_be_the_previous_weeks_task(
    example_doc: Doc, after: str
) -> None:
    set_unlock(example_doc, ("sections", 1), {"after": after, "start_date": DATE})
    issue = only(validate_course_document(example_doc).errors)
    assert issue.code == "unlock_after_not_previous_task"
    assert issue.location == WEEK2 + AFTER
    assert issue.idnumber == after


# --- sections-only mode ---------------------------------------------------------------------


def test_sections_only_after_may_name_an_activity_that_only_the_template_has(
    example_doc: Doc,
) -> None:
    to_sections_only(
        example_doc
    )  # week 1 waits for tpl-sample-task, not in the package
    report = validate_course_document(example_doc)
    # Not a package error: that reference is resolved after the merge (checker CK-04).
    assert report.errors == ()
    assert report.ok


def test_sections_only_after_naming_an_activity_in_the_package_is_not_judged(
    example_doc: Doc,
) -> None:
    to_sections_only(example_doc)
    set_unlock(example_doc, ("sections", 1), {"after": "wk-01-guide"})
    assert validate_course_document(example_doc).errors == ()


@pytest.mark.parametrize("index", [0, 1])
@pytest.mark.parametrize("name", ["both null", "date only", "absent"])
def test_sections_only_section_without_after_is_rejected(
    example_doc: Doc, index: int, name: str
) -> None:
    to_sections_only(example_doc)
    forms = {
        "both null": {"after": None, "start_date": None},
        "date only": {"after": None, "start_date": DATE},
        "absent": "absent",
    }
    set_unlock(example_doc, ("sections", index), forms[name])
    issue = only(validate_course_document(example_doc).errors)
    assert issue.code == "unlock_after_missing"
    assert issue.location == ("sections", index) + AFTER
    assert "sections-only" in issue.message


def test_a_badly_shaped_after_is_a_schema_error_and_the_unlock_rules_wait(
    example_doc: Doc,
) -> None:
    to_sections_only(example_doc)
    set_unlock(example_doc, ("sections", 0), {"after": "Not A Valid Id!"})
    report = validate_course_document(example_doc)
    assert error_codes(report) == ["schema_oneOf"]
    assert report.errors[0].location == WEEK1 + AFTER


def test_unlock_problems_in_every_section_are_all_reported_in_document_order(
    example_doc: Doc,
) -> None:
    to_sections_only(example_doc)
    set_unlock(example_doc, ("sections", 0), "absent")
    set_unlock(example_doc, ("sections", 1), {"start_date": DATE})
    report = validate_course_document(example_doc)
    assert [(i.code, i.location) for i in report.errors] == [
        ("unlock_after_missing", WEEK1 + AFTER),
        ("unlock_after_missing", WEEK2 + AFTER),
    ]


def test_the_unlock_rule_is_no_longer_listed_as_not_checked(example_doc: Doc) -> None:
    report = validate_course_document(example_doc)
    assert "unlock_chain_not_checked" not in {i.code for i in report.not_checked}


# --- decision 1: the previous task is the single assignment of the section before ----------


def assignment(doc: Doc, idnumber: str) -> Doc:
    """A copy of week 1's task under a new idnumber, so that it stays schema-valid."""
    task: Doc = copy.deepcopy(doc["sections"][0]["activities"][1])
    task["idnumber"] = idnumber
    return task


def test_full_mode_previous_section_with_two_assignments_is_reported(
    example_doc: Doc,
) -> None:
    example_doc["sections"][0]["activities"].append(
        assignment(example_doc, "wk-01-extra")
    )
    report = validate_course_document(example_doc)
    issue = only(report.errors)
    assert issue.code == "unlock_previous_task_count"
    assert issue.location == WEEK1 + ("activities",)
    assert (
        "2 assignments" in issue.message and "sections[0].activities" in issue.message
    )
    # Naming either of the two is not reported twice: the section is what is wrong.
    set_unlock(example_doc, ("sections", 1), {"after": "wk-01-extra"})
    assert error_codes(validate_course_document(example_doc)) == [
        "unlock_previous_task_count"
    ]


def test_full_mode_previous_section_without_an_assignment_is_reported(
    example_doc: Doc,
) -> None:
    example_doc["sections"][0]["activities"].pop(1)  # the task
    set_unlock(example_doc, ("sections", 1), {"after": "wk-01-guide"})
    issue = only(validate_course_document(example_doc).errors)
    assert issue.code == "unlock_previous_task_count"
    assert (
        issue.location == WEEK1 + ("activities",) and "0 assignments" in issue.message
    )


def test_full_mode_a_missing_after_and_a_bad_task_count_are_both_reported(
    example_doc: Doc,
) -> None:
    example_doc["sections"][0]["activities"].append(
        assignment(example_doc, "wk-01-extra")
    )
    set_unlock(example_doc, ("sections", 1), {"after": None})
    assert [
        (i.code, i.location) for i in validate_course_document(example_doc).errors
    ] == [
        ("unlock_previous_task_count", WEEK1 + ("activities",)),
        ("unlock_after_missing", WEEK2 + AFTER),
    ]


def test_the_last_section_may_have_any_number_of_assignments(example_doc: Doc) -> None:
    example_doc["sections"][1]["activities"].append(
        assignment(example_doc, "wk-02-extra")
    )
    assert validate_course_document(example_doc).errors == ()


def test_sections_only_does_not_count_assignments(example_doc: Doc) -> None:
    to_sections_only(example_doc)
    example_doc["sections"][0]["activities"].append(
        assignment(example_doc, "wk-01-extra")
    )
    assert validate_course_document(example_doc).errors == ()


def test_a_moodle_assign_type_never_reaches_the_unlock_rule(example_doc: Doc) -> None:
    # Tasks are counted by the B1 name `assignment`. The B1 schema has no `assign`, so the
    # document is rejected first and the unlock rules wait.
    example_doc["sections"][0]["activities"][1]["type"] = "assign"
    report = validate_course_document(example_doc)
    assert error_codes(report) == ["schema_enum"]
    assert report.errors[0].location == WEEK1_TASK + ("type",)


# --- decision 2: previous is document order, never the number or a title -------------------


def test_previous_week_follows_document_order_not_the_section_number(
    example_doc: Doc,
) -> None:
    example_doc["sections"][0]["number"], example_doc["sections"][1]["number"] = 2, 1
    assert validate_course_document(example_doc).errors == ()
    set_unlock(example_doc, ("sections", 1), {"after": "wk-02-task"})
    issue = only(validate_course_document(example_doc).errors)
    assert issue.code == "unlock_after_not_previous_task"


def test_the_section_idnumber_and_title_do_not_decide_which_week_is_previous(
    example_doc: Doc,
) -> None:
    example_doc["sections"][0]["idnumber"] = "wk-09"
    example_doc["sections"][1]["title"] = "Week 0"
    assert validate_course_document(example_doc).errors == ()


# --- decisions 5 and 6: sections-only references --------------------------------------------


def three_sections_only(doc: Doc) -> None:
    to_sections_only(doc)
    third: Doc = copy.deepcopy(doc["sections"][1])
    third["idnumber"] = "wk-03"
    third["unlock"] = {"after": "wk-02-task"}
    third["activities"][0]["idnumber"] = "wk-03-guide"
    third["activities"][1]["idnumber"] = "wk-03-task"
    doc["sections"].append(third)


def test_sections_only_after_naming_a_later_section_is_a_forward_reference(
    example_doc: Doc,
) -> None:
    to_sections_only(example_doc)
    set_unlock(example_doc, ("sections", 0), {"after": "wk-02-task"})
    issue = only(validate_course_document(example_doc).errors)
    assert issue.code == "unlock_after_forward_reference"
    assert issue.rule == "B1.2 rule 2"
    assert issue.location == WEEK1 + AFTER and issue.idnumber == "wk-02-task"
    assert "later week" in issue.message and issue.fix_hint


def test_sections_only_after_naming_an_earlier_section_or_the_template_is_accepted(
    example_doc: Doc,
) -> None:
    to_sections_only(example_doc)
    for after in ("wk-01-task", "wk-01-guide", "tpl-sample-task", "tpl-other"):
        set_unlock(example_doc, ("sections", 1), {"after": after})
        assert validate_course_document(example_doc).errors == (), after


def test_sections_only_only_the_later_section_reference_is_reported(
    example_doc: Doc,
) -> None:
    three_sections_only(example_doc)
    set_unlock(example_doc, ("sections", 1), {"after": "wk-03-task"})
    issue = only(validate_course_document(example_doc).errors)
    assert issue.code == "unlock_after_forward_reference"
    assert issue.location == WEEK2 + AFTER


@pytest.mark.parametrize(
    "after",
    ["wk-02-guide", "wk-02-task"],
    ids=["its first activity", "its last activity"],
)
def test_sections_only_a_reference_inside_its_own_section_is_rejected(
    example_doc: Doc, after: str
) -> None:
    # The activity's position in the section does not matter: it is not an earlier activity.
    to_sections_only(example_doc)
    set_unlock(example_doc, ("sections", 1), {"after": after})
    issue = only(validate_course_document(example_doc).errors)
    assert issue.code == "unlock_after_forward_reference"
    assert issue.rule == "B1.2 rule 2"
    assert issue.location == WEEK2 + AFTER and issue.idnumber == after
    assert "this week or of a later week" in issue.message


def test_sections_only_own_section_reference_is_rejected_for_a_single_section(
    example_doc: Doc,
) -> None:
    to_sections_only(example_doc)
    del example_doc["sections"][1]
    set_unlock(example_doc, ("sections", 0), {"after": "wk-01-guide"})
    issue = only(validate_course_document(example_doc).errors)
    assert (
        issue.code == "unlock_after_forward_reference"
        and issue.location == WEEK1 + AFTER
    )


def test_sections_only_template_references_stay_accepted(example_doc: Doc) -> None:
    # Outside the package: accepted, and a name that matches nothing is CK-04 after the merge.
    to_sections_only(example_doc)
    set_unlock(example_doc, ("sections", 1), {"after": "tpl-sample-task"})
    assert validate_course_document(example_doc).errors == ()
    set_unlock(example_doc, ("sections", 1), {"after": "matches-nothing"})
    assert validate_course_document(example_doc).errors == ()


def test_sections_only_a_cycle_through_the_template_is_not_a_package_error(
    example_doc: Doc,
) -> None:
    # Within the package a cycle needs a forward or own-section reference, which is rejected.
    # A cycle through the template is only visible after the merge (CK-05).
    to_sections_only(example_doc)
    set_unlock(example_doc, ("sections", 0), {"after": "tpl-final-step"})
    set_unlock(example_doc, ("sections", 1), {"after": "wk-01-task"})
    assert validate_course_document(example_doc).errors == ()


@pytest.mark.parametrize("after", [None, "absent"])
def test_a_single_section_sections_only_package_still_needs_after(
    example_doc: Doc, after: str | None
) -> None:
    to_sections_only(example_doc)
    del example_doc["sections"][1]
    set_unlock(example_doc, ("sections", 0), "absent" if after else {"after": None})
    issue = only(validate_course_document(example_doc).errors)
    assert issue.code == "unlock_after_missing" and issue.location == WEEK1 + AFTER


def test_a_single_section_sections_only_package_with_after_is_valid(
    example_doc: Doc,
) -> None:
    to_sections_only(example_doc)
    del example_doc["sections"][1]
    assert validate_course_document(example_doc).errors == ()

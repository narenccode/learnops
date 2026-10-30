"""B2 course model contract (PRD B2): the JSON Schema and its two examples.

The schema is a DRAFT with 17 unresolved decisions, all listed in docs/traceability.md. The
OPEN DECISION markers in the schema cover only some of them, so an unmarked field is not settled.
Nothing here means the contract is approved or frozen.

These are structural schema-validation tests. They do not implement CK-01 to CK-13 and do not
show that any rule detects anything.

AUTOMATED here (structure only, by contracts/course-model.v1.schema.json):
  * the schema is a valid Draft 2020-12 schema and both examples validate;
  * required fields, types and enums, and the fields required by source kind and activity type;
  * unknown fields are accepted at every level (PRD B.0, EXT-02);
  * broken courses still validate, so that the checker can report them instead of the schema
    refusing them;
  * the package example matches the B1 example package it models;
  * every field in the proposed, unapproved CK-rule-to-field mapping (CK_FIELDS) is present in
    the examples.

NOT automated here, and therefore NOT claimed as enforced (the schema's $comment lists them):
  * that any CK rule works: no parser, evaluator or rule engine exists yet (FR-C-01 to FR-C-03);
  * CK-07 beyond representation: a course with its protected items missing can be represented,
    but nothing here establishes detection of missing, duplicated or changed protected items;
  * that the .mbz example matches a real Moodle backup: it is hand-written and the lab is not
    ready, so its shape is unverified on Moodle 4.5 and 5.3.

Each invalid case below must fail at the expected place with the expected schema keyword, so a
case cannot pass for the wrong reason.
"""

from __future__ import annotations

import copy
import datetime
import json
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "contracts" / "course-model.v1.schema.json"
EXAMPLES = ROOT / "contracts" / "examples" / "course-model.v1"
FROM_PACKAGE = EXAMPLES / "from-package.json"
FROM_MBZ = EXAMPLES / "from-mbz.json"
B1_EXAMPLE = ROOT / "contracts" / "examples" / "course-package.v1" / "course.yaml"

Doc = dict[str, Any]
Loc = tuple[str | int, ...]
Edit = Callable[[Doc], None]

# Places in from-mbz.json.
COURSE: Loc = ("course",)
SOURCE: Loc = ("source",)
SECTION0: Loc = ("sections", 0)
WEEK1: Loc = ("sections", 1)
WEEK2: Loc = ("sections", 2)
PAGE: Loc = ("sections", 1, "activities", 0)  # wk-01-guide
H5P: Loc = ("sections", 1, "activities", 1)  # wk-01-practice
TASK: Loc = ("sections", 1, "activities", 2)  # wk-01-task
FINAL: Loc = ("sections", 3, "activities", 0)  # final-project
CRITERION: Loc = ("course_completion", "criteria", 0)
BADGE: Loc = ("badges", 0)


# --- helpers -------------------------------------------------------------------------------


def _parent(doc: Doc, loc: Loc) -> Any:
    node: Any = doc
    for key in loc[:-1]:
        node = node[key]
    return node


def set_at(loc: Loc, value: Any) -> Edit:
    def edit(doc: Doc) -> None:
        _parent(doc, loc)[loc[-1]] = value

    return edit


def drop_at(loc: Loc) -> Edit:
    def edit(doc: Doc) -> None:
        del _parent(doc, loc)[loc[-1]]

    return edit


def error_keys(validator: Draft202012Validator, instance: Any) -> set[tuple[Loc, str]]:
    """(where, which schema keyword) for every error, so a test can name the exact failure."""
    return {
        (tuple(e.absolute_path), str(e.validator))
        for e in validator.iter_errors(instance)
    }


def messages(validator: Draft202012Validator, instance: Any) -> list[str]:
    return [e.message for e in validator.iter_errors(instance)]


def load_json(path: Path) -> Doc:
    loaded: Doc = json.loads(path.read_text(encoding="utf-8"))
    return loaded


@dataclass(frozen=True)
class Case:
    name: str
    edit: Edit
    at: Loc
    keyword: str


def bad(name: str, loc: Loc, value: Any, keyword: str = "type") -> Case:
    """Replace the value at loc; the schema must reject it at loc with keyword."""
    return Case(name, set_at(loc, value), loc, keyword)


def missing(name: str, loc: Loc) -> Case:
    """Remove the field at loc; the schema must report it as required on its parent."""
    return Case(name, drop_at(loc), loc[:-1], "required")


def params(cases: list[Case]) -> list[Any]:
    return [pytest.param(c, id=c.name) for c in cases]


# --- fixtures ------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def schema() -> dict[str, Any]:
    return load_json(SCHEMA_PATH)


@pytest.fixture(scope="module")
def validator(schema: dict[str, Any]) -> Draft202012Validator:
    return Draft202012Validator(schema)


@pytest.fixture
def doc() -> Doc:
    return load_json(FROM_MBZ)


@pytest.fixture
def package_doc() -> Doc:
    return load_json(FROM_PACKAGE)


# --- the schema and the examples -----------------------------------------------------------


def test_schema_is_a_valid_draft_2020_12_schema(schema: dict[str, Any]) -> None:
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    Draft202012Validator.check_schema(schema)


def test_schema_says_it_is_a_draft(schema: dict[str, Any]) -> None:
    assert schema["description"].startswith("DRAFT, not approved and not frozen")


@pytest.mark.parametrize(
    "path", [FROM_PACKAGE, FROM_MBZ], ids=["from-package", "from-mbz"]
)
def test_example_is_valid(validator: Draft202012Validator, path: Path) -> None:
    assert messages(validator, load_json(path)) == []


def test_mbz_example_is_labelled_illustrative(doc: Doc) -> None:
    assert doc["_note"].split(": ")[0].endswith("ILLUSTRATIVE")


def test_sections_only_package_is_valid(
    validator: Draft202012Validator, package_doc: Doc
) -> None:
    package_doc["source"]["mode"] = "sections-only"
    assert messages(validator, package_doc) == []


# --- the package example models the B1 example ---------------------------------------------


def _activities(doc: Doc) -> Iterator[Doc]:
    for section in doc["sections"]:
        yield from section["activities"]


def test_package_example_matches_b1_example(package_doc: Doc) -> None:
    b1 = yaml.safe_load(B1_EXAMPLE.read_text(encoding="utf-8"))

    assert package_doc["source"]["mode"] == b1["course"]["mode"]
    assert package_doc["course"]["shortname"] == b1["course"]["shortname"]
    assert package_doc["course"]["total_points"] == b1["course"]["total_points"]
    assert [
        (s["number"], s["idnumber"], s["title"]) for s in package_doc["sections"]
    ] == [(s["number"], s["idnumber"], s["title"]) for s in b1["sections"]]

    b1_activities = [a for s in b1["sections"] for a in s["activities"]]
    assert [
        (a["type"], a["idnumber"], a["title"]) for a in _activities(package_doc)
    ] == [(a["type"], a["idnumber"], a["title"]) for a in b1_activities]
    for model, source in zip(_activities(package_doc), b1_activities, strict=True):
        grade = model["grade_item"]
        assert (grade["max_grade"] if grade else None) == source.get("points")


def test_package_example_unlock_rule_matches_b1_example(package_doc: Doc) -> None:
    b1 = yaml.safe_load(B1_EXAMPLE.read_text(encoding="utf-8"))
    unlock = b1["sections"][1]["unlock"]
    completion, date = package_doc["sections"][1]["availability"]["c"]

    by_cmid = {a["cmid"]: a["idnumber"] for a in _activities(package_doc)}
    assert by_cmid[completion["cm"]] == unlock["after"]
    opens = datetime.datetime.fromtimestamp(date["t"], datetime.UTC)
    assert opens.date().isoformat() == unlock["start_date"]


# --- every CK rule has the fields it needs -------------------------------------------------

# Proposed, unapproved mapping: the PRD's rules do not name model fields.
# Presence of the fields only: this does not show that a rule works.
CK_FIELDS = {
    "CK-01": ["availability", "completion", "visible"],
    "CK-02": ["completion", "grade_item"],
    "CK-03": ["grade_item", "total_points"],
    "CK-04": ["availability", "cmid"],
    "CK-05": ["availability", "cmid"],
    "CK-06": ["idnumber"],
    "CK-07": ["idnumber", "source", "mode"],
    "CK-08": ["course_completion", "badges", "criteria"],
    "CK-09": ["marking_table", "points_total", "grade_item"],
    "CK-10": ["marking_workflow"],
    "CK-11": ["type", "grade_item"],
    "CK-12": ["media_refs"],
    "CK-13": ["availability", "completion"],
}


def _keys(node: Any) -> Iterator[str]:
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from _keys(value)
    elif isinstance(node, list):
        for item in node:
            yield from _keys(item)


@pytest.mark.parametrize("rule", sorted(CK_FIELDS))
def test_examples_carry_the_fields_a_rule_needs(rule: str) -> None:
    present = set(_keys(load_json(FROM_PACKAGE))) | set(_keys(load_json(FROM_MBZ)))
    assert set(CK_FIELDS[rule]) <= present


# --- broken courses must still validate ----------------------------------------------------

# The CK ids in these case names label the kind of broken input. A passing case shows only that
# the schema accepts the course, not that a rule detects the error.


def _duplicate_idnumber(doc: Doc) -> None:
    doc["sections"][2]["activities"][0]["idnumber"] = "wk-01-guide"


def _remove_protected_items(doc: Doc) -> None:
    del doc["sections"][3]


def _circular_unlock(doc: Doc) -> None:
    doc["sections"][1]["availability"] = {
        "op": "&",
        "c": [{"type": "completion", "cm": 105, "e": 1}],
        "showc": [True],
    }


BROKEN = {
    "CK-01 hidden section": set_at(WEEK2 + ("visible",), False),
    "CK-02 grade completion without a grade item": set_at(
        PAGE + ("completion",), {"tracking": "automatic", "use_grade": True}
    ),
    "CK-02 submit completion on a page": set_at(
        PAGE + ("completion",), {"tracking": "automatic", "submit": True}
    ),
    "CK-03 points over the target": set_at(TASK + ("grade_item",), {"max_grade": 999}),
    "CK-04 unlock rule names a missing activity": set_at(
        WEEK2 + ("availability", "c", 0, "cm"), 9999
    ),
    "CK-05 circular unlock": _circular_unlock,
    "CK-06 invalid idnumber": set_at(PAGE + ("idnumber",), "Week 1 Guide!"),
    "CK-06 empty idnumber": set_at(PAGE + ("idnumber",), ""),
    "CK-06 no idnumber": set_at(PAGE + ("idnumber",), None),
    "CK-06 duplicate idnumber": _duplicate_idnumber,
    "CK-07 protected items missing": _remove_protected_items,
    "CK-08 criterion names a missing activity": set_at(CRITERION + ("cmid",), 9999),
    "CK-08 badge criterion unresolved": set_at(
        BADGE + ("criteria", 0, "idnumber"), None
    ),
    "CK-09 no marking table": set_at(
        TASK + ("marking_table",), {"present": False, "points_total": None}
    ),
    "CK-09 unparseable marking table": set_at(
        TASK + ("marking_table",), {"present": True, "points_total": None}
    ),
    "CK-09 points differ": set_at(
        TASK + ("marking_table",), {"present": True, "points_total": 7}
    ),
    "CK-10 no marking workflow": set_at(TASK + ("marking_workflow",), False),
    "CK-11 graded h5p": set_at(H5P + ("grade_item",), {"max_grade": 10}),
    "CK-12 full media url": set_at(
        PAGE + ("media_refs",), ["https://media.example.org/a.mp4"]
    ),
    "CK-13 unlock activity without completion": set_at(
        TASK + ("completion",), {"tracking": "none"}
    ),
    "C2.8 unknown activity type": set_at(PAGE + ("type",), "wiki"),
    "empty course": set_at(("sections",), []),
    "section with no activities": set_at(WEEK1 + ("activities",), []),
    "duplicate section numbers": set_at(WEEK2 + ("number",), 1),
    "availability of an unexpected shape": set_at(
        PAGE + ("availability",), {"odd": "shape"}
    ),
    "marking workflow not known": set_at(TASK + ("marking_workflow",), None),
}


@pytest.mark.parametrize("name", list(BROKEN))
def test_broken_course_still_validates(
    validator: Draft202012Validator, doc: Doc, name: str
) -> None:
    BROKEN[name](doc)
    assert messages(validator, doc) == []


def test_protected_idnumbers_are_allowed_unlike_b1(
    validator: Draft202012Validator, doc: Doc
) -> None:
    assert doc["sections"][3]["activities"][0]["idnumber"] == "final-project"
    assert doc["sections"][3]["activities"][1]["idnumber"] == "course-feedback"
    assert messages(validator, doc) == []


# --- null and absent values that are valid -------------------------------------------------

ACCEPTED = {
    "no fullname": drop_at(COURSE + ("fullname",)),
    "null total_points": set_at(COURSE + ("total_points",), None),
    "decimal total_points": set_at(COURSE + ("total_points",), 99.5),
    "null completion_enabled": set_at(COURSE + ("completion_enabled",), None),
    "null section visible": set_at(WEEK1 + ("visible",), None),
    "null activity visible": set_at(PAGE + ("visible",), None),
    "no section title": drop_at(WEEK1 + ("title",)),
    "no activity title": drop_at(PAGE + ("title",)),
    "no media_refs": drop_at(PAGE + ("media_refs",)),
    "decimal max_grade": set_at(TASK + ("grade_item",), {"max_grade": 12.5}),
    "marking table without points_total": set_at(
        TASK + ("marking_table",), {"present": False}
    ),
    "null course_completion": set_at(("course_completion",), None),
    "null badges": set_at(("badges",), None),
    "empty badges": set_at(("badges",), []),
    "criterion of another type": set_at(CRITERION, {"type": "role"}),
    "null criterion cmid": set_at(CRITERION + ("cmid",), None),
}


@pytest.mark.parametrize("name", list(ACCEPTED))
def test_valid_variation_is_accepted(
    validator: Draft202012Validator, doc: Doc, name: str
) -> None:
    ACCEPTED[name](doc)
    assert messages(validator, doc) == []


# --- invalid: required fields --------------------------------------------------------------

MISSING = [
    missing("root without schema", ("schema",)),
    missing("root without source", ("source",)),
    missing("root without course", ("course",)),
    missing("root without sections", ("sections",)),
    missing("root without course_completion", ("course_completion",)),
    missing("root without badges", ("badges",)),
    missing("source without kind", SOURCE + ("kind",)),
    missing("course without shortname", COURSE + ("shortname",)),
    missing("course without completion_enabled", COURSE + ("completion_enabled",)),
    missing("section without number", WEEK1 + ("number",)),
    missing("section without idnumber", WEEK1 + ("idnumber",)),
    missing("section without visible", WEEK1 + ("visible",)),
    missing("section without availability", WEEK1 + ("availability",)),
    missing("section without activities", WEEK1 + ("activities",)),
    missing("activity without type", PAGE + ("type",)),
    missing("activity without idnumber", PAGE + ("idnumber",)),
    missing("activity without cmid", PAGE + ("cmid",)),
    missing("activity without visible", PAGE + ("visible",)),
    missing("activity without availability", PAGE + ("availability",)),
    missing("activity without completion", PAGE + ("completion",)),
    missing("activity without grade_item", PAGE + ("grade_item",)),
    missing("assignment without marking_workflow", TASK + ("marking_workflow",)),
    missing("assignment without marking_table", TASK + ("marking_table",)),
    missing("completion without tracking", PAGE + ("completion", "tracking")),
    missing("grade_item without max_grade", TASK + ("grade_item", "max_grade")),
    missing("marking_table without present", TASK + ("marking_table", "present")),
    missing("criterion without type", CRITERION + ("type",)),
    missing("course_completion without criteria", ("course_completion", "criteria")),
    missing("badge without name", BADGE + ("name",)),
    missing("badge without criteria", BADGE + ("criteria",)),
]


@pytest.mark.parametrize("case", params(MISSING))
def test_missing_required_field_is_rejected(
    validator: Draft202012Validator, doc: Doc, case: Case
) -> None:
    case.edit(doc)
    assert (case.at, case.keyword) in error_keys(validator, doc)


def test_package_source_without_mode_is_rejected(
    validator: Draft202012Validator, package_doc: Doc
) -> None:
    del package_doc["source"]["mode"]
    assert (SOURCE, "required") in error_keys(validator, package_doc)


def test_non_assignment_needs_no_marking_fields(
    validator: Draft202012Validator, doc: Doc
) -> None:
    assert "marking_table" not in doc["sections"][1]["activities"][0]
    assert messages(validator, doc) == []


# --- invalid: wrong type or value ----------------------------------------------------------

WRONG = [
    bad("wrong schema name", ("schema",), "learnops.course/v1", "const"),
    bad("wrong source kind", SOURCE + ("kind",), "zip", "enum"),
    bad("wrong source mode", SOURCE + ("mode",), "partial", "enum"),
    bad("empty shortname", COURSE + ("shortname",), "", "minLength"),
    bad("numeric shortname", COURSE + ("shortname",), 101),
    bad("completion_enabled as text", COURSE + ("completion_enabled",), "yes"),
    bad("total_points as text", COURSE + ("total_points",), "100"),
    bad("negative total_points", COURSE + ("total_points",), -1, "minimum"),
    bad("sections not a list", ("sections",), {}),
    bad("section number as text", WEEK1 + ("number",), "1"),
    bad("negative section number", WEEK1 + ("number",), -1, "minimum"),
    bad("decimal section number", WEEK1 + ("number",), 1.5),
    bad("numeric section idnumber", WEEK1 + ("idnumber",), 1),
    bad("section visible as number", WEEK1 + ("visible",), 1),
    bad("availability as a string", WEEK1 + ("availability",), '{"op": "&"}'),
    bad("activities not a list", WEEK1 + ("activities",), {}),
    bad("empty activity type", PAGE + ("type",), "", "minLength"),
    bad("numeric activity type", PAGE + ("type",), 1),
    bad("numeric activity idnumber", PAGE + ("idnumber",), 1),
    bad("cmid as text", PAGE + ("cmid",), "101"),
    bad("cmid zero", PAGE + ("cmid",), 0, "minimum"),
    bad("activity visible as number", PAGE + ("visible",), 1),
    bad("activity availability as list", PAGE + ("availability",), []),
    bad("completion as text", PAGE + ("completion",), "submit"),
    bad("completion tracking number", PAGE + ("completion", "tracking"), 2, "enum"),
    bad("completion tracking unknown", PAGE + ("completion", "tracking"), "x", "enum"),
    bad("completion submit as number", TASK + ("completion", "submit"), 1),
    bad("grade_item as number", TASK + ("grade_item",), 40),
    bad("max_grade as text", TASK + ("grade_item", "max_grade"), "40"),
    bad("negative max_grade", TASK + ("grade_item", "max_grade"), -1, "minimum"),
    bad("marking_workflow as number", TASK + ("marking_workflow",), 1),
    bad("marking_table as boolean", TASK + ("marking_table",), True),
    bad("present as number", TASK + ("marking_table", "present"), 1),
    bad("points_total as text", TASK + ("marking_table", "points_total"), "40"),
    bad("media_refs as text", PAGE + ("media_refs",), "a.mp4"),
    bad("media_refs item as number", PAGE + ("media_refs", 0), 1),
    bad("course_completion as list", ("course_completion",), []),
    bad("criteria not a list", ("course_completion", "criteria"), {}),
    bad("criterion cmid as text", CRITERION + ("cmid",), "106"),
    bad("empty criterion type", CRITERION + ("type",), "", "minLength"),
    bad("badges as object", ("badges",), {}),
    bad("badge name as number", BADGE + ("name",), 1),
]


@pytest.mark.parametrize("case", params(WRONG))
def test_wrong_type_or_value_is_rejected(
    validator: Draft202012Validator, doc: Doc, case: Case
) -> None:
    case.edit(doc)
    assert (case.at, case.keyword) in error_keys(validator, doc)


# --- unknown fields are accepted -----------------------------------------------------------

UNKNOWN_FIELD_PLACES: list[Loc] = [
    (),
    SOURCE,
    COURSE,
    WEEK1,
    PAGE,
    PAGE + ("completion",),
    TASK + ("grade_item",),
    TASK + ("marking_table",),
    ("course_completion",),
    CRITERION,
    BADGE,
]


@pytest.mark.parametrize(
    "loc", UNKNOWN_FIELD_PLACES, ids=lambda loc: "/".join(map(str, loc)) or "root"
)
def test_unknown_field_is_accepted(
    validator: Draft202012Validator, doc: Doc, loc: Loc
) -> None:
    target = copy.deepcopy(doc)
    node: Any = target
    for key in loc:
        node = node[key]
    node["added_later"] = "ignored"
    assert messages(validator, target) == []

"""B2 course model contract (PRD B2): the JSON Schema and its two examples.

The schema is a DRAFT. Confirmed decisions and open items are in
docs/decisions/0003-b2-course-model.md. The OPEN DECISION markers in the schema cover only some of
them, so an unmarked field is not settled. Nothing here means the contract is approved or frozen.

These are structural schema-validation tests. They do not implement CK-01 to CK-13 and do not
show that any rule detects anything. Not automated here: any CK rule (no parser, evaluator or
rule engine exists yet, FR-C-01 to FR-C-03); CK-07 beyond representing a course whose protected
items are missing, so no detection of missing, duplicated or changed items; how cm = -1 resolves;
and any match between the hand-written .mbz example and a real Moodle backup (unverified on Moodle
4.5 and 5.3).

Each invalid case must fail at the expected place with the expected schema keyword, so a case
cannot pass for the wrong reason.
"""

from __future__ import annotations

import datetime
import json
from collections.abc import Callable, Iterator
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
WEEK1: Loc = ("sections", 1)
WEEK2: Loc = ("sections", 2)
PAGE: Loc = ("sections", 1, "activities", 0)  # wk-01-guide
H5P: Loc = ("sections", 1, "activities", 1)  # wk-01-practice
TASK: Loc = ("sections", 1, "activities", 2)  # wk-01-task
PAGE_COMPLETION: Loc = PAGE + ("completion",)
TASK_COMPLETION: Loc = TASK + ("completion",)
GRADE: Loc = TASK + ("grade_item",)
TABLE: Loc = TASK + ("marking_table",)
COMPLETION_RULES: Loc = ("course_completion",)
CRITERION: Loc = ("course_completion", "criteria", 0)
BADGE: Loc = ("badges", 0)

# The lab site timezone is Asia/Kolkata. A fixed offset avoids needing tzdata on Windows.
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


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


def load_json(path: Path) -> Doc:
    loaded: Doc = json.loads(path.read_text(encoding="utf-8"))
    return loaded


SCHEMA = load_json(SCHEMA_PATH)
VALIDATOR = Draft202012Validator(SCHEMA)


def error_keys(instance: Any) -> set[tuple[Loc, str]]:
    """(where, which schema keyword) for every error, so a test can name the exact failure."""
    return {
        (tuple(e.absolute_path), str(e.validator))
        for e in VALIDATOR.iter_errors(instance)
    }


def messages(instance: Any) -> list[str]:
    return [e.message for e in VALIDATOR.iter_errors(instance)]


def path_id(loc: Loc) -> str:
    return "/".join(map(str, loc)) or "root"


@pytest.fixture
def doc() -> Doc:
    return load_json(FROM_MBZ)


@pytest.fixture
def package_doc() -> Doc:
    return load_json(FROM_PACKAGE)


# --- the schema and the examples -----------------------------------------------------------


def test_schema_is_a_valid_draft_2020_12_schema() -> None:
    assert SCHEMA["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    Draft202012Validator.check_schema(SCHEMA)


def test_draft_and_illustrative_labels(doc: Doc) -> None:
    assert SCHEMA["description"].startswith("DRAFT, not approved and not frozen")
    assert doc["_note"].split(": ")[0].endswith("ILLUSTRATIVE")


@pytest.mark.parametrize(
    "path", [FROM_PACKAGE, FROM_MBZ], ids=["from-package", "from-mbz"]
)
def test_example_is_valid(path: Path) -> None:
    assert messages(load_json(path)) == []


def test_sections_only_package_is_valid(package_doc: Doc) -> None:
    package_doc["source"]["mode"] = "sections-only"
    assert messages(package_doc) == []


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
        submits = source.get("completion") == "submit"
        assert model["completion"] == (
            {"tracking": "automatic", "submit": True}
            if submits
            else {"tracking": "none"}
        )


def test_package_example_unlock_rule_matches_b1_example(package_doc: Doc) -> None:
    b1 = yaml.safe_load(B1_EXAMPLE.read_text(encoding="utf-8"))
    unlock = b1["sections"][1]["unlock"]
    completion, date = package_doc["sections"][1]["availability"]["c"]

    by_cmid = {a["cmid"]: a["idnumber"] for a in _activities(package_doc)}
    assert by_cmid[completion["cm"]] == unlock["after"]
    assert package_doc["source"]["timezone"] == "Asia/Kolkata"
    opens = datetime.datetime.fromtimestamp(date["t"], IST)
    assert opens.isoformat() == f"{unlock['start_date']}T00:00:00+05:30"


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


@pytest.mark.parametrize("rule", sorted(CK_FIELDS))
def test_examples_carry_the_fields_a_rule_needs(rule: str) -> None:
    text = FROM_PACKAGE.read_text(encoding="utf-8") + FROM_MBZ.read_text(
        encoding="utf-8"
    )
    assert [f for f in CK_FIELDS[rule] if f'"{f}":' not in text] == []


# --- broken courses must still validate ----------------------------------------------------

# The CK ids in these case names label the kind of broken input. A passing case shows only that
# the schema accepts the course, not that a rule detects the error.
BROKEN = {
    "CK-01 hidden section": set_at(WEEK2 + ("visible",), False),
    "CK-02 grade completion without a grade item": set_at(
        PAGE_COMPLETION, {"tracking": "automatic", "use_grade": True}
    ),
    "CK-02 submit completion on a page": set_at(
        PAGE_COMPLETION, {"tracking": "automatic", "submit": True}
    ),
    "CK-03 points over the target": set_at(GRADE, {"max_grade": 999}),
    "CK-04 unlock rule names a missing activity": set_at(
        WEEK2 + ("availability", "c", 0, "cm"), 9999
    ),
    "CK-05 circular unlock": set_at(
        WEEK1 + ("availability",),
        {
            "op": "&",
            "c": [{"type": "completion", "cm": 105, "e": 1}],
            "showc": [True],
        },
    ),
    "CK-06 invalid idnumber": set_at(PAGE + ("idnumber",), "Week 1 Guide!"),
    "CK-06 empty idnumber": set_at(PAGE + ("idnumber",), ""),
    "CK-06 no idnumber": set_at(PAGE + ("idnumber",), None),
    "CK-06 duplicate idnumber": set_at(
        WEEK2 + ("activities", 0, "idnumber"), "wk-01-guide"
    ),
    "CK-07 protected items missing": drop_at(("sections", 3)),
    "CK-08 criterion names a missing activity": set_at(CRITERION + ("cmid",), 9999),
    "CK-08 badge criterion unresolved": set_at(
        BADGE + ("criteria", 0, "idnumber"), None
    ),
    "CK-09 no marking table": set_at(TABLE, {"present": False, "points_total": None}),
    "CK-09 unparseable marking table": set_at(
        TABLE, {"present": True, "points_total": None}
    ),
    "CK-09 points differ": set_at(TABLE, {"present": True, "points_total": 7}),
    "CK-10 no marking workflow": set_at(TASK + ("marking_workflow",), False),
    "CK-11 graded h5p": set_at(H5P + ("grade_item",), {"max_grade": 10}),
    "CK-12 full media url": set_at(
        PAGE + ("media_refs",), ["https://media.example.org/a.mp4"]
    ),
    "CK-13 unlock activity without completion": set_at(
        TASK_COMPLETION, {"tracking": "none"}
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
def test_broken_course_still_validates(doc: Doc, name: str) -> None:
    BROKEN[name](doc)
    assert messages(doc) == []


def test_protected_idnumbers_are_allowed_unlike_b1(doc: Doc) -> None:
    assert doc["sections"][3]["activities"][0]["idnumber"] == "final-project"
    assert doc["sections"][3]["activities"][1]["idnumber"] == "course-feedback"
    assert messages(doc) == []


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
    "decimal max_grade": set_at(GRADE, {"max_grade": 12.5}),
    "marking table without points_total": set_at(TABLE, {"present": False}),
    "null course_completion": set_at(COMPLETION_RULES, None),
    "null badges": set_at(("badges",), None),
    "empty badges": set_at(("badges",), []),
    "criterion of another type": set_at(CRITERION, {"type": "role"}),
    "null criterion cmid": set_at(CRITERION + ("cmid",), None),
    "previous-activity reference in availability": set_at(
        WEEK2 + ("availability", "c", 0, "cm"), -1
    ),
    "mbz source with a timezone": set_at(SOURCE + ("timezone",), "Asia/Kolkata"),
}


@pytest.mark.parametrize("name", list(ACCEPTED))
def test_valid_variation_is_accepted(doc: Doc, name: str) -> None:
    ACCEPTED[name](doc)
    assert messages(doc) == []


# --- invalid: required fields --------------------------------------------------------------

# Each object in the model, with its required fields.
REQUIRED: dict[Loc, str] = {
    (): "schema source course sections course_completion badges",
    SOURCE: "kind",
    COURSE: "shortname completion_enabled",
    WEEK1: "number idnumber visible availability activities",
    PAGE: "type idnumber cmid visible availability completion grade_item",
    TASK: "marking_workflow marking_table",
    PAGE_COMPLETION: "tracking",
    GRADE: "max_grade",
    TABLE: "present",
    CRITERION: "type",
    COMPLETION_RULES: "criteria",
    BADGE: "name criteria",
}
MISSING = [(loc, name) for loc, names in REQUIRED.items() for name in names.split()]


@pytest.mark.parametrize(
    ("loc", "name"), MISSING, ids=[path_id(loc + (name,)) for loc, name in MISSING]
)
def test_missing_required_field_is_rejected(doc: Doc, loc: Loc, name: str) -> None:
    drop_at(loc + (name,))(doc)
    assert (loc, "required") in error_keys(doc)


def test_package_source_without_mode_is_rejected(package_doc: Doc) -> None:
    del package_doc["source"]["mode"]
    assert (SOURCE, "required") in error_keys(package_doc)


def test_package_source_without_timezone_is_rejected(package_doc: Doc) -> None:
    del package_doc["source"]["timezone"]
    assert (SOURCE, "required") in error_keys(package_doc)


def test_non_assignment_needs_no_marking_fields(doc: Doc) -> None:
    assert "marking_table" not in doc["sections"][1]["activities"][0]
    assert messages(doc) == []


# --- invalid: wrong type or value ----------------------------------------------------------

# (bad value, expected schema keyword, the places that must reject it).
WRONG_VALUES: list[tuple[Any, str, list[Loc]]] = [
    ("learnops.course/v1", "const", [("schema",)]),
    ("zip", "enum", [SOURCE + ("kind",)]),
    ("partial", "enum", [SOURCE + ("mode",)]),
    (2, "enum", [PAGE_COMPLETION + ("tracking",)]),
    ("x", "enum", [PAGE_COMPLETION + ("tracking",)]),
    (
        "",
        "minLength",
        [
            COURSE + ("shortname",),
            SOURCE + ("timezone",),
            PAGE + ("type",),
            CRITERION + ("type",),
        ],
    ),
    (
        -1,
        "minimum",
        [
            COURSE + ("total_points",),
            WEEK1 + ("number",),
            PAGE + ("cmid",),  # cm = -1 is only a reference, never an activity's own id
            GRADE + ("max_grade",),
        ],
    ),
    (0, "minimum", [PAGE + ("cmid",)]),
    (101, "type", [COURSE + ("shortname",)]),
    ("yes", "type", [COURSE + ("completion_enabled",)]),
    ("100", "type", [COURSE + ("total_points",)]),
    ("1", "type", [WEEK1 + ("number",)]),
    (1.5, "type", [WEEK1 + ("number",)]),
    ('{"op": "&"}', "type", [WEEK1 + ("availability",)]),
    ([], "type", [PAGE + ("availability",), COMPLETION_RULES]),
    ("101", "type", [PAGE + ("cmid",)]),
    ("submit", "type", [PAGE_COMPLETION]),
    (40, "type", [GRADE]),
    ("40", "type", [GRADE + ("max_grade",), TABLE + ("points_total",)]),
    (True, "type", [TABLE]),
    ("a.mp4", "type", [PAGE + ("media_refs",)]),
    ("106", "type", [CRITERION + ("cmid",)]),
    (
        {},
        "type",
        [
            ("sections",),
            WEEK1 + ("activities",),
            COMPLETION_RULES + ("criteria",),
            ("badges",),
        ],
    ),
    (
        1,
        "type",
        [
            SOURCE + ("timezone",),
            WEEK1 + ("idnumber",),
            WEEK1 + ("visible",),
            PAGE + ("type",),
            PAGE + ("idnumber",),
            PAGE + ("visible",),
            PAGE + ("media_refs", 0),
            TASK_COMPLETION + ("submit",),
            TASK + ("marking_workflow",),
            TABLE + ("present",),
            BADGE + ("name",),
        ],
    ),
]
WRONG = [(loc, value, kw) for value, kw, locs in WRONG_VALUES for loc in locs]


@pytest.mark.parametrize(
    ("loc", "value", "keyword"),
    WRONG,
    ids=[f"{path_id(loc)} = {value!r}" for loc, value, _ in WRONG],
)
def test_wrong_type_or_value_is_rejected(
    doc: Doc, loc: Loc, value: Any, keyword: str
) -> None:
    set_at(loc, value)(doc)
    assert (loc, keyword) in error_keys(doc)


# --- unknown fields are accepted -----------------------------------------------------------


@pytest.mark.parametrize("loc", list(REQUIRED), ids=path_id)
def test_unknown_field_is_accepted(doc: Doc, loc: Loc) -> None:
    node: Any = doc
    for key in loc:
        node = node[key]
    node["added_later"] = "ignored"
    assert messages(doc) == []

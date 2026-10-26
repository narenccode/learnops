"""B1 course package contract (PRD B1): the JSON Schema and its example package.

AUTOMATED here (structure only, by contracts/course-package.v1.schema.json):
  * the schema is a valid Draft 2020-12 schema;
  * the example package's course.yaml validates, also with mode "sections-only";
  * required fields, types, enums, identifier and path patterns, ISO dates, the two default
    protected idnumbers (B1.4), the per-type required fields (B1.1, B7), and that unknown
    fields are accepted (PRD B.0, EXT-02).

NOT automated here, and therefore NOT claimed as enforced (the schema's $comment lists them):
  * B1.2 rules 1, 2, 3, 5 and 6: one guide Page and one task Assignment per week, the unlock
    chain, points summing to total_points, completion on unlock activities, unique idnumbers;
  * B1.3: the marking table inside an assignment body (markers, columns, points, Check names);
  * B1.4: configured protected idnumbers other than the two defaults, protected_section;
  * that the files named by "body" exist.
These need validator code that does not exist yet (Release 0/1 work in libs/contracts and the
checker). Until then they are checked by hand, not by this file.

Each invalid case below must fail at the expected place with the expected schema keyword, so a
case cannot pass for the wrong reason.
"""

from __future__ import annotations

import copy
import datetime
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "contracts" / "course-package.v1.schema.json"
EXAMPLE_YAML = ROOT / "contracts" / "examples" / "course-package.v1" / "course.yaml"

Doc = dict[str, Any]
Loc = tuple[str | int, ...]
Edit = Callable[[Doc], None]

# Places in the example package.
COURSE: Loc = ("course",)
WEEK1: Loc = ("sections", 0)
WEEK2: Loc = ("sections", 1)
PAGE: Loc = ("sections", 0, "activities", 0)  # wk-01-guide
TASK: Loc = ("sections", 0, "activities", 1)  # wk-01-task
NEW_ACTIVITY: Loc = ("sections", 0, "activities", 2)  # appended by add_activity()
UNLOCK2: Loc = ("sections", 1, "unlock")


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


def add_activity(**fields: Any) -> Edit:
    def edit(doc: Doc) -> None:
        doc["sections"][0]["activities"].append(fields)

    return edit


def compose(*edits: Edit) -> Edit:
    def edit(doc: Doc) -> None:
        for each in edits:
            each(doc)

    return edit


def error_keys(validator: Draft202012Validator, instance: Any) -> set[tuple[Loc, str]]:
    """(where, which schema keyword) for every error, so a test can name the exact failure."""
    return {
        (tuple(e.absolute_path), str(e.validator))
        for e in validator.iter_errors(instance)
    }


def messages(validator: Draft202012Validator, instance: Any) -> list[str]:
    return [e.message for e in validator.iter_errors(instance)]


@dataclass(frozen=True)
class Case:
    name: str
    edit: Edit
    at: Loc
    keyword: str


def bad(name: str, loc: Loc, value: Any, keyword: str) -> Case:
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
    loaded: dict[str, Any] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return loaded


@pytest.fixture(scope="module")
def validator(schema: dict[str, Any]) -> Draft202012Validator:
    # The format checker is on so that "format": "date" rejects impossible calendar dates.
    return Draft202012Validator(schema, format_checker=FormatChecker())


@pytest.fixture(scope="module")
def example() -> Doc:
    loaded: Doc = yaml.safe_load(EXAMPLE_YAML.read_text(encoding="utf-8"))
    return loaded


@pytest.fixture
def doc(example: Doc) -> Doc:
    return copy.deepcopy(example)


# --- the schema and the example ------------------------------------------------------------


def test_schema_is_a_valid_draft_2020_12_schema(schema: dict[str, Any]) -> None:
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    Draft202012Validator.check_schema(schema)


def test_example_package_is_valid(
    validator: Draft202012Validator, example: Doc
) -> None:
    assert messages(validator, example) == []


def test_example_in_sections_only_mode_is_valid(
    validator: Draft202012Validator, doc: Doc
) -> None:
    doc["course"]["mode"] = "sections-only"
    assert messages(validator, doc) == []


# --- invalid: required fields --------------------------------------------------------------

MISSING = [
    missing("root without schema", ("schema",)),
    missing("root without course", ("course",)),
    missing("root without sections", ("sections",)),
    missing("course without shortname", COURSE + ("shortname",)),
    missing("course without fullname", COURSE + ("fullname",)),
    missing("course without slug", COURSE + ("slug",)),
    missing("course without mode", COURSE + ("mode",)),
    missing("section without number", WEEK1 + ("number",)),
    missing("section without title", WEEK1 + ("title",)),
    missing("section without idnumber", WEEK1 + ("idnumber",)),
    missing("section without activities", WEEK1 + ("activities",)),
    missing("activity without type", PAGE + ("type",)),
    missing("activity without idnumber", PAGE + ("idnumber",)),
    missing("activity without title", PAGE + ("title",)),
    missing("page without body", PAGE + ("body",)),
    missing("assignment without body", TASK + ("body",)),
    missing("assignment without points", TASK + ("points",)),
    missing("assignment without submission", TASK + ("submission",)),
    missing("assignment without completion", TASK + ("completion",)),
    Case(
        "h5p without graded",
        add_activity(type="h5p", idnumber="wk-01-practice", title="Practice"),
        NEW_ACTIVITY,
        "required",
    ),
]


@pytest.mark.parametrize("case", params(MISSING))
def test_missing_required_field_is_rejected(
    validator: Draft202012Validator, doc: Doc, case: Case
) -> None:
    case.edit(doc)
    assert (case.at, case.keyword) in error_keys(validator, doc)


# --- invalid: identifiers (slug, idnumber, unlock.after) -----------------------------------

BAD_IDENTIFIERS = ["Wk-01", "wk_01", "wk 01", "wk--01", "-wk-01", "wk-01-", "wk-é1", ""]
BAD_IDENTIFIERS += ["wk-01\n"]  # a trailing newline (e.g. from a YAML block scalar)
IDENTIFIER_TARGETS: list[tuple[str, Loc, str]] = [
    ("slug", COURSE + ("slug",), "pattern"),
    ("section idnumber", WEEK1 + ("idnumber",), "pattern"),
    ("activity idnumber", PAGE + ("idnumber",), "pattern"),
    ("unlock.after", UNLOCK2 + ("after",), "oneOf"),
]
IDENTIFIER_CASES = [
    bad(f"{label} {value!r}", loc, value, keyword)
    for label, loc, keyword in IDENTIFIER_TARGETS
    for value in BAD_IDENTIFIERS
]


@pytest.mark.parametrize("case", params(IDENTIFIER_CASES))
def test_invalid_identifier_is_rejected(
    validator: Draft202012Validator, doc: Doc, case: Case
) -> None:
    case.edit(doc)
    assert (case.at, case.keyword) in error_keys(validator, doc)


# --- invalid: protected idnumbers (B1.4), in both modes ------------------------------------

PROTECTED_CASES = [
    Case(
        f"{label} {value} in {mode} mode",
        compose(set_at(COURSE + ("mode",), mode), set_at(loc, value)),
        loc,
        "not",
    )
    for mode in ("full", "sections-only")
    for label, loc in (
        ("section idnumber", WEEK1 + ("idnumber",)),
        ("activity idnumber", PAGE + ("idnumber",)),
    )
    for value in ("final-project", "course-feedback")
]


@pytest.mark.parametrize("case", params(PROTECTED_CASES))
def test_protected_idnumber_is_rejected(
    validator: Draft202012Validator, doc: Doc, case: Case
) -> None:
    case.edit(doc)
    assert (case.at, case.keyword) in error_keys(validator, doc)


# --- invalid: dates ------------------------------------------------------------------------

START_DATE = UNLOCK2 + ("start_date",)
DATE_CASES = [
    bad("impossible day 2026-02-31", START_DATE, "2026-02-31", "format"),
    bad("not a leap year 2026-02-29", START_DATE, "2026-02-29", "format"),
    bad("month 13", START_DATE, "2026-13-01", "format"),
    bad("month 00", START_DATE, "2026-00-10", "format"),
    bad("two-digit year", START_DATE, "26-1-12", "pattern"),
    bad("day first", START_DATE, "12/01/2026", "pattern"),
    bad("date and time", START_DATE, "2026-01-12T00:00:00", "pattern"),
    bad("compact form", START_DATE, "20260112", "pattern"),
    bad("trailing newline", START_DATE, "2026-01-12\n", "pattern"),
    bad("empty string", START_DATE, "", "pattern"),
    bad("number", START_DATE, 20260112, "type"),
    bad("boolean", START_DATE, True, "type"),
    bad("list", START_DATE, ["2026-01-12"], "type"),
]


@pytest.mark.parametrize("case", params(DATE_CASES))
def test_invalid_start_date_is_rejected(
    validator: Draft202012Validator, doc: Doc, case: Case
) -> None:
    case.edit(doc)
    assert (case.at, case.keyword) in error_keys(validator, doc)


def test_unquoted_yaml_date_is_rejected_so_it_must_be_quoted(
    validator: Draft202012Validator, doc: Doc
) -> None:
    # PyYAML turns an unquoted 2026-01-12 into a date object, not a string.
    parsed = yaml.safe_load("start_date: 2026-01-12")["start_date"]
    assert isinstance(parsed, datetime.date)
    doc["sections"][1]["unlock"]["start_date"] = parsed
    assert (START_DATE, "type") in error_keys(validator, doc)


# --- invalid: wrong types, values, enums, sizes --------------------------------------------

TYPE_CASES = [
    bad("schema is another version", ("schema",), "learnops.course/v2", "const"),
    bad("schema has trailing space", ("schema",), "learnops.course/v1 ", "const"),
    bad("schema is a number", ("schema",), 1, "const"),
    bad("course is a string", COURSE, "x", "type"),
    bad("shortname is empty", COURSE + ("shortname",), "", "minLength"),
    bad("shortname is a number", COURSE + ("shortname",), 101, "type"),
    bad("fullname is empty", COURSE + ("fullname",), "", "minLength"),
    bad("mode is unknown", COURSE + ("mode",), "partial", "enum"),
    bad("mode has wrong case", COURSE + ("mode",), "Full", "enum"),
    bad("mode is a number", COURSE + ("mode",), 1, "enum"),
    bad("total_points is a string", COURSE + ("total_points",), "100", "type"),
    bad("total_points is fractional", COURSE + ("total_points",), 100.5, "type"),
    bad("total_points is boolean", COURSE + ("total_points",), True, "type"),
    bad("total_points is negative", COURSE + ("total_points",), -1, "minimum"),
    bad("sections is an object", ("sections",), {}, "type"),
    bad("sections is empty", ("sections",), [], "minItems"),
    bad("section number is a string", WEEK1 + ("number",), "1", "type"),
    bad("section number is fractional", WEEK1 + ("number",), 1.5, "type"),
    bad("section number is zero", WEEK1 + ("number",), 0, "minimum"),
    bad("section number is negative", WEEK1 + ("number",), -1, "minimum"),
    bad("section title is empty", WEEK1 + ("title",), "", "minLength"),
    bad("section idnumber is a number", WEEK1 + ("idnumber",), 1, "type"),
    bad("activities is a string", WEEK1 + ("activities",), "x", "type"),
    bad("activities is empty", WEEK1 + ("activities",), [], "minItems"),
    bad("unlock is a list", WEEK1 + ("unlock",), [], "type"),
    bad("unlock.after is a number", UNLOCK2 + ("after",), 5, "oneOf"),
    bad("activity type is unknown", PAGE + ("type",), "quiz", "enum"),
    bad("activity type has wrong case", PAGE + ("type",), "Page", "enum"),
    bad("activity type is a number", PAGE + ("type",), 5, "enum"),
    bad("activity title is empty", PAGE + ("title",), "", "minLength"),
    bad("activity title is a number", PAGE + ("title",), 5, "type"),
    bad("points is a string", TASK + ("points",), "50", "type"),
    bad("points is fractional", TASK + ("points",), 2.5, "type"),
    bad("points is negative", TASK + ("points",), -5, "minimum"),
    bad("submission is a string", TASK + ("submission",), "file", "type"),
    bad("submission is empty", TASK + ("submission",), [], "minItems"),
    bad(
        "submission repeats a value",
        TASK + ("submission",),
        ["file", "file"],
        "uniqueItems",
    ),
    # An invalid item is reported at its index, not at the array.
    Case(
        "submission has unknown value",
        set_at(TASK + ("submission",), ["email"]),
        TASK + ("submission", 0),
        "enum",
    ),
    Case(
        "submission has a number",
        set_at(TASK + ("submission",), [1]),
        TASK + ("submission", 0),
        "enum",
    ),
    bad("completion is unknown", TASK + ("completion",), "view", "enum"),
    bad("completion is a list", TASK + ("completion",), ["submit"], "enum"),
    bad("graded is a string", PAGE + ("graded",), "yes", "type"),
    bad("body is a number", PAGE + ("body",), 5, "type"),
    Case(
        "h5p that is graded",
        add_activity(
            type="h5p", idnumber="wk-01-practice", title="Practice", graded=True
        ),
        NEW_ACTIVITY + ("graded",),
        "const",
    ),
]


@pytest.mark.parametrize("case", params(TYPE_CASES))
def test_wrong_type_or_value_is_rejected(
    validator: Draft202012Validator, doc: Doc, case: Case
) -> None:
    case.edit(doc)
    assert (case.at, case.keyword) in error_keys(validator, doc)


@pytest.mark.parametrize("value", [[], "learnops.course/v1", None, 1], ids=repr)
def test_document_that_is_not_an_object_is_rejected(
    validator: Draft202012Validator, value: Any
) -> None:
    assert ((), "type") in error_keys(validator, value)


# --- invalid: body paths (relative paths only, PRD C-08) -----------------------------------

BAD_BODIES = [
    "../x.md",
    "weeks/../../x.md",
    "..",
    "/abs/x.md",
    "https://example.org/x.md",
    "file:///x.md",
    "mailto:a@b.c",
    "C:\\x.md",
    "weeks\\01-guide.md",
    "",
    "weeks/01-guide.md\n",
    "weeks/01\n-guide.md",
]
BODY_CASES = [bad(f"body {v!r}", PAGE + ("body",), v, "pattern") for v in BAD_BODIES]


@pytest.mark.parametrize("case", params(BODY_CASES))
def test_body_that_is_not_a_relative_path_is_rejected(
    validator: Draft202012Validator, doc: Doc, case: Case
) -> None:
    case.edit(doc)
    assert (case.at, case.keyword) in error_keys(validator, doc)


# --- valid variations: the schema must NOT reject these ------------------------------------


@dataclass(frozen=True)
class Accepted:
    name: str
    edit: Edit


ACCEPTED = [
    Accepted("unknown field at root", set_at(("future_root",), 1)),
    Accepted("unknown field in course", set_at(COURSE + ("future",), {"a": 1})),
    Accepted("unknown field in section", set_at(WEEK1 + ("future",), [1])),
    Accepted("unknown field in unlock", set_at(UNLOCK2 + ("future",), "x")),
    Accepted("unknown field in activity", set_at(PAGE + ("future",), True)),
    Accepted("no total_points", drop_at(COURSE + ("total_points",))),
    Accepted("no unlock", drop_at(WEEK1 + ("unlock",))),
    Accepted("empty unlock", set_at(WEEK1 + ("unlock",), {})),
    Accepted("no unlock.after", drop_at(UNLOCK2 + ("after",))),
    Accepted("no unlock.start_date", drop_at(UNLOCK2 + ("start_date",))),
    Accepted("null start_date", set_at(UNLOCK2 + ("start_date",), None)),
    Accepted("leap-day start_date", set_at(UNLOCK2 + ("start_date",), "2024-02-29")),
    Accepted("sections-only mode", set_at(COURSE + ("mode",), "sections-only")),
    Accepted("submission file only", set_at(TASK + ("submission",), ["file"])),
    Accepted(
        "submission online text only", set_at(TASK + ("submission",), ["onlinetext"])
    ),
    Accepted(
        "url activity", add_activity(type="url", idnumber="wk-01-link", title="Link")
    ),
    Accepted(
        "label activity", add_activity(type="label", idnumber="wk-01-note", title="N")
    ),
    Accepted(
        "ungraded h5p activity",
        add_activity(
            type="h5p", idnumber="wk-01-practice", title="Practice", graded=False
        ),
    ),
    Accepted(
        "idnumber that only contains a protected one",
        compose(
            set_at(PAGE + ("idnumber",), "final-project-draft"),
            set_at(WEEK1 + ("idnumber",), "my-course-feedback"),
        ),
    ),
    Accepted("body with '..' inside a name", set_at(PAGE + ("body",), "a/..b/c.md")),
    Accepted("non-ASCII title", set_at(PAGE + ("title",), "Week 1 — Set up é")),
]


@pytest.mark.parametrize("case", [pytest.param(a, id=a.name) for a in ACCEPTED])
def test_valid_variation_is_accepted(
    validator: Draft202012Validator, doc: Doc, case: Accepted
) -> None:
    case.edit(doc)
    assert messages(validator, doc) == []

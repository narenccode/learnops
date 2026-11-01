"""B4 Moodle web-services contract (PRD B4): the allow-list schema, its example, and their agreement
with the PRD and with the normative text contracts/moodle-ws.v1.md.

AUTOMATED here:
  * the schema is a valid Draft 2020-12 schema and the example validates;
  * the example's function names equal the PRD B4 function list exactly (no extra, none missing,
    no duplicates) and equal the function names in the §2 table of moodle-ws.v1.md;
  * each example entry's purpose is the PRD B4 Purpose cell for that function;
  * every listed parameter is named in the PRD for that function, so none is invented or
    attached to the wrong function;
  * a replacement name, if any, also appears in the PRD B4 text (guide's rule, PR #27), and a
    replacement applies only to its own Moodle version (shown on a test-local document, because
    the contract example records none);
  * no verification state is stored: the schema refuses any field name containing "verif"
    (guide's decision on Q1);
  * .env.example has one token variable per site with a placeholder, and no MOODLE_WS_TOKEN
    (guide's decision on Q24).

NOT automated, and therefore NOT claimed:
  * that any function exists on Moodle 4.5 or 5.3, or takes the parameters used: all ten lab
    checks in moodle-ws.v1.md §5 are open (no lab access yet);
  * that libs/moodle_ws refuses functions outside this list: the library does not exist yet;
  * the draft rule (readyforrelease, never released), the service account and capabilities:
    rules text in moodle-ws.v1.md, enforced later by libs/moodle_ws.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "contracts" / "moodle-ws.v1.schema.json"
EXAMPLE_PATH = ROOT / "contracts" / "examples" / "moodle-ws.v1.functions.json"
RULES_PATH = ROOT / "contracts" / "moodle-ws.v1.md"
PRD_PATH = ROOT / "docs" / "PRD.md"
ENV_EXAMPLE = ROOT / ".env.example"

# A Moodle function name has at least one underscore; "readyforrelease" and "released" in the
# same table cells do not, so they are never mistaken for functions.
FUNCTION = re.compile(r"`([a-z]+(?:_[a-z0-9]+)+)`")
# How the PRD ties a parameter to a function: App-C item 1 says "`workflowstate` on `mod_...`".
PARAMETER_ON_FUNCTION = re.compile(r"`([a-z][a-z0-9_]*)` on `([a-z0-9_]+)`")

Doc = dict[str, Any]


# --- helpers -------------------------------------------------------------------------------


def section(text: str, start: str, end: str) -> str:
    """The text from the heading that starts with `start` to the next heading starting with `end`."""
    begin = text.index(start)
    return text[begin : text.index(end, begin + len(start))]


def table_rows(text: str) -> list[list[str]]:
    """Cells of every Markdown table body row (header and separator rows dropped)."""
    rows = []
    for line in text.splitlines():
        if line.startswith("|") and not re.match(r"^\|[\s|:-]+\|$", line):
            rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return [row for row in rows if row[0] not in ("Purpose",)]


def prd_b4() -> str:
    return section(PRD_PATH.read_text(encoding="utf-8"), "## B4.", "## B5.")


def prd_functions() -> dict[str, str]:
    """Function name -> PRD B4 Purpose cell, from the PRD B4 table."""
    functions: dict[str, str] = {}
    for purpose, function_cell in (row[:2] for row in table_rows(prd_b4())):
        for name in FUNCTION.findall(function_cell):
            assert name not in functions, f"{name} listed twice in PRD B4"
            functions[name] = purpose
    return functions


def prd_parameters(prd: str) -> dict[str, set[str]]:
    """Function name -> the parameters the PRD names for that function."""
    named: dict[str, set[str]] = {}
    for parameter, function in PARAMETER_ON_FUNCTION.findall(prd):
        named.setdefault(function, set()).add(parameter)
    return named


def wrongly_placed(functions: list[Doc], prd: str) -> list[tuple[str, str]]:
    """(function, parameter) pairs where the PRD does not name that parameter for that function."""
    named = prd_parameters(prd)
    return [
        (function["name"], parameter)
        for function in functions
        for parameter in function["parameters"]
        if parameter not in named.get(function["name"], set())
    ]


def replacements_outside_prd(functions: list[Doc], b4: str) -> list[str]:
    """Replacement names that the PRD B4 text does not contain."""
    return [
        replacement["name"]
        for function in functions
        for replacement in function.get("replacements", [])
        if f"`{replacement['name']}`" not in b4
    ]


def resolved_name(doc: Doc, function: str, moodle_version: str) -> str:
    """The name to call on a version, by the rule in moodle-ws.v1.md §2a."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    replacement_item = schema["$defs"]["function"]["properties"]["replacements"][
        "items"
    ]
    if moodle_version not in replacement_item["properties"]["moodle_version"]["enum"]:
        raise ValueError(f"Moodle {moodle_version} is not supported")
    entry = next(f for f in doc["functions"] if f["name"] == function)
    for replacement in entry.get("replacements", []):
        if replacement["moodle_version"] == moodle_version:
            return str(replacement["name"])
    return function


def rules_functions() -> list[str]:
    """Function names in the §2 table of moodle-ws.v1.md (the Function column)."""
    text = section(RULES_PATH.read_text(encoding="utf-8"), "## 2. Functions", "## 2a.")
    return [name for row in table_rows(text) for name in FUNCTION.findall(row[1])]


def error_keys(
    validator: Draft202012Validator, instance: Any
) -> set[tuple[tuple[Any, ...], str]]:
    return {
        (tuple(e.absolute_path), str(e.validator))
        for e in validator.iter_errors(instance)
    }


# --- fixtures ------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def validator() -> Draft202012Validator:
    return Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


@pytest.fixture(scope="module")
def example() -> Doc:
    loaded: Doc = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    return loaded


# --- schema and example --------------------------------------------------------------------


def test_schema_is_a_valid_draft_2020_12_schema() -> None:
    Draft202012Validator.check_schema(
        json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    )


def test_example_is_valid(validator: Draft202012Validator, example: Doc) -> None:
    assert error_keys(validator, example) == set()


def test_prd_b4_lists_the_expected_number_of_functions() -> None:
    """Guards the PRD parsing itself: the B4 table names eight functions."""
    assert len(prd_functions()) == 8


# --- agreement with the PRD and the rules text ---------------------------------------------


def test_function_names_equal_the_prd_b4_list(example: Doc) -> None:
    names = [f["name"] for f in example["functions"]]
    assert len(names) == len(set(names)), "duplicate function in the example"
    assert sorted(names) == sorted(prd_functions())


def test_function_names_equal_the_rules_table(example: Doc) -> None:
    assert sorted(f["name"] for f in example["functions"]) == sorted(rules_functions())


def test_purpose_is_the_prd_purpose(example: Doc) -> None:
    purposes = prd_functions()
    for function in example["functions"]:
        if "purpose" in function:
            assert function["purpose"] == purposes[function["name"]], function["name"]


def test_every_parameter_is_named_in_the_prd_for_its_function(example: Doc) -> None:
    prd = PRD_PATH.read_text(encoding="utf-8")
    assert wrongly_placed(example["functions"], prd) == []


def test_the_prd_names_workflowstate_only_for_save_grade() -> None:
    """Guards the PRD parsing: no other parameter is tied to any function yet (lab check 1)."""
    prd = PRD_PATH.read_text(encoding="utf-8")
    assert prd_parameters(prd) == {"mod_assign_save_grade": {"workflowstate"}}


@pytest.mark.parametrize(
    "functions",
    [
        pytest.param(
            [{"name": "mod_assign_set_user_flags", "parameters": ["workflowstate"]}],
            id="a real parameter on the wrong function",
        ),
        pytest.param(
            [{"name": "mod_assign_save_grade", "parameters": ["readyforrelease"]}],
            id="a workflow value is not a parameter",
        ),
        pytest.param(
            [{"name": "mod_assign_save_grade", "parameters": ["feedback"]}],
            id="a parameter the PRD does not name",
        ),
    ],
)
def test_a_parameter_not_named_for_its_function_is_found(functions: list[Doc]) -> None:
    prd = PRD_PATH.read_text(encoding="utf-8")
    assert wrongly_placed(functions, prd) != []


def test_save_grade_sends_the_workflow_state(example: Doc) -> None:
    """PRD App-C 1 names `workflowstate` on mod_assign_save_grade; B4 requires readyforrelease."""
    save = next(f for f in example["functions"] if f["name"] == "mod_assign_save_grade")
    assert "workflowstate" in save["parameters"]


def test_a_replacement_name_is_also_in_the_prd(example: Doc) -> None:
    assert replacements_outside_prd(example["functions"], prd_b4()) == []


# --- the replacement rule, on a test-local document ------------------------------------------


@pytest.fixture
def with_replacement(example: Doc) -> Doc:
    """The contract example records no replacement, so this one exists only in this test."""
    doc = copy.deepcopy(example)
    doc["functions"][0]["replacements"] = [
        {"moodle_version": "5.3", "name": "core_course_example_replacement"}
    ]
    return doc


def test_a_replacement_entry_is_valid(
    validator: Draft202012Validator, with_replacement: Doc
) -> None:
    assert error_keys(validator, with_replacement) == set()


def test_a_replacement_applies_only_to_its_version(with_replacement: Doc) -> None:
    name = with_replacement["functions"][0]["name"]
    assert resolved_name(with_replacement, name, "4.5") == name
    assert (
        resolved_name(with_replacement, name, "5.3")
        == "core_course_example_replacement"
    )


def test_a_function_without_a_replacement_keeps_its_name(with_replacement: Doc) -> None:
    name = with_replacement["functions"][1]["name"]
    assert resolved_name(with_replacement, name, "5.3") == name


def test_an_unsupported_version_is_refused(with_replacement: Doc) -> None:
    name = with_replacement["functions"][0]["name"]
    with pytest.raises(ValueError, match="5.0"):
        resolved_name(with_replacement, name, "5.0")


def test_a_replacement_missing_from_the_prd_is_found(with_replacement: Doc) -> None:
    missing = replacements_outside_prd(with_replacement["functions"], prd_b4())
    assert missing == ["core_course_example_replacement"]


# --- invalid documents ---------------------------------------------------------------------


def edited(example: Doc, change: Any) -> Doc:
    doc = copy.deepcopy(example)
    change(doc)
    return doc


@pytest.mark.parametrize(
    ("name", "change", "where", "keyword"),
    [
        (
            "verified flag on a function",
            lambda d: d["functions"][0].update(verified_on_45=True),
            ("functions", 0),
            "not",  # the "not 'verif'" rule inside propertyNames
        ),
        (
            "verified flag at the top",
            lambda d: d.update(verified=True),
            (),
            "not",  # the "not 'verif'" rule inside propertyNames
        ),
        (
            "verification on a replacement",
            lambda d: d["functions"][0].update(
                replacements=[
                    {"moodle_version": "4.5", "name": "core_x_y", "verified": True}
                ]
            ),
            ("functions", 0, "replacements", 0),
            "not",  # the "not 'verif'" rule inside propertyNames
        ),
        (
            "missing parameters",
            lambda d: d["functions"][0].pop("parameters"),
            ("functions", 0),
            "required",
        ),
        (
            "bad function name",
            lambda d: d["functions"][0].update(name="GetContents"),
            ("functions", 0, "name"),
            "pattern",
        ),
        (
            "function name with a trailing newline",
            lambda d: d["functions"][0].update(
                name="core_course_get_courses_by_field\n"
            ),
            ("functions", 0, "name"),
            "pattern",
        ),
        (
            "replacement name with a trailing newline",
            lambda d: d["functions"][0].update(
                replacements=[{"moodle_version": "5.3", "name": "core_x_y\n"}]
            ),
            ("functions", 0, "replacements", 0, "name"),
            "pattern",
        ),
        (
            "parameter name with a trailing newline",
            lambda d: d["functions"][6].update(parameters=["workflowstate\n"]),
            ("functions", 6, "parameters", 0),
            "pattern",
        ),
        (
            "parameter name with a trailing carriage return and newline",
            lambda d: d["functions"][6].update(parameters=["workflowstate\r\n"]),
            ("functions", 6, "parameters", 0),
            "pattern",
        ),
        (
            "duplicate parameter",
            lambda d: d["functions"][6].update(
                parameters=["workflowstate", "workflowstate"]
            ),
            ("functions", 6, "parameters"),
            "uniqueItems",
        ),
        (
            "unknown Moodle version",
            lambda d: d["functions"][0].update(
                replacements=[{"moodle_version": "5.0", "name": "core_x_y"}]
            ),
            ("functions", 0, "replacements", 0, "moodle_version"),
            "enum",
        ),
        (
            "empty replacements",
            lambda d: d["functions"][0].update(replacements=[]),
            ("functions", 0, "replacements"),
            "minItems",
        ),
        (
            "wrong schema name",
            lambda d: d.update(schema="learnops.moodle-ws/v2"),
            ("schema",),
            "const",
        ),
        ("no functions", lambda d: d.update(functions=[]), ("functions",), "minItems"),
    ],
    ids=lambda v: v if isinstance(v, str) else None,
)
def test_invalid_document_is_rejected_at_the_expected_place(
    validator: Draft202012Validator,
    example: Doc,
    name: str,
    change: Any,
    where: tuple[Any, ...],
    keyword: str,
) -> None:
    assert (where, keyword) in error_keys(validator, edited(example, change)), name


@pytest.mark.parametrize("parameter", ["workflowstate", "a", "field_2_name"])
def test_a_valid_parameter_name_is_accepted(
    validator: Draft202012Validator, example: Doc, parameter: str
) -> None:
    doc = edited(example, lambda d: d["functions"][6].update(parameters=[parameter]))
    assert error_keys(validator, doc) == set()


def test_unknown_fields_are_accepted(
    validator: Draft202012Validator, example: Doc
) -> None:
    doc = edited(
        example, lambda d: d["functions"][0].update(note="readers ignore this")
    )
    assert error_keys(validator, doc) == set()


# --- token variables (Q24) -----------------------------------------------------------------


def env_example() -> dict[str, str]:
    values = {}
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, _, rest = line.partition("=")
            values[key.strip()] = rest.split("#", 1)[0].strip()
    return values


def test_one_token_variable_per_site_with_a_placeholder() -> None:
    env = env_example()
    assert env.get("MOODLE45_WS_TOKEN") == "CHANGE_ME"
    assert env.get("MOODLE53_WS_TOKEN") == "CHANGE_ME"
    assert "MOODLE_WS_TOKEN" not in env

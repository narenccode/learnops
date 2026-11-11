"""B4 Moodle web-services contract (PRD B4): the allow-list schema, its example, and their agreement
with the PRD and with the normative text contracts/moodle-ws.v1.md.

AUTOMATED here:
  * the schema is a valid Draft 2020-12 schema and the example validates;
  * the example's function names equal the PRD B4 function list exactly (no extra, none missing,
    no duplicates) and equal the function names in the §2 table of moodle-ws.v1.md;
  * each example entry's purpose is the PRD B4 Purpose cell for that function;
  * the example's required and optional parameters equal the PRD B4 parameter table exactly, so
    none is invented, attached to the wrong function, or listed as both;
  * mod_assign_set_user_flags is allowed nowhere (guide's B4 findings);
  * mod_assign_save_grade has the guide's required and optional parameters;
  * course identification: by course id or shortname, never idnumber (rules §2b, PRD B4);
  * the capability lists in rules §4 (needed, never granted) and that every lab check in §5 is
    still open;
  * a replacement name, if any, also appears in the PRD B4 text (guide's rule, PR #27), and a
    replacement applies only to its own Moodle version (shown on a test-local document, because
    the contract example records none);
  * no verification state is stored: the schema refuses any field name containing "verif"
    (guide's decision on Q1);
  * .env.example has one token variable per site with a placeholder, and no MOODLE_WS_TOKEN
    (guide's decision on Q24).

NOT automated, and therefore NOT claimed:
  * that any function exists on Moodle 4.5 or 5.3, or behaves as expected with the parameters
    used: the names come from the Moodle source (rules §7), and all lab checks in §5 are open;
  * that the capability list is enough or minimal: lab check 9 is open;
  * that libs/moodle_ws refuses functions outside this list, or enforces the draft rule and the
    read-back (rules §3): that is the library's own tests, not this contract's.
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
NAME = re.compile(r"`([a-z][a-z0-9_]*)`")
CAPABILITY = re.compile(r"`([a-z]+/[a-z]+:[a-z]+)`")
REMOVED = "mod_assign_set_user_flags"
# The guide's B4 findings, also read from the Moodle 4.5 and 5.3 source (rules §7).
SAVE_GRADE_REQUIRED = {
    "assignmentid",
    "userid",
    "grade",
    "attemptnumber",
    "addattempt",
    "workflowstate",
    "applytoall",
}
SAVE_GRADE_OPTIONAL = {"plugindata", "advancedgradingdata"}
CAPABILITIES_NEEDED = {
    "moodle/course:viewparticipants",
    "moodle/user:viewdetails",
    "mod/assign:view",
    "mod/assign:viewgrades",
    "mod/assign:grade",
    "mod/assign:reviewgrades",
}
CAPABILITIES_NEVER = {
    "moodle/user:update",
    "moodle/course:update",
    "mod/assign:managegrades",
    "mod/assign:releasegrades",
}

Doc = dict[str, Any]
Parameters = dict[str, tuple[set[str], set[str]]]


# --- helpers -------------------------------------------------------------------------------


def section(text: str, start: str, end: str) -> str:
    """The text from the heading that starts with `start` to the next heading starting with `end`."""
    begin = text.index(start)
    return text[begin : text.index(end, begin + len(start))]


def tables(text: str) -> dict[str, list[list[str]]]:
    """Body rows of every Markdown table, keyed by the first header cell."""
    found: dict[str, list[list[str]]] = {}
    header: str | None = None
    for line in text.splitlines():
        if not line.startswith("|"):
            header = None
            continue
        if re.match(r"^\|[\s|:-]+\|$", line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if header is None:
            header = cells[0]
            assert header not in found, f"two tables start with {header!r}"
            found[header] = []
        else:
            found[header].append(cells)
    return found


def table_rows(text: str) -> list[list[str]]:
    """Body rows of the table whose first header cell is "Purpose" (the function table)."""
    return tables(text)["Purpose"]


def prd_b4() -> str:
    return section(PRD_PATH.read_text(encoding="utf-8"), "## B4.", "## B5.")


def prd_functions() -> dict[str, str]:
    """Function name -> PRD B4 Purpose cell, from the PRD B4 function table."""
    functions: dict[str, str] = {}
    for purpose, function_cell in (row[:2] for row in table_rows(prd_b4())):
        for name in FUNCTION.findall(function_cell):
            assert name not in functions, f"{name} listed twice in PRD B4"
            functions[name] = purpose
    return functions


def prd_parameters(b4: str) -> Parameters:
    """Function name -> (required, optional) parameters, from the PRD B4 parameter table."""
    named: Parameters = {}
    for function_cell, required, optional in (
        row[:3] for row in tables(b4)["Function"]
    ):
        (function,) = FUNCTION.findall(function_cell)
        named[function] = (set(NAME.findall(required)), set(NAME.findall(optional)))
    return named


def example_parameters(functions: list[Doc]) -> Parameters:
    """Function name -> (required, optional) parameters, for entries that list any."""
    return {
        f["name"]: (set(f["parameters"]), set(f.get("optional_parameters", [])))
        for f in functions
        if f["parameters"] or f.get("optional_parameters")
    }


def wrongly_placed(functions: list[Doc], b4: str) -> list[tuple[str, str]]:
    """(function, parameter) pairs the PRD does not name for that function in that list."""
    named = prd_parameters(b4)
    wrong = []
    for function in functions:
        required, optional = named.get(function["name"], (set(), set()))
        wrong += [
            (function["name"], p) for p in function["parameters"] if p not in required
        ]
        wrong += [
            (function["name"], p)
            for p in function.get("optional_parameters", [])
            if p not in optional
        ]
    return wrong


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


def rules() -> str:
    return RULES_PATH.read_text(encoding="utf-8")


def rules_functions() -> list[str]:
    """Function names in the §2 table of moodle-ws.v1.md (the Function column)."""
    text = section(rules(), "## 2. Functions", "## 2a.")
    return [name for row in table_rows(text) for name in FUNCTION.findall(row[1])]


def rules_capabilities() -> tuple[set[str], set[str]]:
    """(needed, never) capabilities from the two tables in rules §4."""
    found = tables(section(rules(), "## 4. Capabilities", "## 5."))
    needed = {c for row in found["Needed"] for c in CAPABILITY.findall(row[0])}
    never = {c for row in found["Capability"] for c in CAPABILITY.findall(row[0])}
    return needed, never


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
    """Guards the PRD parsing itself: the B4 table names seven functions."""
    assert len(prd_functions()) == 7


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
    assert wrongly_placed(example["functions"], prd_b4()) == []


def test_example_parameters_equal_the_prd_parameter_table(example: Doc) -> None:
    """Both directions: nothing in the PRD table is missing from the example either."""
    assert example_parameters(example["functions"]) == prd_parameters(prd_b4())


def test_the_prd_names_exactly_these_parameters() -> None:
    """Guards the PRD parsing: the B4 parameter table has these rows and no others."""
    assert prd_parameters(prd_b4()) == {
        "core_course_get_courses_by_field": ({"field", "value"}, set()),
        "mod_assign_get_submission_status": ({"assignid", "userid"}, set()),
        "mod_assign_save_grade": (SAVE_GRADE_REQUIRED, SAVE_GRADE_OPTIONAL),
    }


def test_no_parameter_is_both_required_and_optional(example: Doc) -> None:
    for function in example["functions"]:
        both = set(function["parameters"]) & set(
            function.get("optional_parameters", [])
        )
        assert both == set(), function["name"]


@pytest.mark.parametrize(
    "functions",
    [
        pytest.param(
            [
                {
                    "name": "mod_assign_get_submission_status",
                    "parameters": ["workflowstate"],
                }
            ],
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
        pytest.param(
            [{"name": "mod_assign_save_grade", "parameters": ["plugindata"]}],
            id="an optional parameter listed as required",
        ),
        pytest.param(
            [
                {
                    "name": "mod_assign_save_grade",
                    "parameters": [],
                    "optional_parameters": ["workflowstate"],
                }
            ],
            id="a required parameter listed as optional",
        ),
        pytest.param(
            [{"name": REMOVED, "parameters": ["workflowstate"]}],
            id="any parameter on the removed function",
        ),
    ],
)
def test_a_parameter_not_named_for_its_function_is_found(functions: list[Doc]) -> None:
    assert wrongly_placed(functions, prd_b4()) != []


def test_save_grade_sends_the_workflow_state(example: Doc) -> None:
    """PRD App-C 1 names `workflowstate` on mod_assign_save_grade; B4 requires readyforrelease."""
    save = next(f for f in example["functions"] if f["name"] == "mod_assign_save_grade")
    assert "workflowstate" in save["parameters"]


def test_save_grade_has_the_guides_required_and_optional_parameters(
    example: Doc,
) -> None:
    save = next(f for f in example["functions"] if f["name"] == "mod_assign_save_grade")
    assert set(save["parameters"]) == SAVE_GRADE_REQUIRED
    assert set(save["optional_parameters"]) == SAVE_GRADE_OPTIONAL


def test_always_sent_is_kept_apart_from_moodle_required() -> None:
    """'Always sent' is LearnOps's rule; the rules text says where Moodle has a default instead."""
    prd_header = next(
        line for line in prd_b4().splitlines() if line.startswith("| Function |")
    )
    assert prd_header.split("|")[2].strip() == "Always sent"
    rows = tables(section(rules(), "## 2. Functions", "## 2a."))["Parameter"]
    moodle_requires = {row[0]: row[1] for row in rows}
    assert moodle_requires["`userid` on `mod_assign_get_submission_status`"].startswith(
        "No"
    )
    assert moodle_requires[
        "`field`, `value` on `core_course_get_courses_by_field`"
    ].startswith("No")
    assert moodle_requires[
        "The seven always-sent `mod_assign_save_grade` parameters"
    ].startswith("Yes")


# --- the guide's B4 findings ---------------------------------------------------------------


def test_set_user_flags_is_allowed_nowhere(example: Doc) -> None:
    assert REMOVED not in {f["name"] for f in example["functions"]}
    assert REMOVED not in prd_functions()
    assert REMOVED not in rules_functions()
    assert REMOVED not in prd_parameters(prd_b4())


def test_the_status_read_back_sends_assignment_and_learner(example: Doc) -> None:
    """Rules §3: the read-back names the learner, or Moodle reports the caller's own status."""
    status = next(
        f
        for f in example["functions"]
        if f["name"] == "mod_assign_get_submission_status"
    )
    assert set(status["parameters"]) == {"assignid", "userid"}


def plain(text: str) -> str:
    """Text with line wrapping and bold markers removed, for checking a stated rule."""
    return " ".join(text.replace("**", "").split())


def test_the_read_back_field_is_stated_in_the_rules_and_the_prd() -> None:
    draft_rule = plain(section(rules(), "## 3. Draft rule", "## 4."))
    rule = "`lastattempt.gradingstatus` is exactly `readyforrelease`"
    assert rule in draft_rule
    assert rule in plain(prd_b4())
    assert "reported as not verified, never as done" in draft_rule


def test_success_needs_both_the_state_and_the_grade_value() -> None:
    """Rules §3 and the PRD: the workflow state alone never makes a write count as done."""
    draft_rule = plain(section(rules(), "## 3. Draft rule", "## 4."))
    assert "only if both are confirmed" in draft_rule
    assert "numerically equal to the grade that was sent" in draft_rule
    assert "The workflow state alone is never enough." in draft_rule
    prd = plain(prd_b4())
    assert "done only when both are confirmed" in prd
    assert "numerically equal to the grade sent" in prd


def test_the_grade_value_source_is_only_a_pending_proposal(example: Doc) -> None:
    """Rules §6a proposes mod_assign_get_grades; it is in no contract list until the guide
    approves it, and no text claims grade verification works yet."""
    proposed = "mod_assign_get_grades"
    assert proposed not in {f["name"] for f in example["functions"]}
    assert proposed not in prd_functions()
    assert proposed not in prd_parameters(prd_b4())
    assert proposed not in rules_functions()
    assert proposed not in prd_b4()
    pending = plain(
        section(rules(), "### 6a. Pending decision: grade-value read-back", "## 7.")
    )
    assert "Status: proposal for the guide. Not part of B4 yet." in pending
    assert "Nothing in this section is implemented" in pending
    draft_rule = plain(section(rules(), "## 3. Draft rule", "## 4."))
    assert "is pending the guide's decision" in draft_rule
    assert "no grade write is reported as done" in draft_rule
    assert "until it is decided, no write is reported as done" in plain(prd_b4())


def test_course_lookup_does_not_rely_on_idnumber(example: Doc) -> None:
    lookup = next(
        f
        for f in example["functions"]
        if f["name"] == "core_course_get_courses_by_field"
    )
    assert set(lookup["parameters"]) == {"field", "value"}
    course_rule = section(rules(), "### 2b. Course identification", "## 2a.")
    assert "(`field` = `id`)" in course_rule
    assert "**never** uses a course's idnumber" in course_rule
    assert "never by its idnumber" in prd_b4()
    # idnumber is a value of `field` in Moodle, never a parameter LearnOps sends.
    assert all(
        "idnumber" not in f["parameters"] + f.get("optional_parameters", [])
        for f in example["functions"]
    )


def test_the_capability_lists_are_the_guides_and_do_not_overlap() -> None:
    needed, never = rules_capabilities()
    assert needed == CAPABILITIES_NEEDED
    assert never == CAPABILITIES_NEVER
    assert needed & never == set()


def test_the_custom_role_rule_is_stated() -> None:
    capabilities = section(rules(), "## 4. Capabilities", "## 5.")
    assert "**custom role**" in capabilities
    assert "non-editing teacher role is **not** used" in capabilities


def test_every_lab_check_is_still_open() -> None:
    """No live check is claimed: every row of the §5 checklist says open on 4.5 and 5.3."""
    rows = tables(section(rules(), "## 5. Lab verification checklist", "## 6."))["#"]
    assert [row[0] for row in rows] == [str(n) for n in range(1, 13)]
    assert all(row[2:4] == ["open", "open"] for row in rows)


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
            "optional parameter name with a trailing newline",
            lambda d: d["functions"][6].update(optional_parameters=["plugindata\n"]),
            ("functions", 6, "optional_parameters", 0),
            "pattern",
        ),
        (
            "duplicate optional parameter",
            lambda d: d["functions"][6].update(
                optional_parameters=["plugindata", "plugindata"]
            ),
            ("functions", 6, "optional_parameters"),
            "uniqueItems",
        ),
        (
            "optional parameters that are not a list",
            lambda d: d["functions"][6].update(optional_parameters="plugindata"),
            ("functions", 6, "optional_parameters"),
            "type",
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

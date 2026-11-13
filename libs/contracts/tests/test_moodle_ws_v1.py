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
  * the guide's eleven decisions on PR #64 (rules §3a, R1 to R11), one test each:
    mod_assign_get_grades as the stored-grade read-back and its matching rule (§3b), the explicit
    attempt, locked states, the declared capabilities kept out, suspended learners, the
    viewownsubmissionsummary lab check, reviewgrades on both versions, NOT_VERIFIED without a
    repeated write, exact numeric match and the range check, separate outcomes, and no automatic
    retry; plus the open lab checks 13 to 16 for what the guide read in the code but did not run,
    and the recorded follow-up for docs/design/grading.md §10.1;
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
  * any 4.5 / 5.3 behaviour behind R1, R3, R4 and R9 (the grade text format, locked-state
    handling, calls without the declared capabilities, out-of-range grades): lab checks 13 to 16;
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
GET_GRADES = "mod_assign_get_grades"  # guide's decision R1, PR #64
# Declared by Moodle for functions in §2 but never granted (guide's decisions R4 and R5).
CAPABILITIES_DECLARED_NOT_GRANTED = {
    "moodle/course:viewhiddencourses",
    "moodle/user:viewhiddendetails",
    "moodle/course:useremail",
    "moodle/course:viewsuspendedusers",
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


def rules_not_granted() -> set[str]:
    """Capabilities in the "Not granted" table of rules §4 (guide's decisions R4, R5)."""
    found = tables(section(rules(), "## 4. Capabilities", "## 5."))
    return {c for row in found["Not granted"] for c in CAPABILITY.findall(row[0])}


def lab_checks() -> dict[str, list[str]]:
    """Check number -> row of the rules §5 checklist."""
    rows = tables(section(rules(), "## 5. Lab verification checklist", "## 6."))["#"]
    return {row[0]: row for row in rows}


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
    """Guards the PRD parsing itself: the B4 table names eight functions (R1 added
    mod_assign_get_grades)."""
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
        GET_GRADES: ({"assignmentids"}, set()),
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


# --- guide's decisions on PR #64 (rules §3a, R1 to R11), one test each -----------------------


def write_rules() -> dict[str, str]:
    """Rule id -> plain text of its row in the rules §3a table."""
    rows = tables(section(rules(), "### 3a. Write rules", "### 3b."))["Rule"]
    return {row[0]: plain(row[1]) for row in rows}


def test_the_write_rules_are_exactly_r1_to_r11() -> None:
    assert list(write_rules()) == [f"R{n}" for n in range(1, 12)]


def test_r1_get_grades_is_the_stored_grade_read_back(example: Doc) -> None:
    """R1: mod_assign_get_grades is in the example, the rules table and the PRD, sends only
    assignmentids, and the grade-value check is no longer a pending proposal."""
    entry = next(f for f in example["functions"] if f["name"] == GET_GRADES)
    assert entry["parameters"] == ["assignmentids"]
    assert "optional_parameters" not in entry
    assert GET_GRADES in prd_functions()
    assert GET_GRADES in rules_functions()
    r1 = write_rules()["R1"]
    assert "`mod_assign_get_grades` is the grade-value read-back" in r1
    assert "lab check 13" in r1
    draft_rule = plain(section(rules(), "## 3. Draft rule", "## 4."))
    assert "read with `mod_assign_get_grades`" in draft_rule
    assert "pending" not in draft_rule.casefold()
    assert "pending the guide's decision" not in plain(prd_b4())
    assert "read with `mod_assign_get_grades`" in plain(prd_b4())
    matching = plain(section(rules(), "### 3b. Grade-value matching rule", "## 4."))
    for check in (
        "exactly one entry whose `assignmentid` is the one sent",
        "`warnings[]` has no entry for that assignment",
        "exactly one row whose `userid` is the one sent",
        "equals the explicit `attemptnumber` sent",
    ):
        assert check in matching


def test_r2_attempt_number_is_explicit_never_minus_one() -> None:
    r2 = write_rules()["R2"]
    assert "always the explicit attempt being graded, never `-1`" in r2
    assert "matches that same attempt" in r2
    functions = section(rules(), "## 2. Functions", "## 2a.")
    assert "`attemptnumber` (explicit, never `-1`)" in functions
    assert "never `-1`" in plain(prd_b4())


def test_r3_locked_states_are_refused_before_sending_and_still_verified() -> None:
    r3 = write_rules()["R3"]
    assert "already `readyforrelease` or `released`, the write is refused" in r3
    assert "nothing is sent" in r3
    assert "read-back after the write is still required" in r3
    # The 4.5 / 5.3 difference is recorded and left to the lab.
    assert "On 5.3 a locked submission keeps its old grade value" in r3
    assert "on 4.5 the code overwrites the grade" in r3
    assert "lab check 16" in r3
    assert "already `readyforrelease` or `released`" in plain(prd_b4())


def test_r4_declared_capabilities_are_not_granted() -> None:
    needed, never = rules_capabilities()
    not_granted = rules_not_granted()
    assert CAPABILITIES_DECLARED_NOT_GRANTED <= not_granted
    assert not_granted & needed == set()
    assert "lab check 14" in write_rules()["R4"]


def test_r5_suspended_learners_are_skipped_and_reported() -> None:
    r5 = write_rules()["R5"]
    assert "skipped and reported as skipped" in r5
    assert "`moodle/course:viewsuspendedusers` is not granted" in r5
    needed, _ = rules_capabilities()
    assert "moodle/course:viewsuspendedusers" in rules_not_granted()
    assert "moodle/course:viewsuspendedusers" not in needed
    assert "Suspended learners are skipped and reported as skipped" in plain(prd_b4())


def test_r6_view_own_submission_summary_stays_a_lab_check() -> None:
    r6 = write_rules()["R6"]
    assert "stays lab check 12" in r6
    assert "the write is not verified" in r6
    rows = lab_checks()
    assert "`mod/assign:viewownsubmissionsummary`" in rows["12"][1]


def test_r7_review_grades_is_granted_on_both_versions() -> None:
    needed, _ = rules_capabilities()
    assert "mod/assign:reviewgrades" in needed
    capabilities = plain(section(rules(), "## 4. Capabilities", "## 5."))
    assert "Granted on both 4.5 and 5.3, with one role definition" in capabilities
    assert "Moodle 5.3 only" not in capabilities
    r7 = write_rules()["R7"]
    assert "not `released`" in r7
    assert "On 4.5 Moodle does not check it" in r7


def test_r8_failed_read_back_is_not_verified_and_never_rewrites() -> None:
    r8 = write_rules()["R8"]
    assert "reported as `NOT_VERIFIED`" in r8
    assert "never repeated" in r8
    assert "separate operation that sends no write" in r8
    assert "the write is never repeated" in plain(prd_b4())


def test_r9_exact_numeric_match_and_range_check_before_writing() -> None:
    r9 = write_rules()["R9"]
    assert "exactly equal; there is no tolerance and no rounding" in r9
    assert (
        "Before writing, the grade must be a number from 0 to the assignment's maximum"
        in r9
    )
    assert "lab check 15" in r9
    prd = plain(prd_b4())
    assert "compared as a number after parsing, never as text, with no tolerance" in prd
    assert "below zero or above the assignment's maximum" in prd


def test_r10_missing_and_inaccessible_are_separate_outcomes() -> None:
    r10 = write_rules()["R10"]
    for outcome in (
        "`NO_SUBMISSION`",
        "`NO_GRADE`",
        "`ACCESS_DENIED`",
        "`SKIPPED_SUSPENDED`",
    ):
        assert outcome in r10
    assert "None is ever reported as success" in r10
    assert "Processing continues for the other learners" in r10
    assert "the other learners are still processed" in plain(prd_b4())


def test_r11_uncertain_write_is_never_retried_automatically() -> None:
    r11 = write_rules()["R11"]
    assert "does not retry the write automatically" in r11
    assert "reads back first" in r11
    assert "the mentor decides" in r11
    assert "never retried automatically" in plain(prd_b4())


def test_the_grading_design_conflict_with_r11_is_an_open_follow_up() -> None:
    """docs/design/grading.md §10.1 (Release 4) is left unchanged on purpose; the conflict is
    recorded in rules §6, so it cannot be forgotten."""
    open_questions = plain(section(rules(), "## 6. Open questions", "### 6a."))
    assert "`docs/design/grading.md` §10.1" in open_questions
    assert "conflicts with R11" in open_questions
    assert "Pre-write state unreadable" in open_questions


def test_the_fail_closed_proposals_are_open_questions_for_the_guide() -> None:
    """The three cases the decisions do not settle are recorded, each with its fail-closed
    proposal and the guide as decider, and none is written as a decided rule in §3a."""
    rows = {
        row[0].split("**")[1]: plain(row[0])
        for row in tables(section(rules(), "## 6. Open questions", "### 6a."))[
            "Question"
        ]
        if row[0].startswith("**") and row[1] == "Guide"
    }
    assert "does not write in that case" in rows["Pre-write state unreadable."]
    off = rows["Marking workflow off."]
    assert "refuses `graded` and `notgraded`" in off and "Lab check 4" in off
    assert (
        "not counted as done until the mentor confirms it"
        in rows["Lost answer, matching read-back."]
    )
    for name in (
        "Pre-write state unreadable.",
        "Marking workflow off.",
        "Lost answer, matching read-back.",
    ):
        assert "Proposed, fail closed" in rows[name]
    decided = plain(section(rules(), "### 3a. Write rules", "### 3b."))
    assert "`graded`" not in decided and "NEEDS_MENTOR_CONFIRMATION" not in decided


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
    """No live check is claimed: every row of the §5 checklist says open on 4.5 and 5.3,
    including checks 13 to 16 added for the guide's decisions."""
    rows = lab_checks()
    assert list(rows) == [str(n) for n in range(1, 17)]
    assert all(row[2:4] == ["open", "open"] for row in rows.values())
    assert all(row[4] == "—" for row in rows.values()), "no decision record exists yet"


def test_the_decision_lab_checks_name_their_rules() -> None:
    """Source reading is never a lab result: each decision the guide could not run has an open
    lab check that names its rule."""
    rows = lab_checks()
    assert "`mod_assign_get_grades`" in rows["13"][1] and "(R1, R9)" in rows["13"][1]
    assert "(R4" in rows["14"][1]
    assert "silently ignored" in rows["15"][1] and "(R9)" in rows["15"][1]
    assert "5.3 keeps the old grade" in rows["16"][1] and "(R3)" in rows["16"][1]
    intro = plain(section(rules(), "## 5. Lab verification checklist", "| #"))
    assert "reading the source (§7) never closes one" in intro


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

"""B1.3 `Check` cell: the shared test vectors and their link to the PRD text.

AUTOMATED here (data and text only; the marking-table parser does not exist yet):
  * `contracts/test-vectors/check-cells.v1.json` has the twenty-three cases, each with the exact
    shape, the closed vocabularies (status, result, rule, covers) and an expected result that fits
    its cell (an `invalid` result names a check that the cell contains, by its whole name, or the
    empty name of an empty check; a `checks` result has arguments that follow the B1.3 formats);
  * the cases cover each B1.3 rule they claim to show, and no case decides an open point: no space
    before the colon, no whitespace-only cell, no argument for `repo_clone`, no `repo_file` or
    `command` check (their arguments are not defined);
  * the PRD names the vectors file, and `docs/traceability.md` lists the open decisions;
  * the shape and open-point checks catch the mistakes they exist for (negative controls).

NOT automated here, so NOT claimed: that any parser splits a cell correctly. The marking-table
parser (Module 2, `libs/contracts`, first used by CK-09) does not exist; it must pass these
vectors. There is no test-only parser, on purpose (the guide's decision on PR #87).
"""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Callable
from typing import Any

import pytest

from .helpers import ROOT

VECTORS_PATH = ROOT / "contracts" / "test-vectors" / "check-cells.v1.json"
PRD_PATH = ROOT / "docs" / "PRD.md"
TRACEABILITY_PATH = ROOT / "docs" / "traceability.md"

CASE_IDS = [
    "single-check-with-argument",
    "check-without-argument",
    "spaces-around-the-argument",
    "readme-sections-with-spaces",
    "several-checks-with-spaces",
    "em-dash-only",
    "word-count-zero",
    "word-count-plus-sign",
    "word-count-underscore",
    "word-count-not-a-number",
    "word-count-empty-argument",
    "word-count-space-inside",
    "word-count-non-ascii-digits",
    "http-ok-other-field",
    "unknown-check-name",
    "blank-cell",
    "trailing-semicolon",
    "leading-semicolon",
    "doubled-semicolon",
    "empty-readme-sections-list",
    "empty-readme-sections-name",
    "empty-http-ok-field",
    "uppercase-check-name",
]

# 'extends-stated-rule': the guide's rule names a trailing ';'; a leading and a doubled ';' apply
# the same reason (an empty check) to other positions and need the guide's or M2's confirmation.
STATUSES = {"derived", "extends-stated-rule"}
EXTENDING_CASES = {"leading-semicolon", "doubled-semicolon"}
RESULTS = {"checks", "none", "invalid"}
RULES = {
    "B1.3-separator",
    "B1.3-spaces-ignored",
    "B1.3-name-and-argument",
    "B1.3-no-machine-check",
    "B1.3-check-optional",
    "B1.3-name-case-sensitive",
    "B1.3-word_count-argument",
    "B1.3-http_ok-field",
    "B1.3-unknown-name",
    "B1.3-bad-argument-fails",
    "B1.3-empty-pieces-fail",
}
CASE_KEYS = {"id", "title", "status", "covers", "cell", "expected"}
EM_DASH = "—"
# The checks of PRD C3.5 whose arguments B1.3 defines, plus the one with no argument. `repo_file`
# and `command` are left out on purpose: B1.3 does not define their arguments.
USABLE_NAMES = {"repo_clone", "readme_sections", "word_count", "http_ok"}
KNOWN_NAMES = USABLE_NAMES | {"repo_file", "command"}

Case = dict[str, Any]


def _vectors() -> dict[str, Any]:
    doc: dict[str, Any] = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
    return doc


def _case(case_id: str) -> Case:
    found = [c for c in _vectors()["cases"] if c["id"] == case_id]
    assert len(found) == 1, case_id
    case: Case = found[0]
    return case


def _check_names(cell: str) -> list[str]:
    """The names in a cell, for label consistency only (PRD B1.3): not a parser.

    Checks are separated by `;`, spaces around each check are ignored, and a name is the text
    before the first `:`. An empty check has the empty name.
    """
    return [part.strip().split(":", 1)[0].strip() for part in cell.split(";")]


def case_problems(case: Any) -> list[str]:
    """What is wrong with one vector: shape, vocabularies and the expected result."""
    if not isinstance(case, dict) or set(case) != CASE_KEYS:
        return [f"keys are not exactly {sorted(CASE_KEYS)}"]
    problems: list[str] = []
    if case["status"] not in STATUSES:
        problems.append(f"status must be one of {sorted(STATUSES)}")
    if (case["status"] == "extends-stated-rule") != (case["id"] in EXTENDING_CASES):
        problems.append("only the leading and doubled ';' cases extend a stated rule")
    covers = case["covers"]
    if not (isinstance(covers, list) and covers and set(covers) <= RULES):
        problems.append(f"covers must be a non-empty list from {sorted(RULES)}")
    cell = case["cell"]
    # An empty cell is a blank `Check` cell; a cell of only spaces is not decided (see the open
    # decisions), so it is not allowed.
    if not isinstance(cell, str) or (cell != "" and not cell.strip()):
        return [
            *problems,
            "cell must be a string that is empty or has a visible character",
        ]
    expected = case["expected"]
    result = expected.get("result") if isinstance(expected, dict) else None
    if result not in RESULTS:
        return [*problems, f"result must be one of {sorted(RESULTS)}"]
    if result == "none":
        if set(expected) != {"result"}:
            problems.append("a 'none' result has no other key")
        if cell != "" and cell.strip() != EM_DASH:
            problems.append("only a blank cell or the em dash alone is 'none'")
    elif result == "checks":
        problems += _checks_problems(cell, expected)
    else:
        problems += _invalid_problems(cell, expected)
    if (cell == "" or cell.strip() == EM_DASH) and result != "none":
        problems.append("a blank cell or the em dash alone must be 'none'")
    return problems


def _argument_problems(name: str, argument: str) -> list[str]:
    """A valid check has an argument in the B1.3 format (only the formats B1.3 defines)."""
    if name == "word_count":
        if not (re.fullmatch(r"[0-9]+", argument) and int(argument) >= 1):
            return [
                "word_count takes one or more ASCII digits with a value of at least 1"
            ]
    elif name == "http_ok":
        if argument != "demo_url":
            return ["demo_url is the only http_ok field in v1"]
    elif name == "readme_sections":
        if any(not section.strip() for section in argument.split(",")):
            return ["readme_sections has no empty list and no empty name"]
    return []


def _checks_problems(cell: str, expected: Any) -> list[str]:
    if set(expected) != {"result", "checks"}:
        return ["a 'checks' result has exactly 'result' and 'checks'"]
    checks = expected["checks"]
    if not (
        isinstance(checks, list)
        and checks
        and all(
            isinstance(c, dict)
            and set(c) == {"name", "argument"}
            and isinstance(c["name"], str)
            and (c["argument"] is None or isinstance(c["argument"], str))
            for c in checks
        )
    ):
        return ["checks must be a non-empty list of {name, argument}"]
    problems: list[str] = []
    if [c["name"] for c in checks] != _check_names(cell):
        problems.append("the names must be the check names of the cell, in order")
    if any(c["name"] not in USABLE_NAMES for c in checks):
        problems.append(f"a valid check name must be one of {sorted(USABLE_NAMES)}")
    if any(
        c["argument"] is not None and c["argument"] != c["argument"].strip()
        for c in checks
    ):
        problems.append("an argument has no space at either end")
    if any(
        (":" in part) != (c["argument"] is not None)
        for part, c in zip(cell.split(";"), checks, strict=False)
    ):
        problems.append("an argument is null exactly when the check has no colon")
    for c in checks:
        if c["argument"] is not None:
            problems += _argument_problems(c["name"], c["argument"])
    return problems


def _invalid_problems(cell: str, expected: Any) -> list[str]:
    if set(expected) != {"result", "rule", "check"}:
        return ["an 'invalid' result has exactly 'result', 'rule' and 'check'"]
    problems: list[str] = []
    if expected["rule"] != "CK-09":
        problems.append("the rule must be CK-09")
    # Whole check names, not substrings: `repo_clo` is not a check of the cell `repo_clon`.
    # The empty name is the name of an empty check (a leading, doubled or trailing `;`).
    if expected["check"] not in _check_names(cell):
        problems.append("check must be the whole name of a check in the cell")
    return problems


def open_point_problems(case: Case) -> list[str]:
    """A vector must not decide what B1.3 leaves open (see docs/traceability.md)."""
    cell = case["cell"]
    problems: list[str] = []
    if cell == "" or cell.strip() == EM_DASH:
        return problems
    for raw in cell.split(";"):
        # Spaces around a whole check are ignored (B1.3); a space between the name and the
        # colon is not stated, so no vector may contain one.
        part = raw.strip()
        if not part:
            continue  # an empty check: decided (fails CK-09)
        name = part.split(":", 1)[0]
        if ":" in part and name != name.rstrip():
            problems.append("a space before the colon is not defined")
        name = name.strip()
        if name in {"repo_file", "command"}:
            problems.append(f"the argument of {name} is not defined")
        if name == "repo_clone" and ":" in part:
            problems.append("repo_clone has no argument in any case: not defined")
    return problems


def duplicate_ids(cases: list[Case]) -> list[str]:
    ids = [c["id"] for c in cases]
    return sorted({i for i in ids if ids.count(i) > 1})


def _prd() -> str:
    return PRD_PATH.read_text(encoding="utf-8")


def _b13() -> str:
    match = re.search(
        r"^### B1\.3 Marking table format\n.*?(?=^### B1\.4)",
        _prd(),
        flags=re.DOTALL | re.MULTILINE,
    )
    assert match, "PRD section B1.3 was not found"
    return match.group(0)


# --- the vectors file ----------------------------------------------------------------------


def test_vectors_file_is_lf_json_with_a_version_and_unique_case_ids() -> None:
    assert b"\r" not in VECTORS_PATH.read_bytes()
    doc = _vectors()
    assert doc["version"] == 1 and doc["$comment"]
    assert set(doc) == {"$comment", "version", "cases"}
    assert [c["id"] for c in doc["cases"]] == CASE_IDS
    assert duplicate_ids(doc["cases"]) == []


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_case_has_the_required_shape_and_a_consistent_result(case_id: str) -> None:
    assert case_problems(_case(case_id)) == []


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_case_does_not_decide_an_open_point(case_id: str) -> None:
    assert open_point_problems(_case(case_id)) == []


def test_the_cases_cover_every_rule_they_claim_and_each_result_kind() -> None:
    cases = _vectors()["cases"]
    assert {r for c in cases for r in c["covers"]} == RULES
    assert {c["expected"]["result"] for c in cases} == RESULTS


def test_the_valid_and_invalid_cases_are_the_agreed_twenty_three() -> None:
    results = [c["expected"]["result"] for c in _vectors()["cases"]]
    assert len(results) == 23
    assert results.count("checks") == 5
    assert results.count("none") == 2
    assert results.count("invalid") == 16


def test_the_empty_piece_cases_name_the_empty_check() -> None:
    # An empty check (a leading, doubled or trailing `;`) has the empty name; an empty argument
    # belongs to the check that has it.
    by_id = {c["id"]: c for c in _vectors()["cases"]}
    for case_id in ("trailing-semicolon", "leading-semicolon", "doubled-semicolon"):
        assert by_id[case_id]["expected"]["check"] == ""
    assert by_id["empty-readme-sections-list"]["expected"]["check"] == "readme_sections"
    assert by_id["empty-http-ok-field"]["expected"]["check"] == "http_ok"


def test_only_the_two_unstated_positions_extend_a_stated_rule() -> None:
    extending = {
        c["id"] for c in _vectors()["cases"] if c["status"] == "extends-stated-rule"
    }
    assert extending == EXTENDING_CASES


# Each edit makes one case wrong in the way the check exists to catch.
SHAPE_EDITS: dict[str, tuple[str, Callable[[Case], None]]] = {
    "a missing key": ("single-check-with-argument", lambda c: c.pop("covers")),
    "an unknown status": (
        "single-check-with-argument",
        lambda c: c.update(status="confirmed"),
    ),
    "an unknown rule id": (
        "single-check-with-argument",
        lambda c: c["covers"].append("B1.3-made-up"),
    ),
    "an unknown result kind": (
        "single-check-with-argument",
        lambda c: c["expected"].update(result="error"),
    ),
    "a name that is not in the cell": (
        "several-checks-with-spaces",
        lambda c: c["expected"]["checks"][1].update(name="http_ok"),
    ),
    "checks in the wrong order": (
        "several-checks-with-spaces",
        lambda c: c["expected"]["checks"].reverse(),
    ),
    "an argument with a space at its end": (
        "spaces-around-the-argument",
        lambda c: c["expected"]["checks"][0].update(argument="200 "),
    ),
    "an argument for a check that has no colon": (
        "check-without-argument",
        lambda c: c["expected"]["checks"][0].update(argument="x"),
    ),
    "a missing argument for a check that has a colon": (
        "single-check-with-argument",
        lambda c: c["expected"]["checks"][0].update(argument=None),
    ),
    "a none result for a cell that is not blank or the em dash": (
        "single-check-with-argument",
        lambda c: c.update(expected={"result": "none"}),
    ),
    "the em dash with a checks result": (
        "em-dash-only",
        lambda c: c.update(
            expected={
                "result": "checks",
                "checks": [{"name": "repo_clone", "argument": None}],
            }
        ),
    ),
    "a blank cell read as an empty check": (
        "blank-cell",
        lambda c: c.update(
            expected={"result": "invalid", "rule": "CK-09", "check": ""}
        ),
    ),
    "a cell of only spaces": ("blank-cell", lambda c: c.update(cell="  ")),
    "an invalid result with another rule": (
        "word-count-zero",
        lambda c: c["expected"].update(rule="CK-07"),
    ),
    "an invalid check that is not in the cell": (
        "word-count-zero",
        lambda c: c["expected"].update(check="http_ok"),
    ),
    # `repo_clo` is only a substring of the check name `repo_clon`.
    "an invalid check that is only part of a longer name": (
        "unknown-check-name",
        lambda c: c["expected"].update(check="repo_clo"),
    ),
    # A parser that reads these cells as valid would accept what B1.3 says fails CK-09.
    "a trailing semicolon read as a valid cell": (
        "trailing-semicolon",
        lambda c: c.update(
            expected={
                "result": "checks",
                "checks": [{"name": "http_ok", "argument": "demo_url"}],
            }
        ),
    ),
    "an empty readme_sections list read as a valid check": (
        "empty-readme-sections-list",
        lambda c: c.update(
            expected={
                "result": "checks",
                "checks": [{"name": "readme_sections", "argument": ""}],
            }
        ),
    ),
    "an empty readme_sections name read as a valid check": (
        "empty-readme-sections-name",
        lambda c: c.update(
            expected={
                "result": "checks",
                "checks": [{"name": "readme_sections", "argument": "a,,b"}],
            }
        ),
    ),
    "an empty http_ok field read as a valid check": (
        "empty-http-ok-field",
        lambda c: c.update(
            expected={
                "result": "checks",
                "checks": [{"name": "http_ok", "argument": ""}],
            }
        ),
    ),
    "a capital letter in a name read as a valid check": (
        "uppercase-check-name",
        lambda c: c.update(
            expected={
                "result": "checks",
                "checks": [{"name": "Word_Count", "argument": "5"}],
            }
        ),
    ),
    "word_count zero read as a valid check": (
        "word-count-zero",
        lambda c: c.update(
            expected={
                "result": "checks",
                "checks": [{"name": "word_count", "argument": "0"}],
            }
        ),
    ),
    "a stated-rule case marked as extending it": (
        "trailing-semicolon",
        lambda c: c.update(status="extends-stated-rule"),
    ),
    "an extending case marked as derived": (
        "leading-semicolon",
        lambda c: c.update(status="derived"),
    ),
}


@pytest.mark.parametrize("name", list(SHAPE_EDITS))
def test_the_shape_check_catches_what_it_exists_for(name: str) -> None:
    case_id, edit = SHAPE_EDITS[name]
    case = copy.deepcopy(_case(case_id))
    assert case_problems(case) == []
    edit(case)
    assert case_problems(case)


OPEN_POINT_EDITS: dict[str, tuple[str, Callable[[Case], None]]] = {
    "a space before the colon": (
        "spaces-around-the-argument",
        lambda c: c.update(cell="word_count :200"),
    ),
    "a repo_file check": (
        "single-check-with-argument",
        lambda c: c.update(cell="repo_file:README.md"),
    ),
    "a command check": (
        "single-check-with-argument",
        lambda c: c.update(cell="command:setup"),
    ),
    "an argument for repo_clone": (
        "check-without-argument",
        lambda c: c.update(cell="repo_clone:x"),
    ),
}


@pytest.mark.parametrize("name", list(OPEN_POINT_EDITS))
def test_the_open_point_check_catches_what_it_exists_for(name: str) -> None:
    case_id, edit = OPEN_POINT_EDITS[name]
    case = copy.deepcopy(_case(case_id))
    assert open_point_problems(case) == []
    edit(case)
    assert open_point_problems(case)


def test_the_duplicate_id_check_catches_a_repeated_id() -> None:
    cases = copy.deepcopy(_vectors()["cases"])
    cases.append(copy.deepcopy(cases[0]))
    assert duplicate_ids(cases) == [cases[0]["id"]]


# --- the PRD text and the traceability file ------------------------------------------------


def test_the_prd_names_the_vectors_file_next_to_the_check_formats() -> None:
    assert "contracts/test-vectors/check-cells.v1.json" in _b13()


def test_the_prd_states_the_rules_the_decided_cases_rely_on() -> None:
    # The cases for empty pieces and for the name case are decided by the PRD text, not by this
    # file: if the text changed, the cases would decide it instead.
    text = " ".join(_b13().split())
    for phrase in (
        "Check names are lowercase and case-sensitive",
        "An empty section list (`readme_sections:`)",
        "an empty section name (`readme_sections:a,,b`)",
        "an empty field (`http_ok:`) and a trailing `;` fail the same way (CK-09)",
        "A cell that contains only `—` means no machine check",
        "`Check` is optional",
    ):
        assert phrase in text, phrase


def test_traceability_lists_the_check_cell_open_decisions() -> None:
    raw = TRACEABILITY_PATH.read_text(encoding="utf-8")
    found = re.search(
        r"^#+ Open decisions \(B1 submission content\)\n(.*?)(?=^#+ |\Z)",
        raw,
        flags=re.DOTALL | re.MULTILINE,
    )
    assert found, "the open-decisions section was not found"
    section = " ".join(found.group(1).split()).lower()
    for phrase in (
        "contracts/test-vectors/check-cells.v1.json",
        "space before the colon",
        "a `check` cell of only spaces",
        "a leading `;` and a doubled `;`",
        "a closing fence with text after it",
        "a tab before a `#` or a fence",
        "result kinds",
    ):
        assert phrase.lower() in section, phrase
    assert "test_check_cell_vectors_v1.py" in " ".join(raw.split())

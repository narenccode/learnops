"""B1 submission-content rules (PRD B1.3 check formats, B1.5): the shared test vectors and their
link to the PRD text.

AUTOMATED here (data and text only; no reader of submissions exists yet):
  * `contracts/test-vectors/submission.v1.json` has the eleven cases, each with the exact shape, the
    closed vocabularies (status, format, source, error code) and consistent expected values (a
    word count equals the words of the report, a report file named as the source is in the input,
    a part has a value or an error, never both). The HTML case is marked unverified until the lab;
  * `covers` says what a case shows: rules 8 and 9 are never listed (part-level results cannot show
    them), a word-count entry appears exactly when the report has a word count, an expected error
    lists rule 7, an HTML case lists rule 5, a report from a file lists rule 4, and every other
    rule that a vector can show (1 to 7 and the word count) is covered by at least one case;
  * the five PRD examples in B1.5 are the same texts as the five required vectors, with the same
    word counts and error codes, so the PRD and the vectors cannot drift apart;
  * the PRD has the B1.3 check formats and nine numbered B1.5 rules, and every `covers` entry of a
    vector names a rule that exists;
  * the open points are written down, not decided: the PRD says what v1 does not define, the
    traceability file lists each open decision with who decides it, and no vector covers one
    (no carriage return, no empty label value, no HTML entity or link, no trailing whitespace);
  * the shape and open-point checks catch the mistakes they exist for (negative controls).

NOT automated here, so NOT claimed: that any reader extracts the parts correctly. The marking-table
parser (Module 2, `libs/contracts`) and the submission extractor (Module 3, Release 4) do not exist;
the extractor must pass these vectors. The HTML result is unverified until the Moodle lab check.
"""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Callable
from typing import Any

import pytest

from .helpers import ROOT

VECTORS_PATH = ROOT / "contracts" / "test-vectors" / "submission.v1.json"
PRD_PATH = ROOT / "docs" / "PRD.md"
TRACEABILITY_PATH = ROOT / "docs" / "traceability.md"

# The five cases of the guide (PR #61, 2026-11-13), in the order of the PRD examples, then the
# case for `field_repeated` (the guide's change to the owner's default 7), then five cases for
# the other approved defaults of PR #61 (numbered as in the 2026-11-13 comment): label case and
# spacing (defaults 5 and 7), a missing Repository and a missing report (6), the report.txt
# fallback and both report files (9), and labels that are misspelled or not at the start of a
# line (the guide's answer A3).
PRD_EXAMPLE_IDS = [
    "all-labels",
    "labels-in-html",
    "missing-demo",
    "report-as-file",
    "report-contains-demo-label",
]
CASE_IDS = [
    *PRD_EXAMPLE_IDS,
    "repeated-label",
    "labels-case-and-spacing",
    "missing-repository-and-report",
    "report-as-txt",
    "report-md-before-txt",
    "misspelled-and-inline-labels",
]

STATUSES = {"derived", "unverified-until-lab"}
FORMATS = {"plain", "html"}
SOURCES = {"onlinetext", "report.md", "report.txt"}
ERRORS = {"field_missing", "field_repeated"}
PARTS = ("repository", "demo", "report")
RULES = {f"B1.5-{n}" for n in range(1, 10)} | {"B1.3-word_count"}
# Rule 8 maps checks to parts and rule 9 is guidance that is not validated: neither can show in a
# result that lists the three parts, so a vector never lists them.
UNSHOWABLE_RULES = {"B1.5-8", "B1.5-9"}
SHOWABLE_RULES = RULES - UNSHOWABLE_RULES
CASE_KEYS = {"id", "title", "status", "covers", "input", "expected"}
INPUT_KEYS = {"onlinetext", "onlinetext_format", "files"}

EMPTY_LABEL = re.compile(
    r"^\s*(repository|demo|report):\s*$", re.IGNORECASE | re.MULTILINE
)
ENTITY = re.compile(r"&(#\d+|#x[0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]*);")
URL = re.compile(r"https?://[^\s<]+")

Case = dict[str, Any]


def _vectors() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
    return loaded


def _case(case_id: str) -> Case:
    found = [c for c in _vectors()["cases"] if c["id"] == case_id]
    assert (
        len(found) == 1
    ), f"expected one vector with id {case_id!r}, found {len(found)}"
    case: Case = found[0]
    return case


def case_problems(case: Any) -> list[str]:
    """What is wrong with one vector: shape, vocabularies and consistency of the expected values."""
    if not isinstance(case, dict) or set(case) != CASE_KEYS:
        return [f"keys are not exactly {sorted(CASE_KEYS)}"]
    problems: list[str] = []
    if not (
        isinstance(case["id"], str)
        and re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", case["id"])
    ):
        problems.append("id is not a lower-case slug")
    if not (isinstance(case["title"], str) and case["title"]):
        problems.append("title is empty")
    if case["status"] not in STATUSES:
        problems.append(f"status {case['status']!r} is not one of {sorted(STATUSES)}")
    covers = case["covers"]
    if not (isinstance(covers, list) and covers and set(covers) <= RULES):
        problems.append(
            f"covers must be a non-empty list of rule ids from {sorted(RULES)}"
        )
    given = case["input"]
    if not isinstance(given, dict) or set(given) != INPUT_KEYS:
        return [*problems, f"input keys are not exactly {sorted(INPUT_KEYS)}"]
    if not isinstance(given["onlinetext"], str):
        problems.append("onlinetext is not a string")
    if given["onlinetext_format"] not in FORMATS:
        problems.append(f"onlinetext_format is not one of {sorted(FORMATS)}")
    if (
        given["onlinetext_format"] == "html"
        and case["status"] != "unverified-until-lab"
    ):
        problems.append("an HTML case must be 'unverified-until-lab'")
    files = given["files"]
    if not (
        isinstance(files, list)
        and all(isinstance(f, dict) and set(f) == {"name", "text"} for f in files)
    ):
        return [*problems, "files must be a list of {name, text}"]
    expected = case["expected"]
    if not isinstance(expected, dict) or set(expected) != set(PARTS):
        return [*problems, f"expected must have exactly {list(PARTS)}"]
    for part in PARTS:
        problems += _part_problems(part, expected[part], files)
    return problems + _covers_problems(case)


def _covers_problems(case: Case) -> list[str]:
    """What `covers` says that the case's own expected result does not support."""
    covers = case["covers"]
    if not isinstance(covers, list):
        return []
    listed = set(covers)
    expected = case["expected"]
    report = expected["report"]
    problems: list[str] = []
    if listed & UNSHOWABLE_RULES:
        problems.append("covers lists B1.5-8 or B1.5-9, which a result cannot show")
    if ("words" in report) != ("B1.3-word_count" in listed):
        problems.append(
            "covers lists B1.3-word_count exactly when the report has a word count"
        )
    if any("error" in expected[part] for part in PARTS) and "B1.5-7" not in listed:
        problems.append("an expected error needs B1.5-7 in covers")
    if case["input"]["onlinetext_format"] == "html" and "B1.5-5" not in listed:
        problems.append("an HTML case needs B1.5-5 in covers")
    if report.get("source") in {"report.md", "report.txt"} and "B1.5-4" not in listed:
        problems.append("a report from a file needs B1.5-4 in covers")
    return problems


def _part_problems(part: str, entry: Any, files: list[Case]) -> list[str]:
    if not isinstance(entry, dict):
        return [f"{part}: not an object"]
    if "error" in entry:
        allowed = {"field_missing"} if part == "report" else ERRORS
        if set(entry) != {"error"} or entry["error"] not in allowed:
            return [f"{part}: bad error entry {entry!r}"]
        return []
    keys = {"value", "source", "words"} if part == "report" else {"value"}
    if set(entry) != keys or not (isinstance(entry["value"], str) and entry["value"]):
        return [f"{part}: needs exactly {sorted(keys)} (or only an error)"]
    if part != "report":
        return []
    problems: list[str] = []
    if entry["source"] not in SOURCES:
        problems.append(f"report: source is not one of {sorted(SOURCES)}")
    if entry["words"] != len(entry["value"].split()):
        problems.append(
            "report: words is not the number of whitespace-separated pieces of value"
        )
    if entry["source"] != "onlinetext" and not any(
        f["name"] == entry["source"] and f["text"] == entry["value"] for f in files
    ):
        problems.append(
            "report: source names a file that is not in the input with this text"
        )
    return problems


def open_point_problems(case: Case) -> list[str]:
    """B1.5 'Not defined in v1': a vector must not decide any of these points."""
    given = case["input"]
    texts = [given["onlinetext"], *(f["text"] for f in given["files"])]
    problems: list[str] = []
    if any("\r" in t for t in texts):
        problems.append("uses a carriage return (line endings are not defined in v1)")
    if EMPTY_LABEL.search(given["onlinetext"]):
        problems.append("has a label with an empty value (not defined in v1)")
    if given["onlinetext_format"] == "html":
        if ENTITY.search(given["onlinetext"]) or re.search(
            r"<a[\s>]", given["onlinetext"]
        ):
            problems.append("uses an HTML entity or link (not defined in v1)")
    values = [e["value"] for e in case["expected"].values() if "value" in e]
    if any(v != v.strip() for v in values):
        problems.append(
            "expects a value with leading or trailing whitespace (not defined in v1)"
        )
    urls = URL.findall(given["onlinetext"]) + [
        u for v in values for u in URL.findall(v)
    ]
    if any(not u.startswith("https://example.org/") for u in urls):
        problems.append("uses a URL outside https://example.org/")
    return problems


def duplicate_ids(cases: list[Case]) -> list[str]:
    ids = [c["id"] for c in cases]
    return sorted({i for i in ids if ids.count(i) > 1})


def _prd() -> str:
    return PRD_PATH.read_text(encoding="utf-8")


def _section(start: str, end: str) -> str:
    match = re.search(
        rf"^{start}\n.*?(?=^{end})", _prd(), flags=re.DOTALL | re.MULTILINE
    )
    assert match, f"PRD section {start!r} was not found"
    return match.group(0)


def _b13() -> str:
    return _section("### B1.3 Marking table format", "### B1.4")


def _b15() -> str:
    return _section("### B1.5 Submission content", "## B2")


def _example_blocks_and_items() -> tuple[list[str], list[str]]:
    part = _b15()
    examples = part[part.index("**Examples.**") :]
    blocks = re.findall(r"```text\n(.*?)\n\s*```", examples, flags=re.DOTALL)
    blocks = [
        re.sub(r"(?m)^   ", "", b) for b in blocks
    ]  # the blocks sit inside list items
    return blocks, re.split(r"(?m)^\d\. \*", examples)[1:]


# --- the vectors file ----------------------------------------------------------------------


def test_vectors_file_is_lf_json_with_a_version_and_eleven_cases() -> None:
    assert b"\r" not in VECTORS_PATH.read_bytes()
    doc = _vectors()
    assert doc["version"] == 1 and doc["$comment"]
    assert [c["id"] for c in doc["cases"]] == CASE_IDS
    assert duplicate_ids(doc["cases"]) == []


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_case_has_the_required_shape_and_consistent_expected_values(
    case_id: str,
) -> None:
    assert case_problems(_case(case_id)) == []


def test_only_the_html_case_is_unverified_until_the_lab() -> None:
    unverified = [
        c["id"] for c in _vectors()["cases"] if c["status"] == "unverified-until-lab"
    ]
    assert unverified == ["labels-in-html"]
    assert {c["status"] for c in _vectors()["cases"]} == STATUSES


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_case_does_not_decide_an_open_point(case_id: str) -> None:
    assert open_point_problems(_case(case_id)) == []


# Each edit makes one case wrong in the way the check exists to catch.
SHAPE_EDITS: dict[str, tuple[str, Callable[[Case], None]]] = {
    "a missing key": ("all-labels", lambda c: c.pop("covers")),
    "the retired status 'confirmed'": (
        "all-labels",
        lambda c: c.update(status="confirmed"),
    ),
    "an unknown reason code": (
        "missing-demo",
        lambda c: c["expected"].update(demo={"error": "field_unknown"}),
    ),
    "a repeated report error": (
        "missing-demo",
        lambda c: c["expected"].update(report={"error": "field_repeated"}),
    ),
    "words that do not match": (
        "all-labels",
        lambda c: c["expected"]["report"].update(words=13),
    ),
    "a value and an error together": (
        "all-labels",
        lambda c: c["expected"]["demo"].update(error="field_missing"),
    ),
    "a file source with no such file": (
        "all-labels",
        lambda c: c["expected"]["report"].update(source="report.md"),
    ),
    "an HTML case marked derived": (
        "labels-in-html",
        lambda c: c.update(status="derived"),
    ),
    "an unknown rule id": ("all-labels", lambda c: c["covers"].append("B1.5-10")),
    "an unknown input key": (
        "all-labels",
        lambda c: c["input"].update(submission_types=["file"]),
    ),
    "a rule that a result cannot show": (
        "all-labels",
        lambda c: c["covers"].append("B1.5-8"),
    ),
    "a word count that covers does not declare": (
        "all-labels",
        lambda c: c["covers"].remove("B1.3-word_count"),
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
    "a carriage return": (
        "all-labels",
        lambda c: c["input"].update(
            onlinetext=c["input"]["onlinetext"].replace("\n", "\r\n")
        ),
    ),
    "an empty label value": (
        "all-labels",
        lambda c: c["input"].update(onlinetext="Demo:\n" + c["input"]["onlinetext"]),
    ),
    "an HTML entity": (
        "labels-in-html",
        lambda c: c["input"].update(onlinetext=c["input"]["onlinetext"] + "&amp;"),
    ),
    "an HTML link": (
        "labels-in-html",
        lambda c: c["input"].update(
            onlinetext=c["input"]["onlinetext"] + '<a href="x">x</a>'
        ),
    ),
    "trailing whitespace in an expected value": (
        "all-labels",
        lambda c: c["expected"]["report"].update(
            value=c["expected"]["report"]["value"] + "\n"
        ),
    ),
    "a URL outside example.org": (
        "all-labels",
        lambda c: c["input"].update(
            onlinetext=c["input"]["onlinetext"].replace(
                "https://example.org/", "https://example.com/"
            )
        ),
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
    assert duplicate_ids([{"id": "a"}, {"id": "b"}]) == []
    assert duplicate_ids([{"id": "a"}, {"id": "a"}]) == ["a"]


# --- the PRD text --------------------------------------------------------------------------


def test_prd_b13_has_the_check_formats_and_names_what_it_does_not_define() -> None:
    text = " ".join(_b13().split())
    for phrase in (
        "separated by `;`",
        "`readme_sections:<a,b,c>`",
        "case-insensitively",
        "cannot contain a comma",
        "`word_count:<n>`",
        "a whole number of at least 1",
        "`demo_url` is the only field in v1",
        "An unknown check name fails validation",
        "are not defined here",
        "the argument format of `repo_file:<path>`",
    ):
        assert phrase in text, phrase


def test_prd_b15_has_nine_numbered_rules_and_both_reason_codes() -> None:
    part = _b15()
    rules = part[: part.index("**Examples.**")]
    assert re.findall(r"(?m)^(\d)\. \*\*", rules) == [str(n) for n in range(1, 10)]
    assert "`field_missing`" in rules and "`field_repeated`" in rules
    assert "should tell the learner how to label each part" in " ".join(rules.split())
    assert "unverified" in " ".join(rules.split())


def test_prd_b15_says_what_v1_does_not_define() -> None:
    text = " ".join(_b15().split())
    assert "**Not defined in v1.**" in text
    for phrase in (
        "an empty label value",
        "line endings and trailing blank lines",
        "character entities and links",
        "only `onlinetext` or only `file`",
        "These are open decisions",
    ):
        assert phrase in text, phrase


def test_prd_examples_are_the_five_required_vectors() -> None:
    blocks, items = _example_blocks_and_items()
    assert len(blocks) == 5 and len(items) == 5
    for case_id, block, item in zip(PRD_EXAMPLE_IDS, blocks, items, strict=True):
        case = _case(case_id)
        assert block == case["input"]["onlinetext"], case_id
        report = case["expected"]["report"]
        if "words" in report:
            found = re.search(r"(\d+) words", item)
            assert found and int(found.group(1)) == report["words"], case_id
        for part in PARTS:
            if "error" in case["expected"][part]:
                assert f"`{case['expected'][part]['error']}`" in item, case_id
    file_case = _case("report-as-file")["input"]["files"][0]
    assert file_case["name"] == "report.md" and "`report.md`" in items[3]
    assert (
        file_case["text"]
        == "# Reflection\n\nI built an assistant and it answered badly at first."
    )
    assert (
        "`# Reflection`" in items[3]
        and "I built an assistant and it answered badly at first." in items[3]
    )
    assert "unverified" in items[1]


def test_every_covers_entry_names_a_rule_the_prd_has() -> None:
    covered = {r for c in _vectors()["cases"] for r in c["covers"]}
    assert covered <= RULES
    numbers = {int(r.split("-")[1]) for r in covered if r.startswith("B1.5-")}
    assert numbers <= set(range(1, 10))
    assert "B1.3-word_count" in covered and "`word_count:<n>`" in _b13()


def test_every_rule_a_vector_can_show_is_covered_by_a_vector() -> None:
    covered = {r for c in _vectors()["cases"] for r in c["covers"]}
    assert covered == SHOWABLE_RULES


def test_the_prd_mentions_the_vectors_file() -> None:
    assert "contracts/test-vectors/submission.v1.json" in _b15()


# --- the traceability file -----------------------------------------------------------------


def test_traceability_lists_the_open_decisions_and_who_decides_them() -> None:
    text = " ".join(TRACEABILITY_PATH.read_text(encoding="utf-8").split())
    assert "contracts/test-vectors/submission.v1.json" in text
    assert "test_submission_vectors_v1.py" in text
    start = text.index("Open decisions (B1 submission content)")
    section = text[start : start + 4000].lower()
    for phrase in (
        "Harshitha",
        "Shraddha",
        "The guide",
        "empty label value",
        "line endings",
        "character entities",
        "only `onlinetext` or only `file`",
        "`repo_file:<path>`",
        "test-only reference extractor",
        "decision record",
    ):
        assert phrase.lower() in section, phrase

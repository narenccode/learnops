"""B1 submission-content rules (PRD B1.3 check formats, B1.5): the shared test vectors and their
link to the PRD text.

AUTOMATED here (data and text only; no reader of submissions exists yet):
  * `contracts/test-vectors/submission.v1.json` has the submission cases and the README cases,
    each with the exact shape, the closed vocabularies (status, format, source, error code, result)
    and consistent expected values (a word count equals the words of the report, a report file
    named as the source is in the input, a part has a value or an error, never both, a missing
    README section is named in the check). The HTML case is marked unverified until the lab;
  * `covers` says what a case shows: rules 8 and 9 are never listed (part-level results cannot show
    them), a word-count entry appears exactly when the report has a word count, an expected error
    lists rule 7, an HTML case lists rule 5, a report from a file lists rule 4, and every other
    rule that a vector can show (1 to 7 and the word count) is covered by at least one case;
  * the five PRD examples in B1.5 are the same texts as the five required vectors, with the same
    word counts and error codes, so the PRD and the vectors cannot drift apart;
  * the PRD has the B1.3 check formats (including how a Check cell is split, the `word_count`
    argument, and the README file, heading, fence and name rules), C3.5 says `word_count` reads the
    report, and the PRD has nine numbered B1.5 rules; every `covers` entry of a vector names a
    rule that exists;
  * the open points are written down, not decided: the PRD says what v1 does not define, the
    traceability file lists each open decision with who decides it, and no vector covers one
    (no carriage return, no empty label value, no HTML entity or link, no trailing whitespace);
  * the shape and open-point checks catch the mistakes they exist for (negative controls).

NOT automated here, so NOT claimed: that any reader extracts the parts correctly or finds README
headings correctly. The marking-table parser (Module 2, `libs/contracts`) and the submission
extractor (Module 3, Release 4) do not exist; they must pass these vectors. There is no test-only
reader of either, on purpose. The HTML result is unverified until the Moodle lab check.
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
# line (the guide's answer A3). Two more cases clarify rule 7 (a Demo: after Report: and a second
# Report: line), decided by the guide on PR #87 (2026-11-15).
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
    "demo-after-report",
    "second-report-line",
    # The word_count counting rule (#186, proposed by Student 1 through /contract-change).
    "word-count-punctuation-and-url",
    "word-count-plain-markdown-kept",
    "report-md-with-byte-order-mark",
]
README_CASE_IDS = [
    "readme-headings-any-case",
    "readme-setext-and-fenced-are-not-headings",
    "readme-only-root-readme-md",
    "readme-name-with-semicolon",
    "readme-heading-must-match-whole-text",
    "readme-closing-hashes-tab-and-trailing-spaces",
    "readme-tilde-and-unclosed-fences",
    "readme-closing-hashes-must-follow-a-space",
    "readme-heading-indentation-up-to-three-spaces",
    "readme-fence-indentation-up-to-three-spaces",
    "readme-closing-fence-same-character-and-length",
    "readme-fence-needs-three-characters",
    "readme-fence-needs-three-tildes",
    # The readme_sections matching rule (#186, proposed by Student 1 through /contract-change).
    "readme-case-folding-and-nfc",
    "readme-runs-of-spaces-are-one",
    "readme-inline-markup-is-kept",
    "readme-byte-order-mark-and-crlf",
    "readme-repeated-name-reported-once",
    "readme-non-breaking-space-is-not-a-space",
]
# The machine checks of PRD C3.5. A check that is named in a vector as the unknown one must not be
# one of these: a known name is not unknown. A test keeps this set equal to the PRD list.
C35_CHECK_NAMES = {
    "repo_clone",
    "repo_file",
    "readme_sections",
    "command",
    "http_ok",
    "word_count",
}

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
README_KEYS = {"id", "title", "status", "covers", "check", "files", "expected"}
README_COVERS = {"B1.3-readme-file", "B1.3-readme-headings", "B1.3-readme-name-chars"}
README_RESULTS = {"pass", "fail", "invalid"}
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
    # str.split() with no argument splits on any Unicode whitespace, so a non-breaking space
    # (U+00A0) also separates words here. The PRD only says "between whitespace"; whether a reader
    # must split on a non-breaking space is part of the open HTML-details decision, and no vector
    # contains one, so this does not decide it. The word-count definition is unchanged.
    if entry["words"] != len(entry["value"].split()):
        problems.append(
            "report: words is not the number of whitespace-separated pieces of value"
        )
    # A report file is read as UTF-8 with a leading byte-order mark removed (PRD B1.3), so the
    # report is the file text without it.
    if entry["source"] != "onlinetext" and not any(
        f["name"] == entry["source"] and f["text"].removeprefix("﻿") == entry["value"]
        for f in files
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


def _later_check_names(check: str) -> list[str]:
    """The names of the checks after the first one in a Check cell (PRD B1.3).

    Checks are separated by `;`, spaces around each check are ignored, and a name is the text
    before the first `:`. Only what this file's vectors need: it does not validate arguments.
    """
    parts = [part.strip() for part in check.split(";")]
    return [part.split(":", 1)[0].strip() for part in parts[1:]]


def readme_case_problems(case: Any) -> list[str]:
    """What is wrong with one README vector: shape, vocabularies and the expected result.

    Data only: there is no reader of READMEs, so a result is not recomputed here.
    """
    if not isinstance(case, dict) or set(case) != README_KEYS:
        return [f"keys are not exactly {sorted(README_KEYS)}"]
    problems: list[str] = []
    if case["status"] != "derived":
        problems.append("status must be 'derived'")
    covers = case["covers"]
    if not (isinstance(covers, list) and covers and set(covers) <= README_COVERS):
        problems.append(f"covers must be a non-empty list from {sorted(README_COVERS)}")
    check = case["check"]
    if not (isinstance(check, str) and check.startswith("readme_sections:")):
        return [*problems, "check must be a readme_sections check"]
    files = case["files"]
    if not (
        isinstance(files, list)
        and files
        and all(isinstance(f, dict) and set(f) == {"name", "text"} for f in files)
    ):
        return [*problems, "files must be a non-empty list of {name, text}"]
    expected = case["expected"]
    result = expected.get("result") if isinstance(expected, dict) else None
    names = check.removeprefix("readme_sections:").replace(";", ",").split(",")
    if result == "pass" and set(expected) == {"result"}:
        return problems
    if result == "fail" and set(expected) == {"result", "missing"}:
        missing = expected["missing"]
        if not (isinstance(missing, list) and missing and set(missing) <= set(names)):
            problems.append("missing must name sections that the check lists")
        return problems
    if result == "invalid" and set(expected) == {"result", "unknown_check"}:
        # Whole check names, not substrings: `Usage` is not a match for the check `Usage2`.
        if expected["unknown_check"] not in _later_check_names(check):
            problems.append(
                "unknown_check must be a whole check name that follows a ';'"
            )
        # An unknown check cannot be a known one: `word_count` after a `;` is a valid check.
        if expected["unknown_check"] in C35_CHECK_NAMES:
            problems.append("unknown_check must not be a C3.5 check name")
        return problems
    return [*problems, f"expected {expected!r} is not a valid result"]


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


def test_vectors_file_is_lf_json_with_a_version_and_unique_case_ids() -> None:
    assert b"\r" not in VECTORS_PATH.read_bytes()
    doc = _vectors()
    assert doc["version"] == 1 and doc["$comment"]
    assert set(doc) == {"$comment", "version", "cases", "readme_cases"}
    assert [c["id"] for c in doc["cases"]] == CASE_IDS
    assert [c["id"] for c in doc["readme_cases"]] == README_CASE_IDS
    assert duplicate_ids(doc["cases"]) == [] == duplicate_ids(doc["readme_cases"])


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


def _readme_case(case_id: str) -> Case:
    found = [c for c in _vectors()["readme_cases"] if c["id"] == case_id]
    assert len(found) == 1, case_id
    case: Case = found[0]
    return case


@pytest.mark.parametrize("case_id", README_CASE_IDS)
def test_readme_case_has_the_required_shape_and_a_consistent_result(
    case_id: str,
) -> None:
    assert readme_case_problems(_readme_case(case_id)) == []


def test_readme_cases_cover_the_file_the_headings_and_the_name_rule() -> None:
    covered = {r for c in _vectors()["readme_cases"] for r in c["covers"]}
    assert covered == README_COVERS
    results = {c["expected"]["result"] for c in _vectors()["readme_cases"]}
    assert results == README_RESULTS


def _known_check_named_as_unknown(case: Case) -> None:
    # `word_count` really is the later check here, so only the C3.5 rule can reject this vector.
    case["check"] = "readme_sections:Setup;word_count:5"
    case["expected"]["unknown_check"] = "word_count"


README_EDITS: dict[str, tuple[str, Callable[[Case], None]]] = {
    "a missing key": ("readme-headings-any-case", lambda c: c.pop("check")),
    "a status that is not derived": (
        "readme-headings-any-case",
        lambda c: c.update(status="unverified-until-lab"),
    ),
    "an unknown result": (
        "readme-headings-any-case",
        lambda c: c["expected"].update(result="error"),
    ),
    "a missing section that the check does not list": (
        "readme-only-root-readme-md",
        lambda c: c["expected"].update(missing=["Deploy"]),
    ),
    "a fail with no missing sections": (
        "readme-only-root-readme-md",
        lambda c: c["expected"].update(missing=[]),
    ),
    "an unknown check that does not follow a semicolon": (
        "readme-name-with-semicolon",
        lambda c: c["expected"].update(unknown_check="Setup"),
    ),
    # `Usage` is only a substring of the check `Usage2`, so it is not that check's name.
    "an unknown check that is only part of a longer check name": (
        "readme-name-with-semicolon",
        lambda c: c.update(check="readme_sections:Setup;Usage2"),
    ),
    # The check is `readme_sections:Setup;word_count:5` and the unknown one `word_count`: it is
    # the later check, but it is a known C3.5 check, so the vector must be rejected.
    "an unknown check that is a known C3.5 check name": (
        "readme-name-with-semicolon",
        _known_check_named_as_unknown,
    ),
    "a case with no files": (
        "readme-headings-any-case",
        lambda c: c.update(files=[]),
    ),
}


@pytest.mark.parametrize("name", list(README_EDITS))
def test_the_readme_check_catches_what_it_exists_for(name: str) -> None:
    case_id, edit = README_EDITS[name]
    case = copy.deepcopy(_readme_case(case_id))
    assert readme_case_problems(case) == []
    edit(case)
    assert readme_case_problems(case)


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
        "Spaces around each check and around its argument are ignored",
        "The check name is the text before the first `:`",
        "Check names are lowercase and case-sensitive",
        "`Word_Count:5` is an unknown name",
        "A cell that contains only `—` means no machine check",
        "`readme_sections:<a,b,c>`",
        "case-insensitively",
        "cannot contain a comma or a semicolon",
        "named exactly `README.md` at the root of the repository",
        "is an ATX heading: up to three spaces, then one to six `#` characters",
        "then a space or a tab and the heading text",
        "four or more spaces before the `#` is not a heading",
        "is removed only when a space or a tab comes before it and only spaces or tabs follow it",
        "`## Setup ##` is the heading text `Setup` and `## C#` is `C#`",
        "Trailing spaces and tabs are removed and the heading text is trimmed",
        "matched against the whole heading text",
        "`Setup instructions` does not satisfy the name `Setup`",
        "is not a heading",
        "fenced code block",
        "A fence line starts, after up to three spaces, with at least three backticks",
        "or at least three tildes",
        "four or more spaces do not make a fence",
        "fewer than three of the same character",
        "is not a fence",
        "A closing fence uses the same character as the opening fence and is at least as long",
        "A fence that is not closed runs to the end of the file",
        "Setext heading",
        "`word_count:<n>`",
        "one or more ASCII digits (`0` to `9`) with no sign, space or underscore",
        "a value of at least 1",
        "`demo_url` is the only field in v1",
        "An unknown check name fails validation",
        "So does a known check whose argument breaks a format defined here",
        "An empty section list (`readme_sections:`)",
        "an empty section name (`readme_sections:a,,b`)",
        "an empty field (`http_ok:`) and a trailing `;` fail the same way (CK-09)",
        "are not defined here",
        "the argument format of `repo_file:<path>`",
        "the criterion keys",
        # The matching and counting rule (#186, /contract-change).
        "compared after Unicode normalisation NFC and case folding",
        "each run of spaces or tabs inside them treated as one space",
        "Inline markup is not removed",
        "A name listed twice must exist once, and a missing name is reported once",
        "a leading byte-order mark is removed, and LF, CRLF and CR each end a line",
        "A README that is missing or not valid UTF-8 fails the check",
        "Every piece counts, including one that is only punctuation",
        "a URL is one word",
        "Online text in plain format has no markup to remove",
        "A report file is read as UTF-8, and a leading byte-order mark is removed",
        "A report file that is not valid UTF-8 is not defined in v1",
        "Space, tab and the line ends separate words",
        "such as the non-breaking space, separates words is not defined in v1",
        "a non-breaking space is not a space",
    ):
        assert phrase in text, phrase
    # The finer Markdown details are decided (the guide, 2026-11-16), so they are no longer listed
    # as undefined, and each rule is written once.
    assert "finer details" not in text
    assert "whether a closing `#` sequence must follow a space" not in text
    assert text.count("a trailing `;`") == 1
    assert text.count("case-sensitive") == 1


def test_the_c35_names_in_the_tests_are_the_names_in_the_prd() -> None:
    # `unknown_check` in a vector is checked against this list, so it must not drift from C3.5.
    # Only the list itself counts: from the end of the "Machine checks (...)" heading to the
    # sentence "Unknown check names", with each parenthesised explanation removed first. A word
    # in backticks inside an explanation (say `demo_url`) is not a check name, so a later
    # additive edit to C3.5 cannot fail this test for the wrong reason.
    match = re.search(
        r"\*\*Machine checks[^\n]*?:\*\*(?P<list>.*?)Unknown check names",
        _prd(),
        flags=re.DOTALL,
    )
    assert match, "the C3.5 machine-check list was not found"
    without_explanations = re.sub(r"\([^()]*\)", "", match.group("list"))
    names = set(re.findall(r"`([a-z_]+)(?::<[^>]*>)?`", without_explanations))
    assert names == C35_CHECK_NAMES
    # The same extraction ignores a backticked word inside an explanation (negative control).
    probe = "`repo_clone` (the field `demo_url` is read), `word_count:<min>` (report) "
    probe_names = set(
        re.findall(r"`([a-z_]+)(?::<[^>]*>)?`", re.sub(r"\([^()]*\)", "", probe))
    )
    assert probe_names == {"repo_clone", "word_count"}


def test_prd_c35_says_word_count_reads_the_report() -> None:
    match = re.search(
        r"^### C3\.5 Technical requirements\n.*?(?=^\*\*Sandbox:\*\*)",
        _prd(),
        flags=re.DOTALL | re.MULTILINE,
    )
    assert match, "the C3.5 machine-check list was not found"
    text = " ".join(match.group(0).split())
    assert "`word_count:<min>` (report)" in text
    assert "report or text" not in text


def test_prd_b15_has_nine_numbered_rules_and_both_reason_codes() -> None:
    part = _b15()
    rules = part[: part.index("**Examples.**")]
    assert re.findall(r"(?m)^(\d)\. \*\*", rules) == [str(n) for n in range(1, 10)]
    assert "`field_missing`" in rules and "`field_repeated`" in rules
    flat = " ".join(rules.split())
    for phrase in (
        "must appear before `Report:`",
        "A second `Report:` line is part of the report",
        "is not `field_repeated`",
        "does not stop the others",
    ):
        assert phrase in flat, phrase
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
    raw = TRACEABILITY_PATH.read_text(encoding="utf-8")
    text = " ".join(raw.split())
    assert "contracts/test-vectors/submission.v1.json" in text
    assert "test_submission_vectors_v1.py" in text
    # The section runs from its heading to the next heading, whatever its length.
    found = re.search(
        r"^#+ Open decisions \(B1 submission content\)\n(.*?)(?=^#+ |\Z)",
        raw,
        flags=re.DOTALL | re.MULTILINE,
    )
    assert found, "the open-decisions section was not found"
    section = " ".join(found.group(1).split()).lower()
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
    # The Markdown details were decided on 2026-11-16: they are recorded as decided, no longer
    # listed as open, and the parser vectors are said to come in a separate pull request.
    assert "finer markdown details" not in section
    assert "Decided by the guide on PR #87 (2026-11-16)" in text
    assert "separate follow-up pull request" in section

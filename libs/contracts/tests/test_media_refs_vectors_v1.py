"""CK-12 `media_refs`: the shared test vectors and their link to the v1 scope.

AUTOMATED here (data and text only; the extractor does not exist yet):
  * `contracts/test-vectors/media-refs.v1.json` has the twenty-four cases, each with the exact
    shape, the closed vocabularies (status, format, input kind, covers) and expected values that
    are consistent with the body text: every listed reference appears in the body as written, a
    flagged reference is a listed reference that has a documented full-URL form (`http://`,
    `https://` or a protocol-relative `//host/`), and a listed reference that is not flagged has
    none;
  * every rule of the scope is covered by at least one case, and a case that claims an HTML
    element and attribute really contains it in its body;
  * `media_refs` lists every in-scope reference as written (full, protocol-relative and relative
    paths, `@@PLUGINFILE@@` and `data:` references), each URL of an srcset is its own entry
    without its descriptor, raw HTML inside a Markdown body is covered, and the excluded
    constructs (ordinary links, PDF links, iframes) give an empty list and no finding;
  * the one point that is not decided (whether CK-12 flags a URI scheme other than `http:`,
    `https:` and `data:`) is recorded as an `open-point` case that leaves exactly that part null;
  * the status of each case says where it comes from: the guide's scope (`derived`), or Akshita's
    M1 scope confirmation (`m1-scope-confirmed`, not a formal approval), or an undecided point (`open-point`);
  * the shape and consistency checks catch the mistakes they exist for (negative controls).

NOT automated here, so NOT claimed: that any extractor finds these references, or that CK-12 reports
them. The extractor belongs to the FR-C-01 model builder (Release 1, reused by Course Studio) and
CK-12 to the checker; both must pass these vectors. There is no test-only extractor, on purpose
(the same rule as the check-cell vectors, the guide's decision on PR #87). Approval of the B2
contract change by the affected M1 owner is tracked separately, not by these tests.
"""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Callable
from typing import Any

import pytest

from .helpers import ROOT

VECTORS_PATH = ROOT / "contracts" / "test-vectors" / "media-refs.v1.json"

CASE_IDS = [
    "markdown-image-inline",
    "markdown-image-reference-style",
    "html-img-src",
    "html-img-srcset-single-candidate",
    "html-video-src",
    "html-video-poster",
    "html-audio-src",
    "html-source-src",
    "html-source-srcset-single-candidate",
    "html-track-src",
    "mbz-html-body-full-url",
    "mbz-html-body-pluginfile-is-relative",
    "markdown-image-http",
    "html-img-protocol-relative",
    "data-uri-is-listed-and-not-flagged",
    "html-img-srcset-several-candidates",
    "relative-path-is-listed-and-not-flagged",
    "raw-html-inside-a-markdown-body",
    "other-uri-scheme-flagging-is-open",
    "excluded-ordinary-link",
    "excluded-pdf-link",
    "excluded-iframe-embed",
    "embedded-media-next-to-excluded-constructs",
    "no-media-in-body",
]

# 'derived' follows directly from the guide's scope (issue #232, item 6). 'm1-scope-confirmed' follows
# from Akshita's scope confirmation and review (issue #232): that `media_refs` lists every
# in-scope reference, which the guide's text does not state in so many words. 'open-point' records
# a point that is not decided and asserts nothing about the undecided part.
STATUSES = {"derived", "m1-scope-confirmed", "open-point"}
M1_CASES = {
    "mbz-html-body-pluginfile-is-relative",
    "data-uri-is-listed-and-not-flagged",
    "html-img-srcset-several-candidates",
    "relative-path-is-listed-and-not-flagged",
    "raw-html-inside-a-markdown-body",
}
OPEN_POINT_CASES = {"other-uri-scheme-flagging-is-open"}
# What the open point leaves undecided: whether CK-12 flags a scheme other than http:, https: and
# data:. The reference itself is in scope and is listed (Akshita's listing interpretation, as for
# data: and relative paths); only its flagging is undecided.
OPEN_POINT_NULLS = {"other-uri-scheme-flagging-is-open": {"ck12_flagged"}}
FORMATS = {"markdown", "html"}
INPUT_KINDS = {"package", "mbz"}
# One rule per element and attribute of the scope, plus the other rules.
ELEMENT_RULES = {
    "html-img-src": r"<img\b[^>]*\ssrc=",
    "html-img-srcset": r"<img\b[^>]*\ssrcset=",
    "html-video-src": r"<video\b[^>]*\ssrc=",
    "html-video-poster": r"<video\b[^>]*\sposter=",
    "html-audio-src": r"<audio\b[^>]*\ssrc=",
    "html-source-src": r"<source\b[^>]*\ssrc=",
    "html-source-srcset": r"<source\b[^>]*\ssrcset=",
    "html-track-src": r"<track\b[^>]*\ssrc=",
}
EXCLUDED_RULES = {
    "excluded-ordinary-link": r"\]\(https?://[^)]*/guide\)|<a\b[^>]*\shref=",
    "excluded-pdf-link": r"\.pdf",
    "excluded-iframe": r"<iframe\b",
}
OTHER_RULES = {
    "markdown-image-inline",
    "markdown-image-reference-style",
    "activity-body-mbz-html",
    "html-in-markdown-body",
    "pluginfile-relative",
    "data-uri-listed-not-flagged",
    "relative-path-listed-not-flagged",
    "srcset-one-entry-per-url",
    "flag-http",
    "flag-https",
    "flag-protocol-relative",
    "other-scheme-flagging-open",
    "empty-means-none",
}
RULES = set(ELEMENT_RULES) | set(EXCLUDED_RULES) | OTHER_RULES
CASE_KEYS = {"id", "title", "status", "covers", "input_kind", "body", "expected"}
EXPECTED_KEYS = {"media_refs", "ck12_flagged"}
# The full-URL forms the guide's list names for CK-12: http://, https:// and //host/. A scheme
# other than these and data: is an open point, and only that case uses one.
FULL_URL = re.compile(r"^(?:https?://|//[^/\s])")
HTML_TAG = re.compile(r"<(?:img|video|audio|source|track)\b")

Case = dict[str, Any]


def _vectors() -> dict[str, Any]:
    doc: dict[str, Any] = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
    return doc


def _case(case_id: str) -> Case:
    found = [c for c in _vectors()["cases"] if c["id"] == case_id]
    assert len(found) == 1, case_id
    case: Case = found[0]
    return case


def _is_str_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) for v in value)


def _status_problems(case: Case) -> list[str]:
    problems: list[str] = []
    if case["status"] not in STATUSES:
        problems.append(f"status must be one of {sorted(STATUSES)}")
    if (case["status"] == "open-point") != (case["id"] in OPEN_POINT_CASES):
        problems.append("only the undecided case is an open point")
    if (case["status"] == "m1-scope-confirmed") != (case["id"] in M1_CASES):
        problems.append(
            "m1-scope-confirmed is for the cases that rest on Akshita's confirmation"
        )
    return problems


def _rule_problems(case: Case, covers: list[str], text: str) -> list[str]:
    """What a case claims to show (`covers`) against its body and expected values."""
    problems: list[str] = []
    refs, flagged = case["expected"]["media_refs"], case["expected"]["ck12_flagged"]
    for rule in covers:
        pattern = ELEMENT_RULES.get(rule) or EXCLUDED_RULES.get(rule)
        if pattern and not re.search(pattern, text):
            problems.append(f"the body does not contain what {rule} claims")
    if covers and all(rule in EXCLUDED_RULES for rule in covers):
        if refs != [] or flagged != []:
            problems.append("an excluded construct gives no reference and no finding")
    if "pluginfile-relative" in covers and (
        "@@PLUGINFILE@@/" not in text
        or flagged != []
        or not any(r.startswith("@@PLUGINFILE@@/") for r in refs or [])
    ):
        problems.append(
            "a @@PLUGINFILE@@ reference is relative: listed and not flagged"
        )
    if "data-uri-listed-not-flagged" in covers and not (
        any(r.startswith("data:") for r in refs or []) and flagged == []
    ):
        problems.append("a data: URI is listed as written and not flagged")
    if "relative-path-listed-not-flagged" in covers and not (
        refs
        and all(
            not FULL_URL.match(r) and not r.startswith(("data:", "@@PLUGINFILE@@"))
            for r in refs
        )
        and flagged == []
    ):
        problems.append("a plain relative path is listed as written and not flagged")
    if "srcset-one-entry-per-url" in covers and not (
        refs and len(refs) >= 2 and not any(re.search(r"\s", r) for r in refs)
    ):
        problems.append("each srcset URL is its own entry, without its descriptor")
    if "html-in-markdown-body" in covers and not (
        case["body"]["format"] == "markdown" and HTML_TAG.search(text)
    ):
        problems.append("raw HTML inside a Markdown body")
    if "other-scheme-flagging-open" in covers and not re.search(r"\bftp://", text):
        problems.append(
            "the open case uses a scheme other than http:, https: and data:"
        )
    if "activity-body-mbz-html" in covers and (
        case["input_kind"] != "mbz" or case["body"]["format"] != "html"
    ):
        problems.append("an .mbz body case must be input_kind mbz with html text")
    return problems


def case_problems(case: Any) -> list[str]:
    """What is wrong with one vector: shape, vocabularies and the expected values."""
    if not isinstance(case, dict) or set(case) != CASE_KEYS:
        return [f"keys are not exactly {sorted(CASE_KEYS)}"]
    problems = _status_problems(case)
    if case["input_kind"] not in INPUT_KINDS:
        problems.append(f"input_kind must be one of {sorted(INPUT_KINDS)}")
    covers = case["covers"]
    if not (isinstance(covers, list) and covers and set(covers) <= RULES):
        problems.append("covers must be a non-empty list of rules of the scope")
        covers = []
    body = case["body"]
    if not (
        isinstance(body, dict)
        and set(body) == {"format", "text"}
        and body["format"] in FORMATS
        and isinstance(body["text"], str)
        and body["text"]
    ):
        return problems + ["body must be {format, text} with a known format and text"]
    text: str = body["text"]
    expected = case["expected"]
    if not (isinstance(expected, dict) and set(expected) == EXPECTED_KEYS):
        return problems + [f"expected keys are not exactly {sorted(EXPECTED_KEYS)}"]
    refs, flagged = expected["media_refs"], expected["ck12_flagged"]
    for name, value in (("media_refs", refs), ("ck12_flagged", flagged)):
        if value is not None and not _is_str_list(value):
            problems.append(f"{name} must be a list of strings or null")
    if problems:
        return problems
    if case["status"] != "open-point" and (refs is None or flagged is None):
        problems.append("a derived or m1-scope-confirmed case decides both lists")
    if case["status"] == "open-point":
        undecided = {k for k, v in expected.items() if v is None}
        if undecided != OPEN_POINT_NULLS.get(case["id"]):
            problems.append("an open point must leave exactly the undecided part null")
    if refs is not None:
        for ref in refs:
            if ref not in text:
                problems.append(f"{ref!r} is listed but is not in the body as written")
        if len(set(refs)) != len(refs):
            problems.append("duplicate references are not covered by the decisions")
    if flagged is not None:
        if any(f.startswith("data:") for f in flagged):
            problems.append("a data: URI is never flagged in v1")
        for ref in flagged:
            if not FULL_URL.match(ref):
                problems.append(
                    f"{ref!r} is flagged but has no documented full-URL form"
                )
            if refs is not None and ref not in refs:
                problems.append(f"{ref!r} is flagged but is not listed")
        if refs is not None:
            for ref in refs:
                if FULL_URL.match(ref) and ref not in flagged:
                    problems.append(f"{ref!r} is a full URL but is not flagged")
    return problems + _rule_problems(case, covers, text)


def test_the_vectors_file_has_the_agreed_top_level_shape() -> None:
    doc = _vectors()
    assert set(doc) == {"$comment", "version", "cases"}
    assert doc["version"] == 1
    comment = doc["$comment"]
    assert "issues/232" in comment and "item 6" in comment
    assert "7183976351" in comment  # Akshita's M1 confirmation and review
    assert "not an extractor" in comment
    assert "tracked separately" in comment


def test_the_cases_are_exactly_the_expected_ones_in_order() -> None:
    ids = [c["id"] for c in _vectors()["cases"]]
    assert ids == CASE_IDS
    assert len(set(ids)) == len(ids)


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_every_case_is_well_formed_and_consistent(case_id: str) -> None:
    assert case_problems(_case(case_id)) == []


def test_every_rule_of_the_scope_is_covered() -> None:
    covered = {rule for c in _vectors()["cases"] for rule in c["covers"]}
    assert covered == RULES


def test_both_input_kinds_are_used_and_mbz_bodies_are_html() -> None:
    cases = _vectors()["cases"]
    assert {c["input_kind"] for c in cases} == INPUT_KINDS
    assert all(c["body"]["format"] == "html" for c in cases if c["input_kind"] == "mbz")


def test_every_element_and_attribute_of_the_scope_has_its_own_case() -> None:
    by_rule = {
        rule: [c["id"] for c in _vectors()["cases"] if rule in c["covers"]]
        for rule in ELEMENT_RULES
    }
    assert all(by_rule.values()), by_rule


def test_a_moodle_pluginfile_reference_is_listed_and_never_flagged() -> None:
    case = _case("mbz-html-body-pluginfile-is-relative")
    assert case["expected"] == {
        "media_refs": ["@@PLUGINFILE@@/diagram.png"],
        "ck12_flagged": [],
    }


def test_every_in_scope_reference_is_listed_even_when_it_is_not_flagged() -> None:
    data = _case("data-uri-is-listed-and-not-flagged")
    assert data["expected"] == {
        "media_refs": ["data:image/png;base64,iVBORw0KGgo="],
        "ck12_flagged": [],
    }
    relative = _case("relative-path-is-listed-and-not-flagged")
    assert relative["expected"] == {
        "media_refs": ["media/week-01/diagram.png"],
        "ck12_flagged": [],
    }


def test_each_url_of_a_srcset_is_its_own_entry_without_the_descriptor() -> None:
    case = _case("html-img-srcset-several-candidates")
    assert "1x" in case["body"]["text"] and "2x" in case["body"]["text"]
    refs = case["expected"]["media_refs"]
    assert refs == [
        "https://example.invalid/a.png",
        "https://example.invalid/b.png",
    ]
    assert case["expected"]["ck12_flagged"] == refs


def test_raw_html_inside_a_markdown_body_is_covered() -> None:
    case = _case("raw-html-inside-a-markdown-body")
    assert case["body"]["format"] == "markdown" and case["input_kind"] == "package"
    refs = case["expected"]["media_refs"]
    assert refs == ["https://example.invalid/a.png", "https://example.invalid/a.mp3"]
    assert case["expected"]["ck12_flagged"] == refs


def test_the_excluded_constructs_give_no_reference_and_no_finding() -> None:
    for case_id in (
        "excluded-ordinary-link",
        "excluded-pdf-link",
        "excluded-iframe-embed",
        "no-media-in-body",
    ):
        assert _case(case_id)["expected"] == {"media_refs": [], "ck12_flagged": []}


def test_embedded_media_is_listed_next_to_excluded_constructs() -> None:
    case = _case("embedded-media-next-to-excluded-constructs")
    text = case["body"]["text"]
    assert "<iframe" in text and ".pdf" in text and "](https://" in text
    ref = "https://example.invalid/media/diagram.png"
    assert case["expected"] == {"media_refs": [ref], "ck12_flagged": [ref]}


def test_the_full_url_forms_are_http_https_and_protocol_relative() -> None:
    flagged = {
        ref
        for c in _vectors()["cases"]
        for ref in (c["expected"]["ck12_flagged"] or [])
    }
    assert any(r.startswith("https://") for r in flagged)
    assert any(r.startswith("http://") for r in flagged)
    assert any(r.startswith("//") for r in flagged)
    assert not any(r.startswith("data:") for r in flagged)


def test_the_statuses_say_where_each_case_comes_from() -> None:
    status = {c["id"]: c["status"] for c in _vectors()["cases"]}
    assert {i for i, s in status.items() if s == "m1-scope-confirmed"} == M1_CASES
    assert {i for i, s in status.items() if s == "open-point"} == OPEN_POINT_CASES
    assert {s for s in status.values()} == STATUSES


def test_the_open_point_is_the_flagging_of_other_uri_schemes() -> None:
    # The guide's list flags http://, https:// and //host/. Akshita proposes any scheme other than
    # data:. The vectors list the reference and leave the flagging undecided (null).
    case = _case("other-uri-scheme-flagging-is-open")
    assert case["status"] == "open-point"
    assert case["expected"] == {
        "media_refs": ["ftp://example.invalid/a.png"],
        "ck12_flagged": None,
    }


def test_no_other_case_uses_a_scheme_or_form_that_is_not_decided() -> None:
    # Other schemes (ftp:, mailto:, file:, ...), tag or attribute case, quoting styles, duplicates
    # and Markdown titles are not covered; a case that used one would be deciding it. The one
    # case that uses ftp: is the open point.
    for case in _vectors()["cases"]:
        text = case["body"]["text"]
        assert not re.search(r"(?i)\b(?:mailto|file|javascript):", text), case["id"]
        if case["id"] not in OPEN_POINT_CASES:
            assert not re.search(r"(?i)\bftp:", text), case["id"]
        assert not re.search(r"<[A-Z]", text), case["id"]
        assert "='" not in text and '=""' not in text, case["id"]
        assert not re.search(r'\]\([^)]*\s"', text), case["id"]


# --- the checks themselves must catch what they exist for (negative controls) ---------------


def _with(case_id: str, change: Callable[[Case], None]) -> Case:
    case = copy.deepcopy(_case(case_id))
    change(case)
    return case


def _set_expected(key: str, value: Any) -> Callable[[Case], None]:
    def change(case: Case) -> None:
        case["expected"][key] = value

    return change


NEGATIVE_CONTROLS: dict[str, tuple[str, Callable[[Case], None], str]] = {
    "unknown status": (
        "html-img-src",
        lambda c: c.__setitem__("status", "guess"),
        "status must be one of",
    ),
    "a status that does not match the source": (
        "data-uri-is-listed-and-not-flagged",
        lambda c: c.__setitem__("status", "derived"),
        "m1-scope-confirmed is for the cases",
    ),
    "a listed reference that is not in the body": (
        "html-img-src",
        _set_expected("media_refs", ["https://example.invalid/other.png"]),
        "is listed but is not in the body",
    ),
    "a full URL that is not flagged": (
        "html-img-src",
        _set_expected("ck12_flagged", []),
        "is a full URL but is not flagged",
    ),
    "a relative reference that is flagged": (
        "mbz-html-body-pluginfile-is-relative",
        _set_expected("ck12_flagged", ["@@PLUGINFILE@@/diagram.png"]),
        "has no documented full-URL form",
    ),
    "a plain relative path that is flagged": (
        "relative-path-is-listed-and-not-flagged",
        _set_expected("ck12_flagged", ["media/week-01/diagram.png"]),
        "has no documented full-URL form",
    ),
    "a data: URI that is flagged": (
        "data-uri-is-listed-and-not-flagged",
        _set_expected("ck12_flagged", ["data:image/png;base64,iVBORw0KGgo="]),
        "a data: URI is never flagged in v1",
    ),
    "a data: URI that is not listed": (
        "data-uri-is-listed-and-not-flagged",
        _set_expected("media_refs", []),
        "a data: URI is listed as written and not flagged",
    ),
    "an srcset entry that keeps its descriptor": (
        "html-img-srcset-several-candidates",
        _set_expected(
            "media_refs",
            ["https://example.invalid/a.png 1x", "https://example.invalid/b.png 2x"],
        ),
        "each srcset URL is its own entry, without its descriptor",
    ),
    "an srcset with only one entry": (
        "html-img-srcset-several-candidates",
        _set_expected("media_refs", ["https://example.invalid/a.png"]),
        "each srcset URL is its own entry, without its descriptor",
    ),
    "raw HTML claimed in a body that is not Markdown": (
        "raw-html-inside-a-markdown-body",
        lambda c: c["body"].__setitem__("format", "html"),
        "raw HTML inside a Markdown body",
    ),
    "an excluded construct that gives a finding": (
        "excluded-iframe-embed",
        _set_expected("media_refs", ["https://example.invalid/embed/video"]),
        "an excluded construct gives no reference and no finding",
    ),
    "a covers claim the body does not show": (
        "html-video-poster",
        lambda c: c["covers"].append("html-audio-src"),
        "the body does not contain what html-audio-src claims",
    ),
    "a derived case that leaves a part undecided": (
        "html-img-src",
        _set_expected("media_refs", None),
        "decides both lists",
    ),
    "an open point that decides the undecided part": (
        "other-uri-scheme-flagging-is-open",
        _set_expected("ck12_flagged", ["ftp://example.invalid/a.png"]),
        "an open point must leave exactly the undecided part null",
    ),
    "an open point that leaves a decided part null": (
        "other-uri-scheme-flagging-is-open",
        _set_expected("media_refs", None),
        "an open point must leave exactly the undecided part null",
    ),
    "an extra key": (
        "html-img-src",
        lambda c: c.__setitem__("note", "x"),
        "keys are not exactly",
    ),
}


@pytest.mark.parametrize("name", list(NEGATIVE_CONTROLS))
def test_the_checks_catch_the_mistakes_they_exist_for(name: str) -> None:
    case_id, change, expected_text = NEGATIVE_CONTROLS[name]
    assert any(expected_text in p for p in case_problems(_with(case_id, change))), name

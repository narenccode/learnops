"""B6.2 lesson files (PRD B6.2): chapters.json, slides.json and cues.json.

AUTOMATED here:
  * the three schemas are valid Draft 2020-12 schemas, and every top-level example in
    contracts/examples/<name>.v1/ validates against its schema and its validator;
  * chapters: bare array of {start, end, title}; fractional seconds; end after start, ascending
    order and no overlap (validator rules, because JSON Schema cannot compare two properties);
    gaps and touching chapters allowed;
  * slides: bare array of {t, thumb, text?}; thumb follows the manifest relative-path rule, starts
    with slides/ and ends in .jpg; no fixed number of digits; text unrestricted;
  * cues: bare array of {t, type, ref, label, required?}; types h5p, image and url with the ref
    rules of the guide's decision; any other lowercase token accepted by the schema and ignored by
    a v1 reader; label required and not empty; required is a boolean, absent means false; an
    empty array is valid;
  * the path rule and the type-token pattern are the same text as in the manifest schema, and the
    shared path vectors are run against the new schemas; a lesson with no cues file has no cues;
  * check_within_duration, the consumer-level rule that every chapter start and end and every cue
    t is within duration_s, with duration_s used as given (no rounding, no tolerance);
  * the guide's four decisions of 2026-11-15: unrounded duration_s without tolerance, times of at
    least 0, cue types in the slug form of a track role, and a thumbnail name with at least one
    character before .jpg.

NOT automated here, and therefore NOT claimed:
  * that the files named by thumb and image refs exist, that an h5p ref is the idnumber of a real
    activity, that a url is allowed by the player (the validators list these as not checked);
  * that duration_s is checked by JSON Schema: it is not. Only check_within_duration does it.
"""

from __future__ import annotations

import copy
import json
import math
import re
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from contracts import (
    check_within_duration,
    cue_is_required,
    readable_cues,
    validate_chapters,
    validate_cues,
    validate_slides,
)

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "contracts"
EXAMPLES = CONTRACTS / "examples"
MANIFEST_SCHEMA = CONTRACTS / "lesson-manifest.v1.schema.json"
VECTORS = CONTRACTS / "test-vectors" / "relative-path.v1.json"
DURATION_S = 742  # the duration_s of the manifest examples; the examples stay within it

Doc = Any


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_of(name: str) -> Draft202012Validator:
    return Draft202012Validator(load(CONTRACTS / f"{name}.v1.schema.json"))


CHAPTERS_SCHEMA = schema_of("chapters")
SLIDES_SCHEMA = schema_of("slides")
CUES_SCHEMA = schema_of("cues")
SCHEMAS = {"chapters": CHAPTERS_SCHEMA, "slides": SLIDES_SCHEMA, "cues": CUES_SCHEMA}
VALIDATORS = {
    "chapters": validate_chapters,
    "slides": validate_slides,
    "cues": validate_cues,
}


def example_files(name: str) -> list[Path]:
    return sorted(p for p in (EXAMPLES / f"{name}.v1").glob("*.json"))


def codes(report: Any) -> list[str]:
    return [issue.code for issue in report.errors]


def chapter(start: float, end: float, title: str = "A chapter") -> dict[str, Any]:
    return {"start": start, "end": end, "title": title}


def cue(**fields: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "t": 10,
        "type": "h5p",
        "ref": "wk-01-practice",
        "label": "Try it",
    }
    base.update(fields)
    return base


def slide(**fields: Any) -> dict[str, Any]:
    base: dict[str, Any] = {"t": 0, "thumb": "slides/001.jpg"}
    base.update(fields)
    return base


# --- schemas and examples ------------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(SCHEMAS))
def test_schema_is_a_valid_draft_2020_12_schema(name: str) -> None:
    schema = load(CONTRACTS / f"{name}.v1.schema.json")
    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["type"] == "array", "each file is a bare array, not an object wrapper"


@pytest.mark.parametrize("name", sorted(SCHEMAS))
def test_each_schema_has_a_top_level_example(name: str) -> None:
    # The layout the shared example validator (PR #68) reads: top-level files of
    # contracts/examples/<name>.v1/.
    assert example_files(name), f"no example in contracts/examples/{name}.v1/"


@pytest.mark.parametrize(
    "path",
    [p for n in sorted(SCHEMAS) for p in example_files(n)],
    ids=lambda p: f"{p.parent.name}/{p.name}",
)
def test_every_example_is_valid(path: Path) -> None:
    name = path.parent.name.removesuffix(".v1")
    document = load(path)
    assert isinstance(document, list)
    assert not list(SCHEMAS[name].iter_errors(document))
    report = VALIDATORS[name](document)
    assert report.ok, report.errors


def test_examples_show_what_the_guide_decided() -> None:
    chapters = load(EXAMPLES / "chapters.v1" / "chapters.json")
    assert len(chapters) > 1
    assert any(isinstance(c["start"], float) for c in chapters), "fractional seconds"
    assert any(b["start"] > a["end"] for a, b in zip(chapters, chapters[1:])), "a gap"

    slides = load(EXAMPLES / "slides.v1" / "slides.json")
    assert any("text" in s for s in slides) and any("text" not in s for s in slides)
    assert any(isinstance(s["t"], float) for s in slides)

    cues = load(EXAMPLES / "cues.v1" / "cues.json")
    assert {c["type"] for c in cues} == {"h5p", "image", "url"}
    assert any(c.get("required") is True for c in cues)
    assert any("required" not in c for c in cues)
    assert load(EXAMPLES / "cues.v1" / "empty.json") == []


def test_examples_are_within_the_example_lesson_duration() -> None:
    report = check_within_duration(
        DURATION_S,
        chapters=load(EXAMPLES / "chapters.v1" / "chapters.json"),
        slides=load(EXAMPLES / "slides.v1" / "slides.json"),
        cues=load(EXAMPLES / "cues.v1" / "cues.json"),
    )
    assert report.ok, report.errors


@pytest.mark.parametrize("name", sorted(SCHEMAS))
@pytest.mark.parametrize("bad", [{}, {"items": []}, "text", 5, None])
def test_a_document_that_is_not_an_array_is_rejected(name: str, bad: Any) -> None:
    assert list(SCHEMAS[name].iter_errors(bad))
    assert VALIDATORS[name](bad).errors


@pytest.mark.parametrize("name", sorted(SCHEMAS))
def test_unknown_fields_are_accepted(name: str) -> None:
    # PRD B.0, EXT-02: readers ignore unknown fields.
    sample = {
        "chapters": [chapter(0, 10)],
        "slides": [slide()],
        "cues": [cue()],
    }[name]
    sample = [chapter(0, 10), chapter(10, 20)] if name == "chapters" else sample * 2
    for entry in sample:
        entry["added_in_a_later_release"] = {"anything": True}
    assert not list(SCHEMAS[name].iter_errors(sample))
    assert VALIDATORS[name](sample).ok


# --- the shared rules are the same text as in the other contracts --------------------------


def test_relative_path_pattern_is_the_manifest_pattern() -> None:
    manifest = load(MANIFEST_SCHEMA)["$defs"]["relative_path"]["pattern"]
    slides = load(CONTRACTS / "slides.v1.schema.json")["$defs"]["relative_path"][
        "pattern"
    ]
    cues = load(CONTRACTS / "cues.v1.schema.json")["$defs"]["relative_path"]["pattern"]
    assert slides == manifest
    assert cues == manifest


def test_type_token_pattern_is_the_manifest_slug_pattern() -> None:
    slug = load(MANIFEST_SCHEMA)["$defs"]["slug"]["pattern"]
    cue_type = load(CONTRACTS / "cues.v1.schema.json")["$defs"]["cue"]["properties"][
        "type"
    ]
    assert cue_type["pattern"] == slug


def test_shared_path_vectors_are_accepted_and_rejected_in_slides_and_cues() -> None:
    vectors = load(VECTORS)
    for item in vectors["invalid"]:
        path = item["path"]
        assert list(SLIDES_SCHEMA.iter_errors([slide(thumb=path)])), path
        assert list(CUES_SCHEMA.iter_errors([cue(type="image", ref=path)])), path
    for item in vectors["valid"]:
        path = item["path"]
        assert not list(CUES_SCHEMA.iter_errors([cue(type="image", ref=path)])), path
        # A valid manifest path is a valid thumbnail once it is under slides/ and ends in .jpg.
        thumb = f"slides/{path}.jpg"
        assert not list(SLIDES_SCHEMA.iter_errors([slide(thumb=thumb)])), thumb


# --- chapters ------------------------------------------------------------------------------


def test_valid_chapter_list_is_accepted() -> None:
    assert validate_chapters([chapter(0, 60), chapter(60, 120.5), chapter(130, 200)]).ok


def test_empty_chapter_list_is_accepted_by_the_schema() -> None:
    # The guide did not ask for a minimum number of chapters, so none is required.
    assert validate_chapters([]).ok


def test_fractional_chapter_times_are_accepted() -> None:
    assert validate_chapters([chapter(0.25, 95.5), chapter(95.5, 301.125)]).ok


def test_chapter_gaps_are_accepted() -> None:
    assert validate_chapters([chapter(0, 10), chapter(50, 60)]).ok


def test_chapters_that_touch_are_not_an_overlap() -> None:
    assert validate_chapters([chapter(0, 10), chapter(10, 20)]).ok


@pytest.mark.parametrize("start,end", [(10, 10), (10, 9.999), (10, 0)])
def test_chapter_end_not_after_start_is_rejected(start: float, end: float) -> None:
    report = validate_chapters([chapter(start, end)])
    assert codes(report) == ["chapter_end_not_after_start"]
    assert report.errors[0].location == (0, "end")


def test_unordered_chapters_are_rejected() -> None:
    report = validate_chapters([chapter(100, 110), chapter(0, 10)])
    assert codes(report) == ["chapters_not_in_order"]
    assert report.errors[0].location == (1, "start")


def test_overlapping_chapters_are_rejected() -> None:
    report = validate_chapters([chapter(0, 60), chapter(59.9, 120)])
    assert codes(report) == ["chapters_overlap"]
    assert report.errors[0].location == (1, "start")


def test_a_chapter_inside_another_is_an_overlap() -> None:
    assert codes(validate_chapters([chapter(0, 100), chapter(10, 20)])) == [
        "chapters_overlap"
    ]


def test_chapters_with_the_same_start_are_an_overlap() -> None:
    assert "chapters_overlap" in codes(
        validate_chapters([chapter(0, 10), chapter(0, 5)])
    )


def test_one_mistake_is_reported_once() -> None:
    # Out of order is reported as order only, not also as an overlap.
    assert codes(validate_chapters([chapter(100, 110), chapter(0, 150)])) == [
        "chapters_not_in_order"
    ]


def test_schema_alone_does_not_enforce_the_order_rules() -> None:
    # Documents the limit: JSON Schema cannot compare two properties, so these rules are the
    # validator's. If this ever fails, the schema has started to enforce them: update the docs.
    wrong = [chapter(10, 5), chapter(100, 110), chapter(0, 150)]
    assert not list(CHAPTERS_SCHEMA.iter_errors(wrong))
    assert validate_chapters(wrong).errors


@pytest.mark.parametrize(
    "bad",
    [
        [{"end": 10, "title": "x"}],
        [{"start": 0, "title": "x"}],
        [{"start": 0, "end": 10}],
        [{"start": "0", "end": 10, "title": "x"}],
        [{"start": 0, "end": "00:10", "title": "x"}],
        [{"start": 0, "end": 10, "title": 5}],
        [{"start": True, "end": 10, "title": "x"}],
        [{"start": -1, "end": 10, "title": "x"}],
        ["not an object"],
    ],
)
def test_chapter_with_wrong_fields_is_rejected(bad: Doc) -> None:
    assert validate_chapters(bad).errors


@pytest.mark.parametrize("bad_time", [math.nan, math.inf])
def test_non_finite_chapter_time_is_rejected(bad_time: float) -> None:
    assert "time_not_finite" in codes(validate_chapters([chapter(0, bad_time)]))


# --- slides --------------------------------------------------------------------------------


def test_valid_slide_list_is_accepted() -> None:
    assert validate_slides([slide(), slide(t=12.5, thumb="slides/002.jpg")]).ok


def test_slide_text_is_optional() -> None:
    assert validate_slides([slide()]).ok
    assert validate_slides([slide(text="Install Python")]).ok


def test_slide_text_has_no_restriction_in_v1() -> None:
    long_text = "<b>markup</b> and a very long text. " * 500
    assert validate_slides([slide(text=long_text), slide(text="")]).ok


def test_fractional_slide_time_is_accepted() -> None:
    assert validate_slides([slide(t=301.25)]).ok


def test_slide_thumbnail_names_have_no_fixed_digit_count() -> None:
    for name in (
        "slides/1.jpg",
        "slides/001.jpg",
        "slides/00001.jpg",
        "slides/intro.jpg",
    ):
        assert validate_slides([slide(thumb=name)]).ok, name


def test_slide_thumbnail_may_be_in_a_subfolder_of_slides() -> None:
    assert validate_slides([slide(thumb="slides/part-1/001.jpg")]).ok


@pytest.mark.parametrize(
    "thumb",
    [
        "001.jpg",  # not under slides/
        "images/001.jpg",
        "slides",  # no file
        "slides/",
        "slides/001.png",  # wrong extension
        "slides/001.jpeg",
        "slides/001.JPG",  # the extension is lowercase .jpg
        "slides/001.jpg.png",
        "Slides/001.jpg",
        "slides-extra/001.jpg",
    ],
)
def test_slide_thumbnail_outside_slides_or_not_jpg_is_rejected(thumb: str) -> None:
    assert validate_slides([slide(thumb=thumb)]).errors


@pytest.mark.parametrize(
    "thumb",
    [
        "/slides/001.jpg",  # absolute
        "slides/../001.jpg",
        "slides/./001.jpg",
        "slides//001.jpg",
        "slides\\001.jpg",
        "slides/0 01.jpg",
        "slides/001.jpg?x=1",
        "slides/001.jpg#frag",
        "https://example.org/slides/001.jpg",
        "slides/‮001.jpg",  # a control or format character
        "slides/001\n.jpg",
        "",
    ],
)
def test_slide_thumbnail_breaking_the_relative_path_rule_is_rejected(
    thumb: str,
) -> None:
    assert validate_slides([slide(thumb=thumb)]).errors


# --- no percent sign in a path (guide decision, B6.3 relative_path) ------------------------


@pytest.mark.parametrize(
    "thumb",
    [
        "slides/%2e.jpg",
        "slides/%2E.jpg",
        "slides/%252e.jpg",
        "slides/%25%32%65.jpg",
        "slides/100%.jpg",
        "slides/a%2fb.jpg",
        "slides/%/001.jpg",
        "slides/%2e%2e/001.jpg",
    ],
)
def test_slide_thumbnail_with_a_percent_sign_is_rejected(thumb: str) -> None:
    assert validate_slides([slide(thumb=thumb)]).errors


@pytest.mark.parametrize(
    "thumb", ["slides/001.jpg", "slides/12.jpg", "slides/week-1/001.jpg"]
)
def test_slide_thumbnail_without_a_percent_sign_is_accepted(thumb: str) -> None:
    assert validate_slides([slide(thumb=thumb)]).ok


@pytest.mark.parametrize(
    "bad",
    [
        [{"thumb": "slides/001.jpg"}],
        [{"t": 0}],
        [{"t": "0", "thumb": "slides/001.jpg"}],
        [{"t": -0.5, "thumb": "slides/001.jpg"}],
        [{"t": 0, "thumb": "slides/001.jpg", "text": 5}],
        [{"t": 0, "thumb": 5}],
    ],
)
def test_slide_with_wrong_fields_is_rejected(bad: Doc) -> None:
    assert validate_slides(bad).errors


def test_non_finite_slide_time_is_rejected() -> None:
    assert "time_not_finite" in codes(validate_slides([slide(t=math.nan)]))


# --- cues ----------------------------------------------------------------------------------


def test_all_three_known_cue_types_are_accepted() -> None:
    cues = [
        cue(type="h5p", ref="wk-01-practice"),
        cue(type="image", ref="images/diagram.png"),
        cue(type="url", ref="https://example.org/page"),
    ]
    assert validate_cues(cues).ok


def test_empty_cues_array_is_accepted() -> None:
    assert validate_cues([]).ok
    assert readable_cues([]) == []


def test_fractional_cue_time_is_accepted() -> None:
    assert validate_cues([cue(t=120.5)]).ok


def test_unknown_lowercase_type_is_accepted_and_ignored_by_a_v1_reader() -> None:
    cues = [cue(), cue(type="future-kind", ref="anything at all", label="Later")]
    assert validate_cues(cues).ok
    assert [c["type"] for c in readable_cues(cues)] == ["h5p"]


def test_a_cue_with_a_type_the_contract_dropped_is_not_special() -> None:
    # The guide decided against a separate scenario type: a branching scenario is an h5p item.
    # The token is still a valid lowercase token, so the schema accepts it and a v1 reader
    # ignores it, like any unknown type.
    cues = [cue(type="scenario", ref="x")]
    assert validate_cues(cues).ok
    assert readable_cues(cues) == []


@pytest.mark.parametrize(
    "bad_type",
    ["H5P", "Image", "h5p ", " h5p", "two words", "-x", "x-", "a--b", "h5p!", ""],
)
def test_malformed_or_uppercase_type_is_rejected(bad_type: str) -> None:
    assert validate_cues([cue(type=bad_type)]).errors


@pytest.mark.parametrize("bad_type", [5, None, ["h5p"], True])
def test_type_that_is_not_a_string_is_rejected(bad_type: Any) -> None:
    assert validate_cues([cue(type=bad_type)]).errors


@pytest.mark.parametrize("label", ["", None, 5, True])
def test_empty_or_non_string_label_is_rejected(label: Any) -> None:
    assert validate_cues([cue(label=label)]).errors


def test_missing_label_is_rejected() -> None:
    bad = cue()
    del bad["label"]
    assert validate_cues([bad]).errors


def test_label_has_no_length_limit_in_v1() -> None:
    assert validate_cues([cue(label="x" * 10_000)]).ok


@pytest.mark.parametrize("missing", ["t", "type", "ref"])
def test_missing_required_cue_field_is_rejected(missing: str) -> None:
    bad = cue()
    del bad[missing]
    assert validate_cues([bad]).errors


def test_missing_required_means_false() -> None:
    plain = cue()
    assert "required" not in plain
    assert validate_cues([plain]).ok
    assert cue_is_required(plain) is False


def test_required_true_and_false_are_accepted() -> None:
    assert validate_cues([cue(required=True), cue(required=False)]).ok
    assert cue_is_required(cue(required=True)) is True
    assert cue_is_required(cue(required=False)) is False


@pytest.mark.parametrize("bad", ["true", "yes", 1, 0, None, [], {}])
def test_non_boolean_required_is_rejected(bad: Any) -> None:
    assert validate_cues([cue(required=bad)]).errors


@pytest.mark.parametrize(
    "ref", ["wk-01-practice", "a", "Practice 1", "wk_01", "WK-01", "q1/2"]
)
def test_h5p_ref_that_is_an_idnumber_is_accepted(ref: str) -> None:
    # EXT-06 says "Moodle idnumber" and the guide named no form, so no form is imposed.
    assert validate_cues([cue(type="h5p", ref=ref)]).ok


@pytest.mark.parametrize("ref", ["", 5, None, ["wk-01"]])
def test_h5p_ref_that_is_empty_or_not_a_string_is_rejected(ref: Any) -> None:
    assert validate_cues([cue(type="h5p", ref=ref)]).errors


@pytest.mark.parametrize(
    "ref", ["diagram.png", "images/diagram.png", "whiteboards/w1/board.jpg"]
)
def test_image_ref_that_is_a_relative_path_is_accepted(ref: str) -> None:
    assert validate_cues([cue(type="image", ref=ref)]).ok


@pytest.mark.parametrize(
    "ref",
    [
        "",
        "/images/diagram.png",
        "../diagram.png",
        "images//diagram.png",
        "images\\diagram.png",
        "https://example.org/diagram.png",
        "images/diagram.png?x=1",
        "images/my diagram.png",
    ],
)
def test_image_ref_that_is_not_a_relative_path_is_rejected(ref: str) -> None:
    assert validate_cues([cue(type="image", ref=ref)]).errors


@pytest.mark.parametrize(
    "ref",
    [
        "https://example.org",
        "https://example.org/",
        "https://example.org/a/b?x=1&y=2#top",
        "https://sub.example.org:8443/path",
        "HTTPS://example.org/page",  # a URL scheme is not case-sensitive
    ],
)
def test_absolute_https_url_is_accepted(ref: str) -> None:
    assert validate_cues([cue(type="url", ref=ref)]).ok


@pytest.mark.parametrize(
    "ref",
    [
        "http://example.org/page",
        "HTTP://example.org",
        "ftp://example.org/file",
        "javascript:alert(1)",
        "data:text/html;base64,AAAA",
        "mailto:a@example.org",
        "//example.org/page",
        "example.org/page",
        "images/diagram.png",
        "https://",
        "https:///path",
        "https://example.org/a b",
        "https://example.org/\n",
        "https://exa mple.org",
        "",
    ],
)
def test_url_that_is_not_an_absolute_https_address_is_rejected(ref: str) -> None:
    assert validate_cues([cue(type="url", ref=ref)]).errors


def test_url_ref_is_not_subject_to_the_relative_path_rule() -> None:
    # C-08 does not apply to the url field: this value breaks the relative-path rule
    # (scheme, slashes, ?, #) and is still a valid url cue.
    ref = "https://example.org/a/b?x=1#top"
    relative = re.compile(load(MANIFEST_SCHEMA)["$defs"]["relative_path"]["pattern"])
    assert (
        relative.search(ref) is None
    ), "the example url must break the relative-path rule"
    assert validate_cues([cue(type="url", ref=ref)]).ok


@pytest.mark.parametrize(
    "ref",
    [
        "%2e%2e/x.png",
        "images/%252e%252e/x.png",
        "images/a%5cb.png",
        "images/%25%32%65.png",
        "100%.png",
        "%",
    ],
)
def test_image_ref_with_a_percent_sign_is_rejected(ref: str) -> None:
    assert validate_cues([cue(type="image", ref=ref)]).errors


@pytest.mark.parametrize(
    "ref",
    [
        "https://example.org/a%20b",
        "https://example.org/a%2Fb?q=100%25#top",
    ],
)
def test_url_ref_with_a_percent_sign_is_accepted(ref: str) -> None:
    # The no-% rule is the path rule (C-08) and does not apply to a url ref.
    assert validate_cues([cue(type="url", ref=ref)]).ok


def test_ref_of_an_unknown_type_is_only_a_string() -> None:
    assert validate_cues([cue(type="future-kind", ref="anything: at all/../x")]).ok
    assert validate_cues([cue(type="future-kind", ref="")]).ok
    assert validate_cues([cue(type="future-kind", ref=5)]).errors


def test_non_finite_cue_time_is_rejected() -> None:
    assert "time_not_finite" in codes(validate_cues([cue(t=math.inf)]))


def test_cue_time_must_not_be_negative() -> None:
    assert validate_cues([cue(t=-1)]).errors


# --- times against duration_s: a consumer-level rule ---------------------------------------


def test_schemas_do_not_check_times_against_the_duration() -> None:
    # The duration is in lesson.json, another file: no JSON Schema here can compare with it.
    far = 10**9
    assert not list(CHAPTERS_SCHEMA.iter_errors([chapter(0, far)]))
    assert not list(SLIDES_SCHEMA.iter_errors([slide(t=far)]))
    assert not list(CUES_SCHEMA.iter_errors([cue(t=far)]))
    assert validate_chapters([chapter(0, far)]).ok


def test_time_beyond_duration_is_rejected_by_the_consumer_check() -> None:
    report = check_within_duration(
        100,
        chapters=[chapter(0, 50), chapter(50, 100.5)],
        slides=[slide(t=101)],
        cues=[cue(t=100.0001)],
    )
    assert codes(report) == ["time_beyond_duration"] * 3
    assert [i.location for i in report.errors] == [(1, "end"), (0, "t"), (0, "t")]


def test_time_exactly_at_the_duration_is_accepted() -> None:
    assert check_within_duration(
        100, chapters=[chapter(0, 100)], slides=[slide(t=100)], cues=[cue(t=100)]
    ).ok


def test_absent_files_are_not_checked() -> None:
    assert check_within_duration(0).ok


@pytest.mark.parametrize("bad", [-1, math.nan, math.inf, True, "10", None])
def test_invalid_duration_is_a_programming_error(bad: Any) -> None:
    with pytest.raises(ValueError):
        check_within_duration(bad)


# --- what the reports say they did not check -----------------------------------------------


def test_reports_list_what_was_not_checked() -> None:
    for name, validator in VALIDATORS.items():
        document = load(example_files(name)[0])
        report = validator(document)
        held = {i.code for i in report.not_checked}
        assert report.ok
        assert "duration_not_checked" in held, name
        assert "files_not_checked" in held, name
    cue_held = {i.code for i in validate_cues([cue()]).not_checked}
    assert {"h5p_activities_not_checked", "url_allow_list_not_checked"} <= cue_held


def test_error_messages_name_the_file_place_and_next_step() -> None:
    report = validate_chapters([chapter(0, 10), chapter(5, 20)])
    issue = report.errors[0]
    assert "chapters.json[1]" in issue.message
    assert issue.fix_hint
    bad_cue = copy.deepcopy([cue(type="url", ref="http://example.org")])
    schema_issue = validate_cues(bad_cue).errors[0]
    assert schema_issue.message.startswith("cues.json[0].ref")
    assert "cues.v1.schema.json" in schema_issue.fix_hint


# --- nothing is imposed that the guide did not decide -------------------------------------


def test_slides_and_cues_need_no_particular_order() -> None:
    assert validate_slides([slide(t=50, thumb="slides/2.jpg"), slide(t=5)]).ok
    assert validate_cues([cue(t=90), cue(t=3)]).ok
    assert check_within_duration(100, slides=[slide(t=50), slide(t=5)]).ok


def test_chapter_title_may_be_empty() -> None:
    assert validate_chapters([chapter(0, 10, title="")]).ok


def test_lesson_with_no_cues_file_has_no_readable_cues() -> None:
    # The manifest's cues path is optional: a missing file and an empty array are the same.
    assert readable_cues(None) == []
    assert readable_cues([]) == []
    assert check_within_duration(100, cues=()).ok


# --- guide decisions of 2026-11-15 --------------------------------------------------------


def test_duration_is_used_as_given_without_rounding() -> None:
    # 1. duration_s stays unrounded: 742.4 is not treated as 742 or as 743.
    assert check_within_duration(742.5, chapters=[chapter(0, 742.5)]).ok
    assert codes(check_within_duration(742.5, chapters=[chapter(0, 742.6)])) == [
        "time_beyond_duration"
    ]
    assert codes(check_within_duration(742.4, chapters=[chapter(0, 742.5)])) == [
        "time_beyond_duration"
    ]
    assert check_within_duration(742.4, chapters=[chapter(0, 742.4)]).ok


@pytest.mark.parametrize("excess", [1e-9, 0.001, 0.4])
def test_duration_check_has_no_tolerance(excess: float) -> None:
    assert codes(check_within_duration(742, chapters=[chapter(0, 742 + excess)])) == [
        "time_beyond_duration"
    ]
    assert codes(check_within_duration(742, cues=[cue(t=742 + excess)])) == [
        "time_beyond_duration"
    ]


def test_every_chapter_start_and_end_and_cue_t_is_checked_against_duration() -> None:
    report = check_within_duration(
        100,
        chapters=[chapter(0, 50), chapter(150, 160)],
        cues=[cue(t=99.9), cue(t=100.1)],
    )
    assert codes(report) == ["time_beyond_duration"] * 3
    assert [i.location for i in report.errors] == [(1, "start"), (1, "end"), (1, "t")]
    assert "chapters.json[1].start" in report.errors[0].message
    assert "cues.json[1].t" in report.errors[2].message
    assert check_within_duration(
        100, chapters=[chapter(0, 100)], cues=[cue(t=0), cue(t=100)]
    ).ok


def test_times_of_zero_are_accepted() -> None:
    # 2. the minimum is 0, and 0 itself is allowed.
    assert validate_chapters([chapter(0, 0.001)]).ok
    assert validate_slides([slide(t=0)]).ok
    assert validate_slides([slide(t=0.0)]).ok
    assert validate_cues([cue(t=0)]).ok
    assert validate_cues([cue(t=0.0)]).ok


@pytest.mark.parametrize("below", [-0.001, -1, -1e-9])
def test_times_below_zero_are_rejected_by_the_schema(below: float) -> None:
    cases = {
        "chapter start": (CHAPTERS_SCHEMA, [chapter(below, 5)]),
        "chapter end": (CHAPTERS_SCHEMA, [chapter(0, below)]),
        "slide t": (SLIDES_SCHEMA, [slide(t=below)]),
        "cue t": (CUES_SCHEMA, [cue(t=below)]),
    }
    for name, (schema, document) in cases.items():
        found = list(schema.iter_errors(document))
        assert found, name
        assert {e.validator for e in found} == {"minimum"}, name


@pytest.mark.parametrize(
    "token", ["h5p", "image", "url", "quiz-2", "a1", "x-y-z", "2fa", "a"]
)
def test_cue_type_in_the_track_role_slug_form_is_accepted(token: str) -> None:
    # 3. lowercase ASCII letters and digits, single hyphens. A url cue needs an https ref.
    ref = "https://example.org" if token == "url" else "x"
    assert validate_cues([cue(type=token, ref=ref)]).ok


@pytest.mark.parametrize(
    "token",
    [
        "h5p_question",
        "a_b",
        "a.b",
        "h5p.",
        ".h5p",
        "a b",
        " a",
        "a ",
        "a--b",
        "-a",
        "a-",
        "H5p",
        "é",
        "ａ",
    ],
)
def test_cue_type_with_underscore_dot_space_or_other_characters_is_rejected(
    token: str,
) -> None:
    assert validate_cues([cue(type=token, ref="x")]).errors


def test_cue_type_form_agrees_with_the_manifest_track_role_form() -> None:
    # A track role is a "$ref" to the manifest's slug definition.
    track_role = load(MANIFEST_SCHEMA)["$defs"]["track"]["properties"]["role"]
    assert track_role["$ref"] == "#/$defs/slug"
    role = re.compile(load(MANIFEST_SCHEMA)["$defs"]["slug"]["pattern"])
    tokens = [
        "h5p",
        "a-b",
        "a1",
        "2fa",
        "h5p_question",
        "a.b",
        "a b",
        "A",
        "a--b",
        "-a",
        "a-",
        "",
    ]
    for token in tokens:
        assert bool(role.search(token)) == (
            not validate_cues([cue(type=token, ref="x")]).errors
        ), token


def test_slide_thumbnail_needs_a_character_before_the_extension() -> None:
    # 4. at least one character before the lowercase .jpg.
    for thumb in ("slides/.jpg", "slides/a/.jpg", "slides/part-1/.jpg"):
        assert validate_slides([slide(thumb=thumb)]).errors, thumb
    for thumb in ("slides/a.jpg", "slides/1.jpg", "slides/001.jpg", "slides/a/b.jpg"):
        assert validate_slides([slide(thumb=thumb)]).ok, thumb

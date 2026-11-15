"""Tests for slug, relative-path and number validation.

``validate_relative_path`` must implement exactly the B6.3 contract's
``$defs/relative_path`` rule (guide decisions on PR #38 and PR #32). Every
shared vector in ``contracts/test-vectors/relative-path.v1.json`` (PR #32,
which merges first) is run through it, and the library and the schema pattern
are compared on every Unicode code point.

Unicode Cc and Cf characters are rejected from explicit Unicode 15.0.0 range
tables. The tests below check every range at its edges and inside, check that
the tables equal the running Python's Cc and Cf sets, and fail if the running
Python uses another Unicode version, so that an upgrade needs a reviewed
contract decision.

Not enforced in v1, so not tested (guide decision on PR #32): Windows reserved
names, Unicode normalization, and a maximum length.
"""

import json
import re
import unicodedata
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from media_paths.validation import (
    CC_RANGES,
    CF_RANGES,
    UNICODE_VERSION,
    require_int_in_range,
    require_positive_int,
    require_slug,
    validate_relative_path,
    validate_slug,
)


@pytest.mark.parametrize(
    "slug",
    [
        "python",
        "build-ai-assistant",
        "lesson-01",
        "a1-b2",
    ],
)
def test_valid_slugs_are_accepted(slug: str) -> None:
    assert validate_slug(slug) is True


@pytest.mark.parametrize(
    "slug",
    [
        "",
        "Python",
        "python_course",
        "python course",
        "-python",
        "python-",
        "python--course",
        "python/course",
    ],
)
def test_invalid_slugs_are_rejected(slug: str) -> None:
    assert validate_slug(slug) is False


@pytest.mark.parametrize(
    "slug",
    ["../../etc", "..", "python\n", "pythön", "python\\course", "python.course"],
)
def test_traversal_and_non_ascii_slugs_are_rejected(slug: str) -> None:
    assert validate_slug(slug) is False


@pytest.mark.parametrize("value", [None, 1, 1.5, True, b"python", ["python"]])
def test_validate_slug_returns_false_for_non_strings(value: object) -> None:
    # Regression: a non-string used to raise TypeError from re.fullmatch.
    assert validate_slug(value) is False


@pytest.mark.parametrize(
    "path",
    [
        "courses/python/01-basics/01-intro/720p.mp4",
        "poster.jpg",
        "captions.en.vtt",
    ],
)
def test_valid_relative_paths_are_accepted(path: str) -> None:
    assert validate_relative_path(path) is True


@pytest.mark.parametrize(
    "path",
    [
        "",
        "../secret.txt",
        "/absolute/path.mp4",
        "https://example.com/video.mp4",
        "C:\\videos\\lesson.mp4",
        "courses//lesson.mp4",
        "courses/./lesson.mp4",
        "courses/lesson name.mp4",
        "courses\\lesson.mp4",
    ],
)
def test_invalid_relative_paths_are_rejected(path: str) -> None:
    assert validate_relative_path(path) is False


# Every file name listed in PRD B6.2 must stay valid inside a lesson folder.
@pytest.mark.parametrize(
    "path",
    [
        "720p.mp4",
        "360p.mp4",
        "poster.jpg",
        "captions.en.vtt",
        "transcript.en.json",
        "chapters.json",
        "summary.en.md",
        "slides.json",
        "slides/001.jpg",
        "cues.json",
        "camera.mp4",
        "screen.mp4",
        "lesson.json",
        "courses/build-ai-assistant/live-batch-01/01-recap/720p.mp4",
        "courses/python/01-basics/01-intro/slides/012.jpg",
        "...",  # a legal file name, not a traversal segment
        "a..b.mp4",
        "ünïcode/lesson.mp4",
    ],
)
def test_prd_b6_2_and_other_legitimate_paths_are_accepted(path: str) -> None:
    assert validate_relative_path(path) is True


@pytest.mark.parametrize(
    "path",
    [
        "notes/b:c.md",  # a colon after the first segment is not a scheme
        "12:30.mp4",  # a scheme starts with a letter
        "slides/12:30/001.jpg",
        "1a:b.mp4",
        "_x:y.mp4",
        "-a:b.mp4",
    ],
)
def test_colon_that_is_not_a_scheme_or_drive_is_accepted(path: str) -> None:
    # Regression: ":" was rejected anywhere, unlike the B6.3 contract.
    assert validate_relative_path(path) is True


@pytest.mark.parametrize(
    "path",
    [
        "a:b",
        "s3://bucket/720p.mp4",
        "git+ssh:repo/x.mp4",
        "a.b-c:x.mp4",
        "mailto:mentor@example.org",
        "Z:video.mp4",
    ],
)
def test_scheme_or_drive_at_the_start_is_rejected(path: str) -> None:
    assert validate_relative_path(path) is False


@pytest.mark.parametrize(
    "path",
    [
        # traversal, at the start, middle and end
        "../../etc",
        "..",
        ".",
        "module/../secret",
        "module/..",
        "module/./video.mp4",
        # absolute paths and drives
        "/etc/passwd",
        "//server/share/video.mp4",
        "C:/videos/lesson.mp4",
        "c:lesson.mp4",
        # URLs and schemes, with and without "//"
        "https://example.com/video.mp4",
        "http:video.mp4",
        "file:///etc/passwd",
        "javascript:alert(1)",
        "data:text/plain,hello",
        # query strings and fragments
        "module/video.mp4?token=x",
        "module/video.mp4#fragment",
        "module/video.mp4?",
        # alternate separators
        "module\\video.mp4",
        "..\\..\\etc",
        # empty segments
        "module/",
        "module//video.mp4",
        # whitespace (the contract's "no whitespace" rule)
        " ",
        "   ",
        "\t",
        "module/video.mp4\n",
        "module/vi\tdeo.mp4",
        "module/video\r.mp4",
        "module/video\u00a0.mp4",  # no-break space
    ],
)
def test_unsafe_relative_paths_are_rejected(path: str) -> None:
    assert validate_relative_path(path) is False


@pytest.mark.parametrize(
    "path",
    [
        # Cc: C0 controls, DEL, C1 controls
        "module/video\x00.mp4",
        "module/video\x1b.mp4",
        "module/video\x7f.mp4",
        "module/video\x80.mp4",
        "module/video\x9f.mp4",
        # Cf: format characters
        "module/video\u202e4pm.mp4",  # right-to-left override
        "module/video\u061c.mp4",  # Arabic letter mark, also a bidi control
        "module/video\u2066.mp4",  # left-to-right isolate
        "module/video\u200b.mp4",  # zero-width space
        "module/video\u200d.mp4",  # zero-width joiner
        "\ufeffmodule/video.mp4",  # byte order mark (BOM)
        "module/video\u00ad.mp4",  # soft hyphen
        "module/video\u0600.mp4",  # Arabic number sign
        "module/video\u06dd.mp4",  # Arabic end of ayah
        "module/video\U000e0001.mp4",  # language tag, outside the BMP
    ],
)
def test_control_and_format_characters_are_rejected(path: str) -> None:
    # Guide decision on PR #38: Unicode categories Cc and Cf are rejected.
    assert validate_relative_path(path) is False


# --- the Cc and Cf range tables (Unicode 15.0.0) ----------------------------------------

TABLES = {"Cc": CC_RANGES, "Cf": CF_RANGES}
ALL_RANGES = sorted(CC_RANGES + CF_RANGES)


def _forbidden(code_point: int) -> bool:
    return any(start <= code_point <= end for start, end in ALL_RANGES)


def _name(code_point: int) -> str:
    return f"U+{code_point:04X}"


def test_range_tables_are_sorted_non_overlapping_and_not_adjacent() -> None:
    # Adjacent ranges would be one range; overlapping ones would hide a typo.
    for table in TABLES.values():
        assert all(start <= end for start, end in table)
    for (_, end), (next_start, _) in zip(ALL_RANGES, ALL_RANGES[1:]):
        assert end + 1 < next_start


def test_range_tables_hold_the_unicode_15_0_counts() -> None:
    # UCD 15.0.0 DerivedGeneralCategory.txt: "Total code points" is 65 for Cc
    # and 170 for Cf.
    def count(table: tuple[tuple[int, int], ...]) -> int:
        return sum(end - start + 1 for start, end in table)

    assert (count(CC_RANGES), count(CF_RANGES)) == (65, 170)


# First, middle and last code point of every range.
INSIDE = sorted(
    {p for start, end in ALL_RANGES for p in (start, (start + end) // 2, end)}
)


@pytest.mark.parametrize("code_point", INSIDE, ids=_name)
def test_every_range_is_rejected_at_its_edges_and_inside(code_point: int) -> None:
    assert validate_relative_path(f"a{chr(code_point)}.mp4") is False


# The code point just before and just after every range, unless it is itself in a
# range or is whitespace, which the whitespace rule rejects (for example U+0020
# after the C0 controls and U+200A before U+200B).
OUTSIDE = sorted(
    {
        p
        for start, end in ALL_RANGES
        for p in (start - 1, end + 1)
        if p >= 0 and not _forbidden(p) and not chr(p).isspace()
    }
)


@pytest.mark.parametrize("code_point", OUTSIDE, ids=_name)
def test_code_point_next_to_a_range_is_accepted(code_point: int) -> None:
    assert validate_relative_path(f"a{chr(code_point)}.mp4") is True


@pytest.mark.parametrize(
    "path",
    [
        "module/video\ue000.mp4",  # Co: private use
        "module/video\U000f0000.mp4",  # Co: supplementary private use
        "module/video\ud800.mp4",  # Cs: lone high surrogate
        "module/video\udfff.mp4",  # Cs: lone low surrogate
        "module/video\uffff.mp4",  # Cn: a noncharacter, unassigned in every version
        "module/video\u2065.mp4",  # Cn: unassigned, between two Cf ranges
    ],
)
def test_private_use_surrogate_and_unassigned_are_not_rejected_by_category(
    path: str,
) -> None:
    # Guide decision on PR #38: only Cc and Cf are rejected as categories.
    assert validate_relative_path(path) is True


# --- the tables against the running Python's Unicode database ---------------------------


def _unicode_mismatches(version: str, category_of: Callable[[str], str]) -> list[str]:
    """Every difference between the pinned tables and a Unicode database.

    version and category_of stand for unicodedata.unidata_version and
    unicodedata.category, so a test can pass a simulated database.
    """
    problems: list[str] = []
    if version != UNICODE_VERSION:
        problems.append(
            f"this Python uses Unicode {version}, but the relative-path rule is "
            f"pinned to Unicode {UNICODE_VERSION}"
        )
    actual: dict[str, set[int]] = {category: set() for category in TABLES}
    for code_point in range(0x110000):
        category = category_of(chr(code_point))
        if category in actual:
            actual[category].add(code_point)
    for category, table in TABLES.items():
        pinned = {p for start, end in table for p in range(start, end + 1)}
        if missing := sorted(actual[category] - pinned):
            problems.append(
                f"{category} has {', '.join(map(_name, missing))}, the table does not"
            )
        if extra := sorted(pinned - actual[category]):
            problems.append(
                f"the {category} table has {', '.join(map(_name, extra))}, "
                f"{category} does not"
            )
    return problems


def test_tables_match_the_unicode_database_of_the_running_python() -> None:
    problems = _unicode_mismatches(unicodedata.unidata_version, unicodedata.category)
    if problems:
        pytest.fail(
            "The Cc/Cf tables in media_paths/validation.py no longer match this Python's "
            "Unicode database:\n  - "
            + "\n  - ".join(problems)
            + "\nDo not edit the tables to make this pass. Changing them changes the B6.3 "
            "relative-path rule, which needs a reviewed contract decision (PRD B.0) that "
            "updates the library and the B6.3 schema pattern together."
        )


def test_mismatch_check_reports_a_new_unicode_version() -> None:
    problems = _unicode_mismatches("16.0.0", unicodedata.category)
    assert problems == [
        "this Python uses Unicode 16.0.0, but the relative-path rule is pinned to "
        "Unicode 15.0.0"
    ]


def test_mismatch_check_reports_a_character_whose_category_changed() -> None:
    # Simulate a Unicode database where U+061C is no longer Cf and U+0378 (Cn in
    # 15.0) became Cf.
    def drifted(char: str) -> str:
        if char == "\u061c":
            return "Lo"
        if char == "\u0378":
            return "Cf"
        return unicodedata.category(char)

    assert _unicode_mismatches(UNICODE_VERSION, drifted) == [
        "Cf has U+0378, the table does not",
        "the Cf table has U+061C, Cf does not",
    ]


# --- no percent sign anywhere (guide decision on PR #32, 2026-11-15) ---------------------

ENCODED = ["%", "%2e", "%2E", "%2f", "%5C", "%252e", "%25%32%65", "%20", "%41", "100%"]
PLACES = ["{}", "{}/720p.mp4", "a/{}/b.mp4", "a/b{}", "a{}b.mp4", "a/.{}/b.mp4"]


@pytest.mark.parametrize("path", [p.format(e) for e in ENCODED for p in PLACES])
def test_percent_sign_is_rejected_anywhere(path: str) -> None:
    # The 'none' signer appends the path to the base URL, and a layer that
    # decodes it once or more could turn an encoded form into "." or "/".
    # Regression: "%2e%2e/x" used to be accepted.
    assert validate_relative_path(path) is False


def test_encoded_characters_without_a_percent_sign_are_accepted() -> None:
    assert validate_relative_path("2e2f5c/x2E.mp4") is True


# --- the shared B6.3 contract: vectors and schema pattern --------------------------------

ROOT = Path(__file__).resolve().parents[3]
VECTORS: dict[str, Any] = json.loads(
    (ROOT / "contracts/test-vectors/relative-path.v1.json").read_text("utf-8")
)
SCHEMA: dict[str, Any] = json.loads(
    (ROOT / "contracts/lesson-manifest.v1.schema.json").read_text("utf-8")
)
# jsonschema checks "pattern" with Python's re.search, so this is the schema's rule.
SCHEMA_PATTERN = re.compile(SCHEMA["$defs"]["relative_path"]["pattern"])


@pytest.mark.parametrize("vector", VECTORS["valid"], ids=repr)
def test_every_valid_shared_vector_is_accepted(vector: dict[str, Any]) -> None:
    assert validate_relative_path(vector["path"]) is True


@pytest.mark.parametrize("vector", VECTORS["invalid"], ids=repr)
def test_every_invalid_shared_vector_is_rejected(vector: dict[str, Any]) -> None:
    assert validate_relative_path(vector["path"]) is False


def test_library_and_schema_pattern_agree_on_every_code_point() -> None:
    # The guide asked for one Cc/Cf table in both; this compares them directly,
    # whatever the running Python's Unicode version.
    differ = [
        f"U+{p:04X}"
        for p in range(0x110000)
        if validate_relative_path(f"a{chr(p)}.mp4")
        != (SCHEMA_PATTERN.search(f"a{chr(p)}.mp4") is not None)
    ]
    assert differ == []


@pytest.mark.parametrize("value", [None, 1, True, b"poster.jpg", ["poster.jpg"]])
def test_validate_relative_path_returns_false_for_non_strings(value: object) -> None:
    # Regression: a non-string used to raise TypeError instead of returning False.
    assert validate_relative_path(value) is False


def test_require_slug_returns_valid_value() -> None:
    assert require_slug("batch-01", "cohort") == "batch-01"


def test_require_slug_error_names_the_field() -> None:
    with pytest.raises(ValueError, match=r"cohort must be a slug.*'\.\./x'"):
        require_slug("../x", "cohort")


@pytest.mark.parametrize("value", [1, 7, 100])
def test_require_positive_int_returns_valid_value(value: int) -> None:
    assert require_positive_int(value, "n") == value


@pytest.mark.parametrize("value", [True, False, 1.0, "1", None])
def test_require_positive_int_rejects_non_integers(value: object) -> None:
    with pytest.raises(TypeError, match="n must be an integer"):
        require_positive_int(value, "n")


@pytest.mark.parametrize("value", [0, -1])
def test_require_positive_int_rejects_values_below_one(value: int) -> None:
    with pytest.raises(ValueError, match="n must be 1 or greater"):
        require_positive_int(value, "n")


@pytest.mark.parametrize("value", [1, 50, 99])
def test_require_int_in_range_returns_valid_value(value: int) -> None:
    assert require_int_in_range(value, "n", 1, 99) == value


@pytest.mark.parametrize("value", [0, -1, 100])
def test_require_int_in_range_rejects_values_outside_the_range(value: int) -> None:
    with pytest.raises(ValueError, match=f"n must be between 1 and 99, got {value}"):
        require_int_in_range(value, "n", 1, 99)


@pytest.mark.parametrize("value", [True, False, 1.0, "1", None])
def test_require_int_in_range_rejects_non_integers(value: object) -> None:
    with pytest.raises(TypeError, match="n must be an integer"):
        require_int_in_range(value, "n", 1, 99)

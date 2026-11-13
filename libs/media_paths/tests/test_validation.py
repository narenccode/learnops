"""Tests for slug, relative-path and number validation.

``validate_relative_path`` must implement exactly the B6.3 contract's
``$defs/relative_path`` rule (guide decision on PR #38, 2026-11-08). The shared
vectors for that rule, ``contracts/test-vectors/relative-path.v1.json``, arrive
with PR #32, which merges first. The test that reads that file directly is
added to this module after PR #32 is on ``main``; until then it is not claimed.
The cases below are the library's own; they agree with those vectors.

Not claimed yet: that the library and the schema agree on control and format
characters (see ``test_control_and_format_characters_are_rejected``).
"""

import pytest

from media_paths.validation import (
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
        "100%.mp4",
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
        "module/video\x00.mp4",
        "module/video\x1b.mp4",
        "module/video\x7f.mp4",
        "module/video\u202e4pm.mp4",  # right-to-left override
        "module/video\u200b.mp4",  # zero-width space
    ],
)
def test_control_and_format_characters_are_rejected(path: str) -> None:
    # OPEN, waiting for the guide: the PR #38 review asked for this, but the
    # B6.3 pattern in PR #32 accepts these characters, and the guide requires
    # one rule for both. Until that is decided, the library keeps rejecting
    # them, and this is the one known difference from the contract.
    assert validate_relative_path(path) is False


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

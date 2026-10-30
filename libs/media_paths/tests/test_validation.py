import pytest

from libs.media_paths.validation import (
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

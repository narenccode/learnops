import pytest

from libs.media_paths.paths import (
    course_lesson_path,
    live_class_path,
)


def test_course_lesson_path_uses_prd_template() -> None:
    result = course_lesson_path(
        course_slug="build-ai-assistant",
        module_number=1,
        module_slug="setup",
        lesson_number=2,
        lesson_slug="install-python",
    )

    assert result == ("courses/build-ai-assistant/" "01-setup/02-install-python/")


def test_live_class_path_uses_prd_template() -> None:
    result = live_class_path(
        course_slug="build-ai-assistant",
        cohort="batch-01",
        number=1,
        topic_slug="python-introduction",
    )

    assert result == (
        "courses/build-ai-assistant/" "live-batch-01/01-python-introduction/"
    )


@pytest.mark.parametrize(
    ("number", "expected"),
    [
        (1, "01"),
        (2, "02"),
        (9, "09"),
        (10, "10"),
        (25, "25"),
    ],
)
def test_path_numbers_are_zero_padded(
    number: int,
    expected: str,
) -> None:
    result = course_lesson_path(
        course_slug="python-course",
        module_number=number,
        module_slug="basics",
        lesson_number=number,
        lesson_slug="introduction",
    )

    assert f"/{expected}-basics/{expected}-introduction/" in result

from string import Formatter

import pytest

from media_paths.paths import (
    COURSE_LESSON_PLACEHOLDERS,
    COURSE_LESSON_TEMPLATE,
    LIVE_CLASS_PLACEHOLDERS,
    LIVE_CLASS_TEMPLATE,
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


# --- B6.1 placeholder contract -------------------------------------------------


def _fields(template: str) -> set[str]:
    return {field for _, field, _, _ in Formatter().parse(template) if field}


def test_default_templates_match_prd_b6_1() -> None:
    assert COURSE_LESSON_TEMPLATE == (
        "courses/{course_slug}/{module_nn}-{module_slug}/{lesson_nn}-{lesson_slug}/"
    )
    assert LIVE_CLASS_TEMPLATE == (
        "courses/{course_slug}/live-{cohort}/{nn}-{topic_slug}/"
    )


def test_default_templates_use_exactly_the_documented_placeholders() -> None:
    assert _fields(COURSE_LESSON_TEMPLATE) == COURSE_LESSON_PLACEHOLDERS
    assert _fields(LIVE_CLASS_TEMPLATE) == LIVE_CLASS_PLACEHOLDERS


def test_course_lesson_custom_template_with_documented_placeholders() -> None:
    # Regression: the documented {module_nn} and {lesson_nn} raised KeyError.
    result = course_lesson_path(
        course_slug="build-ai-assistant",
        module_number=3,
        module_slug="setup",
        lesson_number=7,
        lesson_slug="install-python",
        template="media/{course_slug}/m{module_nn}/{lesson_nn}-{lesson_slug}/",
    )

    assert result == "media/build-ai-assistant/m03/07-install-python/"


def test_live_class_custom_template_with_documented_placeholders() -> None:
    # Regression: the documented {nn} raised KeyError.
    result = live_class_path(
        course_slug="build-ai-assistant",
        cohort="batch-01",
        number=4,
        topic_slug="recap",
        template="live/{cohort}/{course_slug}/{nn}-{topic_slug}/",
    )

    assert result == "live/batch-01/build-ai-assistant/04-recap/"


@pytest.mark.parametrize(
    ("placeholder", "expected"),
    [
        ("course_slug", "build-ai-assistant"),
        ("module_nn", "03"),
        ("module_slug", "setup"),
        ("lesson_nn", "07"),
        ("lesson_slug", "install-python"),
    ],
)
def test_each_course_lesson_placeholder_is_supported(
    placeholder: str, expected: str
) -> None:
    result = course_lesson_path(
        course_slug="build-ai-assistant",
        module_number=3,
        module_slug="setup",
        lesson_number=7,
        lesson_slug="install-python",
        template="x/{" + placeholder + "}/",
    )

    assert result == f"x/{expected}/"


@pytest.mark.parametrize(
    ("placeholder", "expected"),
    [
        ("course_slug", "build-ai-assistant"),
        ("cohort", "batch-01"),
        ("nn", "04"),
        ("topic_slug", "recap"),
    ],
)
def test_each_live_class_placeholder_is_supported(
    placeholder: str, expected: str
) -> None:
    result = live_class_path(
        course_slug="build-ai-assistant",
        cohort="batch-01",
        number=4,
        topic_slug="recap",
        template="x/{" + placeholder + "}/",
    )

    assert result == f"x/{expected}/"


@pytest.mark.parametrize(
    "template",
    [
        "courses/{module_number}/",  # old internal name, never documented
        "courses/{course}/",
        "courses/{nn}/",  # live-class placeholder in a lesson template
        "courses/{}/",
        "courses/{0}/",
        "courses/{course_slug.upper}/",
        "courses/{course_slug[0]}/",
    ],
)
def test_unknown_placeholder_is_rejected_with_clear_error(template: str) -> None:
    with pytest.raises(ValueError, match="unsupported placeholder"):
        course_lesson_path("python", 1, "basics", 1, "intro", template=template)


def test_lesson_placeholder_in_live_class_template_is_rejected() -> None:
    with pytest.raises(ValueError, match=r"unsupported placeholder \{module_nn\}"):
        live_class_path("python", "batch-01", 1, "recap", template="{module_nn}/")


@pytest.mark.parametrize(
    "template",
    ["courses/{course_slug", "courses/course_slug}/", "courses/{/"],
)
def test_malformed_template_is_rejected(template: str) -> None:
    with pytest.raises(ValueError, match="template is malformed"):
        course_lesson_path("python", 1, "basics", 1, "intro", template=template)


@pytest.mark.parametrize(
    "template", ["courses/{module_nn:>4}/", "courses/{course_slug!r}/"]
)
def test_format_spec_or_conversion_is_rejected(template: str) -> None:
    with pytest.raises(ValueError, match="format spec or conversion"):
        course_lesson_path("python", 1, "basics", 1, "intro", template=template)


def test_escaped_literal_braces_are_allowed() -> None:
    result = course_lesson_path(
        "python", 1, "basics", 1, "intro", template="a{{b}}/{course_slug}/"
    )

    assert result == "a{b}/python/"


@pytest.mark.parametrize(
    "template",
    [
        "/srv/{course_slug}/",
        "../{course_slug}/",
        "courses/../{course_slug}/",
        "https://cdn.example.com/{course_slug}/",
        "courses//{course_slug}/",
    ],
)
def test_template_producing_unsafe_path_is_rejected(template: str) -> None:
    with pytest.raises(ValueError, match="safe relative media path"):
        course_lesson_path("python", 1, "basics", 1, "intro", template=template)


def test_non_string_template_is_rejected() -> None:
    with pytest.raises(TypeError, match="template must be a string"):
        course_lesson_path(
            "python",
            1,
            "basics",
            1,
            "intro",
            template=None,  # type: ignore[arg-type]
        )


# --- Slug, cohort and number validation ----------------------------------------

LESSON_ARGS: dict[str, object] = {
    "course_slug": "python",
    "module_number": 1,
    "module_slug": "basics",
    "lesson_number": 1,
    "lesson_slug": "intro",
}
LIVE_ARGS: dict[str, object] = {
    "course_slug": "python",
    "cohort": "batch-01",
    "number": 1,
    "topic_slug": "recap",
}
BAD_SLUGS = [
    "",
    "../../etc",
    "..",
    "/etc",
    "a/b",
    "a\\b",
    "C:",
    "Python",
    "my_course",
    "a--b",
    "-a",
    "a-",
    "a b",
    "intro\n",
]


@pytest.mark.parametrize("field", ["course_slug", "module_slug", "lesson_slug"])
@pytest.mark.parametrize("bad", BAD_SLUGS)
def test_course_lesson_rejects_invalid_slugs(field: str, bad: str) -> None:
    with pytest.raises(ValueError, match=f"{field} must be a slug"):
        course_lesson_path(**{**LESSON_ARGS, field: bad})  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["course_slug", "cohort", "topic_slug"])
@pytest.mark.parametrize("bad", BAD_SLUGS)
def test_live_class_rejects_invalid_slugs_and_cohorts(field: str, bad: str) -> None:
    with pytest.raises(ValueError, match=f"{field} must be a slug"):
        live_class_path(**{**LIVE_ARGS, field: bad})  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [None, 1, b"python"])
def test_non_string_slug_is_rejected(bad: object) -> None:
    with pytest.raises(TypeError, match="course_slug must be a string"):
        course_lesson_path(**{**LESSON_ARGS, "course_slug": bad})  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["module_number", "lesson_number"])
@pytest.mark.parametrize("bad", [True, False, 1.0, 2.5, "1", None])
def test_course_lesson_rejects_non_integer_numbers(field: str, bad: object) -> None:
    with pytest.raises(TypeError, match=f"{field} must be an integer"):
        course_lesson_path(**{**LESSON_ARGS, field: bad})  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["module_number", "lesson_number"])
@pytest.mark.parametrize("bad", [0, -1, -10])
def test_course_lesson_rejects_numbers_below_one(field: str, bad: int) -> None:
    with pytest.raises(ValueError, match=f"{field} must be 1 or greater"):
        course_lesson_path(**{**LESSON_ARGS, field: bad})  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [True, 1.0, "1", None])
def test_live_class_rejects_non_integer_number(bad: object) -> None:
    with pytest.raises(TypeError, match="number must be an integer"):
        live_class_path(**{**LIVE_ARGS, "number": bad})  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [0, -1])
def test_live_class_rejects_number_below_one(bad: int) -> None:
    with pytest.raises(ValueError, match="number must be 1 or greater"):
        live_class_path(**{**LIVE_ARGS, "number": bad})  # type: ignore[arg-type]


def test_numbers_above_99_are_not_truncated() -> None:
    # PRD B6.1 sets no upper limit; two digits is a minimum width, not a cap.
    result = live_class_path("python", "batch-01", 100, "recap")

    assert result == "courses/python/live-batch-01/100-recap/"

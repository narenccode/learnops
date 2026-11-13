from string import Formatter

import pytest

import media_paths.paths as paths_module
from media_paths.paths import (
    COURSE_LESSON_PLACEHOLDERS,
    COURSE_LESSON_REQUIRED_PLACEHOLDERS,
    COURSE_LESSON_TEMPLATE,
    DEFAULT_COURSE_LESSON_TEMPLATE,
    DEFAULT_LIVE_CLASS_TEMPLATE,
    LIVE_CLASS_PLACEHOLDERS,
    LIVE_CLASS_REQUIRED_PLACEHOLDERS,
    LIVE_CLASS_TEMPLATE,
    CourseLessonTemplate,
    LiveClassTemplate,
    check_course_lesson_template,
    check_live_class_template,
    course_lesson_path,
    live_class_path,
)

# Required placeholders in a lesson / live-class template, for tests that add
# one more placeholder or literal text around them.
LESSON_IDS = "{course_slug}/{module_slug}/{lesson_slug}/"
LIVE_IDS = "{course_slug}/{cohort}/{topic_slug}/"


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
        (99, "99"),
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


def test_default_templates_are_loaded_checked_templates() -> None:
    assert DEFAULT_COURSE_LESSON_TEMPLATE == CourseLessonTemplate(
        COURSE_LESSON_TEMPLATE
    )
    assert DEFAULT_LIVE_CLASS_TEMPLATE == LiveClassTemplate(LIVE_CLASS_TEMPLATE)


def test_required_placeholders_are_the_guide_decision() -> None:
    assert COURSE_LESSON_REQUIRED_PLACEHOLDERS == {
        "course_slug",
        "module_slug",
        "lesson_slug",
    }
    assert LIVE_CLASS_REQUIRED_PLACEHOLDERS == {"course_slug", "cohort", "topic_slug"}


def test_course_lesson_custom_template_with_documented_placeholders() -> None:
    # Regression: the documented {module_nn} and {lesson_nn} raised KeyError.
    template = check_course_lesson_template(
        "media/{course_slug}/m{module_nn}-{module_slug}/{lesson_nn}-{lesson_slug}/"
    )

    result = course_lesson_path(
        course_slug="build-ai-assistant",
        module_number=3,
        module_slug="setup",
        lesson_number=7,
        lesson_slug="install-python",
        template=template,
    )

    assert result == "media/build-ai-assistant/m03-setup/07-install-python/"


def test_live_class_custom_template_with_documented_placeholders() -> None:
    # Regression: the documented {nn} raised KeyError.
    template = check_live_class_template(
        "live/{cohort}/{course_slug}/{nn}-{topic_slug}/"
    )

    result = live_class_path(
        course_slug="build-ai-assistant",
        cohort="batch-01",
        number=4,
        topic_slug="recap",
        template=template,
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
    template = check_course_lesson_template("x/{" + placeholder + "}/" + LESSON_IDS)

    result = course_lesson_path(
        course_slug="build-ai-assistant",
        module_number=3,
        module_slug="setup",
        lesson_number=7,
        lesson_slug="install-python",
        template=template,
    )

    assert result == f"x/{expected}/build-ai-assistant/setup/install-python/"


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
    template = check_live_class_template("x/{" + placeholder + "}/" + LIVE_IDS)

    result = live_class_path(
        course_slug="build-ai-assistant",
        cohort="batch-01",
        number=4,
        topic_slug="recap",
        template=template,
    )

    assert result == f"x/{expected}/build-ai-assistant/batch-01/recap/"


# --- Required placeholders (guide decision, PR #38) ---------------------------


@pytest.mark.parametrize("missing", sorted(COURSE_LESSON_REQUIRED_PLACEHOLDERS))
def test_course_lesson_template_without_identifying_placeholder_is_rejected(
    missing: str,
) -> None:
    template = COURSE_LESSON_TEMPLATE.replace("{" + missing + "}", "x")

    with pytest.raises(
        ValueError, match=r"missing required placeholder\(s\) \{" + missing + r"\}"
    ):
        check_course_lesson_template(template)


@pytest.mark.parametrize("missing", sorted(LIVE_CLASS_REQUIRED_PLACEHOLDERS))
def test_live_class_template_without_identifying_placeholder_is_rejected(
    missing: str,
) -> None:
    template = LIVE_CLASS_TEMPLATE.replace("{" + missing + "}", "x")

    with pytest.raises(
        ValueError, match=r"missing required placeholder\(s\) \{" + missing + r"\}"
    ):
        check_live_class_template(template)


def test_missing_placeholder_error_names_every_missing_one() -> None:
    with pytest.raises(
        ValueError, match=r"\{lesson_slug\}, \{module_slug\}.*share one folder"
    ):
        check_course_lesson_template("courses/{course_slug}/")


def test_number_placeholders_are_optional() -> None:
    lesson = check_course_lesson_template(LESSON_IDS)
    live = check_live_class_template(LIVE_IDS)

    assert course_lesson_path("python", 1, "basics", 2, "intro", template=lesson) == (
        "python/basics/intro/"
    )
    assert live_class_path("python", "batch-01", 3, "recap", template=live) == (
        "python/batch-01/recap/"
    )


def test_lessons_differing_only_by_lesson_slug_get_different_folders() -> None:
    # The reason for the rule: with {lesson_slug} required, two lessons in the
    # same module can never resolve to the same storage folder.
    template = check_course_lesson_template(LESSON_IDS)

    first = course_lesson_path("python", 1, "basics", 1, "intro", template=template)
    second = course_lesson_path("python", 1, "basics", 1, "loops", template=template)

    assert first != second


# --- Checked once when loaded, not at each call --------------------------------


def test_template_is_checked_once_when_loaded_not_at_each_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []
    real_check = paths_module._check_template

    def counting_check(*args: object, **kwargs: object) -> str:
        calls.append(args[0])
        return real_check(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(paths_module, "_check_template", counting_check)

    template = check_course_lesson_template(COURSE_LESSON_TEMPLATE)
    for lesson_number in range(1, 6):
        course_lesson_path("python", 1, "basics", lesson_number, "intro", template)

    assert calls == [COURSE_LESSON_TEMPLATE]


def test_checked_template_cannot_be_created_unchecked() -> None:
    # The template classes check themselves, so no unchecked one can exist.
    with pytest.raises(ValueError, match="missing required placeholder"):
        CourseLessonTemplate("courses/{course_slug}/")
    with pytest.raises(ValueError, match="missing required placeholder"):
        LiveClassTemplate("courses/{course_slug}/")


@pytest.mark.parametrize("raw", [COURSE_LESSON_TEMPLATE, None])
def test_course_lesson_path_rejects_an_unloaded_template(raw: object) -> None:
    with pytest.raises(TypeError, match="check_course_lesson_template"):
        course_lesson_path("python", 1, "basics", 1, "intro", template=raw)  # type: ignore[arg-type]


@pytest.mark.parametrize("raw", [LIVE_CLASS_TEMPLATE, None])
def test_live_class_path_rejects_an_unloaded_template(raw: object) -> None:
    with pytest.raises(TypeError, match="check_live_class_template"):
        live_class_path("python", "batch-01", 1, "recap", template=raw)  # type: ignore[arg-type]


def test_lesson_template_is_not_accepted_for_live_class() -> None:
    with pytest.raises(TypeError, match="LiveClassTemplate"):
        live_class_path(
            "python",
            "batch-01",
            1,
            "recap",
            template=DEFAULT_COURSE_LESSON_TEMPLATE,  # type: ignore[arg-type]
        )


# --- Template rejection (at load) ---------------------------------------------


@pytest.mark.parametrize(
    "template",
    [
        "courses/{module_number}/" + LESSON_IDS,  # old internal name, never documented
        "courses/{course}/" + LESSON_IDS,
        "courses/{nn}/" + LESSON_IDS,  # live-class placeholder in a lesson template
        "courses/{}/" + LESSON_IDS,
        "courses/{0}/" + LESSON_IDS,
        "courses/{course_slug.upper}/" + LESSON_IDS,
        "courses/{course_slug[0]}/" + LESSON_IDS,
    ],
)
def test_unknown_placeholder_is_rejected_with_clear_error(template: str) -> None:
    with pytest.raises(ValueError, match="unsupported placeholder"):
        check_course_lesson_template(template)


def test_lesson_placeholder_in_live_class_template_is_rejected() -> None:
    with pytest.raises(ValueError, match=r"unsupported placeholder \{module_nn\}"):
        check_live_class_template("{module_nn}/" + LIVE_IDS)


@pytest.mark.parametrize(
    "template",
    ["courses/{course_slug", "courses/course_slug}/", "courses/{/"],
)
def test_malformed_template_is_rejected(template: str) -> None:
    with pytest.raises(ValueError, match="template is malformed"):
        check_course_lesson_template(template + LESSON_IDS)


@pytest.mark.parametrize(
    "template", ["courses/{module_nn:>4}/", "courses/{course_slug!r}/"]
)
def test_format_spec_or_conversion_is_rejected(template: str) -> None:
    with pytest.raises(ValueError, match="format spec or conversion"):
        check_course_lesson_template(template + LESSON_IDS)


def test_escaped_literal_braces_are_allowed() -> None:
    template = check_course_lesson_template("a{{b}}/" + LESSON_IDS)

    result = course_lesson_path("python", 1, "basics", 1, "intro", template=template)

    assert result == "a{b}/python/basics/intro/"


@pytest.mark.parametrize(
    "template",
    [
        "/srv/" + LESSON_IDS,
        "../" + LESSON_IDS,
        "courses/../" + LESSON_IDS,
        "https://cdn.example.com/" + LESSON_IDS,
        "courses//" + LESSON_IDS,
        "C:/media/" + LESSON_IDS,
        # A placeholder value starting with a letter becomes a scheme ("a:x").
        "{course_slug}:x/{module_slug}/{lesson_slug}/",
        "courses/?/" + LESSON_IDS,
    ],
)
def test_template_producing_unsafe_path_is_rejected_at_load(template: str) -> None:
    with pytest.raises(ValueError, match="safe relative media path"):
        check_course_lesson_template(template)


def test_unsafe_live_class_template_is_rejected_at_load() -> None:
    with pytest.raises(ValueError, match="safe relative media path"):
        check_live_class_template("/srv/" + LIVE_IDS)


@pytest.mark.parametrize("bad", [None, 1, b"courses/"])
def test_non_string_template_is_rejected(bad: object) -> None:
    with pytest.raises(TypeError, match="template must be a string"):
        check_course_lesson_template(bad)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="template must be a string"):
        check_live_class_template(bad)  # type: ignore[arg-type]


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


def test_cohort_in_slug_form_such_as_a_date_is_accepted() -> None:
    # Guide decision on PR #38: cohort uses the slug rule, which allows 2026-01.
    result = live_class_path("python", "2026-01", 1, "recap")

    assert result == "courses/python/live-2026-01/01-recap/"


@pytest.mark.parametrize("bad", [None, 1, b"python"])
def test_non_string_slug_is_rejected(bad: object) -> None:
    with pytest.raises(TypeError, match="course_slug must be a string"):
        course_lesson_path(**{**LESSON_ARGS, "course_slug": bad})  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["module_number", "lesson_number"])
@pytest.mark.parametrize("bad", [True, False, 1.0, 2.5, "1", "01", None, [1]])
def test_course_lesson_rejects_non_integer_numbers(field: str, bad: object) -> None:
    with pytest.raises(TypeError, match=f"{field} must be an integer"):
        course_lesson_path(**{**LESSON_ARGS, field: bad})  # type: ignore[arg-type]


# Guide decision on PR #38: numbers start at 1 and stop at 99.
OUT_OF_RANGE_NUMBERS = [0, -1, -10, 100, 101, 1000]


@pytest.mark.parametrize("field", ["module_number", "lesson_number"])
@pytest.mark.parametrize("bad", OUT_OF_RANGE_NUMBERS)
def test_course_lesson_rejects_numbers_outside_1_to_99(field: str, bad: int) -> None:
    with pytest.raises(
        ValueError, match=f"{field} must be between 1 and 99, got {bad}"
    ):
        course_lesson_path(**{**LESSON_ARGS, field: bad})  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["module_number", "lesson_number"])
@pytest.mark.parametrize("edge", [1, 99])
def test_course_lesson_accepts_numbers_1_and_99(field: str, edge: int) -> None:
    result = course_lesson_path(**{**LESSON_ARGS, field: edge})  # type: ignore[arg-type]

    assert f"{edge:02d}-" in result


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None])
def test_live_class_rejects_non_integer_number(bad: object) -> None:
    with pytest.raises(TypeError, match="number must be an integer"):
        live_class_path(**{**LIVE_ARGS, "number": bad})  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", OUT_OF_RANGE_NUMBERS)
def test_live_class_rejects_number_outside_1_to_99(bad: int) -> None:
    with pytest.raises(ValueError, match=f"number must be between 1 and 99, got {bad}"):
        live_class_path(**{**LIVE_ARGS, "number": bad})  # type: ignore[arg-type]


def test_live_class_accepts_number_99() -> None:
    assert live_class_path("python", "batch-01", 99, "recap") == (
        "courses/python/live-batch-01/99-recap/"
    )

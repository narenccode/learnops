from string import Formatter

from media_paths.validation import (
    require_positive_int,
    require_slug,
    validate_relative_path,
)

# Default templates and placeholder names are PRD B6.1, unchanged. The same
# names are used in MEDIA_PATH_TEMPLATE in .env.example.
COURSE_LESSON_TEMPLATE = (
    "courses/{course_slug}/{module_nn}-{module_slug}/{lesson_nn}-{lesson_slug}/"
)
LIVE_CLASS_TEMPLATE = "courses/{course_slug}/live-{cohort}/{nn}-{topic_slug}/"

COURSE_LESSON_PLACEHOLDERS = frozenset(
    {"course_slug", "module_nn", "module_slug", "lesson_nn", "lesson_slug"}
)
LIVE_CLASS_PLACEHOLDERS = frozenset({"course_slug", "cohort", "nn", "topic_slug"})


def _two_digits(number: int) -> str:
    # PRD B6.1: "Numbers zero-padded to two digits". No upper limit is defined,
    # so 100 and above render with three or more digits.
    return f"{number:02d}"


def _check_template(template: object, allowed: frozenset[str]) -> str:
    """Reject templates that str.format would fail on or misinterpret."""
    if not isinstance(template, str):
        raise TypeError(f"template must be a string, got {type(template).__name__}")

    allowed_list = ", ".join(f"{{{name}}}" for name in sorted(allowed))
    try:
        fields = list(Formatter().parse(template))
    except ValueError as error:
        raise ValueError(
            f"template is malformed ({error}). Use only {allowed_list}; "
            "write a literal brace as '{{' or '}}'."
        ) from None

    for _literal, field, spec, conversion in fields:
        if field is None:
            continue
        if field not in allowed:
            raise ValueError(
                f"template uses unsupported placeholder {{{field}}}. "
                f"Supported placeholders: {allowed_list}."
            )
        if spec or conversion:
            raise ValueError(
                f"template placeholder {{{field}}} must not have a format "
                "spec or conversion; numbers are already zero-padded."
            )
    return template


def _render(template: str, allowed: frozenset[str], values: dict[str, str]) -> str:
    path = _check_template(template, allowed).format(**values)
    # A custom template could still produce an absolute or traversing path
    # (e.g. "/srv/{course_slug}/" or "../{course_slug}/"); the trailing "/"
    # marks a folder and is not a segment.
    if not validate_relative_path(path.removesuffix("/")):
        raise ValueError(
            "template does not produce a safe relative media path (PRD C-08): "
            f"{path!r}"
        )
    return path


def course_lesson_path(
    course_slug: str,
    module_number: int,
    module_slug: str,
    lesson_number: int,
    lesson_slug: str,
    template: str = COURSE_LESSON_TEMPLATE,
) -> str:
    """Return the relative folder for a course lesson (PRD B6.1)."""
    values = {
        "course_slug": require_slug(course_slug, "course_slug"),
        "module_nn": _two_digits(require_positive_int(module_number, "module_number")),
        "module_slug": require_slug(module_slug, "module_slug"),
        "lesson_nn": _two_digits(require_positive_int(lesson_number, "lesson_number")),
        "lesson_slug": require_slug(lesson_slug, "lesson_slug"),
    }
    return _render(template, COURSE_LESSON_PLACEHOLDERS, values)


def live_class_path(
    course_slug: str,
    cohort: str,
    number: int,
    topic_slug: str,
    template: str = LIVE_CLASS_TEMPLATE,
) -> str:
    """Return the relative folder for a live-class recording (PRD B6.1)."""
    values = {
        "course_slug": require_slug(course_slug, "course_slug"),
        "cohort": require_slug(cohort, "cohort"),
        "nn": _two_digits(require_positive_int(number, "number")),
        "topic_slug": require_slug(topic_slug, "topic_slug"),
    }
    return _render(template, LIVE_CLASS_PLACEHOLDERS, values)

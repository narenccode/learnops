from dataclasses import dataclass
from string import Formatter

from media_paths.validation import (
    require_int_in_range,
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

# Guide decision on PR #38 (2026-11-08): the placeholders that identify the
# item are required, so two lessons can never share one folder and overwrite
# each other. The number placeholders stay optional.
COURSE_LESSON_REQUIRED_PLACEHOLDERS = frozenset(
    {"course_slug", "module_slug", "lesson_slug"}
)
LIVE_CLASS_REQUIRED_PLACEHOLDERS = frozenset({"course_slug", "cohort", "topic_slug"})

# Guide decision on PR #38: B6.1 pads numbers to two digits, so 1-99 only.
MIN_PATH_NUMBER = 1
MAX_PATH_NUMBER = 99

# Values used to try a template out when it is loaded. A slug value starting
# with a letter is the worst case for the scheme check ("{course_slug}:x"
# reads as "a:x"), and real values contain only [a-z0-9-] or two digits, so a
# template that renders safely here renders safely for every valid input.
_SAMPLE_VALUES = {
    "course_slug": "a",
    "module_nn": "01",
    "module_slug": "a",
    "lesson_nn": "01",
    "lesson_slug": "a",
    "cohort": "a",
    "nn": "01",
    "topic_slug": "a",
}


def _check_template(
    template: object, allowed: frozenset[str], required: frozenset[str]
) -> str:
    """Reject templates that str.format would fail on, misinterpret, or that
    could make two items share a folder or leave the media root."""
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

    used: set[str] = set()
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
        used.add(field)

    missing = sorted(required - used)
    if missing:
        missing_list = ", ".join(f"{{{name}}}" for name in missing)
        raise ValueError(
            f"template is missing required placeholder(s) {missing_list}. "
            "Without them two items could share one folder and overwrite each "
            "other's files."
        )

    sample = template.format(**{name: _SAMPLE_VALUES[name] for name in allowed})
    # The trailing "/" marks a folder and is not a segment.
    if not validate_relative_path(sample.removesuffix("/")):
        raise ValueError(
            "template does not produce a safe relative media path (PRD C-08), "
            f"for example {sample!r}. Remove any leading '/', '..', '//', URL "
            "scheme or drive letter."
        )
    return template


@dataclass(frozen=True)
class CourseLessonTemplate:
    """A course-lesson path template, checked once when it is created."""

    text: str

    def __post_init__(self) -> None:
        _check_template(
            self.text, COURSE_LESSON_PLACEHOLDERS, COURSE_LESSON_REQUIRED_PLACEHOLDERS
        )


@dataclass(frozen=True)
class LiveClassTemplate:
    """A live-class path template, checked once when it is created."""

    text: str

    def __post_init__(self) -> None:
        _check_template(
            self.text, LIVE_CLASS_PLACEHOLDERS, LIVE_CLASS_REQUIRED_PLACEHOLDERS
        )


def check_course_lesson_template(template: str) -> CourseLessonTemplate:
    """Load a course-lesson template (e.g. MEDIA_PATH_TEMPLATE) once.

    Raises ``TypeError`` or ``ValueError`` naming the problem.
    """
    return CourseLessonTemplate(template)


def check_live_class_template(template: str) -> LiveClassTemplate:
    """Load a live-class template once. Raises ``TypeError`` or ``ValueError``."""
    return LiveClassTemplate(template)


DEFAULT_COURSE_LESSON_TEMPLATE = CourseLessonTemplate(COURSE_LESSON_TEMPLATE)
DEFAULT_LIVE_CLASS_TEMPLATE = LiveClassTemplate(LIVE_CLASS_TEMPLATE)


def _two_digits(value: object, name: str) -> str:
    number = require_int_in_range(value, name, MIN_PATH_NUMBER, MAX_PATH_NUMBER)
    return f"{number:02d}"


def course_lesson_path(
    course_slug: str,
    module_number: int,
    module_slug: str,
    lesson_number: int,
    lesson_slug: str,
    template: CourseLessonTemplate = DEFAULT_COURSE_LESSON_TEMPLATE,
) -> str:
    """Return the relative folder for a course lesson (PRD B6.1)."""
    if not isinstance(template, CourseLessonTemplate):
        raise TypeError(
            "template must be a CourseLessonTemplate; load the text once with "
            "check_course_lesson_template(text) and pass the result"
        )
    values = {
        "course_slug": require_slug(course_slug, "course_slug"),
        "module_nn": _two_digits(module_number, "module_number"),
        "module_slug": require_slug(module_slug, "module_slug"),
        "lesson_nn": _two_digits(lesson_number, "lesson_number"),
        "lesson_slug": require_slug(lesson_slug, "lesson_slug"),
    }
    # No path check here: the template was checked when it was loaded, and
    # valid values cannot make a safe template unsafe (see _SAMPLE_VALUES).
    return template.text.format(**values)


def live_class_path(
    course_slug: str,
    cohort: str,
    number: int,
    topic_slug: str,
    template: LiveClassTemplate = DEFAULT_LIVE_CLASS_TEMPLATE,
) -> str:
    """Return the relative folder for a live-class recording (PRD B6.1)."""
    if not isinstance(template, LiveClassTemplate):
        raise TypeError(
            "template must be a LiveClassTemplate; load the text once with "
            "check_live_class_template(text) and pass the result"
        )
    values = {
        "course_slug": require_slug(course_slug, "course_slug"),
        "cohort": require_slug(cohort, "cohort"),
        "nn": _two_digits(number, "number"),
        "topic_slug": require_slug(topic_slug, "topic_slug"),
    }
    return template.text.format(**values)

COURSE_LESSON_TEMPLATE = (
    "courses/{course_slug}/"
    "{module_number:02d}-{module_slug}/"
    "{lesson_number:02d}-{lesson_slug}/"
)

LIVE_CLASS_TEMPLATE = (
    "courses/{course_slug}/" "live-{cohort}/" "{number:02d}-{topic_slug}/"
)


def course_lesson_path(
    course_slug: str,
    module_number: int,
    module_slug: str,
    lesson_number: int,
    lesson_slug: str,
    template: str = COURSE_LESSON_TEMPLATE,
) -> str:
    return template.format(
        course_slug=course_slug,
        module_number=module_number,
        module_slug=module_slug,
        lesson_number=lesson_number,
        lesson_slug=lesson_slug,
    )


def live_class_path(
    course_slug: str,
    cohort: str,
    number: int,
    topic_slug: str,
    template: str = LIVE_CLASS_TEMPLATE,
) -> str:
    return template.format(
        course_slug=course_slug,
        cohort=cohort,
        number=number,
        topic_slug=topic_slug,
    )

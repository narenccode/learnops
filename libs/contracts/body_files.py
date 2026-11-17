"""Every `body` named in course.yaml must be a file inside the package (PRD B1.1).

Only the existence of the file is checked. Its content (the marking table, B1.3) is not read.
"""

from __future__ import annotations

from . import messages
from .course_rules import Doc
from .report import Issue
from .source import FileState, PackageSource

# For each file state that is a problem: the issue code, the message and the fix hint.
_PROBLEMS = {
    FileState.MISSING: (
        "body_file_missing",
        messages.BODY_FILE_MISSING,
        messages.BODY_FILE_MISSING_HINT,
    ),
    FileState.NOT_A_FILE: (
        "body_not_a_file",
        messages.BODY_NOT_A_FILE,
        messages.BODY_NOT_A_FILE_HINT,
    ),
    FileState.OUTSIDE_PACKAGE: (
        "body_outside_package",
        messages.BODY_OUTSIDE_PACKAGE,
        messages.BODY_OUTSIDE_PACKAGE_HINT,
    ),
}


def check_body_files(doc: Doc, source: PackageSource) -> list[Issue]:
    """One issue for each `body` that does not name a file inside the package, in document
    order. A file may be shared by two activities: the PRD does not forbid it."""
    issues: list[Issue] = []
    for s_index, section in enumerate(doc["sections"]):
        for a_index, activity in enumerate(section["activities"]):
            body = activity.get("body")
            state = FileState.OK if body is None else source.file_state(body)
            if state is FileState.OK:
                continue
            code, message, hint = _PROBLEMS[state]
            place = ("sections", s_index, "activities", a_index, "body")
            issues.append(
                Issue(
                    code=code,
                    rule="B1.1",
                    message=message.format(where=messages.where(place), path=body),
                    fix_hint=hint,
                    location=place,
                    idnumber=activity["idnumber"],
                )
            )
    return issues

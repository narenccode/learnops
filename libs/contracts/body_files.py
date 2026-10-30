"""Every `body` named in course.yaml must be a file inside the package (PRD B1.1)."""

from __future__ import annotations

from . import messages
from .course_rules import Doc, iter_items
from .report import Issue
from .source import FileState, PackageSource

RULE = "B1.1"

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
    issues: list[Issue] = []
    for item in iter_items(doc):
        body = item.node.get("body")
        if body is None:
            continue
        state = source.file_state(body)
        if state is FileState.OK:
            continue
        code, message, hint = _PROBLEMS[state]
        place = item.location + ("body",)
        issues.append(
            Issue(
                code=code,
                rule=RULE,
                message=message.format(where=messages.where(place), path=body),
                fix_hint=hint,
                location=place,
                idnumber=item.idnumber,
            )
        )
    return issues

"""Course-level rules on a parsed course.yaml whose structure the schema has already accepted.

Implemented here: idnumbers unique within the one package being checked (PRD B1.2 rule 6, first
half), protected idnumbers a site adds to the two defaults (B1.4), and the unlock dependency of
each section, which depends on the package mode (B1.2 rule 2, guide-confirmed). NOT here: that an idnumber
is never reused for a different activity across package versions (B1.2 rule 6, second half). That
needs the previous version of the package and has no assigned owner yet. Every other course-level
rule is also still listed in `messages.HELD_RULES`.
"""

from __future__ import annotations

from collections.abc import Collection, Iterator
from dataclasses import dataclass
from typing import Any

from . import messages
from .report import Issue, Location

Doc = dict[str, Any]


@dataclass(frozen=True)
class Item:
    """A section that has an idnumber, or an activity: where its idnumber is, and the idnumber."""

    location: Location
    idnumber: str


def iter_items(doc: Doc) -> Iterator[Item]:
    """Sections and their activities in document order, each section before its activities.

    A section idnumber is optional (PRD B1.1): Moodle stores none, and a section is matched by its
    number. A section without one is skipped, never yielded with an empty or missing idnumber, so
    two sections without one are not duplicates of each other. Activities always have one.
    """
    for s_index, section in enumerate(doc["sections"]):
        if "idnumber" in section:
            yield Item(("sections", s_index, "idnumber"), section["idnumber"])
        for a_index, activity in enumerate(section["activities"]):
            yield Item(
                ("sections", s_index, "activities", a_index, "idnumber"),
                activity["idnumber"],
            )


def check_unique_idnumbers(doc: Doc) -> list[Issue]:
    """B1.2 rule 6, first half: idnumbers are unique within this package.

    Sections and activities share one namespace. The first use in document order is accepted
    and every later use is the error, so the fix is clear. Reuse across package versions is not
    checked here (see the module docstring).
    """
    first_use: dict[str, Location] = {}
    issues: list[Issue] = []
    for item in iter_items(doc):
        if item.idnumber not in first_use:
            first_use[item.idnumber] = item.location
            continue
        issues.append(
            Issue(
                code="duplicate_idnumber",
                rule="B1.2 rule 6",
                message=messages.DUPLICATE_IDNUMBER.format(
                    where=messages.where(item.location),
                    idnumber=item.idnumber,
                    first=messages.where(first_use[item.idnumber]),
                ),
                fix_hint=messages.DUPLICATE_IDNUMBER_HINT,
                location=item.location,
                idnumber=item.idnumber,
            )
        )
    return issues


def check_extra_protected_idnumbers(
    doc: Doc, protected: Collection[str]
) -> list[Issue]:
    """B1.4: idnumbers a site configures as protected, in either mode.

    The two defaults are rejected by the schema and are not repeated here.
    """
    return [
        Issue(
            code="protected_idnumber",
            rule="B1.4",
            message=messages.PROTECTED_IDNUMBER.format(
                where=messages.where(item.location), idnumber=item.idnumber
            ),
            fix_hint=messages.PROTECTED_IDNUMBER_HINT,
            location=item.location,
            idnumber=item.idnumber,
        )
        for item in iter_items(doc)
        if item.idnumber in protected
    ]


def check_unlock_rules(doc: Doc) -> list[Issue]:
    """B1.2 rule 2, by mode (guide-confirmed). Only the shape of `unlock` is judged here.

    "Previous" is document order: the number of a section is not read. `start_date` is optional
    and never replaces `after`. An absent `unlock` counts as `after: null`, `start_date: null`.

    full: the first section must have `after` null (nothing earlier exists to name). Every later
    section must have `after` naming the one assignment of the section just before it, and that
    section must hold exactly one assignment, or it is reported.

    sections-only: every listed section, a single one included, must have `after`. It may name
    an activity of the template course that this package does not contain; whether it resolves
    in the merged course is the checker's CK-04, and a loop is CK-05. It must not name an
    activity of its own section or of a later one in this package: that is not an earlier
    activity. CK-05 still covers cycles across sections after the merge. The idnumber's shape is
    already checked by the schema.
    """
    sections_only = doc["course"]["mode"] == "sections-only"
    sections = doc["sections"]
    section_of = _section_of_each_activity(sections)
    issues: list[Issue] = []
    for index, section in enumerate(sections):
        after = (section.get("unlock") or {}).get("after")
        location: Location = ("sections", index, "unlock", "after")
        if sections_only:
            if after is None:
                issues.append(_after_missing(location, sections_only))
            elif section_of.get(after, -1) >= index:
                issues.append(_after_forward_reference(location, after))
        elif index == 0:
            if after is not None:
                issues.append(_after_on_first_section(location, after))
        else:
            tasks = _tasks(sections[index - 1])
            if len(tasks) != 1:
                issues.append(_task_count(index - 1, len(tasks)))
            if after is None:
                issues.append(_after_missing(location, sections_only))
            elif len(tasks) == 1 and after != tasks[0]:
                issues.append(_after_not_previous_task(location, after, index))
    return issues


def _tasks(section: Doc) -> list[str]:
    # B1 names only: the schema allows `assignment`, never Moodle's `assign`.
    return [a["idnumber"] for a in section["activities"] if a["type"] == "assignment"]


def _section_of_each_activity(sections: list[Doc]) -> dict[str, int]:
    found: dict[str, int] = {}
    for index, section in enumerate(sections):
        for activity in section["activities"]:
            found.setdefault(activity["idnumber"], index)
    return found


def _after_on_first_section(location: Location, after: str) -> Issue:
    return Issue(
        code="unlock_after_on_first_section",
        rule="B1.2 rule 2",
        message=messages.UNLOCK_AFTER_ON_FIRST_SECTION.format(
            where=messages.where(location), idnumber=after
        ),
        fix_hint=messages.UNLOCK_AFTER_ON_FIRST_SECTION_HINT,
        location=location,
        idnumber=after,
    )


def _after_forward_reference(location: Location, after: str) -> Issue:
    return Issue(
        code="unlock_after_forward_reference",
        rule="B1.2 rule 2",
        message=messages.UNLOCK_AFTER_FORWARD_REFERENCE.format(
            where=messages.where(location), idnumber=after
        ),
        fix_hint=messages.UNLOCK_AFTER_FORWARD_REFERENCE_HINT,
        location=location,
        idnumber=after,
    )


def _task_count(section_index: int, count: int) -> Issue:
    location: Location = ("sections", section_index, "activities")
    return Issue(
        code="unlock_previous_task_count",
        rule="B1.2 rule 2",
        message=messages.UNLOCK_PREVIOUS_TASK_COUNT.format(
            where=messages.where(location), count=count
        ),
        fix_hint=messages.UNLOCK_PREVIOUS_TASK_COUNT_HINT,
        location=location,
    )


def _after_missing(location: Location, sections_only: bool) -> Issue:
    if sections_only:
        message = messages.UNLOCK_AFTER_MISSING_SECTIONS_ONLY
        hint = messages.UNLOCK_AFTER_MISSING_SECTIONS_ONLY_HINT
    else:
        message = messages.UNLOCK_AFTER_MISSING_FULL
        hint = messages.UNLOCK_AFTER_MISSING_FULL_HINT
    return Issue(
        code="unlock_after_missing",
        rule="B1.2 rule 2",
        message=message.format(where=messages.where(location)),
        fix_hint=hint,
        location=location,
    )


def _after_not_previous_task(location: Location, after: str, index: int) -> Issue:
    return Issue(
        code="unlock_after_not_previous_task",
        rule="B1.2 rule 2",
        message=messages.UNLOCK_AFTER_NOT_PREVIOUS_TASK.format(
            where=messages.where(location),
            idnumber=after,
            previous=messages.where(("sections", index - 1)),
        ),
        fix_hint=messages.UNLOCK_AFTER_NOT_PREVIOUS_TASK_HINT,
        location=location,
        idnumber=after,
    )

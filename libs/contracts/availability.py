"""Reading the Moodle availability JSON that the course model (B2) keeps whole.

The inner form belongs to Moodle and is deliberately not described by a schema here (decision
0003, guide-confirmed). So this module only finds conditions by their `type`, never by their
position in a list, and ignores anything it does not understand. The meaning of `cm = -1` is the
guide's: the nearest earlier activity in course order with manual or automatic completion
tracking. That is documented but still provisional until it is verified on Moodle 4.5 and 5.3.

It does not report anything. Reporting an unresolved `-1` as CK-04 is the checker's job.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

Doc = dict[str, Any]

PREVIOUS_ACTIVITY = -1
"""Moodle's OPTION_PREVIOUS marker. It is not a real course-module id."""

TRACKED = frozenset({"manual", "automatic"})


def conditions_of_type(availability: object, kind: str) -> list[Doc]:
    """Every condition whose `type` is `kind`, at any depth, in the order they are written.

    The order is only the order of the input: callers must not rely on it. Nested groups (a
    condition list inside a condition) are searched too, because Moodle allows them.
    """
    return list(_walk(availability, kind))


def _walk(node: object, kind: str) -> Iterator[Doc]:
    if not isinstance(node, dict):
        return
    if node.get("type") == kind:
        yield node
    children = node.get("c")
    if isinstance(children, list):
        for child in children:
            yield from _walk(child, kind)


def resolve_previous_cmid(
    model: Doc, section_index: int, activity_index: int | None = None
) -> int | None:
    """The `cmid` that `cm = -1` stands for, or None when the condition cannot be met.

    `section_index` and `activity_index` are positions in the model's `sections` and
    `activities` lists, which are in course order (section order, then activity order). For an
    activity, "earlier" means before it. A section's availability has the same semantics (guide
    decision 13) and is read from just before its first activity, so only activities of earlier
    sections count. Activities whose tracking is `none` are skipped.

    Raises ValueError when `section_index` is not a section of the model, or `activity_index`
    is not an activity of that section (negative, or past the end). An index outside the model
    must never resolve to some unrelated activity.
    """
    _check_holder(model, section_index, activity_index)
    holder = (section_index, -1 if activity_index is None else activity_index)
    found: int | None = None
    for s_index, section in enumerate(model["sections"]):
        for a_index, activity in enumerate(section["activities"]):
            if (s_index, a_index) >= holder:
                return found
            if activity["completion"]["tracking"] in TRACKED:
                found = activity["cmid"]
    return found


def _check_holder(model: Doc, section_index: int, activity_index: int | None) -> None:
    sections = model["sections"]
    if not 0 <= section_index < len(sections):
        raise ValueError(
            f"section_index {section_index} is outside the model, which has "
            f"{len(sections)} section(s)."
        )
    count = len(sections[section_index]["activities"])
    if activity_index is not None and not 0 <= activity_index < count:
        raise ValueError(
            f"activity_index {activity_index} is outside section {section_index}, "
            f"which has {count} activity(ies)."
        )

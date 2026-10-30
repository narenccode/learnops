"""Course-level rules on a parsed course.yaml whose structure the schema has already accepted.

Implemented: unique idnumbers (B1.2 rule 6), extra protected idnumbers (B1.4) and the points
total (B1.2 rule 3). Weekly structure, the unlock chain, the marking table and protected_section
are NOT here: their ownership or details are not decided yet (see messages.HELD_RULES).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from . import messages
from .report import Issue, Location
from .schema import default_total_points

Doc = dict[str, Any]


@dataclass(frozen=True)
class Item:
    """A section or an activity: where it is, and its idnumber."""

    location: Location
    idnumber: str
    node: Doc


def iter_items(doc: Doc) -> Iterator[Item]:
    """Sections and their activities in document order, each section before its activities."""
    for s_index, section in enumerate(doc["sections"]):
        yield Item(("sections", s_index), section["idnumber"], section)
        for a_index, activity in enumerate(section["activities"]):
            location = ("sections", s_index, "activities", a_index)
            yield Item(location, activity["idnumber"], activity)


def check_unique_idnumbers(doc: Doc) -> list[Issue]:
    """B1.2 rule 6: sections and activities share one namespace of idnumbers."""
    first_use: dict[str, Location] = {}
    issues: list[Issue] = []
    for item in iter_items(doc):
        place = item.location + ("idnumber",)
        if item.idnumber not in first_use:
            first_use[item.idnumber] = place
            continue
        issues.append(
            Issue(
                code="duplicate_idnumber",
                rule="B1.2 rule 6",
                message=messages.DUPLICATE_IDNUMBER.format(
                    where=messages.where(place),
                    idnumber=item.idnumber,
                    first=messages.where(first_use[item.idnumber]),
                ),
                fix_hint=messages.DUPLICATE_IDNUMBER_HINT,
                location=place,
                idnumber=item.idnumber,
            )
        )
    return issues


def check_extra_protected_idnumbers(doc: Doc, protected: frozenset[str]) -> list[Issue]:
    """B1.4: idnumbers a site configures as protected, in either mode. The two defaults are
    rejected by the schema and are not repeated here."""
    issues: list[Issue] = []
    for item in iter_items(doc):
        if item.idnumber not in protected:
            continue
        place = item.location + ("idnumber",)
        issues.append(
            Issue(
                code="protected_idnumber",
                rule="B1.4",
                message=messages.PROTECTED_IDNUMBER.format(
                    where=messages.where(place), idnumber=item.idnumber
                ),
                fix_hint=messages.PROTECTED_IDNUMBER_HINT,
                location=place,
                idnumber=item.idnumber,
            )
        )
    return issues


def check_points_total(doc: Doc) -> list[Issue]:
    """B1.2 rule 3, narrow reading: the points of the assignments add up to total_points.

    Whether other things count as graded points, and how this applies to a sections-only
    package, are open questions; callers decide whether to call this (see validate.py).
    """
    expected = int(doc["course"].get("total_points", default_total_points()))
    actual = sum(
        int(item.node["points"])
        for item in iter_items(doc)
        if item.node.get("type") == "assignment"
    )
    if actual == expected:
        return []
    return [
        Issue(
            code="points_total_mismatch",
            rule="B1.2 rule 3",
            message=messages.POINTS_TOTAL_MISMATCH.format(
                actual=actual, expected=expected
            ),
            fix_hint=messages.POINTS_TOTAL_MISMATCH_HINT,
            location=("course", "total_points"),
        )
    ]

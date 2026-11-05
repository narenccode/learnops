"""Course-level rules on a parsed course.yaml whose structure the schema has already accepted.

Implemented here: idnumbers unique within the one package being checked (PRD B1.2 rule 6, first
half) and protected idnumbers a site adds to the two defaults (B1.4). NOT here: that an idnumber
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
    """A section or an activity: where its idnumber is, and the idnumber."""

    location: Location
    idnumber: str


def iter_items(doc: Doc) -> Iterator[Item]:
    """Sections and their activities in document order, each section before its activities."""
    for s_index, section in enumerate(doc["sections"]):
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

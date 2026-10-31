"""All user-facing text of this library, in one place (root CLAUDE.md §6, PRD UI-05).

Each message says what happened and each hint says what to do next.
"""

from __future__ import annotations

from .report import Location

DOCUMENT_NAME = "course.yaml"


def where(location: Location) -> str:
    """A readable place in course.yaml, e.g. `sections[1].activities[0].idnumber`."""
    if not location:
        return DOCUMENT_NAME
    text = ""
    for part in location:
        if isinstance(part, int):
            text += f"[{part}]"
        else:
            text += f".{part}" if text else part
    return text


# --- schema (B1.1) --------------------------------------------------------------------------

SCHEMA_ERROR = "{where}: {detail}"
SCHEMA_HINT = (
    "Change this value in course.yaml so that it matches the course package schema "
    "(contracts/course-package.v1.schema.json)."
)
PROTECTED_DEFAULT = (
    "{where}: '{value}' is a protected idnumber and cannot be used in a package."
)
PROTECTED_DEFAULT_HINT = (
    "Remove this item or give it another idnumber. Protected items belong to the template "
    "course and are never generated (PRD B1.4)."
)

# --- rules that did not run -----------------------------------------------------------------

NOT_CHECKED_HINT = "Check this by hand until the validator supports it."

# Rules that are not implemented yet. Each is (code, PRD rule, what is not checked). They are
# listed in every report so that "no errors" is not read as "fully checked".
HELD_RULES: tuple[tuple[str, str, str], ...] = (
    (
        "week_structure_not_checked",
        "B1.2 rule 1",
        "Not checked: exactly one guide Page and one task Assignment in each week.",
    ),
    (
        "unlock_chain_not_checked",
        "B1.2 rule 2",
        "Not checked: week N unlocks when the task of week N-1 is submitted.",
    ),
    (
        "marking_table_not_checked",
        "B1.3",
        "Not checked: the marking table in each assignment body (format and points).",
    ),
    (
        "check_vocabulary_not_checked",
        "B1.3",
        "Not checked: the allowed values of the marking table's Check column.",
    ),
    (
        "protected_section_not_checked",
        "B1.4",
        "Not checked: that no section uses the protected section number.",
    ),
)

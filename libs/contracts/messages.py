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


# --- reading course.yaml --------------------------------------------------------------------

COURSE_YAML_MISSING = "The package has no course.yaml."
COURSE_YAML_MISSING_HINT = (
    "Put course.yaml at the top of the package folder (PRD B1.1), then validate again."
)
COURSE_YAML_UNREADABLE = "course.yaml could not be read: {reason}."
COURSE_YAML_UNREADABLE_HINT = (
    "Save course.yaml as UTF-8 and fix the YAML syntax at the place named above."
)

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

# --- idnumbers (B1.2 rule 6, B1.4) ----------------------------------------------------------

DUPLICATE_IDNUMBER = (
    "{where}: the idnumber '{idnumber}' is already used at {first}. "
    "Idnumbers must be unique in the course."
)
DUPLICATE_IDNUMBER_HINT = (
    "Give this section or activity its own idnumber. Idnumbers are unique across the whole "
    "course, sections and activities together."
)
PROTECTED_IDNUMBER = (
    "{where}: '{idnumber}' is a protected idnumber and cannot be used in a package."
)
PROTECTED_IDNUMBER_HINT = (
    "Remove this item or give it another idnumber. Protected items belong to the template "
    "course and are never generated (PRD B1.4)."
)

# --- points (B1.2 rule 3) -------------------------------------------------------------------

POINTS_TOTAL_MISMATCH = (
    "The assignments add up to {actual} points, but total_points is {expected}."
)
POINTS_TOTAL_MISMATCH_HINT = (
    "Change the points of the assignments so that they add up to total_points, or change "
    "total_points."
)

# --- body files (B1.1) ----------------------------------------------------------------------

BODY_FILE_MISSING = "{where}: the file '{path}' does not exist in the package."
BODY_FILE_MISSING_HINT = (
    "Add the file at that path, or change 'body' to a file that exists in the package."
)
BODY_NOT_A_FILE = "{where}: '{path}' is a folder, not a file."
BODY_NOT_A_FILE_HINT = "Point 'body' at a Markdown file, not at a folder."
BODY_OUTSIDE_PACKAGE = "{where}: '{path}' leads outside the package folder."
BODY_OUTSIDE_PACKAGE_HINT = (
    "Move the file into the package folder and point 'body' at it. Links that leave the "
    "folder are not allowed."
)

# --- rules that did not run -----------------------------------------------------------------

NOT_CHECKED_HINT = "Check this by hand until the validator supports it."

CROSS_RULES_NOT_CHECKED = "The course-level rules did not run because the structure of course.yaml is invalid."
CROSS_RULES_NOT_CHECKED_HINT = "Fix the structure errors first; the course-level rules run once the structure is valid."
POINTS_NOT_CHECKED_SECTIONS_ONLY = (
    "The points total was not checked: this is a sections-only package, and how the total "
    "applies to it has not been decided."
)

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

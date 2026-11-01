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
PROTECTED_IDNUMBER_HINT = PROTECTED_DEFAULT_HINT

# --- reading a package folder (B1.1) -------------------------------------------------------

COURSE_YAML_MISSING = "The package has no course.yaml."
COURSE_YAML_MISSING_HINT = (
    "Put course.yaml at the top of the package folder (PRD B1.1), then validate again."
)
COURSE_YAML_UNREADABLE = "course.yaml could not be read: {reason}."
COURSE_YAML_UNREADABLE_HINT = (
    "Save course.yaml as UTF-8 and fix the YAML syntax at the place named above."
)
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

# --- settings -------------------------------------------------------------------------------

CONFIG_BAD_PROTECTED_IDNUMBER = (
    "Protected idnumber {value!r} is not a valid idnumber. Use lowercase ASCII letters and "
    "digits separated by single hyphens, for example 'capstone-gate'."
)
CONFIG_PROTECTED_NOT_A_LIST = (
    "protected_idnumbers must be a collection of idnumbers, for example "
    "frozenset({{'capstone-gate'}}), not {found}. Split a comma-separated setting into "
    "separate idnumbers before passing it."
)
CONFIG_WRONG_TYPE = (
    "config must be a ValidationConfig instance, not {found}. "
    "Pass a ValidationConfig instance, e.g. ValidationConfig(...)."
)
CONFIG_PROTECTED_NOT_TEXT = (
    "Protected idnumber {value!r} is not text. Pass each idnumber as a string, for example "
    "'capstone-gate'."
)

# --- rules that did not run -----------------------------------------------------------------

NOT_CHECKED_HINT = "Check this by hand until the validator supports it."

# Reported when the structure is invalid: the course-level rules need a sound structure. The
# text names no rule, so that it stays true as more course-level rules are implemented.
CROSS_RULES_NOT_CHECKED = (
    "The course-level rules did not run because course.yaml could not be checked."
)
CROSS_RULES_NOT_CHECKED_HINT = (
    "Fix the errors listed above. The course-level rules run once course.yaml is valid."
)
# Same code as the held rule below, for a package whose body check did not run.
BODY_FILES_NOT_CHECKED_YET = (
    "Not checked: that the file named by each body exists. This check runs once "
    "course.yaml is valid."
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
        "points_total_not_checked",
        "B1.2 rule 3",
        "Not checked: graded points across the course sum to total_points.",
    ),
    (
        "unlock_completion_not_checked",
        "B1.2 rule 5",
        "Not checked: completion tracking is on for every activity used in an unlock rule.",
    ),
    (
        "idnumber_reuse_not_checked",
        "B1.2 rule 6",
        (
            "Not checked: that an idnumber is never reused for a different activity. This "
            "needs the previous version of the package, which one course.yaml cannot supply. "
            "Uniqueness within this package is checked."
        ),
    ),
    (
        "body_files_not_checked",
        "B1.1",
        "Not checked: that the file named by each body exists. This needs the package folder, which a parsed course.yaml does not carry. validate_package checks it.",
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

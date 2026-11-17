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

# --- contract examples (example_check.py, validate_examples.py; PRD B.0 rule 1, E1) --------

EX_PLACE_DOCUMENT = "(document)"
EX_SCHEMA_VIOLATION = "{where}: {detail} [{keyword}]"
EX_SCHEMA_VIOLATION_HINT = (
    "Change the example so that it matches the schema. If the schema is wrong instead, change "
    "it only through /contract-change (PRD B.0)."
)
EX_NO_SCHEMAS = "No *.schema.json file was found in {folder}."
EX_NO_SCHEMAS_HINT = (
    "Check that --contracts-dir points at the repository's contracts folder."
)
EX_CONTRACTS_DIR_MISSING = "The contracts folder {folder} does not exist."
EX_CONTRACTS_DIR_MISSING_HINT = "Run the script from a repository checkout, or pass --contracts-dir with an existing folder."
EX_UNREADABLE_SCHEMA = "The schema could not be read: {reason}."
EX_UNREADABLE_SCHEMA_HINT = "Save the schema as UTF-8 JSON and fix the syntax error."
EX_INVALID_SCHEMA = "The file is not a valid JSON Schema: {reason}."
EX_INVALID_SCHEMA_HINT = "Fix the schema so that it passes its meta-schema."
EX_UNRESOLVABLE_REFERENCE = (
    "The schema has a reference that cannot be resolved: {reason}."
)
EX_UNRESOLVABLE_REFERENCE_HINT = (
    "Fix the $ref so that it points at a definition inside this schema (for example "
    "'#/$defs/name'). References to other files are not loaded by this validator."
)
EX_SCHEMA_KEYWORD_NOT_TEXT = (
    "the `$schema` keyword must be a string (a meta-schema URI)"
)
EX_NESTED_TOO_DEEP = "it is nested too deeply"
EX_TOO_DEEP_TO_VALIDATE = (
    "it is nested too deeply for the schema to check, or the schema's references loop"
)
EX_NOT_VALIDATED = "Not validated, because its schema could not be loaded."
EX_NOT_VALIDATED_HINT = "Fix the schema problem reported above, then validate again."
EX_MISNAMED_SCHEMA = (
    "The schema file '{name}' is not named <name>.v<N>.schema.json, so its examples cannot be "
    "found."
)
EX_MISNAMED_SCHEMA_HINT = (
    "Rename it to <name>.v<N>.schema.json: lowercase letters and digits separated by single "
    "hyphens, then .v and a version number without a leading zero (for example "
    "course-package.v1.schema.json)."
)
EX_MISSING_EXAMPLE = (
    "The schema has no example in the folder {folder} or in a file named "
    "{stem}.<suffix>.json, .yaml or .yml."
)
EX_MISSING_EXAMPLE_HINT = (
    "Add at least one valid .json, .yaml or .yml example at the top of that folder, or a file "
    "named <schema name>.<suffix>.json, .yaml or .yml in contracts/examples (PRD B.0 rule 1)."
)
EX_UNREADABLE_EXAMPLE = "The example could not be read: {reason}."
EX_UNREADABLE_EXAMPLE_HINT = (
    "Fix the problem described above: save the example as UTF-8 and use JSON or YAML syntax "
    "(the reason gives a line and column when the parser reports one)."
)
EX_LINE_WITH_SCHEMA = "FAIL {target} (schema {schema}): {message}"
EX_LINE = "FAIL {target}: {message}"
EX_LINE_HINT = "     next: {hint}"
EX_LINE_OK = "OK {example} (schema {schema})"
# "found", not "checked": it includes examples whose schema could not be loaded (not validated).
EX_SUMMARY = (
    "{examples} examples found, {schemas} schemas: {passed} passed, {failed} failed, "
    "{not_validated} not validated; {problems} problems found."
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
    (
        "h5p_files_not_checked",
        "B7",
        "Not checked: that the .h5p file named by each h5p activity exists or is valid, or which content type it holds. Interactive video (lab demonstrations only) is therefore not checked either.",
    ),
)


# --- B6.2 lesson files: chapters.json, slides.json, cues.json -------------------------------


def lesson_file_where(filename: str, location: Location) -> str:
    """A readable place in a lesson file, e.g. `chapters.json[2].end`."""
    text = filename
    for part in location:
        text += f"[{part}]" if isinstance(part, int) else f".{part}"
    return text


LESSON_FILE_SCHEMA_ERROR = "{where}: {detail}"
LESSON_FILE_SCHEMA_HINT = (
    "Change this value so that {filename} matches contracts/{schema}. "
    "It must be a JSON array, as PRD B6.2 describes."
)

TIME_NOT_FINITE = "{where}: {value} is not a finite number of seconds."
TIME_NOT_FINITE_HINT = "Use a number of seconds such as 95.5 (PRD B6.2)."

CHAPTER_END_NOT_AFTER_START = (
    "{where}: the chapter ends at {end} s, which is not after its start at {start} s."
)
CHAPTER_END_NOT_AFTER_START_HINT = "Make end greater than start."
CHAPTER_NOT_IN_ORDER = (
    "{where}: this chapter starts at {start} s, before the previous chapter starts at "
    "{previous} s."
)
CHAPTER_NOT_IN_ORDER_HINT = "List the chapters in ascending order of start."
CHAPTER_OVERLAP = (
    "{where}: this chapter starts at {start} s, before an earlier chapter ends at "
    "{previous_end} s."
)
CHAPTER_OVERLAP_HINT = (
    "Start the chapter at or after the end of every earlier chapter. A gap between chapters is "
    "allowed."
)

TIME_BEYOND_DURATION = (
    "{where}: {value} s is after the end of the lesson at {duration} s (duration_s in "
    "lesson.json)."
)
TIME_BEYOND_DURATION_HINT = (
    "Use a time that is not after duration_s, or correct duration_s in lesson.json."
)

# What a lesson-file report does not check, so that "no errors" is not read as "fully checked".
# Each is (code, PRD rule, text).
LESSON_FILE_HELD_DURATION: tuple[str, str, str] = (
    "duration_not_checked",
    "B6.2",
    "Not checked: that every time is within duration_s. That value is in lesson.json, "
    "another file. check_within_duration does it.",
)
LESSON_FILE_HELD_FILES: tuple[str, str, str] = (
    "files_not_checked",
    "B6.2",
    "Not checked: that the files named here exist in the lesson folder.",
)
LESSON_FILE_HELD_H5P: tuple[str, str, str] = (
    "h5p_activities_not_checked",
    "B6.2, B7",
    "Not checked: that an h5p ref is the idnumber of an activity in the course.",
)
LESSON_FILE_HELD_URL: tuple[str, str, str] = (
    "url_allow_list_not_checked",
    "B6.2, FR-X-12",
    "Not checked: that a url is allowed by the player's configuration. The player checks it.",
)

LESSON_FILE_SEE_SCHEMA = "The rule is in contracts/{schema}."

# A `pattern` that fails in a lesson file: (message, hint). Each says what the value must be.
PATH_NOT_RELATIVE = (
    "{where}: '{value}' is not a path relative to the lesson folder.",
    "Use a path such as images/diagram.png: forward slashes, no leading slash, no '.' or '..' "
    "part, no empty part, no space, no ?, #, % or backslash, and no URL scheme such as https:.",
)
THUMB_NOT_IN_SLIDES = (
    "{where}: '{value}' is not a thumbnail path: it must start with slides/ and end in .jpg, "
    "with at least one character before the lowercase extension.",
    "Use a path such as slides/001.jpg, relative to the lesson folder.",
)
URL_NOT_HTTPS = (
    "{where}: '{value}' is not an https address with a host.",
    "Use an address such as https://example.org/page: the https scheme, a host, an optional "
    "numeric port, no user name or password, no @ before the path and no backslash.",
)
H5P_REF_NOT_IDNUMBER = (
    "{where}: '{value}' is not an activity idnumber.",
    "Use the idnumber of the H5P activity in course.yaml: lowercase letters and digits "
    "separated by single hyphens, for example wk-01-quiz (PRD B1.2).",
)
TEXT_IS_BLANK = (
    "{where}: the text is blank.",
    "Write at least one character that is not a space.",
)

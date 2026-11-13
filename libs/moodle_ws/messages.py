"""User-facing messages of the Moodle client (PRD UI-05: what happened, then what to do next).

No message here may contain a token, a full URL or request parameters (PRD SEC-03, OPS-04): only
names LearnOps itself defines, such as setting names and file names. A value a caller supplied is
never repeated: a token made of letters and digits cannot be told apart from a plain name, so no
filter could make that safe.
"""

from __future__ import annotations

from typing import Final

FUNCTION_NOT_ALLOWED: Final = (
    "That function is not in the B4 allow-list, so it was not sent to Moodle. Use a "
    "listed function, or add this one to B4 through /contract-change."
)
WORKFLOW_STATE_REQUIRED: Final = (
    "{function} must send the workflow state '{state}', so nothing was sent to Moodle. Set "
    "workflowstate to '{state}'."
)
RELEASE_REFUSED: Final = (
    "{function} tried to send the state '{state}', so nothing was sent to Moodle. LearnOps never "
    "releases grades; a mentor releases them in Moodle."
)
WRITE_NEEDS_HELPER: Final = (
    "A grade write is sent only through write_draft_grade(), which checks the maximum grade, the "
    "learner's state and marking workflow and reads the result back, so nothing was sent to "
    "Moodle. Call write_draft_grade() instead."
)
ATTEMPT_REQUIRED: Final = (
    "mod_assign_save_grade needs the explicit attempt being graded (a whole number from 0, never "
    "-1), so nothing was sent to Moodle. Pass the attempt number you graded."
)
GRADE_NOT_A_NUMBER: Final = (
    "The grade is not a plain number of 0 or more, so nothing was sent to Moodle. Pass the "
    "approved grade as a number, for example 84.5."
)
MISSING_SETTING: Final = (
    "{variable} is not set. Set it in the environment before contacting Moodle."
)
PLACEHOLDER_SETTING: Final = "{variable} still has the placeholder from .env.example. Set the real value in the environment."
UNKNOWN_SITE: Final = "That is not a Moodle site. Use one of: {allowed}."
ALLOW_LIST_UNREADABLE: Final = (
    "The B4 allow-list file {file} could not be read. Restore it from the repository."
)
ALLOW_LIST_INVALID: Final = "The B4 allow-list file {file} does not match its schema. Fix the file before contacting Moodle."
ALLOW_LIST_DUPLICATE: Final = (
    "The B4 allow-list file {file} lists '{function}' twice. Remove the duplicate."
)
VERSION_NOT_SUPPORTED: Final = (
    "That is not a version B4 supports, so nothing was sent. Use Moodle 4.5 or 5.3."
)
TOKEN_NOT_PICKLABLE: Final = (
    "A Token cannot be pickled. Read it from the environment instead."
)
TOKEN_REJECTED: Final = (
    "Moodle site '{site}' rejected the service token. Ask your administrator."
)
PERMISSION_REFUSED: Final = "The service account cannot do this on Moodle site '{site}'. Ask your administrator."
SITE_CANNOT_DO_THIS: Final = (
    "Moodle site '{site}' does not support this. Grade this in Moodle instead."
)
INVALID_PARAMETERS: Final = (
    "The parameters could not be accepted, so nothing was sent to Moodle. Use a mapping of plain "
    "text, numbers, lists and mappings, at most 32 levels deep."
)
INVALID_SITE_SETTING: Final = (
    "The site setting '{field}' is not valid. Use load_site(), or correct that setting."
)
CLIENT_NEEDS_SETTINGS: Final = "MoodleClient needs site settings, not a site name. Use create_client() or load_site()."
CLIENT_NEEDS_TRANSPORT: Final = (
    "MoodleClient needs a transport with a call method. Pass one in tests."
)
CLIENT_NEEDS_ALLOW_LIST: Final = (
    "MoodleClient needs an AllowList. Leave it out to use the B4 contract."
)
LOG_NOT_CLEANED: Final = (
    "A log entry could not be cleaned, so it was removed. Check the calling code."
)
NOT_INTEGRATED: Final = (
    "No real Moodle transport exists yet: it waits for the lab checks in contracts/moodle-ws.v1.md "
    "§5. Pass a transport in tests."
)
UNREACHABLE: Final = "Moodle site '{site}' did not answer. Try again in a few minutes."
UNEXPECTED: Final = "Moodle site '{site}' gave an answer that could not be understood. Ask your administrator."

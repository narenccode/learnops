"""Shared Moodle web-services client (PRD B4). Release 0 skeleton; no real transport yet.

    from moodle_ws import create_client
    client = create_client("moodle45", transport)
    client.call("mod_assign_get_assignments", params)

Every web-services call in LearnOps goes through MoodleClient. See README.md in this folder.
"""

from . import messages
from .allowlist import AllowList, load_allowlist
from .client import MoodleClient, create_client
from .config import Site, SiteSettings, load_site
from .errors import (
    FunctionNotAllowed,
    GradeWriteNotAllowed,
    InvalidParameters,
    MoodleConfigError,
    MoodleError,
    MoodleUnreachable,
    NotSupported,
    PermissionDenied,
    TokenInvalid,
    UnexpectedResponse,
    WorkflowStateNotAllowed,
)
from .grade_write import (
    Outcome,
    WriteResult,
    grading_status,
    result_for,
    stored_grade_matches,
    write_draft_grade,
)
from .grades import grade_in_range, parse_grade
from .redact import RedactingFilter, redact, safe_url, sanitize, sanitize_value
from .secrets import Token
from .transport import MoodleTransport

__all__ = [
    "AllowList",
    "FunctionNotAllowed",
    "GradeWriteNotAllowed",
    "InvalidParameters",
    "MoodleClient",
    "MoodleConfigError",
    "MoodleError",
    "MoodleTransport",
    "MoodleUnreachable",
    "NotSupported",
    "Outcome",
    "PermissionDenied",
    "RedactingFilter",
    "Site",
    "SiteSettings",
    "Token",
    "TokenInvalid",
    "UnexpectedResponse",
    "WorkflowStateNotAllowed",
    "WriteResult",
    "create_client",
    "grade_in_range",
    "grading_status",
    "load_allowlist",
    "load_site",
    "messages",
    "parse_grade",
    "redact",
    "result_for",
    "safe_url",
    "sanitize",
    "sanitize_value",
    "stored_grade_matches",
    "write_draft_grade",
]

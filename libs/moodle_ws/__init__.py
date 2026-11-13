"""Shared Moodle web-services client (PRD B4). Release 0 skeleton; no real transport yet.

This part provides the error family, the user-facing messages, the Token type, the site
settings and redaction. The client itself follows in a later pull request. See README.md in
this folder.
"""

from . import messages
from .config import Site, SiteSettings, load_site
from .errors import (
    FunctionNotAllowed,
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
from .redact import RedactingFilter, redact, safe_url, sanitize, sanitize_value
from .secrets import Token

__all__ = [
    "FunctionNotAllowed",
    "InvalidParameters",
    "MoodleConfigError",
    "MoodleError",
    "MoodleUnreachable",
    "NotSupported",
    "PermissionDenied",
    "RedactingFilter",
    "Site",
    "SiteSettings",
    "Token",
    "TokenInvalid",
    "UnexpectedResponse",
    "WorkflowStateNotAllowed",
    "load_site",
    "messages",
    "redact",
    "safe_url",
    "sanitize",
    "sanitize_value",
]

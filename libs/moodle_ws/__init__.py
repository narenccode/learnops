"""Shared Moodle web-services client (PRD B4). Release 0 skeleton; no real transport yet.

This part provides the error family, the user-facing messages, the Token type, the site
settings, redaction, the allow-list and the transport interface. The client itself follows in
a later pull request. See README.md in this folder.
"""

from . import messages
from .allowlist import AllowList, load_allowlist
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
from .transport import MoodleTransport

__all__ = [
    "AllowList",
    "FunctionNotAllowed",
    "InvalidParameters",
    "MoodleConfigError",
    "MoodleError",
    "MoodleTransport",
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
    "load_allowlist",
    "load_site",
    "messages",
    "redact",
    "safe_url",
    "sanitize",
    "sanitize_value",
]

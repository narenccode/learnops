"""Shared Moodle web-services client (PRD B4). Release 0 skeleton; no real transport yet.

This part provides the error family, the user-facing messages, the Token type and the site
settings. Redaction, the allow-list, the transport interface and the client follow in later pull
requests. See README.md in this folder.
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
from .secrets import Token


__all__ = [
    "FunctionNotAllowed",
    "InvalidParameters",
    "MoodleConfigError",
    "MoodleError",
    "MoodleUnreachable",
    "NotSupported",
    "PermissionDenied",
    "Site",
    "SiteSettings",
    "Token",
    "TokenInvalid",
    "UnexpectedResponse",
    "WorkflowStateNotAllowed",
    "load_site",
    "messages",
]

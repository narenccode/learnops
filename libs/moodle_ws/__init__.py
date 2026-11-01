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
    "MoodleClient",
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
    "create_client",
    "load_allowlist",
    "load_site",
    "messages",
    "redact",
    "safe_url",
    "sanitize",
    "sanitize_value",
]

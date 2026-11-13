"""Typed errors of the Moodle web-services client.

Every error derives from MoodleError so callers can catch one type. `code` is the stable name used
in job records and the failure table (design §10.2); `retryable` tells the job runner whether a
retry can help. The class list is library documentation, not contract text (guide on Q37, PR #27).
Messages never contain tokens, full URLs or request parameters.
"""

from __future__ import annotations

from typing import ClassVar


class MoodleError(Exception):
    """Base class of every Moodle web-services error."""

    code: ClassVar[str] = "moodle_error"
    retryable: ClassVar[bool] = False


class MoodleUnreachable(MoodleError):
    """Moodle did not answer. Retrying later can help."""

    code = "moodle_unreachable"
    retryable = True


class TokenInvalid(MoodleError):
    """Moodle rejected the service token."""

    code = "token_invalid"


class PermissionDenied(MoodleError):
    """The service account may not do this: a missing capability or enrolment."""

    code = "permission_denied"


class UnexpectedResponse(MoodleError):
    """The answer could not be understood. Never returned as partial data."""

    code = "unexpected_response"


class NotSupported(MoodleError):
    """The site or this library cannot do what was asked."""

    code = "not_supported"


class FunctionNotAllowed(MoodleError):
    """The function is not in the B4 allow-list. Nothing was sent to Moodle."""

    code = "function_not_allowed"


class WorkflowStateNotAllowed(MoodleError):
    """A write broke the draft rule (B4 §3). Nothing was sent to Moodle."""

    code = "workflow_state_not_allowed"


class InvalidParameters(MoodleError):
    """The parameters are not a mapping of plain values. Nothing was sent to Moodle."""

    code = "invalid_parameters"


class MoodleConfigError(MoodleError):
    """A setting or the allow-list is missing or invalid. Nothing was sent to Moodle."""

    code = "moodle_config_error"

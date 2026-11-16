"""The one way LearnOps calls Moodle web services (PRD B4, C-02).

call() enforces the allow-list and the draft rule before the transport is touched, so a refused
call never reaches Moodle. This is a second guard behind the restricted external service.

A grade write reaches Moodle only through MoodleClient.write_draft_grade (also reachable as
grade_write.write_draft_grade). _send, used by call(), refuses mod_assign_save_grade on every path.
The sender the guarded write uses is a closure created inside that one call, so there is no name to
import that sends a grade write without the write checks (the guide on PR #76, 15 Nov: close the
receipt bypass in code).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Final

from . import messages
from .allowlist import AllowList, load_allowlist
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
from .grades import parse_grade
from .transport import MoodleTransport

if TYPE_CHECKING:  # grade_write imports this module, so only for the type
    from .grade_write import WriteResult

SAVE_GRADE: Final = "mod_assign_save_grade"
# Removed from B4 by the guide's findings (PR #64). Refused here even if an allow-list file still
# lists it, so an older contract file cannot bring it back.
SET_USER_FLAGS: Final = "mod_assign_set_user_flags"
_ALWAYS_REFUSED: Final = frozenset({SET_USER_FLAGS})
WORKFLOW_PARAMETER: Final = "workflowstate"  # named by PRD App-C item 1
ATTEMPT_PARAMETER: Final = "attemptnumber"  # PRD B4 parameter table
GRADE_PARAMETER: Final = "grade"  # PRD B4 parameter table
READY_FOR_RELEASE: Final = "readyforrelease"
RELEASED: Final = "released"
MAX_DEPTH: Final = 32  # a local safety limit on nesting, not a Moodle rule
_PLAIN_VALUES: Final = (str, int, float, bool, type(None))
_PLAIN_KEYS: Final = (str, int)

# A transport's own text may hold a token, a URL or a parameter, so it is never shown.
_PUBLIC_MESSAGES: Final = {
    MoodleUnreachable.code: messages.UNREACHABLE,
    TokenInvalid.code: messages.TOKEN_REJECTED,
    PermissionDenied.code: messages.PERMISSION_REFUSED,
    NotSupported.code: messages.SITE_CANNOT_DO_THIS,
}


def _copy_value(value: Any, path: frozenset[int]) -> Any:
    """A private copy, built from exact plain types only. copy.deepcopy is not used, because it
    runs an object's own code. An object cannot pass the draft rule by hiding what it holds."""
    kind = type(value)
    if kind in _PLAIN_VALUES:
        return value
    if (
        kind not in (dict, list, tuple, set, frozenset)
        or id(value) in path
        or len(path) >= MAX_DEPTH
    ):
        raise InvalidParameters(messages.INVALID_PARAMETERS)
    inner = path | {id(value)}
    if kind is dict:
        if any(type(key) not in _PLAIN_KEYS for key in value):
            raise InvalidParameters(messages.INVALID_PARAMETERS)
        return {key: _copy_value(item, inner) for key, item in value.items()}
    copied = [_copy_value(item, inner) for item in value]
    return copied if kind is list else kind(copied)


def _copy_params(params: Mapping[str, Any] | None) -> dict[str, Any]:
    """Read a mapping once, so what is checked is exactly what the transport receives."""
    if params is None:
        return {}
    if not isinstance(params, Mapping):
        raise InvalidParameters(messages.INVALID_PARAMETERS)
    try:
        items = dict(params.items())
    except Exception:
        items = None
    if items is None:
        raise InvalidParameters(messages.INVALID_PARAMETERS)
    copied: dict[str, Any] = _copy_value(items, frozenset())
    return copied


def _holds_released(params: dict[str, Any]) -> bool:
    """True if any key or value, at any depth, is exactly `released`. A sentence containing the
    word is not: feedback is free text. Parameter names are not used, because B4 does not name
    them yet. It reads the copy from _copy_params, so only plain values are present.
    """
    pending: list[Any] = [params]
    while pending:
        value = pending.pop()
        if isinstance(value, str):
            if value.strip().casefold() == RELEASED:
                return True
        elif isinstance(value, dict):
            pending.extend(value.keys())
            pending.extend(value.values())
        elif isinstance(value, list | tuple | set | frozenset):
            pending.extend(value)
    return False


def _check_draft_rule(function: str, params: dict[str, Any]) -> None:
    """B4 §3: a grade write sends readyforrelease and never released."""
    if function != SAVE_GRADE:
        return
    if _holds_released(params):
        raise WorkflowStateNotAllowed(
            messages.RELEASE_REFUSED.format(function=function, state=RELEASED)
        )
    if params.get(WORKFLOW_PARAMETER) != READY_FOR_RELEASE:
        raise WorkflowStateNotAllowed(
            messages.WORKFLOW_STATE_REQUIRED.format(
                function=function, state=READY_FOR_RELEASE
            )
        )


def is_explicit_attempt(value: object) -> bool:
    """B4 R2: an attempt number is a whole number from 0; never -1 ("latest") and never bool."""
    return type(value) is int and value >= 0


def _check_grade_write(function: str, params: dict[str, Any]) -> None:
    """B4 R2 and R9, the part the client can check alone: an explicit attempt and a plain,
    non-negative number as the grade. The maximum needs the assignment, so it is checked by the
    guarded write, not here."""
    if function != SAVE_GRADE:
        return
    if not is_explicit_attempt(params.get(ATTEMPT_PARAMETER)):
        raise GradeWriteNotAllowed(messages.ATTEMPT_REQUIRED)
    grade = parse_grade(params.get(GRADE_PARAMETER))
    if grade is None or grade < 0:
        raise GradeWriteNotAllowed(messages.GRADE_NOT_A_NUMBER)


def _public_error(error: MoodleError, settings: SiteSettings) -> MoodleError:
    """The same class with a fixed message. __new__ skips a subclass's own __init__, which could
    fail here or keep a raw value as an attribute."""
    text = _PUBLIC_MESSAGES.get(error.code, messages.UNEXPECTED)
    public = type(error).__new__(type(error))
    Exception.__init__(public, text.format(site=settings.site))
    return public


def _failure_for(error: Exception, settings: SiteSettings) -> MoodleError:
    """The library's own error for anything a transport raised, with a fixed message."""
    if isinstance(error, MoodleError):
        return _public_error(error, settings)
    if isinstance(error, OSError):  # includes TimeoutError and ConnectionError
        return MoodleUnreachable(messages.UNREACHABLE.format(site=settings.site))
    return UnexpectedResponse(messages.UNEXPECTED.format(site=settings.site))


class MoodleClient:
    def __init__(
        self,
        site: SiteSettings,
        transport: MoodleTransport,
        allowlist: AllowList | None = None,
    ) -> None:
        if not isinstance(site, SiteSettings):
            raise MoodleConfigError(messages.CLIENT_NEEDS_SETTINGS)
        if not callable(getattr(transport, "call", None)):
            raise MoodleConfigError(messages.CLIENT_NEEDS_TRANSPORT)
        if allowlist is not None and not isinstance(allowlist, AllowList):
            raise MoodleConfigError(messages.CLIENT_NEEDS_ALLOW_LIST)
        self._settings = site
        self._transport = transport
        self._allowlist = load_allowlist() if allowlist is None else allowlist

    def call(self, function: str, params: Mapping[str, Any] | None = None) -> Any:
        """The transport's answer, unchanged until the normalized models exist (design §4.1).

        mod_assign_save_grade is checked like any call and then refused: a grade write is sent
        only through grade_write.write_draft_grade, which runs the checks call() cannot run alone
        (maximum grade, locked state, marking workflow) and reads the result back."""
        return self._send(function, _copy_params(params))

    def write_draft_grade(
        self, params: Mapping[str, Any], max_grade: object
    ) -> WriteResult:
        """Write one mentor-approved draft grade, at most once, and read it back (B4 §3, §3a).

        The checks and the read-back are grade_write's; the send is created here, inside this one
        call, and works once, so it cannot be imported or reused to skip them."""
        from . import (
            grade_write,
        )  # here, not at the top: grade_write imports this module

        settings = self._settings
        used = False

        def send_once(checked: Mapping[str, Any]) -> Any:
            nonlocal used
            if used:
                raise GradeWriteNotAllowed(messages.WRITE_NEEDS_HELPER)
            used = True  # before sending: a write is never sent twice (R8, R11)
            values = _copy_params(checked)
            name = self._allowlist.resolve(SAVE_GRADE, settings.moodle_version)
            _check_draft_rule(SAVE_GRADE, values)
            _check_grade_write(SAVE_GRADE, values)
            try:
                return self._transport.call(settings, name, values)
            except Exception as error:
                failure = _failure_for(error, settings)
            raise failure  # outside the except block, as in _send

        return grade_write._checked_write(self, params, max_grade, send_once)

    def _send(self, function: str, values: dict[str, Any]) -> Any:
        settings = self._settings
        if function in _ALWAYS_REFUSED:
            raise FunctionNotAllowed(messages.FUNCTION_NOT_ALLOWED)
        name = self._allowlist.resolve(function, settings.moodle_version)
        _check_draft_rule(function, values)
        _check_grade_write(function, values)
        # The guards above still run first, so a direct call reports its specific reason. Then a
        # grade write is refused on every path: no caller can get past this line with one.
        if function == SAVE_GRADE:
            raise GradeWriteNotAllowed(messages.WRITE_NEEDS_HELPER)
        try:
            return self._transport.call(settings, name, values)
        except Exception as error:
            failure = _failure_for(error, settings)
        # Raised outside the except block so the original, which may hold a token or a URL, is not
        # kept as __context__. "raise ... from None" would only hide it.
        raise failure


def create_client(
    site: Site | str,
    transport: MoodleTransport | None = None,
    environ: Mapping[str, str] | None = None,
) -> MoodleClient:
    if transport is None:
        raise NotSupported(messages.NOT_INTEGRATED)
    return MoodleClient(load_site(site, environ), transport)

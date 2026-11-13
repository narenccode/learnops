"""The one way LearnOps calls Moodle web services (PRD B4, C-02).

call() enforces the allow-list and the draft rule before the transport is touched, so a refused
call never reaches Moodle. This is a second guard behind the restricted external service. A grade
write is never sent by call(): only grade_write.write_draft_grade can send one (see WriteReceipt).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

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
    non-negative number as the grade. It runs on every path, including a receipt's. The maximum
    needs the assignment, so grade_write checks it before issuing the receipt."""
    if function != SAVE_GRADE:
        return
    if not is_explicit_attempt(params.get(ATTEMPT_PARAMETER)):
        raise GradeWriteNotAllowed(messages.ATTEMPT_REQUIRED)
    grade = parse_grade(params.get(GRADE_PARAMETER))
    if grade is None or grade < 0:
        raise GradeWriteNotAllowed(messages.GRADE_NOT_A_NUMBER)


_RECEIPT_SEAL: Final = object()


class WriteReceipt:
    """Proof that grade_write.write_draft_grade ran every pre-write check (R2, R3, R9 and the
    marking-workflow and state checks) for exactly these parameters, on this client.

    It holds its own copy of the checked parameters, so what was checked is what is sent, and it
    works once. It cannot be built without the module's seal. This stops a grade write that skips
    the checks by mistake; it is not a boundary against code that deliberately imports private
    names (a test checks no module outside this library does)."""

    __slots__ = ("_client", "_params", "_used")

    def __init__(
        self, seal: object, client: MoodleClient, params: dict[str, Any]
    ) -> None:
        if seal is not _RECEIPT_SEAL:
            raise GradeWriteNotAllowed(messages.WRITE_NEEDS_HELPER)
        self._client = client
        self._params = params
        self._used = False


def _issue_receipt(client: MoodleClient, checked: Mapping[str, Any]) -> WriteReceipt:
    """For grade_write only, after all its checks have passed."""
    return WriteReceipt(_RECEIPT_SEAL, client, _copy_params(checked))


def _public_error(error: MoodleError, settings: SiteSettings) -> MoodleError:
    """The same class with a fixed message. __new__ skips a subclass's own __init__, which could
    fail here or keep a raw value as an attribute."""
    text = _PUBLIC_MESSAGES.get(error.code, messages.UNEXPECTED)
    public = type(error).__new__(type(error))
    Exception.__init__(public, text.format(site=settings.site))
    return public


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
        return self._send(function, _copy_params(params), None)

    def _send_checked_write(self, receipt: WriteReceipt) -> Any:
        """Send the grade write a receipt allows. For grade_write only."""
        if (
            type(receipt) is not WriteReceipt
            or receipt._client is not self
            or receipt._used
        ):
            raise GradeWriteNotAllowed(messages.WRITE_NEEDS_HELPER)
        receipt._used = True  # before sending: a write is never sent twice (R8, R11)
        return self._send(SAVE_GRADE, receipt._params, receipt)

    def _send(
        self, function: str, values: dict[str, Any], receipt: WriteReceipt | None
    ) -> Any:
        settings = self._settings
        if function in _ALWAYS_REFUSED:
            raise FunctionNotAllowed(messages.FUNCTION_NOT_ALLOWED)
        name = self._allowlist.resolve(function, settings.moodle_version)
        _check_draft_rule(function, values)
        _check_grade_write(function, values)
        if function == SAVE_GRADE and receipt is None:
            raise GradeWriteNotAllowed(messages.WRITE_NEEDS_HELPER)
        try:
            return self._transport.call(settings, name, values)
        except MoodleError as error:
            failure = _public_error(error, settings)
        except OSError:  # includes TimeoutError and ConnectionError
            failure = MoodleUnreachable(messages.UNREACHABLE.format(site=settings.site))
        except Exception:
            failure = UnexpectedResponse(messages.UNEXPECTED.format(site=settings.site))
        # Raised outside the except blocks so the original, which may hold a token or a URL, is not
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

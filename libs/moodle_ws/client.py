"""The one way LearnOps calls Moodle web services (PRD B4, C-02).

call() enforces the allow-list and the draft rule before the transport is touched, so a refused
call never reaches Moodle. This is a second guard behind the restricted external service.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

from . import messages
from .allowlist import AllowList, load_allowlist
from .config import Site, SiteSettings, load_site
from .errors import (
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
from .transport import MoodleTransport

SAVE_GRADE: Final = "mod_assign_save_grade"
SET_USER_FLAGS: Final = "mod_assign_set_user_flags"
WORKFLOW_PARAMETER: Final = "workflowstate"  # named by PRD App-C item 1
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
    if function not in (SAVE_GRADE, SET_USER_FLAGS):
        return
    if _holds_released(params):
        raise WorkflowStateNotAllowed(
            messages.RELEASE_REFUSED.format(function=function, state=RELEASED)
        )
    if function == SAVE_GRADE and params.get(WORKFLOW_PARAMETER) != READY_FOR_RELEASE:
        raise WorkflowStateNotAllowed(
            messages.WORKFLOW_STATE_REQUIRED.format(
                function=function, state=READY_FOR_RELEASE
            )
        )


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
        """The transport's answer, unchanged until the normalized models exist (design §4.1)."""
        settings = self._settings
        name = self._allowlist.resolve(function, settings.moodle_version)
        values = _copy_params(params)
        _check_draft_rule(function, values)
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

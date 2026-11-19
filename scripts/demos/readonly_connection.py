"""H5: the demo's read-only connection to Moodle (PLAN-demo-grading.md, ground rule 5).

A transport for libs/moodle_ws that can only READ. It allows the six read functions of PRD B4 §2 and
refuses every other function name, above all mod_assign_save_grade, BEFORE anything is sent. It also
downloads one submitted file (plan step H4.6), only from the site's own pluginfile.php.

This is a demo-only helper, allowed by the guide. It is NOT the library's real transport (that waits
for the lab checks, B4 §5), it stays out of libs/, and the library's HTTP transport that was reverted
(issue #107) is not reused here.

Use it with the library's client, which checks its own allow-list first:

    from moodle_ws import MoodleClient, load_site
    client = MoodleClient(load_site("moodle53"), ReadOnlyTransport())

The site address and the token come from the environment (MOODLE53_URL, MOODLE53_WS_TOKEN) through
load_site; nothing here reads or prints them. The token goes in the POST body, never in the address,
except for the file download, where Moodle takes it in the address: that address is never shown.

Undo: nothing to undo. It sends only reads and keeps no state.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Final
from urllib.parse import quote, unquote, urlencode, urlsplit

ROOT = Path(__file__).resolve().parents[2]
# The repository has a data folder named contracts/ at its root. Put libs/ first so that imports
# find the libraries, not that folder.
sys.path.insert(0, str(ROOT / "libs"))

from moodle_ws import (  # noqa: E402
    FunctionNotAllowed,
    InvalidParameters,
    MoodleError,
    MoodleUnreachable,
    PermissionDenied,
    SiteSettings,
    TokenInvalid,
    UnexpectedResponse,
    messages,
)

# The six read functions of PRD B4 §2, as posted in #112 (H1). Exact match only.
ALLOWED_FUNCTIONS: Final = frozenset(
    {
        "core_course_get_courses_by_field",
        "core_course_get_contents",
        "core_enrol_get_enrolled_users",
        "mod_assign_get_assignments",
        "mod_assign_get_submissions",
        "mod_assign_get_submission_status",
    }
)
# Moodle's REST fields. A parameter may not use them, or it could replace the function or the token.
RESERVED_FIELDS: Final = frozenset({"wstoken", "wsfunction", "moodlewsrestformat"})
REST_PATH: Final = "/webservice/rest/server.php"
FILE_PATH: Final = "/webservice/pluginfile.php/"
TIMEOUT_SECONDS: Final = 30.0
MAX_ANSWER_BYTES: Final = 10_000_000  # a safety limit on one answer, not a Moodle rule
_NAME: Final = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# Moodle's error codes (answer field `errorcode`) that mean "the token" or "the rights".
_TOKEN_CODES: Final = frozenset({"invalidtoken"})
_RIGHTS_CODES: Final = frozenset({"accessexception", "nopermissions"})

# --- all user-facing text in one place (root CLAUDE.md §6) ---------------------------------

REFUSED_FUNCTION = (
    "The demo's read-only connection allows only the six read functions, so this call was not "
    "sent to Moodle. Nothing was written."
)
REFUSED_DOWNLOAD = (
    "The demo's read-only connection downloads only files under /webservice/pluginfile.php on its "
    "own Moodle site, so this download was not sent."
)
BAD_LIMIT = "The download size limit must be a whole number of bytes above zero."
FILE_TOO_BIG = (
    "The file is larger than the limit of {limit} bytes, so it was not accepted. Raise the limit "
    "or check the file in Moodle."
)

Post = Callable[[str, bytes, float], bytes]
Get = Callable[[str, float, int], bytes]


# --- the real HTTP functions (replaced by fakes in the tests) --------------------------------


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect could carry the token to another host, so a redirect is an error."""

    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


_OPENER: Final = urllib.request.build_opener(_NoRedirect)


def _http_post(url: str, body: bytes, timeout: float) -> bytes:
    request = urllib.request.Request(  # noqa: S310  (the address is http(s), checked in SiteSettings)
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with _OPENER.open(request, timeout=timeout) as response:
        data: bytes = response.read(MAX_ANSWER_BYTES + 1)
    if len(data) > MAX_ANSWER_BYTES:
        raise UnexpectedResponse("answer too large")
    return data


def _http_get(url: str, timeout: float, max_bytes: int) -> bytes:
    request = urllib.request.Request(url, method="GET")  # noqa: S310
    with _OPENER.open(request, timeout=timeout) as response:
        data: bytes = response.read(max_bytes + 1)  # one byte more, to see "too big"
    return data


# --- parameters ------------------------------------------------------------------------------


def _flatten(prefix: str, value: Any, out: list[tuple[str, str]]) -> None:
    """Moodle's REST form: lists and mappings become name[0][key]=value."""
    if isinstance(value, bool):
        out.append((prefix, "1" if value else "0"))
    elif isinstance(value, int | float | str):
        out.append((prefix, str(value)))
    elif isinstance(value, Mapping):
        for key, item in value.items():
            if not (isinstance(key, str) and _NAME.fullmatch(key)):
                raise InvalidParameters(messages.INVALID_PARAMETERS)
            _flatten(f"{prefix}[{key}]", item, out)
    elif isinstance(value, list | tuple):
        for index, item in enumerate(value):
            _flatten(f"{prefix}[{index}]", item, out)
    else:
        raise InvalidParameters(messages.INVALID_PARAMETERS)


def _encode(params: Mapping[str, Any] | None) -> list[tuple[str, str]]:
    if params is None:
        return []
    if not isinstance(params, Mapping):
        raise InvalidParameters(messages.INVALID_PARAMETERS)
    out: list[tuple[str, str]] = []
    for key, value in params.items():
        valid = isinstance(key, str) and _NAME.fullmatch(key)
        if not valid or key in RESERVED_FIELDS:
            raise InvalidParameters(messages.INVALID_PARAMETERS)
        _flatten(key, value, out)
    return out


# --- the transport ---------------------------------------------------------------------------


class ReadOnlyTransport:
    """Sends only the six read functions. Fixed error texts only: Moodle's own message can echo
    the token or the address, so it is never passed on."""

    def __init__(
        self,
        post: Post = _http_post,
        get: Get = _http_get,
        timeout: float = TIMEOUT_SECONDS,
    ) -> None:
        self._post = post
        self._get = get
        self._timeout = timeout

    def __repr__(self) -> str:
        return "ReadOnlyTransport(read-only)"

    def call(
        self, settings: SiteSettings, function: str, params: Mapping[str, Any]
    ) -> Any:
        # Every refusal is decided here, before anything is built or sent.
        if type(function) is not str or function not in ALLOWED_FUNCTIONS:
            raise FunctionNotAllowed(REFUSED_FUNCTION)
        fields = _encode(params)
        body = urlencode(
            [
                ("wstoken", settings.token.reveal()),
                ("wsfunction", function),
                ("moodlewsrestformat", "json"),
                *fields,
            ]
        ).encode("utf-8")
        url = settings.url.rstrip("/") + REST_PATH
        try:
            raw = self._post(url, body, self._timeout)
        except Exception as error:
            failure = _failure_for(error, settings)
        else:
            return _answer(raw, settings)
        raise failure  # outside the except block, so the original is not kept as __context__

    def download_file(self, settings: SiteSettings, url: str, max_bytes: int) -> bytes:
        """One submitted file, from this site's pluginfile.php only (plan H4 step 6)."""
        if type(max_bytes) is not int or max_bytes <= 0:
            raise InvalidParameters(BAD_LIMIT)
        if not _is_own_file_address(url, settings):
            raise FunctionNotAllowed(REFUSED_DOWNLOAD)
        address = f"{url}?token={quote(settings.token.reveal(), safe='')}"
        try:
            data = self._get(address, self._timeout, max_bytes)
        except Exception as error:
            failure = _failure_for(error, settings)
        else:
            if len(data) > max_bytes:
                raise UnexpectedResponse(FILE_TOO_BIG.format(limit=max_bytes))
            return data
        raise failure


def _is_own_file_address(url: object, settings: SiteSettings) -> bool:
    """Same scheme, host and port as the site, under its pluginfile.php, with nothing else in it."""
    if not isinstance(url, str) or not url:
        return False
    if any(c.isspace() or c == "\\" for c in url) or "?" in url or "#" in url:
        return False
    try:
        site = urlsplit(settings.url)
        parts = urlsplit(url)
        parts.port  # noqa: B018  # raises on a malformed port
    except ValueError:
        return False
    if parts.username is not None or parts.password is not None:
        return False
    if (parts.scheme, parts.netloc.lower()) != (site.scheme, site.netloc.lower()):
        return False
    required = site.path.rstrip("/") + FILE_PATH
    if not parts.path.startswith(required):
        return False
    # Dots in a path would climb out of pluginfile.php, also when written as %2e.
    segments = unquote(parts.path).split("/")
    return "." not in segments and ".." not in segments


# --- Moodle's answers ----------------------------------------------------------------------------


def _answer(raw: bytes, settings: SiteSettings) -> Any:
    try:
        answer = json.loads(raw)
    except ValueError:
        answer = None
        failed = True
    else:
        failed = False
    if failed:
        raise UnexpectedResponse(messages.UNEXPECTED.format(site=settings.site))
    if isinstance(answer, Mapping) and "exception" in answer:
        code = answer.get("errorcode")
        if code in _TOKEN_CODES:
            raise TokenInvalid(messages.TOKEN_REJECTED.format(site=settings.site))
        if code in _RIGHTS_CODES:
            raise PermissionDenied(
                messages.PERMISSION_REFUSED.format(site=settings.site)
            )
        raise UnexpectedResponse(messages.UNEXPECTED.format(site=settings.site))
    return answer


def _failure_for(error: Exception, settings: SiteSettings) -> MoodleError:
    """The library's own error, with a fixed message. A transport's text may hold a token."""
    if isinstance(error, MoodleError):
        return error
    if isinstance(
        error, OSError
    ):  # includes TimeoutError, ConnectionError and HTTPError
        return MoodleUnreachable(messages.UNREACHABLE.format(site=settings.site))
    return UnexpectedResponse(messages.UNEXPECTED.format(site=settings.site))

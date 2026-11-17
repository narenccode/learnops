"""A real transport: Moodle's REST web-service protocol over HTTP(S), standard library only.

Endpoint `<site url>/webservice/rest/server.php`, one POST per call, form-encoded, with `wstoken`,
`wsfunction` and `moodlewsrestformat=json`. The token goes in the request body, never in the URL,
so the URL a log or proxy may see holds no secret. Lists and mappings use Moodle's array form
(`assignmentids[0]=7`, `plugindata[x][text]=...`).

This follows Moodle's documented REST protocol. It has NOT been run against a lab site: that is lab
check 1 (contracts/moodle-ws.v1.md §5). The error codes below are read from Moodle's source, not
observed. An unknown error answer fails closed as UnexpectedResponse.

This is the only module that calls Token.reveal(). The client replaces every error message with a
fixed one, and the messages raised here never hold the token, the URL or a parameter.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator, Mapping
from typing import Any, Final, Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from . import messages
from .config import SiteSettings
from .errors import (
    MoodleError,
    NotSupported,
    PermissionDenied,
    TokenInvalid,
    UnexpectedResponse,
)

ENDPOINT: Final = "/webservice/rest/server.php"
DEFAULT_TIMEOUT: Final = 30.0  # seconds; a local choice, not a Moodle rule
MAX_RESPONSE_BYTES: Final = 10 * 1024 * 1024  # a local safety limit, not a Moodle rule

_NOT_JSON: Final = object()

# Moodle's errorcode values (read from the Moodle source, not observed: lab check 1).
_ERROR_CLASSES: Final[Mapping[str, type[MoodleError]]] = {
    "invalidtoken": TokenInvalid,
    "accessexception": PermissionDenied,
    "nopermissions": PermissionDenied,
    "requireloginerror": PermissionDenied,
    "webservicesnotenabled": NotSupported,
    "servicenotavailable": NotSupported,
}


class _Response(Protocol):
    def read(self, amt: int = ..., /) -> bytes: ...

    def __enter__(self) -> _Response: ...

    def __exit__(self, *args: object) -> object: ...


Opener = Callable[[Request, float], _Response]


def _default_opener(request: Request, timeout: float) -> _Response:
    response: _Response = urlopen(request, timeout=timeout)  # noqa: S310  # http(s) only, checked by SiteSettings
    return response


def _flatten(prefix: str, value: Any) -> Iterator[tuple[str, str]]:
    """Moodle's array form. The client has already copied the parameters into plain values."""
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield from _flatten(f"{prefix}[{key}]", item)
    elif isinstance(value, list | tuple):
        for index, item in enumerate(value):
            yield from _flatten(f"{prefix}[{index}]", item)
    elif isinstance(value, bool):
        yield prefix, "1" if value else "0"
    elif value is None:
        return
    elif isinstance(value, str | int | float):
        yield prefix, str(value)
    else:  # sets have no order Moodle could rely on
        raise UnexpectedResponse(messages.TRANSPORT_PARAMETER_REFUSED)


def encode_params(params: Mapping[str, Any]) -> list[tuple[str, str]]:
    """The form fields for these parameters, in a stable order. No token here."""
    fields: list[tuple[str, str]] = []
    for name, value in params.items():
        fields.extend(_flatten(str(name), value))
    return fields


def endpoint(settings: SiteSettings) -> str:
    return settings.url.rstrip("/") + ENDPOINT


def _error_for(answer: Any, settings: SiteSettings) -> MoodleError | None:
    """Moodle answers a failed call with HTTP 200 and an object holding `exception`."""
    if not isinstance(answer, dict) or "exception" not in answer:
        return None
    kind = _ERROR_CLASSES.get(str(answer.get("errorcode", "")), UnexpectedResponse)
    return kind(messages.UNEXPECTED.format(site=settings.site))


class HttpTransport:
    """MoodleTransport over Moodle's REST protocol. Pass `opener` in tests; never a real socket."""

    def __init__(
        self, opener: Opener | None = None, timeout: float = DEFAULT_TIMEOUT
    ) -> None:
        self._opener = _default_opener if opener is None else opener
        self._timeout = timeout

    def call(
        self, settings: SiteSettings, function: str, params: Mapping[str, Any]
    ) -> Any:
        fields = [
            ("wstoken", settings.token.reveal()),
            ("wsfunction", function),
            ("moodlewsrestformat", "json"),
            *encode_params(params),
        ]
        request = Request(
            endpoint(settings),
            data=urlencode(fields).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        # OSError (network, timeout, HTTP status) passes up: the client turns it into
        # MoodleUnreachable with a fixed message.
        with self._opener(request, self._timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise UnexpectedResponse(messages.UNEXPECTED.format(site=settings.site))
        try:
            answer = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            answer = _NOT_JSON
        if answer is _NOT_JSON:
            raise UnexpectedResponse(messages.UNEXPECTED.format(site=settings.site))
        error = _error_for(answer, settings)
        if error is not None:
            raise error
        return answer

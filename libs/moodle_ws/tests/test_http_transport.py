"""HttpTransport with an injected opener: no socket is opened (conftest), and no Moodle is reached.

These show the request is built and the answer read as Moodle's REST protocol is documented. They
show nothing about a real Moodle (lab check 1).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import parse_qsl
from urllib.request import Request

import pytest

from moodle_ws import (
    FunctionNotAllowed,
    HttpTransport,
    MoodleClient,
    MoodleUnreachable,
    NotSupported,
    PermissionDenied,
    SiteSettings,
    TokenInvalid,
    UnexpectedResponse,
)
from moodle_ws.http_transport import MAX_RESPONSE_BYTES, encode_params, endpoint

from .conftest import FAKE_TOKEN


class _Answer:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self, amt: int = -1, /) -> bytes:
        return self._body if amt < 0 else self._body[:amt]

    def __enter__(self) -> _Answer:
        return self

    def __exit__(self, *args: object) -> None:
        return None


@dataclass
class Opener:
    body: bytes = b"[]"
    failure: Exception | None = None
    requests: list[Request] = field(default_factory=list)
    timeouts: list[float] = field(default_factory=list)

    def __call__(self, request: Request, timeout: float) -> _Answer:
        self.requests.append(request)
        self.timeouts.append(timeout)
        if self.failure is not None:
            raise self.failure
        return _Answer(self.body)

    def form(self) -> list[tuple[str, str]]:
        data = self.requests[-1].data
        assert isinstance(data, bytes)
        return parse_qsl(data.decode("utf-8"), keep_blank_values=True)


def answer(value: Any) -> bytes:
    return json.dumps(value).encode("utf-8")


def test_posts_to_the_rest_endpoint_with_the_token_in_the_body(
    settings: SiteSettings,
) -> None:
    opener = Opener(answer({"assignments": []}))
    result = HttpTransport(opener).call(
        settings, "mod_assign_get_grades", {"assignmentids": [7]}
    )
    request = opener.requests[0]
    assert result == {"assignments": []}
    assert request.get_method() == "POST"
    assert request.full_url == "https://moodle45.lab.invalid/webservice/rest/server.php"
    assert FAKE_TOKEN not in request.full_url
    assert opener.form() == [
        ("wstoken", FAKE_TOKEN),
        ("wsfunction", "mod_assign_get_grades"),
        ("moodlewsrestformat", "json"),
        ("assignmentids[0]", "7"),
    ]


def test_endpoint_ignores_a_trailing_slash(settings: SiteSettings) -> None:
    with_slash = SiteSettings(settings.site, "4.5", settings.url + "/", settings.token)
    assert endpoint(with_slash) == endpoint(settings)


def test_parameters_use_moodles_array_form() -> None:
    assert encode_params(
        {
            "assignmentid": 7,
            "grade": 84.5,
            "applytoall": 0,
            "flag": True,
            "skipped": None,
            "plugindata": {"editor": {"text": "Good", "format": 1}},
            "ids": [3, 4],
        }
    ) == [
        ("assignmentid", "7"),
        ("grade", "84.5"),
        ("applytoall", "0"),
        ("flag", "1"),
        ("plugindata[editor][text]", "Good"),
        ("plugindata[editor][format]", "1"),
        ("ids[0]", "3"),
        ("ids[1]", "4"),
    ]


def test_a_set_is_refused_before_anything_is_sent(settings: SiteSettings) -> None:
    opener = Opener()
    with pytest.raises(UnexpectedResponse):
        HttpTransport(opener).call(settings, "mod_assign_get_grades", {"ids": {7}})
    assert opener.requests == []


def test_a_void_function_answers_null(settings: SiteSettings) -> None:
    assert HttpTransport(Opener(b"null")).call(settings, "f", {}) is None


@pytest.mark.parametrize(
    ("errorcode", "kind"),
    [
        ("invalidtoken", TokenInvalid),
        ("accessexception", PermissionDenied),
        ("nopermissions", PermissionDenied),
        ("requireloginerror", PermissionDenied),
        ("webservicesnotenabled", NotSupported),
        ("servicenotavailable", NotSupported),
        ("invalidparameter", UnexpectedResponse),
        ("something_new", UnexpectedResponse),
    ],
)
def test_moodle_error_answers_become_typed_errors(
    settings: SiteSettings, errorcode: str, kind: type[Exception]
) -> None:
    body = answer(
        {
            "exception": "moodle_exception",
            "errorcode": errorcode,
            "message": f"detail with {FAKE_TOKEN} and https://moodle45.lab.invalid/x?y=1",
        }
    )
    with pytest.raises(kind) as raised:
        HttpTransport(Opener(body)).call(settings, "f", {})
    assert type(raised.value) is kind
    assert FAKE_TOKEN not in str(raised.value)
    assert "https://" not in str(raised.value)


@pytest.mark.parametrize(
    "body", [b"<html>login</html>", b"\xff\xfe", b"", b"{not json"]
)
def test_an_answer_that_is_not_json_is_unexpected(
    settings: SiteSettings, body: bytes
) -> None:
    with pytest.raises(UnexpectedResponse):
        HttpTransport(Opener(body)).call(settings, "f", {})


def test_a_too_large_answer_is_refused(settings: SiteSettings) -> None:
    with pytest.raises(UnexpectedResponse):
        HttpTransport(Opener(b" " * (MAX_RESPONSE_BYTES + 1))).call(settings, "f", {})


def test_the_timeout_is_passed_to_the_opener(settings: SiteSettings) -> None:
    opener = Opener()
    HttpTransport(opener, timeout=5.0).call(settings, "f", {})
    assert opener.timeouts == [5.0]


def test_through_the_client_a_network_failure_is_unreachable_without_the_token(
    settings: SiteSettings,
) -> None:
    opener = Opener(
        failure=OSError(f"refused {FAKE_TOKEN} https://moodle45.lab.invalid/x")
    )
    client = MoodleClient(settings, HttpTransport(opener))
    with pytest.raises(MoodleUnreachable) as raised:
        client.call("mod_assign_get_grades", {"assignmentids": [7]})
    assert FAKE_TOKEN not in str(raised.value)
    assert raised.value.__context__ is None


def test_through_the_client_the_allow_list_is_checked_before_the_opener(
    settings: SiteSettings,
) -> None:
    opener = Opener()
    client = MoodleClient(settings, HttpTransport(opener))
    with pytest.raises(FunctionNotAllowed):
        client.call("core_user_delete_users", {"userids": [42]})
    assert opener.requests == []

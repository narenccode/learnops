"""mod_assign_save_grade is blocked BEFORE transmission, proved on the real HTTP code.

The other tests inject fake HTTP functions. These do not: they use the helper's real urllib functions.
Part 1 blocks every socket, so any attempt to transmit fails loudly. Part 2 runs a real HTTP server on
127.0.0.1 (this machine only, no outside network) that records every request, and checks what reached
it: reads arrive, a grade write never does. This also runs the helper's real HTTP code, including the
no-redirect rule, for the first time (the plan's reminder for H4).
"""

from __future__ import annotations

import json
import secrets
import socket
import sys
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "libs"))
sys.path.insert(0, str(ROOT / "scripts" / "demos"))

import readonly_connection  # noqa: E402
from moodle_ws import (  # noqa: E402
    FunctionNotAllowed,
    MoodleClient,
    MoodleError,
    MoodleUnreachable,
    Site,
    SiteSettings,
    Token,
    TokenInvalid,
    UnexpectedResponse,
)
from readonly_connection import ReadOnlyTransport  # noqa: E402

# A random value made for this test run: no token value is written in the repository (PRD C-06).
TOKEN = "t" + secrets.token_hex(12)
SAVE = "mod_assign_save_grade"
WRITE = {
    "assignmentid": 7,
    "userid": 42,
    "grade": 5,
    "attemptnumber": 0,
    "addattempt": 0,
    "workflowstate": "readyforrelease",
    "applytoall": 0,
}


def settings_for(url: str) -> SiteSettings:
    return SiteSettings(Site.MOODLE53, "5.3", url, Token(TOKEN))


# --- part 1: no socket is ever opened ------------------------------------------------------------


@pytest.fixture
def no_socket(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    attempts: list[str] = []

    def refuse(*args: Any, **kwargs: Any) -> None:
        attempts.append("socket")
        raise AssertionError("something tried to open a network connection")

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    return attempts


def test_the_write_function_opens_no_socket_and_never_reaches_urllib(
    no_socket: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    class Opener:
        calls = 0

        def open(self, *args: Any, **kwargs: Any) -> None:
            Opener.calls += 1
            raise AssertionError("urllib was asked to send")

    monkeypatch.setattr(readonly_connection, "_OPENER", Opener())
    transport = ReadOnlyTransport()  # the REAL http functions
    with pytest.raises(FunctionNotAllowed):
        transport.call(settings_for("http://127.0.0.1:9"), SAVE, dict(WRITE))
    assert no_socket == [] and Opener.calls == 0


def test_the_library_client_blocks_a_direct_write_before_the_transport(
    no_socket: list[str],
) -> None:
    client = MoodleClient(settings_for("http://127.0.0.1:9"), ReadOnlyTransport())
    with pytest.raises(MoodleError):
        client.call(SAVE, dict(WRITE))
    assert no_socket == []


# --- part 2: a real local server records what reaches it -----------------------------------------


class Server:
    def __init__(self) -> None:
        self.requests: list[tuple[str, str, dict[str, list[str]]]] = []
        self.answer: Any = []
        self.status = 200
        self.file_bytes = b"a small test file"
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def _reply(
                self, code: int, body: bytes, extra: dict[str, str] | None = None
            ) -> None:
                self.send_response(code)
                self.send_header("Content-Length", str(len(body)))
                for key, value in (extra or {}).items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length", 0))
                fields = parse_qs(self.rfile.read(length).decode("utf-8"))
                owner.requests.append(("POST", self.path, fields))
                self._reply(owner.status, json.dumps(owner.answer).encode("utf-8"))

            def do_GET(self) -> None:  # noqa: N802
                owner.requests.append(("GET", self.path, {}))
                if "/redirect" in self.path:
                    where = f"http://127.0.0.1:{owner.port}/elsewhere/leak"
                    self._reply(302, b"", {"Location": where})
                else:
                    self._reply(200, owner.file_bytes)

            def log_message(self, *args: Any) -> None:  # keep the test output quiet
                pass

        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self._httpd.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}"
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()

    @property
    def functions(self) -> list[str]:
        return [
            f["wsfunction"][0] for method, _, f in self.requests if method == "POST"
        ]


@pytest.fixture
def server() -> Iterator[Server]:
    site = Server()
    site.start()
    try:
        yield site
    finally:
        site.stop()


def test_the_write_function_sends_nothing_over_a_real_connection(
    server: Server,
) -> None:
    transport = ReadOnlyTransport()
    with pytest.raises(FunctionNotAllowed):
        transport.call(settings_for(server.url), SAVE, dict(WRITE))
    assert server.requests == []  # not one request arrived


def test_a_read_does_reach_the_server_with_the_token_in_the_body_only(
    server: Server,
) -> None:
    ReadOnlyTransport().call(
        settings_for(server.url), "core_course_get_contents", {"courseid": 2}
    )
    assert server.functions == ["core_course_get_contents"]
    _, path, fields = server.requests[0]
    assert path == "/webservice/rest/server.php"
    assert fields["wstoken"] == [TOKEN] and TOKEN not in path


def test_a_draft_grade_write_reads_the_state_then_is_stopped_before_sending(
    server: Server,
) -> None:
    server.answer = {"lastattempt": {"gradingstatus": "notmarked"}}
    client = MoodleClient(settings_for(server.url), ReadOnlyTransport())
    with pytest.raises(FunctionNotAllowed):
        client.write_draft_grade(dict(WRITE), 10)
    assert server.functions == ["mod_assign_get_submission_status"]
    assert SAVE not in server.functions


def test_moodles_error_answer_over_a_real_connection_becomes_the_librarys_error(
    server: Server,
) -> None:
    server.answer = {
        "exception": "moodle_exception",
        "errorcode": "invalidtoken",
        "message": f"bad {TOKEN}",
    }
    with pytest.raises(TokenInvalid) as caught:
        ReadOnlyTransport().call(
            settings_for(server.url), "core_course_get_contents", {"courseid": 2}
        )
    assert TOKEN not in str(caught.value)


# --- the real file download, and the no-redirect rule ----------------------------------------------


def test_a_file_is_downloaded_over_a_real_connection(server: Server) -> None:
    url = f"{server.url}/webservice/pluginfile.php/55/assignsubmission_file/files/9/note.txt"
    data = ReadOnlyTransport().download_file(
        settings_for(server.url), url, max_bytes=1000
    )
    assert data == server.file_bytes
    assert urlsplit(server.requests[0][1]).path.startswith(
        "/webservice/pluginfile.php/"
    )


def test_a_redirect_is_not_followed_so_the_token_cannot_be_carried_elsewhere(
    server: Server,
) -> None:
    url = f"{server.url}/webservice/pluginfile.php/redirect/note.txt"
    with pytest.raises(MoodleUnreachable):
        ReadOnlyTransport().download_file(settings_for(server.url), url, max_bytes=1000)
    paths = [path for _, path, _ in server.requests]
    assert len(paths) == 1 and not any("elsewhere" in p for p in paths)


def test_a_file_over_the_limit_is_refused_over_a_real_connection(
    server: Server,
) -> None:
    server.file_bytes = b"x" * 5000
    url = f"{server.url}/webservice/pluginfile.php/1/a.txt"
    with pytest.raises(UnexpectedResponse):
        ReadOnlyTransport().download_file(settings_for(server.url), url, max_bytes=100)

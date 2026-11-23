"""`/media` route: path traversal, unexpected file names and HTTP Range requests.

These tests need no ffmpeg: the lesson folder is built by hand. They show what the route does for
the requests below. They do not show that the route is safe to expose: the demo has no
authentication or authorisation, so anyone who can reach the port can read every finished lesson.
"""

from pathlib import Path

import pytest

# fastapi and httpx are not in the shared requirements files (see requirements-video-demo.txt). The generic
# `checks` job runs every test without them, so these API tests skip there (listed by `pytest -rs`).
# The `video-demo` job installs them and fails on any skip.
pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402
from lesson_processor import app as app_module  # noqa: E402

LESSON = "courses/demo/01-demo-lessons/01-sample"
LESSON_URL = "/media/01-demo-lessons/01-sample"
VIDEO_BYTES = bytes(range(256)) * 20  # 5120 bytes, every offset has a known value
SECRET = b"TOP-SECRET-DO-NOT-SERVE"


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    out = tmp_path / "out"
    lesson = out / LESSON
    lesson.mkdir(parents=True)
    (lesson / "720p.mp4").write_bytes(VIDEO_BYTES)
    (lesson / "poster.jpg").write_bytes(b"\xff\xd8\xff-poster")
    (lesson / "lesson.json").write_text("{}", encoding="utf-8")
    # Files that exist but must never be served.
    (lesson / "captions.en.vtt").write_bytes(b"WEBVTT\n")
    (lesson / "secret.txt").write_bytes(SECRET)
    (out / "secret.txt").write_bytes(SECRET)
    (tmp_path / "secret.txt").write_bytes(SECRET)
    # A lesson folder without lesson.json is unfinished and is never served.
    unfinished = out / "courses/demo/01-demo-lessons/02-unfinished"
    unfinished.mkdir(parents=True)
    (unfinished / "720p.mp4").write_bytes(VIDEO_BYTES)
    monkeypatch.setenv("LESSON_OUTPUT_DIR", str(out))
    return TestClient(app_module.app)


def test_the_hand_built_lesson_is_served(client: TestClient) -> None:
    """Control case: if this fails, the refusals below prove nothing."""
    video = client.get(f"{LESSON_URL}/720p.mp4")
    assert video.status_code == 200
    assert video.content == VIDEO_BYTES
    assert video.headers["content-type"] == "video/mp4"
    assert video.headers["accept-ranges"] == "bytes"
    assert client.get(f"{LESSON_URL}/poster.jpg").status_code == 200
    assert client.get(f"{LESSON_URL}/lesson.json").status_code == 200


@pytest.mark.parametrize(
    "url",
    [
        # URL-encoded dot segments and separators, single and double encoded
        "/media/%2e%2e/%2e%2e/secret.txt",
        "/media/%2E%2E/%2E%2E/720p.mp4",
        "/media/01-demo-lessons/%2e%2e/720p.mp4",
        "/media/01-demo-lessons/01-sample/%2e%2e%2fsecret.txt",
        "/media/01-demo-lessons/01-sample/..%2fsecret.txt",
        "/media/01-demo-lessons/01-sample/..%2f..%2fsecret.txt",
        "/media/01-demo-lessons/01-sample/%252e%252e%252fsecret.txt",
        "/media/..%2f..%2f/01-sample/720p.mp4",
        "/media/01-demo-lessons/..%2f01-sample/720p.mp4",
        "/media/%2e%2e%2f%2e%2e%2f/x/lesson.json",
        # backslash separators (Windows)
        "/media/01-demo-lessons/01-sample/..%5csecret.txt",
        "/media/..%5c..%5c/01-sample/720p.mp4",
        "/media/01-demo-lessons/..%5c01-sample/720p.mp4",
        # absolute paths and drive letters
        "/media/%2fetc/passwd/720p.mp4",
        "/media//etc/passwd/720p.mp4",
        "/media/01-demo-lessons/%2fetc%2fpasswd/720p.mp4",
        "/media/01-demo-lessons/01-sample/%2fetc%2fpasswd",
        "/media/C:%5cWindows/System32/720p.mp4",
        "/media/01-demo-lessons/01-sample/C:%5csecret.txt",
        # NUL byte
        "/media/01-demo-lessons/01-sample/720p.mp4%00",
        "/media/01-demo-lessons%00/01-sample/720p.mp4",
    ],
)
def test_traversal_attempts_are_refused_with_404(client: TestClient, url: str) -> None:
    response = client.get(url)
    assert response.status_code == 404, url
    assert SECRET not in response.content
    assert "etc" not in response.text.lower() or "Not found" in response.text


@pytest.mark.parametrize(
    "name",
    [
        "captions.en.vtt",  # exists, but is not one of the public files
        "transcript.en.json",
        "chapters.json",
        "secret.txt",  # exists in the lesson folder
        "720p.mp4.bak",
        "720P.MP4",
        "Poster.jpg",
        "720p.mp4.",
        "720p.mp4%20",
        ".env",
        "..",
        ".",
    ],
)
def test_names_outside_the_three_public_files_are_refused(
    client: TestClient, name: str
) -> None:
    response = client.get(f"{LESSON_URL}/{name}")
    assert response.status_code == 404, name
    assert SECRET not in response.content


@pytest.mark.parametrize(
    "folder",
    [
        "01-demo-lessons/02-unfinished",  # no lesson.json: never served
        "01-demo-lessons/99-missing",
        "99-missing/01-sample",
        "01-Demo-Lessons/01-sample",  # upper case is not a valid lesson folder name
        "1-demo-lessons/01-sample",
        "01-demo lessons/01-sample",
        "01-demo--lessons/01-sample",
    ],
)
def test_unfinished_missing_or_malformed_lesson_folders_are_refused(
    client: TestClient, folder: str
) -> None:
    assert client.get(f"/media/{folder}/720p.mp4").status_code == 404


def test_only_get_is_routed(client: TestClient) -> None:
    for method in ("post", "put", "delete", "patch"):
        response = getattr(client, method)(f"{LESSON_URL}/720p.mp4")
        assert response.status_code == 405, method


def test_valid_range_returns_206_with_the_requested_bytes(client: TestClient) -> None:
    response = client.get(f"{LESSON_URL}/720p.mp4", headers={"Range": "bytes=10-19"})
    assert response.status_code == 206
    assert response.content == VIDEO_BYTES[10:20]
    assert response.headers["content-range"] == f"bytes 10-19/{len(VIDEO_BYTES)}"
    assert response.headers["content-length"] == "10"
    assert response.headers["accept-ranges"] == "bytes"
    assert response.headers["content-type"] == "video/mp4"


def test_open_ended_and_suffix_ranges(client: TestClient) -> None:
    size = len(VIDEO_BYTES)
    tail = client.get(f"{LESSON_URL}/720p.mp4", headers={"Range": "bytes=5000-"})
    assert tail.status_code == 206
    assert tail.content == VIDEO_BYTES[5000:]
    assert tail.headers["content-range"] == f"bytes 5000-{size - 1}/{size}"

    last = client.get(f"{LESSON_URL}/720p.mp4", headers={"Range": "bytes=-50"})
    assert last.status_code == 206
    assert last.content == VIDEO_BYTES[-50:]
    assert last.headers["content-range"] == f"bytes {size - 50}-{size - 1}/{size}"


def test_range_past_the_end_is_clamped_to_the_file(client: TestClient) -> None:
    size = len(VIDEO_BYTES)
    response = client.get(f"{LESSON_URL}/720p.mp4", headers={"Range": "bytes=0-999999"})
    assert response.status_code == 206
    assert response.content == VIDEO_BYTES
    assert response.headers["content-range"] == f"bytes 0-{size - 1}/{size}"


def test_range_starting_past_the_end_is_416(client: TestClient) -> None:
    size = len(VIDEO_BYTES)
    response = client.get(
        f"{LESSON_URL}/720p.mp4", headers={"Range": f"bytes={size}-{size + 10}"}
    )
    assert response.status_code == 416
    # Starlette 0.41.3 sends "*/<size>"; RFC 9110 says "bytes */<size>". A library quirk, not ours.
    assert response.headers["content-range"].endswith(f"*/{size}")


@pytest.mark.parametrize(
    "header",
    ["bytes=abc", "bytes=10-5", "bytes=", "items=0-9", "garbage"],
)
def test_malformed_or_inverted_range_is_not_served_as_content(
    client: TestClient, header: str
) -> None:
    response = client.get(f"{LESSON_URL}/720p.mp4", headers={"Range": header})
    assert response.status_code in (400, 416), header
    assert response.content != VIDEO_BYTES


def test_range_does_not_open_a_way_around_the_name_rules(client: TestClient) -> None:
    response = client.get(
        f"{LESSON_URL}/captions.en.vtt", headers={"Range": "bytes=0-3"}
    )
    assert response.status_code == 404

"""API tests: upload, progress, serving, traversal refusal. Needs fastapi and httpx (requirements-video-demo.txt)."""

import time
from pathlib import Path

import pytest
from conftest import needs_ffmpeg

# fastapi and httpx are not in the shared requirements files (see requirements-video-demo.txt). The generic
# `checks` job runs every test without them, so these API tests skip there (listed by `pytest -rs`).
# The `video-demo` job installs them and fails on any skip.
pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402
from lesson_processor import app as app_module  # noqa: E402


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("LESSON_OUTPUT_DIR", str(tmp_path / "out"))
    return TestClient(app_module.app)


def _wait(client: TestClient, job: str) -> dict:
    for _ in range(200):
        s = client.get(f"/api/jobs/{job}").json()
        if s["status"] != "running":
            return s
        time.sleep(0.2)
    raise AssertionError("job did not finish")


def test_rejects_bad_extension(client: TestClient) -> None:
    r = client.post("/api/jobs?filename=x.exe", content=b"abc")
    assert r.status_code == 415


@needs_ffmpeg
def test_fake_upload_fails_cleanly(client: TestClient) -> None:
    r = client.post("/api/jobs?filename=x.mp4", content=b"not a video" * 100)
    s = _wait(client, r.json()["job"])
    assert s["status"] == "failed" and "could not be read" in s["error"]
    assert client.get("/api/lessons").json() == []


@needs_ffmpeg
def test_upload_process_and_serve(client: TestClient, synthetic_video: Path) -> None:
    r = client.post(
        "/api/jobs?filename=sample.mp4&title=Demo%20lesson",
        content=synthetic_video.read_bytes(),
    )
    assert r.status_code == 202
    s = _wait(client, r.json()["job"])
    assert s["status"] == "done", s
    key = s["lesson"]
    video = client.get(f"/media/{key}/720p.mp4")
    assert video.status_code == 200 and len(video.content) > 1000
    assert client.get(f"/media/{key}/poster.jpg").status_code == 200
    assert client.get(f"/media/{key}/lesson.json").json()["title"] == "Demo lesson"
    assert (
        client.get(f"/media/{key}/captions.en.vtt").status_code == 404
    )  # not a public file
    ranged = client.get(f"/media/{key}/720p.mp4", headers={"Range": "bytes=0-99"})
    assert ranged.status_code == 206  # browsers can seek
    assert len(client.get("/api/lessons").json()) == 1


def test_media_refuses_traversal(client: TestClient) -> None:
    for url in (
        "/media/..%2f..%2f/x/lesson.json",
        "/media/01-a/01-b/../../x",
        "/media/99-x/01-y/secret.txt",
    ):
        assert client.get(url).status_code == 404

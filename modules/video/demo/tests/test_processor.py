"""Tests for the lesson processor demo. Media is generated with ffmpeg; nothing is committed."""

import json
import shutil
from pathlib import Path

import pytest
from conftest import needs_ffmpeg
from lesson_processor import processor as p
from media_paths import validate_relative_path


def _process(
    src: Path, root: Path, name: str = "sample.mp4", title: str = "Intro to Python"
):
    return p.process_video(src, name, title, root)


def test_unsupported_extension_rejected(tmp_path: Path) -> None:
    f = tmp_path / "notes.txt"
    f.write_text("hello")
    with pytest.raises(p.ProcessingError, match="Unsupported file type"):
        p.validate_input(f, "notes.txt")


def test_empty_file_rejected(tmp_path: Path) -> None:
    f = tmp_path / "a.mp4"
    f.write_bytes(b"")
    with pytest.raises(p.ProcessingError, match="empty"):
        p.validate_input(f, "a.mp4")


def test_oversize_rejected(tmp_path: Path) -> None:
    f = tmp_path / "a.mp4"
    f.write_bytes(b"x" * 100)
    with pytest.raises(p.ProcessingError, match="limit"):
        p.validate_input(f, "a.mp4", max_bytes=10)


@needs_ffmpeg
def test_fake_video_content_rejected(tmp_path: Path) -> None:
    """A text file renamed .mp4 passes the extension check but not the content check."""
    f = tmp_path / "fake.mp4"
    f.write_text("this is not a video" * 50)
    with pytest.raises(p.ProcessingError, match="could not be read"):
        p.validate_input(f, "fake.mp4")


@needs_ffmpeg
def test_supported_input_accepted(synthetic_video: Path) -> None:
    info = p.validate_input(synthetic_video, "x.MP4")
    assert info.height == 360 and info.audio_codec == "aac" and info.duration_s > 2


def test_safe_paths() -> None:
    folder = p.lesson_relative_folder(3, "intro")
    assert folder == "courses/demo/01-demo-lessons/03-intro/"
    assert validate_relative_path(folder.rstrip("/"))
    assert p.slugify("../../Evil Title!!") == "evil-title"
    assert p.slugify("???") == "lesson"


def test_safe_join_refuses_traversal(tmp_path: Path) -> None:
    for bad in ("../x", "a/../../x", "/abs", "C:/x", "a%2e%2e/x", "a\\b"):
        with pytest.raises(p.ProcessingError):
            p.safe_join(tmp_path, bad)
    assert p.safe_join(tmp_path, "courses/demo/x").is_relative_to(tmp_path.resolve())


@needs_ffmpeg
def test_end_to_end_conversion_poster_manifest(
    synthetic_video: Path, tmp_path: Path
) -> None:
    result = _process(synthetic_video, tmp_path)
    folder = result.folder
    assert sorted(x.name for x in folder.iterdir()) == sorted(
        ["720p.mp4", "poster.jpg", "lesson.json", "captions.en.vtt",
         "transcript.en.json", "chapters.json"]
    )  # fmt: skip
    out = p.probe(
        folder / "720p.mp4"
    )  # real conversion: 360p source became 720p H.264/AAC
    assert (out.video_codec, out.height, out.audio_codec) == ("h264", 720, "aac")
    poster = p.probe(folder / "poster.jpg")  # a real decodable image
    assert poster.height == 720
    manifest = json.loads((folder / "lesson.json").read_text())
    p.validate_manifest(manifest)  # real B6.3 schema
    assert manifest["lesson_id"] == "01-demo-lessons/01-intro-to-python"
    assert all(validate_relative_path(t["file"]) for t in manifest["tracks"])
    assert "http" not in json.dumps(manifest)  # relative paths only (C-08)
    assert not [x for x in tmp_path.iterdir() if x.name.startswith(".tmp-")]


@needs_ffmpeg
def test_second_lesson_does_not_overwrite_first(
    synthetic_video: Path, tmp_path: Path
) -> None:
    first = _process(synthetic_video, tmp_path)
    marker = first.folder / "720p.mp4"
    before = marker.stat().st_mtime_ns
    second = _process(synthetic_video, tmp_path)
    assert second.folder != first.folder
    assert marker.stat().st_mtime_ns == before
    assert len(p.list_lessons(tmp_path)) == 2


@needs_ffmpeg
def test_truncated_video_leaves_no_lesson(
    synthetic_video: Path, tmp_path: Path
) -> None:
    """A video cut off before its index is refused; no folder, manifest or temp dir remains."""
    broken = tmp_path / "broken.mp4"
    broken.write_bytes(
        synthetic_video.read_bytes()[: synthetic_video.stat().st_size // 2]
    )
    root = tmp_path / "out"
    with pytest.raises(p.ProcessingError):
        _process(broken, root, "broken.mp4")
    assert p.list_lessons(root) == []
    assert not root.exists() or not list(
        root.rglob("lesson.json")
    )  # rejected before any output


@needs_ffmpeg
def test_real_ffmpeg_failure_cleans_up(
    synthetic_video: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A real ffmpeg error (unknown encoder) after the temp folder exists leaves nothing behind."""
    real = p._run_ffmpeg

    def broken_encoder(cmd: list[str], *args: object) -> None:
        real([*cmd[:-1], "-c:v", "no_such_encoder", cmd[-1]], *args)  # type: ignore[arg-type]

    monkeypatch.setattr(p, "_run_ffmpeg", broken_encoder)
    root = tmp_path / "out"
    with pytest.raises(p.ProcessingError, match="FFmpeg failed"):
        _process(synthetic_video, root)
    assert p.list_lessons(root) == []
    assert list(root.iterdir()) == []


@needs_ffmpeg
def test_ffmpeg_failure_is_reported_and_cleaned(
    synthetic_video: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Force ffmpeg itself to fail: no partial package is reported as complete."""
    real = p.transcode_720p

    def bad(source: Path, dest: Path, info: p.MediaInfo, progress: object) -> None:
        dest.write_bytes(b"partial")  # a half-written output exists when the step fails
        raise p.ProcessingError(
            "FFmpeg failed during 'Converting to 720p'. Try another file."
        )

    monkeypatch.setattr(p, "transcode_720p", bad)
    root = tmp_path / "out"
    with pytest.raises(p.ProcessingError, match="FFmpeg failed"):
        _process(synthetic_video, root)
    assert p.list_lessons(root) == []
    assert list(root.iterdir()) == []
    monkeypatch.setattr(p, "transcode_720p", real)


def test_manifest_without_required_field_is_rejected() -> None:
    m = p.build_manifest("01-demo-lessons/01-x", "X", 3.0)
    p.validate_manifest(m)
    del m["chapters"]
    with pytest.raises(p.ProcessingError, match="invalid"):
        p.validate_manifest(m)
    m2 = p.build_manifest("01-demo-lessons/01-x", "X", 3.0)
    m2["tracks"][0]["file"] = "../evil.mp4"
    with pytest.raises(p.ProcessingError):
        p.validate_manifest(m2)


def test_list_lessons_ignores_unfinished_folder(tmp_path: Path) -> None:
    folder = tmp_path / "courses" / "demo" / "01-demo-lessons" / "01-half"
    folder.mkdir(parents=True)
    (folder / "720p.mp4").write_bytes(b"partial")  # no lesson.json: not complete
    assert p.list_lessons(tmp_path) == []
    shutil.rmtree(folder)

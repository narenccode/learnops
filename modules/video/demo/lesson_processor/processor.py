"""Turn one uploaded lecture video into a lesson folder: 720p.mp4, poster.jpg, lesson.json.

Rules followed (modules/video/CLAUDE.md): paths come from `media_paths`; the manifest is checked
against the real B6.3 schema; everything is built in a temp folder inside the output root and
moved into place with one rename; `lesson.json` is written last. A failed run leaves no lesson.
"""

from __future__ import annotations

import json
import logging
import os
import posixpath
import re
import shutil
import subprocess
import tempfile
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from media_paths import course_lesson_path, validate_relative_path, validate_slug

log = logging.getLogger("lesson_processor")

REPO = Path(__file__).resolve().parents[4]
MANIFEST_SCHEMA = REPO / "contracts" / "lesson-manifest.v1.schema.json"

COURSE_SLUG = "demo"
MODULE_NUMBER = 1
MODULE_SLUG = "demo-lessons"
PIPELINE_VERSION = "demo-0.1"

# Fixed file names (PRD B6.2). The task text says `lesson.mp4`; the PRD says `720p.mp4`: PRD wins.
VIDEO_FILE = "720p.mp4"
POSTER_FILE = "poster.jpg"
MANIFEST_FILE = "lesson.json"
CAPTIONS_FILE = "captions.en.vtt"
TRANSCRIPT_FILE = "transcript.en.json"
CHAPTERS_FILE = "chapters.json"
SERVED_FILES = frozenset({VIDEO_FILE, POSTER_FILE, MANIFEST_FILE})

ALLOWED_EXTENSIONS = frozenset({".mp4", ".mov", ".mkv", ".webm"})  # FR-V-01
# ffprobe `format_name` values of those containers: content is checked, not only the extension.
ALLOWED_CONTAINERS = frozenset({"mov", "mp4", "matroska", "webm"})
MAX_UPLOAD_BYTES = 4 * 1024**3  # FR-V-01: max file 4 GB
FFMPEG_TIMEOUT_S = 3600
TARGET_HEIGHT = 720

Progress = Callable[[str, float], None]


class ProcessingError(Exception):
    """A failure whose message says what happened and what to do next (PRD UI-05)."""


@dataclass(frozen=True)
class MediaInfo:
    container: str
    duration_s: float
    width: int
    height: int
    video_codec: str
    audio_codec: str | None
    size_bytes: int


@dataclass(frozen=True)
class LessonResult:
    lesson_key: str  # "<module folder>/<lesson folder>", relative to the course folder
    folder: Path
    manifest: dict[str, Any]


def find_tool(name: str) -> str:
    """Locate ffmpeg / ffprobe: env FFMPEG_PATH / FFPROBE_PATH first, then PATH."""
    explicit = os.environ.get(f"{name.upper()}_PATH")
    found = explicit if explicit and Path(explicit).is_file() else shutil.which(name)
    if not found:
        raise ProcessingError(
            f"{name} was not found. Install FFmpeg (Windows: `winget install Gyan.FFmpeg`), "
            f"open a new terminal, or set {name.upper()}_PATH to the executable."
        )
    return found


def ffmpeg_available() -> bool:
    try:
        find_tool("ffmpeg")
        find_tool("ffprobe")
    except ProcessingError:
        return False
    return True


def probe(path: Path) -> MediaInfo:
    """Inspect a media file with ffprobe. Raises ProcessingError if it is not readable media."""
    cmd = [
        find_tool("ffprobe"), "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ]  # fmt: skip
    done = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
    if done.returncode != 0:
        raise ProcessingError(
            "The file could not be read as a video. Choose another video file."
        )
    try:
        data = json.loads(done.stdout)
        streams = data.get("streams", [])
        video = next(s for s in streams if s.get("codec_type") == "video")
        audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
        fmt = data["format"]
        return MediaInfo(
            container=str(fmt.get("format_name", "")),
            duration_s=float(fmt.get("duration") or video.get("duration") or 0),
            width=int(video["width"]),
            height=int(video["height"]),
            video_codec=str(video.get("codec_name", "")),
            audio_codec=str(audio["codec_name"]) if audio else None,
            size_bytes=int(fmt.get("size") or path.stat().st_size),
        )
    except (StopIteration, KeyError, ValueError, json.JSONDecodeError):
        raise ProcessingError(
            "The file has no usable video track. Choose another file."
        ) from None


def validate_input(
    path: Path, original_name: str, max_bytes: int = MAX_UPLOAD_BYTES
) -> MediaInfo:
    """Check extension, size and (via ffprobe) the real content before any processing."""
    if Path(original_name).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ProcessingError(
            "Unsupported file type. Upload an .mp4, .mov, .mkv or .webm file."
        )
    size = path.stat().st_size
    if size == 0:
        raise ProcessingError("The file is empty. Choose a video file with content.")
    if size > max_bytes:
        raise ProcessingError(
            f"The file is larger than the {max_bytes // 1024**2} MB limit. Use a smaller file."
        )
    info = probe(path)
    if not ALLOWED_CONTAINERS.intersection(info.container.split(",")):
        raise ProcessingError("The file content is not an mp4, mov, mkv or webm video.")
    if info.duration_s <= 0:
        raise ProcessingError(
            "The video has no duration. Choose a different recording."
        )
    return info


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40].strip("-")
    return slug if validate_slug(slug) else "lesson"


_allocation_lock = threading.Lock()


def _next_lesson_number(module_dir: Path) -> int:
    used: set[int] = set()
    if module_dir.is_dir():
        used = {int(p.name[:2]) for p in module_dir.glob("[0-9][0-9]-*")}
    for number in range(1, 100):
        if number not in used:
            return number
    raise ProcessingError(
        "This demo course already has 99 lessons. Delete one to add another."
    )


def lesson_relative_folder(lesson_number: int, lesson_slug: str) -> str:
    """Folder below the media root, built only by `media_paths` (no string concatenation)."""
    folder = course_lesson_path(
        COURSE_SLUG, MODULE_NUMBER, MODULE_SLUG, lesson_number, lesson_slug
    )
    if not validate_relative_path(folder.rstrip("/")):
        raise ProcessingError("Internal error: the lesson folder is not a safe path.")
    return folder


def safe_join(root: Path, relative: str) -> Path:
    """Join a validated relative path to root; refuse anything that resolves outside root."""
    if not validate_relative_path(relative.rstrip("/")):
        raise ProcessingError("That path is not allowed.")
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ProcessingError("That path is not allowed.")
    return target


def _run_ffmpeg(
    cmd: list[str], duration_s: float, progress: Progress | None, step: str
) -> None:
    """Run ffmpeg, reading `-progress` output for a percentage. Raises ProcessingError on failure."""
    with tempfile.TemporaryFile() as err:
        proc = subprocess.Popen(  # fixed argument list, no shell
            cmd, stdout=subprocess.PIPE, stderr=err, text=True, stdin=subprocess.DEVNULL
        )
        timer = threading.Timer(FFMPEG_TIMEOUT_S, proc.kill)
        timer.start()
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                key, _, value = line.strip().partition("=")
                if key == "out_time_us" and progress and value.isdigit():
                    progress(step, max(0.0, min(1.0, int(value) / 1e6 / duration_s)))
            code = proc.wait()
        finally:
            timer.cancel()
            if proc.poll() is None:
                proc.kill()
        if code != 0:
            err.seek(0)
            tail = err.read().decode("utf-8", "replace").strip().splitlines()[-1:]
            log.error(
                json.dumps(
                    {"event": "ffmpeg_failed", "step": step, "code": code, "tail": tail}
                )
            )
            raise ProcessingError(
                f"FFmpeg failed during '{step}'. The video may be damaged; try another file."
            )


def transcode_720p(
    source: Path, dest: Path, info: MediaInfo, progress: Progress | None
) -> None:
    cmd = [
        find_tool("ffmpeg"), "-nostdin", "-y", "-v", "error", "-i", str(source),
        "-map", "0:v:0", "-map", "0:a:0?",
        "-vf", f"scale=-2:{TARGET_HEIGHT}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
        "-progress", "pipe:1", "-nostats", str(dest),
    ]  # fmt: skip
    _run_ffmpeg(cmd, info.duration_s, progress, "Converting to 720p")


def extract_poster(source: Path, dest: Path, info: MediaInfo) -> None:
    """One frame from 10% into the video (skips black intro frames), scaled like the video."""
    cmd = [
        find_tool("ffmpeg"), "-nostdin", "-y", "-v", "error",
        "-ss", f"{info.duration_s * 0.1:.2f}", "-i", str(source),
        "-frames:v", "1", "-vf", f"scale=-2:{TARGET_HEIGHT}", "-q:v", "3", str(dest),
    ]  # fmt: skip
    _run_ffmpeg(cmd, info.duration_s, None, "Extracting poster")
    if not dest.is_file() or dest.stat().st_size == 0:
        raise ProcessingError("No poster frame could be extracted. Try another video.")


def verify_output(video: Path, source_info: MediaInfo) -> MediaInfo:
    out = probe(video)
    if out.video_codec != "h264" or out.height != TARGET_HEIGHT:
        raise ProcessingError(
            "The converted video is not 720p H.264. Please try again."
        )
    if source_info.audio_codec and out.audio_codec != "aac":
        raise ProcessingError("The converted video lost its audio. Please try again.")
    if abs(out.duration_s - source_info.duration_s) > 2.0:
        raise ProcessingError(
            "The converted video has the wrong length. Please try again."
        )
    return out


def build_manifest(lesson_key: str, title: str, duration_s: float) -> dict[str, Any]:
    """B6.3 manifest. captions, transcript and chapters are required by the schema; the demo
    writes them EMPTY (no transcription here). `source` holds no user name or file name."""
    return {
        "schema": "learnops.lesson/v1",
        "course_slug": COURSE_SLUG,
        "lesson_id": lesson_key,
        "title": title,
        "duration_s": round(duration_s, 2),
        "tracks": [{"role": "main", "file": VIDEO_FILE, "height": TARGET_HEIGHT}],
        "captions": [{"lang": "en", "file": CAPTIONS_FILE}],
        "transcript": TRANSCRIPT_FILE,
        "chapters": CHAPTERS_FILE,
        "source": {"kind": "upload"},
        "processing": {
            "pipeline_version": PIPELINE_VERSION,
            "completed_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }


def validate_manifest(manifest: dict[str, Any]) -> None:
    """Check against the real B6.3 schema, then the path rule for every file it names."""
    schema = json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(manifest), key=lambda e: list(e.path)
    )
    if errors:
        where = "/".join(str(p) for p in errors[0].path) or "(root)"
        raise ProcessingError(
            f"The lesson manifest is invalid at '{where}'. Report this bug."
        )
    files = [t["file"] for t in manifest["tracks"]] + [
        c["file"] for c in manifest["captions"]
    ]
    files += [manifest["transcript"], manifest["chapters"]]
    if not all(validate_relative_path(f) for f in files):
        raise ProcessingError(
            "The lesson manifest names an unsafe path. Report this bug."
        )


def process_video(
    source: Path,
    original_name: str,
    title: str,
    output_root: Path,
    progress: Progress | None = None,
    max_bytes: int = MAX_UPLOAD_BYTES,
) -> LessonResult:
    """Validate, convert, extract a poster, write lesson.json last, move into place atomically."""
    report: Progress = progress or (lambda _step, _fraction: None)
    report("Checking the video", 0.0)
    info = validate_input(source, original_name, max_bytes)

    output_root.mkdir(parents=True, exist_ok=True)
    work = (
        output_root / f".tmp-{uuid.uuid4().hex}"
    )  # same drive as the target: rename is atomic
    work.mkdir()
    try:
        transcode_720p(source, work / VIDEO_FILE, info, report)
        report("Extracting poster", 0.0)
        extract_poster(source, work / POSTER_FILE, info)
        out = verify_output(work / VIDEO_FILE, info)

        clean_title = title.strip()[:120] or "Untitled lesson"
        (work / CAPTIONS_FILE).write_text("WEBVTT\n", encoding="utf-8")
        (work / TRANSCRIPT_FILE).write_text('{"segments": []}\n', encoding="utf-8")
        (work / CHAPTERS_FILE).write_text("[]\n", encoding="utf-8")

        with _allocation_lock:  # number allocation and rename together: no two lessons collide
            module_dir = (
                output_root
                / "courses"
                / COURSE_SLUG
                / f"{MODULE_NUMBER:02d}-{MODULE_SLUG}"
            )
            number = _next_lesson_number(module_dir)
            folder_rel = lesson_relative_folder(number, slugify(clean_title))
            final = safe_join(output_root, folder_rel)
            if final.exists():
                raise ProcessingError(
                    "That lesson already exists; nothing was overwritten."
                )
            lesson_key = posixpath.relpath(
                folder_rel.rstrip("/"), f"courses/{COURSE_SLUG}"
            )
            manifest = build_manifest(lesson_key, clean_title, out.duration_s)
            validate_manifest(manifest)
            # lesson.json last: only when every required file exists (FR-V-08).
            needed = [
                VIDEO_FILE,
                POSTER_FILE,
                CAPTIONS_FILE,
                TRANSCRIPT_FILE,
                CHAPTERS_FILE,
            ]
            if not all((work / name).is_file() for name in needed):
                raise ProcessingError(
                    "Some lesson files are missing. Nothing was published."
                )
            (work / MANIFEST_FILE).write_text(
                json.dumps(manifest, indent=2) + "\n", "utf-8"
            )
            final.parent.mkdir(parents=True, exist_ok=True)
            work.rename(final)
        report("Done", 1.0)
        log.info(json.dumps({"event": "lesson_ready", "lesson": lesson_key}))
        return LessonResult(lesson_key, final, manifest)
    except BaseException:
        shutil.rmtree(
            work, ignore_errors=True
        )  # never leave a half-built lesson behind
        raise


def list_lessons(output_root: Path) -> list[dict[str, Any]]:
    """Completed lessons only: a folder counts if its valid lesson.json exists (written last)."""
    found: list[dict[str, Any]] = []
    base = output_root / "courses" / COURSE_SLUG
    for manifest_path in sorted(base.glob("*/*/" + MANIFEST_FILE)):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            validate_manifest(manifest)
        except (OSError, ValueError, ProcessingError):
            continue
        found.append(manifest)
    return found

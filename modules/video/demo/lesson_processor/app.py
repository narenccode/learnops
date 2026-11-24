"""Local web app for the lesson processor demo (FastAPI).

Browser picks a file and sends its bytes; the server never reveals or accepts a server path.
Processing runs in a background thread: a demo stand-in for the job queue (OPS-10, not built).
Run:  PYTHONPATH=libs:modules/video/demo python -m uvicorn lesson_processor.app:app
"""

from __future__ import annotations

import os
import re
import tempfile
import threading
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from media_paths import validate_slug

from lesson_processor import processor as proc

STATIC = Path(__file__).parent / "static"
LESSON_PART = re.compile(r"^\d\d-[a-z0-9]+(-[a-z0-9]+)*$")

app = FastAPI(title="LearnOps lesson processor demo")
_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = threading.Lock()


def output_root() -> Path:
    return Path(
        os.environ.get("LESSON_OUTPUT_DIR", proc.REPO / "processed-lessons")
    ).resolve()


def max_bytes() -> int:
    return int(os.environ.get("LESSON_MAX_UPLOAD_BYTES", proc.MAX_UPLOAD_BYTES))


def _update(job_id: str, **fields: Any) -> None:
    with _jobs_lock:
        _jobs[job_id].update(fields)


def _run_job(job_id: str, source: Path, name: str, title: str) -> None:
    def progress(step: str, fraction: float) -> None:
        _update(job_id, step=step, progress=round(fraction, 3))

    try:
        result = proc.process_video(
            source, name, title, output_root(), progress, max_bytes()
        )
        _update(
            job_id, status="done", step="Done", progress=1.0, lesson=result.lesson_key
        )
    except proc.ProcessingError as error:
        _update(job_id, status="failed", error=str(error))
    except Exception:  # unexpected: do not leak internals to the browser
        proc.log.exception("job_crashed")
        _update(
            job_id,
            status="failed",
            error="Something went wrong. Try again or use another file.",
        )
    finally:
        source.unlink(missing_ok=True)  # the raw upload is not kept


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ffmpeg": proc.ffmpeg_available()}


@app.post("/api/jobs")
async def create_job(
    request: Request, filename: str = "", title: str = ""
) -> JSONResponse:
    """Body = raw file bytes. `filename` is only used for its extension and is never stored."""
    if not proc.ffmpeg_available():
        raise HTTPException(
            503, "FFmpeg is not installed on the server. See the demo README."
        )
    name = Path(filename.replace("\\", "/")).name
    if Path(name).suffix.lower() not in proc.ALLOWED_EXTENSIONS:
        raise HTTPException(
            415, "Unsupported file type. Upload an .mp4, .mov, .mkv or .webm file."
        )
    limit = max_bytes()
    root = output_root()
    root.mkdir(parents=True, exist_ok=True)
    incoming = (
        Path(tempfile.mkdtemp(prefix=".incoming-", dir=root))
        / f"upload{Path(name).suffix.lower()}"
    )
    size = 0
    try:
        with incoming.open("wb") as out:
            async for chunk in request.stream():
                size += len(chunk)
                if size > limit:
                    raise HTTPException(
                        413, f"The file is larger than the {limit // 1024**2} MB limit."
                    )
                out.write(chunk)
    except BaseException:
        incoming.unlink(missing_ok=True)
        incoming.parent.rmdir()
        raise
    job_id = uuid.uuid4().hex
    with _jobs_lock:
        _jobs[job_id] = {
            "status": "running",
            "step": "Queued",
            "progress": 0.0,
            "error": None,
            "lesson": None,
        }

    def work() -> None:
        _run_job(job_id, incoming, name, title or Path(name).stem)
        incoming.parent.rmdir()

    threading.Thread(target=work, daemon=True).start()
    return JSONResponse({"job": job_id}, status_code=202)


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str) -> dict[str, Any]:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            raise HTTPException(404, "Unknown job. Start processing again.")
        return dict(job)


@app.get("/api/lessons")
def lessons() -> list[dict[str, Any]]:
    return proc.list_lessons(output_root())


@app.get("/media/{module_dir}/{lesson_dir}/{name}")
def media(module_dir: str, lesson_dir: str, name: str) -> FileResponse:
    """Serve only the three public files of a completed lesson (supports Range for seeking)."""
    if not (LESSON_PART.match(module_dir) and LESSON_PART.match(lesson_dir)):
        raise HTTPException(404, "Not found.")
    if name not in proc.SERVED_FILES:
        raise HTTPException(404, "Not found.")
    rel = f"courses/{proc.COURSE_SLUG}/{module_dir}/{lesson_dir}/{name}"
    try:
        path = proc.safe_join(output_root(), rel)
    except proc.ProcessingError:
        raise HTTPException(404, "Not found.") from None
    manifest = path.with_name(proc.MANIFEST_FILE)
    if (
        not manifest.is_file() or not path.is_file()
    ):  # unfinished lessons are never served
        raise HTTPException(404, "Not found.")
    return FileResponse(path)


assert validate_slug(proc.COURSE_SLUG)

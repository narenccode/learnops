# Lesson processor demo (limited, local)

Converts one lecture video to `720p.mp4` (H.264/AAC), extracts `poster.jpg`, writes `lesson.json`
(B6.3, validated against `contracts/lesson-manifest.v1.schema.json`) and plays it in a browser page.
**Local demo only. Not the production Video pipeline, and not safe to expose to a network:** it has
no authentication or authorisation. Design doc `docs/design/video.md` is still Draft; this is a
demo beside `paths_demo.py`, not Release 3 work.

Reuses: `libs/media_paths` (folder via `course_lesson_path`, `validate_relative_path`,
`validate_slug`) and the B6.3 schema. No contract or library was changed.

## Setup (Windows)
```powershell
winget install Gyan.FFmpeg          # then open a NEW terminal; check: ffmpeg -version ; ffprobe -version
pip install -r requirements.txt -r requirements-dev.txt -r requirements-video-demo.txt
# requirements-video-demo.txt: fastapi, uvicorn, httpx (demo and its tests only)
```
## Run (from the repository root, PowerShell)
```powershell
$env:PYTHONPATH = "libs;modules/video/demo"
python -m uvicorn lesson_processor.app:app --port 8765
```
Open http://127.0.0.1:8765, choose a video, press **Process lesson**.

## Output (git-ignored, under `processed-lessons/`)
`courses/demo/01-demo-lessons/NN-<slug>/` with `720p.mp4`, `poster.jpg`, `lesson.json`, plus
**empty placeholders** `captions.en.vtt`, `transcript.en.json`, `chapters.json` (the schema
requires them; transcription is out of scope). The file is `720p.mp4`, not `lesson.mp4`: PRD B6.2.

## Flow
upload (raw body, size-limited) -> extension + ffprobe content check -> ffmpeg 720p -> poster at 10%
-> verify output (h264, 720 high, aac, duration) -> files in `.tmp-*` folder -> manifest validated,
`lesson.json` written last -> one atomic rename into a new numbered folder. Any failure deletes the
temp folder; the list/serve code only treats folders with `lesson.json` as lessons.

## Tests
`python -m pytest modules/video/demo/tests -v -rs`. The tests need ffmpeg and ffprobe on PATH (or
`FFMPEG_PATH` / `FFPROBE_PATH`), plus fastapi, uvicorn and httpx (`requirements-video-demo.txt`).
Without ffmpeg the ffmpeg tests, and without httpx the API tests, are **skipped** locally; the `video-demo` job in
`.github/workflows/ci.yml` installs ffmpeg and fails if any test is skipped. Media is generated
synthetically. `test_media_security.py` covers what the `/media` route does with traversal
attempts, unexpected names and Range requests; it does not make the route safe to expose.

## Limitations (what this demo is not)
- **No authentication or authorisation.** Anyone who can reach the port can upload, list and read
  every finished lesson (`/media`). Run it on localhost only. No per-user or per-course access.
- **No Moodle or LTI integration** (no launch, no course context, no learner or mentor roles).
- **No resumable (tus) upload (module rule 4 of `modules/video/CLAUDE.md` is not met).** One request carries the whole file; no 90 MB chunks, no resume.
- **No persistent background queue (module rule 5 and OPS-10 are not met).** A thread in the web process does the work; job state is in
  memory and is lost on restart.
- **ffmpeg licence status (PRD C-11).** The demo runs ffmpeg as a separate program and encodes with
  `libx264`, which is a **GPL** encoder; the Windows build named above and the `apt` package in CI are
  typically built with it. That build was **not checked against C-11 and is not an approved
  production build**: it is for local demonstration only. The Video design (`docs/design/video.md`,
  Q10) requires an LGPL build with no GPL-only parts for the pipeline, to be confirmed from the lab
  image's `ffmpeg -version` output. Do not read this demo's encoder as the pipeline's. The guide granted a narrow, recorded exception for this demo only, which is the licence record for its ffmpeg: `docs/decisions/0013-video-demo-ffmpeg-libx264-exception.md`. It ends when the demo is removed or replaced by the pipeline and is not a precedent.
- **No production deployment configuration.** No Dockerfile, Compose file, worker container,
  storage adapter or TLS. ffmpeg is installed by hand (Windows steps above) and in the CI job.
- **No generated captions, transcript or chapters.** `captions.en.vtt`, `transcript.en.json` and
  `chapters.json` are empty placeholders so the B6.3 manifest is valid. No summary, slide index,
  360p, camera/screen tracks, retention or BigBlueButton intake; `source.uploaded_by` is not set.
- Requirement coverage is partial: see the demo section of `docs/traceability.md`.

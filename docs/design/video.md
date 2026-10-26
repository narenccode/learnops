# Design document: Video pipeline

**Module:** video — Student 4, Video Pipeline
**Owner:** Nagashree V (GitHub: vnaags) · **Peer reviewer:** Harshithamanjunatha
**Release(s):** Release 3 (core), Release 5 (stretch)
**Status:** Draft

`Status` values: `Draft` → `In review` (peer reviewing) → `Approved`. **Only the guide sets
`Approved`**, in a pull request the guide merges. Feature code for this module starts only when the
status is `Approved` (foundation work listed in §13 under "Release 0" is allowed earlier).

> Reading key: the design content is taken from `docs/PRD.md` (section given in brackets); the
> structure follows `docs/design/TEMPLATE.md`. This document makes no design choices of its own.

## 1. Purpose and scope

The video pipeline accepts large lecture videos and live-class recordings and processes them into the standard lesson folder (B6), with captions, transcript, chapters, summary, slide index and manifest, ready for Moodle to play by relative path. It is built so the future dual-stream player (F-1) needs no rework [§C4.1]. A mentor uploads a 700 MB lecture from the browser and the upload resumes if the connection drops; a live-class recording appears in the right course folder with captions and chapters without the mentor doing anything; the mentor sees the processing status of every lesson and can fix a wrong chapter title; an administrator can re-run processing for a lesson after a pipeline upgrade [§C4.2].

**PRD chapter and goals:** PRD §C4 — Video pipeline; problem P4 (videos are hard to handle and to use: large files are hard to upload; lectures and live-class recordings have no captions, chapters or index) [§A2]. Goals [§A3], all delivered in Release 3: G-6 — caption word error rate on Indian-English lectures (B8.5), measured and reported, target fixed in Release 0; G-7 — time from a 90-min recording becoming available to captions, chapters and index ready ≤ 30 min; G-8 — a 700 MB file through a proxy that limits requests to 100 MB, with one interruption, succeeds and resumes.

**Out of scope** (PRD §C4.11, complete list): the dual-stream player (F-1) and importing BigBlueButton's separate streams (F-2), both of which belong to the extension track (§C6); live streaming; video editing.

## 2. Requirements covered

Requirement wording is copied from PRD §C4.3. The "approach" and "components" columns repeat only what other PRD sections state about the requirement.

| Requirement | Release | Approach in one line | Main components |
|---|---|---|---|
| FR-V-01: Resumable chunked upload (tus protocol), chunk size configurable (default 90 MB, below a 100 MB proxy limit), max file 4 GB; accepts mp4, mov, mkv, webm. | R3 | Upload page with drag-and-drop, per-file progress, resume after reload [§C4.4]; size limit, type check by content, stored outside any web root until processed [SEC-05]. | Upload page [§C4.4]; `video.upload` [§C4.5] |
| FR-V-02: Upload form chooses course (from LTI context), module and lesson (number + title → slug); accepts optional `camera` and `screen` tracks (stored and listed, not processed beyond validation in v1). | R3 | Lesson folder follows the B6.1 path template; slugs lowercase ASCII, hyphens, immutable [§B6.1]; `camera`/`screen` are reserved track roles [§B6.3]. | Upload page [§C4.4] |
| FR-V-03: Transcode to `720p.mp4` (H.264/AAC) when needed; optional `360p.mp4`; extract `poster.jpg`. | R3 | ffmpeg for transcode and poster [§C4.5] in worker containers [OPS-10]; `360p.mp4` behind a feature flag [§B6.2]. | Workers; ffmpeg |
| FR-V-04: Transcribe via B5.4; write `transcript.en.json` and `captions.en.vtt`. | R3 | `speech.transcribe(audio_path, language="en")` [§B5.4]; transcript in the B5.4 segment shape [§B6.2]; transcription runs in workers [OPS-10]. | Workers; speech interface |
| FR-V-05: Chapters via B5.1 from the transcript; write `chapters.json`; mentor can edit titles. | R3 | `model.run(task, inputs, output_schema)` [§B5.1]; `chapters.json` is `[{start, end, title}]` [§B6.2]; chapters editable on the lesson detail page [§C4.4]. | Model interface; lesson detail page |
| FR-V-06: Summary via B5.1; write `summary.en.md` (feature flag). | R3 | `model.run` [§B5.1]; optional file behind a feature flag [§B6.2]. | Model interface |
| FR-V-07: Slide index: detect slide changes, write `slides.json` and thumbnails (feature flag, on by default). | R3 | ffmpeg for scene detection [§C4.5] in workers [OPS-10]; `slides.json` is `[{t, thumb, text?}]`, thumbnails 320 px wide [§B6.2]. | Workers; ffmpeg |
| FR-V-08: Write `lesson.json` (B6.3) last, only when all required files exist. | R3 | Outputs written to a temporary folder and moved into place atomically [§C4.5]; partial outputs never exposed [§C4.8]. | TO DECIDE |
| FR-V-09: BigBlueButton intake: poll recordings via the BigBlueButton API (shared secret), fetch the **video** format output, map it to course and cohort using the recording metadata set by Moodle's BigBlueButton activity, and process it into the live-class path. | R3 | Live-class path `courses/{course_slug}/live-{cohort}/{nn}-{topic_slug}/` [§B6.1]; lab BigBlueButton has the video recording format enabled [§A11]; metadata fields verified in Release 0 [App-C 4]. | TO DECIDE |
| FR-V-10: Status page per course: queued / processing (step) / ready / failed, with retry. | R3 | Failed step shown with reason and retry [§C4.8]; long operations show progress and can be left and resumed [UI-04]. | Status list [§C4.4]; `video.job`, `video.step` [§C4.5] |
| FR-V-11: Re-process a lesson (new `pipeline_version`) without changing its path or deleting the previous outputs until the new ones are complete. | R3 | `pipeline_version` is recorded in the manifest's `processing` object [§B6.3]. | TO DECIDE |
| FR-V-12: Storage adapter: local folder or S3-compatible bucket, chosen by configuration (EXT-04). | R3 | Swapping a backend is configuration, not code [EXT-04]. | Storage adapter |
| FR-V-13: Embed snippet: give the mentor the relative path and an HTML snippet (video + captions track) to paste into a Moodle Page. | R3 | Copy-snippet button on the lesson detail page [§C4.4]; media stored by relative path [C-08]. | Lesson detail page [§C4.4] |
| FR-V-14: *(Stretch)* Checkpoint questions per chapter via B5 → B7 items (separate activity) and `cues.json` entries. | R5 | AI-drafted only, mentor-approved, ungraded; starts only when Releases 1–4 meet their exit criteria [§C5]. | TO DECIDE |
| FR-V-15: Retention: raw uploads and BigBlueButton intake files are deleted a configurable number of days after the lesson is ready (default 30); published lesson folders are never deleted automatically; a CLI lists and, with confirmation, removes lessons older than a configurable age (default off). | R3 | CLI with `--dry-run`, `--check` and a documented undo [C-05, OPS-05]. | CLI |

Deferrals: none. FR-V-14 is Release 5 by the PRD [§C4.10].

Release 3 also includes a harness smoke test for this module [§D1]. The integration harness is Module 2's [§C2].

## 3. Architecture

The diagram shows only the components and flows named in PRD §A8, §A10, §C4.5, OPS-10 and FR-V-12. Which part of the module polls BigBlueButton, and how the parts inside the module exchange work, are open (OQ-19, OQ-20).

```mermaid
flowchart LR
    MENTOR(["Mentor / Admin"]) -->|launch from course| MOODLE["Moodle 4.5 / 5.3<br/>(unmodified)"]
    MOODLE -->|LTI 1.3 launch| LTI["libs/lti"]
    subgraph M4["M4 Video pipeline"]
        SVC["Video service<br/>(FastAPI; serves React static build)"]
        Q[("Job queue<br/>(persistent state)")]
        WORKER["Worker containers<br/>(ffmpeg)"]
        Q -->|feeds| WORKER
    end
    LTI --> SVC
    BBB["BigBlueButton 3.0<br/>(unmodified)"] -->|"recordings (API)"| M4
    M4 --> MI["libs/model_interface<br/>(B5: LLM + speech)"]
    MI --> AI["AI providers<br/>local (lab) or hosted API"]
    M4 -->|storage adapter| MEDIA[("Media store<br/>local folder or S3-compatible<br/>(path template B6)")]
    M4 --> STORE[("PostgreSQL 16<br/>tool database")]
    MOODLE -->|plays media by relative path| MEDIA
```

| Part | Kind | Notes |
|---|---|---|
| Video service | Web service (FastAPI) [§A10] | Exposes `GET /health` [OPS-03]. Transcoding, transcription and scene detection never run inside web request handlers [OPS-10]. |
| Front end | React + TypeScript, built to static files served by the tool [§A10] | Upload page (drag-and-drop, per-file progress, resume after reload); status list; lesson detail (chapters editable, slide thumbnails, captions preview, copy-snippet button). Meets A14 [§C4.4]. |
| Job queue | Persistent state; survives restart [§C4.5] | Feeds the workers [OPS-10]. |
| Workers | Worker containers [OPS-10] | ffmpeg for transcode, poster and scene detection [§C4.5]. Steps are idempotent (re-running a step overwrites only its own outputs); outputs are written to a temporary folder and moved into place atomically [§C4.5]. Can run on a different host by configuration alone [OPS-10]. |
| Storage adapter | Adapter [EXT-04] | Local folder or S3-compatible bucket, chosen by configuration [FR-V-12]. |
| Retention CLI | CLI | Lists and, with confirmation, removes lessons older than a configurable age [FR-V-15]. |
| Shared libraries used | `libs/lti`, `libs/model_interface`, `libs/contracts`, `libs/media_paths` [EXT-09] | Modules import them and never copy code [EXT-09]. |

**Where the video pipeline touches other systems (PRD C-02):**
- **Moodle:** LTI 1.3 launches [§B3]; Moodle plays media by relative path [§A8]; the mentor pastes an HTML snippet into a Moodle Page [FR-V-13]. Moodle is never modified [C-01].
- **BigBlueButton:** its API, with a shared secret; the **video** format output [FR-V-09]. BigBlueButton is never modified [C-01].
- **Model interface:** all AI calls through the model interface, all speech-to-text through the speech interface [C-10].
- **Media store:** through the storage adapter [FR-V-12]; relative paths only [C-08].

**Worker on a separate host [OPS-10]:** workers can be deployed on a different host from the web services by configuration alone. How files are shared across hosts is OQ-21.

## 4. Contracts

| Contract | Provided / used | Fields or functions I rely on | Change needed? |
|---|---|---|---|
| B6 Media paths and lesson manifest | Provided (owner: Student 4) [§B.0] | Path templates `courses/{course_slug}/{module_nn}-{module_slug}/{lesson_nn}-{lesson_slug}/` and `courses/{course_slug}/live-{cohort}/{nn}-{topic_slug}/`; slugs lowercase ASCII, hyphens, immutable; numbers zero-padded to two digits [§B6.1]. Lesson-folder files [§B6.2]. Manifest fields `schema`, `course_slug`, `lesson_id`, `title`, `duration_s`, `tracks` (`role`, `file`, `height`), `captions` (`lang`, `file`), `transcript`, `chapters`, `slides`, `cues`, `summary`, `source` (`kind`, `uploaded_by`, `original_name`), `processing` (`pipeline_version`, `completed_at`); all paths relative to the lesson folder; reserved roles `camera`, `screen`; a v1 reader ignores roles it doesn't play [§B6.3]. `media_signing.sign(relative_path, ttl_seconds=3600)`; implementations `none`, `hmac`, `s3`; the baseline pipeline never calls it [§B6.4] | none (after Release 0: additive only, via `/contract-change`).|
| B3 LTI 1.3 launch | Used | Claims `sub`, `name`, `email` (if shared), `roles`, `context` (course id, title), `resource_link`, `deployment_id`; role mapping (Instructor → Mentor, Administrator → Administrator, Learner refused by baseline tools); session bound to (`sub`, context id), expires after 2 h idle; `shared.course_link` [§B3] | none. |
| B5 Model and speech interface | Used | `model.run(task, inputs, output_schema)` → `result.data`, `result.meta` [§B5.1]; on invalid output one retry, then a clear error [§B5.2]; prompts are versioned files in `/libs/model_interface/prompts/`; every call logs `meta` to `shared.model_calls` [§B5.3]; `speech.transcribe(audio_path, language="en")` → `segments` (`start`, `end`, `text`, `words`), `meta` [§B5.4] | none. |
| B7 H5P practice output | Used, R5 only [§C4.6] | Standard `.h5p` file plus `course.yaml` entry (`type: h5p`, `idnumber`, `graded: false`); never graded; video checkpoints as a separate activity (default) and as `cues.json` entries [§B7] | none |
| B8.5 Lecture videos | Provided (owner: Student 4) [§B8] | ≥ 5 Indian-English technical lectures (≥ 3 h total) with reference transcripts; recorded with written consent or openly licensed (licence verified and recorded) | none. |

Lesson-folder files [§B6.2]: `720p.mp4` (main track, H.264/AAC, 1280×720; required); `360p.mp4` (optional, feature flag); `poster.jpg` (required); `captions.en.vtt` (required); `transcript.en.json` (required); `chapters.json` (required); `summary.en.md` (optional, feature flag); `slides.json` + `slides/NNN.jpg` (optional, feature flag, on by default); `cues.json` (optional); `camera.mp4`, `screen.mp4` (optional; accepted and listed, not played in v1); `lesson.json` (required).

No contract change is proposed. Every module validates contract data it reads and writes against the schema; invalid data is rejected with a clear error [§B.0].

## 5. Data model

Tables in schema `video` named by PRD §C4.5: `video.lesson`, `video.upload`, `video.job`, `video.step`. Their columns, keys and states are OQ-22.

- Audit entries (who, what, when, course) for every state-changing operation go to `shared.audit_log` [OPS-06].
- The LTI context id is mapped to the Moodle course id and stored in `shared.course_link` [§B3].
- Model and speech call metadata are logged to `shared.model_calls` by the model interface [§B5.3].
- **Migrations:** versioned and reversible [OPS-07].
- **Relative vs absolute:** any media URL stored by a tool is a relative path, never a full fixed URL [C-08]; all manifest paths are relative to the lesson folder [§B6.3].
- **Backup and restore:** a documented procedure for the tool database and media store [OPS-08] (OQ-28).
- **Personal data:** no personal data beyond what LTI provides (name, email if shared, role) [SEC-06]; the manifest records `source.uploaded_by` as the LTI `sub` [§B6.3].
- Tables `video.watch` and `video.cue_response` belong to the extension track (Release 6) [§C6.5] and are not part of this module's baseline.

## 6. Interfaces

### Web/API

| Route | Purpose | Allowed roles |
|---|---|---|
| `GET /health` | Status and version [OPS-03] | TO DECIDE |
| Login initiation, launch (redirect), JWKS | LTI 1.3 endpoints, one registration per tool [§B3] | Moodle |

The pages in §3 (upload, status, lesson detail) serve mentors for their own course's lessons and administrators for all courses [§A5]. Their routes and payloads are OQ-30.

Rules: a launch with any role not listed is refused with a clear message; a user sees only data for the course they launched from, except administrators [§A5]. Learner launches are refused by the baseline tools [EXT-07]. Authorisation on every request from the LTI session: role + course context [SEC-02]. CSRF protection on all state-changing web requests [SEC-09].

### CLI (PRD C-05, OPS-05)

Every CLI supports `--dry-run` (prints intended changes, changes nothing), `--check` (read-only status, exit code 0 = OK, 1 = problems found) and `--config <file>`; exit code 2 = error [OPS-05]. Every CLI has a documented undo [C-05].

| Command | Purpose | Source |
|---|---|---|
| Retention CLI | Lists and, with confirmation, removes lessons older than a configurable age (default off) | FR-V-15 |

Command names, other commands (for example the administrator's re-run in §C4.2) and the undo for each are OQ-31; the undo for lesson removal is also OQ-5.

### Configuration (all through environment variables; `.env.example` lists every variable with a safe default or a placeholder [OPS-02])

| Setting | Default | Source |
|---|---|---|
| Upload chunk size | 90 MB | FR-V-01 |
| Storage backend: local folder or S3-compatible bucket | — | FR-V-12 |
| Path template | B6.1 templates | §B6.1 ("configurable") |
| Days before raw uploads and BigBlueButton intake files are deleted | 30 | FR-V-15 |
| Lesson age for the removal CLI | off | FR-V-15 |
| Feature flag: slide index | on | FR-V-07 |
| Feature flags: summary, `360p` copy, BigBlueButton intake | — | FR-V-06, §B6.2, EXT-05 |
| BigBlueButton shared secret | — (secret; environment only) | FR-V-09, C-06 |
| Model provider and model | — | `MODEL_PROVIDER`, `MODEL_NAME` [§B5.2] (owned by `libs/model_interface`) |

FR-V-01 sets a maximum file size of 4 GB; whether that limit is configurable is OQ-43. Variable names and the defaults marked "—" are OQ-32. No variable has been added to `.env.example` by this document.

## 7. Key decisions and alternatives

Only decisions the PRD itself makes are listed; they are fixed by the PRD, so no alternatives are weighed here. Decisions that change design are recorded in `docs/decisions/` [WW-04].

| Decision | Alternatives considered | Why this one | Record |
|---|---|---|---|
| Resumable upload with the tus protocol, default chunk 90 MB | None (fixed by PRD) | Below a 100 MB proxy limit; uploads must resume [FR-V-01, G-8] | Follows the PRD |
| ffmpeg for transcode, poster and scene detection | None (fixed by PRD) | Fixed stack [§A10, §C4.5] | Follows the PRD |
| Whisper-family speech-to-text in the lab, through the speech interface | None (fixed by PRD) | Fixed stack [§A10]; C-10 | Follows the PRD |
| Heavy work in worker containers fed by a job queue with persistent state | None (fixed by PRD) | [OPS-10, §C4.5] | Follows the PRD |
| Storage adapter: local folder or S3-compatible | None (fixed by PRD) | Swapping is configuration, not code [EXT-04] | Follows the PRD |
| Manifest lists every track and derived file | None (fixed by PRD) | Later camera and screen tracks need no change to existing lessons [EXT-03] | Follows the PRD |
| Slide index produced now for the future player | None (fixed by PRD) | F-1 will display it [EXT-08] | Follows the PRD |
| BigBlueButton **video** recording format | None (fixed by PRD) | [FR-V-09, §A11] | Follows the PRD |

## 8. Libraries and licences

The PRD fixes the stack but not library versions or licences (OQ-36).

| Library | Pinned version | Licence | Why needed | Alternative |
|---|---|---|---|---|
| FastAPI | TO VERIFY: https://pypi.org/project/fastapi/ | TO VERIFY: https://github.com/fastapi/fastapi/blob/master/LICENSE | Web framework [§A10] | none (stack fixed) |
| React + TypeScript | TO VERIFY: https://www.npmjs.com/package/react and https://www.npmjs.com/package/typescript | TO VERIFY: https://github.com/facebook/react/blob/main/LICENSE and https://github.com/microsoft/TypeScript/blob/main/LICENSE.txt | Front end, static build [§A10] | none (stack fixed) |
| PostgreSQL | 16 [§A10]; minor version TO VERIFY: https://www.postgresql.org/support/versioning/ | TO VERIFY: https://www.postgresql.org/about/licence/ | Database [§A10] | none (stack fixed) |
| ffmpeg | TO VERIFY: https://ffmpeg.org/download.html | TO VERIFY: https://ffmpeg.org/legal.html (licence depends on the build; C-11 allows LGPL only as an unmodified library) | Transcode, poster and scene detection [§C4.5]; called as a separate process (proposed; the PRD does not say) | none (stack fixed) |
| LTI 1.3 library | TO VERIFY: `docs/decisions/0001` (not yet written; chosen in Release 0) [§A10, App-C 6] | TO VERIFY: `docs/decisions/0001`; must be compatible [§A10, C-11] | LTI 1.3 launches [§B3] | Chosen in Release 0 and recorded in `docs/decisions/0001` [App-C 6] |
| Playwright (Python) | TO VERIFY: https://pypi.org/project/playwright/ | TO VERIFY: https://github.com/microsoft/playwright-python/blob/main/LICENSE | Browser tests [§A10] | none (stack fixed) |
| Docker + Docker Compose | TO VERIFY: https://docs.docker.com/engine/release-notes/ and https://docs.docker.com/compose/releases/release-notes/ | TO VERIFY: https://github.com/moby/moby/blob/master/LICENSE and https://github.com/docker/compose/blob/main/LICENSE | Containers [§A10] | none (stack fixed) |

Licences must be MIT, BSD or Apache-2.0 (LGPL only as an unmodified library): PRD C-11.

## 9. Security and privacy

| ID | Applies? | How it is met |
|---|---|---|
| SEC-01 LTI launch validation | Yes | Launches validated fully (signature, issuer, audience, nonce, expiry, deployment id) [SEC-01] |
| SEC-02 Authorisation per request | Yes | Role + course context from the LTI session on every request [SEC-02]; mentor: own course's lessons; administrator: all [§A5] |
| SEC-03 Service-account token | TO DECIDE | B4 is listed as used by M2 and M3 [§B.0] |
| SEC-04 Sandbox | No | Applies to untrusted learner code in Module 3 [SEC-04] |
| SEC-05 Uploads | Yes | Size limit (max 4 GB [FR-V-01]); type check by content, not only extension; virus-free assumption documented; stored outside any web root until processed [SEC-05] |
| SEC-06 Personal data | Yes | No personal data beyond what LTI provides; test data only in the lab [SEC-06, C-07] |
| SEC-07 Data to hosted AI | Yes | Data sent limited to what the task needs; provider and data sent documented in the data map [SEC-07] |
| SEC-08 Dependency scan | Yes | Dependencies scanned in CI; no known critical vulnerabilities at release [SEC-08] |
| SEC-09 CSRF and cookies | Yes | CSRF protection on state-changing requests; secure, same-site cookies for LTI sessions [SEC-09] |

Other handling:
- **Secrets and logs:** no secrets in the repository; configuration through environment variables [C-06]. Logs are structured JSON with request id, user (LTI `sub`), course (LTI context id) and action; no secrets or file contents [OPS-04].
- **Learner role:** refused by baseline tools [EXT-07].
- **Test data only:** test data only (§B8) [C-07]; B8.5 lectures are recorded with written consent or openly licensed; no real learner data in any set [§B8] (OQ-6).
- **Untrusted input:** uploads, handled as SEC-05 (OQ-35).

**For `docs/data-map.md`** (every data item stored or sent, where, for how long, and why [§E6]; open details in OQ-34):

| Data item | Stored where | Sent to | Kept for | Why |
|---|---|---|---|---|
| Raw uploads and BigBlueButton intake files | Outside any web root until processed [SEC-05] | — | Configurable days after the lesson is ready (default 30) [FR-V-15] | Processing |
| Lesson folder files (B6.2) | Media store [§A8] | Played by Moodle by relative path [§A8] | Never deleted automatically [FR-V-15] | Lesson playback |
| Audio for transcription | — | Speech provider, local or hosted [§B5.4] | — | FR-V-04 |
| Transcript | Lesson folder [§B6.2] | Model provider, local or hosted [§B5.2], for chapters [FR-V-05] | As the lesson folder [FR-V-15] | FR-V-04, FR-V-05 |
| Uploader LTI `sub` | Manifest `source.uploaded_by` [§B6.3]; `shared.audit_log` [OPS-06] | — | — | Audit |

## 10. Error handling

Messages say what happened and what to do next, in plain English [UI-05]. All user-facing strings live in one place in the module [UI-07]. Behaviours are from PRD §C4.8 and the sections given; message texts and the remaining cases are OQ-33.

| Situation | Behaviour | Recovery |
|---|---|---|
| Upload interrupted | Resumable [§C4.8, FR-V-01] | Resume after reload [§C4.4] |
| Wrong file type or size | Clear messages for type/size [§C4.8] | Accepted: mp4, mov, mkv, webm; max file 4 GB [FR-V-01] |
| Processing step fails | Failed step shown with reason and retry [§C4.8, FR-V-10] | Retry from the status page |
| Partial outputs | Never exposed [§C4.8]; `lesson.json` written last [FR-V-08] | — |
| BigBlueButton unreachable | Retry with back-off; status shows last successful poll [§C4.8] | Automatic |
| Invalid model output | One retry, then a clear error; never a silent partial result [§B5.2] | TO DECIDE |
| Session expired (2 h idle) | Session ends [§B3] | Re-launch from Moodle to continue [§B3] |
| Role not allowed / Learner launch | Refused with a clear message [§A5, EXT-07] | Use Moodle |

## 11. Test plan

| Level | What is tested | Test data | Requirement IDs |
|---|---|---|---|
| Unit | Functions and validators (contracts, rules, parsers) [§E1] | Proposed: small fixture files written for the tests and the B6 example files; no real recordings [§B8] | Proposed: FR-V-01 (type and size checks), FR-V-02 (slug rules), FR-V-08 (manifest written last), FR-V-12 (storage adapter), FR-V-15 (retention age) [§C4.3] |
| Contract | Every example and generated file validates against its schema [§E1]; `lesson.json` validates against B6.3 [§C4.7] | At least one valid example file per contract [§B.0] | FR-V-08 |
| Integration (harness) | Module smoke test in the harness [§D1, §E1]; restore + role tests + module smoke tests on fresh Moodle 4.5 and 5.3 sites every release [§E2] | Proposed: B8.5 lecture videos with reference transcripts [§B8.5]; a recording from a lab course on the lab BigBlueButton [§C4.7] | Proposed: FR-V-01, FR-V-03, FR-V-04, FR-V-05, FR-V-07, FR-V-08, FR-V-09 (§C4.7 criteria 1–5) |
| End-to-end | Mentor flows in a real browser [§E1]; pasted snippet plays with captions in a Moodle Page on 4.5 and 5.3 [§C4.7] | Lab Moodle sites [§A11] | FR-V-13 |

**Acceptance criteria (PRD §C4.7) and how each is shown** (test methods and data are OQ-38):

| Criterion | Demonstration |
|---|---|
| 700 MB file uploaded through a 100 MB-limited proxy with one forced interruption: completes and plays. | Final demonstration step 3 includes a browser upload with an interruption [§E5] |
| For a 90-minute recording: lesson ready (captions, transcript, chapters, slide index, manifest) ≤ 30 min after it becomes available. | Measured for G-7 [§A3] |
| Caption word error rate measured on B8.5 and reported against the Release 0 target. | Measured on B8.5 against the App-C 7 target |
| `lesson.json` validates against B6.3; all paths relative; existing single-track lessons remain valid when `camera`/`screen` tracks are added later. | Contract tests [§E1] |
| A BigBlueButton recording from a lab course appears in the correct live-class folder without manual steps. | Final demonstration step 3 [§E5] |
| Pasted snippet plays the video with captions in a Moodle Page on 4.5 and 5.3. | Final demonstration step 3 [§E5]; end-to-end test |

Final demonstration [§E5, step 3]: a lecture is uploaded from the browser (with an interruption); a live class runs on BigBlueButton and is recorded; both appear with captions, chapters and slide index; the snippet plays in a Moodle Page.

**Metrics (PRD §C4.9)** — processing time per minute of video; word error rate; upload success rate; manual chapter edits per lesson. Numbers come from logs or recorded sessions, never estimates; each measurement states the data set, method, date and who measured [§E3]. The method and the person measuring each metric are OQ-40.

Traceability: every FR is mapped to test(s), demonstration step and Bloom level in `docs/traceability.md`, updated in every pull request that adds or changes an FR [§E4].

## 12. Risks :

Project risks from PRD Appendix D that apply to this module:

| # | Risk | Needs the lab? | Plan or owner |
|---|---|---|---|
| 1 | Lab downtime | Yes (proposed): integration and end-to-end tests and BigBlueButton intake run on the lab [§E1] | VM images backed up; tools rebuildable with `docker compose` [App-D] |
| 2 | Contract drift between modules | No (proposed): contract tests run in CI on every pull request [§E1] | Freeze at Release 0; B.0 change rule; contract tests in CI [App-D] |
| 3 | Scope pressure | No (proposed): a planning risk handled by release order, not by lab work | Releases are independent; stretch only after Releases 1–4 [App-D] |

## 13. Work breakdown

One requirement (or one tightly related group) per pull request. Feature work starts only when this document says `Status: Approved`. Items marked "Release 0" are foundation work the PRD places in Release 0 [§D1] and may start earlier. Release 3 depends on Release 0; Release 5 depends on Releases 2 and 3 [§D1]. The order of pull requests within Release 3 is OQ-41.

| Order | Pull request | Requirements | Depends on | Notes |
|---|---|---|---|---|
| 1 | B6 contract: schema and at least one valid example | B6 (contract) | — | **Release 0** [§D1, §B.0]. Owner: Student 4. Frozen at the end of Release 0 |
| 2 | `media_paths` shared library, including B6.4 with the `none` implementation | B6.4 | — | **Release 0** [§D1, §B6.4] |
| 3 | B8.5 lecture videos | B8.5 | — | **Release 0** test data [§D1] |
| 4 | Appendix C verification of items that concern the video pipeline | App-C #4, #7, #8 | Lab | **Release 0**; results in `docs/decisions/` [App-C]. |
| 5 | Resumable upload | FR-V-01 | Release 0 | Release 3 |
| 6 | Upload form | FR-V-02 | Release 0 | Release 3 |
| 7 | Transcode and poster | FR-V-03 | Release 0 | Release 3 |
| 8 | Transcription and captions | FR-V-04 | Release 0 | Release 3 |
| 9 | Chapters | FR-V-05 | FR-V-04 (chapters are made from the transcript) | Release 3 |
| 10 | Summary | FR-V-06 | Release 0 | Release 3. Feature flag |
| 11 | Slide index | FR-V-07 | Release 0 | Release 3. Feature flag, on by default |
| 12 | Manifest | FR-V-08 | All required files of B6.2 | Release 3. `lesson.json` written last |
| 13 | BigBlueButton intake | FR-V-09 | App-C #4 | Release 3 |
| 14 | Status page | FR-V-10 | Release 0 | Release 3 |
| 15 | Re-process | FR-V-11 | Release 0 | Release 3 |
| 16 | Storage adapter | FR-V-12 | Release 0 | Release 3 |
| 17 | Embed snippet | FR-V-13 | Release 0 | Release 3 |
| 18 | Retention | FR-V-15 | Release 0 | Release 3 |
| 19 | Harness smoke test | Release 3 [§D1] | Release 3 features | The harness is Module 2's |
| 20 | README, `.env.example`, changelog, traceability, data map, release notes | §D2 items 5–7, §E4, §E6 | All | Release 3 exit criteria |
| 21 | *(R5, stretch)* Checkpoints | FR-V-14 | Releases 2 and 3 [§D1]; Releases 1–4 exit criteria [§C5] | Release 5 |

## 14. Review and approval

- [ ] Owner: I understand and can explain every section.
- [ ] Peer reviewer: checked against the PRD chapter and the contracts; comments resolved.
- [ ] Guide: approved (sets `Status: Approved`).

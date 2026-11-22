# D4: video paths demo (5 to 7 minutes)

Shows the existing `libs/media_paths` library and the B6.3 lesson manifest (PRD B6.1, B6.3, B6.4;
EXT-09, C-08). Synthetic names only. No media files, no services, no network, no secrets.
This is not the Release 0 demonstration (that material is in `docs/release-0/`: the report, the
demo script and the traceability note, merged in PR #105) and not B8.5 evidence.

## Prerequisites

- Python 3.12 and `jsonschema` (`pip install -r requirements-dev.txt`).
- Requires `libs/media_paths/paths.py`, on `main` since PR #85.

## Run (one command, from the repository root)

```bash
PYTHONPATH=libs python -B modules/video/demo/paths_demo.py
```

`PYTHONPATH=libs` is needed because the library is imported as `media_paths`, not
`libs.media_paths` (`libs/` is deliberately not a package). Do not use `python -I`: it ignores
`PYTHONPATH`, so the import fails. `-B` stops Python writing `__pycache__` files.
Exit code 0 means every outcome below was observed; 1 means something differed (it is listed).

## Expected output (observed 2026-11-16, Python 3.12.5)

Checks print `[ok]`; informational lines do not. Abbreviated:

```text
A. [ok] 'slides/001.jpg' valid=True   [ok] '../720p.mp4' valid=False
   [ok] '%2e%2e/720p.mp4' valid=False   [ok] 'https:/720p.mp4' valid=False
B. lesson folder: courses/build-ai-assistant/01-setup/02-install-python/
   live folder  : courses/build-ai-assistant/live-spring-2027/03-rag-basics/
   lesson number 100 -> lesson_number must be between 1 and 99, got 100
   cohort 'Spring 27' -> cohort must be a slug: lowercase ASCII letters and digits ...
   template without {lesson_slug} -> template is missing required placeholder(s) {lesson_slug}. ...
   template with {bogus} -> template uses unsupported placeholder {bogus}. ...
C. result = <media base URL> + '/courses/build-ai-assistant/01-setup/02-install-python/720p.mp4'
   MEDIA_SIGNING=hmac -> MEDIA_SIGNING='hmac' is defined in PRD B6.4 but not implemented yet.
D. single-track.json validates against the schema (0 errors)
   hardcoded example values give courses/<course_slug>/<lesson_id>/ (consistency only)
   Note: the library does not derive the folder from lesson_id or check this link.
   PENDING: BigBlueButton source value and recording metadata are not verified
All expected outcomes observed.
```

## Walkthrough

| Min | Part | Say | Show |
|---|---|---|---|
| 0:00 | Intro | One rule for every media path; media is stored as relative paths, never URLs (C-08). | Run the command once, scroll to A. |
| 0:45 | A. Validate | The same rule as the B6.3 schema. Traversal, `%` (so any encoded traversal) and a leading URL scheme (`https:`) are refused. Paths are never decoded. | Four lines of A. |
| 2:00 | B. Templates | PRD B6.1 folders for lessons and live classes. Numbers are 1 to 99, cohort is a slug. Templates are checked once when loaded: the placeholders that identify the item are required, unknown ones are refused (Guide decision recorded in PR #38). | Both folders; the four refusals. |
| 3:45 | C. Signing | Release 0 has only the `none` signer (B6.4): base URL plus path. No signature, no expiry; `ttl_seconds` is accepted and ignored. `hmac` and `s3` are defined in the PRD but **not implemented**; asking for them is a configuration error. This is not a production signed URL. | The unsigned checks; the `hmac` message. |
| 5:00 | D. Manifest | The example manifest passes the real schema. The folder in B was built from hardcoded example values; they are consistent with `courses/<course_slug>/<lesson_id>/` for the default layout. This is a consistency check only: the library does not derive a folder from `lesson_id` or validate that link. Track files are relative to the folder. `source.kind` is `upload`. | Part D lines. |
| 6:15 | Limits | BigBlueButton is pending (below). | The PENDING lines. |

## Limitations and pending items

- **BigBlueButton recordings: PENDING.** The PRD names no `source.kind` value for BigBlueButton
  intake (schema: "this is not an enum"), and App-C 4 (FR-V-09) is NOT VERIFIED: no lab run
  (see PR #96). The demo invents neither a value nor recording metadata.
- Nothing here reads or writes `lesson.json`; no pipeline writes one yet (FR-V-08, Release 3).
- Part B uses the path templates merged in PR #85. The demo changes no library code and no contract.
- The base URL is the placeholder host from `.env.example`; full URLs are not printed.

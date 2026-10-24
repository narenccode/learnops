# Module 4 — Video pipeline (owner: Student 4)

Adds to the root `CLAUDE.md`; never overrides it. Spec: PRD §C4. Release 3 (core), Release 5 (checkpoints, stretch). Extension track (player, §C6) only after the baseline is frozen.

## Scope
FR-V-01…13, FR-V-15 (Release 3); FR-V-14 (Release 5).

## Contracts
- **Owns:** B6 media paths, lesson manifest, signing interface (and `libs/media_paths`). Changes only via `/contract-change`.
- **Uses:** B3 LTI, B5 model and speech interfaces, B7 (stretch), B8.5 lecture set.

## Module rules
1. **Relative paths only** in every file and database row (C-08). Never store a full media URL.
2. `lesson.json` is written **last**, only when every required file exists; outputs are written to a temp folder and moved into place atomically.
3. Track roles `camera` and `screen` are accepted and listed but not processed beyond validation in the baseline (EXT-03). Don't remove them; the extension player depends on them.
4. Upload chunks default to 90 MB (below a 100 MB proxy limit); uploads must resume after interruption.
5. Heavy steps run in workers from the job queue (OPS-10); every step is idempotent and retryable.
6. Transcription only through the speech interface; chapters and summaries only through the model interface.
7. Retention (FR-V-15): raw files deleted after the configured days; published lessons never deleted automatically.
8. BigBlueButton: use its public API and the **video** recording format only; don't read BigBlueButton's internal files in the baseline (that is extension F-2).
9. Lecture videos in `testdata/` must have recorded consent or a verified licence.

## Typical commands
`video process <lesson> [--dry-run]` · `video reprocess <lesson>` · `video bbb-poll [--dry-run]` · `video retention --check`

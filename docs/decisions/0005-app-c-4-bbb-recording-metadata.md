# App-C item 4 — BigBlueButton recording metadata and video-format output (T17)

**Status: PENDING — NOT VERIFIED.** No lab BigBlueButton was contacted. Nothing below counts as
lab evidence until the checklist at the end is done and its result is recorded here.

## What was done (2026-11-16)

- Read PRD §A11, §B6, FR-V-09, App-C 4, `docs/design/video.md` (FR-V-09, §12), `modules/video/CLAUDE.md`
  and `CLAUDE.md`. There is no earlier App-C evidence folder; this record and
  `docs/decisions/evidence/0005-app-c-4-bbb/` start it.
- Checked, without printing values, whether lab access is configured. It is not: the environment has
  no `BBB_*` variables, and the only local `.env` holds the placeholder values from `.env.example`
  (`bbb.lab.invalid`, `CHANGE_ME`). The host in `.env.example` is a reserved invalid name, so no
  request was sent.
- Wrote `verify_bbb.py` (read-only: version call and `getRecordings` only; no meeting or recording is
  created; no configuration is changed). Its `--selftest` passes on synthetic data. This shows the
  script's logic only.

## Verification table

| # | Item | Result | Evidence |
|---|---|---|---|
| 1 | BBB server reachable | PENDING | No lab access in this session |
| 2 | Version (expected 3.0, PRD §A11) and recording API available | PENDING | same |
| 3 | Recording metadata retrievable (`getRecordings`) | PENDING | same |
| 4 | **video** format present, and its output location | PENDING | same |
| 5 | Metadata has the fields the Video contract needs (see below) | PENDING | same |
| 6 | A lab recording can be located and its metadata inspected | PENDING | Needs an existing recording made from a lab course |
| 7 | Permissions, configuration, missing dependencies | PENDING | Lab values must come from the environment; the lab network must be reachable from where the script runs |

## What FR-V-09 needs from the metadata (the questions the lab must answer)

FR-V-09 maps a recording to `courses/{course_slug}/live-{cohort}/{nn}-{topic_slug}/` (B6.1) and the
manifest needs `course_slug`, `lesson_id`, `title`, `duration_s` and a `source` (B6.3).

| Needed | Possible BBB / Moodle source | Status |
|---|---|---|
| Course | Moodle's BigBlueButton activity is *expected* to set `bbb-context-id` (course id), `bbb-context-label` (course short name) and `bbb-context-name` as recording metadata. From knowledge of that plugin, **not verified**. | PENDING |
| How a Moodle course becomes `course_slug` | The PRD does not say (short name? a mapping table?) | TO DECIDE (guide); do not invent |
| Cohort (`live-{cohort}`) | No cohort field is expected from Moodle. May need a group, activity name or a mapping. | PENDING: likely **gap** |
| `nn` and `topic_slug` | Possibly derived from the recording name (`bbb-recording-name`) or the activity; undefined. | PENDING: likely **gap** |
| Title, duration | Recording name; `startTime`/`endTime` or the media file | PENDING |
| `source.kind` and who started it | Not named by the PRD (design `video.md` §4 TO DECIDE) | TO DECIDE |
| Video format output location | `playback/format` with type `video` in `getRecordings`; the file path pattern on the server is to be read from the lab | PENDING |

If cohort, `nn` or `topic_slug` are not in the metadata, that is a finding to give the guide: either
the PRD mapping changes or Moodle-side naming rules are agreed. This record does not decide it.

## Checklist for manual completion (needs lab access and a person allowed to use it)

1. On a machine that reaches the `bbb` VM, set `BBB_URL` and `BBB_SECRET` in the **environment**
   (take them from the lab's secret store; do not paste them in chat, files or the repository).
2. `python -I docs/decisions/evidence/0005-app-c-4-bbb/verify_bbb.py --out report.json`.
   Exit 0 = API ok and a video format found; 1 = a check failed (read the report); 2 = unreachable/not configured.
3. Confirm the version in the report is BigBlueButton 3.0 (items 1–2).
4. If there are no recordings, ask the lab owner for an existing recording from a lab course. Do **not**
   record a real learner session for this. If a new one is unavoidable, use a test course and test
   participants only, with the lab owner's approval (PRD B8, CLAUDE.md rule 4).
5. If the video format is missing, report it to the lab owner: enabling it is a BBB server change and
   is theirs to make (PRD §A11), not part of this task.
6. Read `metadata_keys` and `expected_moodle_keys_missing` for each recording; fill the table above.
7. Replace PENDING with the result, add the redacted `report.json` to the evidence folder after
   reading it, and note the date, BBB version and who ran it. Never add URLs, IDs, secrets or recordings.
8. Update `docs/traceability.md` and `docs/design/video.md` §12 row 4 from this record.

# App-C 4 — BigBlueButton recording metadata and video-format output

**Status:** NOT VERIFIED (lab evidence PENDING)
**Verification ID:** App-C item 4 (task T10, Student 4, Module 4 Video)
**Requirement (PRD App-C, item 4):** "BigBlueButton recording metadata fields set by Moodle's
BigBlueButton activity (for course mapping) and the video-format output location."
**Needed by:** FR-V-09 (BigBlueButton intake, Release 3); design document `docs/design/video.md`
section 13, order 4 and row 13; PRD C4.7 acceptance criterion "A BigBlueButton recording from a lab
course appears in the correct live-class folder without manual steps."

## Result

**NOT VERIFIED.** No BigBlueButton or Moodle observation exists yet, so no field, value or output
location is recorded as observed. Nothing in this record is a PASS.

Reason: this verification needs a recording made from a Moodle BigBlueButton activity on the lab
(`moodle45` or `moodle53`, and `bbb`; PRD A11). The dependency task **T17** (lab BigBlueButton
verification) is itself PENDING: `docs/decisions/0005-app-c-4-bbb-recording-metadata.md` and its
evidence folder (`docs/decisions/evidence/0005-app-c-4-bbb/`) exist in this branch, but they hold
only a read-only check script and one run that contacted nothing (lab values not configured, exit
code 2). They contain no server, version, recording, metadata or video-format observation. No
`lab/` setup notes exist on `origin/main` at `ca989f9` (checked 2026-11-16). The lab was not
reachable from the sessions that wrote these records. When T17 delivers
evidence, fill in the PENDING cells below; do not edit anything else without new evidence.

## Environment and version

| Item | Value | Source |
|---|---|---|
| BigBlueButton | PRD expects 3.0 on Ubuntu 22.04 with the **video** recording format enabled | PRD A11 (expectation, not observed) |
| BigBlueButton version actually installed | PENDING | T17 |
| Recording formats enabled on the lab server | PENDING | T17 |
| Moodle versions | PRD expects 4.5 and 5.3; the owner's decision (Issue #55, `docs/traceability.md`) is to build on 4.5 and test on 5.3 | PRD C-03 (expectation, not observed) |
| Moodle build and BigBlueButton plugin (`mod_bigbluebuttonbn`) versions actually installed | PENDING | T17 |
| Date of observation | PENDING | T17 |

## Steps performed

Done in this record (read-only, repository only):

1. Read PRD App-C item 4, A11, B6.1, B6.3, C4.3 (FR-V-09, FR-V-15), C4.7 and C4.8.
2. Read `CLAUDE.md` (rules 1, 3, 4 and the section 8 rules) and `modules/video/CLAUDE.md` rule 8:
   use BigBlueButton's public API and the **video** format only; do not read BigBlueButton's
   internal files in the baseline (that is extension F-2).
3. Read `docs/design/video.md` (FR-V-09 row marked TO DECIDE; section 4 `source.kind` for intake;
   section 13 order 4) and `contracts/lesson-manifest.v1.schema.json`.
4. Searched the repository, its remote branches and the open and closed pull requests for T17
   evidence, BigBlueButton recording samples and metadata notes. Found only the T17 record `0005`
   described above, with no lab observations. I did not run its script.
5. Checked that `.env.example` only holds placeholders (`BBB_URL`, `BBB_SECRET`); no secret was
   read or written.

Not done (needs the lab; PENDING):

6. Use an existing lab recording made from a Moodle BigBlueButton activity in a test course, with
   the **video** format enabled. Do not record a real learner session (CLAUDE.md rule 4).
7. Call the BigBlueButton `getRecordings` API (shared secret from the environment, never written
   here), for example with T17's `verify_bbb.py`, and save the metadata and format entries, with the
   secret and any personal data removed.
8. Record where the **video** format output is published and how it is fetched through the public
   API (a playback URL from `getRecordings`, not a file path on the server).

## Actual evidence

None. The tables below list what must be observed. Cells say PENDING until T17 supplies the
output; expected values are not evidence.

### Recording metadata set by Moodle's BigBlueButton activity

Record every `<metadata>` key returned by `getRecordings` for the lab recording. The fields
below are what the intake needs to map a recording to a course and cohort.

| Needed by the intake | Observed key | Observed value (test data only) | Present? |
|---|---|---|---|
| Course identity (to choose `{course_slug}`, B6.1) | PENDING | PENDING | PENDING |
| Cohort (to choose `live-{cohort}`, B6.1) | PENDING | PENDING | PENDING |
| Activity / meeting identity (to give a stable `{nn}` and `{topic_slug}`) | PENDING | PENDING | PENDING |
| Recording name (to give a topic title) | PENDING | PENDING | PENDING |
| Moodle origin and version (to tell sites apart) | PENDING | PENDING | PENDING |
| Full list of all other metadata keys | PENDING | PENDING | — |

### Video-format output

| Item | Observed |
|---|---|
| `getRecordings` entry for the **video** format (format type name, `url`, `length`, size) | PENDING |
| Where the output is published and how the pipeline fetches it through the public API | PENDING |
| Container and codecs of the output file (to be checked against FR-V-03: transcode to `720p.mp4` "when needed") | PENDING |
| Whether one single file is produced (the design assumes one **video** output becomes the `main` track) | PENDING |
| Recording state flow and the time until the recording is available (relevant to G-7 and the poll interval) | PENDING |

## Comparison with the LearnOps contract

What the contract needs, from the repository, and what can be said without lab evidence:

| Contract need | Where | Status |
|---|---|---|
| A course slug, lowercase ASCII with hyphens (live path `courses/{course_slug}/live-{cohort}/{nn}-{topic_slug}/`) | PRD B6.1; manifest `course_slug` | PENDING: a Moodle metadata value is not necessarily a slug. How a Moodle course maps to a `course_slug` is not defined in the PRD; the mapping (for example a configured table) must be decided and recorded. Not a result. |
| A cohort value (`live-{cohort}`) | PRD B6.1, FR-V-09 | PENDING: the PRD says to map "to course and cohort using the recording metadata", so the metadata must carry or lead to a cohort. Whether the Moodle activity sets anything for it is unknown until observed. If it does not, FR-V-09 has a gap that the guide must resolve (for example a Moodle group name or an administrator mapping). |
| `{nn}` and `{topic_slug}` | PRD B6.1 | PENDING: no source named for the number or the topic; to be derived from the observed metadata or a rule recorded in `docs/design/video.md`. |
| `source.kind` for intake | `contracts/lesson-manifest.v1.schema.json` (`source.kind` is a free, non-empty string; `uploaded_by` is an LTI `sub`) | No incompatibility in the schema: the intake value is not an enum value the schema forbids. The value is still TO DECIDE (design section 4). Any BigBlueButton user or meeting identifier must not be written to the manifest unless it is not personal data (SEC-06). |
| Relative paths only (C-08) | CLAUDE.md rule 7 | The playback URL returned by BigBlueButton is a full URL: it may be used to fetch the file but must not be stored in the manifest or the database; store only the relative lesson path. |
| Public API and **video** format only (no BigBlueButton internal files) | `modules/video/CLAUDE.md` rule 8 | The output location must be reachable through the API (a playback URL). A result that only gives a server directory is a blocker, not a pass. |
| Never modify BigBlueButton or Moodle (C-01) | CLAUDE.md rule 1 | All steps above are read-only on both. |

**Missing or incompatible fields found so far:** none confirmed, none ruled out. The course
slug, cohort and `{nn}`/`{topic_slug}` mappings are the open risks, listed above, and are not
results.

## Supporting references

- PRD: App-C item 4; A11 (lab); B6.1 (path template); B6.3 (manifest `source`); C4.3 FR-V-09,
  FR-V-15; C4.7; C4.8; C-01; C-08; SEC-06.
- `docs/design/video.md`: FR-V-09 row (TO DECIDE), section 4 (`source`), App-C table row 4,
  section 13 order 4 and row 13.
- `modules/video/CLAUDE.md` rule 8; root `CLAUDE.md` rules 1, 3, 4, 7.
- `contracts/lesson-manifest.v1.schema.json` (`source`).
- `.env.example` (`BBB_URL`, `BBB_SECRET`; placeholders only).
- Moodle BigBlueButton activity and BigBlueButton `getRecordings` public documentation: to be
  opened and cited with their version when the evidence is filled in (CLAUDE.md section 6a rule 5:
  verify every reference; none is cited here because none was opened for this record).
- T17 lab verification: `docs/decisions/0005-app-c-4-bbb-recording-metadata.md` and `docs/decisions/evidence/0005-app-c-4-bbb/` (PENDING, no lab observations).

## Remaining blockers

1. **T17 has no lab evidence.** Its record `0005` is PENDING and its script has not reached the lab. Owner: T17 assignee. When T17 fills in `0005`, copy its observed values into this record.
2. **Lab access** for a Moodle BigBlueButton activity recording with the **video** format enabled,
   and the shared secret supplied through the environment only.
3. **Decisions for the guide once evidence exists:** the course-slug mapping, the cohort source
   and the `{nn}`/`{topic_slug}` rule for the live-class path; the `source.kind` value for
   intake.
4. Close this item by changing **Status** to PASS only when every PENDING cell above holds an
   observed value, the video-format output is fetchable through the public API, and the comparison
   table has no unresolved row. If a needed field is absent, set the status to FAIL and record
   the gap.

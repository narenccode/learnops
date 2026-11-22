# App-C 4: acceptance evidence map

**Status: NOT VERIFIED. App-C 4 is NOT complete and nothing here is a PASS.**
**Audit date:** 2026-11-20, re-audited at `origin/main` `5f3a794` (the first audit was at `3abbc02` on
2026-11-16; 37 commits have merged since). GitHub state was queried on the audit date and changes
quickly; re-check before relying on it.

## Ownership: no work duplicated

This document **maps** App-C 4 evidence; it adds no implementation, test or decision record for it.

| Task label | Meaning (source) | PR | State on 2026-11-20 |
|---|---|---|---|
| T10 | App-C 4 verification record, decision `0006` (PR #96 description, "Task T10") | #96 | **Merged** 2026-11-16; approved by Harshithamanjunatha, shraddha0103 and Akshita21-09 |
| T17 | Lab BigBlueButton verification, decision `0005` and the evidence folder (PR #97 description) | #97 | **Closed** 2026-11-18 as superseded by #96: its ADR, README and run record are identical to `main`, its older `verify_bbb.py` is replaced by #96's, and its traceability section was already on `main` |

The labels T10 and T17 are the PR authors'; neither is defined in a repository file, so the mapping
stays **PENDING confirmation** against the external tracker.

**Scope (PRD App-C and §D1, PRDs #113 and #116):** App-C item 4 is verified "in the first release that relies on it", which is Release 3 (FR-V-09). It is **not** a Release 0 item any more; Release 0 carries App-C items 6 and 9 only. The record and script on `main` are early preparation.

Both records are on `main` (decisions `0005` and `0006`, evidence folder
`docs/decisions/evidence/0005-app-c-4-bbb/`). They use different numbers, so there is no numbering
collision. The decision files are numbered independently of the two T-labels.

## Requirement (verbatim)

PRD App-C item 4 (`docs/PRD.md`, App-C heading says "record results in `docs/decisions/`"):

> BigBlueButton recording metadata fields set by Moodle's BigBlueButton activity (for course
> mapping) and the video-format output location.

Related requirements it feeds: FR-V-09 (PRD C4.3: poll recordings via the BigBlueButton API with
the shared secret, fetch the **video** format output, map it to course and cohort using the
recording metadata set by Moodle's BigBlueButton activity, and process it into the live-class
path; Release 3) and the C4.7 criterion "A BigBlueButton recording from a lab course appears in the
correct live-class folder without manual steps." Constraints: C-01 (never modify Moodle or
BigBlueButton), C-08 and CLAUDE.md rule 7 (relative paths only), `modules/video/CLAUDE.md` rule 8
(public API and video format only). The PRD gives **no numeric acceptance criterion** for App-C 4;
its acceptance is a recorded observation from the lab (`moodle45`/`moodle53` and `bbb`, PRD A11).

## Evidence mapping

| Requirement | Implementation | Test | Actual result | Evidence | Remaining gap |
|---|---|---|---|---|---|
| Record the metadata keys Moodle's BBB activity sets on a recording, usable for course and cohort mapping | Read-only script `docs/decisions/evidence/0005-app-c-4-bbb/verify_bbb.py` on `main` | `verify_bbb.py --selftest`: synthetic XML only | Self-test passes (run for this audit: "selftest OK (synthetic data only; proves the script logic, NOT the lab)"). The one real run, `run-2026-11-16-unconfigured.json`, is `{"configured": false}`: no lab was reachable | Decisions `0005`, `0006`; the run record | **No lab observation of any metadata key** |
| Record the video-format output location and how the pipeline fetches it through the public API | Same | Same (the self-test asserts only a synthetic `video` format URL shape) | Same | Same | **No lab observation of the output location** |
| Contract compatibility (B6.1 path, B6.3 `source`) | `contracts/lesson-manifest.v1.schema.json` on `main`: `source.kind` is a free non-empty string, not an enum | `libs/contracts` tests (CI `ci` is green on `main` `5f3a794`) | They do not use a real BBB recording. The guide answered on PR #140 (merged 2026-11-22) that the intake value is `bbb` and `uploaded_by` is omitted; this is now in the design document on `main`, which is still `Draft` | Schema; PR #140 comment | The design approval (the guide's) |
| Result recorded in `docs/decisions/` and linked from `docs/traceability.md` | Decisions `0005`, `0006`; the App-C 4 section of `docs/traceability.md` on `main` | n/a | Recorded as NOT VERIFIED | `main` | Update both with a real lab result |

## Status by evidence type

| Level | State |
|---|---|
| Implemented | On `main`: a read-only check script and two decision records |
| Unit tested | Script self-test only (synthetic data), passes; proves script logic, not the requirement |
| Integration tested | **No** |
| Manually verified | **No** (no lab observation exists) |
| Awaiting external service | **Yes**: lab Moodle 4.5/5.3 with the BigBlueButton activity, and a BBB 3.0 server with the video format enabled. Not reachable from the sessions that wrote the records |
| Awaiting guide approval | Confirmation of the T10/T17 labels against the external tracker; no approval of the result is recorded because there is no result |

## Conclusion

- App-C 4 is **not satisfied**: no observation of any metadata field or output location exists.
- A merged PR is not evidence: #96 merged a record that says NOT VERIFIED. This map claims no acceptance result.
- Next step (Student 4 with lab access): run `verify_bbb.py` against the lab BigBlueButton, fill the
  PENDING cells in decisions `0005` and `0006`, and update `docs/traceability.md`. No further PR is
  needed for the records themselves until that run exists.

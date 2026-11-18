# App-C 4: acceptance evidence map

> **Update 2026-11-18 (the facts below are stale where they conflict):** PR #96 was **merged** on 2026-11-16 (approved by Harshithamanjunatha, Shraddha and Akshita21-09) and is the carrier of decisions `0005`/`0006` and `verify_bbb.py`. PR #97 was **closed as superseded by #96**: its ADR, README and run record are identical to `main`, its older `verify_bbb.py` is replaced by #96's, and its traceability section is already on `main`. The `0005` numbering collision therefore no longer exists. App-C 4 is **still NOT VERIFIED**: no lab observation exists, so nothing here is a PASS.

**Status: NOT VERIFIED. App-C 4 is NOT complete and nothing here is a PASS.**
**Audit date:** 2026-11-16. First pass at `origin/main` `3abbc02`; second pass merged with `ecb4389`.
Open-PR facts below were queried on 2026-11-16 and change quickly.

## Ownership: no work duplicated

App-C 4 belongs to another active session. This document **maps** that work; it adds no
implementation, test or decision record for App-C 4 and touches neither branch.

| Task label | Meaning (source) | PR | State |
|---|---|---|---|
| T10 | App-C 4 verification record, decision `0006` (PR #96 description, "Task T10") | #96 `video/app-c-4-bbb-recording-metadata` | Open, not draft, `CHANGES_REQUESTED`, label `needs-rework`, `checks` FAILURE |
| T17 | Lab BigBlueButton verification, decision `0005` and evidence folder (PR #97 description) | #97 `video/t17-bbb-lab-verification` | Open, **Draft**, `REVIEW_REQUIRED`, `checks` FAILURE |

*First-pass correction:* the first version of this document attributed App-C 4 to "T17/BBB" only.
PR #96 names it T10 and treats T17 as its dependency. Neither label is defined in any repository
file; the mapping is the PR authors' and stays **PENDING confirmation** against the external tracker.

Neither PR has merged, so **no App-C 4 code, decision or evidence is on `main`**.
PR #96 contains the files of PR #97 as well (its own description says so and asks the reviewer to
decide whether to split them). Both claim decision number `0005`; PR #96 also adds `0006`. The
`verify_bbb.py` in the two branches is byte-identical (compared with `diff`). Resolving the number
collision and the split is for the owning session and the guide.

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
| Record the metadata keys Moodle's BBB activity sets on a recording, usable for course and cohort mapping | None on `main`. Read-only script `verify_bbb.py` and record `0006` exist only on the #96/#97 branches | `verify_bbb.py --selftest`, synthetic XML only | **Executed by this audit** from a scratchpad copy of the #96 file: `selftest OK (synthetic data only; proves the script logic, NOT the lab)`, exit 0. No lab test exists | PR branches: `docs/decisions/0006-…`, `docs/decisions/0005-…`, `docs/decisions/evidence/0005-app-c-4-bbb/` (all cells PENDING) | A real `getRecordings` run on the lab BBB with a Moodle-made recording; fill the PENDING observed-key table |
| Record the video-format output location and how the pipeline fetches it through the public API | Same | Same (selftest asserts only a synthetic `video` format URL shape) | Same; the one real run, `run-2026-11-16-unconfigured.json`, contains `{"configured": false}`: it contacted nothing | Same | Same. A server directory without an API playback URL would be a blocker, per record `0006` |
| Contract compatibility (B6.1 path, B6.3 `source`) | `contracts/lesson-manifest.v1.schema.json` on `main`: `source.kind` is a free non-empty string, not an enum | `libs/contracts` tests, which pass for B6 (full suite in the venv run: 2044 passed) | They do not test BBB intake | Record `0006`, "Comparison with the LearnOps contract" | Course slug, cohort, `{nn}` and `{topic_slug}` sources are **open risks**, not results |
| Result recorded in `docs/decisions/` and linked from `docs/traceability.md` | Both PRs edit `docs/traceability.md` | n/a | n/a | PR #96, PR #97 | Merge conflicts on the shared file are likely; `needs-rework` and failing checks on both PRs |

## Status by evidence type

| Level | State |
|---|---|
| Implemented | Not on `main`; read-only script exists on two open PR branches |
| Unit tested | Script self-test only (synthetic data), passes; proves script logic, not the requirement |
| Integration tested | **No** |
| Manually verified | **No** (no lab observation exists) |
| Awaiting external service | **Yes**: lab Moodle 4.5/5.3 with the BigBlueButton activity, and a BBB 3.0 server with the video format enabled. Not reachable from the sessions that wrote the records |
| Awaiting guide approval | Decision numbering and merge of #96/#97; no approval recorded |

## Conclusion

- App-C 4 is **not satisfied**: no observation of any metadata field or output location exists.
- Another PR's existence is not evidence. This map claims no acceptance result.
- Next steps belong to the owning session: run the script against the lab, fill the PENDING cells,
  resolve the `0005`/`0006` collision, fix the failing checks, and obtain review.

## Proposed (not applied) change

For whoever merges #96/#97: keep one carrier PR, renumber so only one record uses `0005`, keep the
verdict "NOT VERIFIED" until a lab run exists, and then update this map.

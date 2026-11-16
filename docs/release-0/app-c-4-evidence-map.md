# App-C 4: acceptance evidence map

**Status: NOT VERIFIED. App-C 4 is NOT complete.**
**Audit date:** 2026-11-16. **Base:** `origin/main` at `3abbc02`.

## Ownership note: no work duplicated

App-C 4 (BigBlueButton recording verification) and T17 are being handled by another active session,
in these open pull requests. This document **only maps** what exists there. It adds no
implementation, test or decision record for App-C 4 and does not touch those branches.

| PR | State (queried 2026-11-16) | What it holds |
|---|---|---|
| #96 `video/app-c-4-bbb-recording-metadata` | Open, not draft, `CHANGES_REQUESTED`, label `needs-rework`, one failing check | `docs/decisions/0005-…` and `0006-app-c-4-bbb-recording-metadata.md`, evidence README, `run-2026-11-16-unconfigured.json`, `verify_bbb.py`, traceability edit |
| #97 `video/t17-bbb-lab-verification` | Open, **Draft**, `REVIEW_REQUIRED`, one failing check | `docs/decisions/0005-…`, evidence README, `run-2026-11-16-unconfigured.json`, `verify_bbb.py`, traceability edit |

Both claim decision number 0005 (and #96 also adds 0006), and both edit `docs/traceability.md`. That
collision is for the owning session and the guide to resolve; it is reported here, not fixed.

## Requirement (PRD App-C 4, verbatim)

> BigBlueButton recording metadata fields set by Moodle's BigBlueButton activity (for course
> mapping) and the video-format output location.

Related: FR-V-09 (BigBlueButton intake, Release 3, `docs/design/video.md` item 13). The PRD gives no
numeric acceptance criteria for App-C 4 beyond "record results in `docs/decisions/`" (App-C heading).
It needs a lab Moodle with the BigBlueButton activity and a BigBlueButton server.

## Evidence mapping

| Requirement | Implementation location | Relevant test | Actual test result | Evidence location | Remaining gap |
|---|---|---|---|---|---|
| Record which metadata fields Moodle's BBB activity sets on a recording (for course mapping) | `verify_bbb.py` on PR #96/#97 branches (not on `main`; not run by this audit) | None found on `main`; not examined on the PR branches | **Not run.** The PR's own evidence file is named `run-2026-11-16-unconfigured.json`, i.e. no BBB server was configured | `docs/decisions/evidence/0005-app-c-4-bbb/` on PR branches only | A real run against the lab BBB and Moodle; decision record merged on `main` |
| Record the video-format output location | Same | Same | Same | Same | Same |
| Result recorded in `docs/decisions/` | Decision 0005 (and 0006) on PR branches | n/a | n/a | PR #96, PR #97 | PR #96 has changes requested and a failing check; PR #97 is Draft; numbering conflict |
| `docs/traceability.md` updated | Edits in both PRs | n/a | n/a | PR #96, PR #97 | Same shared-file conflict risk |

## Conclusion

- Not satisfied on `main`: no App-C 4 decision, evidence or script exists there.
- Not satisfied in the PRs: they record the item as not verified; no run against a real BBB server
  is documented.
- **No acceptance result is claimed here.** The requirement must not be marked complete until a
  real lab run is recorded and the owning PR is approved and merged.

## Proposed (not applied) change for the owning session

Proposed for whoever merges #96/#97, to avoid editing the same files concurrently: choose one of the
two PRs as the carrier, renumber the decision so only one record uses 0005, and keep the verdict
"NOT VERIFIED" until a lab run exists.

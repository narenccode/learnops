# Release 0 freeze-readiness checklist (T20 preparation)

> **Update 2026-11-18 (the facts below are stale where they conflict):** PR #96 was **merged** on 2026-11-16 (approved by Harshithamanjunatha, Shraddha and Akshita21-09) and is the carrier of decisions `0005`/`0006` and `verify_bbb.py`. PR #97 was **closed as superseded by #96**: its ADR, README and run record are identical to `main`, its older `verify_bbb.py` is replaced by #96's, and its traceability section is already on `main`. The `0005` numbering collision therefore no longer exists. App-C 4 is **still NOT VERIFIED**: no lab observation exists, so nothing here is a PASS.
> **Update 2026-11-18:** PR #99 recorded SHA-256 values and `ffprobe` durations for five recordings in the B8.5 inventory; PR #125 recorded the guide-approved temporary exceptions in decision 0004 (four lectures, no 1800 s total, for interim demonstration and testing only); PR #126 corrected the status wording. B8.5 stays **PENDING**: file names, speakers, consent lines, transcripts and review are not recorded, so no licence or consent evidence exists yet.

**Verdict: NOT READY. Release 0 is NOT frozen, and this document does not freeze it.** The guide
performs the adoption test and the tag (PRD §D2 items 7 and 8; `.claude/commands/release-check.md`).
**Audit date:** 2026-11-16. First pass at `origin/main` `3abbc02`; second pass (corrections) merged
with `ecb4389`. GitHub state was queried with `gh` the same day and changes quickly; re-check
before relying on it.

**Sibling documents (other sessions, not duplicated):** PR #105 adds the Release 0 report, demo
script and traceability needs under the same folder (`docs/release-0/`, different file names); PR #103
adds the G-6 evaluation preparation (T9); PR #106 the literature entries (T13). None had merged
when this was written.

Release 0 contents (PRD §D1): lab VMs ready (A11); repository, CI, coding standards; contracts
B1 to B8 v1 **frozen**; shared libraries `lti`, `moodle_ws`, `model_interface`, `contracts`,
`media_paths`; test data B8 v1; verification of assumptions (App-C); a design document per module
approved. Exit criteria are PRD §D2 items 1 to 8.

Status key (the six classes requested for T20): **COMPLETED** (genuine evidence exists) ·
**IMPLEMENTED, NOT VERIFIED** (implementation exists, acceptance evidence missing) · **AWAITING
GUIDE APPROVAL** · **BLOCKED** (unavailable service, external evidence or dependency) · **NOT
STARTED** · **READY FOR FINAL ACCEPTANCE**. Where a row says only "Completed", "Blocked" and so
on, it uses these classes. **NOT READY** and **UNKNOWN** mean the evidence needed to classify the
row was not found. Rows owned by another active session are marked *Other session*: their status
here is only what GitHub shows, not assessed. A merged PR is not treated as proof of its
acceptance criteria.

> Label note: T-numbers are not defined in the repository (see the B8.5 evidence document). Rows
> use PRD/PR identifiers; tracker labels are added only where the request stated them.

## 1. Known statuses taken as given

| Item | Status | Note |
|---|---|---|
| Video design | Completed (as stated by the owner); **not confirmed by the repository** | Second-pass check: `git log origin/main -- docs/design/video.md` shows only #17, #24, #34 and #47; no commit sets `Approved`, and the file on `main` reads `**Status:** Draft`. Not listed as pending, and not changed here. The guide or owner should point to the approval record, or the guide should set `Approved` in a PR |
| PR #100 (S2 Svarah literature audit) | Completed | Merged 2026-11-16 06:36 UTC; the T13 survey as a whole is not complete (PR #106: 1 of 6 sources verified) |
| PR #90 | Completed | Merged (`a500409`); verification not reopened |
| PR #85, PR #93 | Excluded | Not examined beyond state; not modified |
| Official B8.5 evidence | Separate from temporary test data | See B8.5 evidence document |
| T8, T10, T14, T17, BBB Recording Verification, T18 | *Other session* | Not duplicated |
| T13, T19, T9 preparation | *Other session* | Not duplicated |

## 2. PRD §D2 exit criteria

| # | Criterion | Status | Evidence / gap |
|---|---|---|---|
| 1 | Every Release 0 FR implemented and linked to passing tests (traceability E4) | **Not ready** | Release 0 work is foundation (contracts, libs, test data), mostly without FR IDs; `docs/traceability.md` has rows for B6 and B8.5 and records B8.1 as having no test. No complete Release 0 inventory exists in the repo (see §6) |
| 2 | Acceptance criteria (§C.x.7) pass | **Not applicable / unknown** | Release 0 has no module acceptance criteria in the PRD; its content is §D1 |
| 3 | Restore and role-test matrix on Moodle 4.5 **and** 5.3, harness report attached | **Blocked** | Needs lab Moodle sites; B8.1 `.mbz` does not exist; no harness report found |
| 4 | Contracts unchanged, or changed only additively under B.0 | **Not verified** | Only `course-package.v1` and `lesson-manifest.v1` schemas exist on `main`. Contract PRs open: #101, #94, #93, #87, #83 (and B2 branch). "Frozen" requires them resolved |
| 5 | README, `.env.example`, changelog updated | **Not verified** | `.env.example` exists; **no changelog file found** |
| 6 | Security items (A13) reviewed; dependency scan clean | **Not verified** | No scan result recorded in this audit |
| 7 | Tagged `r0-v1.0`; release notes | **Not started** | Release 0 report/demo is *Other session* (T19). Tag is the guide's act |
| 8 | Guide's adoption test passes | **Not started** | Guide's act |

## 3. Release 0 contents

| Item | Status | Evidence / gap |
|---|---|---|
| Contracts B1 to B8 v1 frozen | **Not ready** | On `main`: B2 course package and B6.3 lesson manifest schemas only. B1 (#87, #94, #101), B3 (#83), B6.2 (#93), B4 (#72, #64, moodle_ws PRs) and others are open |
| `libs/contracts` | **Implemented, not verified** | Example validator merged (#90, #102). Not re-verified here beyond the B8.5 test |
| `libs/media_paths` (B6) | **Implemented, not verified** | #84 and #86 merged; #85 open, excluded |
| `libs/moodle_ws` | **Implemented, not verified** | Pieces merged (#73 to #75, #77, #78); #76, #79, #80 open |
| `libs/lti`, `libs/model_interface` | **Not started** (as far as `main` shows) | Not present under `libs/` on `main` |
| Test data B8.1 | **Blocked** | No `.mbz`; needs Moodle lab (PENDING MOODLE LAB) |
| Test data B8.5 | **Blocked** | 0 of 5 consent lines, no transcripts, 338 s of 1800 s; see B8.5 evidence document |
| Lab VMs ready (A11) | **Unknown / Blocked** | No evidence in the repository |
| Design document per module approved | **Awaiting guide** | `studio.md`, `checker.md`, `grading.md` all `Status: Draft` on `main`; `video.md` see §1 discrepancy |
| CI and repository standards | **Completed** (in place) | `.github/workflows/ci.yml` and review bot exist; CI passed on recent merges |

## 4. App-C verification items

| # | Item | Status | Evidence / gap |
|---|---|---|---|
| 1 | B4 functions on 4.5 and 5.3 | **Blocked** | Needs lab; design lists eleven lab items |
| 2 | Restore merges sections-only backup | **Blocked** | Needs lab; no decision record |
| 3 | CLI restore route | **Blocked** | Needs lab |
| 4 | BBB recording metadata | **Blocked** | *Other session* (T10 in PR #96, T17 in PR #97); both record NOT VERIFIED, neither merged, both with failing `checks`; script self-test passes on synthetic data only; see App-C 4 map |
| 5 | H5P content-type versions | **Blocked** | Needs lab |
| 6 | LTI 1.3 library and licence | **Awaiting guide** | `docs/decisions/0001` not on `main` (PR #83 open) |
| 7 | Caption WER target from baseline run | **Blocked** | Needs B8.5 complete and a speech provider (T8/ADR 0002 is PR #98, Draft) |
| 8 | Licence or consent for every B8.5 video | **Blocked** | 0 of 5; see B8.5 evidence document |
| 9 | Moodle 5.3 AI features | **Not started** | No decision record found |
| 10 | Backup/restore roles | **Blocked** | Needs lab |

## 5. Pull requests (queried 2026-11-16, second pass; 31 open including #104)

Merged and relevant: #82, #84, #86, #89, #90, #92 (merged since the first pass), #99, #100, #102.
New since the first pass, all open: #103 (T9, G-6 evaluation prep), #105 (T19, report and demo,
Draft criteria not found), #106 (T13, pending literature entries). PR #104 (this audit) is a Draft
and has not been reviewed.

| PR | State | Review | Note |
|---|---|---|---|
| #96 App-C 4 record | Open | Changes requested, `needs-rework`, failing check | *Other session* |
| #97 T17 BBB lab verification | Draft | Review required, failing check | *Other session* |
| #98 T8 STT ADR 0002 | Draft | Review required | *Other session*; PROPOSED, pending guide |
| #101, #83, #87 | Open | Review required / awaiting owners | Contract PRs |
| #94, #93 | Open | Approved, `awaiting-owners` | #93 excluded |
| #85 | Open | Approved, `needs-judgement` | Excluded |
| #61 B8.2 sample course | Open | Changes requested, conflicting | |

Remaining open PRs were not individually assessed.

## 6. Approvals and decisions still needed

**Awaiting guide:**
- Approval of the four design documents (`Status: Approved` is the guide's alone).
- Approval reference for the temporary 1800 s B8.5 exception (decision 0004).
- Retention, lab-storage access and withdrawal handling for B8.5 (data-map questions 1 to 3).
- Decision for the LTI library (`0001`), STT options (`0002`, PR #98), and App-C 2/9 records.
- Contract-change approvals (all affected owners and the guide, PRD B.0).
- Resolving the decision-number collision on 0005/0006 (PRs #96, #97).
- Confirming a complete Release 0 task list: the repository has none.

**Awaiting the owner / team:**
- Speaker consent lines, speaker names, file names, transcripts and Harshitha's review for B8.5.
- Written confirmation that the five local files are the official B8.5 set.
- Merging the unmerged B8.5 duration and hash commits (`video/b8-5-dataset-evidence`).

**Blocked by unavailable external services:** the lab Moodle 4.5 and 5.3 sites, a BigBlueButton
server, and a speech provider.

## 7. Ready for final acceptance

**None.** No Release 0 item can be shown as ready for final acceptance on the evidence available.

## 8. Shared-file changes proposed, not made

Not edited, to avoid colliding with other sessions:
- `docs/traceability.md`: add a B8.5 line stating that, as of 2026-11-16, 5 of 5 recordings
  exist locally with verified hashes and durations (338 s), 0 of 5 have consent, and App-C 8 is not
  met. Add pointers to the three documents in `docs/release-0/`.
- `docs/decisions/0004-b8-5-lecture-videos.md`: add the guide's approval reference for the
  temporary exception (guide only).
- `docs/design/video.md`: confirm whether its `Status` line should read `Approved`.

## 9. Checks run for this checklist

| Command | Result |
|---|---|
| `python -m pytest -q libs/contracts/tests/test_b8_5_dataset.py` (first pass) | `71 passed in 18.55s` |
| Same, second pass, after merging `origin/main` `ecb4389` | `71 passed in 5.19s`, exit 0 |
| `python -m pytest -q` (whole repo), system Python with older `jsonschema 4.23.0` / `referencing 0.36.2` than the pins | `4 failed, 2041 passed, 4 skipped`: three failures are the version mismatch against `requirements-dev.txt`, one is the case-insensitivity test below |
| Same, in a clean venv with `requirements-dev.txt` | `1 failed, 2044 passed, 4 skipped` (91 s). The failure, `test_validate_examples.py::test_misnamed_schema_is_reported_with_its_path[Thing.v1.schema.json]`, is in code merged by PR #92 and is probably a Windows case-insensitive-filesystem effect; **not confirmed on Linux CI** |
| `pre-commit run --files docs/release-0/*.md` (first pass) | All applicable hooks passed (end-of-file, whitespace, large files, private key, hardcoded secrets); ruff and file-type hooks skipped (no matching files) |
| `gh pr list` and `gh pr view <n> --json …` | Used for §5 |
| Full `/preflight` (`ruff check .`, `mypy libs`, contract validation, requirement-ID check) | **Not run as a whole.** `ruff` 0.6.9 and `mypy` 2.4.1 are installed but were not executed on the repository; the docs-only change touches no Python |

**Not found in the PRD, so not audited:** a Release 0 "backup" requirement. PRD App-D lists VM image
backups only as a risk mitigation, and §D2 has no backup criterion. Marked UNKNOWN pending the
guide's list of Release 0 tasks; no changelog and no release tag exist (`git tag -l` is empty).

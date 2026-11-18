# Release 0 report chapter: Foundation (T19, revision 2)

> **Update 2026-11-18 (the facts below are stale where they conflict):** PR #96 was **merged** on 2026-11-16 (approved by Harshithamanjunatha, Shraddha and Akshita21-09) and is the carrier of decisions `0005`/`0006` and `verify_bbb.py`. PR #97 was **closed as superseded by #96**: its ADR, README and run record are identical to `main`, its older `verify_bbb.py` is replaced by #96's, and its traceability section is already on `main`. The `0005` numbering collision therefore no longer exists. App-C 4 is **still NOT VERIFIED**: no lab observation exists, so nothing here is a PASS.
> **Update 2026-11-18:** PR #99 recorded SHA-256 values and `ffprobe` durations for five recordings in the B8.5 inventory; PR #125 recorded the guide-approved temporary exceptions in decision 0004 (four lectures, no 1800 s total, for interim demonstration and testing only); PR #126 corrected the status wording. B8.5 stays **PENDING**: file names, speakers, consent lines, transcripts and review are not recorded, so no licence or consent evidence exists yet.
> Also on 2026-11-18: PR #126 merged; draft PR #98 (speech ADR) received the guide questions; PR #129 (lesson processor demo) is open as a Draft awaiting the guide's decision.

**Status:** Draft for review. **Audited against:** `origin/main` at `3abbc02` (2026-11-16), which
did not move between revision 1 and this revision. GitHub state (PRs, issues, runs) was queried on
the same day and changes quickly; re-check before relying on it.
**Release 0 is not tagged.** `git tag` and the GitHub releases list are both empty.

Every statement below rests on a file, a command run for this report, a pull request (PR) or a
GitHub issue comment. Where none exists, the item is marked as missing. Nothing is marked complete
because the work is probably done somewhere else.

## 0. T19's acceptance criteria: not found

**The original T19 description could not be located.** Searched on 2026-11-16:

| Where | Result |
|---|---|
| All files on `main` (`CLAUDE.md`, `docs/PRD.md`, `docs/REVIEW-PROCESS.md`, `GETTING-STARTED.md`, `docs/design/*`, `docs/decisions/*`, `docs/traceability.md`, `.claude/commands/*`) | No task tracker. The only "T19" is a grading test in `docs/design/grading.md:865` (XSS and CSP), which is unrelated |
| All 96 PRs (title, body) and the issue and PR comment search for "T19" | Only this PR (#105) |
| GitHub issues (open and closed) | No T19 |
| Commit messages on all branches | Only this PR's commit |
| Other task numbers | T7, T8, T9, T10, T11, T13, T14, T17, T18, T20 appear in PR titles and bodies (#96 to #98, #103, #104, #106), but **no document defines any of them**. PRs #103 and #104 say the same: "T-numbers are not defined in the repository" |

So the exact T19 criteria are unavailable and nothing here claims to satisfy them. The criteria
below are **provisional**, derived only from the PRD and from the wording of the task request; they
are not T19's own.

| ID | Provisional criterion | Source | Status in this PR |
|---|---|---|---|
| P1 | A report chapter on Release 0 | PRD App-A ("report chapter; final-demo segment") | This document. **Provisional, unreviewed** |
| P2 | A demonstration segment | PRD App-A, E5 | `demo-script.md`. Covers only what exists; E5 as a whole is not demonstrable |
| P3 | Each demonstrated requirement mapped to implementation, test, PR | Task request; PRD E4 | `demo-script.md` section 3 |
| P4 | Evidence is real; gaps are recorded | CLAUDE.md §8 "Prove it works"; PRD E3 | Sections 4 and 5 |
| P5 | Release 0 contents and exit criteria assessed | PRD D1, D2 | Sections 2 and 3 |
| P6 | Traceability work not duplicated | Task request | `traceability-needs.md` |

**Owner action:** supply the real T19 text. Then this table is replaced by a criterion-by-criterion check.

## 1. Classification used

| Class | Meaning |
|---|---|
| 1 Merged and verified | On `main` (base branch confirmed), and its tests pass locally and in hosted CI on `main` |
| 2 Merged, not independently verified | On `main`, but no test or run covers the claim (for example documentation) |
| 3 Implemented, unverified | Exists, but a required check (lab, review, guide) has not happened |
| 4 Open PR | Not on `main`. A PR that shows "MERGED" into another branch is also class 4 |
| 5 Pending | Waiting for a person, a record or evidence |
| 6 Blocked | Cannot proceed until a named dependency exists |
| 7 Not implemented | No file, PR or record found |
| 8 Not applicable | Does not apply to Release 0 |

An open PR is never described as merged implementation.

## 2. Release 0 contents (PRD §D1)

| # | Item | Class | Evidence and gap |
|---|---|---|---|
| 1 | Lab VMs ready (A11) | **5 Pending** | The guide says on issue #55 that the Moodle 4.5 and 5.3 lab sites exist (2026-11-11) and gave an owner an account on 5.3 (2026-11-14). No A11 readiness record exists. **Lab BigBlueButton: no evidence** (records `0005` and `0006` exist only on open PRs #96 and #97, and say the server was not reachable) |
| 2 | Repository, CI, standards | **1** | `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `CLAUDE.md`. Hosted `ci` on `3abbc02`: success (section 5). PRs #52, #59, #60 |
| 3 | Contracts B1 to B8 v1 frozen | **4 / not frozen** | See table 2a |
| 4a | `libs/contracts` | **1** | `libs/contracts/`; PRs #37, #48, #49, #90, #102 (all base `main`) |
| 4b | `libs/media_paths`: validation and `none` signer | **1** | PRs #84, #86. Path templates: #85 **class 4**. PR #38 is an older combined version of #84, #85 and #86 and is still open (owner to close or confirm) |
| 4c | `libs/media_paths`: `hmac` and `s3` signers | **7** | Raise a configuration error. B6.4 needs only `none` for the baseline |
| 4d | `libs/moodle_ws` | **4** | `libs/moodle_ws` does not exist on `main`. #73 to #75, #77, #78 show MERGED but into stacked branches (`grading/b4-guide-decisions`, `grading/moodle-ws-b-redaction`, `grading/moodle-ws-d-client`). Open: #63, #76, #79, #80 |
| 4e | `libs/model_interface` (FR-M-01) | **4** | #35 (draft, partial, stacked on #25). Not on `main` |
| 4f | Speech interface (FR-M-02, B5.4) | **7** | No library code in any PR. The B5 contract is part of open #25 |
| 4g | `libs/lti` | **7** | No library code. The B3 contract and library decision is open #83 |
| 5 | Test data B8 v1 | See table 2b | |
| 6 | App-C verification (10 items) | **5 / 6** | See table 2c |
| 7 | Design document per module approved | **5 Pending (guide)** | On `main` all four say `**Status:** Draft`. The grading design is `In review` on the open PR #62 branch. PR #104's checklist records the video design as "completed (as stated by the owner)" but `docs/design/video.md` on `main` still says Draft, so **the approval is not visible in the file**. Only the guide sets `Approved` |

**2a. Contracts.** On `main`: B1 course package v1 (#23) and B6.3 lesson manifest v1 (#32), plus the
shared relative-path vectors. Class 4 (open): B2 #46, B3 #83, B4 #27 (draft, "unverified") with its
findings #64 and rules #72, B5 #25, B6.2 file shapes #93, B7 #54, and B1 changes #87, #94, #101.
Class 4, but not contract PRs: #31 (B8.4), #33 (B8.6). The freeze requires these to be resolved.

**2b. Test data.**

| Set | Class | Evidence and gap |
|---|---|---|
| B8.1 template course | **2** documentation (#57) / **7** `.mbz` / **6** lab verification | No `.mbz`, no decision record. The guide's 5.3-only waiver is not yet on `main` (open #95, section 7) |
| B8.2 sample course | **4** | #61 (changes requested) |
| B8.3 planted-error courses | **7** | No PR or file found |
| B8.4 synthetic submissions | **4** | #31 (provisional pilot of 6, PRD asks for at least 30) |
| B8.5 lecture videos: checker and tests | **1** | #82, #89; decision 0004 and inventory #99 |
| B8.5 lecture videos: data | **5 Pending** | `main` says PENDING and "No consent lines yet". PR #104 (open, draft) reports 5 local files with matching hashes and 338 s of 1800 s, 0 of 5 consent lines; **not reviewed or merged, and not re-checked here**. B8.5 is not accepted |
| B8.6 model comparison set | **4** | #33 (draft, "one transcript") |

**2c. App-C.**

| # | Item | Class | Evidence and gap |
|---|---|---|---|
| 1 | B4 functions on 4.5 and 5.3 | 6 | Needs lab; `moodle_ws` not on `main` |
| 2 | Restore merge, protected items | 6 | Needs lab and the `.mbz`; no decision record |
| 3 | CLI restore route | 6 | Needs lab |
| 4 | BBB recording metadata | 5 | #96, #97 (both record NOT VERIFIED or PENDING); lab BBB unreachable |
| 5 | H5P versions | 6 | Needs lab |
| 6 | LTI library and licence | 5 | `docs/decisions/0001` not written; #83 open |
| 7 | Caption WER target | 6 | Needs B8.5 complete and a speech provider; ADR 0002 (#98) is PROPOSED; evaluation tooling is draft #103 and refuses `official` mode |
| 8 | Licence or consent for B8.5 | 6 | 0 consent lines (decision 0004). Evidence audit: #104 |
| 9 | Moodle 5.3 AI features | 7 | No record |
| 10 | Backup and restore roles | 6 | Needs lab |

## 3. Release exit criteria (PRD §D2; format of `.claude/commands/release-check.md`)

| # | Criterion | Result | Evidence or gap |
|---|---|---|---|
| 1 | Every FR for the release implemented, linked to passing tests | **Not met** | Release 0 FRs are FR-M-01 and FR-M-02 (PRD §C3, lines 778-779). FR-M-01 is open #35, FR-M-02 is class 7 |
| 2 | Module acceptance criteria (§C.x.7) pass | **Not applicable** | Release 0 has none; its content is §D1. (#104 reaches the same conclusion) |
| 3 | Restore and role-test matrix, 4.5 and 5.3 | **Not met** | No harness, no lab results |
| 4 | Contracts unchanged or additive under B.0 | **Not applicable yet** | Not frozen (2a) |
| 5 | README, `.env.example`, changelog | **Partly met** | `.env.example` and library READMEs exist. **No changelog file** |
| 6 | Security (A13) reviewed; dependency scan clean | **Unknown** | Secret scan passes in CI. No A13 review or dependency scan record |
| 7 | Tagged `r0-v1.0`; release notes | **Not met** | No tag, no release |
| 8 | Guide's adoption test | **Not started** | The guide's act |

**Verdict: not ready to freeze.** This is not an approval and tags nothing. The same verdict is
reached independently by `freeze-readiness-checklist.md` in open PR #104; this report does not copy
it (see `traceability-needs.md`).

## 4. Evidence audit

| Requirement | Required evidence | Available evidence | Missing evidence | Owner / action |
|---|---|---|---|---|
| CI and standards (D1) | Passing CI on `main` | Hosted `ci` run 43824425528 on `3abbc02`: all steps success | none for this item | none |
| Contract validation (EXT-09, B.0 rule 1, E1) | Examples validate; CI fails otherwise | `libs/contracts/validate_examples.py`; run: 3 of 3 pass; tests | Only B1 and B6.3 have schemas | Open contract PRs' owners |
| Media paths (C-08) | Unsafe paths refused; `none` signer | `libs/media_paths/`; demo D4; tests | Path templates (#85); `hmac`, `s3` | Owner of B6 |
| Security and validation (A13, SEC) | Review record; dependency scan | gitleaks and pre-commit in CI | A13 review, dependency scan | Guide, owners |
| Model interface (FR-M-01, FR-M-02) | Library, tests, B5 | #25, #35 open (stacked) | Anything on `main`; speech interface | Student 3 |
| Moodle web services (B4, FR-M-01 area) | Library and lab verification | #27, #64, #72, #63, #76, #79, #80 open | `libs/moodle_ws` on `main`; App-C 1 lab results | Student 3, lab |
| LTI (B3, App-C 6) | Contract, library, licence record | #83 open | Library; `docs/decisions/0001` | Student 2, guide |
| B8.5 data (App-C 8, 7) | Recordings, consent, transcripts, approval of exception | Checker on `main`; evidence audit in #104 (not merged) | 0 of 5 consent lines; transcripts; 1800 s total; approval reference | Speakers, Student 3, guide. **Official B8.5 evidence stays outside this PR** |
| BBB (App-C 4, FR-V-09) | Lab metadata and format output | Check script and NOT VERIFIED records in #96, #97 (open) | Any lab run | Student 4, lab |
| WER (G-6, App-C 7) | Baseline run, target, method | Tooling draft #103 | A complete B8.5; ADR 0002 approval; normalisation rule; provider permission | Guide, Student 3, Student 4 |
| Moodle 4.5 and 5.3 (C-03, D2.3, E2) | Restore and role results on both | Guide's waiver comments for B8.1 and B8.2 (section 7) | All results | Student 1, 2, guide |
| Design approval | `Status: Approved` | none | All four | Guide |
| Release readiness (D2.5 to 8) | Changelog, notes, tag, adoption test | none | All | Guide, owners |

## 5. Verification record

**Local (Windows 11, Python 3.12.5, fresh virtual environment from `requirements-dev.txt`, clean
worktree of `3abbc02`), run 2026-11-16.** The full command list and exit codes are in section 7 of
`demo-script.md`; summary: validator 3 of 3, `pytest -q -rs` 2038 passed and 4 skipped (symbolic
links unavailable on this host), CI-script tests 137 passed, `mypy libs` clean in 30 files.

**Hosted (GitHub Actions), separate from the above.** `ci` run 43824425528, event `push` on `main`,
commit `3abbc022d051e4ec6b7f720cbba4b26180985a2c`, 2026-11-16T07:31Z: conclusion success. Steps
succeeded: pre-commit, gitleaks over the whole history, mypy, contract examples, unit tests
(`2042 passed`), "Symlink tests must pass, not skip" ("All three symlink tests passed"), CI-script
tests (137 passed). The four symlink tests skipped locally therefore **did run and pass on Linux CI**
(2038 + 4 = 2042). For PR #105's own head `7ce91e8`, `ci` run 43827139494 also succeeded.

## 6. What revision 1 got wrong (corrected here)

| Revision 1 said | Correct |
|---|---|
| B4 and B5 have "no PR found" | B4 is #27, #64, #72 and the moodle_ws PRs; B5 is #25. All open |
| B8.4 has no PR | #31 (open); B8.6 is #33 (open) |
| Hosted CI for `3abbc02` "unconfirmed" | Confirmed success (section 5) |
| B8.5 "no lecture is recorded" | That is what `main` says. #104 (unmerged) reports 5 local files. Both are stated in 2b |
| #35 listed without its base | Stacked on #25, not on `main` |
| Moodle: "#95 aligns docs to a 5.3-only decision while the PRD says 4.5 and 5.3" | The decision is scoped and recorded as a waiver; see section 7 |
| Design documents: all Draft | True on `main`; added the grading `In review` branch and the video discrepancy |

## 7. Decisions and dependencies (not resolved here)

| Decision or dependency | Authority | Impact if open |
|---|---|---|
| **Moodle versions.** PRD C-03, D2.3 and E2 still say 4.5 **and** 5.3, unchanged. The guide decided on issue #55 (2026-11-14, 12:19 UTC) that B8.1 builds and tests on **5.3 only**, with 4.5 "not tested: waived by the guide for Release 0" (the PR #95 description adds "confirmed as a C-03 deviation 2026-11-15"; I did not find that comment itself), and on PR #61 (2026-11-16, answer A5) extended the waiver to B8.2, with "C-03 returns in Release 1". The waiver is scoped to B8.1 and B8.2 and the harness is unaffected. Docs on `main` still say "build on 4.5": `docs/traceability.md` lines 166-167 and `testdata/b8-1-template-course/README.md`. PR #95 (approved, `needs-judgement`) corrects them. Until it merges, `main` contradicts the guide | Guide (decision made); #95 merge: owner and reviewers | Report cannot state a tested Moodle version. No Moodle result exists for either |
| Approval reference for the **1800 s B8.5 exception**: decision 0004 says PENDING, "reported by the developer" | Guide | B8.5 cannot be called complete; App-C 7, 8 stay blocked |
| Retention, lab storage and withdrawal handling for B8.5 (data-map questions) | Guide | Consent text depends on it |
| Decision-number collision: `0005` and `0006` both cover App-C 4 across #96 and #97 | Guide or owners | One of the records is renumbered after rebase |
| Approval of four design documents | Guide only | Feature code cannot start; D1 not met |
| LTI library (`0001`), STT options (`0002`, #98), App-C 2 and 9 records | Guide | App-C 2, 6, 7, 9 |
| Contract changes: B1/B2 section `idnumber` conflict (issue #65, PR #101), B3 (issue #58), B7 (issue #44), B2 (issue #45), checker CK-01 to CK-13 (issue #67); open B6 questions in `docs/design/video.md` §4 ("TO DECIDE") | All affected owners and the guide (PRD B.0) | Freeze cannot happen |
| Open B8.1 questions (issue #55) | Guide | App-C 2 |
| Real T19 criteria | Owner | This chapter stays provisional |

## 8. Known limitations of the code on `main`

- `media_paths` has only the `none` signer. Windows reserved names, Unicode normalization and a
  maximum path length are not enforced in v1 (guide decision, `docs/traceability.md`).
- The B1 validator checks idnumber uniqueness within one package only; reuse across versions is
  reported in every report as `idnumber_reuse_not_checked`. It reports 8 rules as not checked.
- The contract validator does not find a dangling `$ref` no example reaches and checks `date`, not
  `date-time` (`libs/contracts/README.md`).
- Only two contract schemas exist on `main`; no module code exists (`modules/*` hold only `CLAUDE.md`).
- No changelog.

## 9. Not claimed

No evidence exists for: BigBlueButton lab verification, a word-error-rate result, B8.5 acceptance,
Moodle restore or web-service results on either version, any LTI launch, or any AI or speech call.
This chapter claims none of them.

## 10. PRD §E5 final demonstration

Steps 1 to 6 need Releases 1 to 4 and fresh lab sites, and none exists. Release 0 can show only
the foundation. See `demo-script.md` section 5.

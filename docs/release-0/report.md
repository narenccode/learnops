# Release 0 report chapter: Foundation (T19, revision 3)

**Status:** Draft for review. **Audited against:** `origin/main` at `8559c4d` (2026-11-20; first at `5f3a794`,
refreshed after #130, #142, #145 and #147 merged). The previous revision audited `3abbc02`
(2026-11-16); 41 commits have merged since, and **the PRD changed
what Release 0 contains** (PRs #113 and #116), so this revision re-states the contents list. GitHub
state (PRs, issues, runs) was queried on 2026-11-20 and changes quickly; re-check before relying on it.
**Release 0 is not tagged.** `git tag` and the GitHub releases list are both empty.

Every statement below rests on a file, a command run for this report, a pull request (PR) or a
GitHub issue comment. Where none exists, the item is marked as missing. Nothing is marked complete
because the work is probably done somewhere else.

## 0. T19's acceptance criteria: still not found

**The original T19 description could not be located.** Searched again on 2026-11-20:

| Where | Result |
|---|---|
| All files on `main` | No task tracker. `T19` appears in `docs/design/grading.md` as a **test identifier** ("T19 XSS and CSP"), a different meaning that must not be confused with this task, and in `modules/video/demo/README.md` ("the T19 branch") |
| GitHub issues (open and closed), search "T19" | No result. Issue #107 ("Plan for tonight and tomorrow: what to show at the evaluation") defines **five demos D1 to D5** but gives no T-numbers |
| Pull requests | Only this PR (#105) names T19 as a task |
| Other task numbers | T7, T8, T9, T10, T11, T13, T14, T17, T18, T20 appear in PR titles and bodies, but **no document defines any of them** |

So the exact T19 criteria are unavailable and nothing here claims to satisfy them. The criteria
below are **provisional**, derived only from the PRD and the wording of the task request.

| ID | Provisional criterion | Source | Status in this PR |
|---|---|---|---|
| P1 | A report chapter on Release 0 | PRD App-A ("report chapter; final-demo segment") | This document. **Provisional, unreviewed** |
| P2 | A demonstration segment | PRD App-A, E5 | `demo-script.md`. Covers only what exists; E5 as a whole is not demonstrable |
| P3 | Each demonstrated requirement mapped to implementation, test, PR | Task request; PRD E4 | `demo-script.md` section 3 |
| P4 | Evidence is real; gaps are recorded | CLAUDE.md §8 "Prove it works"; PRD E3 | Sections 4 and 5 |
| P5 | Release 0 contents and exit criteria assessed | PRD D1, D2 | Sections 2 and 3 |
| P6 | Traceability work not duplicated | Task request | `traceability-needs.md` |

**Working criteria (the guide's assistant, 2026-11-19):** the original T19 text is not in the repository and the guide has no separate copy. P1 to P6 are therefore the **working acceptance criteria**, and this chapter **does not claim to satisfy T19**. If the original turns up, it replaces them and this table becomes a criterion-by-criterion check. The guide also accepted the report and demo as documentation, after a status refresh against `main` (this revision), not as a completion claim.

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

## 2. Release 0 contents (PRD §D1, as it reads on 2026-11-20)

PRD §D1 now lists for Release 0: lab VMs ready (A11); repository, CI, coding standards; contracts
B1 to B8 v1 **frozen**; shared libraries **`contracts` and `media_paths`**; test data B8 v1; App-C
items **6 and 9**; a design document per module approved. `lti`, `moodle_ws`, `model_interface` and
the other App-C items belong to the first release that uses them, and "the Release 0 notes list
where each one goes" (not written yet).

| # | Item | Class | Evidence and gap |
|---|---|---|---|
| 1 | Lab VMs ready (A11) | **5 Pending** | The guide said on issue #55 that the Moodle 4.5 and 5.3 lab sites exist (2026-11-11) and gave an owner an account on 5.3 (2026-11-14). No A11 readiness record exists |
| 2 | Repository, CI, standards | **1** | `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `CLAUDE.md`. Hosted `ci` succeeded on `main` `5f3a794` and the two commits before it (section 5) |
| 3 | Contracts B1 to B8 v1 frozen | **4 / not frozen** | See table 2a |
| 4a | `libs/contracts` | **1** | `libs/contracts/` (PRs #37, #48, #49, #90, #92, #102, #131) |
| 4b | `libs/media_paths` (validation, templates, `none` signer) | **1** | PRs #84, #85, #86, all merged. The demo D4 (#117) exercises it |
| 4c | `libs/media_paths`: `hmac` and `s3` signers | **7** | Raise a configuration error by design. B6.4 needs only `none` for the baseline |
| 5 | Test data B8 v1 | See table 2b | |
| 6 | App-C items 6 and 9 | **5** | See table 2c |
| 7 | Design document per module approved | **5 Pending (guide), 1 of 4** | On `main`: `studio.md` says `Approved` (PR #147, 2026-11-20); `grading.md` says `In review`; `checker.md` and `video.md` say `Draft`. Draft PR #140 completes `video.md` and records the guide's answers; the approval is the guide's |

**Not Release 0 any more (PRD change):** `libs/lti` (class 7; contract and ADR only, ADR `Proposed`),
`libs/moodle_ws` (class 4; pieces merged into stacked branches, PRs #73 to #78, and open PRs #76,
#79, #80, #63), `libs/model_interface` and the speech interface (class 4 / 7; draft #35, B5 contract
merged in #25). `libs/speech_eval` (G-6 preparation, #103) is merged and is not a Release 0 item.

**2a. Contracts.** On `main`: B1 course package (#23, with #87, #94, #101, #110 vectors and rules),
B2 course model (#46), B3 LTI launch (#83), B4 Moodle web services (#27, "draft, unverified"), B5
model interface (#25), B6.3 lesson manifest (#32) and B6.2 chapters, slides and cues (#93), B7 H5P
practice (#54, draft). Open: B4 follow-ups #64 and #72 (the guide's findings and decisions). The
freeze requires every contract's owners and the guide to approve (PRD B.0); no approval is recorded
as a freeze, and draft PR #115 prepares the post-freeze CODEOWNERS rule.

**2b. Test data.**

| Set | Class | Evidence and gap |
|---|---|---|
| B8.1 template course | **2** documentation (#57, decision 0009) / **7** `.mbz` / **6** lab verification | No `.mbz`. The guide's 5.3-only waiver for Release 0 is on `main` (#95); PR #130 (merged) added a register of version exceptions in `docs/decisions/README.md` |
| B8.2 sample course | **1** | Package and dataset test merged (#61, decision 0010) |
| B8.3 planted-error courses | **7** | No PR or file found |
| B8.4 synthetic submissions | **4** | #31 (provisional pilot of 6; the PRD asks for at least 30) |
| B8.5 lecture videos: checker and tests | **1** | #82, #89; decision 0004 and the inventory hashes (#99) |
| B8.5 lecture videos: data | **5 Pending** | `main` says PENDING: five hashes, no duration, no consent line, no transcript. Decision 0004 records the guide's temporary exceptions (four lectures, no 1800 s total; issue #121, PR #125). #104 (draft) reports 5 local files with matching hashes, 338 s of 1800 s and 0 of 5 consent lines; **not reviewed** |
| B8.6 model comparison set | **4** | #33 (draft, "one transcript") |

**2c. App-C.**

| # | Item | Release (PRD) | Class | Evidence and gap |
|---|---|---|---|---|
| 1 | B4 functions on 4.5 and 5.3 | First release that relies on it | 6 | Needs lab; `moodle_ws` not on `main` |
| 2 | Restore merge, protected items | Same | 6 | Needs lab and the `.mbz`; no decision record |
| 3 | CLI restore route | Same | 6 | Needs lab |
| 4 | BBB recording metadata | Release 3 (FR-V-09) | 5 | Records `0005` and `0006` merged (#96, NOT VERIFIED); #97 closed as superseded; lab BBB unreachable |
| 5 | H5P versions | First release that uses them | 6 | Decision 0008; needs lab |
| 6 | LTI library and licence | **Release 0** | 5 | `docs/decisions/0001-lti-library.md` exists but is `Proposed`, pending the guide's review; a second file is also numbered `0001` |
| 7 | Caption WER target | Release 3 (G-6) | 6 | Needs B8.5 complete and a speech provider; ADR 0002 (#98) is `PROPOSED`; evaluation tooling merged (#103) and refuses `official` mode |
| 8 | Licence or consent for B8.5 | First release that relies on it | 6 | 0 consent lines (decision 0004). Evidence audit: #104 |
| 9 | Moodle 5.3 AI features | **Release 0** | 7 | No record. The guide's answer on #140 puts the check in scope for Student 4 |
| 10 | Backup and restore roles | First release that relies on it | 6 | Needs lab |

## 3. Release exit criteria (PRD §D2; format of `.claude/commands/release-check.md`)

| # | Criterion | Result | Evidence or gap |
|---|---|---|---|
| 1 | Every FR for the release implemented, linked to passing tests | **Not met / unclear** | The PRD no longer lists a Release 0 FR: FR-M-01 and FR-M-02 go with the first release that uses them. Traceability rows exist for the contracts, `media_paths`, the example checkers and the B8 sets |
| 2 | Module acceptance criteria (§C.x.7) pass | **Not applicable** | Release 0 has none; its content is §D1 |
| 3 | Restore and role-test matrix, 4.5 and 5.3 | **Not met** | No harness, no lab results |
| 4 | Contracts unchanged or additive under B.0 | **Not applicable yet** | Not frozen (2a) |
| 5 | README, `.env.example`, changelog | **Partly met** | `.env.example` and library READMEs exist. **No `CHANGELOG.md` and no `docs/releases/` folder** (`docs/RELEASING.md` step 2 requires both) |
| 6 | Security (A13) reviewed; dependency scan clean | **Unknown** | Secret scan passes in CI. No A13 review or dependency scan record |
| 7 | Tagged `r0-v1.0`; release notes | **Not met** | No tag, no release, no `docs/releases/r0.md` |
| 8 | Guide's adoption test | **Not started** | The guide's act |

**Verdict: not ready to freeze.** This is not an approval and tags nothing. The same verdict is
reached independently by `freeze-readiness-checklist.md` in open PR #104; this report does not copy
it (see `traceability-needs.md`).

## 4. Evidence audit

| Requirement | Required evidence | Available evidence | Missing evidence | Owner / action |
|---|---|---|---|---|
| CI and standards (D1) | Passing CI on `main` | Hosted `ci` on `5f3a794`: success | none for this item | none |
| Contract validation (EXT-09, B.0 rule 1, E1) | Examples validate; CI fails otherwise | `libs/contracts/validate_examples.py`: 26 examples, 10 schemas, 26 passed (run for this report); tests | Freeze and owner approvals | Contract owners, guide |
| Media paths (C-08) | Unsafe paths refused; `none` signer | `libs/media_paths/`; demo D4 (#117); tests | `hmac` and `s3` signers (not needed for the baseline) | Student 4 |
| Security and validation (A13, SEC) | Review record; dependency scan | gitleaks and pre-commit in CI | A13 review, dependency scan | Guide, owners |
| Model interface (FR-M-01, FR-M-02) | Library, tests, B5 | B5 contract merged (#25); draft #35 | Library on `main`; speech interface (not Release 0) | Student 3 |
| Moodle web services (B4, FR-M-01 area) | Library and lab verification | B4 contract merged (#27); #64, #72, #63, #76, #79, #80 open | `libs/moodle_ws` on `main`; App-C 1 lab results (not Release 0) | Student 3, lab |
| LTI (B3, App-C 6) | Contract, library, licence record | B3 contract merged (#83); ADR 0001 `Proposed` | Guide review of the library choice | Student 2, guide |
| B8.5 data (App-C 8, 7) | Recordings, consent, transcripts, approval of exception | Checker on `main`; exceptions in decision 0004; evidence audit in #104 (not merged) | 0 of 5 consent lines; transcripts; 1800 s total; five-lecture rule | Speakers, Student 3, guide |
| BBB (App-C 4, FR-V-09) | Lab metadata and format output | Check script and NOT VERIFIED records on `main` (#96) | Any lab run | Student 4, lab |
| WER (G-6, App-C 7) | Baseline run, target, method | Tooling merged (#103) | A complete B8.5; ADR 0002 approval; normalisation rule; provider permission | Guide, Student 3, Student 4 |
| Moodle 4.5 and 5.3 (C-03, D2.3, E2) | Restore and role results on both | Guide's waiver comments for B8.1 and B8.2 (section 7); register in `docs/decisions/README.md` (#130, merged) | All results | Student 1, 2, guide |
| Design approval | `Status: Approved` | none | All four | Guide |
| Release readiness (D2.5 to 8) | Changelog, notes, tag, adoption test | none | All | Guide, owners |

## 5. Verification record

**Local (Windows 11, Python 3.12.5, fresh virtual environment from `requirements-dev.txt`, worktree
of `origin/main` `5f3a794` plus this PR), run 2026-11-20.** The command list and exit codes are in
section 7 of `demo-script.md`; summary: validator 26 of 26 examples passed, `pytest -q -rs` 1 failed, 4103 passed, 5 skipped (the one failure is a Windows-only case-insensitive-filesystem test; CI on Linux is the reference), CI-script
tests 88 passed, `mypy libs` clean in 56 source files.

**Hosted (GitHub Actions), separate from the above.** `gh run list --branch main` on 2026-11-20:
workflow `ci` succeeded on `5f3a794`, `d1faffc` and `d28018f` (the three latest commits on `main`).
Per-step detail for the earlier run on `3abbc02` (run 43824425528, 2026-11-16) is unchanged and was
not re-fetched: pre-commit, gitleaks over the whole history, mypy, contract examples, unit tests,
"Symlink tests must pass, not skip" and the CI-script tests all succeeded.

## 6. What revision 2 got wrong or left stale (corrected here)

| Revision 2 said | Correct on 2026-11-20 |
|---|---|
| B4 and B5 are open PRs | B4 contract #27 and B5 contract #25 are **merged**; only the B4 follow-ups #64, #72 and library PRs are open |
| Path templates (#85), B6.2 (#93) are open | Both merged; #38 closed as superseded |
| B3 contract and `docs/decisions/0001` "not written"; #83 open | #83 merged; `0001-lti-library.md` exists, `Proposed` |
| B2 (#46), B7 (#54), B8.2 (#61), #95 open | All merged |
| App-C 4: #96 and #97 open | #96 merged (NOT VERIFIED); #97 closed as superseded |
| WER tooling "draft #103" | Merged |
| Release 0 includes `lti`, `moodle_ws`, `model_interface` and App-C items 1 to 10 | PRD §D1 now limits Release 0 to `contracts`, `media_paths` and App-C 6 and 9 |
| 1800 s exception: "PENDING, reported by the developer" | Decision 0004 cites the guide's confirmation on issue #121 (PR #125) and adds a four-lecture exception; the set is still not complete |
| "No lecture is recorded" | Corrected on `main` (#126): five local files are identified and hashed |

## 7. Decisions and dependencies (not resolved here)

| Decision or dependency | Authority | Impact if open |
|---|---|---|
| **Moodle versions.** PRD C-03, D2.3 and E2 still say 4.5 **and** 5.3. The guide decided on issue #55 that B8.1 builds and tests on **5.3 only**, with 4.5 waived for Release 0 (decision 0009; #95 merged); PR #130 (merged) added one register | Guide | Row D2.3 stays "not met" |
| The date of the guide's earlier approval of the 1800 s exception | Guide | B8.5 cannot be called complete; the five-lecture rule still holds |
| Retention, lab storage, names and transcripts, and processing services for B8.5 (data-map questions) | **Decided by the guide** (2026-11-19, confirmed in his own words 2026-11-20) and recorded in `docs/decisions/0011-b8-5-data-handling.md` in the open audit PR #104 (not merged); the data map follows it. What the lab endpoint keeps is not recorded yet (ADR 0002, PR #98) | Speakers are told about withdrawal and Git history before writing the consent line |
| Which of the two `0001` decision records is renumbered | Guide | Decision records are ambiguous |
| Approval of the three remaining design documents (`studio.md` is `Approved`, PR #147) | Guide only | Feature code cannot start for those modules; D1 not met |
| LTI library (`0001`), STT options (`0002`, #98), App-C 9 record | Guide | App-C 6 and 9 (Release 0) |
| The Release 0 notes that list where each moved item goes | Owners, guide | PRD §D1 requires them |
| Contract changes and the freeze (B.0); open questions on issues #44, #45, #58, #65, #67 | All affected owners and the guide | Contracts not frozen |
| Real T19 criteria | Owner | This chapter stays provisional |

## 8. Known limitations of the code on `main`

- `media_paths` has only the `none` signer. Windows reserved names, Unicode normalization and a
  maximum path length are not enforced in v1 (guide decision, `docs/traceability.md`).
- The B1 validator checks idnumber uniqueness within one package only; reuse across versions is
  reported as `idnumber_reuse_not_checked`. It reports several rules as not checked (8 for the
  example package).
- The contract validator does not find a dangling `$ref` no example reaches and checks `date`, not
  `date-time` (`libs/contracts/README.md`).
- Contract schemas exist on `main` for B1 to B7 (10 schemas); only `modules/video/demo` has module
  code (the D4 demo); the other `modules/*` hold documentation.
- No changelog and no release notes.

## 9. Not claimed

No evidence exists for: BigBlueButton lab verification, a word-error-rate result, B8.5 acceptance,
Moodle restore or web-service results on either version, any LTI launch, or any AI or speech call.
This chapter claims none of them.

## 10. PRD §E5 final demonstration

Steps 1 to 6 need Releases 1 to 4 and fresh lab sites, and none exists. Release 0 can show only
the foundation. See `demo-script.md` sections 1 and 4. The five evaluation demos D1 to D5 planned
in issue #107 are separate from this script; D4 (video paths) and D5 (course input) are on `main`.

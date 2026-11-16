# Release 0 report chapter: Foundation (T19 draft)

**Status:** Draft for review. **Written against:** `origin/main` at `3abbc02` (2026-11-16).
**Release:** Release 0 (PRD §D1). **Not tagged:** no `r0-v1.0` tag or GitHub release exists.

This chapter reports what the repository actually contains for Release 0. It makes no claim that
is not backed by a file, a command run for this report, or a pull request (PR). Where evidence is
missing it says so (section 6). Where a claim would need a lab, a recording or a guide decision
that does not exist in the repository, the item is listed as pending, blocked or not implemented.

## 0. About T19 and its acceptance criteria

The task tracker that defines T19 is **not in the repository, the GitHub issues or the PR history**.
The only "T19" in the repository is an unrelated grading test in `docs/design/grading.md:865`
(XSS and CSP). T8 and T17 appear in PR titles and `docs/decisions/0005`/`0006`, but the tracker
itself was not found. T19's exact acceptance criteria are therefore **unknown to this report**.

What this report used instead (all from `docs/PRD.md`):

| Source | Says |
|---|---|
| App-A | Everyone owes a "report chapter; final-demo segment" |
| §D1 | What Release 0 contains |
| §D2 | Release exit criteria (1–8) |
| §E5 | Final demonstration, about 20 minutes, fresh lab sites |
| `.claude/commands/release-check.md` | The pass / fail / unknown format used in section 4 |

**Action for the owner:** compare this chapter with the real T19 text and tell me what differs.

## 1. Status vocabulary

| Label | Meaning here |
|---|---|
| **Merged (main)** | Merged into `main`; I confirmed the base branch is `main` |
| **Merged (stacked only)** | PR shows MERGED but its base was another branch; the code is **not** on `main` |
| **Implemented, unverified** | Code or text exists, but a required check (lab, review, guide) has not happened |
| **Open PR** | PR exists and is not merged |
| **Pending** | Waiting for a person, a record or evidence |
| **Blocked** | Cannot proceed until a named dependency is delivered |
| **Not implemented** | Nothing exists |

## 2. Release 0 contents against what exists (PRD §D1)

| # | Release 0 item | Status | Evidence |
|---|---|---|---|
| 1 | Lab VMs ready (A11) | **Not implemented / no evidence** | No lab record in the repository. `docs/decisions/0006` says the lab BigBlueButton was not reachable from the writing sessions |
| 2 | Repository, CI, coding standards | **Merged (main)** | `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `CLAUDE.md`; PRs #59 (full gitleaks), #60 (licence rule), #52 (test discovery); local run in section 3 |
| 3 | Contracts B1–B8 v1 frozen | **Partly merged, not frozen.** Merged on `main`: B1 course package v1 (#23), B6.3 lesson manifest v1 (#32), shared relative-path vectors. **Open PRs:** B2 #46, B3 #83, B7 #54, B6.2 chapters/slides/cues #93, B1 changes #87 #94 #101. **No PR found:** B4 (only rules R1–R11 in #72), B5 | PR list; `contracts/` on `main` holds two schemas. Freeze has not happened |
| 4a | Library `contracts` | **Merged (main)** | `libs/contracts/`; PRs #37 #48 #49 (B1 validator), #90 (engine), #102 (repository-wide validator). #91 shows MERGED but into a stacked branch; #102 replaced it |
| 4b | Library `media_paths` | **Merged (main), partly.** Path and slug validation (#84), `none` signer (#86). Path **templates** (#85) is still an **open PR**. `hmac` and `s3` signers: **not implemented** (B6.4 needs only `none` for the baseline) | `libs/media_paths/` |
| 4c | Library `moodle_ws` | **Merged (stacked only)** for parts A, B, C, E, L1 (#73–#75, #77, #78). **Not on `main`**: `libs/moodle_ws` does not exist there. Open PRs #63 #76 #79 #80 | `ls libs` on `main` shows only `contracts`, `media_paths` |
| 4d | Libraries `model_interface` (FR-M-01, FR-M-02) | **Open PR** #35 (FR-M-01 skeleton, partial). FR-M-02 speech interface: **no PR found** | PR list |
| 4e | Library `lti` | **No PR found** (B3 contract is open, #83) | PR list |
| 5 | Test data B8 v1 | **Mixed.** B8.5 checker and tests: merged. B8.5 data itself: **Pending**. B8.1: documentation only, no `.mbz`. B8.2: open PR #61. B8.3, B8.4: no PR found | `testdata/`, section 5 |
| 6 | Verification of assumptions (App-C 1–10) | **Mostly pending.** Only decision `0004` (B8.5) is on `main`. App-C 4: records `0005`/`0006` are on **open** PRs #96 #97 and say NOT VERIFIED / PENDING. App-C 7: depends on B8.5. App-C 6 (LTI library): `docs/decisions/0001` not written | `docs/decisions/` on `main` |
| 7 | Design document per module approved | **Not met.** All four documents say `Status: Draft`; only the guide sets `Approved` | `docs/design/*.md` line 6–7 |

## 3. Checks run for this report

Run on a clean worktree of `origin/main` (`3abbc02`), Windows, Python 3.12.5, in a fresh virtual
environment from `requirements-dev.txt` plus `mypy`. Date: 2026-11-16.

| Check | Result |
|---|---|
| `python libs/contracts/validate_examples.py` | 3 examples, 2 schemas: 3 passed, 0 failed |
| `pytest -q -rs` (whole repository) | **2038 passed, 4 skipped.** The 4 skips are symbolic-link tests ("not available here (Windows without developer mode)") |
| `pytest -q .github/scripts/tests` | 137 passed |
| `mypy libs` | Success: no issues in 30 source files |

**Not run:** `pre-commit` (format, lint), `gitleaks`, and CI's "symlink tests must pass, not skip"
step. The four skipped symlink tests are exactly what that CI step guards, so **they are not
verified by me**; the Linux CI is the place that proves them. I did not find a completed hosted `ci`
run for `3abbc02` in the last four workflow runs on `main` (only `guide-inbox` runs appeared), so
the hosted result is **unconfirmed**.

## 4. Release exit criteria (PRD §D2)

| # | Criterion | Result | Evidence or gap |
|---|---|---|---|
| 1 | Every FR for the release implemented and linked to passing tests | **Unknown / not met.** Release 0 has no FR of its own except FR-M-01 and FR-M-02 (PRD §C3). FR-M-01 is an open PR; FR-M-02 has none | `docs/PRD.md:778-779` |
| 2 | Acceptance criteria pass | **Not met** (see section 2) | |
| 3 | Restore and role-test matrix on Moodle 4.5 and 5.3 | **Not met.** No harness exists; the matrix belongs to Release 1 onwards | `modules/*` hold only `CLAUDE.md` |
| 4 | Contracts unchanged, or additive under B.0 | **Not applicable yet.** The freeze has not happened | |
| 5 | README, `.env.example`, changelog | **Partly.** `libs/contracts/README.md` and `libs/media_paths/README.md` exist. No changelog file found | |
| 6 | Security reviewed; dependency scan clean | **Unknown.** Secret scan is in CI; no dependency scan or A13 review record found | |
| 7 | Tagged `rN-v1.0`; release notes | **Not met.** No tag | `git tag` is empty |
| 8 | Guide's adoption test | **Not met.** Done by the guide after the tag | |

**One-line verdict: Release 0 is not ready to freeze.** Blockers: items 1, 3, 6 and 7 of section 2
and criteria 1, 2, 7 and 8 above. This verdict follows `.claude/commands/release-check.md`; it is
not an approval and tags nothing.

## 5. Evidence for the claims the demonstration makes

Every row is something I ran (section 3 of `demo-script.md` has the commands and output).

| Claim | Status | Implementation | Test | PR |
|---|---|---|---|---|
| Every contract example validates against its schema; CI fails otherwise | **Merged (main)** | `libs/contracts/validate_examples.py`, `example_check.py` | `test_validate_examples.py`, `test_example_check.py` | #90, #102 |
| A B1 course package is validated, and a protected idnumber is rejected with a clear message | **Merged (main)** | `libs/contracts/validate.py`, `course_rules.py` | `test_validate_course.py`, `test_validate_package.py` | #37, #48, #49 |
| The B6.3 lesson manifest schema rejects unsafe paths and a lesson with no English caption | **Merged (main)** | `contracts/lesson-manifest.v1.schema.json` | `test_lesson_manifest_v1.py` | #32 |
| Unsafe media paths are refused; the `none` signer builds a relative-path URL | **Merged (main)** | `libs/media_paths/validation.py`, `signing.py` | `test_validation.py`, `test_signing.py` | #84, #86 |
| The B8.5 checker reports the lecture set honestly as PENDING | **Merged (main)**; the data is **pending** | `libs/contracts/tests/test_b8_5_dataset.py` | same file | #82, #89, #99 |
| Guide decision 0004: consent sentence, 1800 s threshold, temporary exception | **Merged (main)** | `docs/decisions/0004-b8-5-lecture-videos.md` | covered by the dataset test | #99 |

Test names for each row are listed in `docs/traceability.md` on `main`; this report does not copy
them (see `traceability-needs.md` for the overlap).

### B8.5 state (what is and is not true)

- The checker and its tests are merged. The data set is **PENDING**: no lecture is recorded, no
  consent line is written, no transcript is typed (`testdata/README.md:21-22`, decision `0004`
  "No consent lines yet").
- The guide's temporary exception to the 1800 s minimum has **no approval reference**
  (`0004`: "PENDING. It was reported by the developer").
- Because of this, **no caption word error rate (G-6, App-C 7) exists**, and no speech-to-text
  evaluation was run. The B8.5 data is not claimed as accepted. Official B8.5 acceptance evidence is
  kept out of this PR by design.

## 6. Missing evidence (not fabricated)

| Missing | Needed for | Who or what provides it |
|---|---|---|
| T19's real acceptance criteria | This task | The task tracker; owner |
| Lab Moodle 4.5 / 5.3 sites and a lab BigBlueButton running | Items 1, App-C 1–5, 9, 10, E5 | Student 2 (lab sites), Student 4 (BBB) |
| BigBlueButton recording metadata and video-format location | App-C 4, FR-V-09 | Output of `verify_bbb.py` from a lab run (PRs #96, #97 say NOT VERIFIED) |
| Recorded lectures, hashes, durations, consent lines, reviewed transcripts | B8.5, App-C 8 | Speakers; Student 3 reviews transcripts |
| Guide's approval reference for the 1800 s exception | Decision `0004` | Guide |
| Caption word error rate baseline and G-6 target | App-C 7 | A run on real B8.5 data and a chosen speech provider |
| Speech-to-text options decision (ADR 0002) | App-C 7, FR-M-02 | PR #98 is PROPOSED, pending the guide |
| LTI 1.3 library choice (`0001`), and B3 contract | App-C 6 | PR #83 open |
| Moodle 5.3 AI-feature overlap record | App-C 9 | Not started |
| Moodle web-service functions on 4.5 and 5.3 | App-C 1 | Needs lab; depends on `moodle_ws` reaching `main` |
| Moodle Restore merge and protected items; B8.1 `.mbz` | App-C 2, C1.7 | Needs lab and the `.mbz` |
| CLI restore route; H5P versions; backup roles | App-C 3, 5, 10 | Needs lab |
| Approved design documents (all four are Draft) | D1, CLAUDE.md §6a | Guide |
| Hosted CI result for `3abbc02` and Linux run of the symlink tests | Section 3 | GitHub Actions |
| Dependency scan; A13 security review | D2.6 | Not started |
| Changelog; release notes; tag | D2.5, D2.7 | After the above |

**Not claimed anywhere in this chapter:** BigBlueButton lab verification, a successful WER
evaluation, B8.5 acceptance, or any Moodle integration. None has evidence in the repository.

## 7. Known limitations

- `libs/media_paths` implements only the `none` signer. `hmac` and `s3` raise a configuration error
  (planned). `docs/traceability.md` notes that Windows reserved names, Unicode normalization and a
  maximum length are **not** enforced in v1 (guide decision).
- The B1 validator checks idnumber uniqueness **within one package** only. Reuse across versions is
  listed in every report as `idnumber_reuse_not_checked`.
- The contract validator does not find a dangling `$ref` that no example reaches, and checks
  `date` but not `date-time` (`libs/contracts/README.md`).
- Windows runs skip the four symlink tests; only Linux CI can prove them.
- The review process depends on bots and the guide inbox; none of that is part of Release 0 scope.
- Nothing in `modules/` is implemented; each holds only `CLAUDE.md`.

## 8. Dependencies and outstanding guide decisions

| Item | Where | Needed by |
|---|---|---|
| Open B6 questions: poster field, required manifest fields, `source` for BBB intake, camera/screen-only lessons, scope of B6 schemas | `docs/design/video.md` "TO DECIDE" (§4) | B6 freeze |
| B1/B2 conflict: section `idnumber` required in B1 but null in B2 | Issue #65, PR #101 | B1/B2 freeze |
| B3 LTI launch clarifications | Issue #58, PR #83 | B3 freeze, App-C 6 |
| B7 H5P clarifications | Issue #44, PR #54 | B7 freeze |
| B8.1 template backup clarifications | Issue #55 | App-C 2 |
| Course Checker architectural decisions CK-01–13 | Issue #67 | Checker design approval |
| B2 size limit / draft handling | Issue #45 | B2 |
| Approval reference for the B8.5 1800 s exception | Decision `0004` | B8.5 completion |
| Speech-to-text options ADR | PR #98 | App-C 7, FR-M-02 |
| `docs/decisions/0005`/`0006` both cover App-C 4 (two numbers for one topic across PRs #96, #97) | Open PRs | Needs one number after rebase |
| Moodle versions: PR #95 aligns docs to a "5.3-only" decision, while PRD and CLAUDE.md say 4.5 **and** 5.3 | PR #95 (open) | Guide to settle before the report states a version |

## 9. How this maps to the final demonstration (PRD §E5)

The 20-minute final demonstration (E5) needs Release 1 to 4 deliverables that **do not exist
yet**. For Release 0 the report can only demonstrate the foundation, as described in
`demo-script.md`. Steps 1–6 of E5 are **Not implemented** for the video module (FR-V-01…13 are
Release 3), and step 3 additionally needs a lab BigBlueButton that has no evidence.

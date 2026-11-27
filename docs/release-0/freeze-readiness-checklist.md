# Release 0 freeze-readiness checklist (T20 preparation)

**Verdict: NOT READY. Release 0 is NOT frozen, and this document does not freeze it.** The guide
performs the adoption test and the tag (PRD §D2 items 7 and 8; `docs/RELEASING.md`;
`.claude/commands/release-check.md`).
**Audit date:** 2026-11-20, re-audited at `origin/main` `8559c4d` (first at `5f3a794`, refreshed after
four more commits, #130, #142, #145 and #147, merged). The first audit was at `3abbc02` on
2026-11-16; 41 commits have merged since, and the PRD changed what Release 0 contains (see below). GitHub state was queried with `gh` on the audit date and changes quickly; re-check before
relying on it.
**Refresh 2026-11-23** (`origin/main` `dedf578`, after #169 and #129 merged): only the B8.5 rows, the #129 row and the owner list were updated; no other row was re-read, and the verdict is unchanged.
**Refresh 2026-11-24** (PR #213, from the lab 5.3 check of 2026-11-24): only the "Lab VMs ready (A11)" row was updated, to point to the new A11 readiness record (the App-C item 9 rows were updated by #212 the same day). No other row was re-read; this is not a re-audit of the checklist, and the verdict (NOT READY) is unchanged.
**Narrow refresh 2026-11-26** (after PR #142 merged and the subsequent PR #241 review requests): records the M2 survey's source-verification provenance and accurately describes #142's automated review. The survey-preparation assistant directly checked 13 references and used archived copies for MoodleDocs [3], [10] and [11] during research preparation. The owner reports personally opening and verifying all 16 retained references [1]–[16], including the live MoodleDocs pages, on 2026-11-25; this is recorded as the owner's statement in `docs/literature-checker.md`. The Student 2 M2 literature-survey source-verification task is therefore **COMPLETED** on that owner-reported evidence. No separate human peer approval of #142 is claimed. No other row was re-audited; the overall Release 0 verdict remains NOT READY.
**Full refresh 2026-11-27** (`origin/main` `017f279`, after #254). Sections 1 to 4 and 6 were re-read against `main`, `gh` and the repository files on this date; the earlier narrow-refresh notes stay as history. **The verdict is unchanged: NOT READY.** This document does not freeze Release 0. Section 5 (pull requests) was not re-queried in full; only the open Release 0 contract and design PRs are named in sections 2, 3 and 6. Progress is an estimate, not a gate: about 60% overall (PRD D1 content about 72%, D2 closing steps about 12%). Moodle 4.5 is out of scope for the baseline (decisions 0017 and 0018).
**Narrow refresh 2026-11-27, guide's answers on #112** ([comment 7221502371](https://github.com/narenccode/learnops/issues/112#issuecomment-7221502371)): only the rows named in it were updated (B4 outcome names, the grading design, B8.4, B8.6 and where the moved libraries go). Items waiting on a merge are marked as such: #251, #258, #259 and #260 were still open when this was written. No other row was re-read, and the overall Release 0 verdict remains NOT READY.
**Narrow refresh 2026-11-26, App-C item 9** (after the guide's answer of 2026-11-26, [comment](https://github.com/narenccode/learnops/issues/186#issuecomment-7186023695)): only the two App-C item 9 rows were updated. No other row was re-read, and the overall Release 0 verdict remains NOT READY.

**What changed in the PRD since the first audit (PRs #113 and #116).** Release 0 (PRD §D1) now
contains: lab VMs ready (A11); repository, CI, coding standards; contracts B1 to B8 v1 **frozen**;
shared libraries **`contracts` and `media_paths` only**; test data B8 v1; App-C items **6 and 9**;
a design document per module approved. The libraries `lti`, `moodle_ws` and `model_interface`
(FR-M-01, FR-M-02) and the other App-C items (1 to 5, 7, 8, 10) belong to **the first release that
uses them**, and "the Release 0 notes list where each one goes". Earlier versions of this checklist
(and of the report in PR #105) counted those items against Release 0; they no longer are.

**Sibling documents (other sessions, not duplicated):** PR #105 (merged 2026-11-22) added the Release 0 report, demo
script and traceability needs under the same folder; PR #106 the literature entries (T13); PR #98
the speech options record (T8). PR #103 (G-6 evaluation preparation, T9) **merged** after review.

Status key (the six classes requested for T20): **COMPLETED** (genuine evidence exists) ·
**IMPLEMENTED, NOT VERIFIED** (implementation exists, acceptance evidence missing) · **AWAITING
GUIDE APPROVAL** · **BLOCKED** (unavailable service, external evidence or dependency) · **NOT
STARTED** · **READY FOR FINAL ACCEPTANCE**. **NOT READY** and **UNKNOWN** mean the evidence needed
to classify the row was not found. A merged PR is not treated as proof of its acceptance criteria.

> Label note: T-numbers are not defined in the repository (see the B8.5 evidence document). Rows
> use PRD and PR identifiers; tracker labels are added only where the request stated them.

## 1. Known statuses

| Item | Status | Note |
|---|---|---|
| Video design document | **Approved** on `main` | PR #246 (merged 2026-11-26) records the guide's approval and his Q17 answer (issue #186); the peer reviewer ticked section 14 in #239. `Status: Approved` |
| Student 2 — M2 literature survey | **COMPLETED** | `docs/literature-checker.md` covers PRD C2.12 Survey (L2). The survey-preparation assistant directly checked 13 references and used archived copies for MoodleDocs [3], [10], [11] during research preparation. Owner reports personally opening and verifying all 16 retained references [1]–[16], including the live MoodleDocs pages, on 2026-11-25; see the dated owner-verification record in `docs/literature-checker.md`. PR #142 merged 2026-11-20; its APPROVED result was automated review, not separate human peer approval. |
| PR #100 (S2 Svarah literature audit) | Merged | T13: 13 owner-verified sources (S2, P1 to P12), requirement of 6 met; coverage gaps remain |
| PR #103 (G-6 evaluation preparation) | Merged | Preparation only: no official evaluation has run |
| PR #96 (App-C 4 record) | Merged | Records NOT VERIFIED; no lab observation |
| PR #97 | Closed 2026-11-18 | Superseded by #96 |
| Official B8.5 evidence | Separate from temporary test data | See the B8.5 evidence document |

## 2. PRD §D2 exit criteria

| # | Criterion | Status | Evidence / gap |
|---|---|---|---|
| 1 | Every Release 0 FR implemented and linked to passing tests (traceability E4) | **Not ready** | The PRD now gives Release 0 no FR: FR-M-01 and FR-M-02 belong to the first release that uses them. `docs/traceability.md` has rows for the contracts, `media_paths`, the example checkers and B8 sets |
| 2 | Acceptance criteria (§C.x.7) pass | **Not applicable** | Release 0 has none in the PRD; its content is §D1 |
| 3 | Restore and role-test matrix passes on Moodle 5.3, harness report attached | **Blocked** | Moodle 5.3 only (decisions 0017 and 0018; PRD C-03, D2, E2 changed by #225). The B8.1 `.mbz` now exists (release `testdata-b8-1-v1`, rebuilt and restored on the lab 5.3 site on 2026-11-24). No harness report found; the harness is Release 1 work. The 4.5 waivers (decisions 0009, 0010, 0014) are now simply out of scope |
| 4 | Contracts unchanged, or changed only additively under B.0 | **Not verified** | All eight contract families are on `main`. B2 freeze PR #247 merged 2026-11-26 (decision 0003 still reads "freeze candidate"). Open contract PRs: B1 #248 (changes requested) and B7 #250 (approved, not merged). B3, B5 and B6 have no freeze record. B4 freezes separately after its lab checks (decision 0018; results in 0019, merged in #234 and #252; record PR #251 open). Draft PR #115 (CODEOWNERS after the freeze) must not merge before `r0-v1.0` |
| 5 | README, `.env.example`, changelog updated | **Not verified** | `.env.example` exists; **no `CHANGELOG.md` and no `docs/releases/` folder exist** (`docs/RELEASING.md` step 2 requires both) |
| 6 | Security items (A13) reviewed; dependency scan clean | **Partly** | #227 (merged) pinned the LTI dependencies and added a CI vulnerability audit; CI runs a secret scan and pre-commit hooks. No A13 review record and no recorded clean scan result for the release |
| 7 | Tagged `r0-v1.0`; release notes | **Not started** | No tag and no GitHub release exist (`git tag -l` shows only the test-data tag `testdata-b8-1-v1`). The release pull request, candidate tag and release notes are not started |
| 8 | Guide's adoption test passes | **Not started** | The guide's act |

## 3. Release 0 contents (PRD §D1, as it reads now)

| Item | Status | Evidence / gap |
|---|---|---|
| Contracts B1 to B8 v1 frozen | **Not ready** | On `main`: B1 (with vectors), B2 (#46; freeze PR #247 merged), B3 (#83), B4 (#27, #64), B5 (#25; decision 0001-b5 decided by the guide), B6 (#32, #93), B7 (#54), and the B8 sets. Open contract PRs: #248 (B1.5 rule 5, changes requested) and #250 (B7 placement rules, "complete for Release 0", approved, not merged). B4 freezes separately (0018) once #251 and the guide's answers land. The gate review of the whole set is the guide's (PRD B.0 rule 3) |
| `libs/contracts` | **Implemented, not verified** | Example validator and checker merged (#90, #92, #102); CI green on `main`. Local runs on Windows show 4 failures that also occur on a clean `main` |
| `libs/media_paths` | **Implemented, not verified** | Validation (#84), templates (#85) and the `none` signer (#86) merged. `hmac` and `s3` raise a configuration error by design: B6.4 needs only `none` for the baseline |
| Test data B8.1 template course | **Implemented, not verified** | `.mbz` published as release `testdata-b8-1-v1` (2026-11-24, SHA-256 in the README), restored and compared on the lab 5.3 site (README section 8, decision 0009). 5.3 only; the guide's acceptance is not recorded here |
| Test data B8.2 sample course | **Implemented, not verified** | Package and dataset test merged (#61, decision 0010) |
| Test data B8.3 planted-error courses | **Partial** | `testdata/b8-3-planted-errors/` has four variants and `expected-findings.yaml`; the planted-error mapping was confirmed in #253 and decision 0014 (5.3 only). The nine real-backup `.mbz` variants are pending the lab |
| Test data B8.4 synthetic submissions | **Implemented, provisional** | Merged (#31, #189, #190): 33 submissions (PRD minimum 30) and 33 reference grades by `mentor-01`, a student acting as mentor (decision 0016, a recorded deviation from B8.4 and G-5). O6 is Release 4 and O7 is Akshita's approval of the format (#254). The guide said on 27 Nov that it counts for Release 0 ([comment 7221502371](https://github.com/narenccode/learnops/issues/112#issuecomment-7221502371), item 6); the second grader and the sealed test split are Release 4 |
| Test data B8.5 lecture videos | **Implemented, not verified** | On `main` since #169: five lectures (2380 s), outlines, transcripts marked `checked`, four consent lines; COMPLETE under decision 0004. Not verified: durations, hashes, file names, official-set provenance (G-8) and speaker briefings are the owner's statements; no word error rate. See the B8.5 evidence document (2026-11-20 audit, history) |
| Test data B8.6 model comparison set | **Implemented, provisional** | Merged (#33): two transcripts (t001, and t002 from B8.5 lecture-05) with chapter, summary, practice and grading items; every expected output is NOT REVIEWED; `gd-001` may not run until GradeDraftInputV1 and GradeDraftV1 are agreed. Practice format approved by Akshita under B.0 rule 3 (#236). The guide said on 27 Nov that v1 counts for Release 0, with gd-001 and Q41 left for Release 4 ([comment 7221502371](https://github.com/narenccode/learnops/issues/112#issuecomment-7221502371), item 7) |
| App-C item 6 (LTI library and licence) | **Decided by the guide; record not `Approved`** | `0001-lti-library.md`: Stage 1 approved as option A (PyJWT-based validation, no LTI library; PyLTI1p3Next the fallback) and Stage 2 accepted subject to a review (guide, issue #146, 20 Nov). The implementation is not approved until the review and lab check are recorded. Two files are still numbered `0001` (with `0001-b5-model-interface-v1.md`); the guide decides which to renumber |
| App-C item 9 (Moodle 5.3 AI features) | **Complete for the Release 0 freeze (guide, 2026-11-26)** | The decision record **exists on `main`**: `docs/decisions/0012-app-c-9-moodle-ai-features.md` (PR #156, merged 2026-11-22). It is a research record, not an implementation: it does not show that anything is implemented or verified in LearnOps. Its "Lab result" section (2026-11-24) records the lab 5.3 admin screens: seven provider plugins, no provider instance, both placements disabled, no speech or video action. Moodle 4.5 was not looked at. **The guide approved its proposed outcome as written on 2026-11-26** ([comment](https://github.com/narenccode/learnops/issues/186#issuecomment-7186023695)): no scope change, and the lab 5.3 check is sufficient. The guide's answer on PR #140 put it in scope for Student 4 |
| Lab VMs ready (A11) | **Partly recorded; the guide decides** | `docs/release-0/a11-lab-readiness.md` (2026-11-24) records the 5.3 site (5.3+, build 20261030, web services, REST, service account, H5P types, badges); the B4 lab checks on 5.3 are in decision 0019 (run accepted by the guide, 26 Nov). Unknown: `bbb`, `tools`, the lab AI and speech services, the HTTPS certificate and the LTI registrations. `moodle45` is no longer needed (decision 0017). The guide decides whether this is enough |
| Design document per module approved | **Partly done: 2 of 4** | `studio.md` (#147, 2026-11-20) and `video.md` (#246, 2026-11-26) are `Approved`; `grading.md` is `In review` on `main`: the guide said on 27 Nov it can be set to Approved, with section 9.2 outside the approval ([comment 7221502371](https://github.com/narenccode/learnops/issues/112#issuecomment-7221502371), item 3); PR #258 records it and is not yet merged; `checker.md` is `Draft`. The guide approves the other two |
| CI and repository standards | **Completed** | `ci` succeeded on `main` `017f279` (and the two commits before it); review bot and CODEOWNERS exist |

**Moved out of Release 0 by the PRD change:** `libs/lti`, `libs/moodle_ws`, `libs/model_interface`
(none is on `main`; `moodle_ws` pieces merged into stacked branches, PRs #73 to #78), and App-C
items 1 to 5, 7, 8, 10. The Release 0 notes must list where each one goes (not written). The guide's answers of 27 Nov ([comment 7221502371](https://github.com/narenccode/learnops/issues/112#issuecomment-7221502371), items 8 and 9): `model_interface` and the speech interface go to Release 3 (first user: Video; the PRD tags are corrected in draft PR #259, and the grading design in draft PR #260); `moodle_ws` goes to Release 1 (first user: the checker, for course lookup, per Student 2's answer). The grading section of the notes is drafted and handed to the release owner.

## 4. App-C verification items

| # | Item | Belongs to (PRD) | Status | Evidence / gap |
|---|---|---|---|---|
| 1 | B4 functions on 5.3 | B4 freeze (0018) and the first release that relies on it | **Run on the lab 5.3; accepted by the guide (26 Nov)** | Decision 0019 (#234) and its addendum (#252) merged; record PR #251 open. The guide answered on 27 Nov ([comment 7221502371](https://github.com/narenccode/learnops/issues/112#issuecomment-7221502371)): the R12 to R14 names are accepted and he approves the PRD text once the new head is checked; B4 freezes when #251 merges (decision 0018) |
| 2 | Restore merges sections-only backup | Same | **Blocked** | Needs lab; no decision record |
| 3 | CLI restore route | Same | **Blocked** | Needs lab |
| 4 | BBB recording metadata | Release 3 (FR-V-09) | **Blocked** | Records `0005` and `0006` merged (PR #96), both NOT VERIFIED; self-test passes on synthetic data only; see the App-C 4 map |
| 5 | H5P content-type versions | First release that uses them | **Recorded** | Decision 0008: lab check reported by the guide on 2026-11-11; the A11 record lists the H5P types on 5.3 |
| 6 | LTI 1.3 library and licence | **Release 0** | **Decided (option A); ADR not `Approved`** | See section 3 |
| 7 | Caption WER target from baseline run | Release 3 (G-6) | **Blocked** | B8.5 data is complete (#169); still needs a speech provider, an approved normaliser and ADR 0002 (draft PR #98, lab facts pending); evaluation preparation merged (#103) |
| 8 | Licence or consent for every B8.5 video | First release that relies on it | **Implemented, not verified** | Four written consent lines for four speakers in decision 0004 (#169); each speaker's briefing and the official-set provenance are the owner's statements |
| 9 | Moodle 5.3 AI features | **Release 0** | **Complete for the Release 0 freeze (guide, 2026-11-26)** | Record `0012` (PR #156, merged 2026-11-22) now has the lab 5.3 result of 2026-11-24: seven provider plugins and two placements as in the source, no provider instance, both placements disabled, no speech or video action. Moodle 4.5 not tested. The guide approved its proposed outcome as written on 2026-11-26 ([comment](https://github.com/narenccode/learnops/issues/186#issuecomment-7186023695)) |
| 10 | Backup/restore roles | First release that relies on it | **Blocked** | Needs lab |

## 5. Pull requests (base query 2026-11-20; #105 and #106 rows refreshed 2026-11-22; narrow #142 status refresh 2026-11-25)

| PR | State | Review | Note |
|---|---|---|---|
| #98 T8 STT ADR 0002 | Draft | Review required | PROPOSED, pending the guide's approval of its six points |
| #105 T19 report and demo | **Merged** 2026-11-22 | Approved (Harshitha) | Documentation against the provisional criteria P1 to P6; not a completion claim |
| #106 T13 literature (P1 to P12) | Merged 2026-11-22 | Approved (Harshitha, Akshita21-09) | Merged with 1 of 6 verified; since then all of P1 to P12 are owner-verified (owner's statement, 2026-11-23) |
| #129 Lesson Processor demo | Merged 2026-11-23 | Approved (Harshitha, Akshita21-09, guide) | One-PR exception and the `libx264` exception (decision 0013) from the guide |
| #142 M2 literature survey (Student 2) | **Merged 2026-11-20** | **Automated review returned APPROVED (Claude Code run by Akshita21-09, 2026-11-19); no separate human peer approval recorded** | Approval is for commit `d6ce2417`; CI passed. The survey-preparation assistant directly opened 13 primary URLs and archive-checked MoodleDocs [3], [10], [11]; owner later reports verifying all 16 retained references, including the live MoodleDocs pages, on 2026-11-25 (owner's statement; see `docs/literature-checker.md`). |
| #115 CODEOWNERS after the freeze | Draft | Review required | |
| #31, #33 B8.4, B8.6 datasets | Open / Draft | Review required | Provisional |
| #35, #63 model-interface and moodle_ws skeletons | Draft | Review required / changes requested | Not Release 0 after the PRD change |
| #64, #72, #76, #79, #80 B4 and `moodle_ws` | Open | Mixed | B4 follow-ups and stacked library work |
| #118, #138, #139 | Open | Mixed | Other modules; not assessed |

Merged and relevant since the first audit: #25, #27, #46, #54, #61, #83, #85, #87, #93, #94, #95,
#96, #99, #100, #101, #103, #117, #122, #125, #126, #142.

## 6. Approvals and decisions still needed

**Awaiting guide:**
- Approval of the two remaining design documents: `grading.md` and `checker.md` (`Status: Approved` is the guide's alone; `studio.md` and `video.md` are approved).
- Answers on issue #112 for the B4 record (#251), then the B4 freeze; the gate review of B1 to B3, B5 to B7 and the B8 sets (B8.4 and B8.6 are provisional).
- Setting ADR 0001 (LTI) to `Approved` after the review and lab check he asked for, and which of the two `0001` files is renumbered.
- *(Decided.)* Retention, lab-storage access, names and transcripts and processing services for B8.5 were decided on 2026-11-19 and recorded in decision 0011; the data map follows it. Still to record: what the lab endpoint keeps (decision 0002, PR #98).
- Contract-change approvals and the freeze itself (PRD B.0, `docs/RELEASING.md`).
- A complete Release 0 task list and the definition of the T-labels: the repository has none.
- The "Release 0 notes" that list where each moved item goes.

**Awaiting the owner / team:**
- Written confirmation that the five recordings are the official B8.5 set and that each speaker was briefed: **accepted for Release 0 by the guide as the owner's statements, with the caveat recorded** ([issue #186](https://github.com/narenccode/learnops/issues/186#issuecomment-7101984198), 23 November 2026). Not independently verified.
- Creating `CHANGELOG.md` and `docs/releases/r0.md` (PRD §D2 item 5, `docs/RELEASING.md`).

**Blocked by unavailable external services:** the lab Moodle 4.5 and 5.3 sites, a BigBlueButton server, and a speech provider.

## 7. Ready for final acceptance

**None.** No Release 0 item can be shown as ready for final acceptance on the evidence available.

## 8. Shared-file changes proposed, not made

- `docs/traceability.md`: add pointers to the documents in `docs/release-0/`.
- `docs/design/video.md`: no `Approved` until the guide sets it.
- `docs/decisions/`: renumber one of the two `0001` records (the guide decides which).
- Create `CHANGELOG.md` and `docs/releases/r0.md` when the release pull request is prepared.

## 9. Checks run for this checklist

| Command | Result |
|---|---|
| `gh run list --branch main` | `ci` succeeded on `5f3a794`, `d1faffc` and `d28018f` |
| `git tag -l`; `gh release list` | Both empty |
| `ls libs contracts docs/decisions docs/design testdata` and `git ls-files` on `origin/main` | Used for sections 3 and 4 |
| `gh pr list --state open`; `gh pr view <n>` | Used for section 5 |
| `python docs/decisions/evidence/0005-app-c-4-bbb/verify_bbb.py --selftest` | "selftest OK (synthetic data only; proves the script logic, NOT the lab)" |
| Full `/preflight` (`ruff`, `mypy libs`, contract validation, requirement-ID check) | **Not run as a whole** for this audit; the change is documentation only, and `ci` is green on `main` |
| `python -m pytest -q libs/contracts/tests/test_b8_5_dataset.py` on this branch merged with `origin/main` `5f3a794` | `71 passed in 33.48s` |
| Earlier local runs (2026-11-16): whole repo in a clean venv 1 failed, 2044 passed, 4 skipped (Windows case-insensitive filesystem) | **Not repeated** on the current `main`; shown only as history |

**Not found in the PRD, so not audited:** a Release 0 "backup" requirement. PRD App-D lists VM image
backups only as a risk mitigation, and §D2 has no backup criterion. Marked UNKNOWN pending the
guide's list of Release 0 tasks.

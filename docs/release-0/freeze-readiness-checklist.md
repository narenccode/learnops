# Release 0 freeze-readiness checklist (T20 preparation)

**Verdict: NOT READY. Release 0 is NOT frozen, and this document does not freeze it.** The guide
performs the adoption test and the tag (PRD §D2 items 7 and 8; `docs/RELEASING.md`;
`.claude/commands/release-check.md`).
**Audit date:** 2026-11-20, re-audited at `origin/main` `8559c4d` (first at `5f3a794`, refreshed after
four more commits, #130, #142, #145 and #147, merged). The first audit was at `3abbc02` on
2026-11-16; 41 commits have merged since, and the PRD changed what Release 0 contains (see below). GitHub state was queried with `gh` on the audit date and changes quickly; re-check before
relying on it.

**What changed in the PRD since the first audit (PRs #113 and #116).** Release 0 (PRD §D1) now
contains: lab VMs ready (A11); repository, CI, coding standards; contracts B1 to B8 v1 **frozen**;
shared libraries **`contracts` and `media_paths` only**; test data B8 v1; App-C items **6 and 9**;
a design document per module approved. The libraries `lti`, `moodle_ws` and `model_interface`
(FR-M-01, FR-M-02) and the other App-C items (1 to 5, 7, 8, 10) belong to **the first release that
uses them**, and "the Release 0 notes list where each one goes". Earlier versions of this checklist
(and of the report in PR #105) counted those items against Release 0; they no longer are.

**Sibling documents (other sessions, not duplicated):** PR #105 adds the Release 0 report, demo
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
| Video design document | **Draft** on `main` | `git log origin/main -- docs/design/video.md` shows #17, #24, #34, #47 and #93; none sets `Approved`. PR #140 (merged 2026-11-22) completed the draft and recorded the guide's answers; the document is still `Draft`, and the design approval is separate and the guide's alone |
| PR #100 (S2 Svarah literature audit) | Merged | T13 as a whole is not complete (PR #106: 1 of 6 sources verified) |
| PR #103 (G-6 evaluation preparation) | Merged | Preparation only: no official evaluation has run |
| PR #96 (App-C 4 record) | Merged | Records NOT VERIFIED; no lab observation |
| PR #97 | Closed 2026-11-18 | Superseded by #96 |
| Official B8.5 evidence | Separate from temporary test data | See the B8.5 evidence document |

## 2. PRD §D2 exit criteria

| # | Criterion | Status | Evidence / gap |
|---|---|---|---|
| 1 | Every Release 0 FR implemented and linked to passing tests (traceability E4) | **Not ready** | The PRD now gives Release 0 no FR: FR-M-01 and FR-M-02 belong to the first release that uses them. `docs/traceability.md` has rows for the contracts, `media_paths`, the example checkers and B8 sets |
| 2 | Acceptance criteria (§C.x.7) pass | **Not applicable** | Release 0 has none in the PRD; its content is §D1 |
| 3 | Restore and role-test matrix on Moodle 4.5 **and** 5.3, harness report attached | **Blocked** | Needs lab Moodle sites; the B8.1 `.mbz` does not exist; no harness report found. Moodle 4.5 is waived for B8.1 in Release 0 (decision 0009); PR #130 (merged) added one register for version exceptions in `docs/decisions/README.md` |
| 4 | Contracts unchanged, or changed only additively under B.0 | **Not verified** | All eight contract families now have a file on `main` (section 3) but none is frozen; B4 has open follow-ups (#64, #72); B7 is marked draft. Draft PR #115 changes CODEOWNERS for the post-freeze period |
| 5 | README, `.env.example`, changelog updated | **Not verified** | `.env.example` exists; **no `CHANGELOG.md` and no `docs/releases/` folder exist** (`docs/RELEASING.md` step 2 requires both) |
| 6 | Security items (A13) reviewed; dependency scan clean | **Not verified** | No scan result recorded in this audit; CI runs a secret scan and pre-commit hooks |
| 7 | Tagged `r0-v1.0`; release notes | **Not started** | No tag and no GitHub release exist (`git tag -l` is empty). The release pull request, candidate tag and release notes are not started |
| 8 | Guide's adoption test passes | **Not started** | The guide's act |

## 3. Release 0 contents (PRD §D1, as it reads now)

| Item | Status | Evidence / gap |
|---|---|---|
| Contracts B1 to B8 v1 frozen | **Not ready** | On `main`: B1 course package (with submission and check-cell vectors), B2 course model (#46), B3 LTI launch (#83), B4 Moodle web services (#27), B5 model interface (#25), B6 lesson manifest and chapters, slides, cues (#32, #93), B7 H5P practice (#54, draft). Not frozen: nothing sets a freeze, the contract owners' approvals are not recorded, and B4 has open follow-ups |
| `libs/contracts` | **Implemented, not verified** | Example validator and checker merged (#90, #92, #102); CI green on `main`. Local runs on Windows show 4 failures that also occur on a clean `main` |
| `libs/media_paths` | **Implemented, not verified** | Validation (#84), templates (#85) and the `none` signer (#86) merged. `hmac` and `s3` raise a configuration error by design: B6.4 needs only `none` for the baseline |
| Test data B8.1 template course | **Blocked** | Documentation (#57) and decision 0009; no `.mbz`; needs the Moodle lab |
| Test data B8.2 sample course | **Implemented, not verified** | Package and dataset test merged (#61, decision 0010) |
| Test data B8.3 planted-error courses | **Not started** | No PR or file found |
| Test data B8.4 synthetic submissions | **Not ready** | PR #31 (open): provisional pilot of 6; the PRD asks for at least 30 |
| Test data B8.5 lecture videos | **Blocked** | Checker and tests merged (#82, #89); inventory hashes (#99). 0 of 5 consent lines, no transcripts, 338 s of 1800 s measured; see the B8.5 evidence document |
| Test data B8.6 model comparison set | **Not ready** | PR #33 (open, draft): "one transcript" |
| App-C item 6 (LTI library and licence) | **Awaiting guide** | `docs/decisions/0001-lti-library.md` is `Proposed`, pending the guide's review. Two files are numbered `0001` (`0001-lti-library.md` and `0001-b5-model-interface-v1.md`); the guide decides which to renumber |
| App-C item 9 (Moodle 5.3 AI features) | **Implemented, not verified** | The decision record **exists on `main`**: `docs/decisions/0012-app-c-9-moodle-ai-features.md` (PR #156, merged 2026-11-22). It is source-checked, **not lab-verified**: the lab Moodle 5.3 site and Moodle 4.5 were not looked at, and the guide has not approved its proposed outcome. The guide's answer on PR #140 put it in scope for Student 4 |
| Lab VMs ready (A11) | **Unknown / Blocked** | The guide said on issue #55 that the lab Moodle 4.5 and 5.3 sites exist (2026-11-11) and gave an owner an account on 5.3 (2026-11-14); no A11 readiness record exists |
| Design document per module approved | **Partly done: 1 of 4** | `studio.md` is `Approved` (PR #147, 2026-11-20); `grading.md` is `In review`; `checker.md` and `video.md` are `Draft`. The guide approves the other three |
| CI and repository standards | **Completed** | `ci` succeeded on `main` `5f3a794` (and the two commits before it); review bot and CODEOWNERS exist |

**Moved out of Release 0 by the PRD change:** `libs/lti`, `libs/moodle_ws`, `libs/model_interface`
(none is on `main`; `moodle_ws` pieces merged into stacked branches, PRs #73 to #78), and App-C
items 1 to 5, 7, 8, 10. The Release 0 notes must list where each one goes (not written).

## 4. App-C verification items

| # | Item | Belongs to (PRD) | Status | Evidence / gap |
|---|---|---|---|---|
| 1 | B4 functions on 4.5 and 5.3 | First release that relies on it | **Blocked** | Needs lab; all ten lab checks open |
| 2 | Restore merges sections-only backup | Same | **Blocked** | Needs lab; no decision record |
| 3 | CLI restore route | Same | **Blocked** | Needs lab |
| 4 | BBB recording metadata | Release 3 (FR-V-09) | **Blocked** | Records `0005` and `0006` merged (PR #96), both NOT VERIFIED; self-test passes on synthetic data only; see the App-C 4 map |
| 5 | H5P content-type versions | First release that uses them | **Blocked** | Decision 0008 records the lab check design; needs lab |
| 6 | LTI 1.3 library and licence | **Release 0** | **Awaiting guide** | ADR 0001 is Proposed |
| 7 | Caption WER target from baseline run | Release 3 (G-6) | **Blocked** | Needs B8.5 complete and a speech provider; evaluation preparation merged (#103); ADR 0002 is draft PR #98, with the guide's one record fix applied |
| 8 | Licence or consent for every B8.5 video | First release that relies on it | **Blocked** | 0 of 5; see the B8.5 evidence document |
| 9 | Moodle 5.3 AI features | **Release 0** | **Implemented, not verified** | Record `0012` is on `main` (PR #156, merged 2026-11-22), source-checked only; the lab 5.3 check and the guide's approval of its proposed outcome are outstanding |
| 10 | Backup/restore roles | First release that relies on it | **Blocked** | Needs lab |

## 5. Pull requests (queried 2026-11-20; 19 open, listed by relevance; the #105 and #106 rows were refreshed on 2026-11-22)

| PR | State | Review | Note |
|---|---|---|---|
| #98 T8 STT ADR 0002 | Draft | Review required | PROPOSED, pending the guide's approval of its six points |
| #105 T19 report and demo | Open, ready for review | Changes requested (status wording) | The requested corrections were pushed in `37466ca`; **re-review is pending** |
| #106 T13 literature (P1 to P12) | Merged 2026-11-22 | Approved (Harshitha, Akshita21-09) | 1 of 6 sources verified; entries P1 to P12 pending owner verification |
| #129 Lesson Processor demo | Open | Changes requested (Akshita21-09) | One-PR exception from the guide; awaiting peer review |
| #115 CODEOWNERS after the freeze | Draft | Review required | |
| #31, #33 B8.4, B8.6 datasets | Open / Draft | Review required | Provisional |
| #35, #63 model-interface and moodle_ws skeletons | Draft | Review required / changes requested | Not Release 0 after the PRD change |
| #64, #72, #76, #79, #80 B4 and `moodle_ws` | Open | Mixed | B4 follow-ups and stacked library work |
| #118, #138, #139, #142 | Open | Mixed | Other modules; not assessed |

Merged and relevant since the first audit: #25, #27, #46, #54, #61, #83, #85, #87, #93, #94, #95,
#96, #99, #100, #101, #103, #117, #122, #125, #126.

## 6. Approvals and decisions still needed

**Awaiting guide:**
- Approval of the three remaining design documents: `grading.md`, `checker.md`, `video.md` (`Status: Approved` is the guide's alone; `studio.md` was approved in PR #147).
- Review of the LTI library decision (App-C 6, ADR 0001), the B5 decision record, and which of the two `0001` files is renumbered.
- *(Decided.)* Retention, lab-storage access, names and transcripts and processing services for B8.5 were decided on 2026-11-19 and recorded in decision 0011; the data map follows it. Still to record: what the lab endpoint keeps (decision 0002, PR #98).
- Contract-change approvals and the freeze itself (PRD B.0, `docs/RELEASING.md`).
- A complete Release 0 task list and the definition of the T-labels: the repository has none.
- The "Release 0 notes" that list where each moved item goes.

**Awaiting the owner / team:**
- Speaker consent lines, speaker names, file names, transcripts and Harshitha's review for B8.5; written confirmation that the five local files are the official set.
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

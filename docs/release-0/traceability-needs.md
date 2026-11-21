# Traceability needs raised by T19 (for the owner of `docs/traceability.md`)

T19 does **not** edit `docs/traceability.md`. Many open PRs also touch it. This note lists what
T19's documents need so that the change is made once, there. It is a list of observations, not a
set of edits. First written 2026-11-16 against `origin/main` at `3abbc02`; **re-checked
2026-11-20 against `origin/main` `5f3a794`** (`docs/traceability.md` is now 820 lines).

## 1. Coordination and overlap

| Item | State on 2026-11-20 |
|---|---|
| T19 edits `docs/traceability.md`? | **No** |
| Earlier concern: an unmerged combined `media_paths` branch (#38) rewrote the first rows | **Resolved.** #38 was closed on 2026-11-16 as superseded; #84, #85 and #86 are merged and `main` has one row each for validation, templates and the `none` signer |
| Open PRs that also edit the file | Not counted again. Draft PRs #140 and #98 do not edit it. #104 proposes a B8.5 line in its checklist but does not edit the file. Whoever merges later merges `main` into the branch (no force-push, CLAUDE.md) |
| T-series PRs that added traceability text | #96 (App-C 4, merged), #103 (G-6 tooling, merged); #97 (closed as superseded) |
| T19 adds a row? | No. T19 adds no requirement and no test, so CLAUDE.md §7 item 3 has nothing to record beyond this note |

## 2. Missing mappings

| Gap | Observation | Suggested owner action |
|---|---|---|
| Demo column | The table at the top has a "Demo step" column, but most rows leave it empty or say none | Point each row at a step in `docs/release-0/demo-script.md` (steps A1 to A6) or at the D4 and D5 demos in `modules/video/demo/README.md` and `docs/demos/d5-course-input.md` |
| Implementation references | Rows name tests but not implementation files | Optional (PRD E4 asks for FR, tests, demo step, Bloom level). The file paths are in `demo-script.md` section 3 |
| Bloom level | The `media_paths` rows say "–". PRD C1.12 gives levels to kinds of work, not to individual requirements | Owner and guide decide; T19 does not |
| FR-M-01 and FR-M-02 | **No longer a Release 0 gap.** The PRD now places the model and speech interfaces in the first release that uses them (PRD §D1). Draft #35 is the nearest work | Add a row when library code reaches `main` |
| FR-S-03, FR-V-08 | Correctly absent (deliberately not mapped in the file) | None |

## 3. Duplicate and conflicting mappings

- **`media_paths` rows.** Resolved: `main` has three rows (validation #84, templates #85, signing
  #86) and no duplicate from #38.
- **B8.1.** `main` carries the guide's 5.3-only decision for B8.1 (decision 0009, PR #95) and the
  B8.2 deviation; PR #130 (merged) added one register of Moodle version exceptions in `docs/decisions/README.md`. Do not
  add a second wording.
- **B8.5.** `main` says PENDING with five SHA-256 values and no duration. #104 proposes a line
  with 5 local recordings, 338 s of 1800 s and 0 of 5 consent lines. The guide's assistant agreed on
  2026-11-19 that the #104 line stays labelled unmerged and that **nothing is added to
  `docs/traceability.md`**; a line must not run ahead of reviewed evidence. The five measured durations are on
  the branch `video/b8-5-dataset-evidence` (commit `9c6d703`), not on `main`, and no PR carries
  them yet.
- **Video demo.** PR #117 (D4 paths demo) and PR #129 (Lesson Processor demo, FR-V-01, FR-V-03 and
  FR-V-08 in part, one-PR exception from the guide) each add demo text. #129 adds its own
  "Video lesson processor demo" section with rows for FR-V-01, FR-V-03 and FR-V-08, marked "in
  part"; they must not be read as Release 3 coverage.

## 4. Incorrect or stale references

| Where | Problem |
|---|---|
| `docs/traceability.md` line 38 | Cites "#25, #27" as contracts with flat examples. Both are now **merged**, so the sentence is correct as written |
| `docs/traceability.md` (B8.1 and B1 sections, around lines 11 and 41) and `testdata/b8-1-template-course/README.md` | Cite "Issue #61" for a licence answer of 2026-11-11. #61 is a merged pull request (B8.2). The owner must check which issue was meant |
| Anything naming #91 as merged | #91 merged only into a stacked branch and was replaced by #102 |
| `modules/video/demo/README.md` line 5 | Says the Release 0 demonstration "is on the T19 branch, not in this checkout". That becomes false when #105 merges; update the line then |

## 5. Evidence the traceability owner should consider adding

- Pointers to `docs/release-0/report.md`, `demo-script.md` and `traceability-needs.md` once #105 merges
  (#104 proposes the same for its own documents).
- The hosted CI result for the row's commit: `ci` on `main` `5f3a794` succeeded (report section 5).
- For B8.5 and App-C 4: keep "not verified" lines as they are. Nothing in `main` verifies either.

## 6. Not needed

Nothing in T19 changes a requirement, a test or a contract.

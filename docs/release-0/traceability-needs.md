# Traceability needs raised by T19 (for the owner of `docs/traceability.md`)

T19 does **not** edit `docs/traceability.md`. Another session is changing it, and many open PRs
also touch it. This note lists what T19's documents need so that the change is made once, there.
It is a list of observations, not a set of edits. Written 2026-11-16 against `origin/main` at
`3abbc02`.

## 1. Coordination and overlap

| Item | State |
|---|---|
| T19 edits `docs/traceability.md`? | **No** |
| Other session's uncommitted work | In another checkout, branch `video/b6-media-paths` (the branch of PR #38): `docs/traceability.md`, `libs/media_paths/README.md`, `validation.py` and `tests/test_validation.py` are modified. I read the file status and the diff of `docs/traceability.md` only. I changed nothing there |
| What its `traceability.md` diff touches | The first row (B6.1 path templates), which is #38's version of the row. `main` has a different first row (validation, #84). The two will conflict |
| Open PRs that also edit the file (queried 2026-11-16) | #25, #27, #31, #33, #35, #38, #46, #54, #61, #63, #64, #68, #72, #76, #79, #80, #83, #85, #87, #93, #94, #95, #96, #97, #101, #103 (26 PRs). Expect conflicts; whoever merges later rebases |
| PRs of the T-series that add or propose traceability text | #95 (B8.1, 5.3-only), #96 and #97 (App-C 4), #103 (G-6 tooling, adds an entry), #104 (proposes a B8.5 line in its checklist section 8, does not edit the file) |
| T19 adds a row? | No. T19 adds no requirement and no test, so CLAUDE.md §7 item 3 has nothing to record beyond this note |

## 2. Missing mappings

| Gap | Observation | Suggested owner action |
|---|---|---|
| Demo column | The two `media_paths` rows have a demo step; the rows for the contract example validator, the B1 package validator, the B6 manifest and the B8.5 checker say none or are not in the table at the top | Point each row at a step in `docs/release-0/demo-script.md`: A1 (example validator), A2 (B1 package), A3 (B6.3 manifest), A4 (media_paths, both rows), A5 (B8.5 checker). Use the step ids as they stand when the owner edits; they may change |
| Implementation references | Rows name tests but not the implementation files | PRD E4 asks for FR, tests, demo step, Bloom level, so this is optional. If wanted, add the file paths listed in `demo-script.md` section 3 |
| Bloom level | `media_paths` rows say "—". PRD C1.12 gives levels to kinds of work, not to individual requirements | Owner and guide to decide; T19 does not |
| FR-M-01 and FR-M-02 | The only Release 0 FRs have no row; #35 (FR-M-01, partial, open and stacked on #25) is the nearest work | Add a row only when code reaches `main` |
| FR-S-03, FR-V-08 | Correctly absent (deliberately not mapped in the file) | None |

## 3. Duplicate and conflicting mappings

- **`media_paths` rows.** `main` has two rows, validation (#84) and signing (#86). Open #85 (path
  templates) and the older combined #38 each rewrite or add the same rows. #38 contains the work of
  #84, #85 and #86 together (`paths.py`, `signing.py`, `test_paths.py`), so its traceability text
  duplicates three PRs. The owner should decide whether #38 is closed; T19 does not.
- **B8.1.** `main` still says the template is built on 4.5 (lines 166 and 167). The guide's later
  decision is 5.3 only for B8.1 and B8.2 (issue #55, 2026-11-14; PR #61, 2026-11-16). #95 changes the
  B8.1 rows, and #61 is to record the B8.2 deviation. Do not add a second, competing wording.
- **B8.5.** `main` says PENDING. #104 proposes a line saying 5 local recordings with verified hashes
  and 338 s of 1800 s. T19 recommends adding it only after the official evidence is reviewed and
  merged; a traceability line must not run ahead of reviewed evidence.

## 4. Incorrect or stale references

| Where | Problem |
|---|---|
| `docs/traceability.md:37` | Cites "#25, #27" as contracts with flat examples. Both are **open** PRs, not merged contracts. The sentence is correct as a reason, but a reader may assume they are on `main` |
| `docs/traceability.md:166-167` | Stale for the guide's 5.3-only decision (above) |
| `docs/traceability.md` | Cites no PR for #91 or #102, so nothing to correct. Anything elsewhere that names #91 as merged should say #102: #91 merged into a stacked branch and was replaced |
| `testdata/b8-1-template-course/README.md:37` | Cites "Issue #61". #61 is a pull request (B8.2). Owner to check what was meant |

## 5. Evidence the traceability owner should consider adding

- Pointers to `docs/release-0/report.md`, `demo-script.md` and `traceability-needs.md` once #105 merges
  (#104 proposes the same for its own documents).
- The hosted CI result for the row's commit: run 43824425528 on `3abbc02`, success (report section 5).
- For B8.5 and App-C 4: keep "not verified" lines as they are. Nothing in `main` verifies either.

## 6. Not needed

Nothing in T19 changes a requirement, a test or a contract.

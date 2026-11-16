# Traceability needs raised by T19 (for the owner of `docs/traceability.md`)

T19 does **not** edit `docs/traceability.md`: another session is changing it (the working tree of
the main checkout shows it modified and uncommitted at the time of writing, 2026-11-16). This note
lists what T19 would need, so the changes can be made once, there.

## Overlap to resolve

| Item | State |
|---|---|
| File | `docs/traceability.md` |
| T19 edits it? | **No** |
| Other session | Has uncommitted changes to it in another checkout (branch `video/b6-media-paths`, together with `libs/media_paths/` changes). I saw only the file status; I did not read or touch the changes |
| Risk | If both change the media_paths rows, the PR will conflict. Whoever merges second rebases |

## Changes T19's documents rely on

1. **Demonstration column.** `docs/traceability.md` says "Demo step" per row, and the two
   `media_paths` rows say "Show that ...". `demo-script.md` uses its own step ids D1 to D6. When the
   table is next updated, the rows can cite those ids:

   | Traceability row | Suggested demo step |
   |---|---|
   | `media_paths` validation | `docs/release-0/demo-script.md` D4 |
   | `media_paths` signing | D4 |
   | Contract example validator | D1 (no demo step recorded today) |
   | B1 package validator | D2 (no demo step recorded today) |
   | B6 lesson manifest | D3 (no demo step recorded today) |
   | B8.5 checker | D5 |

2. **Rows that cite PR #91 as merged.** #91 merged into a stacked branch and was replaced by #102,
   which is on `main`. If the table or the validator README names #91, say #102.
3. **Statement of what is on `main`.** The `moodle_ws` PRs #73 to #78 are "merged" only into
   stacked branches. Do not add `moodle_ws` rows to traceability until it reaches `main`.
4. **B8.5 row.** Already says PENDING, with accurate limits. Keep it; do not move it to complete
   until the official evidence PR (outside T19) lands.
5. **No requirement ID.** B1, B6 and B8 have none; the existing "Not mapped" notes are correct and
   T19 does not change them.

## Not needed

No new requirement or test was added by T19, so Definition-of-done item 3 (CLAUDE.md §7) has nothing
to record for this PR beyond this note.

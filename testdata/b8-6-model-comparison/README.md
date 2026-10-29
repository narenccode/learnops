# B8.6 model comparison set (PROVISIONAL)

**Status: PROVISIONAL.** A proposed format, a proposed rubric, and one fictional transcript with
author-drafted expected chapters and summary that are **NOT REVIEWED**. No comparison has been
run, and nothing here says how well any model performs.

| | |
|---|---|
| PRD | §B8 (B8.6), FR-M-03, §C3.7 ("comparison report ... all three measures for both providers"), G-10, F-4 |
| Owner | Student 3 |
| Design | `docs/design/grading.md` §11.2 (measures, Q48), §11.4 (B8.6), Q12 (Draft) |
| Module rule | `modules/grading/CLAUDE.md` rule 7: the fixed set B8.6 and the same prompts for every provider |
| Tests | `libs/contracts/tests/test_b8_6_dataset.py` |
| Source | Written for this project by Student 3. Entirely fictional: no recording, no real lecturer, no real course content, no learner data. |
| Licence | Open decision (O9) |

## What PRD §B8 requires, and what this set has

"Fixed inputs and expected outputs for practice drafts, grading drafts, chapters and summaries."

| Task | Item | Status | Input | Expected output |
|---|---|---|---|---|
| Chapters | ch-001 | ready, PROVISIONAL | `inputs/t001/transcript.en.json` | `expected/ch-001/chapters.json`, NOT REVIEWED |
| Summaries | su-001 | ready, PROVISIONAL | `inputs/t001/transcript.en.json` | `expected/su-001/summary.en.md`, NOT REVIEWED |
| Grading drafts | gd-001 | pending | B8.4 submissions (PR #31, not merged) | B8.4 mentor reference grades (none yet, Q13) |
| Practice drafts | pr-001 | placeholder | Not agreed (Q12) | None. No practice questions are written until Q12 is agreed |

"Ready" means the files exist. It does not mean they are agreed or reviewed.

## Layout

```
manifest.yaml                  inputs and items (task, status, input, expected, review status)
rubric.yaml                    review levels and the four FR-M-03 measures (PROVISIONAL, frozen: false)
schemas/                       manifest, rubric and expected-chapters schemas (Draft 2020-12)
inputs/t001/                   transcript.en.json (B5.4 shape) + source.md (provenance)
expected/<item id>/            author-drafted expected outputs (see expected/README.md)
results/                       empty: no comparison has been run
```

How an item links to its input, expected output and rubric:

```
items[].input    ──> inputs[].id ──> inputs[].path (transcript) + source_note
items[].expected ──> expected/<item id>/<file>          (review status in items[].expected_review)
items[].task     ──> rubric.yaml output_review.applies_to / grade_draft_review
```

## Shapes used

- **Transcript:** PRD B5.4, `segments[{start, end, text, words[{start, end, word}]}]` plus
  `meta{provider, model, duration_s, latency_ms, cost_estimate}`, times in seconds from the start
  of the audio. The B5 schema file (`contracts/model-interface.v1.schema.json`) is in PR #25 and
  not on `main` yet. The tests check the PRD B5.4 shape themselves and validate against the B5
  schema when that file is present. Until then that one test is skipped and says why.
- **Chapters:** PRD B6.2 `chapters.json` `[{start, end, title}]`. B6 (PR #32) names the file but
  does not define its content, so `schemas/chapters.schema.json` is a test-data schema, **not a
  contract**.
- **Summary:** PRD B6.2 `summary.en.md`, Markdown. No shape is defined. The first line of the
  expected file is an HTML comment carrying the PROVISIONAL / NOT REVIEWED label. A rendered
  summary does not show it.

## Rules the tests apply to this set (PROVISIONAL)

These are authoring rules for the expected outputs, not requirements from the PRD.

- Every segment and word ends at or after its start. Segments are in time order and lie within
  `duration_s`. (B5 guarantees only segment `end >= start`. Order is not decided there.)
- Expected chapters are in order, do not overlap, have `end > start`, lie within the transcript,
  and start on a segment boundary.

## Open decisions (not decided here)

| # | Decision | Ref | Who |
|---|---|---|---|
| O1 | Chapter, summary and practice inputs: which lectures, how many, who supplies them | design Q12 | Students 1 and 4, integration lead, guide |
| O2 | Who writes and who reviews the expected outputs; how "reviewed" is recorded | — | Guide |
| O3 | Review rubric: the three output levels and the grading-draft wrong rule | design §11.2, Q48 | Guide |
| O4 | Agreement for chapters, summaries and practice (undefined); band for grading (Q44) | Q44, Q48 | Guide |
| O5 | Mentor review time protocol for non-grading outputs (only grading has one, Q46) | Q46 | Guide |
| O6 | Grading-draft items: B8.4 merged, its submission-content rule (Q32), reference grades (Q13), `GradeDraftV1` (Q41) | §4.3a, §4.3d | Guide, Students 1 and 3 |
| O7 | Practice: task shape and output format (B7, FR-S-12, Release 5 stretch) | Q12 | Students 1 and 4 |
| O8 | Size of the set per task (the PRD gives none) | — | Guide |
| O9 | Licence of the test content (proposal: Apache-2.0, like the repository) | root `CLAUDE.md` §2.10 | Guide |
| O10 | Accept this format as the B8.6 part of the B8 contract before the Release 0 freeze | `contracts/CLAUDE.md` | All four students, guide |
| O11 | Chapters content schema: keep this test-data schema or move it into B6. B6 (PR #32) defines `chapters` only as a relative path; this schema is also stricter than PRD B6.2 (at least one chapter, non-empty title), which B6 may decide differently | PR #32 | Student 4 |

Before any comparison run (design §11.4, §11.2): the rubric is fixed (`frozen: true`), every
expected output is reviewed, the prompts are frozen, and the provider they were developed on is
recorded.

**Undo:** the set is plain files. Delete an item's folder and its manifest entry to remove it.

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
| Licence | Apache-2.0 (decided by the guide, issue #186; PRD C-11) |

## What PRD §B8 requires, and what this set has

"Fixed inputs and expected outputs for practice drafts, grading drafts, chapters and summaries."

| Task | Item | Status | Input | Expected output |
|---|---|---|---|---|
| Chapters | ch-001 | ready, PROVISIONAL | `inputs/t001/transcript.en.json` | `expected/ch-001/chapters.json`, NOT REVIEWED |
| Summaries | su-001 | ready, PROVISIONAL | `inputs/t001/transcript.en.json` | `expected/su-001/summary.en.md`, NOT REVIEWED |
| Grading drafts | gd-001 | **pending** | B8.4 submissions (`inputs/b8-4/source.md`; B8.4 is merged: 33 submissions, #31, #189 and #190) | B8.4 mentor reference grades: **none exist yet** (B8.4 has only the author's own grades, labelled as not reference grades), and the student the guide chose to act as mentor (Q13, accepted 24 Nov) has not graded yet. Review form: `templates/` (PROPOSED) |
| Practice drafts | pr-001 | ready, PROVISIONAL | `inputs/t001/transcript.en.json` | `expected/pr-001/practice.yaml`, NOT REVIEWED. Four multiple-choice checkpoint questions in the review-card shape proposed by Student 1 (FR-S-12); the format is confirmed by the guide (reported by Harshitha on 18 Nov; the link to his answer is still to be added) |

"Ready" means the files exist. It does not mean they are agreed or reviewed.

## Layout

```
manifest.yaml                  inputs and items (task, status, input, expected, review status)
rubric.yaml                    review levels and the four FR-M-03 measures (PROVISIONAL, frozen: false)
schemas/                       manifest, rubric, expected-practice and two review-form schemas (Draft 2020-12)
templates/                     PROPOSED mentor review forms with invented examples (see templates/README.md)
inputs/t001/                   transcript.en.json (B5.4 shape) + source.md (provenance)
expected/<item id>/            author-drafted expected outputs (see expected/README.md)
results/                       empty: no comparison has been run
reviews/                       not created yet: real mentor reviews go here
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
- **Chapters:** PRD B6.2 `chapters.json` `[{start, end, title}]`, checked with the merged B6.2
  contract (`contracts/chapters.v1.schema.json`, validator `contracts.validate_chapters`). This set
  has no chapters schema of its own.
- **Practice:** `practice.yaml` (`schemas/practice.schema.json`), a test-data shape, **not a contract**. B7 (PR #54) defines no JSON structure for a draft or a review card, so this follows the FR-S-12 review card (question, correct answer, distractors, explanation, source) as proposed by Student 1 on PR #33. One H5P content type per item (`question_set`); interactive video is never used.
- **Summary:** PRD B6.2 `summary.en.md`, Markdown. No shape is defined. The first line of the
  expected file is an HTML comment carrying the PROVISIONAL / NOT REVIEWED label. A rendered
  summary does not show it.

## Rules the tests apply to this set (PROVISIONAL)

These are authoring rules for the expected outputs, not requirements from the PRD.

- Every segment and word ends at or after its start. Segments are in time order and lie within
  `duration_s`. (B5 guarantees only segment `end >= start`. Order is not decided there.)
- Expected chapters are not empty, lie within the transcript, and start on a segment boundary.
  Order, overlap and `end > start` are B6.2's rules, checked by its validator.

## Open decisions

The guide answered some of these on issue #186 (23 Nov 2026), and the grading design (§11.4, #197) proposes the rest. What is decided is marked **Decided**; what is proposed in the design is marked **Proposed**; the guide settles the proposals when he approves the design.

| # | Decision | Ref | Who |
|---|---|---|---|
| O1 | **Decided (guide, issue #186):** grading inputs come from B8.4 (Student 3), practice inputs from Student 1, chapter and summary inputs from Student 4, and Student 2 coordinates. The input t001 stays for now (Student 4 on PR #33); a checked B8.5 transcript is added later. | design Q12 | Students 1 and 4, integration lead, guide |
| O2 | **Decided (guide, issue #186):** the module owner who supplied an input reviews its expected output, and the guide decides any disagreement. How "reviewed" is recorded stays in the manifest (`expected_review`). | — | Guide |
| O3 | Review rubric: the three output levels and the grading-draft wrong rule | design §11.2, Q48 | Guide |
| O4 | Agreement for grading drafts: within one band (Q44). For chapters, summaries and practice: **proposed in design §11.4** (#197): a usable share and a strict share, with the wrong-answer rate separate. The guide settles it when he approves the design | Q44, Q48 | Guide |
| O5 | Mentor review time for non-grading outputs: **proposed in design §11.4** (#197): reuse the grading protocol (Q46) for every task. The guide settles it when he approves the design | Q46 | Guide |
| O6 | Grading-draft items: B8.4 merged, its submission-content rule (decided: PRD B1.5), reference grades (Q13), `GradeDraftV1` (Q41) | §4.3a, §4.3d | Guide, Students 1 and 3 |
| O7 | Practice: task shape and output format (B7, FR-S-12, Release 5 stretch). **Proposed by Student 1 on PR #33**: multiple-choice checkpoint questions (H5P question set) in the review-card shape; ordering and the branching scenario left out of the first version, no short answer; B7 defines no draft format. Format confirmed by the guide (reported by Harshitha on 18 Nov; the link to his answer is still to be added); the lecture input is still open | Q12 | Students 1 and 4, guide |
| O8 | Size of the set per task (the PRD gives none). **Proposed in design §11.4** (#197): one chapters item and one summary item for one or two of the five B8.5 lectures (Student 4 confirms the number once the timings exist), five practice items, and the grading items from the B8.4 test split (Q45). The guide settles it when he approves the design | — | Guide |
| O9 | **Decided (guide, issue #186):** Apache-2.0, like the repository (PRD C-11) | root `CLAUDE.md` §2.10 | Guide |
| O10 | Accept this format as the B8.6 part of the B8 contract before the Release 0 freeze | `contracts/CLAUDE.md` | All four students, guide |
| O11 | ~~Chapters content schema~~ **Closed:** B6.2 now defines it (`contracts/chapters.v1.schema.json`); this set uses it and keeps no schema of its own | PR #32 | Student 4 |

Before any comparison run (design §11.4, §11.2): the rubric is fixed (`frozen: true`), every
expected output is reviewed, the prompts are frozen, and the provider they were developed on is
recorded.

**Undo:** the set is plain files. Delete an item's folder and its manifest entry to remove it.

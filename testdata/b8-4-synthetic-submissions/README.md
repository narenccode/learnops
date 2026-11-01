# B8.4 synthetic submissions (PROVISIONAL pilot)

**Status: PROVISIONAL.** Six pilot submissions and a proposed format. This is not the B8.4 set
required by PRD §B8 yet, and it does not claim to match the B8.2 sample course.

| | |
|---|---|
| PRD | §B8 (B8.4), §C3.7 (agreement on B8.4), §B1.3 (marking table), §C3.5 (machine checks) |
| Owner | Student 3 |
| Design | `docs/design/grading.md` §11.3 (Draft) |
| Tests | `libs/contracts/tests/test_b8_4_dataset.py` |
| Source | Written for this project by Student 3. Entirely fictional: placeholder learners (`learner-NN`), fictional organisations, reserved `.invalid` URLs (RFC 2606). No real learner data. |
| Licence | Open decision (O8) |

## What PRD §B8 requires, and what this pilot has

| PRD §B8 requires | Pilot |
|---|---|
| At least 30 submissions | 6 |
| Each has a repo, a demo link and a short report | Yes: `repo/`, `demo_url`, `report.md` |
| Across quality levels | strong 2, partial 2, weak 1, incorrect 1 |
| Reference grades from at least one mentor | **None.** No mentor is named yet (O3). Nothing in this folder is a grade. |

## Why the pilot is provisional

1. **Rubrics.** The B8.2 sample course (Student 1) does not exist yet. The pilot uses the two
   marking tables of the merged B1 contract example (`contracts/examples/course-package.v1`,
   `wk-01-task` and `wk-02-task`). That example says it "is not the B8.2 sample course".
2. **Submission form.** How a repository URL, demo link and report are placed in a Moodle
   submission (the submission-content rule, design §4.3a, Q32) is not decided. So
   `submission.yaml` keeps them as separate neutral fields and nothing is rendered for Moodle.
3. **Format.** B8's contract file is `testdata/README.md` (`contracts/CLAUDE.md`), and it is
   frozen after Release 0. The schemas here are a proposal that the other owners and the guide
   have not reviewed.

**The pilot must be retargeted once B8.2 is merged and Q32 is resolved:** point each rubric at
the B8.2 assignment, rewrite the submissions against its marking tables, render them by the
submission-content rule, then extend the set to at least 30.

## Layout

```
manifest.yaml                    index: rubrics + one entry per submission
schemas/                         JSON Schemas (Draft 2020-12) for the four document types
submissions/sNNN/
  submission.yaml                repository_url, demo_url, report, repo_dir, hosting
  report.md                      the short report
  repo/                          the fictional repository content
  expected.yaml                  author's expected outcome per criterion (no scores)
reference-grades/                mentor reference grades (empty, see its README)
```

How a submission links to its question, rubric and reference grade:

```
manifest.submissions[].rubric ──> manifest.rubrics[].id
   rubrics[].assignment_idnumber + course_package ──> the assignment (points)
   rubrics[].task_body ──> task text (the question) + marking table (the rubric)
submissions/<id>/expected.yaml  criteria == marking-table rows, checks == Check cells, in order
reference-grades/**/<id>.yaml   submission_id + rubric; criteria == marking-table rows
```

## Fields

**`manifest.yaml`**: `intended_level` is `strong`, `partial`, `weak` or `incorrect`. It is
what the author wrote the submission to be, **not a grade**. `ambiguous: true` means a reasonable
mentor could judge at least one criterion either way. `split` stays `unassigned` until the guide
decides the split (O5). `edge_cases` uses a fixed list of tags (see the schema).

**`submission.yaml` `hosting`**: what a future publish step must set up. `publish_repo: false`
means the repository is not published, so the URL does not clone. `demo_stub` is `answers` (a
stub page that answers the test question), `unrelated_page` (HTTP 200 with unrelated content) or
`none` (nothing is served). The URLs are placeholders on `git.lab.invalid` / `demo.lab.invalid`.
The publish step replaces them with lab addresses (O6).

**`expected.yaml`**: for every marking-table criterion, the intended result of each check
(`pass`, `fail`, `error`, `undetermined`) with the reason, plus a qualitative `judgement` (`meets`,
`partly_meets`, `does_not_meet`, `ambiguous`) with the rationale. It records **no score**. The
schema and the tests reject `score`, `points`, `total` and `grade`. `ambiguous` is used when the
answer depends on a rubric reading that is not decided. Those cases are left to the mentor.

## Pilot submissions

| Id | Rubric | Level | Designed to exercise |
|---|---|---|---|
| s001 | wk-02 | strong | Every check passes; two weak answers named and explained |
| s002 | wk-02 | partial | README heading "How to use" instead of "Usage" (ambiguous); one clear and one vague weak answer (ambiguous) |
| s003 | wk-02 | strong | Near-duplicate of s001 (renamed identifiers, reworded report) for the similarity flag (FR-G-04) |
| s004 | wk-01 | partial | Good reflection at 193 words, just under `word_count:200` |
| s005 | wk-01 | weak | No README, nothing served at the demo link, very short reflection |
| s006 | wk-01 | incorrect | Off-topic project; repository not published (checks `error`); demo returns 200 with an unrelated page, so the check passes but the criterion is not met; reflection long enough but off topic (ambiguous) |

Not covered yet: a resubmission (needs the submission-version rules, design §5.4), a demo that
times out, and a repository that clones but has no `Usage` section at all. Add them when the set
is retargeted.

## Provisional rules used by the tests

These are not decided. They exist only so that `expected.yaml` can be checked against the files.

- **Word count:** whitespace-separated tokens of the whole `report.md` (the real rule is design §4.3b, Q39).
- **`readme_sections`:** Markdown heading text at any level, case-insensitive, exact names, no synonyms, fenced code ignored (§4.3b proposal).
- **`command:<name>`:** `undetermined`, because no check config exists (§4.3c, Q33). It is `error` when the repository cannot be cloned.
- **No clone:** `repo_clone` is `fail`, and every check that needs the clone is `error` (§4.3d).

## Open decisions (need team or guide agreement; not decided here)

| # | Decision | Design ref | Who |
|---|---|---|---|
| O1 | Retarget to the B8.2 marking tables once B8.2 is merged | §11.3 | Student 1, Student 3 |
| O2 | Submission-content rule: how repository, demo and report appear in Moodle | §4.3a, Q32 | Guide, Student 1 |
| O3 | Who writes the reference grades, when, and whether a second mentor grades ≥ 10 | §11.3, Q13 | Guide |
| O4 | Band definition, whole-number scores and the cap when a required check fails | §11.2, Q44, Q25 | Guide |
| O5 | Set size (30 or ≥ 60), development / sealed test split, who authors the test split | Q45, Q47 | Guide |
| O6 | Lab git server and demo stub hosting; the publish script | §11.3 (lab) | Lab, Student 3 |
| O7 | Accept this format (schemas, field names) as the B8.4 part of the B8 contract before the Release 0 freeze | `contracts/CLAUDE.md` | All four students, guide |
| O8 | Licence of the test content (proposal: Apache-2.0, like the repository) | root `CLAUDE.md` §2.10 | Guide |
| O9 | Counting and matching rules for `word_count` and `readme_sections` | §4.3b, Q39 | Guide, Students 1 and 2 |
| O10 | Ambiguous cases in the pilot: s002 README heading, s002 weak answers, s006 off-topic reflection | — | Mentor (in the reference grade) |

## Adding a submission

1. Add an entry to `manifest.yaml` (next free `sNNN`, fictional `learner-NN`).
2. Create `submissions/sNNN/` with `submission.yaml`, `report.md`, `repo/` and `expected.yaml`.
   Use only `.invalid` URLs and invented names. Do not add an email address or a real person.
3. Run `python -m pytest libs/contracts/tests/test_b8_4_dataset.py -q`.

Repository code under `repo/` is synthetic test content. Do not name a file `test_*.py` or
`*_test.py`, so that the repository's own pytest run does not collect it.

**Undo:** the set is plain files. Remove a submission by deleting its folder and its manifest entry.

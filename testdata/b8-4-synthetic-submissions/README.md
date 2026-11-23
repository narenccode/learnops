# B8.4 synthetic submissions (PROVISIONAL)

**Status: PROVISIONAL, not complete.** 33 submissions and a proposed format. The count meets the
PRD §B8 minimum of 30, but **no mentor has graded them**, so B8.4 is not complete. The submissions are
written against all four tasks of the B8.2 sample course (#61), in the submission form of PRD B1.5 (#87).

| | |
|---|---|
| PRD | §B8 (B8.4), §C3.7 (agreement on B8.4), §B1.3 (marking table), §C3.5 (machine checks) |
| Owner | Student 3 |
| Design | `docs/design/grading.md` §11.3 (Draft) |
| Tests | `libs/contracts/tests/test_b8_4_dataset.py` |
| Source | Written for this project by Student 3. Entirely fictional: placeholder learners (`learner-NN`), fictional organisations, reserved `.invalid` URLs (RFC 2606). No real learner data. |
| Licence | Open decision (O8) |

## What PRD §B8 requires, and what this set has

| PRD §B8 requires | This set |
|---|---|
| At least 30 submissions | 33 |
| Each has a repo, a demo link and a short report | Yes, except where a case removes one on purpose (s021 has no `Demo:`): `repo/`, the `Demo:` line of the online text, and a `Report:` section or `report.md` |
| Across quality levels | strong 8, partial 9, weak 8, incorrect 8 |
| Reference grades from at least one mentor | **None.** No mentor is named yet (O3). Nothing in this folder is a grade. |

## Why the set is provisional

1. **No reference grades.** PRD B8.4 asks for reference grades from at least one mentor. The guide
   (issue #186, 23 Nov 2026) will name the mentor. The author's own grades are in `author-grades/`,
   labelled "author-graded, not reference grades" (see "Author grades" below). Until a mentor has
   graded, the set is not complete.
2. **Development split only.** The author wrote every submission, so all are in the development split.
   The sealed test split (design Q47) is to be written by someone else (Student 1 or the guide) where
   possible; authorship is recorded in `manifest.yaml`.
3. **Submission form.** Each `submission.yaml` carries the online text with the `Repository:`, `Demo:`
   and `Report:` lines of PRD B1.5, and a `report.md` only when the online text has no `Report:`
   section. Plain text only: editor HTML (B1.5 rule 5) is unverified until the lab check, so **no case
   uses it**. A submission written as editor HTML (s028) was left out; its id is not reused. How the
   real extractor reads these files is Module 3's (Release 4); the tests use a stand-in reader that is
   checked against the shared vectors.
4. **Format.** B8's contract file is `testdata/README.md` (`contracts/CLAUDE.md`), and it is frozen after
   Release 0. The schemas here are a proposal that the other owners and the guide have not accepted
   (O7). The guide said on issue #186 that Akshita or Nagashree approve the formats.

## Layout

```
manifest.yaml                    index: rubrics + one entry per submission
schemas/                         JSON Schemas (Draft 2020-12) for the four document types
submissions/sNNN/
  submission.yaml                onlinetext (Repository:, Demo:, Report: lines), files, repo_dir, hosting
  report.md                      the report, only when the online text has no Report: section
  repo/                          the fictional repository content
  expected.yaml                  author's expected outcome per criterion (no scores)
reference-grades/                mentor reference grades (empty, see its README)
author-grades/                   the author's own grades, labelled "author", NOT reference grades
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
`none` (nothing is served). The links in the online text are placeholders on `git.lab.invalid` /
`demo.lab.invalid`. The publish step replaces them with lab addresses (O6).

**`expected.yaml`**: for every marking-table criterion, the intended result of each check
(`pass`, `fail`, `error`, `undetermined`) with the reason, plus a qualitative `judgement` (`meets`,
`partly_meets`, `does_not_meet`, `ambiguous`) with the rationale. It records **no score**. The
schema and the tests reject `score`, `points`, `total` and `grade`. `ambiguous` is used when the
answer depends on a rubric reading that is not decided. Those cases are left to the mentor.

## Submissions

| Id | Task | Level | Exercises |
|---|---|---|---|
| s001 | wk-02 | strong | every check passes |
| s002 | wk-02 | partial | README section missing; ambiguous judgement |
| s003 | wk-02 | strong | near-duplicate of s001 |
| s004 | wk-01 | strong | every check passes |
| s005 | wk-01 | weak | README missing; demo unreachable; report under the word count |
| s006 | wk-01 | incorrect | repository not cloneable; check passes but criterion unmet; off topic; ambiguous judgement |
| s007 | wk-01 | strong | every check passes |
| s008 | wk-01 | partial | README section missing; report just over the word count |
| s009 | wk-01 | partial | report under the word count |
| s010 | wk-01 | weak | demo times out; report under the word count |
| s011 | wk-01 | incorrect | repository not cloneable; report under the word count; check passes but criterion unmet; off topic |
| s012 | wk-02 | partial | README section missing |
| s013 | wk-02 | weak | README missing; demo unreachable |
| s014 | wk-02 | weak | demo times out |
| s015 | wk-02 | incorrect | check passes but criterion unmet; off topic |
| s016 | wk-02 | incorrect | repository not cloneable; demo unreachable |
| s017 | wk-03 | strong | every check passes |
| s018 | wk-03 | strong | report comes from `report.md` because the online text has no `Report:` section (B1.5 rule 4) |
| s019 | wk-03 | partial | check passes but criterion unmet |
| s020 | wk-03 | partial | repository file missing |
| s021 | wk-03 | weak | label missing (B1.5 rule 7); no `Demo:` line, so the demo check is `error` (B1.5 rule 7) |
| s022 | wk-03 | weak | repository file missing; demo unreachable |
| s023 | wk-03 | incorrect | repository not cloneable; check passes but criterion unmet; off topic |
| s024 | wk-03 | incorrect | check passes but criterion unmet; off topic |
| s025 | wk-04 | strong | a `Demo:` line inside the report is report text, not a label (B1.5 rule 3) |
| s026 | wk-04 | strong | near-duplicate of s025; report just over the word count |
| s027 | wk-04 | partial | report under the word count |
| s029 | wk-04 | weak | README section missing; demo unreachable; report under the word count |
| s030 | wk-04 | weak | demo times out; README section missing; report under the word count |
| s031 | wk-04 | incorrect | check passes but criterion unmet; off topic; ambiguous judgement |
| s032 | wk-04 | incorrect | repository not cloneable; demo unreachable; report under the word count |
| s033 | wk-02 | partial | label missing (B1.5 rule 7); ambiguous judgement; a link written inside another line is not a label (B1.5 rule 6) |
| s034 | wk-02 | partial | label repeated (B1.5 rule 7); ambiguous judgement; two `Repository:` lines: `field_repeated`, the first does not win (B1.5 rule 7) |

Not covered yet: a resubmission (needs the submission-version rules, design §5.4), online text as editor
HTML (B1.5 rule 5; add a case only after the lab check), and a `command:<name>` check (B8.2 uses none,
so the tag `command_check_undetermined` is not exercised either). s028 is left out for the HTML reason.

## Author grades (not reference grades)

`author-grades/<submission id>.yaml` holds the author's own grade (Student 3) for 31 of the 33
submissions, graded by hand on the B8.2 marking tables on 17 Nov 2026. s033 and s034 were added later
and are not graded. **They are not reference grades.** PRD B8.4 asks for reference grades from at
least one mentor, and the guide decided on issue #186 (23 Nov 2026) that the author's grades may stay in
the set only when labelled "author-graded, not reference grades". The label is part of every file and of
the schema (`schemas/author-grade.schema.json`):

- `graded_by` is `author` and `reference_grade` is `false`;
- a `mentor_ref` is refused, so an author grade cannot pass as a mentor's;
- an author grade does not validate as a reference grade (`schemas/reference-grade.schema.json`), and
  the tests check that.

The criteria must match the marking table in order, no score may exceed its criterion's points, and
`total` is the sum, as for a reference grade. The set stays not complete until a mentor, named by the
guide, has graded it: the mentor's files go in `reference-grades/`, and the author grades stay as
they are.

## Provisional rules used by the tests

These are not decided. They exist only so that `expected.yaml` can be checked against the files.

- **Reading the online text:** B1.5 rules 1 to 7 on plain text, by a stand-in reader in the test file.
  It is checked against the 12 plain cases of `contracts/test-vectors/submission.v1.json`; it is not
  Module 3's extractor.
- **Word count:** whitespace-separated pieces of the report: the `Report:` text, or the whole report file as it is (B1.3).
- **`readme_sections`:** the B1.3 heading rule (ATX headings of 1 to 6 `#`, at most three leading spaces, closing `#` sequence removed, backtick and tilde fences, an unclosed fence runs to the end, Setext headings do not count), checked against the 12 README cases of the same vectors file. Whole heading text, case-insensitive.
- **`command:<name>`:** `undetermined`, because no check config exists (§4.3c, Q33). It is `error` when the repository cannot be cloned.
- **No clone:** `repo_clone` is `fail`, and every check that needs the clone is `error` (§4.3d).

## Open decisions

The guide answered most of these on issue #186 (23 Nov 2026). What is decided is marked; the rest stays open.

| # | Decision | Design ref | Who |
|---|---|---|---|
| O1 | ~~Retarget to the B8.2 marking tables~~ **Done** (all four tasks; B8.2 merged in #61) | §11.3 | Student 1, Student 3 |
| O2 | ~~Submission-content rule~~ **Decided** in PRD B1.5 (#87); this set follows it for plain text. Editor HTML stays unverified until the lab check | §4.3a, Q32 | Guide, Student 1 |
| O3 | Reference grades. **Decided (guide):** the author's grades may stay, labelled "author-graded, not reference grades"; **one mentor, whom the guide names, must grade the set** before B8.4 counts as complete. A second mentor on at least 10 is for Release 4, not Release 0 | §11.3, Q13, Q47 | Guide (names the mentor) |
| O4 | Band definition, whole-number scores and the cap when a required check fails. **Guide:** use the grading design's proposals for now and mark them provisional; settled when the design is approved | §11.2, Q44, Q25 | Guide |
| O5 | Set size and split. **Decided (guide):** 30 is the minimum, writing 60 can wait; use the seeded development and test split of Q47, with the sealed test split written by Akshita or the guide where possible; record who wrote each submission | Q45, Q47 | Guide |
| O6 | Lab git server and demo stub hosting; the publish script | §11.3 (lab) | Lab, Student 3 |
| O7 | Accept this format (schemas, field names) as the B8.4 part of the B8 contract before the Release 0 freeze. **Guide:** Akshita or Nagashree approve it (PRD B.0 rule 3); he reviews the whole contract set at the Release 0 gate | `contracts/CLAUDE.md` | Akshita or Nagashree, guide |
| O8 | ~~Licence of the test content~~ **Decided (guide):** Apache-2.0, as the repository and PRD C-11 | root `CLAUDE.md` §2.10 | — |
| O9 | Counting and matching rules for `word_count` and `readme_sections`. **Guide:** Akshita proposes one rule, Harshitha and Shraddha check it against the parser in `libs/contracts`, and the guide confirms it through `/contract-change` | §4.3b, Q39 | Akshita, Shraddha, guide |
| O10 | Ambiguous cases: s002 README heading and weak answers, s006, s015 and s031 off-topic reflections, and the label cases s033 and s034 (a link the check cannot read but a person can) | — | Mentor (in the reference grade) |

## Adding a submission

1. Add an entry to `manifest.yaml` (next free `sNNN`, fictional `learner-NN`).
2. Create `submissions/sNNN/` with `submission.yaml` (the online text; `files: [report.md]` and a
   `report.md` only when it has no `Report:` section), `repo/` and `expected.yaml`.
   Use only `.invalid` URLs and invented names. Do not add an email address or a real person.
3. Run `python -m pytest libs/contracts/tests/test_b8_4_dataset.py -q`.

Repository code under `repo/` is synthetic test content. Do not name a file `test_*.py` or
`*_test.py`, so that the repository's own pytest run does not collect it.

**Undo:** the set is plain files. Remove a submission by deleting its folder and its manifest entry.

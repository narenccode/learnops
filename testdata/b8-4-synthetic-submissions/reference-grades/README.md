# B8.4 reference grades

PRD §B8 requires reference grades "from at least one mentor". The guide decided on issue #186
(comment 7097143671) that one student acts as the mentor for the Release 0 reference grades; she
accepted on 24 Nov.

**`mentor-01/` holds her grades for all 33 submissions (graded 25 Nov 2026).** She graded each one by
hand on its B8.2 marking table, from the submission files only: she did not see the author's
`expected.yaml` files, the author's grades or any AI draft (`blind_to_drafts: true`). Every score and
reason is hers; an AI tool only converted her finished score sheet into these files and checked them
against the schema. Nobody else may write or change a grade here, and neither may an AI tool.

The grades are labelled "student acting as mentor": a recorded deviation from PRD B8.4 and G-5, and
any report that uses them says so. The author's `expected.yaml` files are not grades, and the
author's own grades are in `../author-grades/`, labelled as author grades. They are not reference
grades.

When a mentor grades:

- Write one file per submission, `reference-grades/<mentor_ref>/<submission id>.yaml`, valid
  against `../schemas/reference-grade.schema.json`.
- `mentor_ref` is a pseudonym (`mentor-01`). The mapping to a real person is kept outside the
  repository.
- Grade on the submission's rubric before seeing any AI draft, and record `blind_to_drafts`.
- `criteria` lists every marking-table criterion in order with `score` (0 to the criterion's
  points) and `reason`. `total` is their sum. The tests check all of this.
- Score granularity, the band, and how the provisional pilot is graded (or whether it is
  retargeted first) are open decisions O1, O3 and O4 in `../README.md`.

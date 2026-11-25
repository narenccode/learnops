# B8.4 reference grades

**Empty on purpose.** PRD §B8 requires reference grades "from at least one mentor". The guide decided
on issue #186 (comment 7097143671) that one student acts as the mentor for the Release 0
reference grades; she accepted on 24 Nov, and has not graded yet, so this folder has no grade files.
Nobody else may write one, and neither may an AI tool. The grades are labelled "student acting as
mentor": a recorded deviation from PRD B8.4 and G-5, and any report that uses them says so. The author's `expected.yaml` files are not grades, and the author's own
grades are in `../author-grades/`, labelled as author grades. They are not reference grades.

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

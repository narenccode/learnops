# B8.4 reference grades

**Empty on purpose.** PRD §B8 requires reference grades "from at least one mentor". No mentor has
been named yet (design Q13), so this folder has no grade files. Nobody else may write one, and
neither may an AI tool. The author's `expected.yaml` files are not grades.

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

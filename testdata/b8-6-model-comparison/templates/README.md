# B8.6 mentor review templates (PROPOSED)

Two forms for a blinded mentor to review an AI draft, used by the comparison study (FR-M-03). They
are **proposals**: the levels, the questions and the wrong-answer rule come from `../rubric.yaml`,
which the guide has not decided (design section 11.2, Q48; open decisions O2 to O5 in `../README.md`).
Each file here is an **invented example** to show the format. No real review exists, and no model
has been run.

| Form | For | Schema | Example |
|---|---|---|---|
| Grade-draft review | AI grading drafts (items `gd-NNN`) | `../schemas/grade-draft-review.schema.json` | `grade-draft-review.example.yaml` |
| Output review | AI chapters, summaries and practice drafts (items `ch-`, `su-`, `pr-`) | `../schemas/output-review.schema.json` | `output-review.example.yaml` |

## What the mentor writes

- **Grade-draft review**: for every criterion of one draft, the mentor copies their own reference
  score (the B8.4 reference grade, written **before** seeing any draft), writes the draft's score
  and the difference, and answers yes or no: is the draft's evidence supported by the
  submission, is its feedback acceptable, is the criterion draft wrong (the rule in
  `../rubric.yaml`, `grade_draft_review`). Then the totals and whether the draft total is within one
  band of the reference total.
- **Output review**: one level, `acceptable`, `acceptable_with_edits` or `unusable_or_wrong`
  (only the last counts as wrong), four yes or no checks, and the edits needed.
- Both: the time spent, and `blind_to_provider: true` only if the mentor did not know which
  provider wrote the draft. `draft_id` is an opaque id (`draft-NNN`) that never names a provider.

## Rules

- Only a mentor writes a review. Nobody else, and no AI tool.
- `mentor_ref` is a pseudonym (`mentor-01`); the real name is kept outside the repository.
- Fictional test data only: no real names, no email addresses, no real links.
- A real review goes in `../reviews/<item id>/<draft id>.yaml` (not created yet). The example files
  here are not reviews and are never counted as results.

## Not decided here

- The practice form: practice has no agreed format (design Q12), so only the generic output review
  applies to it for now.
- Agreement for chapters, summaries and practice, the timing protocol for review time (O4, O5), and
  how many mentors review each draft.

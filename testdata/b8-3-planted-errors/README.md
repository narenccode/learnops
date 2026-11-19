# B8.3 Planted-error course packages

> **Status.** Four mutated copies of the B8.2 sample course are present. Each was
> checked through the D2 checker CLI and produces exactly one expected error.
> Automated regression tests cover all four cases. This is a D2 demo subset,
> not complete CK-01…CK-13 coverage or proof of PRD §C2.7 acceptance.

## 1. Purpose and scope

B8.3 supplies course-package variants with known planted defects for testing the
Course Checker (PRD §B8.3 and §C2.7). Each variant is copied from the B8.2
four-week sample package and contains one intended defect. The clean B8.2
source is not modified.

These are package folders, not Moodle `.mbz` backups. They test only behavior
currently implemented by the shared B1 validator. They do not exercise every
CK-01…CK-13 rule.

## 2. Layout

```text
testdata/b8-3-planted-errors/
  README.md
  answer.yaml
  duplicate-id/package/
  invalid-mode/package/
  missing-body/package/
  protected-id/package/

## 3. Planted errors and observed results

| Variant | Mutation | Observed validator code | B1 rule | Location |
|---|---|---|---|---|
| `missing-body` | Delete `weeks/02-task.md` | `body_file_missing` | B1.1 | `sections[1].activities[1].body` |
| `duplicate-id` | Week 2 task reuses `wk-01-task` | `duplicate_idnumber` | B1.2 rule 6 | `sections[1].activities[1].idnumber` |
| `protected-id` | Week 4 task uses protected ID `final-project` | `schema_not` | B1.1 | `sections[3].activities[1].idnumber` |
| `invalid-mode` | Change course mode to `everything` | `schema_enum` | B1.1 | `course.mode` |

Each variant returned `ok: false` and exactly one error through
`checker check <package> --json`. The exact messages and expected fields are
recorded in [`answer.yaml`](answer.yaml).

The `not_checked` entries in the CLI report are not additional errors. Some
cross-checks cannot run when the package has a schema-level error.

## 4. Source and licence

The baseline is the B8.2 sample course package from the project repository
(`testdata/b8-2-sample-course/package/`). Its README describes the content as
fictional original LearnOps material, Apache-2.0, with no learner data or
third-party material. The B8.3 packages are copies with only the mutations
listed above; the same source and licence statement applies.

## 5. Limitations

- This four-case set is a D2 demonstration subset, not full CK-01…CK-13
  coverage.
- Three cases are schema or package-structure validation failures under B1.1;
  the duplicate-ID case is B1.2 rule 6.
- The validator's `rule` field identifies B1 rules, not CK catalogue IDs.
  Do not infer CK mapping from these results.
- The current validator does not implement all Course Checker rules.
  Additional planted cases must be added as those rules become testable.
- Akshita's 18-case probe identified five behaviors not currently detected
  by the validator. Those remain known gaps and are not represented as passing
  planted-error cases here.
- `libs/contracts/tests/test_b8_3_dataset.py` verifies each variant against
  its expected error code, rule, location, idnumber and message.
- `modules/checker/tests/test_cli.py` verifies JSON output and exit status for
  the clean B8.2 baseline, all four planted-error variants, and a missing
  package.
- The D2 CLI currently supports directory packages only. It does not implement
  `.mbz` input or `checker diff`.

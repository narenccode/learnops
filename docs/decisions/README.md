# Decision records: index and Moodle version exceptions

This page is the one place to find the Moodle version rule and the Release 0
exceptions. The rule is in `docs/PRD.md` (C-03); this page does not restate it.
Each exception is held in its decision record, and other documents point here
and to that record instead of repeating the waiver.

## The rule

PRD C-03: everything works on Moodle 4.5 and Moodle 5.3. The checker harness
(FR-C-08) and the design documents rest on it. An exception is temporary and is
reviewed at each release gate.

## Release 0 exceptions

| Item | Release 0 | Decision record | Scope | Ends |
|---|---|---|---|---|
| B8.1 template course | Built and tested on 5.3 only; 4.5 not tested | [0009](0009-b8-1-template-course.md) | B8.1 only | Before the harness in Release 1, if C-03 stays: rebuild once on 4.5 |
| B8.2 sample course: restore and merge tests | 5.3 only; 4.5 not tested | [0010](0010-b8-2-sample-course.md) (A5 on PR #61) | B8.2 restore and merge tests only | Release 1, when the template is rebuilt on 4.5 |
| B4 rule R3, lock race on 4.5 | Accepted, documented limitation | B4 contract and grading design | B4 R3 | Not a version exception; it ends when Moodle's behaviour changes |
| Everything else, including B3/LTI and the checker harness (FR-C-08) | Both 4.5 and 5.3 | PRD C-03 | No exception | — |

## How a new exception is added

1. The guide decides it.
2. A decision record holds the scope, the reason, the cost and the date.
3. One row is added above.
4. No other document repeats it; they point here.

## Numbering: two records share 0001

Two records share the number 0001: `0001-lti-library.md` (the LTI library record) and `0001-b5-model-interface-v1.md` (the B5 record). Both stay as they are, because each is cited by file name in about ten places (contract text, schema comments and tests). "ADR 0001" means the LTI record and "decision 0001" means the B5 record, and each is cited by its full file name. New records take the next free number. (Guide, [issue #186](https://github.com/narenccode/learnops/issues/186#issuecomment-7101984198), 23 November 2026.)

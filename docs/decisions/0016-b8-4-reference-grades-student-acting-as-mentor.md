# B8.4 reference grades: a student acting as mentor, for Release 0

**Status:** decided by the guide on issue #186 (2026-11-23, design Q13 and B8.4 O3). Accepted by the
student on 2026-11-24. The grades were delivered on 2026-11-25 (pull request #221).
**Number:** 0016, the next free number when this was written (2026-11-25: `main` has 0001 to 0015, 0017
and 0018; 0016 was kept for this record). It is taken again at merge if another record has merged first.

## Decision

Any one student may act as the mentor for the Release 0 reference grades of the B8.4 synthetic
submissions. The guide chose **Akshita (Student 1)**. She owns B8.2, so she knows its marking tables,
and she did not write the 33 submissions.

- She grades **every** submission on the B8.2 marking table **before she sees any draft** from the
  grading assistant.
- The grades go in `testdata/b8-4-synthetic-submissions/reference-grades/mentor-01/` and are labelled
  **"student acting as mentor"**.
- Harshitha's own grades stay in `author-grades/`, labelled "author-graded, not reference grades". They
  are not reference grades.

This is a **recorded deviation from PRD B8.4 and G-5**, which say "mentor". The PRD text does not
change.

## The label travels with the grades

Any report, table or figure that uses these grades says where they came from: a student acting as
mentor, not a mentor. The guide's lesson: when a student stands in for a mentor, the decision says so
and the label travels with the grades.

## Scope

- Release 0 reference grades for B8.4 only (33 submissions).
- A second grader for at least 10 submissions, and the sealed test split, stay for the **Release 4**
  measurement. The guide decides those then.
- Nothing here changes who may approve a draft grade in the product (PRD A7: AI output is a draft; a
  mentor approves).

## Reason

PRD B8.4 asks for reference grades from at least one mentor.

**The guide's reason, from his comment:** Akshita owns B8.2, so she knows the marking tables, and she did
not write the 33 submissions. His other two points are instructions and a lesson, not reasons: she grades
every submission before she sees any draft from the grading assistant, and the label "student acting as
mentor" travels with the grades.

**The author's reading (Student 3's own words, not the guide's):** grading before seeing any draft keeps the
grades independent of the assistant, and the label keeps the deviation visible to anyone who uses the grades.

## Where it was decided and done

- Guide's decision, issue #186, 2026-11-23:
  [comment](https://github.com/narenccode/learnops/issues/186#issuecomment-7097143671).
- Akshita's acceptance, issue #186, 2026-11-24:
  [comment](https://github.com/narenccode/learnops/issues/186#issuecomment-7128769282).
- Grades: pull request #221, merged 2026-11-25 (33 of 33 in `reference-grades/mentor-01/`).
- Recorded in the grading design (`docs/design/grading.md`, §11.3 and Q13) and in the B8.4 and B8.6
  READMEs.

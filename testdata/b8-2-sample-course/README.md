# B8.2 Sample Course

> **Status.** The package is written and passes the shared validator and a dataset test. No `.mbz`
> exists and nothing has been restored on Moodle or run through the checker. Labels: **PRD** =
> stated by the PRD. **Confirmed** = decided by the guide on PR #61 (2026-11-11). **Owner** =
> confirmed by the project owner on a GitHub issue, cited by number and date (here Issue #55,
> 2026-11-12, and Issue #65, 2026-11-12). **Proposal** = the B8.2 owner's choice where the PRD is
> silent, or a value the owner marked a proposal; not a contract value. **PENDING GUIDE
> CONFIRMATION** = open decision. **PENDING MOODLE LAB** = needs a Moodle site.

## 1. Purpose and scope

**PRD §B8:** "A fictional 4-week project-based course package following B1". It is the clean baseline
for the checker (no false errors, PRD §C2.7), the input of the Studio build and restore test (PRD
§C1.7), and the parent of the planted-error variants in B8.3. Owner: Student 1. Release 0 test data.

It is a **package** (folder with `course.yaml` and Markdown bodies), not a backup. Studio builds the
`.mbz` later (FR-S-06, Release 2). Out of scope here: the `.mbz`, the B8.1 template, B8.3 variants,
B8.4 submissions.

## 2. Layout

```
testdata/b8-2-sample-course/
  README.md                 this file
  package/course.yaml       the B1 document (mode: full)
  package/weeks/01-guide.md … 04-guide.md   guide Pages (weeks 1 to 4; sections 4 to 7)
  package/weeks/01-task.md  … 04-task.md    task Assignments, each with one marking table
libs/contracts/tests/test_b8_2_dataset.py   the dataset test
```

## 3. Expected structure (plain list for the checker)

Weeks 1 to 4 are **sections 4 to 7**. The B8.1 template holds sections 1 to 3, and generated
sections for a merge test must be numbered after the template's last section, because a merge
restore keeps the name and summary of a section that already exists at that number (Owner,
Issue #55, 2026-11-12). The week titles and the idnumbers keep the week numbers. Every task:
`completion: submit`, `submission: [onlinetext, file]`, 25 points. Each week after the first
unlocks on the previous task.

| Section | Week | idnumber | Guide Page | Task Assignment | Unlocks after | Points |
|---|---|---|---|---|---|---|
| 4 | 1 | `wk-01` | `wk-01-guide` | `wk-01-task` | nothing (open) | 25 |
| 5 | 2 | `wk-02` | `wk-02-guide` | `wk-02-task` | `wk-01-task` | 25 |
| 6 | 3 | `wk-03` | `wk-03-guide` | `wk-03-task` | `wk-02-task` | 25 |
| 7 | 4 | `wk-04` | `wk-04-guide` | `wk-04-task` | `wk-03-task` | 25 |

**Section idnumbers (to update later).** The section idnumbers `wk-01` to `wk-04` are kept for now,
because B1 v1 still requires one on every section. The owner decided on Issue #65 (2026-11-12) that
B1's section `idnumber` becomes optional (an authoring label that Moodle never stores) through a B1
`/contract-change` that is not implemented yet. When it is, these idnumbers, the `course.yaml`
comment, this table and the dataset test need updating. The activity idnumbers (`wk-01-guide`,
`wk-01-task`, …) are not affected.

Total: 4 sections (numbers 4 to 7), 8 activities, 100 points (`total_points: 100`, PRD B1.2 rule
3). Marking tables use only checks from PRD §C3.5: `http_ok:demo_url`, `repo_clone`,
`repo_file:TESTS.md`, `readme_sections:…`, `word_count:…`, and `—` for mentor judgement. Each task
body explains the submission format (A12); the marking tables follow the check format (A13).

## 4. Assumptions and decisions

| # | Item | Status |
|---|---|---|
| A1 | Weeks 1 to 4 are sections **4 to 7** (week 1 is section 4) | Owner (Issue #55, 2026-11-12): generated sections for the merge test are numbered after the template's last section (3). Using exactly 4 to 7 is the B8.2 owner's choice within that rule. The PRD's B1.1 example numbers its weeks from 1; that is an example, not a rule |
| A2 | The protected section is the B8.1 template's **section 3** (`Final project`, holding the two protected items). It is **not** a field of `course.yaml`, and the contract and validator never hard-code it (PRD B1.4: configurable, no default). The dataset test holds 3 as a named working value. This replaces the earlier proposal of 7 after the weeks | Proposal: B8.1's README records the number 3 as a proposal, kept configurable (Owner, Issue #55, 2026-11-07). The title and contents of section 3 are Owner (2026-11-12). The number: PENDING GUIDE CONFIRMATION |
| A3 | B8.1's README (PR #57, merged 2026-11-13) records the template's layout: section 1 `Orientation` (Page `Welcome`), section 2 `Sample week` (Page `Sample guide`, Assignment `Sample task`), section 3 `Final project` (the two protected items). The weeks are now sections 4 to 7, so they do not overlap sections 1 to 3. This resolves the earlier mismatch with B8.1 | Owner (Issue #55, 2026-11-12), as recorded in PR #57 (merged 2026-11-13) |
| A4 | What the template holds beyond section 3. The owner's rule is that generated sections are numbered after the template's last section, and the owner gives the last section as 3 ("numbers after 3"). No later template section is stated, and the template has not been built | Sections 1 to 3: Owner (2026-11-12). Whether the built template has any later section: PENDING MOODLE LAB |
| A5 | Each weekly task is 25 points, total 100 | Proposal |
| A6 | **Course total after a merge.** B8.1's `Final project` assignment gets the 100 points and is the only graded item in the template; by the Moodle default those points count in the course total. With B8.2's 100 points (4 tasks of 25) the merged course total would be **200**. B8.2 alone totals 100 and keeps `total_points: 100`. The 200 is arithmetic from B8.1's points and has not been run on Moodle. **CK-03** (graded points differ from the target total) **stays open**: which target the checker uses, 200 for the merged course or the B1 default of 100, and for B8.2 alone, is not decided | B8.1's points: Proposal (Owner, Issue #55, 2026-11-12: "Proposal; do not design around it"; B8.1 README §4). The merged total: PENDING MOODLE LAB. The CK-03 target: PENDING GUIDE CONFIRMATION |
| A7 | `full` mode never contains the protected items (PRD B1.4), so a restored B8.2 has no final project, feedback, completion criteria or badge. Whether the checker (CK-07, CK-08) must accept that for "0 errors" is open (Studio design item 25) | PENDING GUIDE CONFIRMATION |
| A8 | Fictional theme, titles and shortname `SAMPLE-DOC-101` | Proposal |
| A9 | No `command:` checks (the PRD reads them from "the course's check config", which B1 does not define) | Confirmed (PR #61) |
| A10 | No start dates, no H5P, URL or Label activities (B7 practice is optional) | Proposal |
| A11 | Package in a `package/` subfolder so this README stays outside it | Proposal |
| A12 | **Submission format** (grading design Q6, `docs/design/grading.md` §4.3a). Online text with labelled lines `Repository: <URL>`, `Demo: <URL>` and `Report:` followed by the report text to the end. Labels are case-insensitive, one per line. A file named `report.md` or `report.txt` is the report when there is no `Report:` section. `http_ok:demo_url` reads `Demo`, `repo_clone` reads `Repository`, `word_count` reads the report. Each task body says how to label each part | Confirmed (PR #61). Not yet in the B1 contract: the B1 owner adds it with `/contract-change` before the 2026-11-20 freeze, with the five examples from §4.3a. B8.4 (PR #31) must use the same format |
| A13 | **Check format** (grading design Q9, §4.3b). One B1.3 marking table per task, only §C3.5 checks, `;` between checks, `readme_sections:` a comma list matched case-insensitively against README heading text, `word_count:` a whole number | Confirmed (PR #61). Not yet in the B1 contract (same `/contract-change` as A12) |

## 5. Protected items in a sections-only merge

The sections-only variant of B8.2 (the four weeks, as sections 4 to 7) is merged into a course made
from the B8.1 template, whose sections are 1 to 3 (A1 to A4). After the merge, the final project,
course feedback, completion criteria and badge must be unchanged: same `idnumber`s, same count,
criteria intact (PRD §C1.7). The expected list to compare against is in B8.1's README (PR #57,
merged 2026-11-13). The merge-test procedure and the clean-up of the test course are B8.1's:
its README §7 records the owner's sequence of 2026-11-13 (restore the template into a new course,
record the "before" table, merge the sections-only backup, record the "after" table, and delete the
course only after the result is recorded). Nothing below has been run.

**Expected result after the merge (a plan, not a result).** Sections 1 to 3 are the template's,
unchanged. Sections 4 to 7 are the four B8.2 weeks, added beside them. The protected items are
unchanged. The course total is 200 if the Final project's 100 points count (A6).

| Item | Status |
|---|---|
| Studio builds the sections-only variant (FR-S-07, Release 2); how it is made in Release 0 | PENDING GUIDE CONFIRMATION |
| Protected items unchanged after the merge, on Moodle 4.5 and on 5.3 | PENDING MOODLE LAB |
| Sections 4 to 7 added beside the template's sections 1 to 3, which stay unchanged (A1 to A4): the numbers do not overlap | Expected from the owner's numbering rule; PENDING MOODLE LAB (PRD App-C item 2) |
| Course total 200 after the merge (A6) | PENDING MOODLE LAB |
| The target total the checker uses for the merged course (CK-03) | PENDING GUIDE CONFIRMATION (A6) |

## 6. What is verified

| Check | Status |
|---|---|
| Shared validator (`libs/contracts`): schema, unique and non-protected `idnumber`s, body files exist | Passes (test `test_the_shared_validator_accepts_the_package`) |
| Rules the validator lists as not checked: one Page and one Assignment per week, unlock chain, points total, marking tables and check names, weeks numbered 4 to 7 after the template's last section (3) and no collision with the protected section (3, a proposal) | Passes in the dataset test only; the shared rules do not exist yet |
| Each task body explains the submission format (A12) | Passes in the dataset test (`test_task_explains_the_confirmed_submission_format`) |
| `.mbz` built from this package (FR-S-06) | PENDING: Studio, Release 2 |
| Restored on fresh Moodle 4.5 and 5.3 | PENDING MOODLE LAB |
| Checker reports 0 errors (PRD §C1.7, §C2.7) | PENDING: checker, Release 1, and the lab |
| Role tests on the restored course; loading time ≤ 15 minutes | PENDING MOODLE LAB |

## 7. Source and licence

Fictional, original content written for LearnOps. It contains no real learner data, no real course
content and no third-party material (PRD C-07: test data only). The bodies hold no links, a
dataset choice (not a PRD rule) so that no third-party material is pulled in. Licence:
**Apache-2.0**, the same as the repository (PRD C-11, root `LICENSE`); confirmed by the guide on
PR #61. No consent is needed: no real person's work is included. The entry in `testdata/README.md`
points here.

## 8. Run and undo

Run: `python -m pytest libs/contracts/tests/test_b8_2_dataset.py -q`.
Undo: delete `testdata/b8-2-sample-course/`, `libs/contracts/tests/test_b8_2_dataset.py`, the B8.2
section of `testdata/README.md` and the B8.2 section of `docs/traceability.md`. No code or other data
set depends on them yet. B8.4 will retarget to these marking tables (PR #31, open item O1).

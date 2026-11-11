# B8.2 Sample Course

> **Status.** The package is written and passes the shared validator and a dataset test. No `.mbz`
> exists and nothing has been restored on Moodle or run through the checker. Labels: **PRD** =
> stated by the PRD. **Proposal** = put forward for the B8.2 owner where the PRD is silent; not a
> contract value (drafted with Claude Code; pending the owner's review). **PENDING GUIDE
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
  package/weeks/01-guide.md … 04-guide.md   guide Pages
  package/weeks/01-task.md  … 04-task.md    task Assignments, each with one marking table
libs/contracts/tests/test_b8_2_dataset.py   the dataset test
```

## 3. Expected structure (plain list for the checker)

Section numbers 1 to 4 follow the PRD's B1.1 example. Every task: `completion: submit`,
`submission: [onlinetext, file]`, 25 points. Each week after the first unlocks on the previous task.

| Section | idnumber | Guide Page | Task Assignment | Unlocks after | Points |
|---|---|---|---|---|---|
| 1 | `wk-01` | `wk-01-guide` | `wk-01-task` | nothing (open) | 25 |
| 2 | `wk-02` | `wk-02-guide` | `wk-02-task` | `wk-01-task` | 25 |
| 3 | `wk-03` | `wk-03-guide` | `wk-03-task` | `wk-02-task` | 25 |
| 4 | `wk-04` | `wk-04-guide` | `wk-04-task` | `wk-03-task` | 25 |

Total: 4 sections, 8 activities, 100 points (`total_points: 100`, PRD B1.2 rule 3). Marking tables use
only checks from PRD §C3.5: `http_ok:demo_url`, `repo_clone`, `repo_file:TESTS.md`,
`readme_sections:…`, `word_count:…`, and `—` for mentor judgement.

## 4. Assumptions and decisions

| # | Item | Status |
|---|---|---|
| A1 | Weeks are sections 1 to 4 | Follows the PRD's B1.1 example (an example, not a rule) |
| A2 | The protected section is **7**, after the weeks. It is **not** a field of `course.yaml`, and the contract and validator never hard-code it (PRD B1.4: configurable, no default). The dataset test holds it as a named working value | Proposal. PENDING GUIDE CONFIRMATION |
| A3 | B8.1's README (PR #57) still proposes the protected section at 3 and sections 1 and 2 as Orientation and a sample week. That does not match A2 and is **not changed here** | PENDING GUIDE CONFIRMATION |
| A4 | What the B8.1 template holds in sections 1, 2, 5 and 6 (A2 leaves 5 and 6 undefined) | PENDING GUIDE CONFIRMATION |
| A5 | Each weekly task is 25 points, total 100 | Proposal |
| A6 | **Unresolved grading decision.** Whether B8.1's final-project points (100 proposed there, receiving activity not decided) count inside the combined course total. B8.2 alone totals 100; the merged course total, and the target the checker should use (CK-03), are not decided. Nothing here assumes either answer | PENDING GUIDE CONFIRMATION |
| A7 | `full` mode never contains the protected items (PRD B1.4), so a restored B8.2 has no final project, feedback, completion criteria or badge. Whether the checker (CK-07, CK-08) must accept that for "0 errors" is open (Studio design item 25) | PENDING GUIDE CONFIRMATION |
| A8 | Fictional theme, titles and shortname `SAMPLE-DOC-101` | Proposal |
| A9 | No `command:` checks (the PRD reads them from "the course's check config", which B1 does not define) | Proposal |
| A10 | No start dates, no H5P, URL or Label activities (B7 practice is optional) | Proposal |
| A11 | Package in a `package/` subfolder so this README stays outside it | Proposal |

## 5. Protected items in a sections-only merge

The sections-only variant of B8.2 (weeks 1 to 4 only) is merged into a course made from the B8.1
template. After the merge, the final project, course feedback, completion criteria and badge must be
unchanged: same `idnumber`s, same count, criteria intact (PRD §C1.7). The expected list to compare
against is in B8.1's README (open PR #57, not merged yet).

| Item | Status |
|---|---|
| Studio builds the sections-only variant (FR-S-07, Release 2); how it is made in Release 0 | PENDING GUIDE CONFIRMATION |
| Protected items unchanged after the merge, on Moodle 4.5 and on 5.3 | PENDING MOODLE LAB |
| Weeks 1 and 2 beside any template content in sections 1 and 2 (A3, A4): merged or replaced | PENDING MOODLE LAB (PRD App-C item 2) |

## 6. What is verified

| Check | Status |
|---|---|
| Shared validator (`libs/contracts`): schema, unique and non-protected `idnumber`s, body files exist | Passes (test `test_the_shared_validator_accepts_the_package`) |
| Rules the validator lists as not checked: one Page and one Assignment per week, unlock chain, points total, marking tables and check names, no collision with a protected section | Passes in the dataset test only; the shared rules do not exist yet |
| `.mbz` built from this package (FR-S-06) | PENDING: Studio, Release 2 |
| Restored on fresh Moodle 4.5 and 5.3 | PENDING MOODLE LAB |
| Checker reports 0 errors (PRD §C1.7, §C2.7) | PENDING: checker, Release 1, and the lab |
| Role tests on the restored course; loading time ≤ 15 minutes | PENDING MOODLE LAB |

## 7. Source and licence

Written for LearnOps as fictional test content. It contains no real learner data, no real course
content and no third-party material (PRD C-07: test data only). The bodies hold no links, a
dataset choice (not a PRD rule) so that no third-party material is pulled in. It was drafted with
Claude Code and still needs the B8.2 owner's review. Licence of the content: PENDING
GUIDE CONFIRMATION. The entry in `testdata/README.md` points here.

## 8. Run and undo

Run: `python -m pytest libs/contracts/tests/test_b8_2_dataset.py -q`.
Undo: delete `testdata/b8-2-sample-course/`, `libs/contracts/tests/test_b8_2_dataset.py`, the B8.2
section of `testdata/README.md` and the B8.2 section of `docs/traceability.md`. No code or other data
set depends on them yet. B8.4 will retarget to these marking tables (PR #31, open item O1).

# B4 Moodle web-services usage (v1)

**Status:** Draft. Not verified on any Moodle site. Not approved.
**Owner:** Student 3. **Used by:** Module 2 (course checker) and Module 3 (grading) (PRD §B.0).
**Source:** PRD §B4, App-C item 1, SEC-03, C-06. Where this file and the PRD differ, the PRD wins.

This file says which Moodle web-services functions LearnOps may call, with which account, and what
still has to be checked on the lab sites. Nothing in it is verified yet: every "verified" cell below
stays "no" until the check on Moodle 4.5 and 5.3 is recorded in `docs/decisions/`.

Frozen at the end of Release 0 (PRD §B.0 rule 2). After that it changes only through
`/contract-change`.

## 1. Service account and token

From PRD §B4:
- One dedicated **service account per Moodle site**.
- Its token is restricted to an **external service that contains only the functions in §2**.
- The account has only the capabilities those functions need, in the courses where it is enrolled
  for grading.

From PRD SEC-03 and C-06:
- The token is stored only in the environment, never in the repository, logs or error messages.
- One token variable per site: `MOODLE45_WS_TOKEN` and `MOODLE53_WS_TOKEN` (guide's decision on
  Q24, PR #27). `.env.example` lists both with placeholders only. The old single `MOODLE_WS_TOKEN`
  is removed.

## 2. Functions

Only these functions may be called. A replacement is recorded here if a name differs on a Moodle
version (PRD §B4).

| Purpose | Function (PRD §B4) | Used by | Parameters used | Verified on 4.5 | Verified on 5.3 |
|---|---|---|---|---|---|
| Course structure | `core_course_get_courses_by_field` | M2 course lookup; M3 FR-G-01 | To verify in the lab | no | no |
| Course structure | `core_course_get_contents` | M2 course structure; M3 FR-G-01 | To verify in the lab | no | no |
| Enrolled users | `core_enrol_get_enrolled_users` | M3 FR-G-01 | To verify in the lab | no | no |
| Assignments | `mod_assign_get_assignments` | M3 FR-G-01 | To verify in the lab | no | no |
| Submissions | `mod_assign_get_submissions` | M3 FR-G-01, FR-G-08 | To verify in the lab | no | no |
| Submissions | `mod_assign_get_submission_status` | M3 FR-G-01, FR-G-08 | To verify in the lab | no | no |
| Submission files | Download through the token-authenticated file URL returned by the API | M3 FR-G-01 | How the download authenticates: to verify in the lab | no | no |
| Write draft grade and feedback | `mod_assign_save_grade` | M3 FR-G-06 | Workflow state `readyforrelease` (PRD App-C 1 names the parameter `workflowstate`); feedback comments. All other parameters: to verify in the lab | no | no |
| Workflow state | `mod_assign_set_user_flags`, only if needed to set the state | M3 FR-G-06 | To verify in the lab | no | no |

"Used by" for Module 2 comes from `docs/design/checker.md` §4; for Module 3 from
`docs/design/grading.md` §4.1. Both design documents are drafts.

No parameter name, field name or response shape is listed here unless the PRD names it. The others
are added only after they are checked on both lab sites.

**Gap in the PRD:** PRD §B4 says `mod_assign_save_grade` is called with "feedback comments" but
names no parameter for them. No name is guessed; it is added after lab check 1.

## 2a. Machine-readable allow-list

Guide's decision on Q1 (PR #27): this Markdown file stays the normative rules text, and a small
schema plus one example list the allowed functions in machine-readable form.

| File | Content |
|---|---|
| `contracts/moodle-ws.v1.schema.json` | Shape of the allow-list |
| `contracts/examples/moodle-ws.v1.functions.json` | The functions of §2, each with the parameters LearnOps sends and, only where a name differs on a Moodle version, the replacement name |

Rules for the allow-list:
- It holds **no verification state**. Lab results go to `docs/decisions/`, and the "Verified"
  columns in §2 above stay "no" until those records exist. The schema refuses any field whose name
  contains "verif".
- Its function names equal the PRD §B4 list and the §2 table; a test checks both.
- `parameters` lists only names the PRD gives. An empty list means **not yet determined** (lab
  check 1), not "no parameters".
- If a name differs on a Moodle version, the replacement goes into `replacements` **and** the PRD
  §B4 text changes in the same pull request (guide, PR #27). None is recorded yet.
- The file download in §2 is not a web-services function, so it is not in the allow-list.
- `libs/moodle_ws` (not written yet) builds its allow-list from this example and must refuse any
  other function, so the contract and the code cannot drift apart.

## 3. Draft rule

Grades written by LearnOps stay invisible to learners until the mentor releases them in Moodle
(marking workflow). Only mentor-approved drafts are written (PRD §B4, C-09).

- A grade write sends the workflow state **`readyforrelease`** and never **`released`**.
- LearnOps never releases grades.

## 4. Capabilities

The PRD gives no list. The minimum capabilities for exactly the functions in §2 are to be determined
on the lab sites and recorded here (lab check 9 below). SEC-03 then refers to this list.

## 5. Lab verification checklist

Each item is checked on Moodle 4.5 **and** 5.3. The result goes into a decision record in
`docs/decisions/` and then into this file. Until an item is recorded, code that depends on it uses
fakes only.

Item 1 is PRD App-C item 1. Items 2 to 10 come from `docs/design/grading.md` §4.1 (a draft).

| # | Check | 4.5 | 5.3 | Decision record |
|---|---|---|---|---|
| 1 | Every function in §2 exists with the parameters used, including how the workflow state and feedback comments are passed to `mod_assign_save_grade` | open | open | — |
| 2 | What the assignment functions return: description text, `idnumber`, grading type and maximum grade, marking-workflow setting. Where one is missing, the replacement function is added to §2 | open | open | — |
| 3 | What identifies a submission attempt and its last change | open | open | — |
| 4 | Behaviour when the workflow state is sent for an assignment where marking workflow is off | open | open | — |
| 5 | Behaviour when saving over a grade that is already released, or that another grader entered | open | open | — |
| 6 | Whether feedback comments are enabled on assignments built by Course Studio, and which format Moodle stores | open | open | — |
| 7 | Whether the marking-table markers survive Moodle's HTML handling, and how online text arrives | open | open | — |
| 8 | How suspended users, group submissions, and draft versus submitted statuses appear in the submission functions | open | open | — |
| 9 | Which capabilities the service account minimally needs for exactly the functions in §2 | open | open | — |
| 10 | How the file download authenticates | open | open | — |

## 6. Open questions

Not decided. This file does not settle it.

| Question | Who decides |
|---|---|
| **Lab access.** When the Moodle 4.5 and 5.3 lab sites are available. All checks in §5 wait for them. B4 can be merged as a draft before that, but it cannot be frozen at the end of Release 0 until the checks pass (guide, PR #27) | Guide |

**Decided by the guide (PR #27, 2026-10-29):**
- **Q1:** Markdown for the rules plus a small JSON Schema and one example listing the allowed
  functions (§2a). No verified flags in them.
- **Q24:** `MOODLE45_WS_TOKEN` and `MOODLE53_WS_TOKEN`; `MOODLE_WS_TOKEN` removed (§1).
- **Q37:** what `libs/moodle_ws` returns (normalized models), how it enforces the allow-list, and
  its error classes are **not contract text**. They are documented in `docs/design/grading.md`
  §4.1 and, later, in the library's documentation.

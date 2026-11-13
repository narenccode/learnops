# B4 Moodle web-services usage (v1)

**Status:** Draft. Not verified on any Moodle site. Not approved.
**Owner:** Student 3. **Used by:** Module 2 (course checker) and Module 3 (grading) (PRD §B.0).
**Source:** PRD §B4, App-C item 1, SEC-03, C-06, the guide's B4 findings (§4, §7) and the guide's
decisions on PR #64 (§3a). Where this file and the PRD differ, the PRD wins.

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
| Course structure | `core_course_get_courses_by_field` | M2 course lookup; M3 FR-G-01 | `field`, `value` (by course id; shortname as the alternative; never idnumber, §2b) | no | no |
| Course structure | `core_course_get_contents` | M2 course structure; M3 FR-G-01 | To verify in the lab | no | no |
| Enrolled users | `core_enrol_get_enrolled_users` | M3 FR-G-01 | To verify in the lab | no | no |
| Assignments | `mod_assign_get_assignments` | M3 FR-G-01 | To verify in the lab | no | no |
| Submissions | `mod_assign_get_submissions` | M3 FR-G-01, FR-G-08 | To verify in the lab | no | no |
| Submissions | `mod_assign_get_submission_status` | M3 FR-G-01, FR-G-08; read-back after a grade write (§3) | `assignid`, `userid` | no | no |
| Submission files | Download through the token-authenticated file URL returned by the API | M3 FR-G-01 | How the download authenticates: to verify in the lab | no | no |
| Write draft grade and feedback | `mod_assign_save_grade` | M3 FR-G-06 | Always sent: `assignmentid`, `userid`, `grade`, `attemptnumber` (explicit, never `-1`), `addattempt`, `workflowstate` (always `readyforrelease`), `applytoall`. Optional: `plugindata`, `advancedgradingdata` | no | no |
| Stored-grade read-back | `mod_assign_get_grades` | M3 FR-G-06; grade-value read-back after a grade write (§3) | `assignmentids` (the one assignment written; `since` is not sent) | no | no |

"Used by" for Module 2 comes from `docs/design/checker.md` §4; for Module 3 from
`docs/design/grading.md` §4.1. Both design documents are drafts.

No parameter name, field name or response shape is listed here unless the PRD names it. The names
above come from the Moodle 4.5 and 5.3 source (§7) and are in the PRD §B4 parameter table. They are
**not** verified on a lab site: how Moodle behaves with them is still lab check 1. Functions with
"To verify in the lab" have no parameters recorded yet.

`mod_assign_set_user_flags` is **not** allowed (guide's B4 findings). LearnOps sets the workflow state
only through `mod_assign_save_grade`.

**Feedback comments:** PRD §B4 says `mod_assign_save_grade` is called with "feedback comments". In the
Moodle source they travel inside `plugindata`; the exact field inside it is not recorded yet (lab
check 6).

**Always sent and optional:** "Always sent" parameters are sent on every call; "Optional" ones only
when needed. "Always sent" is LearnOps's rule, not Moodle's, and the two differ:

| Parameter | Moodle requires it? | LearnOps |
|---|---|---|
| The seven always-sent `mod_assign_save_grade` parameters | Yes (no default) | Always sent |
| `plugindata`, `advancedgradingdata` | No (default: empty) | Optional |
| `assignid` on `mod_assign_get_submission_status` | Yes | Always sent |
| `assignmentids` on `mod_assign_get_grades` | Yes | Always sent, with exactly one assignment id |
| `userid` on `mod_assign_get_submission_status` | No (default 0, meaning the caller) | Always sent: without it, Moodle reports the service account's own status |
| `field`, `value` on `core_course_get_courses_by_field` | No (default: empty, meaning all courses) | Always sent, so that one course is looked up (§2b) |

### 2b. Course identification

A course is identified by its Moodle course id (`field` = `id`). Its shortname (`field` =
`shortname`) is the accepted alternative. LearnOps **never** uses a course's idnumber:
`core_course_get_courses_by_field` returns `idnumber` only to accounts with `moodle/course:update`
(§7), which the service account must not have (§4).

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
- `parameters` lists the **always-sent** parameters and `optional_parameters` the **optional** ones,
  only with names the PRD gives for that function. An empty or missing list means **not yet
  determined** (lab check 1), not "no parameters". A name may not be in both lists.
- If a name differs on a Moodle version, the replacement goes into `replacements` **and** the PRD
  §B4 text changes in the same pull request (guide, PR #27). None is recorded yet.
- The file download in §2 is not a web-services function, so it is not in the allow-list.
- `libs/moodle_ws` (not written yet) builds its allow-list from this example and must refuse any
  other function, so the contract and the code cannot drift apart.

## 3. Draft rule

Grades written by LearnOps stay invisible to learners until the mentor releases them in Moodle
(marking workflow). Only mentor-approved drafts are written (PRD §B4, C-09).

- A grade write sends the workflow state **`readyforrelease`** and never **`released`**. Every
  other state is refused **before** anything is sent; LearnOps does not rely on Moodle's
  permissions to enforce this.
- **Read-back:** after a successful `mod_assign_save_grade`, LearnOps reads the result back. The
  write counts as done **only** if **both** are confirmed:
  1. **State:** in `mod_assign_get_submission_status` for the same `assignid` and `userid`,
     `lastattempt.gradingstatus` is exactly `readyforrelease`.
  2. **Grade value:** the stored grade for that learner and attempt is numerically equal to the
     grade that was sent, read with `mod_assign_get_grades` (rule R1).

  If either is different, missing, ambiguous or cannot be read, the write is reported as **not
  verified**, never as done. The workflow state alone is never enough.
- The grade value cannot come from `mod_assign_get_submission_status`: before release, Moodle leaves
  `feedback.grade` out of that answer (§7).
- With marking workflow on, `lastattempt.gradingstatus` is the learner's workflow state; with it off,
  it is `graded` or `notgraded` (§7), so the read-back also fails when marking workflow is off.
- LearnOps never releases grades.

### 3a. Write rules (guide's decisions on PR #64, 2026-11-12)

The guide decided the eleven open questions on PR #64. Each is a rule of this contract. Where the
guide read a fact from the Moodle code but could not run it, the rule says so and a lab check in §5
stays open. The outcome names (`NOT_VERIFIED` and the others in R10) are the words this contract
uses; the library's class and code names are not contract text (guide on Q37, PR #27).

| Rule | Decision |
|---|---|
| R1 | **Stored-grade read-back.** `mod_assign_get_grades` is the grade-value read-back (§3 condition 2). It is in §2 and the allow-list. It needs `mod/assign:viewgrades` or `mod/assign:grade` (already in §4) and its code is the same on 4.5 and 5.3. It returns the grade as text, for example `84.50000`; the number of decimals depends on the database and is not verified (lab check 13). The matching rule is §3b |
| R2 | **Explicit attempt.** `attemptnumber` is always the explicit attempt being graded, never `-1` ("latest"). The read-back matches that same attempt |
| R3 | **Locked states.** Before writing, LearnOps reads the learner's state; if it is already `readyforrelease` or `released`, the write is **refused** and nothing is sent. The read-back after the write is still required, because the state can change between the check and the write. On 5.3 a locked submission keeps its old grade value while the call looks successful; on 4.5 the code overwrites the grade without a lock (read from the code, not run: lab check 16) |
| R4 | **Declared capabilities stay out.** `moodle/course:viewhiddencourses`, `moodle/user:viewhiddendetails` and `moodle/course:useremail` are not granted (§4): they cover only hidden courses, hidden profile fields and the email field. That the calls work without them is lab check 14 |
| R5 | **Suspended learners.** A suspended learner is skipped and reported as **skipped**, separately from the other outcomes. `moodle/course:viewsuspendedusers` is not granted |
| R6 | **`mod/assign:viewownsubmissionsummary`.** The student role has it by default on both versions, and Moodle checks it for the learner when filling `lastattempt`. A course can change it, so it stays lab check 12. Without it the state cannot be read, and the write is not verified (§3) |
| R7 | **`mod/assign:reviewgrades` on both versions,** with one role definition (§4). It allows only `inreview` and `readyforrelease`, not `released`. On 4.5 Moodle does not check it, so LearnOps's own state guard (§3) is what protects there |
| R8 | **Read-back failure.** If the read-back fails (timeout, error, answer that cannot be understood), the write is reported as `NOT_VERIFIED`. The write is **never repeated**. Retrying the read-back is a separate operation that sends no write |
| R9 | **Exact numeric match and range.** Both the grade sent and the grade read back are parsed as numbers and must be **exactly equal**; there is no tolerance and no rounding. Moodle stores five decimals, so `84.5` is stored as `84.5`. **Before writing**, the grade must be a number from 0 to the assignment's maximum grade; otherwise the write is refused and nothing is sent. Moodle silently ignores a grade above the maximum or below zero, with no error (lab check 15), so the read-back is the only proof |
| R10 | **Separate outcomes.** A learner with no submission, a submission with no grade, and a submission LearnOps cannot access are **separate** outcomes (`NO_SUBMISSION`, `NO_GRADE`, `ACCESS_DENIED`), next to `SKIPPED_SUSPENDED` (R5) and `NOT_VERIFIED` (R8). None is ever reported as success. Processing continues for the other learners |
| R11 | **Uncertain write.** If LearnOps cannot tell whether Moodle processed a write (for example a timeout), it does **not** retry the write automatically. It reads back first, reports the result, and **the mentor decides** what happens next |

Lesson recorded by the guide: when the platform can ignore a write without an error, the only proof
is a read-back that is compared with what was sent.

### 3b. Grade-value matching rule (R1, R2, R9)

After a successful `mod_assign_save_grade`, LearnOps calls `mod_assign_get_grades` with
`assignmentids` = the one `assignmentid` it sent (`since` is not sent). Condition 2 in §3 holds only
if **all** of these are true; anything else is not verified:

1. `assignments[]` has exactly one entry whose `assignmentid` is the one sent.
2. `warnings[]` has no entry for that assignment.
3. That entry's `grades[]` has exactly one row whose `userid` is the one sent (0 rows or more than
   one row: not verified).
4. That row's `attemptnumber` equals the explicit `attemptnumber` sent (R2).
5. That row's `grade` parses as a number, is not negative, and is exactly numerically equal to the
   grade sent (R9). It is compared as a number, never as text.

This catches the 5.3 case in §7 where the stored state is already `readyforrelease`: Moodle keeps
the old value, so check 5 fails.

## 4. Capabilities

Minimum capabilities, as given by the guide (B4 findings). **Not yet confirmed on a lab site** (lab
check 9). SEC-03 refers to this list.

The service account needs a **custom role**. The built-in non-editing teacher role is **not** used.

| Needed | Why |
|---|---|
| Enrolment in each course it grades | Course-level access; an administrator enrols it (README step) |
| `moodle/course:viewparticipants` | Enrolled users |
| `moodle/user:viewdetails` | Enrolled users |
| `mod/assign:view` | Assignments and submissions |
| `mod/assign:viewgrades` | Submissions and the read-back in §3 |
| `mod/assign:grade` | Writing a draft grade |
| `mod/assign:reviewgrades` | Writing the state `readyforrelease`. Granted on **both** 4.5 and 5.3, with one role definition (R7). Moodle checks it only on 5.3 |

The account must **never** have:

| Capability | Why not |
|---|---|
| `moodle/user:update` | Not needed |
| `moodle/course:update` | Not needed; it would also expose course idnumbers (§2b) |
| `mod/assign:managegrades` | Not needed |
| `mod/assign:releasegrades` | LearnOps never releases grades (§3) |

Moodle declares `moodle/course:update` for `core_course_get_contents` and `moodle/user:update` for
`core_enrol_get_enrolled_users` (§7), but LearnOps does not need them for the parameters and fields it
uses, so they are not granted.

Also declared by Moodle but **not granted** (guide's decisions R4 and R5):

| Not granted | Declared for | Why not |
|---|---|---|
| `moodle/course:viewhiddencourses` | `core_course_get_contents` | Only for hidden courses (R4) |
| `moodle/user:viewhiddendetails` | `core_enrol_get_enrolled_users` | Only for hidden profile fields (R4) |
| `moodle/course:useremail` | `core_enrol_get_enrolled_users` | Only for the email field (R4) |
| `moodle/course:viewsuspendedusers` | — | Suspended learners are skipped and reported as skipped instead (R5) |

That the calls work without the first three is lab check 14 (5.3). How suspended learners'
submissions appear without `moodle/course:viewsuspendedusers` is lab check 11; neither has been
tested.

## 5. Lab verification checklist

Each item is checked on Moodle 4.5 **and** 5.3. The result goes into a decision record in
`docs/decisions/` and then into this file. Until an item is recorded, code that depends on it uses
fakes only.

Item 1 is PRD App-C item 1. Items 2 to 10 come from `docs/design/grading.md` §4.1 (a draft).
Items 11 and 12 come from the guide's B4 findings and the Moodle source (§7). Items 13 to 16 come
from the guide's decisions in §3a, where the guide read the Moodle code but could not run it. Every
item here is a **live lab** check: reading the source (§7) never closes one.

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
| 9 | The capability list in §4 is enough for exactly the functions in §2, and nothing more is needed | open | open | — |
| 10 | How the file download authenticates | open | open | — |
| 11 | How submissions of suspended learners appear without `moodle/course:viewsuspendedusers` | open | open | — |
| 12 | The read-back in §3 returns `lastattempt.gradingstatus` = `readyforrelease` after a write. Moodle returns `lastattempt` only when the learner holds `mod/assign:viewownsubmissionsummary` (§7); the student role has it by default, but a course can change it (R6) | open | open | — |
| 13 | `mod_assign_get_grades` returns the stored, unreleased grade and the attempt number written, and the §3b matching rule holds; record the text format of `grade` (number of decimals) on each database (R1, R9) | open | open | — |
| 14 | `core_course_get_contents` and `core_enrol_get_enrolled_users` work for the service account without `moodle/course:viewhiddencourses`, `moodle/user:viewhiddendetails` and `moodle/course:useremail` (R4; the guide asked for this on 5.3) | open | open | — |
| 15 | A grade below zero or above the maximum is silently ignored by `mod_assign_save_grade` with no error, and the read-back shows it (R9) | open | open | — |
| 16 | Writing over a submission already in `readyforrelease`: 5.3 keeps the old grade while the call looks successful; 4.5 overwrites it (R3) | open | open | — |

## 6. Open questions

Not decided. This file does not settle it.

| Question | Who decides |
|---|---|
| **Pre-write state unreadable.** R3 refuses a write when the state is already `readyforrelease` or `released`. The decisions do not say what happens when the state cannot be read before the write (for example `lastattempt` missing, R6), or is a value Moodle's source does not list. **Proposed, fail closed:** LearnOps does not write in that case, because it cannot show the submission is not locked | Guide |
| **Marking workflow off.** With marking workflow off, `lastattempt.gradingstatus` is `graded` or `notgraded` (§7), and a saved grade can reach the gradebook, and the learner, at once. That breaks the PRD B4 draft rule, but no rule here refuses the write beforehand; the read-back only reports it afterwards (§3). **Proposed, fail closed:** before writing, LearnOps writes only over `notmarked`, `inmarking`, `readyforreview` or `inreview` (the marking-workflow states in the source, §7), and refuses `graded` and `notgraded`. Lab check 4 confirms the behaviour | Guide |
| **Lost answer, matching read-back.** R11 says the mentor decides after an uncertain write. If the read-back then matches exactly, may the write count as done, or must the mentor still confirm it? **Proposed, fail closed:** it is not counted as done until the mentor confirms it | Guide |
| **Grading design §10.1.** `docs/design/grading.md` §10.1 (Release 4, draft) still says an unknown outcome may "write again under the same idempotency key", which conflicts with R11. Follow-up for the grading design; not changed here | Student 3, guide |
| **Lab access.** When the Moodle 4.5 and 5.3 lab sites are available. All checks in §5 wait for them. B4 can be merged as a draft before that, but it cannot be frozen at the end of Release 0 until the checks pass (guide, PR #27) | Guide |

**Decided by the guide (PR #27, 2026-10-29):**
- **Q1:** Markdown for the rules plus a small JSON Schema and one example listing the allowed
  functions (§2a). No verified flags in them.
- **Q24:** `MOODLE45_WS_TOKEN` and `MOODLE53_WS_TOKEN`; `MOODLE_WS_TOKEN` removed (§1).
- **Q37:** what `libs/moodle_ws` returns (normalized models), how it enforces the allow-list, and
  its error classes are **not contract text**. They are documented in `docs/design/grading.md`
  §4.1 and, later, in the library's documentation.

**Decided by the guide (PR #64, 2026-11-12):** the eleven questions on the B4 findings, recorded
as rules R1 to R11 in §3a, with the grade-value matching rule in §3b.

### 6a. `mod_assign_get_grades`: source facts (decided, R1)

The guide approved `mod_assign_get_grades` as the stored-grade read-back (R1). These facts were
read from the source (same commits as §7; the function is identical on 4.5 and 5.3). They are not
a lab check: lab check 13 stays open until it is run.

| Fact | Where |
|---|---|
| `get_grades_parameters`: `assignmentids` (list of ids, required) and `since` (default 0) | `mod/assign/externallib.php` |
| It reads `{assign_grades}` directly (not the gradebook), so an **unreleased** grade is included | same file, `get_grades` |
| It returns only the grade row for the learner's **latest** submission: `s.latest = 1 AND s.attemptnumber = ag.attemptnumber` | same file, `get_grades` |
| Answer: `assignments[]` with `assignmentid` and `grades[]` (`userid`, `attemptnumber`, `grade` as `PARAM_TEXT`, and more), plus `warnings[]` (code 1: no permission; code 3: no grades) | same file, `get_grades_returns`, `get_grade_structure` |
| Access: `require_view_grades()`, i.e. `mod/assign:viewgrades` or `mod/assign:grade` (already in §4); `type` is `read` | same file; `mod/assign/locallib.php`; `mod/assign/db/services.php` |

## 7. Source evidence (Moodle code, not a lab check)

Read from the official `moodle/moodle` repository, `MOODLE_405_STABLE` at `c0690bbc765f` and
`MOODLE_503_STABLE` at `236a9d702e62` (on 5.3 the files are under `public/`). Reading the source
shows what Moodle declares; it does not replace the lab checks in §5.

| Fact | Where (same file on both versions) |
|---|---|
| `get_submission_status_parameters`: `assignid` (required), `userid` and `groupid` (default 0) | `mod/assign/externallib.php` |
| The response field `lastattempt.gradingstatus` (`PARAM_ALPHANUMEXT`); `lastattempt` itself is optional | `mod/assign/externallib.php`, `get_submission_status_returns` |
| `lastattempt` is filled only if the learner has `mod/assign:viewownsubmissionsummary`; a caller that fails `can_view_submission` gets a missing `mod/assign:viewgrades` error | `mod/assign/externallib.php`, `get_submission_status` |
| `gradingstatus` comes from `get_grading_status()`: the user flag `workflowstate` when marking workflow is on (`notmarked` if empty), otherwise `graded` / `notgraded` | `mod/assign/locallib.php` |
| `ASSIGN_MARKING_WORKFLOW_STATE_READYFORRELEASE` is `'readyforrelease'` | `mod/assign/locallib.php` |
| `save_grade_parameters`: the seven required parameters in §2; `plugindata` and `advancedgradingdata` default to empty | `mod/assign/externallib.php` |
| `get_courses_by_field_parameters`: `field` (`id`, `ids`, `shortname`, `idnumber`, `category`, `sectionid`) and `value` | `course/externallib.php` |
| `idnumber` is among the fields added only when the caller has `moodle/course:update` | `course/externallib.php`, `get_courses_by_field` |
| `readyforrelease` is offered only to callers with `mod/assign:reviewgrades` or `mod/assign:managegrades` | `mod/assign/locallib.php`, `get_marking_workflow_states_for_current_user` |
| **4.5:** when grading is not disabled, `apply_grade_to_user` stores the requested workflow state without checking that list. **5.3:** it checks the list, and **a state the caller may not set is silently ignored**, leaving the stored state unchanged. This is why 5.3 needs `mod/assign:reviewgrades`, and why the read-back in §3 is required | `mod/assign/locallib.php`, `apply_grade_to_user` |
| `core_course_get_contents` declares `moodle/course:update`; `core_enrol_get_enrolled_users` declares `moodle/user:update` | `lib/db/services.php` |
| `feedback` in `mod_assign_get_submission_status` is filled only when the **gradebook** has a grade (`$hasgrade` reads `$gradebookgrade->grade`) | `mod/assign/locallib.php`, `get_assign_feedback_status_renderable` |
| With marking workflow on, an unreleased grade is removed from the gradebook ("remove any grade that may exist in the gradebook", `$grade->grade = -1`), so `feedback.grade` is absent before release and cannot confirm the grade value | `mod/assign/locallib.php`, `gradebook_item_update` |

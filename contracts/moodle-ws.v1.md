# B4 Moodle web-services usage (v1)

**Status:** Draft. Lab checks run on Moodle 5.3 and accepted by the guide (decision 0019). Moodle 4.5 is out of scope (decision 0017). Not approved.
**Owner:** Student 3. **Used by:** Module 2 (course checker) and Module 3 (grading) (PRD §B.0).
**Source:** PRD §B4, App-C item 1, SEC-03, C-06, the guide's B4 findings (§4, §7) and the guide's
decisions on PR #64 (§3a). Where this file and the PRD differ, the PRD wins.

This file says which Moodle web-services functions LearnOps may call, with which account, and what
was checked on the lab site. The lab checks were run on Moodle 5.3 on 25 November 2026 and the guide
accepted the run on 26 November 2026 (`docs/decisions/0019-b4-lab-results-moodle-5-3.md`, section 5).
A "yes" below means the function answered on 5.3 in that run. Moodle 4.5 is out of scope
(decision 0017).

Freezes on its own, when this change merges (decision 0018, PRD D1); it is not frozen with the other
contracts at the end of Release 0. After that it changes only through `/contract-change` (PRD §B.0
rule 2).

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
| Course structure | `core_course_get_courses_by_field` | M2 course lookup; M3 FR-G-01 | `field`, `value` (by course id; shortname as the alternative; never idnumber, §2b) | out of scope (0017) | yes (0019) |
| Course structure | `core_course_get_contents` | M2 course structure; M3 FR-G-01 | No parameters recorded; the call answered on 5.3 (0019, check 1) | out of scope (0017) | yes (0019) |
| Enrolled users | `core_enrol_get_enrolled_users` | M3 FR-G-01 | No parameters recorded; the call answered on 5.3 (0019, check 1) | out of scope (0017) | yes (0019) |
| Assignments | `mod_assign_get_assignments` | M3 FR-G-01 | No parameters recorded; the call answered on 5.3 (0019, check 1) | out of scope (0017) | yes (0019) |
| Submissions | `mod_assign_get_submissions` | M3 FR-G-01, FR-G-08 | No parameters recorded; the call answered on 5.3 (0019, check 1) | out of scope (0017) | yes (0019) |
| Submissions | `mod_assign_get_submission_status` | M3 FR-G-01, FR-G-08; read-back after a grade write (§3) | `assignid`, `userid` | out of scope (0017) | yes (0019) |
| Submission files | Download through the token-authenticated file URL returned by the API | M3 FR-G-01 | The token in the site's own file address (0019, check 10) | out of scope (0017) | yes (0019) |
| Write draft grade and feedback | `mod_assign_save_grade` | M3 FR-G-06 | Always sent: `assignmentid`, `userid`, `grade`, `attemptnumber` (explicit, never `-1`), `addattempt`, `workflowstate` (always `readyforrelease`), `applytoall`. Optional: `plugindata`, `advancedgradingdata` | out of scope (0017) | yes (0019) |
| Stored-grade read-back | `mod_assign_get_grades` | M3 FR-G-06; grade-value read-back after a grade write (§3) | `assignmentids` (the one assignment written; `since` is not sent) | out of scope (0017) | yes (0019) |

"Used by" for Module 2 comes from `docs/design/checker.md` §4; for Module 3 from
`docs/design/grading.md` §4.1. Both design documents are drafts.

No parameter name, field name or response shape is listed here unless the PRD names it. The names
above come from the Moodle 4.5 and 5.3 source (§7) and are in the PRD §B4 parameter table. On 5.3
the site's own documentation listed the seven required `mod_assign_save_grade` parameters and the
six read functions answered with the parameters LearnOps sends (decision 0019, check 1). Functions
marked "No parameters recorded" have none listed here, because the PRD names none for them.

**What the assignment functions return (check 2, 5.3).** `mod_assign_get_assignments` returns `intro`
(HTML, with `introformat`), `grade` (the maximum grade; a positive value means points), `markingworkflow`
(0 or 1), `cmid` and `coursemodule`, `teamsubmission` and `configs`. It returns **no `idnumber`**, and
`core_course_get_contents` returns no activity or section `idnumber` to the service account (checks 17
and 18). So Module 3 identifies an assignment by its course-module id (`cmid`) with a stored mapping to
the B1 `idnumber`. No function is added and no capability is widened (guide, issue #186, 25 Nov 2026,
[comment](https://github.com/narenccode/learnops/issues/186#issuecomment-7157135474), item 2). Where
the mapping comes from and who fills it is for the grading design, not this contract.

`mod_assign_set_user_flags` is **not** allowed (guide's B4 findings). LearnOps sets the workflow state
only through `mod_assign_save_grade`.

**Feedback comments:** PRD §B4 says `mod_assign_save_grade` is called with "feedback comments". In the
Moodle source they travel inside `plugindata`. On 5.3 the field is
`plugindata[assignfeedbackcomments_editor]`, with `text` and `format` (1 = HTML) inside it (decision
0019, check 1). A comment sent that way was stored and shown by the editor as HTML (check 6).

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
- `parameters` is **informative**: it records what LearnOps sends. It is not a parameter allow-list,
  and a client is not required to enforce it. Only the function name is allowed or refused.
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
- `libs/moodle_ws` builds its allow-list from this example and must refuse any
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
| R3 | **Locked states.** Before writing, LearnOps reads the learner's state; if it is already `readyforrelease` or `released`, the write is **refused** and nothing is sent. The read-back after the write is still required, because the state can change between the check and the write. On 5.3 a locked submission keeps its old grade value while the call looks successful; on 4.5 the code overwrites the grade without a lock (read from the code, not run: lab check 16). **R3's pre-write check holds on 5.3; its post-write clause does not catch a write over a `released` grade, because that write ends `readyforrelease` (lab check 5, decision 0019); R16 is the safeguard (guide, #112, 26 Nov, point 3). On 4.5 it is best effort:** a grade can become locked between the check and the write, and no allowed function makes the two steps atomic, so the release notes name this limitation (guide, 15 Nov, PR #80). **After the write,** a state that ends `released` is `NOT_VERIFIED` (R8), with no new outcome name; a normal `readyforrelease` write stays verified (guide, PR #80, confirmed on PR #150, 22 Nov) |
| R4 | **Declared capabilities stay out.** `moodle/course:viewhiddencourses`, `moodle/user:viewhiddendetails` and `moodle/course:useremail` are not granted (§4): they cover only hidden courses, hidden profile fields and the email field. That the calls work without them is lab check 14 |
| R5 | **Suspended learners.** A suspended learner is skipped and reported as **skipped**, separately from the other outcomes. `moodle/course:viewsuspendedusers` is not granted |
| R6 | **`mod/assign:viewownsubmissionsummary`.** The student role has it by default on both versions, and Moodle checks it for the learner when filling `lastattempt`. A course can change it, so it stays lab check 12. Without it the state cannot be read, and the write is not verified (§3) |
| R7 | **`mod/assign:reviewgrades` on both versions,** with one role definition (§4). It allows only `inreview` and `readyforrelease`, not `released`. On 4.5 Moodle does not check it, so LearnOps's own state guard (§3) is what protects there |
| R8 | **Read-back failure.** If the read-back fails (timeout, error, answer that cannot be understood), the write is reported as `NOT_VERIFIED`. The write is **never repeated**. Retrying the read-back is a separate operation that sends no write |
| R9 | **Exact numeric match and range.** Both the grade sent and the grade read back are parsed as numbers and must be **exactly equal**; there is no tolerance and no rounding. Moodle stores five decimals, so `84.5` is stored as `84.5`. **Before writing**, the grade must be a number from 0 to the assignment's maximum grade; otherwise the write is refused and nothing is sent. Moodle silently ignores a grade above the maximum or below zero, with no error (lab check 15), so the read-back is the only proof |
| R10 | **Separate outcomes.** A learner with no submission, a submission with no grade, and a submission LearnOps cannot access are **separate** outcomes (`NO_SUBMISSION`, `NO_GRADE`, `ACCESS_DENIED`), next to `SKIPPED_SUSPENDED` (R5) and `NOT_VERIFIED` (R8). None is ever reported as success. Processing continues for the other learners |
| R11 | **Uncertain write.** If LearnOps cannot tell whether Moodle processed a write (for example a timeout), it does **not** retry the write automatically. It reads back first, reports the result, and **the mentor decides** what happens next |
| R12 | **State unreadable or unknown before the write** (guide, PR #72, 2026-11-15). If the learner's state cannot be read before the write (for example `lastattempt` is missing, R6), or is none of the six marking-workflow values in Moodle's source (`notmarked`, `inmarking`, `readyforreview`, `inreview`, `readyforrelease`, `released`; the same constants on 4.5 and 5.3 in `mod/assign/locallib.php`) and not a value of R13, the write is **refused before anything is sent**. Outcome `REFUSED_STATE_UNKNOWN` (name proposed in PR #72). This is R3 applied to a state that cannot be read, so a locked submission cannot be missed |
| R13 | **Marking workflow off** (guide, PR #72, 2026-11-15). With marking workflow off the state is `graded` or `notgraded` (§7), and a saved grade can reach the learner at once, which breaks the draft rule (PRD C-09). The write is **refused before anything is sent**: LearnOps writes only over `notmarked`, `inmarking`, `readyforreview` or `inreview`. Outcome `REFUSED_WORKFLOW_OFF` (name proposed in PR #72). Course Studio builds assignments with marking workflow on (PRD §B1.2 rule 4), so this refusal only meets an assignment created by hand. Lab check 4 stays open |
| R14 | **Lost answer, matching read-back** (guide, PR #72, 2026-11-15). After an uncertain write (R11), a read-back that matches exactly is **not counted as done until the mentor confirms it**. Outcome `NEEDS_MENTOR_CONFIRMATION` (name proposed in PR #72). This follows R11, "the mentor decides" |
| R15 | **`applytoall` and `addattempt` are pinned** (guide, PR #64, 2026-11-16). LearnOps always sends `applytoall=0` and `addattempt=0` with `mod_assign_save_grade`, and the client **refuses any other value before anything is sent**, including a missing value or a bool. With `applytoall=1` a grade on a group assignment would be written to every group member, and with `addattempt=1` a new attempt would be opened for the learner, so both change a learner's grade and are not left to the default. What Moodle does with each value is not yet run on a lab site (lab check 1) |
| R16 | **Read before write** (guide, #112, 26 Nov 2026, point 3; the form of "no grade": his answer of 26 Nov, [comment](https://github.com/narenccode/learnops/issues/112#issuecomment-7190567102)). Before writing, LearnOps reads `mod_assign_get_grades` for the one assignment and **refuses the write before anything is sent** if the learner has a grade for that attempt. A grade value of **0 or more** means the learner has a grade. **No row, an empty or null value, or a negative value (such as `-1`) means no grade**, and the write goes ahead, so a cleared grade is never refused, whatever form it takes. Outcome `REFUSED_ALREADY_GRADED` (name accepted by the guide, 26 Nov, [comment 7196769553](https://github.com/narenccode/learnops/issues/112#issuecomment-7196769553), item 4). It stops LearnOps overwriting a mentor's own unreleased grade (the half of check 5 that was not run) and narrows the release race, which stays accepted as a known risk on 5.3: a mentor can release between this read and the write. A write that ends `NOT_VERIFIED` tells the mentor to check that learner in Moodle. On 5.3 "no grade" was seen only as `-1.00000` (check 15). **Not tested** (the guide: no lab run is needed before the freeze; a run is welcome as confirmation, recorded in decision 0019): a learner with no grade row, and a grade cleared in Moodle's grading screen |
| R17 | **Feedback comments off** (guide, #112, 26 Nov 2026, point 4). If a feedback comment is to be sent and the assignment has the feedback-comments plugin switched off (readable from `configs` in `mod_assign_get_assignments`, check 6), the write is **refused before anything is sent**: fail closed, because Moodle would not store the comment. Outcome `REFUSED_COMMENTS_OFF` (name accepted by the guide, 26 Nov, [comment 7196769553](https://github.com/narenccode/learnops/issues/112#issuecomment-7196769553), item 4). Feedback comments are on by default on 5.3 (check 6) |
| R18 | **Separate-groups mode** (guide, #112, 26 Nov 2026, point 4). A course in separate-groups mode is **refused with its own outcome**, `REFUSED_GROUP_MODE` (name accepted by the guide, 26 Nov, [comment 7196769553](https://github.com/narenccode/learnops/issues/112#issuecomment-7196769553), item 4), because the service account lacks `moodle/site:accessallgroups` and the 5.3 source returns an empty list with no error for an account in no group, so learners could be missing without a sign. The course's group mode and the participant count in the status answer let the tool detect it. **Not run in the lab** (course 6 is in group mode 0) |

The refusals of R12, R13 and R16 to R18 are each their own outcome, separate from `NOT_VERIFIED` (R8,
which is after a write) and never reported as success (R10). The outcome names of R16 to R18 were
accepted by the guide on 26 Nov 2026 ([comment 7196769553](https://github.com/narenccode/learnops/issues/112#issuecomment-7196769553), item 4); he approves the PRD text when this change leaves draft.

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
The account also holds a System role with only `webservice/rest:use`; the 5.3 run used it (check 9,
decision 0019). It is not one of the six capabilities in the table below.

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

That the calls work without the first three was shown on 5.3 (lab check 14). Without
`moodle/course:viewsuspendedusers`, `mod_assign_get_submissions` leaves a suspended learner's row out
with no error, and `mod_assign_get_submission_status` is refused (`nopermission`) for that learner and,
in the 5.3 source, for any learner the account cannot view (check 11, decision 0019).

## 5. Lab verification checklist

Each item was run on Moodle 5.3 (25 Nov 2026); Moodle 4.5 is out of scope (decision 0017). The results
are in `docs/decisions/0019-b4-lab-results-moodle-5-3.md`. The guide accepted the run on 26 Nov 2026
([#112 comment](https://github.com/narenccode/learnops/issues/112#issuecomment-7176860581)) and did not
name which checks pass, so the 5.3 column says "run" and the record holds each result.

Item 1 is PRD App-C item 1. Items 2 to 10 come from `docs/design/grading.md` §4.1 (a draft).
Items 11 and 12 come from the guide's B4 findings and the Moodle source (§7). Items 13 to 16 come
from the guide's decisions in §3a, where the guide read the Moodle code but could not run it. Item 17
comes from the guide's answer of 15 Nov on PR #72 about the fields `core_course_get_contents` returns. Every
item here is a **live lab** check: reading the source (§7) never closes one.

| # | Check | 4.5 | 5.3 | Decision record |
|---|---|---|---|---|
| 1 | Every function in §2 exists with the parameters used, including how the workflow state and feedback comments are passed to `mod_assign_save_grade` | out of scope (0017) | run | 0019 |
| 2 | What the assignment functions return: description text, `idnumber`, grading type and maximum grade, marking-workflow setting. Where one is missing, Module 3 uses `cmid` with a stored mapping to the B1 `idnumber` (§2, guide on #186, 25 Nov); no function is added | out of scope (0017) | run | 0019 |
| 3 | What identifies a submission attempt and its last change | out of scope (0017) | run | 0019 |
| 4 | Behaviour when the workflow state is sent for an assignment where marking workflow is off | out of scope (0017) | run | 0019 |
| 5 | Behaviour when saving over a grade that is already released, or that another grader entered | out of scope (0017) | run, half covered (R16) | 0019 |
| 6 | Whether feedback comments are enabled on assignments built by Course Studio, and which format Moodle stores | out of scope (0017) | run | 0019 |
| 7 | Whether the marking-table markers survive Moodle's HTML handling, and how online text arrives | out of scope (0017) | run | 0019 |
| 8 | How suspended users, group submissions, and draft versus submitted statuses appear in the submission functions | out of scope (0017) | run | 0019 |
| 9 | The capability list in §4 is enough for exactly the functions in §2, and nothing more is needed | out of scope (0017) | run | 0019 |
| 10 | How the file download authenticates | out of scope (0017) | run | 0019 |
| 11 | How submissions of suspended learners appear without `moodle/course:viewsuspendedusers` | out of scope (0017) | run | 0019 |
| 12 | The read-back in §3 returns `lastattempt.gradingstatus` = `readyforrelease` after a write. Moodle returns `lastattempt` only when the learner holds `mod/assign:viewownsubmissionsummary` (§7); the student role has it by default, but a course can change it (R6) | out of scope (0017) | run | 0019 |
| 13 | `mod_assign_get_grades` returns the stored, unreleased grade and the attempt number written, and the §3b matching rule holds; record the text format of `grade` (number of decimals) on each database (R1, R9) | out of scope (0017) | run | 0019 |
| 14 | `core_course_get_contents` and `core_enrol_get_enrolled_users` work for the service account without `moodle/course:viewhiddencourses`, `moodle/user:viewhiddendetails` and `moodle/course:useremail` (R4; the guide asked for this on 5.3) | out of scope (0017) | run | 0019 |
| 15 | A grade below zero or above the maximum is silently ignored by `mod_assign_save_grade` with no error, and the read-back shows it (R9) | out of scope (0017) | run | 0019 |
| 16 | Writing over a submission already in `readyforrelease`: 5.3 keeps the old grade while the call looks successful; 4.5 overwrites it (R3) | out of scope (0017) | run | 0019 |
| 17 | Whether `core_course_get_contents` returns the activity and section `idnumber` to the service account, which has no `moodle/course:update` (item 1 covers the parameters, not these returned fields). Until it is recorded, neither Module 1 nor Module 2 may rely on an `idnumber` from this call | out of scope (0017) | run | 0019 |
| 18 | Whether `mod_assign_get_assignments` returns to the service account a field that maps each assignment to its activity (course-module) `idnumber`, the key of the B1 package (item 1 covers the parameters, not these returned fields). Until it is recorded, Module 3 may not map assignments to B1 idnumbers from this call (reviewer on PR #64, 16 Nov) | out of scope (0017) | closed | 0019 |

### 5a. What the 5.3 run changed in this file, and what it did not test

Changes that come from the run (each is in the section named; the full results are in decision 0019):

| Check | Result | Now stated in |
|---|---|---|
| 1 | Feedback comments go in `plugindata[assignfeedbackcomments_editor]` (`text`, `format`) | §2 |
| 2, 17, 18 | No `idnumber` is returned; Module 3 uses `cmid` with a stored mapping | §2 |
| 9 | The System role's `webservice/rest:use` is also used | §4 |
| 11 | A suspended learner's row is left out silently; the status call returns `nopermission` | §4, R5 |
| 4, 5, 15, 16 | Moodle does not protect locked grades from the web service | R3, R9, R13, R16 |

**Not tested, and why.** None of these holds up the freeze of B4 (see the next paragraph). The reasons come from
decision 0019 and the guide's answers; where no reason is recorded, the table says so.

| Not tested | Reason | Handled by |
|---|---|---|
| A learner with no grade row | The safeguard (R16) was set on 26 Nov, after the run and its clean-up; no `mod_assign_get_grades` answer for such a learner was recorded | No lab run needed before the freeze (guide, #112, 26 Nov, [comment](https://github.com/narenccode/learnops/issues/112#issuecomment-7190567102)); R16 treats no row, an empty or null value and a negative value as no grade. A run is welcome as confirmation, recorded in 0019 |
| A grade cleared in Moodle's grading screen | Same; clearing a grade by hand came up in the manual-undo check, which made no web-service read | Same (R16 refuses nothing for a cleared grade, whatever form it takes) |
| An assignment restored from a Course Studio backup (check 6) | No Studio-built backup exists yet; all lab assignments were made by hand or with default settings | Release 2 harness (guide, #112, 26 Nov) |
| A course in separate-groups mode | Course 6 is in group mode 0 and was not changed | Refused by R18 (guide, #112, 26 Nov) |
| Whether each of the six capabilities is needed (check 9) | Only sufficiency was run; no reason recorded | Accepted as it is (guide, #112, 26 Nov) |
| A write over another grader's unreleased grade (half of check 5) | No reason recorded | Covered by R16 (guide, #112, 26 Nov) |
| The release race | No reason recorded | Accepted as a known risk on 5.3 (guide, #112, 26 Nov) |
| Moodle 4.5 | Out of scope | Decision 0017 |

**Effect on the freeze.** None of the items above is a condition for freezing B4. Decision 0018 freezes B4
when its checks pass on 5.3. The guide accepted the run and said B4 freezes after this change merges
(#112, 26 Nov 2026). He decided how each item is handled; for the first two he said no lab run is needed before the
freeze and that a run is welcome as confirmation, recorded in 0019.

## 6. Open questions

Nothing is open at present. The row below is kept as the record of how the lab question was closed.

| Question | Who decides |
|---|---|
| **Lab access.** Closed. The 5.3 lab checks were run on 25 Nov 2026 and accepted by the guide on 26 Nov (decision 0019). Moodle 4.5 is out of scope (decision 0017). B4 freezes on its own after this change merges (decision 0018) | Decided (guide, #112, 26 Nov 2026; #186, 25 Nov 2026) |

**Decided by the guide (PR #27, 2026-10-29):**
- **Q1:** Markdown for the rules plus a small JSON Schema and one example listing the allowed
  functions (§2a). No verified flags in them.
- **Q24:** `MOODLE45_WS_TOKEN` and `MOODLE53_WS_TOKEN`; `MOODLE_WS_TOKEN` removed (§1).
- **Q37:** what `libs/moodle_ws` returns (normalized models), how it enforces the allow-list, and
  its error classes are **not contract text**. They are documented in `docs/design/grading.md`
  §4.1 and, later, in the library's documentation.

**Decided by the guide (PR #64, 2026-11-12):** the eleven questions on the B4 findings, recorded
as rules R1 to R11 in §3a, with the grade-value matching rule in §3b.

**Decided by the guide (PR #72, 2026-11-15):** the three fail-closed proposals that were open here
(state unreadable or unknown, marking workflow off, lost answer with a matching read-back),
recorded as rules R12 to R14 in §3a.

**Decided by the guide (PR #64, 2026-11-16):** the values of `applytoall` and `addattempt`, recorded
as rule R15 in §3a.

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

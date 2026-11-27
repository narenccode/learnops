# B4 lab checks: results on the Moodle 5.3 lab site (App-C item 1)

**Date:** 2026-11-25
**Status:** **Results recorded by the B4 owner (Student 3); the run is accepted by the guide on 2026-11-26**
([#112 comment](https://github.com/narenccode/learnops/issues/112#issuecomment-7176860581)): fifteen checks pass, several with a B4 text change that comes in one
`/contract-change`; check 18 is closed; B4 freezes after that change merges (decision 0018). Check 5 is half
covered (see "Decided by the guide"). Moodle 4.5 is out of scope (decision 0017).
**Addendum 2026-11-26** (end of this file): three more lab reads on the same site, for multiple marking and for the read-before-write safeguard.
**Owner:** Student 3 (B4 owner), who ran the checks.
**Requirement:** PRD App-C item 1 and `contracts/moodle-ws.v1.md` section 5 (all 18 checks).
**Contracts touched:** none by this record. The text changes it suggests (section "What this suggests for
contract B4") go through `/contract-change`, not through this file.
**Numbering:** 0019, the next free number when this was written (2026-11-25: `main` has 0015 to 0018). It is taken again at merge if another record has merged first.

## How the checks were run

- **Site and date:** the Moodle 5.3 lab site, on 25 November 2026. Fictional data only, in course 6.
- **Conditions:** the guide's answers on issue #112 of 23 and 24 November: the admin login on the lab site only;
  a fresh run of all 18 checks; one custom course role with exactly the six capabilities of contract section 4
  (the Non-editing teacher role removed in course 6; the system role holds only `webservice/rest:use`); the
  token created by the person running the checks; `mod_assign_save_grade` and
  `mod_assign_get_grades` added to the test service for the run; only the workflow state `readyforrelease`
  written; a grade that must be released set by a person in Moodle's grading screen, never through the web
  service.
- **Read calls:** the six read functions, by a read-only demo connection (the demo scripts are on the branch
  `demo/h2-grading-tier1`; their pull request, #139, is closed and was never merged) and by hand.
- **Write calls:** by hand, with a small helper kept outside the repository that allows only the eight functions
  of section 2. Every write was read back with `mod_assign_get_grades` and `mod_assign_get_submission_status`.
- **Parameters of `mod_assign_save_grade`** (and of `mod_assign_get_grades`) were read from the site's own web-service documentation, which was
  switched on for the reading and off again.
- **Evidence:** the full outputs and screenshots are kept by the owner outside the repository. No token, address
  or login is in this record, in any issue or in any pull request.
- **Clean-up** (posted on issue #112, [comment](https://github.com/narenccode/learnops/issues/112#issuecomment-7163378092)):
  the two functions added for the run (`mod_assign_save_grade` and `mod_assign_get_grades`) removed from the service, both tokens deleted, the documentation setting off, and
  the admin login no longer needed.

## Results

| # | Check (short) | Result on 5.3 |
|---|---|---|
| 1 | Functions and parameters | The six read functions answered with the parameters we send. The site documents the seven required parameters of `mod_assign_save_grade` (`assignmentid`, `userid`, `grade`, `attemptnumber`, `addattempt`, `workflowstate`, `applytoall`). The feedback comment goes in `plugindata[assignfeedbackcomments_editor][text]` and `[format]`. Both functions added for the run worked (`mod_assign_save_grade` writes; `mod_assign_get_grades` is the read-back). |
| 2 | What the assignment functions return | `intro` (HTML, with `introformat`), `grade` (the maximum grade; a positive value means points, so the grading type is read from its sign: there is no separate field), `markingworkflow` (0 or 1), `cmid` and `coursemodule`, `teamsubmission`, `configs` (plugin settings). **No `idnumber`.** |
| 3 | What identifies an attempt and its last change | Submission rows carry `id`, `userid`, `attemptnumber`, `status`, `groupid`, `latest` and `timemodified`. Grade rows carry `id`, `userid`, `attemptnumber`, `timemodified` and `grader`. |
| 4 | Workflow state sent where marking workflow is off | The call succeeded with no error. The grade was stored (`7.00000`), the status became `graded`, and the grade was **visible to the learner at once**. The state has no effect. |
| 5 | Saving over a released grade | A person released a grade (6) in the grading screen. A write of 4 returned a success with no error. The grade stayed 6, but the state went back to `readyforrelease` and the grade **left the gradebook** (the final grade became empty). |
| 6 | Feedback comments and format | Feedback comments are enabled on all five assignments of course 6, including two created with default settings (readable from `configs`). A comment sent in `plugindata` was stored; the editor shows it as HTML (format 1). Tested on hand-made assignments. **Not tested:** an assignment restored from a Course Studio backup (Release 2 harness). |
| 7 | Markers and online text | The marker comment lines and `data-marking-table="v1"` **survive** in the stored description. Online text arrives as HTML (format 1). Typed with Enter, each line is its own `<p>`; typed with Shift+Enter, lines are separated by `<br />`; no-break spaces appear at the end of lines (in the saved output they are the character U+00A0, not the `&nbsp;` entity). Plain text **pasted** into the editor lost its line structure (one paragraph, runs of no-break spaces). |
| 8 | Suspended users, group submissions, draft or submitted | Statuses seen: `new`, `draft`, `submitted`, and no row for a learner who never opened the assignment. For a group assignment (`teamsubmission` = 1) the text sits on a **group row** (`userid` 0, `groupid` 1); the members' own rows say `submitted` with empty text; a default-group row says `new`. |
| 9 | The capability list is enough | With exactly the six capabilities of section 4, all eight functions of section 2 worked. The only refusal was the status call for a suspended learner, by design (rule R5). Sufficiency was shown; the need for each capability was not tested. |
| 10 | How the file download authenticates | A submitted file was downloaded with the token in the site's own file address (`demo.txt`, 125 bytes). |
| 11 | Suspended learners without `moodle/course:viewsuspendedusers` | `mod_assign_get_submissions` **leaves the suspended learner's row out, with no error**. `mod_assign_get_submission_status` is refused (`required_capability_exception`, `nopermission`). `core_enrol_get_enrolled_users` still lists the learner and carries no suspended flag. |
| 12 | Read-back `lastattempt.gradingstatus` = `readyforrelease` | Confirmed. `lastattempt` is returned, so the student role holds `mod/assign:viewownsubmissionsummary` on this site (rule R6). |
| 13 | `mod_assign_get_grades` read-back | Returns the stored unreleased grade and the attempt number written. The grade text has **five decimals** (`8.00000`). With marking workflow on, `feedback` is absent from the status answer, so `get_grades` is the grade read-back. |
| 14 | Calls without the three "not granted" capabilities | `core_course_get_contents` and `core_enrol_get_enrolled_users` work without `viewhiddencourses`, `viewhiddendetails` and `useremail`. The site returns no `username` for learners (only for the service account itself). |
| 15 | Out-of-range grades | A grade above the maximum (11 of 10) and a grade below zero (-5) were both **silently ignored**: no error, and the read-back shows the "no grade" value (`-1.00000`). The calls **still set the workflow state to `readyforrelease`**. |
| 16 | Writing over `readyforrelease` | The call looked successful, the old grade (`7.00000`) was **kept**, and the grader and modified time of the row were updated. |
| 17 | `idnumber` from `core_course_get_contents` | **Not returned** to this account, for any section or activity, even after an activity idnumber was set. On 5.3 the section settings form has no ID number field. |
| 18 | `idnumber` from `mod_assign_get_assignments` | **Not returned.** Only `cmid` and `coursemodule`. |

## Decided by the guide (2026-11-26, [#112 comment](https://github.com/narenccode/learnops/issues/112#issuecomment-7176860581))

1. **The run is accepted.** Fifteen checks pass (his comment does not list which fifteen; the `/contract-change` fills the 5.3 column for every check), several with a B4 text change, brought in one `/contract-change`:
   check 1 (feedback comments go in `plugindata[assignfeedbackcomments_editor]`); checks 2, 17 and 18 (no activity
   `idnumber` is returned; check 2's "a replacement function is added" is replaced by the answer of 2026-11-25,
   `cmid` with a stored mapping); check 9 (section 4 also names the System role's `webservice/rest:use`, which the
   run used); check 11 (the status call returns `nopermission` for a suspended learner and, in the 5.3 source, for
   any learner the account cannot view). Check 5 is half covered: a write over another grader's unreleased grade
   was not tested, and point 3 covers it.
2. **Check 18 is closed** on the lab result "no `idnumber` returned", together with the answer of 2026-11-25.
3. **The release race is accepted as a known risk on 5.3, with one safeguard.** Before writing, LearnOps reads
   `mod_assign_get_grades` and refuses the write if the learner already has a grade (a stored `-1` means no
   grade). This narrows the race and stops LearnOps overwriting a mentor's own unreleased grade. A `NOT_VERIFIED`
   write tells the mentor to check that learner in Moodle. R3's wording "holds on 5.3" is corrected, because its
   post-write clause does not catch a write over `released` (it ends `readyforrelease`).
4. **The untested areas.** Feedback comments off on an assignment: the write is refused when a comment is to be
   sent (a B4 rule, fail closed). A course in separate-groups mode: the course is refused with its own outcome (a
   B4 rule); the 5.3 source returns an empty list with no error for an account without
   `moodle/site:accessallgroups` that is in no group. An assignment restored from a Course Studio backup waits
   for the Release 2 harness. Whether each of the six capabilities is strictly needed: accepted as it is.

## Findings, as put to the guide

1. **No `idnumber` for this account (17, 18).** This is the lab result for check 18 that the guide asked for. A B1
   `idnumber` cannot be matched to an assignment from these two calls, so Modules 1 and 2 may not rely on it (check 17), and Module 3 may not map assignments by `idnumber` (check 18).
   The guide decided on 2026-11-25 ([#186 comment](https://github.com/narenccode/learnops/issues/186#issuecomment-7157135474),
   item 2) that the key is the course-module id (`cmid`) with a stored mapping to the B1 `idnumber`: no B4
   function is added and no capability is widened. Where the mapping comes from and who fills it is for the
   grading design.
2. **Moodle does not protect locked grades from the web service (4, 5, 15, 16).** Rules R3, R9 and R13 are
   needed in LearnOps because Moodle gives no error in these cases. A write to a released grade pulls it back
   from the gradebook.
3. **A risk that was inferred, not tested:** if a mentor releases a grade between LearnOps reading the state and
   writing, the write would pull the released grade back. Decided by the guide: accepted, with the safeguard
   above.
4. **Suspended learners are invisible (11).** The omission is silent; only the status call's `nopermission`
   tells a suspended learner from a learner with no submission (rule R5).
5. **Online text (7), a proposal for the B1 owner and the guide.** Typed lines arrive as `<p>` or `<br />`, with
   no-break spaces at the end of lines, and pasted text can arrive as one paragraph. A parser for B1.5 rule 5
   will meet these, so B1 must decide how they are read: where a line ends, and how a no-break space counts
   (B1.3 says this is not defined in v1). This record decides nothing about B1.

## What this suggests for contract B4

Not changed here. One `/contract-change` carries the guide's list: section 2 and checks 1, 2, 17 and 18 (the
`plugindata` field; the `idnumber` is not returned; how Module 3 identifies an assignment), section 4 (the System
role's `webservice/rest:use`), check 11, the section 5 table (the 5.3 results and the record number), the corrected
R3 wording, the read-before-write safeguard, and the two refusals (feedback comments off, separate-groups mode).

## Not tested

- A course in separate-groups mode: not run in the lab. The guide decided that such a course is refused (a B4
  rule); the group mode of a course and the participant count in the status answer let the tool detect it.
- An assignment restored from a Course Studio backup (check 6): waits for the Release 2 harness.
- Whether each of the six capabilities is strictly needed (check 9): accepted as it is.
- A write over another grader's unreleased grade (half of check 5): covered by the read-before-write safeguard.
- The release race (finding 3): accepted as a known risk.

## Addendum, 2026-11-26: multiple marking and two read cases

Run by the B4 owner on the same Moodle 5.3 lab site, course 6, fictional data only. Conditions: the admin login the guide
kept for lab tasks ([#112 comment](https://github.com/narenccode/learnops/issues/112#issuecomment-7176898260)); one
temporary token created for the job; `mod_assign_get_grades` added to the test service for the job. **No write function
was added and no grade was written through the web service.** Clean-up: the function removed (the service lists the six
read functions again), the token deleted after the job, the shell variables cleared. Evidence (the saved
answers and screenshots) is kept by the owner outside the repository; no token or address is in this record.

**Why.** (1) The guide's review of the grading design (#186, item 3) asks the design to cover silent partial writes,
including 5.3 multiple marking. The owner had shown that `markercount` is 2 on every lab assignment and so cannot be the
signal, and said the real signal was a lab check still to do. (2) The guide said that the two read cases of the
read-before-write safeguard (a learner with no grade row; a grade cleared in the grading screen) are welcome as
confirmation, recorded here, and do not block the B4 freeze
([#112 comment](https://github.com/narenccode/learnops/issues/112#issuecomment-7190567102)).

### Multiple marking: which field shows it

`mod_assign_get_assignments` returns these marking fields on every assignment: `blindmarking`, `markingworkflow`,
`markingallocation`, `markercount`, `optionalmarkercount`, `multimarkmethod`, `multimarkrounding` and `markinganonymous`.

| Assignment | `markingworkflow` | `markingallocation` | `markercount` | `optionalmarkercount` | `multimarkmethod` |
|---|---|---|---|---|---|
| The five existing ones (ids 3, 4, 9, 32, 33) | 1 on id 3, otherwise 0 | 0 | 2 | 0 | `manual` |
| New "B4 test: multiple marking" (id 34): workflow Yes, allocation Yes, 2 required markers, 0 optional, Calculate grade Manual | 1 | **1** | 2 | 0 | `manual` |
| Same assignment after the number of required markers was set to 1 | 1 | 1 | **1** | 0 | `manual` |

What the assignment form shows: "Use marking workflow" = Yes reveals "Use marking allocation"; "Use marking allocation" = Yes
reveals "Number of required markers" (2), "Number of optional markers" (0) and "Calculate grade" (Manual, Maximum mark,
Average mark). `multimarkrounding` has no option in the form as it was used.

- **`markingallocation` is the field that changes when marking allocation is switched on.** It is 0 on every existing
  assignment and 1 on the new one.
- **`markercount` follows "Number of required markers" but keeps the default 2 when allocation is off.** On its own it
  shows nothing: it is 2 on all five existing assignments, none of which uses multiple marking. Multiple marking itself
  is `markingallocation` 1 together with `markercount` above 1 (or `optionalmarkercount` above 0).
- **Not run:** a grade write on an assignment with allocation on (the design refuses such an assignment, so the write
  does not change the design); the options "Maximum mark" and "Average mark" (so `multimarkrounding` was never seen
  other than 0).
- **Decided by the guide (26 Nov, [#112 comment](https://github.com/narenccode/learnops/issues/112#issuecomment-7196769553), item 2):** the fail-closed rule. A write is allowed only when `markingallocation` is
  present and 0, and refused when it is absent or anything else. It also covers allocation with a single marker and does
  not use `markercount`. The alternative (refuse only when `markingallocation` is 1 and `markercount` is above 1) was not
  chosen, because a missing or odd value would let a write through. It is a design rule in the grading design (#238), not
  part of B4.
- The test assignment "B4 test: multiple marking" (id 34) was **left in course 6** on purpose, as evidence.

### The two read cases for rule R16

`mod_assign_get_grades` on the assignment "Week 1 task" (id 3):

| Case | What Moodle returned |
|---|---|
| A learner with no grade (Learners E, F, G) | **No row at all** |
| A learner whose state was set without a grade (Learner D, check 15) | A row with `-1.00000` and grader `-1` |
| A learner with a grade (Learners A, B, C) | A row with a decimal, for example `8.00000` |
| A grade cleared in the grading screen (Learner A, state first set to In marking) | The **row stays**; the grade is an **empty string** (type string, not null); the grader field is unchanged |

R16 (as the guide worded it on 26 Nov: a grade of 0 or more is a grade; no row, an empty or null value, or a negative value
means no grade, and the write goes ahead) gives the safe result for all four forms. A rule that treated only `-1` as "no
grade" would have refused the cleared grade. The two cases are therefore no longer "not tested".

### State left on the lab

- Learner A is back to grade 8 with its feedback comment, state Ready for release, nothing released. (A's grader field
  reads 2, the admin, because the grade was saved through the screen.)
- The guide does not need to act on this addendum. It changes no contract.

## Where it was decided

- Guide, issue #112, 2026-11-23 and 2026-11-24: the conditions of the run.
- Guide, issue #186, 2026-11-25: decisions 0017 (5.3 only) and 0018 (B4 freezes separately).
- Guide, issue #112, 2026-11-26: the run is accepted and the four questions are answered ([comment](https://github.com/narenccode/learnops/issues/112#issuecomment-7176860581)).
- Guide, issue #112, 2026-11-26: no lab run is needed before the freeze for the two read cases; they are welcome as confirmation, recorded here ([comment](https://github.com/narenccode/learnops/issues/112#issuecomment-7190567102)).
- Guide, issue #112, 2026-11-26 (15:48): the multiple-marking rule is fail closed on `markingallocation` ([comment](https://github.com/narenccode/learnops/issues/112#issuecomment-7196769553), item 2); it is a design rule for the grading design, not part of B4.

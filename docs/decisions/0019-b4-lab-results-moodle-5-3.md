# B4 lab checks: results on the Moodle 5.3 lab site (App-C item 1)

**Date:** 2026-11-25
**Status:** **Results recorded by the B4 owner (Student 3).** This record closes no check by itself: the guide
records which checks the run covers and whether each one passes (decision 0018: B4 freezes when its checks
pass on Moodle 5.3). Moodle 4.5 is out of scope (decision 0017).
**Owner:** Student 3 (B4 owner), who ran the checks.
**Requirement:** PRD App-C item 1 and `contracts/moodle-ws.v1.md` section 5 (all 18 checks).
**Contracts touched:** none by this record. The text changes it suggests (section "What this suggests for
contract B4") go through `/contract-change`, not through this file.
**Numbering:** 0019, the next free number when this was written (2026-11-25: `main` has 0017 and 0018; open
pull requests #209 and #223 take 0015 and 0016). It is taken again at merge if another record has merged first.

## How the checks were run

- **Site and date:** the Moodle 5.3 lab site, on 25 November 2026. Fictional data only, in course 6.
- **Conditions:** the guide's answers on issue #112 of 23 and 24 November: the admin login on the lab site only;
  a fresh run of all 18 checks; one custom course role with exactly the six capabilities of contract section 4
  (the Non-editing teacher role removed in course 6; the system role holds only `webservice/rest:use`); the
  token created by the person running the checks, with a valid-until date; `mod_assign_save_grade` and
  `mod_assign_get_grades` added to the test service for the run; only the workflow state `readyforrelease`
  written; a grade that must be released set by a person in Moodle's grading screen, never through the web
  service.
- **Read calls:** the six read functions, by a read-only demo connection (the demo scripts are on draft PR #139,
  not merged) and by hand.
- **Write calls:** by hand, with a small helper kept outside the repository that allows only the eight functions
  of section 2. Every write was read back with `mod_assign_get_grades` and `mod_assign_get_submission_status`.
- **Parameters of the write functions** were read from the site's own web-service documentation, which was
  switched on for the reading and off again.
- **Evidence:** the full outputs and screenshots are kept by the owner outside the repository. No token, address
  or login is in this record, in any issue or in any pull request.
- **Clean-up** (posted on issue #112, [comment](https://github.com/narenccode/learnops/issues/112#issuecomment-7163378092)):
  the two write functions removed from the service, both tokens deleted, the documentation setting off, and
  the admin login no longer needed.

## Results

| # | Check (short) | Result on 5.3 |
|---|---|---|
| 1 | Functions and parameters | The six read functions answered with the parameters we send. The site documents the seven required parameters of `mod_assign_save_grade` (`assignmentid`, `userid`, `grade`, `attemptnumber`, `addattempt`, `workflowstate`, `applytoall`). The feedback comment goes in `plugindata[assignfeedbackcomments_editor][text]` and `[format]`. Both write functions worked. |
| 2 | What the assignment functions return | `intro` (HTML, with `introformat`), `grade` (the maximum grade; a positive value means points, so the grading type is read from its sign: there is no separate field), `markingworkflow` (0 or 1), `cmid` and `coursemodule`, `teamsubmission`, `configs` (plugin settings). **No `idnumber`.** |
| 3 | What identifies an attempt and its last change | Submission rows carry `id`, `userid`, `attemptnumber`, `status`, `groupid`, `latest` and `timemodified`. Grade rows carry `id`, `userid`, `attemptnumber`, `timemodified` and `grader`. |
| 4 | Workflow state sent where marking workflow is off | The call succeeded with no error. The grade was stored (`7.00000`), the status became `graded`, and the grade was **visible to the learner at once**. The state has no effect. |
| 5 | Saving over a released grade | A person released a grade (6) in the grading screen. A write of 4 returned a success with no error. The grade stayed 6, but the state went back to `readyforrelease` and the grade **left the gradebook** (the final grade became empty). |
| 6 | Feedback comments and format | Feedback comments are enabled on all five assignments of course 6, including two created with default settings (readable from `configs`). A comment sent in `plugindata` was stored; the editor shows it as HTML (format 1). Tested on hand-made assignments. **Not tested:** an assignment restored from a Course Studio backup (Release 2 harness). |
| 7 | Markers and online text | The marker comment lines and `data-marking-table="v1"` **survive** in the stored description. Online text arrives as HTML (format 1). Typed with Enter, each line is its own `<p>`; typed with Shift+Enter, lines are separated by `<br />`; no-break spaces (U+00A0) appear at the end of lines. Plain text **pasted** into the editor lost its line structure (one paragraph, runs of no-break spaces). |
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

## Findings for the guide

1. **No `idnumber` for this account (17, 18).** A B1 `idnumber` cannot be matched to an assignment from these two
   calls. Modules 1 and 2 may not rely on it. As designed (FR-G-01), Module 3 reads the marking table from the
   description and works from the assignment's Moodle id, so it should not need the `idnumber`; the grading
   design should say so.
2. **Moodle does not protect locked grades from the web service (4, 5, 15, 16).** Rules R3, R9 and R13 are
   needed in LearnOps because Moodle gives no error in these cases. A write to a released grade pulls it back
   from the gradebook.
3. **A risk that was inferred, not tested:** if a mentor releases a grade between LearnOps reading the state and
   writing, the write would pull the released grade back. The guide decides whether to accept this or to add a
   safeguard.
4. **Suspended learners are invisible (11).** The omission is silent; only the status call's `nopermission`
   tells a suspended learner from a learner with no submission (rule R5).
5. **Online text (7).** The parser for B1.5 rule 5 must read HTML: `<p>` and `<br />` end a line, no-break
   spaces count as spaces, and pasted text may arrive as one paragraph. For the B1 owner and the guide.

## What this suggests for contract B4

Not changed here. Each goes through `/contract-change`: section 2 and checks 17 and 18 (the `idnumber` is not
returned; how Module 3 identifies an assignment), the section 5 table (the 5.3 results and the record number),
and a note on rule R3 about the release race (finding 3).

## Not tested

- A course in separate-groups mode (`moodle/site:accessallgroups` is listed by Moodle for
  `core_enrol_get_enrolled_users` and the account does not have it). Learners might be missing silently; the
  group mode of a course and the participant count in the status answer let the tool detect this.
- An assignment restored from a Course Studio backup (check 6).
- Whether each of the six capabilities is strictly needed (check 9).
- The release race (finding 3).

## Where it was decided

- Guide, issue #112, 2026-11-23 and 2026-11-24: the conditions of the run.
- Guide, issue #186, 2026-11-25: decisions 0017 (5.3 only) and 0018 (B4 freezes separately).

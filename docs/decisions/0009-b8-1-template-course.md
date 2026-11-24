# B8.1 — Template course: Moodle 4.5 waived for Release 0

## Decision

For Release 0 the B8.1 template course is built and tested on Moodle 5.3 only. Moodle 4.5 is **waived by the guide for Release 0 (decided 2026-11-14, confirmed as a C-03 deviation 2026-11-15; scope B8.1 only)**.

- Every restore and the sections-only merge test for B8.1 run on Moodle 5.3. The `.mbz` is labelled "built on Moodle 5.3".
- Moodle 4.5 is not tested. It is not recorded as passed.
- This is a recorded deviation from PRD C-03 (the tools must work on Moodle 4.5 and 5.3). The PRD text is not changed; the deviation is recorded here and in the C-03 row of `docs/traceability.md`.

## Scope

B8.1 only. A reader must not apply this waiver to any other data set or release.

- The B8.2 restore and merge tests have their own decision, made by the guide on 2026-11-16 (answer A5 on PR #61) and recorded with B8.2, not here.
- C-03 still applies to the checker harness (FR-C-08).

## Cost

If the project later needs the template on Moodle 4.5 (PRD C-03: it must work on 4.5 and 5.3), it is rebuilt once on 4.5. The owner reports that Moodle restores a backup only into the same or a newer version, so a 5.3 template is expected not to restore on 4.5. This is the owner's report and has not been verified.

## Where it was decided

- Guide, Issue #55, 2026-11-14: [build and test on 5.3 only](https://github.com/narenccode/learnops/issues/55#issuecomment-6877171351).
- Guide, PR #95, 2026-11-15: [confirmed as a formal deviation from C-03, scope B8.1](https://github.com/narenccode/learnops/pull/95#issuecomment-6902712542).
- Guide, PR #95, 2026-11-15: [the traceability row](https://github.com/narenccode/learnops/pull/95#issuecomment-6903284655).
- Guide, PR #95, 2026-11-16: [one phrase in every file](https://github.com/narenccode/learnops/pull/95#issuecomment-6907855168).
- Guide, PR #95, 2026-11-16: [this decision record, PRD unchanged, next free number at merge](https://github.com/narenccode/learnops/pull/95#issuecomment-6913152687).

## Results (App-C item 2)

**Result: PASS on Moodle 5.3+ (Build: 20261030), 2026-11-23.** Moodle 4.5: not tested; waived for Release 0 (B8.1 only), as above.

- **Data set, method, who.** B8.1 template course. Moodle's own Backup and Restore in the browser on the 5.3 lab site, the backup archive opened and read, and the comparison tables written from Moodle's own screens. Measured by Harshitha, who ran the session with the guide's OK ([#112, 2026-11-23](https://github.com/narenccode/learnops/issues/112#issuecomment-7101983721)), following the runbook and the guide's #55 answers.
- **Evidence.** Screenshots, logs and the full tables stay local and are not committed. The local screenshots: `Screenshot 2026-11-23 144812.png` and `144830.png` (course page with the extra empty section, A3); `151120.png` (Final project completion: `Make a submission` and `Receive a grade` both ticked, finding 2); `153245.png` (Course feedback `Record user names` = `Anonymous`); `153318.png` (Course feedback completion `Submit feedback`); `153719.png` (Grader report: Final project and Course total only); `154020.png`, `154100.png`, `154118.png`, `154131.png` (course completion settings: Final project and Course feedback, ALL; no other condition enabled); `154512.png` (badge not available, criterion course completion); `154928.png` and `155001.png` (Sample task: `Type` = `None`, `Make a submission`); `155906.png` (first backup's schema page, with the lowercase `sample task` and the extra section); `162507.png` (Final project section); `165352.png` (schema page of the sections-only backup, sections 1 to 3 not selected); `171138.png` (course 10 after the merge: two `Announcements` forums and sections 1 to 5). All are dated 2026-11-23 and kept local in `Pictures\Screenshots`; none is committed. The message Moodle printed after the merge was not recorded.

| Step | Result |
|---|---|
| Build (course 7) | Three sections (`Orientation`, `Sample week`, `Final project`); five activities with the idnumbers `tpl-welcome`, `tpl-sample-guide`, `tpl-sample-task`, `final-project`, `course-feedback`; completion = Final project AND Course feedback; badge `Template course badge`, issuer `LearnOps lab (placeholder)`, not available. Moodle also adds its own `Announcements` forum to section 0 |
| Backup | `b8-1-template-course.v1.mbz`, 12,591 bytes, SHA-256 `b319839079b1b53827d52dc343f93fc9942a9a04c924ddeb030fc6193392963d`; backup format `moodle2`, `backup_version` 2026100500, `backup_release` 5.3; user data OFF |
| Inspection of the file | No `users.xml`; `users` setting 0; nobody enrolled; no email-like text. **The badge is in the file** (status 0, not available), so the P35 risk did not occur on this build. `final-project` (100 points, 1 attempt, marking workflow on) and `course-feedback` (anonymous) are present, with their completion criteria |
| Restore (course 8) | Restored without errors as a new course from the file with the SHA-256 above. Sections, idnumbers, graded item (only Final project, 100 points), completion criteria and badge all match; no users enrolled |
| Sections-only backup (course A, id 9) | 7,143 bytes, SHA-256 `f23fa4b995c61a9aec00d0ad2d72a743c08f58d8a5f7cde4aba689a2dba5224d`. Contains sections 4 and 5 with their four activities, plus section 0 and the `Announcements` forum. No users, no badge, no completion criteria, and no `final-project` or `course-feedback` |
| Merge (course B, id 10) | Merged with `Restore into this course`, `Merge the backup course into this course`, defaults kept. BEFORE and AFTER tables for the four protected items are **equal in every cell** (the fields are those of the B8.1 README §4). **PASS** |

**Findings.**

1. **Second `Announcements` forum (observation for App-C item 2).** Because the sections-only file included section 0, the merge added a second `Announcements` forum to course 10. It is not a protected item; the merge result is still PASS.
2. **Final project completion.** Both `Receive a grade` and `Make a submission` are ticked; the guide asked for `receive a grade` only. The template is the reference for check CK-07, so the extra condition would be carried into every check. Open question to the guide on [#112](https://github.com/narenccode/learnops/issues/112#issuecomment-7123280531): record as a known difference, or untick it and rebuild (new SHA-256, restore check repeated).
3. **Private lab address in the file.** The `.mbz` carries a private lab address (the badge issuer URL and award message, and the site address Moodle stores in every backup) and nothing else about the lab. The guide decided to publish it as it is ([#112, item 4](https://github.com/narenccode/learnops/issues/112#issuecomment-7101983721)).
4. **Renamed copy.** The release file is Moodle's own backup file renamed; the bytes and the SHA-256 are the same.

**Exact Moodle labels (read from the screenshots).** For the 5.3 site: the 5.3 completion choices are `None`, `Students must manually mark the activity as done` and `Add requirements`; under `Add requirements` the boxes are `View the activity`, `Make a submission` and `Receive a grade` (`Any grade` or `Passing grade`) for an assignment, and `View the activity` and `Submit feedback` for the feedback activity; the other fields read: `Grade > Type` = `None`, `Use marking workflow`, `Record user names` = `Anonymous`. Course completion settings: `Course is complete when ALL conditions are met`, `Condition requires` = `ALL selected activities to be completed`; the other conditions (other courses, date, enrolment duration, unenrolment, course grade, manual self completion, manual completion by others) were not enabled, so Moodle added no extra condition.

**Not recorded.** The administrator-screen checks (completion tracking, badges, course badges on) need the administrator account the guide is creating. The message Moodle printed after the merge, the restore result page of course 8, the backup initial-settings pages and the badge issuer fields have no screenshot.

**Test courses.** Courses 8, 9 and 10 stay until this record is merged; then they are deleted (never course 7, the template). Each deletion, its date and whether the course appears in the recycle bin are recorded here, with no recycle-bin setting changed (guide, #55).

# B8.1 Template Course Backup

> **Status: built and tested on Moodle 5.3 on 2026-11-23; the results are in §8 and in decision 0009. The release upload is pending.** The candidate `.mbz` and its SHA-256 are in §1. Release 0 builds and tests on
> Moodle **5.3 only**; Moodle 4.5 is not tested; waived for Release 0 (B8.1 only; see [0009](../../docs/decisions/0009-b8-1-template-course.md) and the [register](../../docs/decisions/README.md)), and is not recorded as passed. Labels: **PRD** = stated by
> the PRD. **Owner** = confirmed by the project owner in a GitHub reply. Sources used in this file: six
> owner replies on Issue #55, cited by date or by name: 2026-11-07; 2026-11-11; 2026-11-12 at 06:46 UTC
> (cited as 2026-11-12); 2026-11-12 at 14:43 UTC (cited as "the 14:43 reply"); 2026-11-13 at 09:36 UTC
> (cited as "the 09:36 reply", a separate, later reply); 2026-11-14 at 12:19 UTC (cited as "the
> 11-14 reply": it replaces the earlier "build on 4.5" decision, see §3); and 2026-11-18 (cited as "the
> 11-18 reply", with the question number it answers, for example P27). A plain "Owner" with no date
> means an owner reply on Issue #55. Other sources: Issue #65 (2026-11-12, section identity) and Issue #61 (2026-11-11, licence;
> the 2026-11-12 reply on #55 refers to it). A row that cites another source says so. **Proposal** = marked
> a proposal by the owner or in a Draft design document, configurable, not a confirmed requirement.
> **PENDING GUIDE CONFIRMATION** = open decision. **PENDING MOODLE LAB** = a fact only a Moodle site can
> show.

## 1. Purpose and scope

**Purpose (PRD §B8):** "A course backup with the protected items (B1.4), course completion and a
badge". A `sections-only` backup is merged into it (PRD §B1.4) to show that the protected items stay
untouched (PRD §C1.7, App-C item 2). The checker builds its model from the `.mbz` itself (PRD FR-C-01;
Owner), so §4 gives a plain list of expected protected items and no separate format.

| Item | Value |
|---|---|
| Owner and release | Student 1 (PRD §B8); Release 0 test data (PRD §D1) |
| Delivery | Owner: GitHub release asset, tag `testdata-b8-1-v1`, fetched by a download script; `*.mbz` is already gitignored. The README and the release label the file "built on Moodle 5.3" (Owner, the 11-14 reply) |
| Rebuilds | Owner (the 11-18 reply, P24): a rebuild is a new asset under a new tag, `testdata-b8-1-v2` (then v3, ...). v1 is kept; update the SHA-256 and this README to name the current asset. Never overwrite a tag. A wrong upload is deleted and replaced by a new version, never overwritten (P33) |
| Backup file name | Proposal (Owner, 2026-11-12): `b8-1-template-course.v1.mbz` |
| Download script | `download.py` in this folder. Owner (the 11-18 reply, P33): `--check` is read-only: it verifies the SHA-256 of the `.mbz` already at the configured path and writes or deletes nothing; `--dry-run` prints the source and target and writes nothing; the plain run downloads to a `.part` file first, and if its SHA-256 verification fails, or the download fails or is stopped, the `.part` file is removed; the undo is deleting the downloaded `.mbz`. It is Python, not the `download.sh` proposed on 2026-11-12, because the project stack is Python and the lab PCs may run Windows. Until the SHA-256 is recorded in it, the script refuses to download (exit 2). Tests: `libs/contracts/tests/test_b8_1_files.py` |
| SHA-256 of the `.mbz` | `b319839079b1b53827d52dc343f93fc9942a9a04c924ddeb030fc6193392963d` (12,591 bytes; the build record is in §8). **Candidate until the guide answers the Final project completion question on issue #112 (§8, finding 2):** a rebuild would give a new SHA-256 and a new build record. Recorded in `download.py` and `testdata/README.md` too |
| Private lab address in the file | The `.mbz` carries a **private lab address** (the badge's issuer URL and the links in its award message, and the site address Moodle stores in every backup) and nothing else about the lab: no users and no email addresses (checked, §8). The address cannot be removed by a setting on 5.3, so the file is published as it is and is not edited by hand (guide, [issue #112, 2026-11-23](https://github.com/narenccode/learnops/issues/112#issuecomment-7101983721), item 4). The address is not written anywhere else in the repository |

## 2. Source and licence

PRD C-07 and §B8: test data only, no real learner data (CLAUDE.md rule 4: no real course content).
`testdata/README.md` asks for the source and licence of every set to be recorded there too.

| Item | Value |
|---|---|
| Creator | The B8.1 owner (Student 1) provides the `.mbz` (Owner) |
| Licence | Owner (Issue #55, 2026-11-12, referring to the answer on Issue #61, 2026-11-11): Apache-2.0, the same as the repository (PRD C-11, root `LICENSE`) |
| Source of the content | Owner (Issue #55, 2026-11-12): fictional content written for LearnOps. No real learner data and no third-party material |
| Badge image | Owner (2026-11-12): a plain image generated by the project under Apache-2.0, with no third-party image. Owner (the 11-18 reply, P9b): a plain square PNG, its source kept in this folder with a record of how it was made. **How it was made:** `make_badge.py` (Python standard library only, no font or third-party image) writes `badge.png`, 512 x 512 pixels, a blue square with a dark-blue 32-pixel border. `python testdata/b8-1-template-course/make_badge.py --check` confirms the committed image matches the script |
| Moodle site used to build it | The Moodle 5.3 lab site (Owner, the 11-14 reply). Release exactly as Moodle shows it: **5.3+ (Build: 20261030)**; built on 2026-11-23 |

## 3. Moodle version and backup details

| Item | Value |
|---|---|
| Moodle release used | Owner (the 11-14 reply, which replaces the 2026-11-12 decision to build on 4.5): build the template on **Moodle 5.3** and run every restore and the sections-only merge test on **5.3**, to save time. The owner reports (Issue #55, 2026-11-14) that Moodle documents that a backup restores into the same or a newer version only, so a template built on 5.3 is expected not to restore on 4.5. This is the owner's report: it has not been checked in the lab or against the Moodle documentation for this project, and the PRD does not state it. Not built yet |
| Moodle 4.5 | **Not tested; waived for Release 0 (B8.1 only; see [0009](../../docs/decisions/0009-b8-1-template-course.md) and the [register](../../docs/decisions/README.md)).** It is not recorded as passed. It can be tested later with the same steps. Known cost (Owner, the 11-14 reply): if the project later needs the template on 4.5 (PRD C-03: must work on 4.5 and 5.3), it is rebuilt once on 4.5. The decision record and §8 record the waiver with its date |
| Course full name, short name, format | Proposal (Owner, 2026-11-12): full name `Template course`, short name `template`, the default Topics (Custom sections) format |
| User data in the backup | OFF, so the file contains no users (Owner). Checked on the finished file on 2026-11-23: no `users.xml`, the `users` setting in `moodle_backup.xml` is 0, nobody is enrolled, and no email-like text is in the file (§8) |
| Exact build, backup format version, other backup settings, file size, date | Build 5.3+ (Build: 20261030); backup format `moodle2`, `backup_version` 2026100500, `backup_release` 5.3; file size 12,591 bytes; date 2026-11-23. Settings read from `moodle_backup.xml`: **on** = activities, blocks, files, filters, badges, calendar events, groups, competencies, custom fields, content bank content, legacy files; **off** = users, anonymise user information, role assignments, comments, user completion details, logs, grade history, user state of H5P content |
| Section identity | Owner (Issue #65, 2026-11-12): Moodle sections have no `idnumber` on 4.5 or 5.3, so the template's sections carry none. Sections are matched by section number, and the protected section is found by its number (PRD §B1.4). The matching change to the B1 contract is a separate `/contract-change` pull request, not part of B8.1 |
| `protected_section` (PRD §B1.4: configurable, no default) | Section 3 (Owner, #61 A2, 2026-11-16; first proposed on 2026-11-07). The value stays configurable: the contract and the validator never hard-code it |
| Availability and visibility | Owner (2026-11-12): no availability rules; everything is visible |

**Section layout** (titles, activities and `idnumber`s in the table below: Owner, 2026-11-12). The
owner's reason for having sections 1 and 2 (Owner, 2026-11-07): they give a merge restore
non-protected content to leave alone. The `tpl-` prefix keeps these `idnumber`s apart from generated
`wk-` ids (Owner, 2026-11-12).

| Section | Title | Contents |
|---|---|---|
| 1 | `Orientation` | One Page, `Welcome`, idnumber `tpl-welcome` |
| 2 | `Sample week` | Page `Sample guide` (`tpl-sample-guide`) and Assignment `Sample task` (`tpl-sample-task`) |
| 3 | `Final project` | The two protected items (§4) |

`Sample task` is **ungraded**. Proposal (Owner, 2026-11-12, Points): the Final project Assignment gets
the 100 points and is the only graded item (§4). Owner (the 11-18 reply, P27): `Sample task` is an
Assignment left ungraded. On 5.3, find and record the name of the setting that leaves no grade item (or 0
points), and the completion setting (submit): recorded on 2026-11-23, as the operator read them from the 5.3 screens (the labels were not copied letter by letter): `Grade > Type` = `None`; completion = `Add requirements`, then `Make a submission`.

**Text of the three activities** (Owner, the 11-18 reply, P27; fictional):

| Activity | Text |
|---|---|
| `Welcome` (Page) | Welcome to the template course. It shows the weekly pattern: a guide page and a task. Add your weeks after it. |
| `Sample guide` (Page) | This is a sample guide page. It shows where weekly guidance goes. |
| `Sample task` (Assignment, description) | This is a sample task. It is not graded; the final project is the only graded item. |

## 4. Protected items

PRD §B1.4: owned by the template; never generated, changed or duplicated by LearnOps. `idnumber`s:
PRD defaults, configurable (Owner). Completion and badge: Owner. Placement and settings: Proposal,
unless a row below says Owner.

**Expected protected items** (plain list for the checker; checked on the finished `.mbz` on 2026-11-23: all four items are in it, §8):

| idnumber | Type | Section | Count |
|---|---|---|---|
| `final-project` | Assignment | 3 "Final project" (Owner for the title; Owner, #61 A2, for the number 3) | 1 |
| `course-feedback` | Feedback | 3 "Final project" (Owner for the title; Owner, #61 A2, for the number 3) | 1 |
| none | Course completion criteria | course level | 2: final project, feedback (Owner) |
| none | Course badge "Template course badge" | course level | 1 (Owner) |

These four rows are the protected items (PRD §B1.4). The protected section (section 3) is the section
that holds the two activities; it is not one of the four items.

**Configuration.** Each row carries its own label. A Proposal row is not a confirmed requirement.

| Item | Status and value |
|---|---|
| Final project | Proposal (Owner, Issue #55, 2026-11-07, item 6): Moodle Assignment; 5 files; 1 attempt; completion on grade; no rubric (a mentor adds it) |
| Course feedback: type, name, idnumber | Owner (Issue #55, 2026-11-07, item 2): Moodle's own Feedback activity, named "Course feedback", idnumber `course-feedback` (the PRD default) |
| Course feedback: anonymous | **Owner-confirmed** (the 11-18 reply, P28): anonymous. The 2026-11-07 reply intended it; listing it among the proposals was the mistake |
| Points | Proposal (Owner, 2026-11-12): the Final project Assignment gets the 100 points and is the only graded item, so `Sample task` (§3) is ungraded. The Moodle default is left, so the points count in the course total. The owner said not to design around it |
| Final project Assignment name | Owner (the 14:43 reply): `Final project`, idnumber `final-project` |
| Exact Moodle setting names and values on 5.3 (4.5: not tested; waived for Release 0 (B8.1 only; see [0009](../../docs/decisions/0009-b8-1-template-course.md) and the [register](../../docs/decisions/README.md))) | Recorded in §8: the 5.3 completion dropdown offers three choices (the activity is marked done manually, no tracking, or `Add requirements` with the requirements under it). **Final project has both `Receive a grade` and `Make a submission` ticked**, where the guide asked for `receive a grade` only (§8, finding 2). The labels of the other settings were not copied letter by letter |

**Baseline for the merge test.** PRD §C1.7 expects the protected items "unchanged (same idnumbers,
same count, badge and completion criteria intact)"; the list above is the baseline. Totals for the
finished template: five activities (`tpl-welcome`, `tpl-sample-guide`, `tpl-sample-task`, `final-project`, `course-feedback`) plus Moodle's own `Announcements` forum in section 0; one graded item (`final-project`, 100 points); two completion criteria; one badge, not available (§8).

**Comparison method (Owner, the 14:43 reply).** Before and after the sections-only merge, write down the
same table for each protected item, with these fields taken from Moodle's own screens: type, name,
idnumber, section number, points, completion setting and visibility. The two tables must be equal. The
B8.1 owner was to send this field list to Shraddha, so that the checker later compares the same fields:
**sent and answered**: Shraddha confirmed the fields in her review of #141 (2026-11-19); the one difference
for the badge is recorded below. The earlier Draft proposal in
`docs/design/studio.md` (compare `idnumber`s, count, badge and completion criteria) is not the confirmed
method.

**How the fields apply to each item** (Owner, the 11-18 reply, P32). Never leave a field blank; the two
tables must be equal field by field.

| Field | Final project, Course feedback | Course completion | Course badge |
|---|---|---|---|
| Type | filled | filled | filled |
| Name | filled | filled | filled |
| idnumber | filled | not applicable | not applicable |
| Section number | filled | not applicable | not applicable |
| Points | filled | not applicable | not applicable |
| Completion | the completion setting | the criteria list | the award rule |
| Visibility | filled | not applicable | not applicable |
| Extra fields | none | none | issuer, description, active state |

**The manual and the checker comparisons differ for the badge** (Shraddha, checker owner, review of
#141, 2026-11-19). The checker builds its model from the `.mbz` (course model v1, B2). For the final
project and the course feedback, that model holds all seven fields above; for course completion, its
criteria list. For the badge it holds only the name and the award rule: **issuer, description and active
state are not in model v1**, so only the lab tables compare them. If 5.3 leaves the unawarded badge out
of the `.mbz` (P35, §6), the model has no badge at all; the checker treats that as the recorded deviation,
not as a missing protected item, and takes it from the decision record after lab step 8.5.

## 5. Course completion configuration

| Setting | Value |
|---|---|
| Criteria | PRD §B1.4 lists "Course completion criteria and course badge" as protected and says they "Point to the two items above" (`final-project`, `course-feedback`). Owner (Issue #55, 2026-11-07): final project graded AND course feedback submitted |
| Completion on the course | PRD §A11 says lab sites have completion tracking on. Owner (Issue #55, update of 2026-11-11): it is switched on in both lab sites (4.5 and 5.3), on by default; not yet checked by the B8.1 owner on the 5.3 site. Checking it needs an administrator screen: ask the guide (Owner, the 11-14 reply). Completion settings of the template course itself: PENDING MOODLE LAB |
| State after restore, including after a sections-only merge | Restored copy (course 8) and merge target (course 10): the completion criteria are unchanged (§8) |

## 6. Badge configuration

| Setting | Value |
|---|---|
| Badge | PRD §B1.4 lists the course badge as protected; its row, shared with the completion criteria, says "Point to the two items above" (`final-project`, `course-feedback`), and gives no other description. Owner (Issue #55, 2026-11-07): course badge "Template course badge"; awarded on course completion; inactive in the template; placeholder issuer |
| Description | Owner (2026-11-12): `Awarded when the template course is completed (placeholder).` |
| Image and image licence | Owner (2026-11-12): a plain image generated by the project, under Apache-2.0, with no third-party image. The file is `badge.png` in this folder, made by `make_badge.py` (see §2) |
| Placeholder issuer text | Owner (the 11-18 reply, P9b): `LearnOps lab (placeholder)` |
| If 5.3 leaves the unawarded badge out of a users-off backup | Owner (the 11-18 reply, P35). Find out first, in lab step 8.5 (open the `.mbz` and look for the badge). If it is left out: record the deviation ("the `.mbz` contains no unawarded badge"; PRD B8.1 expects a badge) in `docs/decisions/0009-b8-1-template-course.md`, this README and the B8.1 row of `docs/traceability.md`; keep the `.mbz` free of users; add the badge by hand to each restored course with `badge.png` and the settings above. **Never add a test user to carry the badge.** The merge test then compares the badge after the manual add, and the record says the `.mbz` does not hold it |
| Course badges on the lab sites | Owner (Issue #55, update of 2026-11-11): switched on in both lab sites, on by default; not yet checked by the B8.1 owner on the 5.3 site. Checking it needs an administrator screen: ask the guide (Owner, the 11-14 reply) |
| Badge in the `.mbz` on 5.3; state after restore and merge (4.5: not tested; waived for Release 0 (B8.1 only; see [0009](../../docs/decisions/0009-b8-1-template-course.md) and the [register](../../docs/decisions/README.md))) | **The badge is in the `.mbz`:** `badges.xml` holds `Template course badge`, status 0 (not available), issuer `LearnOps lab (placeholder)`. It is present on the restored copy and unchanged after the merge (§8). The risk of P35 did not occur on this build, so no manual badge add was needed. The issuer text is the guide's own wording ([answer P9b, 2026-11-18](https://github.com/narenccode/learnops/issues/55#issuecomment-6985988243)) |

## 7. Restore instructions

**Not written yet:** the restore steps are not verified (PRD App-C items 2 and 3). **Fixed:** Moodle's
own Backup/Restore only (CLAUDE.md rule 1). Owner (the 11-14 reply, which replaces "as the site
administrator"): the B8.1 owner uses their own account on the 5.3 lab site, with Moodle's built-in
**Manager** role at site level. The Manager role can back up, restore and merge courses and cannot change
site settings; a step that needs an administrator screen goes to the guide. The Manager account was not
tested on every step: if a restore or merge screen refuses it, write down the exact message and tell the
guide on Issue #55; do not work around it. Using the Manager account for these tests is the guide's
decision (the 11-14 reply); PRD §A5 names the site administrator as the role that restores courses. App-C
item 10 still verifies which roles hold the backup and restore capabilities. For this
manual test the route is Moodle's own Restore page in the browser (Owner, the 14:43 reply). The
command-line route is the harness's separate question (App-C item 3). A sections-only backup is merged into
a course made from the template (PRD §B1.4).

| Item (Owner decision, or pending lab detail) | Status |
|---|---|
| Restore route for the harness (App-C item 3: admin CLI or browser automation) | The harness's own question, separate from B8.1 (Owner, the 14:43 reply). Not decided here |
| Exact steps and options to create a course and to merge | Run on 2026-11-23: Restore with `Restore as a new course`; merge with `Restore into this course`, then `Merge the backup course into this course`, defaults kept (§8). The menu and option labels were reported by the operator and not all were copied letter by letter |
| Clean-up after a test restore | Owner (the 09:36 reply): every course created for a test is deleted after its result is recorded and checked. Owner (the 11-18 reply, P25, P26, P33): that includes restored copies and the merge target; **the template course stays**. Local copies, screenshots, logs and the downloaded `.mbz` stay local, out of Git, and are deleted once the evidence is in the record. Any deletion beyond a test course needs the guide's approval. Do not change site settings or the recycle bin. How to delete a course on 5.3: PENDING MOODLE LAB |
| Cross-version restore | Owner (the 11-14 reply, which replaces the 14:43 reply on this point): build the template on 5.3 and run every restore and the sections-only merge on 5.3 only. Moodle 4.5 is not tested; waived for Release 0 (B8.1 only; see [0009](../../docs/decisions/0009-b8-1-template-course.md) and the [register](../../docs/decisions/README.md)). There is no 4.5 restore test and no 5.3-to-4.5 test in Release 0; the owner expects a 5.3 template not to restore on 4.5 (owner's report, §3; not verified). For each restore, record the Moodle version, the date and the outcome |

### Release 0 sections-only backup

**Owner's confirmed method (Issue #55, 2026-11-12).** Course Studio's sections-only build (FR-S-07) is
due Release 2. For Release 0, make the backup by hand with Moodle's own Backup page, from a copy of the
template with the protected items removed, and document the steps here. Generated sections for the merge
test must use section numbers after 3, because a merge restore keeps the name and summary of a section
that already exists at that number. Studio replaces this later. PRD §B1.4: sections-only output excludes
the protected items and their section.

**Steps (Owner, the 11-18 reply, P15c, P30, P31).** Run on 2026-11-23 on Moodle 5.3+ (Build: 20261030); the
results are in §8. Moodle menu and option labels are as reported by the operator.

1. Restore the template (§1) into a new course on Moodle 5.3. This copy keeps sections 1 to 3; **do not
   renumber it**.
2. In the copy, add two generated sections **by hand**, numbered 4 and 5, each with one Page and one
   Assignment. The B8.2 sample is only a package, and Studio's sections-only build is Release 2, so
   neither is a shortcut here.
3. Make the sections-only backup on Moodle's Backup page, with **user data off**. It contains **only
   sections 4 and 5 and their activities**: no sections 1 to 3, no `tpl-` activities, no section 3, no
   final project, no feedback, no course completion criteria and no badge. Exclude them on the Backup
   page and record each choice.
4. Check the user data in every `.mbz` you make (the template and the sections-only backup): open the
   archive and record whether a users folder exists, what the backup XML records for users, and whether
   any username or email appears. Do not assume the layout. If any user data is present, **stop and
   report on Issue #55**. The site holds test data only.
5. Run the merge-test sequence below with that backup (PRD §B1.4, §C1.7, App-C item 2). Sections 1 to 3
   of the target keep their name and summary because they already exist at those numbers.

**Merge-test sequence (Owner, the 09:36 reply).** The merge target is a course restored from the template,
so it is a test course like any other. Once a course is deleted nothing can be re-checked, so the order
below is fixed. Nothing here is recorded as run.

1. Restore the template into a new course.
2. Record the "before" table for every protected item: type, name, idnumber, section number, points,
   completion setting and visibility, taken from Moodle's own screens.
3. Merge the sections-only backup into that course.
4. Record the "after" table with the same fields.
5. If the two tables are equal: record the text-only results table in the decision record, with the names of
   the local screenshots and logs, and then delete the course. The results must be in the decision record
   before the course is deleted.
6. If the two tables differ: keep the course and report the difference on Issue #55 before taking further
   action. A difference means the merge changed a protected item.

**Our mapping (not the owner's words).** The sections-only backup for step 3 is made first, by steps 1 to 4
above. The "before" and "after" tables use the fields of §4, as the 11-18 reply (P32) applies them to the
completion criteria and the badge.

Screenshots and logs stay local and are not committed (§8). The decision-record number is still taken when
you merge, after rebasing (Owner, Issue #55, 2026-11-12); no numbering convention is assumed here. The
results go in the existing record, `docs/decisions/0009-b8-1-template-course.md`, before the merge-test
course is deleted (Owner, the 11-18 reply, P34).

**Backup contents** (Owner, the 11-18 reply, P15c, P30): settled by steps 1 to 4 above. Still to record in
the lab: the exact Backup-page choices that exclude sections 1 to 3 and the protected items, and the
contents of the two generated sections: recorded in §8 (the sections-only backup row and the build record).

## 8. Verification results (Moodle 5.3; Moodle 4.5 not tested)

Scope: B8.1 only. B8.2 has its own decision (A5 on PR #61), recorded with B8.2 and not restated here. C-03 still applies to the harness (FR-C-08).

**The B8.1 build, the restore and the merge test ran on 2026-11-23 on Moodle 5.3+ (Build: 20261030); the results are below.** Owner: both sites exist, with
completion tracking and course badges switched on in both (Owner, correcting an earlier answer on
2026-11-11: on by default). **Lab access is ready, in person (Owner, the 11-14 reply):** the B8.1 owner
uses a lab PC and the browser, with their own account on the Moodle 5.3 lab site and the built-in
Manager role at site level. Access being ready does not mean any verification is complete. The site
address and the password were to be given in person; neither is recorded here or in any comment. Results need a real run (PRD §E2), stating data set, method, date,
evidence and who measured (PRD §E3). Until the harness approach to fresh sites is decided, test on the
existing 5.3 lab site: restore into a new course each time, record the result, and delete the course by
the clean-up rule in §7 (Owner, the 14:43, 09:36 and 11-14 replies).

| Check | Moodle 4.5 | Moodle 5.3 |
|---|---|---|
| Site and exact release used | Not tested; waived for Release 0 (B8.1 only; see [0009](../../docs/decisions/0009-b8-1-template-course.md) and the [register](../../docs/decisions/README.md)) | 5.3+ (Build: 20261030), 2026-11-23, lab site (address not recorded) |
| Template `.mbz` restores without error | Not tested; waived for Release 0 (B8.1 only; see [0009](../../docs/decisions/0009-b8-1-template-course.md) and the [register](../../docs/decisions/README.md)) | Restored without errors as a new course (course 8), 2026-11-23, from the file with the SHA-256 in §1 |
| Protected items, completion criteria and badge match §4 to §6 | Not tested; waived for Release 0 (B8.1 only; see [0009](../../docs/decisions/0009-b8-1-template-course.md) and the [register](../../docs/decisions/README.md)) | Match (course 8): sections 1 `Orientation`, 2 `Sample week`, 3 `Final project`; the five idnumbers; only Final project graded (100 points); completion = Final project AND Course feedback; badge present, not available, issuer `LearnOps lab (placeholder)`; no users enrolled. Finding 2 applies |
| Sections-only merge leaves protected items unchanged (PRD §C1.7) | Not tested; waived for Release 0 (B8.1 only; see [0009](../../docs/decisions/0009-b8-1-template-course.md) and the [register](../../docs/decisions/README.md)) | **PASS** (course 10): BEFORE and AFTER equal in every cell, 2026-11-23. Findings 1 and 3 apply |

**Run record (PRD §E3).** Data set: B8.1 template course, built on 2026-11-23. Method: Moodle's own Backup and Restore in the browser on the 5.3 lab site, the backup archive opened and read, and the §4 comparison tables written from Moodle's own screens. Measured by Harshitha, who ran the session with the guide's OK ([issue #112, 2026-11-23](https://github.com/narenccode/learnops/issues/112#issuecomment-7101983721)). Evidence: the screenshots, logs and tables stay local and are not committed; the text results are in `docs/decisions/0009-b8-1-template-course.md`.

| Course | Id | What it is |
|---|---|---|
| Template course | 7 | The template. Stays. |
| Restored copy | 8 | Restore test (C). Deleted after this results pull request merges |
| Course A | 9 | Build copy with sections 4 and 5; source of the sections-only backup. Deleted after the merge |
| Course B | 10 | Merge target. Deleted after the merge |

**Build record.** File `b8-1-template-course.v1.mbz`, 12,591 bytes, SHA-256 `b319839079b1b53827d52dc343f93fc9942a9a04c924ddeb030fc6193392963d`, built on Moodle 5.3+ (Build: 20261030), backup format `moodle2` (`backup_version` 2026100500), 2026-11-23. Moodle names a downloaded backup by its own pattern (`backup-moodle2-course-7-template-20261123-1629-nu.mbz`); the release file name is a copy with the same bytes and the same SHA-256 (finding 4).

**Sections-only backup (course A).** 7,143 bytes, SHA-256 `f23fa4b995c61a9aec00d0ad2d72a743c08f58d8a5f7cde4aba689a2dba5224d`. Options on: activities, blocks, files, filters, calendar events, groups, competencies, custom fields, content bank content, legacy files. Options off: users, anonymise user information, role assignments, comments, **badges**, user completion details, logs, grade history, user state of H5P content. Contents: sections 4 `Week 1` and 5 `Week 2` with their four activities, plus section 0 with Moodle's `Announcements` forum. No `users.xml`, no `badges.xml`, no `completion.xml`, and neither `final-project` nor `course-feedback` anywhere in the file.

**BEFORE and AFTER tables (course 10).** Written from Moodle's own screens; every cell is equal.

| Field | Final project | Course feedback | Course completion | Course badge |
|---|---|---|---|---|
| Type | Assignment | Feedback | Course completion | Course badge |
| Name | Final project | Course feedback | not applicable | Template course badge |
| idnumber | `final-project` | `course-feedback` | not applicable | not applicable |
| Section number | 3 | 3 | not applicable | not applicable |
| Points | 100 | no grade item | not applicable | not applicable |
| Completion | receive a grade, and make a submission (finding 2) | submit feedback | Final project AND Course feedback, ALL required | awarded on course completion |
| Visibility | shown | shown | not applicable | not applicable |
| Issuer | not applicable | not applicable | not applicable | LearnOps lab (placeholder) |
| Description | not applicable | not applicable | not applicable | Awarded when the template course is completed (placeholder). |
| Active state | not applicable | not applicable | not applicable | not available |

**Findings.**

1. **Second `Announcements` forum (App-C item 2 observation).** The sections-only backup also held section 0 and Moodle's own `Announcements` forum, so the merge added a second `Announcements` forum to the merge target. It is not a protected item, and the merge result is still PASS.
2. **Final project completion.** The template has both `Receive a grade` and `Make a submission` ticked on Final project; the guide asked for `receive a grade` only. The template is the reference for check CK-07, so the extra condition would be carried into every check. A question to the guide is open on [issue #112](https://github.com/narenccode/learnops/issues/112#issuecomment-7123280531): record it as a known difference, or untick it on course 7 and make a new v1 backup (new SHA-256, restore check repeated).
3. **Private lab address in the file.** See §1: the file carries a private lab address and nothing else about the lab (guide, [issue #112](https://github.com/narenccode/learnops/issues/112#issuecomment-7101983721), item 4).
4. **Renamed copy.** The release file is a copy of Moodle's own backup file, renamed; the bytes and the SHA-256 are the same.

**Not recorded.** The exact Moodle labels of several settings were reported by the operator, not copied letter by letter (§3, §4). The message Moodle printed after the merge and the names of the local screenshots were not recorded. The administrator-screen checks (completion tracking, badges and course badges on) are not recorded yet: they need the administrator account the guide is setting up.

| Question | Status |
|---|---|
| Test sites for the restore tests | Owner (the 14:43 and 11-14 replies): the existing 5.3 lab site, a new course for each restore, deleted by the clean-up rule in §7, until the harness approach to fresh sites is decided. The site and the B8.1 owner's own account are ready (Owner, the 11-14 reply) |
| Where screenshots, logs and comparison tables are kept | Owner (the 14:43 reply): screenshots and logs stay local and nothing from them is committed. Check each for personal data first. A short, text-only results table goes in the decision record and names the local files |
| Whether this §8 table is also filled in, or the results go only in the decision record | Both, with the same results (Owner, the 11-18 reply, P33, P34) |

**Checklist for when the lab is ready** (tasks, not results):

- [x] Owner confirmed that the B8.1 owner's lab access is ready, in person, on the 5.3 site (the 11-14 reply). This is access only: it is not a lab verification result, and no check below is complete because of it.
- [x] Student accounts: not needed. No student accounts exist on the 5.3 site; the B8.1 owner's Manager account is enough. If a step needs a student, ask the guide for a test account (Owner, the 11-18 reply, P19b).
- [ ] Check on the 5.3 site that completion tracking and course badges are on (the Owner says they are, Issue #55, 2026-11-11). This needs an administrator screen: ask the guide (the 11-14 reply).
- [x] Build the template on Moodle 5.3 (§3 to §6); back it up with user data OFF; record release, format and SHA-256. Label the file "built on Moodle 5.3".
- [x] Open the `.mbz` and check it for user data and for the badge (§7 step 4; §6, P35). If user data is present, stop and report on Issue #55.
- [ ] Upload under tag `testdata-b8-1-v1`; put the SHA-256 in `download.py`, §1 and `testdata/README.md`; check that `download.py` and `download.py --check` give the same SHA-256.
- [ ] Give the checker owner the `.mbz`, its SHA-256 and the §4 list.
- [x] Comparison field list (§4): sent to Shraddha, so that the checker later compares the same fields (Owner, the 14:43 reply), and answered in her review of #141 (2026-11-19); the badge difference is recorded in §4.
- [x] Restore on 5.3 only (4.5 is not tested; waived for Release 0 (B8.1 only; see [0009](../../docs/decisions/0009-b8-1-template-course.md) and the [register](../../docs/decisions/README.md)); the owner expects a 5.3 backup not to restore on 4.5: owner's report, §3, not verified), on the existing 5.3 lab site, into a new course each time, deleting each course by the clean-up rule in §7; record the Moodle version, the date and the outcome of each restore; make the sections-only backup (§7); run the merge test with the §4 tables.
- [x] Record that Moodle 4.5 is not tested; waived for Release 0 (B8.1 only; see [0009](../../docs/decisions/0009-b8-1-template-course.md) and the [register](../../docs/decisions/README.md)), and its cost (a rebuild on 4.5 if PRD C-03 later needs it), in the decision record (`docs/decisions/0009-b8-1-template-course.md`) and in §8.
- [x] Keep screenshots and logs local (not committed), check them for personal data, and add the App-C item 2 results to the same decision record (`docs/decisions/0009-b8-1-template-course.md`) as a short, text-only results table that names the local files, before the merge-test course is deleted (Owner, the 14:43 and 09:36 replies).

## 9. Known limitations and pending decisions

- The `.mbz` exists and was tested on 5.3 on 2026-11-23 (§8). Open: the guide's answer on the Final project completion finding (§8, finding 2), the release upload, and the administrator-screen checks. Every Proposal above that §8 does not confirm can still change; none is a confirmed requirement.

**Owner decisions and remaining work (2026-11-12, 2026-11-13 and 2026-11-14):**

| Item | Status |
|---|---|
| Decision record for App-C item 2 | `docs/decisions/0009-b8-1-template-course.md`, added in PR #95 at the guide's request (2026-11-16). It holds the 4.5 waiver (phrase, B8.1-only scope, cost, links to the guide's comments). The number is the next one no open pull request claims; it is taken again at merge, after rebasing (Owner, Issue #55, 2026-11-12), and a renumbering is one file rename plus the paths in this README, the runbook and `docs/traceability.md`. The same file later holds the short, text-only results table that names the local evidence files (Owner, the 14:43 reply); the results must be in it before the merge-test course is deleted (Owner, the 09:36 reply). The results table is not written yet |
| `docs/traceability.md` | Owner: one B8.1 entry, following the B1 and B8 pattern, no FR id, citing PRD B8.1 and B1.4. Added in PR #57, merged on 2026-11-13 |
| `testdata/README.md` entry | Updated for the 2026-11-12 owner answers. It now records the owner-confirmed Apache-2.0 licence and the owner-confirmed section titles and activity idnumbers. The protected-section number is owner-confirmed (#61 A2); the final-project settings remain proposals. The `.mbz` file and its SHA-256 are still pending, because no backup exists yet |

**Still open:**

| Open item | Status |
|---|---|
| Lab access for the B8.1 owner | Ready, in person: own account on the Moodle 5.3 lab site, Manager role at site level (Owner, the 11-14 reply). Access only; not a lab verification result |
| Student accounts on the lab sites | Answered (the 11-18 reply, P19b): none exist and B8.1 does not need them; ask the guide if a step needs one |
| Text of the Pages, settings of `Sample task`, placeholder issuer text, badge image tool and location | Answered (the 11-18 reply, P27, P9b): see §3, §2 and §6. Recorded on 2026-11-23: `Grade > Type` = `None` and completion `Make a submission` for `Sample task` (§3) |
| How the §4 comparison fields apply to the course completion criteria and the badge (no section number or points) | Answered (the 11-18 reply, P32): see the table in §4 |
| Whether the §8 results table is also filled in, or the results go only in the decision record | Answered (the 11-18 reply, P33): both, with the same results |
| How the decision record is held before its number is taken at merge, because the results must be in it before the merge-test course is deleted (§7) | Answered (the 11-18 reply, P34): the results table goes in `docs/decisions/0009-b8-1-template-course.md`, naming the local evidence files, before the merge-test course is deleted |
| Whether 5.3 keeps an unawarded badge in a users-off backup | **Answered 2026-11-23: yes.** The unawarded, not-available badge is in the users-off `.mbz` on this 5.3 build (§6). What to do either way is settled in §6 (the 11-18 reply, P35) |
| Comparison field list for Shraddha (an action, not a decision) | Owner's instruction (the 14:43 reply). Sent, and answered in Shraddha's review of #141 (2026-11-19): the checker's course model v1 holds the badge's name and award rule only, so issuer, description and active state are compared only in the lab tables (§4) |
| Exact contents of the sections-only backup (which sections are in or out; which of the four PRD §B1.4 protected items are removed: final project assignment, course feedback activity, course completion criteria, course badge; whether the protected section 3 is in the copy or the backup; backup settings; content of generated sections); see §7 | Answered (the 11-18 reply, P15c, P30, P31): only generated sections 4 and 5, user data off; see §7 steps 1 to 4 |
| Whether the course feedback activity is anonymous as a confirmed setting or a proposal (conflicting owner answers, §4) | Answered (the 11-18 reply, P28): owner-confirmed, anonymous |
| Moodle 4.5 | Not tested; waived for Release 0 (B8.1 only; see [0009](../../docs/decisions/0009-b8-1-template-course.md) and the [register](../../docs/decisions/README.md)). The owner expects a 5.3 template not to restore on 4.5 (owner's report, §3; not verified); if PRD C-03 later needs the template on 4.5, it is rebuilt once on 4.5 (Owner, the 11-14 reply) |

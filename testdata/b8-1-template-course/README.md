# B8.1 Template Course Backup

> **Status: skeleton.** No `.mbz` exists; nothing is verified on Moodle. Labels: **PRD** = stated by
> the PRD. **Owner** = confirmed by the project owner in Issue #55. **Proposal** = proposed (Issue #55 or
> a Draft design document), configurable, not a confirmed requirement. **PENDING GUIDE CONFIRMATION**
> = open decision. **PENDING MOODLE LAB** = a fact only a Moodle site can show.

## 1. Purpose and scope

**Purpose (PRD §B8):** "A course backup with the protected items (B1.4), course completion and a
badge". A `sections-only` backup is merged into it (PRD §B1.4) to show that the protected items stay
untouched (PRD §C1.7, App-C item 2). The checker builds its model from the `.mbz` itself (PRD FR-C-01;
Owner), so §4 gives a plain list of expected protected items and no separate format.

| Item | Value |
|---|---|
| Owner and release | Student 1 (PRD §B8); Release 0 test data (PRD §D1) |
| Delivery | Owner: GitHub release asset, tag `testdata-b8-1-v1`, fetched by a download script; `*.mbz` is already gitignored. Script name and path, backup file name: PENDING GUIDE CONFIRMATION |
| SHA-256 of the `.mbz` | PENDING MOODLE LAB (record here and in `testdata/README.md` when the backup exists) |

## 2. Source and licence

PRD C-07 and §B8: test data only, no real learner data (CLAUDE.md rule 4: no real course content).
`testdata/README.md` asks for the source and licence of every set to be recorded there too.

| Item | Value |
|---|---|
| Creator and licence | The B8.1 owner (Student 1) provides the `.mbz` (Owner). Moodle site used; origin and licence of any text, images or files inside it: PENDING GUIDE CONFIRMATION |

## 3. Moodle version and backup details

| Item | Value |
|---|---|
| Moodle release used (PRD C-03: must work on 4.5 and 5.3; Owner: lab sites for both exist); course full name, short name, format | PENDING GUIDE CONFIRMATION |
| User data in the backup | OFF, so the file contains no users (Owner). Check on the finished file, including for real learner data: PENDING MOODLE LAB |
| Exact build, backup format version, other backup settings, file size, date | PENDING MOODLE LAB |
| Sections | Proposal (Issue #55 item 1): 1 "Orientation", 2 a sample week, 3 "Final project". Owner: Moodle sections have no `idnumber` (checked on the 4.5 table); PRD §B1 and its glossary give sections one: PENDING GUIDE CONFIRMATION. Sections 1 and 2 give a merge restore non-protected content to leave alone. |
| Section 2 title; activities (and `idnumber`s) in sections 1 and 2 | PENDING GUIDE CONFIRMATION |
| `protected_section` (PRD §B1.4: configurable, no default) | Proposal: 3, kept configurable |

## 4. Protected items

PRD §B1.4: owned by the template; never generated, changed or duplicated by LearnOps. `idnumber`s:
PRD defaults, configurable (Owner). Completion and badge: Owner. Placement and settings: Proposal.

**Expected protected items** (plain list for the checker; to be checked on the finished `.mbz`: PENDING MOODLE LAB):

| idnumber | Type | Section | Count |
|---|---|---|---|
| `final-project` | Assignment | 3 "Final project" (Proposal) | 1 |
| `course-feedback` | Feedback | 3 "Final project" (Proposal) | 1 |
| none | Course completion criteria | course level | 2: final project, feedback (Owner) |
| none | Course badge "Template course badge" | course level | 1 (Owner) |

**Proposed configuration** (Issue #55 item 6, marked a proposal by the owner; not a confirmed requirement):

| Item | Proposal |
|---|---|
| Final project | Moodle Assignment; 5 files; 1 attempt; completion on grade; no rubric (a mentor adds it) |
| Course feedback | Moodle Feedback activity; anonymous; name "Course feedback" |
| Points | 100 (Owner, Issue #55 item 6: "use 100", marked a proposal). Which activity receives the 100: PENDING GUIDE CONFIRMATION (the Owner's answer does not say). Whether the 100 count inside the course total: not decided (Owner); kept configurable and not designed around: PENDING GUIDE CONFIRMATION |
| Visibility and availability rules | PENDING GUIDE CONFIRMATION |
| Exact Moodle setting names and values on 4.5 and 5.3 | PENDING MOODLE LAB |

**Baseline for the merge test.** PRD §C1.7 expects the protected items "unchanged (same idnumbers,
same count, badge and completion criteria intact)"; the list above is the baseline. Totals for the
finished template: PENDING MOODLE LAB. Comparison method: PENDING GUIDE CONFIRMATION (*Proposal*,
`docs/design/studio.md` Draft: compare `idnumber`s, count, badge and completion criteria).

## 5. Course completion configuration

| Setting | Value |
|---|---|
| Criteria | PRD §B1.4 lists "Course completion criteria and course badge" as protected and says they "Point to the two items above" (`final-project`, `course-feedback`). Owner (Issue #55 item 3): final project graded AND course feedback submitted |
| Completion on the course | PRD §A11 says lab sites have completion tracking on. Owner (Issue #55, update of 2026-11-11): it is switched on in both lab sites (4.5 and 5.3), on by default; not yet checked by the B8.1 owner on a site. Completion settings of the template course itself: PENDING MOODLE LAB |
| State after restore, including after a sections-only merge | PENDING MOODLE LAB |

## 6. Badge configuration

| Setting | Value |
|---|---|
| Badge | PRD §B1.4 lists the course badge as protected; its row, shared with the completion criteria, says "Point to the two items above" (`final-project`, `course-feedback`), and gives no other description. Owner (Issue #55 item 3): course badge "Template course badge"; awarded on course completion; inactive in the template; placeholder issuer |
| Description, image and image licence | PENDING GUIDE CONFIRMATION |
| Course badges on the lab sites | Owner (Issue #55, update of 2026-11-11): switched on in both lab sites, on by default; not yet checked by the B8.1 owner on a site |
| Badge in the `.mbz` on 4.5 and 5.3; state after restore and merge | PENDING MOODLE LAB |

## 7. Restore instructions

**Not written yet:** the restore route is not verified (PRD App-C items 2 and 3). **Fixed:** Moodle's
own Backup/Restore only (CLAUDE.md rule 1); an administrator restores (PRD §C1.2 user story; App-C item
10 still verifies the roles); a sections-only backup is merged into a course made from the template (PRD §B1.4).

| Not yet known | Value |
|---|---|
| Restore route (App-C item 3: admin CLI or browser automation); steps and options to create a course and to merge; clean-up after a test restore | PENDING MOODLE LAB |
| Account and role used to restore on the lab sites | PENDING GUIDE CONFIRMATION |

## 8. Verification results for Moodle 4.5 and 5.3

**Nothing has been verified, and no lab verification has been attempted.** Owner: both sites exist, with
completion tracking and course badges switched on in both (Owner, correcting an earlier answer on
2026-11-11: on by default), but student accounts and the B8.1 owner's access are not ready; the owner will
say when they are. Results need a real run on a fresh site (PRD §E2), stating data set, method, date,
evidence and who measured (PRD §E3).

| Check | Moodle 4.5 | Moodle 5.3 |
|---|---|---|
| Site and exact release used | PENDING MOODLE LAB | PENDING MOODLE LAB |
| Template `.mbz` restores without error | PENDING MOODLE LAB | PENDING MOODLE LAB |
| Protected items, completion criteria and badge match §4 to §6 | PENDING MOODLE LAB | PENDING MOODLE LAB |
| Sections-only merge leaves protected items unchanged (PRD §C1.7) | PENDING MOODLE LAB | PENDING MOODLE LAB |

**Checklist for when the lab is ready** (tasks, not results):

- [ ] Owner confirms: student accounts exist and the B8.1 owner has access to both sites. Then check on each site that completion tracking and course badges are on (the Owner says they are, Issue #55, 2026-11-11).
- [ ] Build the template (§3 to §6); back it up with user data OFF; record release, format and SHA-256.
- [ ] Upload under tag `testdata-b8-1-v1`; check the download script gives the same SHA-256.
- [ ] Give the checker owner the `.mbz`, its SHA-256 and the §4 list.
- [ ] Restore on fresh 4.5 and 5.3 sites; fill in the table; run the merge test; record App-C item 2 in `docs/decisions/` (PRD).

App-C item 2 is a Release 0 verification, but the §C1.7 test uses Course Studio's sections-only build
(FR-S-07, due Release 2). How the Release 0 sections-only backup is made: PENDING GUIDE CONFIRMATION.

## 9. Known limitations and pending decisions

- No `.mbz` exists and nothing is tested. Every Proposal above can change; none is a confirmed requirement.

| Open item | Status |
|---|---|
| Sections-only backup for App-C item 2 (§8); name of the `docs/decisions/` record | PENDING GUIDE CONFIRMATION |
| `testdata/README.md` entry: added (source, section layout marked as a proposal, SHA-256 to be added when the `.mbz` exists). Licence of the content | PENDING GUIDE CONFIRMATION |
| Whether B8.1 needs a `docs/traceability.md` entry (CLAUDE.md §7 item 3; none exists for B8 today) | PENDING GUIDE CONFIRMATION |

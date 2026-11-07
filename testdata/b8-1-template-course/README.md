# B8.1 Template Course Backup

> **Status: skeleton.** No `.mbz` exists and nothing has been verified on Moodle. Labels used below:
> **PRD** = stated by the PRD. **PENDING GUIDE CONFIRMATION** = a decision the guide must make.
> **PENDING MOODLE LAB** = a fact only a Moodle site can show. **Proposed** = taken from a Draft
> design document and not approved.

## 1. Purpose and scope

**Purpose (PRD §B8):** "A course backup with the protected items (B1.4), course completion and a
badge". A `sections-only` backup is restored into it by merging (PRD §B1.4), to show that the merge
leaves the protected items untouched (PRD §C1.7, App-C item 2). The finished set is one `.mbz` of
the template course plus this README, which records how it was made and checked.

| Item | Value |
|---|---|
| Owner and release | Student 1 (PRD §B8); Release 0 test data (PRD §D1) |
| Backup file name | PENDING GUIDE CONFIRMATION |
| Storage: in Git, or fetched by a download script | PENDING GUIDE CONFIRMATION (PRD "Repository layout" allows download scripts "where licences require") |

## 2. Source and licence

PRD C-07 and §B8: test data only, no real learner data (CLAUDE.md rule 4: no real course content).
`testdata/README.md` asks for the source and licence of every set to be recorded there too.

| Item | Value |
|---|---|
| Who creates the course, and on which Moodle site | PENDING GUIDE CONFIRMATION |
| Origin and licence of any text, images or files inside it | PENDING GUIDE CONFIRMATION |
| Check that no real learner data is present | PENDING MOODLE LAB (on the finished backup) |

## 3. Moodle version and backup details

PRD C-03: everything must work on Moodle 4.5 and 5.3. The PRD does not say where the template is made.

| Item | Value |
|---|---|
| Moodle release used to make the backup | PENDING GUIDE CONFIRMATION |
| Exact build, backup format version, backup settings, whether user data is included; file size, checksum and date of the `.mbz` | PENDING MOODLE LAB |
| Course full name, short name, format and number of sections | PENDING GUIDE CONFIRMATION |
| `protected_section` number (PRD §B1.4: configurable, no default given) | PENDING GUIDE CONFIRMATION |

## 4. Protected items

PRD §B1.4: owned by the course template; never generated, changed or duplicated by LearnOps. The
identifiers are the PRD defaults, which the PRD says are configurable.

| Protected item (PRD §B1.4) | Identified by (PRD default) | Used in this template |
|---|---|---|
| Final project assignment | `idnumber: final-project` | PENDING GUIDE CONFIRMATION |
| Course feedback activity | `idnumber: course-feedback` | PENDING GUIDE CONFIRMATION |
| Course completion criteria and course badge | "Point to the two items above" | PENDING GUIDE CONFIRMATION |

For each of the two activities, the type, name, section, visibility, availability rules, completion
rule and (if graded) maximum grade are all PENDING GUIDE CONFIRMATION.

**Baseline for the merge test.** PRD §C1.7 expects the protected items "unchanged (same
idnumbers, same count, badge and completion criteria intact)". To compare, record these from the
finished backup before any merge: the number of protected activities and the `idnumber` of each, and
the total activities and sections (PENDING MOODLE LAB). How "before" and "after" are compared is
PENDING GUIDE CONFIRMATION. *Proposed* (`docs/design/studio.md`, Draft): the harness compares
`idnumber`s, count, badge and completion criteria.

## 5. Course completion configuration

PRD §B1.4: the completion criteria are protected. The PRD does not say which criteria are used.

| Setting | Value |
|---|---|
| Completion enabled on the course (PRD §A11: lab sites have completion tracking on; the course setting is not specified) | PENDING GUIDE CONFIRMATION |
| Criteria used, and whether they refer to the two protected activities | PENDING GUIDE CONFIRMATION |
| State after restore, including after a sections-only merge | PENDING MOODLE LAB |

## 6. Badge configuration

PRD §B1.4: the course badge is protected. The PRD does not describe it.

| Setting | Value |
|---|---|
| Badge name, description, image and image licence | PENDING GUIDE CONFIRMATION |
| Award criteria | PENDING GUIDE CONFIRMATION |
| Whether the badge is included in the `.mbz` on 4.5 and on 5.3 | PENDING MOODLE LAB |
| State after restore, including after a sections-only merge | PENDING MOODLE LAB |

## 7. Restore instructions

**Not written yet:** the restore route is not verified (PRD App-C items 2 and 3). **Fixed by the
PRD and CLAUDE.md:** restore uses Moodle's own Backup/Restore and LearnOps does not modify Moodle
(CLAUDE.md rule 1); an administrator restores (PRD §C1.2 user story; App-C item 10 still has to
verify the roles); a sections-only backup is merged into a course created from the template (PRD §B1.4).

| Not yet known | Value |
|---|---|
| Restore route for the harness: Moodle admin CLI, or browser automation (App-C item 3) | PENDING MOODLE LAB |
| Steps and options to create a course from this backup | PENDING MOODLE LAB |
| Steps to merge a sections-only backup into that course | PENDING MOODLE LAB |
| Clean-up after a test restore | PENDING MOODLE LAB |
| Account and role used to restore on the lab sites | PENDING GUIDE CONFIRMATION |

## 8. Verification results for Moodle 4.5 and 5.3

**Nothing has been verified.** Every result is pending and must come from a real run on a fresh site
(PRD §E2). PRD §E3: each measurement states the data set, method, date and who measured.

| Check | Moodle 4.5 | Moodle 5.3 |
|---|---|---|
| Site and exact release used | PENDING MOODLE LAB | PENDING MOODLE LAB |
| Template `.mbz` restores without error | PENDING MOODLE LAB | PENDING MOODLE LAB |
| Protected activities present with the expected `idnumber`s | PENDING MOODLE LAB | PENDING MOODLE LAB |
| Completion criteria and badge present as recorded in §5 and §6 | PENDING MOODLE LAB | PENDING MOODLE LAB |
| Sections-only merge leaves protected items unchanged (PRD §C1.7) | PENDING MOODLE LAB | PENDING MOODLE LAB |
| Date, who ran it, evidence location | PENDING MOODLE LAB | PENDING MOODLE LAB |

App-C item 2 is a Release 0 verification; the §C1.7 acceptance test uses Course Studio's
sections-only build (FR-S-07, Release 2). Because FR-S-07 is not due until Release 2, how the
sections-only backup for the App-C check is made is PENDING GUIDE CONFIRMATION. The PRD says App-C
results go in `docs/decisions/`; the file name is PENDING GUIDE CONFIRMATION.

## 9. Known limitations and pending decisions

- No `.mbz` exists and nothing is tested. No course names, IDs, section numbers, points, completion
  criteria, badge settings or Moodle configuration are chosen; each is marked pending in its section.

Open items that cross sections (other decisions are marked where they arise):

| Item | Status |
|---|---|
| How the Release 0 sections-only backup is made, and the name of the `docs/decisions/` record (§8) | PENDING GUIDE CONFIRMATION |
| Whether B8.1 needs a `docs/traceability.md` entry (CLAUDE.md §7 item 3; none exists for B8 today) | PENDING GUIDE CONFIRMATION |
| *Proposed* Draft Course Studio consideration, not a B8.1 requirement: the finished backup's size may inform the Draft upload limits (`docs/design/studio.md`, item 30) | PENDING MOODLE LAB |

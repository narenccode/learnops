# A11 lab readiness record (Release 0)

**Date checked:** 2026-11-24, on the lab Moodle 5.3 site, by Akshita (Student 1), with an administrator
account the guide gave her (issue #112, 2026-11-24).
**Requirement:** PRD §A11 (lab environment); §D1 lists "Lab VMs ready (A11)" for Release 0.
**Method:** Moodle's own admin screens, read only. No setting was changed for this record. Nothing here
names an address, host name, IP, password, token or key (PRD C-06, A7). What could not be seen is written
**unknown**, never guessed.
**Status:** partial. It records what the 5.3 site shows; every other A11 machine is unknown or not tested.
Whether the lab is "ready" for Release 0 is the guide's call.

## PRD §A11, item by item

| PRD §A11 item | Expected (PRD) | Found | Source |
|---|---|---|---|
| `moodle53`: Moodle 5.3 | Moodle 5.3 on Ubuntu 22.04, nginx, PHP 8.3, PostgreSQL 16 | **Moodle 5.3+ (Build: 20261030), version 2026100500.08.** The Notifications page also offers an update to 5.3.1+ (Build: 20261117), not installed. Operating system, web server, PHP and database versions: **unknown** (not checked) | B8.1 backup taken on the site (`moodle_backup.xml`), and the Notifications page |
| `moodle45`: Moodle 4.5 | Moodle 4.5, latest point release | **Not tested; 5.3 lab only** (the guide said on #55, 2026-11-11, that the site exists) | — |
| `bbb`: BigBlueButton 3.0, video format | BigBlueButton 3.0 with the video recording format | **Unknown** (not reached) | — |
| `tools`: Docker host | Runs the LearnOps services and the tool database | **Unknown** (not reached; ffmpeg not checked) | — |
| Lab AI services | A local LLM endpoint and a speech-to-text endpoint | **Unknown.** The guide will post the speech service facts on #98 (no date yet) | Issue #112, 2026-11-23 |
| Lab HTTPS certificate | (needed for LTI, ADR 0001) | **Unknown** (the guide's, OI-14) | — |

## Moodle 5.3 site settings that A11 names

| A11 says | Setting | Found |
|---|---|---|
| Completion tracking on | Advanced features > Enable completion tracking (`enablecompletion`) | **On** |
| Web services enabled | Advanced features > Enable web services (`enablewebservices`) | **On** (Moodle's default is off) |
| (web services) | Server > Web services > Manage protocols | **REST enabled**; SOAP disabled. Web services documentation (`enablewsdocumentation`) off. Web services for mobile devices (`enablemobilewebservice`) off |
| Dedicated service account (§B4) | Server > Web services > External services and Manage tokens | **Present.** Service "LearnOps grading read" (`learnops_grading_read`) with six read functions: `core_course_get_contents`, `core_course_get_courses_by_field`, `core_enrol_get_enrolled_users`, `mod_assign_get_assignments`, `mod_assign_get_submission_status`, `mod_assign_get_submissions`. `mod_assign_save_grade` and `mod_assign_get_grades` are not on it (they are added only for the B4 write checks, guide on #112). A dedicated service account has a token for this service. Its operational details are not recorded here (information minimisation, review of #213) |
| H5P enabled with the pinned types (§B7) | H5P > Manage H5P content types | **Present:** Question Set (`H5P.QuestionSet`) 1.21.14 and Drag and Drop (`H5P.DragQuestion`) 1.15.37, both enabled, the versions in decision 0008 |
| (badges, used by B8.1) | Advanced features > Enable badges; Badges settings > Enable course badges | **Both on** |
| LTI 1.3 tools registered (§B3) | External tool registrations | **Unknown** (not checked) |

## Test data and accounts on the 5.3 site (by role name only)

- **Course 6** ("Engineering design analysis", the B4 test course): seven participants, all active, no
  groups: four students (fictional learners a to d), two teachers (a fictional teacher and the admin
  account) and the web-service account. The web-service account holds **two** roles in course 6: the
  built-in "Non-editing teacher" and the custom role "LearnOps web service". The guide's 23 November
  conditions say the built-in role is not used; the B4 checks record this (contract B4 lab check 9).
- **Course 7** ("Template course"): the B8.1 template. Courses 8 to 13 are B8.1 restore and merge test
  courses, to be deleted after their results are recorded (B8.1 runbook, P25).
- **Moodle AI features:** installed but unusable (no provider instance, both placements disabled); see
  decision 0012, "Lab result".

## Still unknown (for the guide or the lab administrator)

1. Operating system, web server, PHP and database versions of `moodle53`.
2. Everything about `moodle45`, `bbb` and `tools`, including ffmpeg on `tools` (decision 0013).
3. The lab AI services (#98).
4. The HTTPS certificate (OI-14) and the LTI 1.3 tool registrations.

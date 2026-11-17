# Course Studio: literature survey (Release 0)

**Module:** Course Studio (M1, Student 1: `Akshita21-09`).
**Requirement:** `docs/GETTING-STARTED.md` (Student 1, "Literature survey for **your** module": at least 6
sources, each opened and verified) and PRD §C1.12 "Bloom mapping" (Survey, L2: Moodle backup format, IMS
Common Cartridge limits, course-as-code).
**Status:** Draft. **7 sources recorded, plus 1 obsolete page kept for comparison (S4).** Owner
verification of each source is still to do (column "Owner verification" below).

This file follows `docs/literature-video.md`: `docs/GETTING-STARTED.md` allows a survey in
`docs/design/<module>.md` §12 or in `docs/literature-<module>.md`, and this file uses the second option.
AI tools can invent citations (root `CLAUDE.md` §6a, rule 5), so every source here was opened at its URL
on 2026-11-18 and only what the page said that day is recorded. The owner opens each source again before
this survey is marked complete.

**How to read an entry.**

- **Source-reported:** what the page itself states (paraphrased; no long quotations).
- **Audit observation:** something noticed while checking, including limits of the source. Discrepancies
  are kept, not resolved.
- **Relevance to Studio:** where it bears on `docs/design/studio.md` or Release 0 work. This is our reading,
  not the source's claim.
- **UNKNOWN:** the source does not supply it. Nothing is filled in from outside the source.

Documentation describes Moodle's intended behaviour. It is not a LearnOps lab result: every Moodle fact
that a design decision depends on is still checked on the lab site (PRD Appendix C).

## Sources recorded

| ID | Source | Type | Topic (§C1.12) | Opened | Owner verification |
|---|---|---|---|---|---|
| S1 | MoodleDocs 4.5, *Course backup* | Official user documentation | Backup format | 2026-11-18 | To do |
| S2 | MoodleDocs 4.4, *Backup and restore FAQ* | Official user documentation | Backup format | 2026-11-18 | To do |
| S3 | MoodleDocs 4.5, *Course restore* | Official user documentation | Backup format | 2026-11-18 | To do |
| S4 | MoodleDocs (dev), *Backup 2.0 general architecture* | Developer documentation, **marked obsolete** | Backup format | 2026-11-18 | To do |
| S5 | Moodle Developer Resources, *Backup API* | Current developer documentation | Backup format | 2026-11-18 | To do |
| S6 | MoodleDocs 4.5, *IMS Common Cartridge import and export* | Official user documentation | Common Cartridge limits | 2026-11-18 | To do |
| S7 | 1EdTech, *Common Cartridge®* standard page | Standards body page | Common Cartridge limits | 2026-11-18 | To do |
| S8 | Open edX docs (Ulmo), *What is the OLX Course Structure?* and *Getting Started with OLX* | Official platform documentation | Course-as-code | 2026-11-18 | To do |

S4 is counted separately: it is kept only because no current page describes the file layout inside a
backup, and its own banner says it is not reliable. Without S4 there are seven sources.

---

## S1. MoodleDocs 4.5: Course backup

**Citation.** Moodle, *Course backup*, MoodleDocs, Moodle 4.5 documentation.
<https://docs.moodle.org/405/en/Course_backup>. Page last edited 11 December 2024.

**Source-reported.**
- A course backup is saved with the extension `.mbz`, chosen so it is not confused with `.zip`, in the
  course backup area. File names end in `-nu` when no users are included and `-an` when user data is
  anonymised.
- The first step, *Initial settings*, offers whether to include users, anonymise user information, and
  include role assignments, groups, user files, comments, user completion details, logs and grade history.
- The next step, *Schema settings*, lets the user select or deselect individual items, with a link to show
  options by activity type.

**UNKNOWN.** The archive format of `.mbz` (see S2); whether badges or course completion can be included or
excluded; restoring into an older Moodle version.

**Relevance to Studio.** The B8.1 runbook makes the template backup with users off (step 7.2): S1 names the
"include users" setting and the `-nu` file-name sign of it. *Schema settings* is the documented place to
choose sections and activities, which is how the B8.1 sections-only backup selects only sections 4 and up
(runbook P15c, still to be confirmed by the guide and checked in the lab).

## S2. MoodleDocs 4.4: Backup and restore FAQ

**Citation.** Moodle, *Backup and restore FAQ*, MoodleDocs, Moodle 4.4 documentation.
<https://docs.moodle.org/404/en/Backup_and_restore_FAQ>. Page last edited 16 September 2023.

**Source-reported.**
- `.mbz` stands for "Moodle backup zip". By default the file is a gzip tarball (TGZ); a site setting
  (`$CFG->usezipbackups`) makes it a zip instead. Renaming it lets ordinary tools extract it.
- Passwords are not backed up even when enrolled users are included. `-nu` marks a backup without enrolled
  users.
- **Badges are not backed up if they have not been awarded to at least one user and users are not included
  in the backup.**
- **Restoring a course into an older Moodle version than the one it was backed up on can fail**; the target
  site should be the same version or newer.

**Audit observation.** This is the 4.4 page (the page itself points to newer documentation); no 4.5 or 5.3
FAQ was opened. Whether the badge rule still holds on 5.3 is not shown.

**UNKNOWN.** How course completion criteria are treated in a backup without users.

**Relevance to Studio.**
- **Risk for B8.1 and App-C item 2.** The B8.1 template's badge is *inactive* (runbook step 6.4) and the
  backup is made *without users* (step 7.2). If S2's badge rule holds on 5.3, the template `.mbz` carries
  **no badge**, so a restored template has no badge and the merge test cannot show the badge "intact"
  (PRD §C1.7). The runbook leaves this as LAB (step 8.5); S2 makes it a likely problem to raise with the
  guide **before** the lab session.
- **Version direction.** S2 is the first documentation source for the statement in the B8.1 runbook (P29)
  that a 5.3 backup is not expected to restore on 4.5, which was only the owner's report. It also supports
  module rule 3 (generate the Moodle 4.5 backup format so it restores on 4.5 and 5.3).
- **Reverse import (FR-S-08)** reads a TGZ or zip archive, so the reader must accept both.

## S3. MoodleDocs 4.5: Course restore

**Citation.** Moodle, *Course restore*, MoodleDocs, Moodle 4.5 documentation.
<https://docs.moodle.org/405/en/Course_restore>. Page last edited 5 July 2024.

**Source-reported.**
- At the *Destination* step a backup is restored as a new course or into an existing course.
  Administrators can set separate restore defaults for merging into another course and for deleting the
  course contents first, and can lock them.
- The restore capabilities include `restore:restorecourse`, `restore:restoresection`,
  `restore:restoreactivity`, `restore:userinfo`, `restore:rolldates` and others. The page does not say which
  default roles hold them.
- A command-line script, `admin/cli/restore_backup.php`, is available from Moodle 3.10, intended for large
  backup files.
- A "Restorers' role in courses" setting gives the person restoring a role in the restored course (default
  Teacher).

**UNKNOWN.** Restoring from a newer into an older version (see S2); which default roles hold the restore
capabilities.

**Relevance to Studio.** Merging into an existing course is the documented route the sections-only build
(FR-S-07) relies on (App-C item 2). The CLI script is a documented candidate for the harness restore route
(App-C item 3, Module 2's question; whether it fits the harness is not shown). The capability list is a
starting point for App-C item 10, which still needs the lab.

## S4. MoodleDocs (dev): Backup 2.0 general architecture (OBSOLETE)

**Citation.** Moodle, *Backup 2.0 general architecture*, MoodleDocs developer documentation.
<https://docs.moodle.org/dev/Backup_2.0_general_architecture>. Page last edited 3 May 2022.

**Audit observation.** The page carries banners saying the site is read-only and that the page "should NOT
be seen as relevant or reliable", and points to moodledev.io. It describes the design "at the time of
writing" (Moodle 2.0). **Nothing here is used as a fact about Moodle 4.5 or 5.3.**

**Source-reported (historical).**
- Backups are run by a backup *controller* that holds a *plan* of *tasks*, each with one or more *steps*;
  `moodle2` is described as the main format, preserving the most data between Moodle sites.
- The backup is a directory: `moodle_backup.xml` at the root (versions, a summary of contents, the full
  settings: the "map" of the backup), `files.xml` with a `files/` directory, a `course/` directory,
  `sections/` with one directory per section, and `activities/` with one directory per activity (each with
  `module.xml` and an XML file named after the activity type). `inforef.xml` files record what each part
  uses, so a restore can be selective.

**Relevance to Studio.** This is the only opened source that describes the layout the generator (FR-S-06)
writes and the reverse importer (FR-S-08) reads. Because it is obsolete, the layout is to be confirmed
against a real 4.5 backup before the generator is written: design §12 item 2, §13 row 4.

## S5. Moodle Developer Resources: Backup API

**Citation.** Moodle, *Backup API*, Moodle Developer Resources.
<https://moodledev.io/docs/apis/subsystems/backup>. Version selector at "main (6.0)"; 4.5 and 5.3 versions
exist. Last updated 13 April 2026.

**Source-reported.**
- A course, or part of one, is backed up by running a backup *plan* made of *tasks*, each with one or more
  *steps*. A plugin defines one task for its data; most use a single structure step that writes an XML file
  from the plugin's tables.
- An activity's backup code lives in `backup/moodle2/` in the plugin: a task class (extending
  `backup_activity_task`) and a steps file whose structure step builds nested elements from database
  tables. The task also encodes links to the activity in a portable form, which restore decodes.
- Restore is described on a separate *Restore API* page (not opened for this survey).

**Audit observation.** The page read was the "main (6.0)" version, not the 4.5 or 5.3 version. It confirms
S4's plan/task/step concepts in a current source, but it does **not** describe the file layout inside a
backup.

**UNKNOWN.** The layout of `moodle_backup.xml`, `sections/` and `activities/`.

**Relevance to Studio.** The XML a Studio-generated backup must contain for page, assign, url and label is
whatever those activities' own backup steps write. So the reliable reference for FR-S-06 is a real backup
made by Moodle 4.5 and the activity backup code in Moodle's source, not a hand-written format (design §12
item 2).

## S6. MoodleDocs 4.5: IMS Common Cartridge import and export

**Citation.** Moodle, *IMS Common Cartridge import and export*, MoodleDocs, Moodle 4.5 documentation.
<https://docs.moodle.org/405/en/IMS_Common_Cartridge_import_and_export>. Page last edited 25 February 2026.

**Source-reported.**
- Moodle imports IMS Common Cartridge **1.0 and 1.1 only**; support for 1.2 and 1.3 is tracked as MDL-60803.
  Import uses the normal restore process.
- Export is an "IMS Common Cartridge 1.1" option in the backup settings and produces an `.imscc` file. The
  only activities that can be exported are Forum, Label, External tool (LTI), Page, Quiz (partial support)
  and URL.
- Export is not available when asynchronous backup and restore is enabled.

**UNKNOWN.** The page does not mention assignments, activity completion, availability (restrictions),
grades, marking workflow or badges.

**Relevance to Studio.** Assignments are not in Moodle's export list, and the page says nothing about
completion, restrictions or grades. The LearnOps course pattern depends on all of these (PRD §B1.2: a task
Assignment per week, unlock rules, points, marking workflow). So Common Cartridge, as Moodle supports it,
cannot carry a LearnOps course. This supports generating Moodle's own backup format instead (PRD §C1.5,
design §7).

## S7. 1EdTech: Common Cartridge® standard page

**Citation.** 1EdTech Consortium, *Common Cartridge®*. <https://www.1edtech.org/standards/cc>. No
publication date shown (footer © 2026).

**Source-reported.**
- Common Cartridge is a set of open standards for packaging and exchanging learning materials and
  assessments between learning platforms, and for exchanging links and authorisation for LTI tools.
- Common Cartridge and Thin Common Cartridge **1.4** have reached Candidate Final status; 1.4 adds, among
  other things, LTI line items for grades and QTI 3.0 packages. Versions 1.3 and Thin 1.2 and 1.3 are listed
  under specification documents.
- *Thin* Common Cartridge exchanges only a list of LTI links (for example a digital textbook); the platform
  imports just the manifest.

**Audit observation.** The standard is at 1.3/1.4 while Moodle imports only 1.0 and 1.1 (S6), so even a
newer cartridge would not reach Moodle intact.

**Relevance to Studio.** Confirms that Common Cartridge is designed for exchanging content between
different platforms, not for carrying one platform's full course settings. LearnOps targets one platform
(Moodle 4.5 and 5.3), which is where Moodle's own backup format fits better.

## S8. Open edX: OLX course structure (course-as-code)

**Citation.** Open edX, *What is the OLX Course Structure?*
<https://docs.openedx.org/en/ulmo/educators/olx/directory-structure.html> and *Getting Started with OLX*
<https://docs.openedx.org/en/ulmo/educators/olx/getting-started.html>, Open edX documentation, Ulmo release.
Both pages show a review date of 2025-11-06.

**Source-reported.**
- OLX (Open Learning XML) is Open edX's XML markup for courses. A course can be built in OLX without, or
  alongside, the Studio editor.
- A course is one `course/` directory. `course.xml` can hold a whole course, but Studio exports split it
  into files by container and component, in directories named after the XML tag (`html`, `problem`,
  `video` …), plus `policies`, `static` and other platform directories.
- Courses are exported from Studio as a `.tar.gz`; the extracted files can be kept with source control
  such as GitHub.
- The page documents how Studio *currently* exports; other structures that import today are not guaranteed
  to keep working.

**UNKNOWN.** How a course team reviews or merges OLX changes; any measurement of authoring time.

**Relevance to Studio.** A working precedent for course-as-code on another platform: text files in a
directory, exchanged with the platform as an archive, kept in Git. It matches the B1 package idea (a folder
of `course.yaml` plus Markdown, zip import and export: FR-S-02). Its warning that the platform's own export
format may change is the same risk as design §12 item 1, and supports restore-testing every Studio build
(module rule 1).

---

## What the survey shows for Studio (our synthesis)

1. **Generate Moodle's own backup format, not Common Cartridge.** Moodle's Common Cartridge support cannot
   export assignments and imports only 1.0/1.1 (S6, S7); the course pattern needs assignments, completion,
   restrictions and marking workflow. This supports PRD §C1.5 and design §7.
2. **The backup layout must come from a real backup.** The only layout description is obsolete (S4), and
   the current API page describes how plugins write their part, not the archive (S5). Make a 4.5 backup of a
   small course in the lab and record its structure before writing the generator (design §12 item 2, §13
   row 4).
3. **Version direction is one-way.** Restoring into an older version can fail (S2). Generating the 4.5
   format (module rule 3) is the safe choice; the B8.1 template, built on 5.3, is expected not to restore
   on 4.5.
4. **Raise the badge rule before the B8.1 lab session.** An unawarded badge in a backup without users is not
   backed up (S2, Moodle 4.4 documentation). This affects B8.1 (template badge inactive, users off) and the
   App-C item 2 merge test. To check on 5.3 and to raise with the guide on Issue #55.
5. **Restore routes exist for the harness.** Merge into an existing course and a CLI restore script are
   documented (S3); whether they suit the harness is App-C item 3 (Module 2).
6. **Course-as-code works elsewhere.** Open edX OLX keeps courses as text in Git and exchanges archives
   with the platform (S8), which supports the B1 package approach.

## Gaps (not yet covered)

- Course-as-code has one source (S8). A second, independent source (for example another platform's
  text-based course format, or a published study of authoring courses as code) is still to be found.
- No 5.3 version of the FAQ (S2) or of the backup and restore pages was opened.
- The *Restore API* page (moodledev.io) was not opened.
- No research paper on course authoring time (goal G-1) has been found yet.

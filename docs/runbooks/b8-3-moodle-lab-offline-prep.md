# B8.3 Moodle lab: offline preparation (DRAFT)

> **Status: DRAFT, preparation only. No step in this document has been run on Moodle, and no result is
> claimed.** Written offline on 27 November 2026 for Student 2 (B8.3 owner). It does not replace
> [`b8-1-moodle-build.md`](b8-1-moodle-build.md) or the B8.1 README §7; where they disagree, those, the PRD
> and the guide's answers win. Moodle 5.3 only (decision 0017).
>
> **Not yet seen:** the two Student 2 decision-register files were not available when this was written, so
> nothing here cites them. Check this draft against the UPDATED register before use.

## Status legend (every section below carries one of these)

| Label | Meaning |
|---|---|
| **VERIFIED (no Moodle)** | Run on 27 Nov 2026 on files only: the downloaded B8.1 asset, a scratch copy of it, and the unit tests. No Moodle site was used |
| **PENDING GUIDE APPROVAL** | Must not be started until the guide approves in writing (creating a temporary B8.2 course; how the sections-only variant is made in Release 0) |
| **UNTESTED (Moodle)** | A procedure or screen name that has not been run. Menu labels here are written from the existing runbook or from memory and are **not** verified on Moodle 5.3 |
| **BLOCKED (merged baseline)** | Needs the merged B8.1 + B8.2 backup, which does not exist: the final CK-07 and CK-08 fixtures, and their hashes |

## What exists and what does not

| Item | State |
|---|---|
| B8.1 backup `b8-1-template-course.v1.mbz` | **VERIFIED (no Moodle).** Downloaded from release `testdata-b8-1-v1` on 27 Nov; 12,612 bytes; SHA-256 `d8869a012a39ae869c54f744d6c391387534bdab2389d8a8aecfd5b481c5585d`, equal to the value in `download.py` and `testdata/README.md`. The file is kept out of Git |
| B8.2 `.mbz` | **Does not exist.** Only the package `testdata/b8-2-sample-course/package/`. No B8.2 backup is made or implied here |
| Merged B8.1 + B8.2 baseline | **Does not exist** |
| `scripts/b8_3/ck08_make_fixture.py` | Written and tested offline on a disposable copy of B8.1 (section 2). Its output is a candidate, **not** the final CK-08 fixture |

## 1. Exact completion-criterion structure in the B8.1 backup (VERIFIED, no Moodle)

Read from the released `.mbz` (a gzip tar; 106 members listed in `.ARCHIVE_INDEX`). This agrees with
decision 0003 #18 and its evidence on `main`; it is a second, independent read of the same file. File `completion.xml`:

```xml
<course_completion>
  <course_completion_criteria id="3">      <!-- Final project -->
    <course>7</course>
    <criteriatype>4</criteriatype>          <!-- 4 = activity completion -->
    <module>assign</module>
    <moduleinstance>28</moduleinstance>     <!-- the activity's cmid in THIS backup -->
    <courseinstanceshortname>$@NULL@$</courseinstanceshortname>
    <enrolperiod>$@NULL@$</enrolperiod> <timeend>$@NULL@$</timeend> <gradepass>$@NULL@$</gradepass>
    <role>$@NULL@$</role> <roleshortname>$@NULL@$</roleshortname>
    <course_completion_crit_completions></course_completion_crit_completions>
  </course_completion_criteria>
  <course_completion_criteria id="4">      <!-- Course feedback: module feedback, moduleinstance 29 -->
  <course_completion_aggr_methd id="5..8"> <!-- aggregation methods, criteriatype NULL/4/8/7, method 1 -->
</course_completion>
```

Facts that matter for CK-07/CK-08:

- The criterion carries **no `idnumber`**. It names the activity only by `<moduleinstance>` = the cmid.
  The contract shape `{type, cmid, idnumber}` (decision 0003, lab item 3) therefore gets `idnumber` by
  looking the cmid up: `moodle_backup.xml` `<activity><moduleid>` → `<directory>` →
  `activities/<mod>_<cmid>/module.xml` `<idnumber>`.
- Backup cmids and ids in this file: forum 25 (idnumber NULL), Page 26 `tpl-welcome`, Page 27
  `tpl-sample-guide`, assign 28 `final-project`, feedback 29 `course-feedback`, assign 30
  `tpl-sample-task`. Sections 27–30 (`0`, `Orientation`, `Sample week`, `Final project`).
- Only two activity criteria exist: 28 and 29 (verified in this file).
- **Expected, not verified here:** Moodle assigns new cmids on a restore, so these numbers are not stable
  across a restore. This is why decision 0003 #4 says never to compare cmids between models. The
  merged-baseline restore will show it; until then, never hard-code the numbers, always look them up.

## 2. `ck08_make_fixture.py` design and test (VERIFIED, no Moodle; the result is a candidate only)

Location: `scripts/b8_3/` (not inside `testdata/b8-3-planted-errors/`, which its dataset test scans).

- **Edit:** in `completion.xml`, one criterion (type 4, resolved from `--criterion-idnumber`, default
  `course-feedback`) gets `<moduleinstance>` set to an unused cmid (default: highest cmid in the backup
  + 1000, re-checked against `moodle_backup.xml`, activity folders and `module.xml` ids). The matching
  size in `.ARCHIVE_INDEX` is updated. All other members are copied byte for byte; no activity is deleted.
- **Safety:** the input is only read, never written, and `--out` may not be the input (checked after
  resolving symlinks). Outputs are created with exclusive create, so an existing file or symlink (also a
  dangling one) is refused, and a manifest that fails to write removes the output again. Output is
  deterministic (gzip timestamp 0, headers copied), so the same input gives the same hash. `--new-id` must be
  a positive whole number that no activity uses. Malformed gzip/tar, non-UTF-8 XML, a missing or duplicate
  criterion, a duplicate activity cmid and an invalid manifest all stop with exit 2 and a message, not a
  traceback. The XML is edited as text (one regex replacement), not parsed, so the rest stays byte-identical.
- **Modes:** default build + verify; `--dry-run` writes nothing; `--check` read-only re-verification
  against `OUT.manifest.json`; `--undo` deletes `OUT` and its manifest only if **all** hold: `OUT` is a
  regular file (not a symlink) and is not the `--input` file; the manifest is a valid manifest made by this
  script (label, `final_ck08_fixture: false`, well-formed hashes and ids, output hash different from input
  hash); `OUT` matches the manifest hash; and `OUT` passes the full structural check. It never opens the
  input for writing. Exit 0 ok, 1 check failed, 2 could not run.
- **Known limit:** `--undo` cannot prove who made a file; a hand-made file that has a valid fixture
  structure, a matching hash and a well-formed manifest beside it would be removed. Only point `--out` at
  files in a scratch folder.
- **Manifest:** label SYNTHETIC, `final_ck08_fixture: false`, criterion, old/new id, input and output
  SHA-256, `completion.xml` SHA-256 before and after. No paths, no secrets.

**Offline test (disposable copy of B8.1 in a scratch folder, read-only copy):**

| Check | Result |
|---|---|
| Input SHA-256 before and after | `d8869a01…585d`, unchanged |
| `--dry-run` | printed plan, no file written |
| Build, course-feedback | criterion 4: `moduleinstance` 29 → 1030; output SHA-256 `f8e15a43…34e8` (disposable candidate only) |
| Rebuild to a second path | identical SHA-256 (repeatable) |
| `diff -r` of the two extracted trees | only `completion.xml` line 21 and the `.ARCHIVE_INDEX` size 1862 → 1864 |
| 1030 resolves to an activity? | No (not in `moodle_backup.xml`, no `activities/*_1030`, no `module.xml` id) |
| Original activity 29 / `course-feedback` | still present |
| Overwrite, same path, unknown idnumber | refused, exit 2 |
| Tampered output: `--check` / `--undo` | check fails (exit 1); undo refused (exit 2) |
| `--undo` on a good output | removed output and manifest only |

**Unit tests:** `scripts/b8_3/tests/test_ck08_make_fixture.py`, 11 tests on a tiny synthetic backup built
inside the test (no real `.mbz` needed): dry-run writes nothing; repeatable build; overwrite, same-path and
unknown-idnumber refused; malformed archives (not gzip, gzip of a non-tar, empty, truncated); missing and
duplicate criteria; duplicate activity cmid; bad or used `--new-id`; dangling-symlink output; six kinds of
invalid manifest for `--check` and `--undo`; undo with a forged manifest pointing at the input, and with
`--out` equal to `--input`; undo of a symlink. Every failure test asserts that the input is byte-identical
and nothing was left behind. The real B8.1 run above was repeated after hardening with the same output hash.

**BLOCKED (merged baseline):** the final CK-08 fixture and its hashes. The candidate's hashes belong to the
B8.1 input only; the final fixture comes from the merged backup and will have different hashes.
**Not tested:** restoring the candidate in Moodle, and any checker run (no checker exists). The scripted
edit approved in principle by the guide (issue #232 point 4) is subject to the CK-07 check, which has not
been done.

## 3. CK-07 comparison note (DRAFT; a reasoned note, nothing here was run against a checker)

Sources: decision 0003 #4 (idnumber is the stable identity; never compare cmids between models), #18
(criterion shape) and #21 (`--reference-model`), and `docs/design/checker.md` on `main` (§3.4 table, §11.3).
The sharper CK-07/CK-08 boundary wording ("an unresolved criterion is CK-08's only") is from **open PR #255,
not merged**: treat it as the intended rule, not as settled text on `main`.

- A protected item is identified by **`idnumber`** (`final-project`, `course-feedback`, or a configured
  one) in the reference model (B8.1) and the checked model.
- **Never compare raw `cmid` values across models** (decision 0003 #4).
- CK-07 compares each protected item with the reference model supplied by `--reference-model` (decision
  0003 #21): absent, duplicated, or changed.
- CK-08 resolves each criterion's `cmid` **within its own model**. The fixture keeps the original
  activity and its configuration unchanged, so, **by reasoning, not by a run**, CK-07 has nothing to report.
  Deleting a protected activity is a different case (CK-07 missing, plus CK-08).
- **BLOCKED (merged baseline) and not done:** confirm that CK-07 does not fire on the final fixture, by the
  checker or a hand comparison of `final-project` and `course-feedback` in B8.1 and in the merged backup.
- Open: exactly which configuration fields CK-07 compares is for the checker design, not decided here.

## 4. B8.2 manual-build procedure (DRAFT; PENDING GUIDE APPROVAL; UNTESTED on Moodle)

**Do not start until the guide has approved creating a temporary B8.2 course.** This is a hand build in
a temporary course, because no B8.2 `.mbz` exists (Studio's builder is Release 2). It must never be
presented as a Studio build or an official B8.2 backup.

**This is a proposal, not the documented method.** The owner's confirmed Release 0 method (B8.1 README §7,
issue #55) adds generated sections by hand **inside a restored copy of the template**, then makes the
sections-only backup from that copy. Building in a new empty course, as written below, is a different
route and is one of the things the guide must approve (decision 0010 lists "how the sections-only variant
is made in Release 0" as pending). The B8.1 README route is the fallback if the guide prefers it. Every
Moodle screen name below is from the existing runbook or from memory, not verified on 5.3.

Prerequisites: guide approval recorded (link); permissions audit (section 5) done on your own account;
storage for the resulting `.mbz` agreed (never public, `*.mbz` is gitignored); a test-data-only site.

1. **Preserve B8.1.** Verify the downloaded B8.1 SHA-256. Never restore into or edit the original template
   course. Work only in new, clearly named temporary courses (e.g. `TMP-B82-…`), and write the names down.
2. **Build B8.2 by hand** in a new empty temporary course, from the unchanged package files only (never
   edit `testdata/b8-2-sample-course/`): shortname `SAMPLE-DOC-101`; sections **4 to 7** (leave sections
   1–3 empty or absent as the lab method allows; record what Moodle did); per week one Page
   (`wk-0N-guide`) and one Assignment (`wk-0N-task`), 25 points, completion on submit, `idnumber` exactly
   as in `course.yaml`; week 2–4 unlock after the previous task. Marking workflow and marking tables per
   the task bodies. **Check every idnumber and points value on Moodle's own screens** and keep screenshots.
3. **Keep this course unchanged afterwards** as the clean B8.2 baseline (it is only a Moodle course; its
   backup would be a *lab-built* B8.2 backup, to be labelled as such).
4. **Sections-only backup** (Moodle Backup page, user data off): only sections 4–7 and their activities;
   no protected items. Open the archive and record the users folder / usernames / emails check (README §7
   step 4). Stop and report if any user data appears.
5. **Merge** into a *new* copy restored from the B8.1 `.mbz` (`Restore as a new course`, then in that copy
   `Restore into this course` → `Merge the backup course into this course`, defaults kept).
6. **Before/after tables** for all protected items by `idnumber` (type, name, section number, points,
   completion, visibility), plus the course total target (200, set by the builder, not derived).
7. **Backup the merged copy**, hash it, record Moodle version/build, date, operator.
8. **Clean-up:** delete only test courses you created, after the evidence is checked (README §7); the
   B8.1 template course stays; any other deletion needs the guide's approval.

Evidence to keep (out of Git unless the guide says otherwise): screenshots of each Moodle screen,
before/after tables, SHA-256 of each `.mbz`, exact error text of any refusal.

## 5. Read-only Moodle permissions audit checklist (UNTESTED; own account; changes nothing)

Menu paths and capability names below are from memory and the B8.1 README and are **not verified on this
Moodle 5.3 site**: if a screen differs, write down what you see instead of following this text. Do not
change any role or permission. Record each answer with a screenshot and the date.

| # | Question | How to see it **for your own account** (read-only) | Result |
|---|---|---|---|
| 1 | Who is logged in? Own account or shared? | Profile page: name, username, and ask who else knows the password | |
| 2 | Site-level role(s) held | Profile → "Roles"/Admin → Users → Permissions → *Check system permissions* for your own user | |
| 3 | Can I create courses? | The "Add a new course" entry in Site administration → Courses → Manage courses and categories is shown and opens (do not save) | |
| 4 | Can I restore? | In a course you may use, the **Restore** page opens and offers the upload area (do not restore); or Check permissions → `moodle/restore:restorecourse` | |
| 5 | Can I back up? | The **Backup** page opens (stop before running); `moodle/backup:backupcourse` | |
| 6 | Can I edit course content? | Course → Turn editing on is available in a course you may use; `moodle/course:update` | |
| 7 | Can I delete my own test courses? | Only the presence of the delete icon on a course you created (do not click) | |
| 8 | Are the capabilities effective, not just defined? | Use **Check permissions** on your own user *in the course context*, because a course-level override or prohibit can differ from the role definition | |

Reminder from the B8.1 README: the Manager role can back up, restore and merge but may be refused on a
screen; if so, record the exact message and tell the guide, do not work around it. App-C item 10 covers
which roles hold backup and restore capabilities.

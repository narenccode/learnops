# B8.3 Moodle build runbook (DRAFT)

> **Status: DRAFT, preparation only. This document records no lab verification result.** No step is
> recorded as run, and nothing here has been checked on Moodle 4.5 or 5.3. It turns the expected
> findings in [`testdata/b8-3-planted-errors/expected-findings.yaml`](../../testdata/b8-3-planted-errors/expected-findings.yaml)
> into steps for a person with lab access, to make the real Moodle `.mbz` versions of the planted
> errors. If this document and the PRD, `expected-findings.yaml` or the guide's answers disagree,
> those win. Where a Moodle setting name or menu path is not known, the step says **LAB**: find it
> on the site, then correct this document and record what you found.

## Purpose

Nine rules (ten variants) cannot be written as a course package. Their variants exist today only as
hand-built B2 course models (`models/`, made by `make_models.py`), which are fictional and not
checked against a real backup (decision 0003 §4). This runbook makes the real backups, so the same
planted errors can be checked against what Moodle itself writes. Each real variant keeps the id in
`expected-findings.yaml` (without the `-model` suffix). Making them also settles the open Moodle
questions listed in decision 0003 §4 (availability JSON, `OPTION_PREVIOUS`, criteria shape, section
numbering).

## Rules that apply (do not skip)

- **Test data only, user data OFF** in every backup (PRD C-07, CLAUDE.md rule 4). After each backup, open the `.mbz`, record whether a users folder exists and whether any username or email is in the XML. If any user data is present, stop and report.
- **Never modify Moodle or BigBlueButton** (CLAUDE.md rule 1): use only the site's own pages (course, backup, restore). No plugin, patch or database edit.
- **One planted change per variant**, nothing else. The planted change and its expected finding are in `expected-findings.yaml`; copy them, do not invent others.
- **No secrets** in screenshots, notes or file names (CLAUDE.md rule 3).
- **Record, do not guess.** Write the exact Moodle release, date and every backup setting. A step you could not do is recorded as not done.

## Decisions needed before you start

| # | Question | Who decides | Effect |
|---|---|---|---|
| 1 | Build on Moodle 4.5 and 5.3, or on 5.3 only with a recorded exception (checker design §12 item 22; register: `docs/decisions/README.md`)? | The guide | Doubles the work if both. B8.1 is 5.3 only (decision 0009) |
| 2 | Is the `.mbz` needed for Release 0, or are the course models enough until Release 1? | The guide | If models are enough, this runbook waits |
| 3 | Is the mapping in `expected-findings.yaml` confirmed? | Akshita and the guide | If a planted change moves, update the file in the same PR as the backup |

## Stage 0. Inputs

| # | Item | Notes |
|---|---|---|
| 0.1 | A Moodle site for the lab (version from decision 1) | PENDING MOODLE LAB. Record the release and build |
| 0.2 | A clean course restored from **B8.2** (full mode) | B8.2 is a package; its `.mbz` is made by Course Studio (not built yet) or restored by the agreed route. PENDING: no B8.2 `.mbz` exists. Record how the course was made |
| 0.3 | For CK-07 only: the **B8.1** template `.mbz` and the B8.2 weeks merged into it | B8.1 `.mbz` does not exist yet either (see `docs/runbooks/b8-1-moodle-build.md`) |
| 0.4 | `models/baseline.model.json` | The model of the same course, for comparison. The real course should match its structure |

Before changing anything, make a **clean backup** of the restored course (Stage 2) and keep it. Every
variant starts from the same restored course: after each backup, restore or reset the course to the
clean state so changes do not pile up.

## Stage 1. The variants

Each row is one variant. After the change, make a backup (Stage 2). The check says what the backup
must show.

| Variant id | Rule | Change in the course (**LAB** = find the setting name) | The backup must show |
|---|---|---|---|
| `ck-01-unreachable-by-past-date` | CK-01 | On the Week 3 guide Page, add restricted access: a date condition "until" 1 January 2020 (a date in the past). LAB | An availability JSON on that activity with a date condition in the past |
| `ck-04-unlock-missing-activity` | CK-04 | Week 3 section waits for another activity's completion, then **delete that activity** so the rule points at a missing activity. Use a spare activity added only for this, so the course content stays as in B8.2. LAB: whether Moodle removes the rule on delete; if it does, record that this variant cannot be made in the UI and report it | A section availability naming an activity that is not in the backup |
| `ck-05-circular-unlock` | CK-05 | Week 2 waits for the Week 3 task, and Week 3 already waits for the Week 2 task. LAB: whether Moodle allows a circular rule; record the result either way | Two section availabilities that wait for each other |
| `ck-06-duplicate-idnumber` | CK-06 | Give the Week 2 task the ID number `wk-01-task`. LAB: Moodle may refuse a duplicate; if so, record it and report | Two activities with the same ID number |
| `ck-06-invalid-idnumber` | CK-06 | Give the Week 1 task the ID number `Week 1 Task`. | An activity whose ID number has spaces and capitals |
| `ck-07-protected-item-changed` | CK-07 | In the merged course (Stage 0.3), set the Final project maximum grade to 80 (it is 100 in B8.1). If the marking table is in use, keep it consistent so CK-09 does not fire | The Final project grade item with max 80; checked with `--reference-model` against the B8.1 model |
| `ck-08-completion-criteria-missing-item` | CK-08 | Add a course completion criterion for a spare activity, then **delete that activity**. LAB: whether Moodle removes the criterion on delete; record it | A course completion criterion pointing at an activity not in the backup |
| `ck-10-no-marking-workflow` | CK-10 | In the Week 1 task assignment settings, turn the marking workflow **off**. LAB | The assignment with marking workflow disabled |
| `ck-11-graded-practice-h5p` | CK-11 | Add a practice H5P activity in Week 1 and give it a grade of 10. LAB: H5P activity grade setting | An H5P activity with a grade item |
| `ck-13-unlock-without-completion` | CK-13 | Turn **completion tracking off** on the Week 1 task, while Week 2 still waits for it. LAB | The Week 1 task with completion tracking none, and the Week 2 availability naming it |

If Moodle prevents a change (it removes the rule, refuses a duplicate, or blocks a circular rule),
that is a **finding about Moodle, not a failure**: record exactly what happened, keep the screenshot,
and report it to the checker owner. Do not edit the backup by hand to force the state.

## Stage 2. Backup

| # | Step | Check |
|---|---|---|
| 2.1 | Use the course's Backup page. Turn **user data OFF** and record every other backup setting. LAB: setting names | Screenshot of the settings screen |
| 2.2 | Name the file `b8-3-<variant id>.v1.mbz`, for example `b8-3-ck-10-no-marking-workflow.v1.mbz`. Label it "built on Moodle <release>" | The name matches the variant id |
| 2.3 | Open the `.mbz`. Record whether a users folder exists and whether any username or email appears | None found. If any is found, stop and report |
| 2.4 | Record the SHA-256 and the size | Hash recorded |
| 2.5 | Restore the course to the clean state before the next variant | The next variant starts from B8.2 |

## Stage 3. Compare with the model

For each backup, record whether the real structure matches the hand-built model for the same
variant: the same activities, the same availability condition, the same criteria. Differences are
useful: they show where the contract's assumptions (decision 0003 §4) are wrong. Report each
difference; do not change the model to hide it.

## Stage 4. Delivery

Large binaries stay out of the repository (`.mbz` is gitignored). Follow B8.1: upload each `.mbz`
as a GitHub release asset under a tag (proposal: `testdata-b8-3-v1`; a rebuild gets `v2`, never
overwrite a tag), and fetch them by a download script that verifies the SHA-256. That script does
not exist for B8.3 yet. Then, in one pull request:

1. In `expected-findings.yaml`, change each real entry from `pending-lab` to `built`, with `path` set to the file name, and record the Moodle release and SHA-256 (new fields are additive).
2. Update `testdata/README.md` (B8.3 section) and `docs/traceability.md`.
3. Record the Moodle version and any exception in the register (`docs/decisions/README.md`).

## Stage 5. Cleanup

Delete every course created for a variant once its backup is checked and its hash recorded, the same
rule as B8.1 (P25a). Keep the clean B8.2 backup until the guide says otherwise.

## Evidence checklist (to fill in on the lab day)

- [ ] Moodle release and build, and the date
- [ ] How the clean B8.2 course was made
- [ ] For each of the 10 variants: screenshot of the change, backup settings screen with user data OFF, file name, size, SHA-256, users-folder check
- [ ] For each variant Moodle did not allow: the exact behaviour, screenshot, and who was told
- [ ] The Stage 3 comparison with the model, with every difference
- [ ] Decisions 1 to 3 above, with who decided and when

## What this document does not do

- It does not claim any step was run or any result observed.
- It does not decide the Moodle versions, the delivery tag or the severities; those are the guide's.
- It does not change B8.2, the contracts or the checker.

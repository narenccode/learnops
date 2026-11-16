# B8.1 Moodle build runbook (DRAFT)

> **Status: DRAFT, preparation only. This document records no lab verification result.** None of its
> steps is recorded as run, and no result is claimed. It turns the requirements in
> [`testdata/b8-1-template-course/README.md`](../../testdata/b8-1-template-course/README.md) and the
> owner's answers (Issue #55, 2026-11-07, 2026-11-11, 2026-11-12, 2026-11-13 and 2026-11-14; Issue #65, 2026-11-12; the licence
> answer on Issue #61, 2026-11-11) into steps
> for a person with lab access. If this document and the README disagree, the README, the PRD and the
> guide's answers on Issues #55 and #65 (and, for the licence, Issue #61) win. **The owner's answers are decisions, not test results.** Release 0
> builds and tests on **Moodle 5.3 only** (Owner, the 11-14 reply). Moodle 4.5 is not tested; waived by the guide for Release 0 (decided 2026-11-14, confirmed as a C-03 deviation 2026-11-15; scope B8.1 only); it is
> never recorded as passed. The statement that a 5.3 backup is expected not to restore on 4.5 is the owner's report of
> what Moodle documents (Issue #55, 2026-11-14); it is not verified here, and the PRD does not state it. Scope: B8.1 only. This does not cover B8.2 or the harness: C-03 still applies to the B8.2 generated backups and to FR-C-08, and the B8.2 extension belongs with B8.2 on PR #61, not here.

## How to read this document

| Label | Meaning |
|---|---|
| **PRD** | Stated by `docs/PRD.md` or a `CLAUDE.md` file |
| **Owner** | Confirmed by the guide on Issue #55 or #65 (answers of 2026-11-07, 2026-11-11, 2026-11-12, 2026-11-13 and 2026-11-14), or on Issue #61 for the licence (2026-11-11). The later reply on Issue #55 of 2026-11-12 (14:43 UTC) is cited below as "the 14:43 reply", the reply of 2026-11-13 (09:36 UTC) as "the 09:36 reply", and the reply of 2026-11-14 (12:19 UTC) as "the 11-14 reply" (it replaces the earlier "build on 4.5" decision) |
| **Proposal** | The owner marked it a proposal (or a Draft design document does); it goes into the README as a proposal, not a confirmed requirement |
| **PENDING** | Not decided. Do not guess; wait for the answer and then fill it in |
| **LAB** | A fact only a Moodle site can show. Record what you see; do not copy it from here |

Rules that apply to every step (CLAUDE.md §2):
- Only Moodle's own Backup and Restore, and the browser. Never change Moodle code, plugins, themes or its database (rule 1).
- The project must work on Moodle 4.5 **and** 5.3 (rule 2; PRD C-03), but for Release 0 the template is built and every restore and merge is tested on **5.3 only** (Owner, the 11-14 reply; PRD §E2, C1.7). Moodle 4.5 is not tested; waived by the guide for Release 0 (decided 2026-11-14, confirmed as a C-03 deviation 2026-11-15; scope B8.1 only), and is not recorded as passed. No 4.5 restore is attempted in Release 0; the owner expects a 5.3 backup not to restore on 4.5 (owner's report, P29; not verified).
- No secrets in evidence. Hide tokens, passwords and cookies in screenshots and logs (rule 3).
- Test data only. No real learner data or real course content (rule 4).

Where an exact Moodle menu path or setting name is needed, this document says **LAB**. The repository
does not contain those names, and none are invented here.

## Decisions

Each row names the steps it affects. "Owner (2026-11-12)" means the guide answered on Issue #55 that day.
Items the owner marked "proposal" stay proposals. **Do not treat a Proposal as a requirement.**

### Answered by the owner

| # | Decision | Status | Steps |
|---|---|---|---|
| P1 | Build the template on **Moodle 5.3** (the 11-14 reply replaces the 2026-11-12 decision to build on 4.5). Course full name `Template course`; short name `template`; format Topics (Custom sections). The exact 5.3 point release is read from the site (LAB) | Owner for 5.3 (the 11-14 reply); **Proposal** for the names and format | 0.3, 1.3, 1.5 |
| P2 | Build the template once, on 5.3, and run every restore and the sections-only merge test on 5.3 only. Moodle 4.5 is **not tested; waived by the guide for Release 0 (decided 2026-11-14, confirmed as a C-03 deviation 2026-11-15; scope B8.1 only)**. The owner expects a 5.3 template not to restore on 4.5 (owner's report, P29; not verified). Label the `.mbz` "built on Moodle 5.3" in the README and in the release. If the project later needs the template on 4.5 (PRD C-03), it is rebuilt once on 4.5: the known cost of this decision (see P29) | Owner (the 11-14 reply, which replaces 2026-11-12 and the 14:43 reply on this point). The 4.5 waiver is not a pass | 1.5, 1.6, Stage 9 |
| P3 | Section 1 `Orientation`: Page `Welcome` (`tpl-welcome`). Section 2 `Sample week`: Page `Sample guide` (`tpl-sample-guide`) and Assignment `Sample task` (`tpl-sample-task`). Section 3 `Final project`: the two protected items. The `tpl-` prefix keeps these apart from generated `wk-` ids | Owner (2026-11-12) for the titles, activities and idnumbers. The README and `testdata/README.md` record them as Owner (PR #57, merged 2026-11-13). The number 3 for the protected section is a Proposal (P4b) | Stage 2 |
| P4 | Sections carry **no** `idnumber`; Moodle matches sections by number. The protected section is found by its number (PRD §B1.4). Issue #65 is decided and does not affect B8.1 | Owner (Issue #55 and #65, 2026-11-12) | 2.7 |
| P4b | The protected section number `protected_section` = 3, kept configurable (PRD §B1.4 gives no default) | **Proposal** (Owner, 2026-11-07). The title `Final project` is Owner (P3) | 2.6, 3.1, 4.1, 8.2, 8.3, 9.7 |
| P5 | Everything is visible. No availability rules | Owner (2026-11-12) | 2.8 |
| P7 | The Final project assignment receives the 100 points and is the **only graded item** | **Proposal** (Owner). Do not design around it | 3.5, 3.7, 5.1 |
| P8 | Leave Moodle's default course-total behaviour, so the points count in the course total | **Proposal** (Owner). Do not design around it | 3.7 |
| P9a | Badge description: `Awarded when the template course is completed (placeholder).` Badge image: a plain image generated by the project under Apache-2.0, with no third-party image | Owner (2026-11-12) | 6.5 |
| P10 | Licence Apache-2.0, the same as the repository. Content is fictional and written for LearnOps | Owner (Issue #55, 2026-11-12, referring to the guide's answer on Issue #61, 2026-11-11). Recorded in the README and `testdata/README.md` (PR #57, merged 2026-11-13) | 10.7 |
| P11 | Backup file name `b8-1-template-course.v1.mbz` (the release asset, tag `testdata-b8-1-v1`) | **Proposal** (Owner) | 7.4, 7.7, 10.3 |
| P12 | Download script path `testdata/b8-1-template-course/download.sh` | **Proposal** (Owner). The script does not exist yet | 10.5 |
| P13a | Restores use Moodle's own Restore. PRD §A5 names the site administrator as the role that restores courses. The 2026-11-12 answer said "by the site administrator"; the 11-14 reply replaces that for these lab tests with P13b | Owner (2026-11-12; replaced in part by the 11-14 reply) | 9.2 |
| P13b | The B8.1 owner restores with their own account on the 5.3 lab site, with Moodle's built-in **Manager** role at site level. The Manager role can back up, restore and merge courses and cannot change site settings; a step that needs an administrator screen (for example checking that completion tracking and badges are on) goes to the guide | Owner (the 11-14 reply). The account was not tested on every step: if a restore or merge screen refuses it, write down the exact message and tell the guide on Issue #55; do not work around it | 9.2, 1.1, 1.2 |
| P15a | Release 0 sections-only backup: make it **by hand** with Moodle's own Backup page, from a copy of the template with the protected items removed, and document the steps in the README. Course Studio (FR-S-07, Release 2) replaces this later | Owner (2026-11-12) | 9.6 |
| P15b | For the merge test, the generated sections must use numbers **after section 3**: a merge restore keeps the name and summary of a section that already exists at that number | Owner (Issue #55 and #65, 2026-11-12) | 9.6, 9.7, 9.8 |
| P17 | Decision record `docs/decisions/NNNN-b8-1-template-course.md`. The next free number is taken when you merge, after rebasing (Owner, Issue #55, 2026-11-12). No number is assigned here. Not written yet. The record also holds the short, text-only results table that names the local evidence files (Owner, the 14:43 reply, P21). The results must be in the record before the merge-test course is deleted (Owner, the 09:36 reply, P25a); how the record is held before its number is taken: PENDING (P34) | Owner (2026-11-12, the 14:43 reply and the 09:36 reply) | 9.10, 10.9 |
| P18 | One B8.1 entry in `docs/traceability.md`, following the B1 and B8 pattern: no FR id; cite PRD B8.1 and B1.4 | Owner (2026-11-12). **Done in PR #57, merged 2026-11-13**: every Test(s) cell says "None yet", and the `.mbz`, SHA-256, release asset, download script, decision record and Moodle verification are listed as pending. Updated for the 5.3-only decision in the follow-up documentation change | 10.10 |
| P6 | The Final project assignment is named `Final project`, idnumber `final-project` | Owner (the 14:43 reply) | 3.1 |
| P14 | The manual restore uses Moodle's own Restore page in the browser, with the B8.1 owner's own Manager account (P13b; the 14:43 reply said "as the site administrator" and the 11-14 reply replaces that). The command-line route is the harness's separate question (App-C item 3), not decided here | Owner (the 14:43 and 11-14 replies) | 9.1 |
| P16 | Comparison method for the merge test: before and after the sections-only merge, write down the same table for each protected item, with these fields taken from Moodle's own screens: type, name, idnumber, section number, points, completion setting and visibility. The two tables must be equal | Owner (the 14:43 reply). How the fields apply to the completion criteria and the badge: PENDING (P32) | 8.7, 9.5, 9.8 |
| P21 | Evidence: screenshots and logs stay local and are not committed; check each for personal data first. A short, text-only results table goes in the decision record and names the local evidence files | Owner (the 14:43 reply). Whether the README §8 table is also filled in: PENDING (P33) | Evidence rules, 7.7, 10.6, 12.3 |
| P19 | Lab access is **ready, in person**: use a lab PC and open the Moodle 5.3 lab site in its browser. The guide shows the site address and gives the password in person; **never put a password or an address in a comment, a file or the evidence** | Owner (the 11-14 reply). This is access, not a test result | Stage 0 |
| P22 | Test sites: until the harness approach to fresh sites is decided, use the existing 5.3 lab site. Restore into a new course each time, record the result, and delete the course by the rule in P25a. The site and the account are ready (P19) | Owner (the 14:43 reply; deletion: the 09:36 reply, P25a; site: the 11-14 reply) | 0.4, Stage 9 |
| P25a | Cleanup rule. Every course created for a test is deleted after its result is recorded and checked. The merge-test course follows the merge-test sequence in Stage 9. | Owner (the 09:36 reply). Whether the sections-only copy and failed builds count as courses created for a test: PENDING (P25) | 9.8, 9.10, 12.1 |
| P25b | After deleting a test course, look at whether it stays in Moodle's recycle bin on the lab site, and record what you see. Moodle's documentation says deleted items are kept for a set period (seven days by default) and are then removed automatically; the owner has not checked this on the lab sites. **Do not change the recycle-bin settings**: site settings belong to the owner | Owner (the 09:36 reply). What the lab sites actually do: LAB | 9.11, 12.1 |
| P29 | Version scope: build the template on 5.3 and run every restore and the sections-only merge on **5.3 only**. Moodle 4.5 is **not tested; waived by the guide for Release 0 (decided 2026-11-14, confirmed as a C-03 deviation 2026-11-15; scope B8.1 only)**: record this waiver, with its date and its cost, in the decision record and in README §8, and never as a pass. **Owner's report, not verified here:** the owner states (Issue #55, 2026-11-14) that Moodle documents that a backup restores into the same or a newer version only, so a 5.3 backup is expected not to restore on 4.5. It has not been checked in the lab or against the Moodle documentation for this project, and the PRD does not state it. If PRD C-03 later needs the template on 4.5, rebuild it once on 4.5 and test with the same steps. For each restore, record the Moodle version, the date and the outcome | Owner (the 11-14 reply, which replaces the 14:43 reply on this point) | 1.5, 1.6, Stage 9 |

### Still PENDING

| # | Decision | Steps |
|---|---|---|
| P9b | The placeholder issuer text for the badge; how and where the badge image is generated and its source kept | 6.3, 6.5 |
| P15c | How the copy of the template ends up with sections numbered after 3 (the owner gave the rule, P15b, but not the method), and the exact manual steps | 9.6 |
| P19b | Whether student accounts exist on the lab sites. The 11-14 reply confirms the B8.1 owner's own account only and does not mention student accounts; their readiness is **not confirmed** (PENDING GUIDE CONFIRMATION) | Stage 0 |
| P24 | How a rebuilt backup is versioned and tagged. The tag `testdata-b8-1-v1` is fixed; replacing or deleting a published asset, or moving a tag, needs the owner's approval | 10.3, Stage 11 |
| P25 | Cleanup beyond what P25a settles: whether the sections-only copy and failed builds count as courses created for a test; what else may be deleted (local copies, evidence, wrong release uploads); who authorizes it; and any retention period | Stage 12, 11.6 |
| P26 | Whether the download script supports `--dry-run`, `--check` and a documented undo (CLAUDE.md §2 rule 9, PRD C-05). Nothing about its contents or options is designed here | 10.5 |
| P27 | Body text and other settings (including completion) of `Welcome`, `Sample guide` and `Sample task`; how `Sample task` is left ungraded (the Final project is the only graded item) | 2.2, 2.4, 2.5 |
| P28 | **Feedback anonymity: the owner's answers conflict.** On 2026-11-07, item 2 names the Feedback activity as anonymous ("Moodle's own Feedback activity, anonymous, named ..."). Item 6 of the same reply lists "an anonymous Feedback activity" among the settings the owner said to mark as proposals. Whether anonymity is confirmed or a proposal is **PENDING GUIDE CONFIRMATION** (the README records it the same way). Do not treat it as confirmed | 4.4, Evidence checklist |
| P30 | **Exact contents of the manual sections-only backup** (README §7): whether sections 1 to 3 and their `tpl-` activities are in it; whether the protected section 3 is in the copy or the backup; whether the badge and the completion criteria are removed from the copy ("the protected items removed" is the owner's wording); how the sections to leave out are excluded on Moodle's Backup page; the backup settings and the content of the generated sections | 9.6, 9.7 |
| P31 | The method for checking the finished `.mbz` for users and for real learner data. The README says the check is needed (PENDING MOODLE LAB) but no method has been decided or written, and none is invented here. The check itself needs a Moodle site and the finished file | 8.1 |
| P32 | How the P16 comparison fields apply to the course completion criteria and the badge, which have no section number or points. The owner said "each protected item" and listed the fields; it did not say how to handle these two. No answer is assumed | 8.7, 9.5, 9.8 |
| P33 | Whether the README §8 results table is also filled in, or the results go only in the decision record. The owner asked for a short text-only results table in the decision record; the README does not say either way | 10.6 |
| P34 | **PENDING GUIDE CONFIRMATION.** How the decision record is held before its number is taken at merge. The owner's rule needs the results in the decision record before the merge-test course is deleted (P25a), and the number is taken when you merge, after rebasing (P17). The owner has not said how the two fit together; no numbering or naming convention is assumed here | 9.10, 10.9 |

### Open actions (not decisions)

| # | Action | Status | Steps |
|---|---|---|---|
| A1 | The P16 field list (type, name, idnumber, section number, points, completion setting, visibility) for Shraddha, so that the checker later compares the same fields | Owner's instruction (the 14:43 reply). **Sent to Shraddha** (reported by the B8.1 owner; the message link and date are not recorded here). **Her response and the alignment with the checker: pending**; no confirmation from her is recorded | 8.7 |

## Evidence rules (PRD §E2, §E3)

PRD §E3 requires each result to state the data set, the method, the date and who measured; PRD §E2
and README §8 also ask for the evidence. This runbook adds the Moodle release to that list. Numbers and
outcomes come from what you saw, never from an estimate.

- **Where evidence is kept (Owner, the 14:43 reply, P21):** screenshots and logs stay local, and nothing
  from them is committed. A short, text-only results table goes in the decision record and names the local
  files. Check every file for personal data first (below). Whether the README §8 table is also filled in:
  **PENDING (P33)**. Record, for every restore, the Moodle version, the date and the outcome (Owner, P29).
- Do not add a `.mbz` to the repository (`*.mbz` is gitignored, Owner, Issue #55 item 4). Because the
  file is ignored, `git status` never shows it; see step 7.6 for a check that does.
- **Privacy check before keeping any screenshot or log:** it must contain no personal data, names, email
  addresses, credentials, tokens or cookies (CLAUDE.md rules 3 and 4; PRD C-07, SEC-06). Lab accounts can
  show names or emails. Crop or redact, then look again.

## Where each stage runs

The owner decided (the 11-14 reply, which replaces the earlier "build on 4.5" decision): build the template
on **Moodle 5.3** and run every restore and the sections-only merge test on **5.3 only** (P29). Moodle 4.5
is not tested; waived by the guide for Release 0 (decided 2026-11-14, confirmed as a C-03 deviation 2026-11-15; scope B8.1 only). "Runbook procedure" below means this document's own plan, not an owner decision.

| Stage | Where it runs | Status |
|---|---|---|
| 0. Before you start | On the 5.3 site (records for that site) | Runbook procedure |
| 1. Site and course preparation | Checks 1.1 and 1.2 on the 5.3 site (an administrator screen: ask the guide). The course is built once, on 5.3 | Owner (P29, P13b) |
| 2 to 6. Sections, activities, completion, badge | On the 5.3 site | Titles and idnumbers: Owner. Settings: Proposal, **PENDING** or LAB, as marked per step |
| 7. Backup | Once, on 5.3, giving one build record, labelled "built on Moodle 5.3" | Owner (build once on 5.3, P29) |
| 8. Inspection | On the 5.3 backup, and on the sections-only file once it exists | Runbook procedure |
| 9. Restore and merge | On 5.3 only, always from the same 5.3 backup, on the existing 5.3 lab site: a new course each time, deleted by the rule in P25a. Moodle 4.5: not tested; waived by the guide for Release 0 (decided 2026-11-14, confirmed as a C-03 deviation 2026-11-15; scope B8.1 only) (README §8 shows the waiver in the 4.5 column) | Owner for the site and the 5.3-only scope (P22, P29); the steps are a runbook procedure; the sections-only contents are **PENDING (P30)** |
| 10. Metadata, release and hash | Once, for the released file; results recorded for 5.3 | Runbook procedure; names are Proposals |
| 11. Failure recovery, 12. Cleanup | As needed | Courses created for a test are deleted by the rule in P25a (Owner, the 09:36 reply); the rest of the cleanup scope is **PENDING (P25)** |

---

## Stage 0. Before you start

| Step | Action | Expected | Evidence to capture |
|---|---|---|---|
| 0.1 | Use the lab access the guide has prepared: a lab PC and the browser, your own Manager account on the 5.3 site (P19, P13b). The guide shows the address and gives the password in person | Owner, Issue #55 (the 11-14 reply): the B8.1 owner's access is ready, in person. Access only, not a lab verification result. Student accounts are not mentioned there (P19b). Never record the address or the password | Link to the guide's 11-14 comment |
| 0.2 | Check which pending items (P9b, P15c, P24 to P28 and P30 to P34; P25 only beyond what P25a settles) are answered. P6, P14, P16, P21 and P22 were answered in the 14:43 reply, and P13b, P19 and P29 in the 11-14 reply; all are recorded above. Do not build an item whose decision is PENDING | Each answered item is recorded in the README first | List of answered and open items, with dates |
| 0.3 | Record the exact Moodle release shown on the 5.3 site | PRD §A11: 4.5 (latest point release) and 5.3. The template is built on 5.3 (Owner, the 11-14 reply). Moodle 4.5: not tested; waived by the guide for Release 0 (decided 2026-11-14, confirmed as a C-03 deviation 2026-11-15; scope B8.1 only), so no 4.5 release is recorded | Release string, site name, date, your name |
| 0.4 | Record the state of the 5.3 lab site before you test: site, Moodle release and date. Use the existing lab site and restore into a new course each time (Owner, the 14:43 and 11-14 replies, P22) | The guide prepared the site and the account (P19). PRD §E2 asks for fresh sites for each release; the owner's rule applies until the harness approach to fresh sites is decided | Site, release, date, your name, and the guide's message about the site, with a link. Do not invent how the site was prepared |

## Stage 1. Moodle site and course preparation

| Step | Action | Expected | Evidence to capture |
|---|---|---|---|
| 1.1 | Check that completion tracking is on at site level, on the 5.3 site | Owner (2026-11-11): on in both sites, on by default. **You have not checked it yet.** Checking it needs an administrator screen (Owner, the 11-14 reply): ask the guide (P13b) | Screenshot of the setting, or the guide's answer with a link |
| 1.2 | Check that course badges are on at site level, on the 5.3 site | Owner (2026-11-11): on in both sites, on by default. Not yet checked. Checking it needs an administrator screen (Owner, the 11-14 reply): ask the guide (P13b) | Screenshot, or the guide's answer with a link |
| 1.3 | Create the template course on the **5.3** site | Full name `Template course`, short name `template`, format Topics (Custom sections): **Proposal** (Owner, 2026-11-12). Record the format as Moodle shows it (LAB) | Course name, short name, format and id as created |
| 1.4 | Check completion tracking for this course | Settings: **LAB** (README §5) | Screenshot |
| 1.5 | Build the template once, on 5.3 | Owner (the 11-14 reply, P29): build on 5.3 and run every restore and merge on 5.3. Do not build on 4.5 for Release 0 | The 5.3 site and release used |
| 1.6 | Record the 4.5 waiver | Owner (the 11-14 reply, P29): Moodle 4.5 is not tested; waived by the guide for Release 0 (decided 2026-11-14, confirmed as a C-03 deviation 2026-11-15; scope B8.1 only). The cost the owner states (P29; the owner expects a 5.3 template not to restore on 4.5, not verified) is a rebuild on 4.5 if PRD C-03 later needs it. This is a decision, not a result | The waiver, its date and its link, for the decision record and README §8 |

## Stage 2. Sections and activities

All of this is on the 5.3 site. Titles and idnumbers come from the owner's answer of 2026-11-12.

| Step | Action | Expected | Evidence to capture |
|---|---|---|---|
| 2.1 | Create section 1 titled `Orientation` | Owner. Gives the merge test non-protected content | Screenshot of the course page |
| 2.2 | Add a Page titled `Welcome`, idnumber `tpl-welcome`, to section 1 | Owner. Body text and other settings: **PENDING (P27)**. Content must be fictional, written for LearnOps (Owner) | Screenshot of the activity and its idnumber |
| 2.3 | Create section 2 titled `Sample week` | Owner | Screenshot |
| 2.4 | Add a Page titled `Sample guide`, idnumber `tpl-sample-guide`, to section 2 | Owner. Body text and other settings: **PENDING (P27)** | Screenshot |
| 2.5 | Add an Assignment titled `Sample task`, idnumber `tpl-sample-task`, to section 2 | Owner for the title and idnumber. Whether it is graded: the owner's proposal is that the Final project is the only graded item (**Proposal**, P7), so leave it ungraded as part of that proposal. How to leave an assignment ungraded: **LAB**. Other settings: **PENDING (P27)** | Screenshot of the settings and the gradebook |
| 2.6 | Create section 3 titled `Final project`. It holds the two protected items (Stages 3 and 4) | Owner for the title and for holding the two protected items. The number 3 (`protected_section`) is a **Proposal** (P4b), kept configurable. The protected section is found by its number (PRD §B1.4) | Screenshot |
| 2.7 | Section `idnumber`: set none | Owner (Issue #55 and #65): Moodle sections have no idnumber; sections are matched by number | What Moodle shows for a section |
| 2.8 | Visibility and availability | Everything visible; no availability rules (Owner). Do not add any | Screenshot of the settings used |

## Stage 3. Final project assignment

| Step | Action | Expected | Evidence to capture |
|---|---|---|---|
| 3.1 | Add an Assignment named `Final project` to the `Final project` section (section 3) | Placement in the `Final project` section (Owner, 2026-11-12); the number 3 is a Proposal (P4b). Name: `Final project` (Owner, the 14:43 reply, P6) | Screenshot |
| 3.2 | Set its `idnumber` | `final-project` (PRD §B1.4 default; Owner) | Screenshot of the field |
| 3.3 | Submission: 5 files | Proposal (Issue #55 item 6). Setting name: **LAB** | Screenshot |
| 3.4 | Attempts: 1 | Proposal. Setting name: **LAB** | Screenshot |
| 3.5 | Completion: on grade. **Set the points first (3.7): grade-based completion needs a grade** | Proposal. Setting name and value: **LAB** | Screenshot |
| 3.6 | Rubric: none (a mentor adds one) | Proposal | Screenshot showing no rubric |
| 3.7 | Points: 100 on this assignment. It is the only graded item | **Proposal** (Owner, 2026-11-12). Leave Moodle's default course-total behaviour, so the points count in the course total (**Proposal**; do not design around it). What the default is: **LAB** | Screenshot of the grade settings and the course total |

## Stage 4. Course feedback activity

| Step | Action | Expected | Evidence to capture |
|---|---|---|---|
| 4.1 | Add Moodle's Feedback activity to the `Final project` section (section 3) | Moodle's own Feedback activity (Owner, Issue #55 item 2). Placement in the `Final project` section (Owner, 2026-11-12); the number 3 is a Proposal (P4b) | Screenshot |
| 4.2 | Name it "Course feedback" | Owner | Screenshot |
| 4.3 | Set its `idnumber` | `course-feedback` (PRD default; Owner) | Screenshot |
| 4.4 | Anonymity: set it only after the guide answers P28 | **PENDING GUIDE CONFIRMATION (P28).** The owner's 2026-11-07 answers conflict: item 2 names the activity as anonymous, and item 6 lists "an anonymous Feedback activity" among the settings to mark as proposals. Do not treat it as confirmed. Setting name: **LAB** | Screenshot of the setting, and the guide's answer |
| 4.5 | Completion on this activity | A submitted feedback counts toward course completion (Owner, item 3). Setting: **LAB** | Screenshot |
| 4.6 | Check whether it has a grade item | **LAB**. The Final project must remain the only graded item (Proposal) | Screenshot of the gradebook |

## Stage 5. Course completion criteria

| Step | Action | Expected | Evidence to capture |
|---|---|---|---|
| 5.1 | Set the course completion criteria | Both protected items: final project graded **and** feedback submitted (Owner, item 3; README §5) | Screenshot of the criteria page |
| 5.2 | Check the criteria point to the right items | `final-project` and `course-feedback` (PRD §B1.4) | Screenshot showing both items |
| 5.3 | Note anything Moodle adds by default | **LAB** | Screenshot or note |

## Stage 6. Course badge

| Step | Action | Expected | Evidence to capture |
|---|---|---|---|
| 6.1 | Create a course badge named "Template course badge" | Owner, item 3 | Screenshot |
| 6.2 | Award criteria: course completion | Owner, item 3 | Screenshot of the criteria |
| 6.3 | Issuer | A placeholder issuer (Owner). **The placeholder text: PENDING (P9b).** Use no real person or organization | Screenshot |
| 6.4 | State: inactive in the template | Owner, item 3 | Screenshot showing it is not enabled |
| 6.5 | Description and image | Description: `Awarded when the template course is completed (placeholder).` (Owner, 2026-11-12). Image: a plain image generated by the project under Apache-2.0, with **no third-party image** (Owner). How and where it is generated and its source kept: **PENDING (P9b)** | Screenshot of the badge; a record that the image is project-generated and Apache-2.0 |

## Stage 7. Backup with user data excluded

| Step | Action | Expected | Evidence to capture |
|---|---|---|---|
| 7.1 | Start a backup of the 5.3 template course from Moodle's own Backup page | Moodle's Backup only (CLAUDE.md rule 1) | Screenshot |
| 7.2 | Turn user data OFF | The file contains no users (Owner, item 4; README §3). Setting name: **LAB** | Screenshot of the setting |
| 7.3 | Record every other backup setting | **LAB** (README §3). Change no default without a reason | Full screenshot of the settings |
| 7.4 | Name the file `b8-1-template-course.v1.mbz` | **Proposal** (Owner, 2026-11-12) | File name |
| 7.5 | Record release, backup format version, size and date | **LAB** (README §3) | Values read from the site and the file |
| 7.6 | Keep the file outside the repository folder, or only at a path Git ignores | `*.mbz` is gitignored (Owner, item 4). **`git status` is not evidence either way:** it never lists ignored files, so it cannot show that the file is absent. If the file is inside the repository folder, run `git check-ignore -v <path>` (prints the ignore rule) and `git ls-files <path>` (prints nothing if the file is not tracked) | Output of both commands, or the file's location outside the repository |
| 7.7 | Write the **build record** for this file: exact file name, size, SHA-256, Moodle release (labelled "built on Moodle 5.3"), backup format version, date, who made it | Every later restore and the release refer to this record (see 9.3, 9.5, 10.4) | The build record, kept with the evidence: local and not committed (Owner, the 14:43 reply, P21); name it in the decision record's results table |

## Stage 8. Backup inspection and protected-item verification

| Step | Action | Expected | Evidence to capture |
|---|---|---|---|
| 8.1 | Check the file for users and for real learner data | None (README §3; PRD C-07). Method: **PENDING (P31)** | What you checked and the result |
| 8.2 | `final-project` | 1 Assignment in the `Final project` section, section 3 (a Proposal, P4b) (README §4 list) | What the file shows |
| 8.3 | `course-feedback` | 1 Feedback in the `Final project` section, section 3 (a Proposal, P4b) | Same |
| 8.4 | Completion criteria | 2 at course level: final project, feedback (Owner) | Same |
| 8.5 | Badge | 1 course badge "Template course badge" (Owner). **Whether the `.mbz` carries a badge: LAB** (README §6) | Same |
| 8.6 | Compare with the README §4 list | Same idnumbers, same count, badge and completion criteria (PRD §C1.7) | Expected vs found table |
| 8.7 | Comparison field list for Shraddha (checker owner) | Owner (the 14:43 reply, P16): the field list (type, name, idnumber, section number, points, completion setting, visibility), so that the checker later compares the same fields. **Sent to Shraddha** (reported by the B8.1 owner; A1). **Her response and the alignment with the checker are pending**; no confirmation from her is recorded. How the fields apply to the completion criteria and the badge: **PENDING (P32)** | The message or link, with its date, and her reply when it comes |

## Stage 9. Restore verification on Moodle 5.3 (Moodle 4.5 not tested)

Restore the **5.3 backup** on Moodle 5.3 only (Owner, the 11-14 reply, P29). PRD §E2 asks for restore tests
on 4.5 and 5.3; for Release 0 the 4.5 test is **not tested; waived by the guide for Release 0 (decided 2026-11-14, confirmed as a C-03 deviation 2026-11-15; scope B8.1 only)**, and is never recorded as a pass. Do every
step with the same file. Until the harness approach to fresh sites is decided, use the existing 5.3 lab
site: restore into a new course each time, record the result, and delete the course by the rule in P25a
(Owner, the 14:43, 09:36 and 11-14 replies, P22 and P25a). No 4.5 restore is attempted in Release 0: 4.5 is not tested, and
the owner expects a 5.3 backup not to restore on 4.5 (owner's report, P29; not verified). For every restore, record the Moodle version, the date and the outcome
(Owner).

**Two separations to keep clear:**
- **This is a manual B8.1 procedure.** It is not Module 2's FR-C-08 harness restore route. The route
  chosen for this test (step 9.1) does not decide the harness route. App-C item 3 ("a CLI restore route
  for the harness") is a separate decision for the harness.
- **The sections-only merge test is App-C item 2** (PRD Appendix C: does Moodle Restore merge a
  sections-only backup into a template course without touching protected items). That is a Release 0
  verification. Course Studio's sections-only build (FR-S-07) is **Release 2** and is **not available**
  for this test; do not use it or assume it. The owner's Release 0 method is manual (P15a, step 9.6).

**Merge-test sequence (Owner, the 09:36 reply, P25a).** The merge target is a course restored from the
template, so it is a test course like any other. Once a course is deleted nothing can be re-checked, so the
order is fixed:
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

**Runbook mapping (ours, not the owner's words).** Sequence steps 1 and 2 are step 9.5. The sections-only
backup for step 3 is made first (steps 9.6 and 9.7); steps 3 and 4 are step 9.8; step 5 is steps 9.10 and
10.9; step 6 is step 9.8. How the fields apply to the completion criteria and the badge in step 2:
**PENDING (P32)**.

| Step | Action | Expected | Evidence to capture |
|---|---|---|---|
| 9.1 | Use the restore route for this manual test | Moodle's own Restore page in the browser, with your own Manager account (Owner, the 14:43 and 11-14 replies, P14). The command-line route is the harness's separate question (App-C item 3), not decided here | Which route and role were used (never the password) |
| 9.2 | Confirm the account used to restore | Your own account on the 5.3 site, with the built-in Manager role at site level (Owner, the 11-14 reply, P13b). This is the guide's decision for these lab tests, not something PRD §A5 says (§A5 names the site administrator); which roles hold the backup and restore capabilities by default is App-C item 10, verified separately. If a restore or merge screen refuses it, write down the exact message and tell the guide on Issue #55; do not work around it | The role and any refusal message (never the password) |
| 9.3 | Restore the full template into a new course. **Before restoring, compute the SHA-256 of the exact file you are about to restore and compare it with the build record (7.7)** | The hashes are equal, so the restore tests the file that will be released. Restores without error (README §8). Steps and options: **LAB**. If the hashes differ, stop (Stage 11) | File name, size and SHA-256 of the restored file; log or screenshot of the result and any messages |
| 9.4 | Re-check protected items, completion criteria and badge in that course | Match README §4 to §6 | The 8.6 table, for the restored course |
| 9.5 | Restore the template into a **second, fresh course** to serve as the merge target. Before any merge, record its baseline: the protected items with their idnumbers, the count, the completion criteria and the badge | Same as README §4 (PRD §C1.7 baseline). Write the table described in P16 (Owner, the 14:43 reply): for each protected item, type, name, idnumber, section number, points, completion setting and visibility, taken from Moodle's own screens. How the fields apply to the completion criteria and the badge: **PENDING (P32)**. Steps and options: **LAB**. As in 9.3, check the SHA-256 of the file you restore against the build record (7.7) first | Baseline table for the merge target, dated, before the merge; file name, size and SHA-256 of the restored file |
| 9.6 | Make the sections-only backup by hand (Owner, 2026-11-12): from a **copy of the template with the protected items removed**, using Moodle's own Backup page. **The generated sections must use numbers after section 3** (P15b). How the copy ends up with sections numbered after 3, and the exact steps: **PENDING (P15c)**. What the backup contains: **PENDING (P30)**. This runbook does not repeat the README's draft steps and invents no Moodle menu path. Do not use Course Studio (FR-S-07 is Release 2) | The owner asked for the steps to be documented in the README (Owner). The README already holds a labelled, untested draft (PR #57, merged 2026-11-13); confirm or update it only after the steps have been done in the lab | How it was made, who made it, the Moodle release; the file's name, size and SHA-256 (its own build record) |
| 9.7 | Before merging, check the sections-only backup | PRD §B1.4: sections-only output excludes the protected items (`final-project`, `course-feedback`, or any protected idnumber configured for the site) and their section. Completion criteria and the badge are also protected items under §B1.4 (Studio design FR-S-07 asserts the same, a Draft). **What the manual backup actually contains is PENDING (P30):** whether sections 1 to 3 and their `tpl-` activities are in it, whether section 3 is in the copy or the backup, and whether the badge and completion criteria are removed from the copy. Owner: the **generated** sections use numbers after 3 (P15b), so they do not collide with the protected section (number 3: a Proposal, P4b) or with sections 1 and 2. Do not use these checks to settle the open points; record what you find. How to inspect: **LAB / PENDING (P15c)** | Result of each check, with what you looked at. If a protected item or the protected section is present, do not merge (PRD §B1.4). For the points in P30, record what you found and ask the guide |
| 9.8 | Merge the sections-only backup into the merge target from 9.5 | Protected items unchanged: same idnumbers, same count, badge and completion criteria intact (PRD §C1.7, App-C item 2). A merge keeps the name and summary of a section that already exists at that number (Owner), which is why the numbers must be after 3. Result: **LAB** | The same table again after the merge, with the P16 fields from Moodle's own screens, set beside the 9.5 baseline. The two tables must be equal (Owner, the 14:43 reply). If the tables differ, keep the course and report the difference on Issue #55 before taking further action (merge-test sequence, step 6): it means the merge changed a protected item (Owner, the 09:36 reply) |
| 9.9 | Record what the merge did to the badge and completion criteria | **LAB** (README §5, §6) | Same |
| 9.10 | Record and check each result, then delete the course (Owner, the 09:36 reply, P22 and P25a). Every course created for a test is deleted after its result is recorded and checked. The merge-test course follows the merge-test sequence above. **For the merge-test course, the results must be in the decision record before it is deleted:** put the text-only results table there, with the names of the local screenshots and logs (Owner, P17). Anything else (the sections-only copy, failed builds, local copies): see Stage 12; nothing else is deleted until the scope and authorization are decided (**PENDING, P25**) | How to delete a course: **LAB** (README §7). The record's number is still taken when you merge, after rebasing (P17); how the record is held before then: **PENDING (P34)** | The cleanup log (Stage 12); the results table in the decision record, written before the deletion |
| 9.11 | After deleting a test course, check whether it stays in Moodle's recycle bin on that lab site, and record what you see | Owner (the 09:36 reply, P25b): Moodle's documentation says deleted items are kept for a set period (seven days by default) and are then removed automatically; the owner has not checked this on the lab sites. What this lab site does: **LAB**. **Do not change the recycle-bin settings**: site settings belong to the owner | Site, release, date, the course deleted, whether it appears in the recycle bin and what the page shows about how long it is kept. Local note or screenshot, checked for personal data first |

## Stage 10. Metadata, release and hash

| Step | Action | Expected | Evidence to capture |
|---|---|---|---|
| 10.1 | Compute the SHA-256 of the final `.mbz` | One value, equal to the build record (7.7) and to the hash recorded for every restore (9.3, 9.5) | The hash string |
| 10.2 | Record the build metadata for the README: Moodle release, backup format version, file size, date and SHA-256 (README §1 and §3; `testdata/README.md`) | Values read from the build record, not typed from memory. The README edit goes in a pull request; this runbook does not edit it | The values, and the PR link |
| 10.3 | Upload the file as a GitHub release asset named `b8-1-template-course.v1.mbz` (Proposal) | Tag `testdata-b8-1-v1` (Owner). **If this tag or asset already exists, do not overwrite, delete or replace it, and do not move the tag.** Ask the owner first (**PENDING, P24**) | Release link; the name of the uploaded asset |
| 10.4 | Download the released asset and compute its SHA-256. Compare it with the build record (7.7) and with the hash recorded for each restore (9.3, 9.5) | All equal. If any differs, the restore tests do not apply to the released file: go to Stage 11 | Table: source of each file, its name, and its SHA-256 |
| 10.5 | Run the download script once it exists, and check it gives the same SHA-256. The path is `testdata/b8-1-template-course/download.sh` (Proposal, Owner). **The script does not exist; this runbook does not design it or assume any command or option.** Check whether it supports `--dry-run`, `--check` and a documented undo (CLAUDE.md §2 rule 9, PRD C-05), and record what it actually does. **If it does not support one, mark it PENDING (P26). Do not claim support that was not seen** | Same hash (README §8). Behaviour of each option: **PENDING (P26)** until the script exists and has been run | Hash printed by the script; for each option, what you ran and what happened (or "not supported") |
| 10.6 | Fill in the README §8 table | For 5.3: release, restore, protected items, merge. Leave the 4.5 column as "Not tested; waived by the guide for Release 0 (decided 2026-11-14, confirmed as a C-03 deviation 2026-11-15; scope B8.1 only)", never a pass | Data set, method, date, evidence, who measured (PRD §E3). Where the evidence is kept: local, not committed (Owner, the 14:43 reply, P21). The owner also asked for a short, text-only results table in the decision record, naming the local files. Whether this README §8 table is filled in as well: **PENDING (P33)** |
| 10.7 | Check the licence and source records | Already recorded in the README and `testdata/README.md` (PR #57, merged 2026-11-13): Apache-2.0, the same as the repository; content is fictional and written for LearnOps; badge image generated by the project under Apache-2.0, no third-party image (Owner, Issue #55, 2026-11-12, referring to the answer on Issue #61, 2026-11-11). At release time, check that both files still say this. Still open: how and where the badge image is generated and its source kept (**PENDING, P9b**) | The two README lines as they stand at release time; the record of the badge image |
| 10.8 | Give the checker owner the `.mbz`, its SHA-256 and the README §4 list | README §8 checklist; Owner, item 7 | Message or PR link |
| 10.9 | Record App-C item 2 in `docs/decisions/` | `docs/decisions/NNNN-b8-1-template-course.md`. The next free number is taken when you merge, after rebasing (Owner, Issue #55, 2026-11-12; same as P17). No number is assigned here. Include the short, text-only results table, naming the local evidence files (Owner, the 14:43 reply, P21). Only results that were really recorded; never estimated. The merge-test results must be in the record before that course is deleted (step 9.10, Owner, the 09:36 reply), so the results table is started in Stage 9 and finished here (runbook mapping, not the owner's words). How the record is held before its number is taken: **PENDING (P34)**; no numbering or naming convention is assumed | The decision file |
| 10.10 | Check the B8.1 entry in `docs/traceability.md` | Already added in PR #57, merged 2026-11-13: no FR id; cites PRD B8.1 and B1.4 (Owner); every Test(s) cell says "None yet". Update it only if a test or a result is added | The entry as it stands, and the PR link |
| 10.11 | Confirm or update the README's sections-only steps | The owner asked for them to be documented there (P15a). The README already holds a labelled, untested draft (PR #57, merged 2026-11-13). Update it only after the steps have been done in the lab (step 9.6) | The README section, in a PR |

## Stage 11. If a check fails: rebuild, re-hash and re-tag

These steps are a **runbook proposal**, not a guide decision. Versioning and tagging are **PENDING (P24)**.

| Step | Action | Expected | Evidence to capture |
|---|---|---|---|
| 11.1 | Stop at the first failure (a hash mismatch in 9.3, 9.5 or 10.4, a failed inspection in Stage 8, a failed restore or merge in Stage 9). Record what failed, where, and any message | Nothing is retried silently | What failed, the file name and SHA-256, the site, the date |
| 11.2 | Decide whether the template course must change. Make any change in the Moodle course on 5.3 and take a **new** backup (Stage 7). Do not alter the existing file | A changed file gets a new SHA-256 | The reason for the rebuild |
| 11.3 | Give the new backup its own build record (7.7): file name (**PENDING, P24**: `b8-1-template-course.v1.mbz` is already the name of the first file), size, SHA-256, release, date | A different file from the failed one, with a different SHA-256 | The new build record |
| 11.4 | Repeat Stages 8 to 10 for the new file. Earlier results do not carry over to it | Every restore and the release refer to the new SHA-256 | A fresh set of evidence for the new file |
| 11.5 | Tagging. If `testdata-b8-1-v1` has **not** been published, use it as the Owner said. If it **has** been published, do not overwrite the asset, delete it or move the tag. Ask the owner how a rebuilt file is versioned and wait for approval | **PENDING (P24).** No new tag name is chosen here | The owner's answer, with a link |
| 11.6 | A wrong or incorrect upload: do not delete or replace it yourself. Tell the owner what was uploaded and why it is wrong | Removal needs the owner's authorization (**PENDING, P25**) | The message to the owner and the reply |

## Stage 12. Cleanup

Every course created for a test is deleted after its result is recorded and checked (Owner, the 09:36
reply, P25a). The merge-test course is deleted last of all, by the rule in P25a and step 9.10. Nothing
else here is deleted until the scope, who authorizes it and any retention period are decided
(**PENDING, P25**). README §7 lists how to delete a course as PENDING MOODLE LAB. Keep a log of
everything you create, as you create it, so cleanup is possible. Delete only what you created. After each
deletion, check the recycle bin (step 9.11) and change no recycle-bin setting.

| Step | Action | Expected | Evidence to capture |
|---|---|---|---|
| 12.1 | Temporary lab courses (restored test courses, merge targets, the copy used for the sections-only backup, failed builds): list each one with its site, course id, who created it and the date. Each course created for a test, including the merge target, is deleted by the rule in P25a (Owner); for the sections-only copy and failed builds, delete only after authorization | Test restore courses and the merge target: Owner (P25a). Whether the sections-only copy and failed builds count as courses created for a test, and the authorization: **PENDING (P25)**. Never delete the template/build course or anything another person made without asking | The creation log, and for each deletion: what, when, by whom, authorized by whom |
| 12.2 | Local backup copies of the `.mbz` (including failed builds and sections-only files): list where each is. The released asset is the master copy once it exists. Which copies to keep, and for how long: **PENDING (P25)** | Nothing deleted before the release hash check (10.4) is done | The list, and what was removed |
| 12.3 | Local evidence files (screenshots, logs, tables): keep them local and never commit them (Owner, P21). Check each for personal data first. Name them in the decision record's results table | Keeping them local: Owner (P21). How long they are kept, and whether any are deleted: **PENDING (P25)** | What was kept or removed, and where |
| 12.4 | Incorrect release uploads: see 11.6. Do not delete or replace an upload without the owner's authorization | **PENDING (P25)** | The owner's authorization |
| 12.5 | Write the cleanup record | Complete log: what was removed, when, by whom, authorized by whom | The record |

## Evidence checklist

Tick each when captured. A blank box means no evidence exists. Lab access being ready (P19) is not evidence of any check, and ticks no box below. The two ticked items under Stage 10
are documentation work already done in PR #57, merged 2026-11-13; they are not Moodle evidence.

**Stage 0 and 1**
- [ ] Guide's 11-14 comment saying the B8.1 owner's access is ready (link; no address or password). This is access, not lab evidence; keep it separate from the checks below
- [ ] Moodle release string, 5.3 site
- [ ] Site, release and date for the 5.3 lab site, and the guide's message about the site (P22, P19)
- [ ] Every screenshot and log checked for personal data, names, email addresses and credentials
- [ ] Completion tracking setting, 5.3 site (administrator screen: ask the guide)
- [ ] Course badges setting, 5.3 site (administrator screen: ask the guide)
- [ ] Course name, short name, format and id on the 5.3 site

**Stage 2 to 6**
- [ ] Course page showing sections 1 to 3 with their titles
- [ ] `Welcome`, `Sample guide` and `Sample task` with their idnumbers; `Sample task` not graded
- [ ] Evidence that no section has an idnumber, and that everything is visible with no availability rules
- [ ] `final-project` Assignment settings (files, attempts, completion, rubric, 100 points, course total)
- [ ] Gradebook showing the Final project as the only graded item
- [ ] `course-feedback` Feedback settings (completion, grade item; anonymity only after the guide answers P28)
- [ ] Course completion criteria page
- [ ] Badge: name, description, criteria, state, issuer (after P9b), image and its Apache-2.0 record

**Stage 7 and 8**
- [ ] Backup settings screen with user data OFF
- [ ] Build record for each backup file: name, size, SHA-256, release, backup format version, date, who (step 7.7)
- [ ] Output showing the file is outside the repository or ignored (`git check-ignore -v`, `git ls-files`) (step 7.6)
- [ ] Check for users and learner data
- [ ] Expected-vs-found table for the protected items

**Stage 9**
- [ ] File name, size and SHA-256 of the exact file restored, for each restore, matched to the build record (steps 9.3, 9.5)
- [ ] Restore result on 5.3 (log or screenshot, messages), with the Moodle version, the date and the outcome of each restore. Moodle 4.5: not tested; waived by the guide for Release 0 (decided 2026-11-14, confirmed as a C-03 deviation 2026-11-15; scope B8.1 only) (record the waiver; no 4.5 restore is attempted)
- [ ] Protected-item check after restore, 5.3 site
- [ ] Baseline table of the merge target before the merge, 5.3 site, with the P16 fields (step 9.5)
- [ ] Each course created for a test deleted by the rule in P25a, logged (steps 9.10, 12.1); the merge-test course last, after the decision-record entry
- [ ] Recycle-bin observation after each deletion: whether the deleted course stays in the recycle bin and what the page shows; no recycle-bin setting changed (step 9.11, P25b)
- [ ] How the sections-only backup was made, and the steps for the README (step 9.6, P15c)
- [ ] Result of the step 9.7 checks, and what the sections-only backup actually contains (sections, protected items, protected section, badge, completion criteria): the open points in P30
- [ ] Merge before-and-after tables with the P16 fields; the two tables are equal (5.3 site). If they differ: the course is kept and the difference is reported on Issue #55 before taking further action (merge-test sequence, step 6)
- [ ] Badge and completion criteria after the merge

**Stage 10**
- [ ] Metadata for the README (release, backup format version, size, date, SHA-256) and the PR that records it (step 10.2)
- [ ] Release link under tag `testdata-b8-1-v1`, and the owner's approval if the tag or asset already existed
- [ ] Hash table: build record, each restore, downloaded asset, all compared (step 10.4)
- [ ] Download-script output with the same hash, and for `--dry-run`, `--check` and undo: what was run and seen, or "not supported" (step 10.5)
- [ ] Filled README §8 table (data set, method, date, evidence, who measured), if P33 says it is wanted
- [ ] Short, text-only results table in the decision record, naming the local evidence files (Owner, P21); the merge-test results are in it before that course is deleted (step 9.10, P25a)
- [ ] Comparison field list sent to Shraddha (A1: sent; keep the message link and date). Her response and the alignment with the checker: pending; no confirmation from her is recorded
- [x] Licence and source recorded in the README and `testdata/README.md` (PR #57, merged 2026-11-13; check again at release time, step 10.7)
- [ ] Hand-off message to the checker owner
- [ ] Decision record `docs/decisions/NNNN-b8-1-template-course.md` (not written yet)
- [x] B8.1 entry in `docs/traceability.md` (PR #57, merged 2026-11-13; every Test(s) cell says "None yet")
- [ ] README sections-only steps confirmed or updated after the lab run (a labelled, untested draft is in the README, PR #57, merged 2026-11-13)

**Stage 11 and 12 (only if they happen)**
- [ ] Failure record: what failed, where, file name and SHA-256 (step 11.1)
- [ ] New build record and a fresh set of evidence for any rebuilt file (steps 11.3, 11.4)
- [ ] Owner's answer on versioning and tagging, with a link (step 11.5)
- [ ] Owner's authorization for any removal of an upload (steps 11.6, 12.4)
- [ ] Creation log for temporary lab courses, local copies and evidence files, and the cleanup record (Stage 12)

## What this document does not do
- It records no result and claims no Moodle verification. The owner's statements (for example the expectation that a 5.3
  backup will not restore on 4.5, or that 4.5 is waived by the guide for Release 0 (decided 2026-11-14, confirmed as a C-03 deviation 2026-11-15; scope B8.1 only)) are decisions or Moodle facts reported
  by the owner, not verified and not checks done here.
- It keeps every Proposal a proposal and every PENDING item open until the guide answers.
- It does not design the download script or assume any command or option for it.
- It does not change the README, a contract, the traceability file, a decision record or any other file.
  When a decision arrives, update the README first, then this runbook.

# 0003: B2 Course Model Decisions

**Status: Draft contract. Freeze candidate for Release 0, pending the required approvals and merge of the pull request. Not yet approved or frozen.**

This document records the decisions and outstanding verification items for Contract B2 (`learnops.course-model/v1`).

## 1. Confirmed by the Guide

| # | Decision |
|---|---|
| 1 | Schema: `contracts/course-model.v1.schema.json`. Examples: `contracts/examples/course-model.v1/`. PRD B2 references the schema filename. |
| 2 | Contract decisions are recorded here. `docs/traceability.md` is reserved for requirement traceability. |
| 3 | Schema identifier is `learnops.course-model/v1`. Changing it is a breaking change requiring v2. Within v1, only optional fields may be added. |
| 4 | `cmid` is required. It represents a Moodle course-module ID. Never compare CMIDs between models; `idnumber` is the stable identity. Package-derived models use synthetic positive CMIDs numbered from 1 in document order. Never use 0 or -1. Synthetic CMIDs have meaning only within their own model. |
| 5 | In availability rules, `cm = -1` represents Moodle's `OPTION_PREVIOUS`, not a real CMID. It resolves to the nearest earlier activity in course order whose completion tracking is manual or automatic. Activities with no completion tracking are skipped. If no eligible activity exists, the condition cannot be met. An unresolved `-1` is reported as CK-04. Course order is section order followed by activity order within each section. |
| 6 | Activity types use B1 names. Exact Moodle-to-B1 mapping: `assign` → `assignment`, `h5pactivity` → `h5p`, `page` → `page`, `url` → `url`, `label` → `label`. The raw Moodle aliases `assign` and `h5pactivity` are rejected in `type` (schema `not` / `enum`), so each activity has one spelling. The mapping is applied before any rule: a source `assign` is checked as `assignment`, so the marking-workflow and marking-table fields that the schema requires for `assignment` apply to it. Every other activity type (for example `quiz`) retains Moodle's module name unchanged and stays structurally valid: `type` remains an open string, not an enum, so the checker reports it as "not checked" and never silently skips it (PRD C2.8). |
| 7 | `visible` and `completion_enabled` keys are always present and may be null. Null means the source does not specify the value; it never means false. A null never gives a finding; the checker reports the affected rule as `not checked` (decision in section 3, report state). |
| 8 | Unlock dates are Unix timestamps. Package dates are converted to 00:00 in the configured site timezone. The timezone name is recorded in the model. The lab/default Indian configuration uses `Asia/Kolkata`. |
| 9 | CK-07 uses no fingerprints. Protected items are compared field by field against a supplied reference model of the template course, consistent with FR-C-05. B2 cannot inspect body text or attached files. |
| 10 | Unknown fields are accepted unless the contract explicitly prohibits them, consistent with EXT-02 and A9. |
| 11 | `source.timezone` is required and non-null for package-derived models. For `.mbz` models, it must be null because Moodle backup `course.xml` has no timezone field and its timestamps are absolute Unix timestamps. |
| 12 | `source.kind` is a closed set: `mbz` or `package`. |
| 13 | Completion tracking is a closed set: `none`, `manual`, and `automatic`, corresponding to Moodle values 0, 1, and 2. |
| 14 | Section `idnumber` is nullable. Moodle's `course_sections` table has no `idnumber` field; `.mbz` models therefore use null, and sections are matched by section number. |
| 15 | `marking_table` has the shape `{present, points_total}`. It does not contain a `valid` field; marking-table validity is the responsibility of CK-09. |
| 16 | `media_refs` is optional. v1 scope (guide, [issue #232, comment of 2026-11-26](https://github.com/narenccode/learnops/issues/232#issuecomment-7176861868), point 6; the scope is the one listed on that issue from Akshita's clarification): it holds the embedded-media references found in activity bodies. Covered: Markdown images (inline and reference-style); HTML `img` (`src`, `srcset`), `video` (`src`, `poster`), `audio` (`src`), `source` (`src`, `srcset`) and `track` (`src`), including HTML bodies from `.mbz` backups. **Extraction:** `media_refs` lists every in-scope reference as written, including relative paths, Moodle `@@PLUGINFILE@@/...` references and `data:` URIs; each URL of an `srcset` is its own entry without its descriptor; raw HTML inside a package's Markdown body is in scope. Ordinary links (including PDF links) and `iframe` embeds are not in scope: they are not listed and not checked in v1. **Flagging** is a separate rule: CK-12 flags only the decided full fixed URL forms, `http://`, `https://` and protocol-relative `//host/`; relative paths, `@@PLUGINFILE@@/...` references and `data:` URIs are listed but not flagged; other URI schemes are an open decision (section 3). The listing reading is Akshita's, as the affected M1 owner ([issue #232, comment of 2026-11-26](https://github.com/narenccode/learnops/issues/232#issuecomment-7183976351)), of the description's wording "as written"; the guide's decision states only that `data:` URIs are not flagged and that `@@PLUGINFILE@@` paths pass. If `media_refs` is absent, CK-12 cannot judge the corresponding media references. One shared extractor in the FR-C-01 model builder fills the list and Course Studio reuses it; it is not implemented by this change. This is a small `/contract-change` to the `media_refs` description only (PRD B2 does not name `media_refs`, so no PRD text changes). The shared CK-12 test vectors are in `contracts/test-vectors/media-refs.v1.json` (24 cases), with data-only checks in `libs/contracts/tests/test_media_refs_vectors_v1.py`; they are not an extractor, and the extractor must pass them. One point stays undecided and is recorded as an open-point case that leaves only the flagging null: whether CK-12 flags a URI scheme other than `http:`, `https:` and `data:` (section 3). Akshita confirmed the scope on issue #232; her formal approval of this `/contract-change` is given on the pull request and is not recorded in this decision. |
| 17 | `course.total_points` is optional. For a package-derived model (`source.kind = package`), it carries the package's declared `total_points`; when that value is absent or null, CK-03 uses the B1 default of 100. For an `.mbz`-derived model (`source.kind = mbz`), it carries a target only when an independent target is supplied to the model builder. An absent or null value means there is no independent target and CK-03 returns `cannot judge`; the checker must not apply the package default or derive a target from the computed gradebook total. |
| 18 | The criterion shape `{type, cmid, idnumber}` is confirmed for a course-completion criterion that refers to an activity, by reading the published Moodle 5.3 B8.1 backup (guide, [issue #232, comment of 2026-11-26](https://github.com/narenccode/learnops/issues/232#issuecomment-7176861868), point 1; no lab visit). The evidence is in section 4. Badge criteria in that backup refer to a course, not to an activity, so they carry `type` only, with `cmid` and `idnumber` null; no badge criterion that refers to an activity is in that backup, so that case is not verified. |
| 20 | `source.timezone` is also checked at run time, because a JSON Schema cannot check a time-zone name. The schema keeps its structural rules (decisions 11 and 14). A name is valid when `zoneinfo.ZoneInfo` resolves it, which accepts `Asia/Kolkata`, aliases such as `Asia/Calcutta`, `UTC` and `Etc/GMT-5`, and rejects `UTC+5:30` and `Mars/olympus`. The configuration variable is `SITE_TIMEZONE`, listed in `.env.example` with `Asia/Kolkata` as the lab value. There is no default in code: a package-derived model needs the variable and fails closed when it is missing or invalid. A `.mbz` model still stores null. `tzdata` is pinned in the root `requirements.txt` (Apache-2.0) for systems without a time-zone database, such as Windows. The public entry point is `validate_course_model(doc)` (guide-confirmed): it validates the B2 schema, runs this run-time check and returns the existing `ValidationReport`, so a consumer cannot bypass the check. `timezone_issues()` is the helper it uses, not the entry point. The model builder does not exist yet (FR-C-01, Release 1): it must read `SITE_TIMEZONE` with `site_timezone(os.environ)`, store the result in `source.timezone` and validate the model with `validate_course_model()`. Shared code: `libs/contracts/timezones.py`. |
| 21 | CK-07 reference model (design decision; the checker does not exist yet). The reference is the B2 course model of the B8.1 template course, built from its `.mbz` backup. It is supplied per run with the checker option `--reference-model <path>`, not through an environment variable. When no reference model is supplied, CK-07 reports `not checked` for that run, not a fault, and the report says the protected items were not compared. This refines decision 9. Recorded in `docs/design/checker.md` risk 11. |
| 22 | `source.mode` is required for every source. Its values are `full` and `sections-only`, which come from PRD B1.4. A package source may use either. A `.mbz`-derived model must use `full`: the mode is the output mode, and a backup represents a whole course. The schema enforces this with the `if/then` rules on `source.kind` (`mode` required for both kinds, `const: full` for `.mbz`), and `from-mbz.json` states `"mode": "full"`. |
| 23 | Unlock rules for a course package, by mode (B1.2 rule 2; guide-confirmed on 2026-11-15). Sections are numbered in document order; the section number, `idnumber` and title are never read to decide which section is previous. An absent `unlock` equals `after: null` and `start_date: null`, and `start_date` never replaces `after`. **Full mode:** the first section must have `after` null, because a non-null value cannot name an earlier activity. Every later section must have `after` naming the previous task, which is the single assignment of the immediately preceding section; that section must hold exactly one assignment, and the validator reports the section when it holds none or more than one. **Sections-only mode:** every listed section must have `after`, a single-section package included, because a template already has the first week and a later week names the template's previous task. A well-formed reference to an activity outside the package is accepted. A reference to an activity of a later section of the package is rejected (decision 24 covers the section's own activities). After the merge, a name that matches nothing is CK-04 and a loop across sections is CK-05; those are checker rules and the contract library does not implement them. **Section-level `cm = -1`** follows decision 5 and resolves strictly before the section: the nearest earlier activity with manual or automatic tracking, which is the last tracked activity of the preceding sections. An activity inside the current section is never previous for its own section; it is still provisional until the Moodle lab check. Nested availability groups: B2 stores Moodle's availability object and does not constrain its nesting; reading groups recursively is an implementation detail of `libs/contracts/availability.py`. Shared code: `check_unlock_rules()` in `libs/contracts/course_rules.py`. |
| 24 | A sections-only section must not reference an activity of its own section. The guide: "A reference to an activity in the same section is not an earlier activity; the sections-only exception is for an activity outside the package, not one at or after the section." The validator rejects it, wherever the activity sits in that section, with the same issue as a reference to a later section. CK-05 still covers cycles across sections. |
| 25 | CK-03 uses an independent grading target (guide-confirmed, 2026-11-16). For a package model, the target is the package's declared `total_points`, with the B1 default of 100 only when the package omits it. For an `.mbz` model, including a merged course, the independently declared target is supplied to the model builder as a separate input and must be written to `course.total_points`; a merged course remains `source.kind = mbz`. The target must never be derived from the gradebook items being checked. If no independent target is supplied, `course.total_points` remains absent or null and CK-03 returns `cannot judge` (no default of 100 for `.mbz`). The merged target includes the final project because it is part of the merged course; the intended merged total must be declared before testing when the package adds graded points. CK-03 sums `grade_item.max_grade` for graded activities, excludes ungraded activities, and compares the sum with the independent target. Its report includes the target, calculated sum, difference and items counted. This decision confirms the target handoff and calculation semantics; it does not define a builder API or input mechanism. |

## Checker implementation clarification

This clarifies decision 6. It is the checker owner's clarification and is not a new decision confirmed by the Guide. It rests on PRD B1.4 and on the Guide's comment of 2026-11-15 that a protected item is defined by its `idnumber`.

- A protected item is identified by its `idnumber` (`final-project`, `course-feedback`), independently of its activity `type`.
- The example course feedback item has `type: feedback`, which has no mapping in the activity-type mapping of decision 6.
- CK-07 can still identify that protected item by its `idnumber`.
- "Not checked" applies to unsupported activity-level rules for an activity type. It does not apply to CK-07's independent identification of protected items.
- B1.4 behaviour is unchanged.

## 2. Confirmed by Student 1

| # | Decision |
|---|---|
| 19 | B1 `completion: submit` maps to B2 `{tracking: automatic, submit: true}`. This represents automatic activity completion satisfied when the learner submits the assignment. This confirms the intended B1 requirement semantics, not the exact Moodle implementation. |

B2 examples and tests must preserve this mapping.

## 3. Open Decisions

The following items have not yet received explicit confirmation:

| Item | Current draft | Outstanding question |
|---|---|---|
| Other completion properties | `{tracking, view?, submit?, use_grade?, pass_grade?}` | The `submit` mapping and tracking enum are confirmed. The exact semantics and support for the other optional properties still need verification. |
| `marking_workflow` | Nullable boolean | **Decided** ([guide, issue #232, comment 7176861868](https://github.com/narenccode/learnops/issues/232#issuecomment-7176861868), point 5, §12 item 16): for package models it remains `null`, and CK-10 reports it as `not checked`. |
| `course_completion` and `badges` | Null in package-derived models | Confirm how CK-10 should assess package models when these values are unavailable. |
| CK-03 comparison of non-integer points | `total_points`, `max_grade` and `points_total` are JSON numbers with a minimum of 0, so decimals are structurally valid; B1 `points` is an integer. The checker design says only: sum `max_grade`, compare with the target; a match is `pass`, a mismatch is `finding`. | **Undecided:** whether the comparison is exact, rounded to a precision or within a tolerance. No rule is specified or implemented. The guide and the checker owner decide this before CK-03 is built. |
| Report state: `cannot judge` versus `not checked` | Decision 25 and the CK-03 design said `cannot judge`; risk 11 (CK-07) and PRD C2.8 say `not checked`. | **Decided** ([guide, issue #232, comment 7176861868](https://github.com/narenccode/learnops/issues/232#issuecomment-7176861868), point 3, §12 item 20): there is one state, named `not checked`. The exit code follows error findings only (OPS-05). Reports always show both the error count and the not-checked count. A run with unchecked rules is never described as clean. |
| CK-12 flagging of other URI schemes | The guide's list flags `http://`, `https://` and protocol-relative `//host/` references; the checker design says "a scheme such as `http:` or `https:`". The vectors list a reference such as `ftp://…` in `media_refs` and leave its flagging null. | **Undecided:** does CK-12 flag every URI scheme other than `data:` (Akshita's proposal: `ftp:` and `file:` are fixed locations, not relative paths, PRD C-08), or only `http:`, `https:` and protocol-relative references, with other schemes written as "not checked in v1"? The guide decides before CK-12 is built. |
| `fullname` and activity/section `title` | Optional | Retain as optional reporting fields unless further requirements dictate otherwise. `fullname` is never null: a Moodle course always has a full name and B1 requires one. Section and activity titles may be null because the source may not name them. |

## 4. Required Moodle Lab Verification

The following decisions are documented but must not be treated as verified Moodle behaviour until tested against real Moodle 4.5 and 5.3 installations/backups.

1. Verify `OPTION_PREVIOUS` resolution using section order followed by activity order within each section.
2. Verify the behaviour when no earlier activity has manual or automatic completion tracking.
3. ~~Verify the criterion representation `{type, cmid, idnumber}` against real Moodle backup data.~~ **Done** for course-completion criteria that refer to an activity, against the published Moodle 5.3 B8.1 backup (decision 18; evidence below). Not verified: a badge criterion that refers to an activity (none is in that backup).
4. Verify availability JSON structures, including completion references and numeric CMIDs.
5. Verify section ordering, section 0, grade values and other Moodle-specific assumptions using real backups.
6. Confirm the B1 submission-based completion mapping against actual Moodle behaviour.

### Evidence for item 3: the published Moodle 5.3 B8.1 backup

Read on 2026-11-26 without a Moodle lab visit (guide, issue #232), with the repository's `testdata/b8-1-template-course/download.py` (it verified the recorded SHA-256) and Python's standard `tarfile` and XML reading. The archive is a gzip tar, not a zip file. Nothing was extracted to disk or committed.

| Item | Value |
|---|---|
| Release and asset | `testdata-b8-1-v1`, `b8-1-template-course.v1.mbz` (12,612 bytes) |
| SHA-256 | `d8869a012a39ae869c54f744d6c391387534bdab2389d8a8aecfd5b481c5585d` |
| Moodle | release `5.3+ (Build: 20261030)`, `moodle_version` 2026100500.08, backup release 5.3 (`moodle_backup.xml`) |
| Paths inspected | `moodle_backup.xml`, `completion.xml`, `badges.xml`, `activities/assign_28/module.xml`, `activities/assign_28/assign.xml`, `activities/feedback_29/module.xml`, `activities/feedback_29/feedback.xml`, and `module.xml` of the other four activities |

**Course-completion criteria (`completion.xml`).** Two `course_completion_criteria` elements, both with `<criteriatype>4</criteriatype>`: `<module>assign</module>` with `<moduleinstance>28</moduleinstance>`, and `<module>feedback</module>` with `<moduleinstance>29</moduleinstance>`. The four `course_completion_aggr_methd` elements (`criteriatype` null, 4, 8 and 7, `method` 1) carry no activity reference and are not criteria.

**How the reference works.** `moduleinstance` is the course-module id, not the plugin's own instance id: for the assignment, `moduleinstance` is 28, `activities/assign_28/module.xml` has `<module id="28">`, `moodle_backup.xml` lists `<moduleid>28</moduleid>` in `activities/assign_28`, and `activities/assign_28/assign.xml` has `<activity id="10" moduleid="28">` (instance id 10). For the feedback activity the course-module id is 29 and the instance id is 1. So `cmid` is read from `<moduleinstance>`.

**How the `idnumber` is obtained.** A criterion carries no `idnumber`. It is resolved from the `<idnumber>` element of `activities/<modulename>_<cmid>/module.xml`: `final-project` for 28 and `course-feedback` for 29. A missing `idnumber` is written as `$@NULL@$` (for example the Announcements forum, `activities/forum_25/module.xml`), which a builder must read as null.

**Badge criteria (`badges.xml`).** One badge with two `criterion` elements: `criteriatype` 0 with no parameters, and `criteriatype` 4 with one parameter `course_7` (value 7), which refers to the course. Neither refers to an activity. The integer 4 therefore has different content in the two files: an activity (`<module>`, `<moduleinstance>`) in `completion.xml` and a course in `badges.xml`. The backup stores only the integer; the string label for `type` (for example `activity`) is the builder's naming and a builder must not reuse the raw integer across the two files.

**Result.** The shape `{type, cmid, idnumber}` is supported for a course-completion criterion that refers to an activity: `type` from `criteriatype`, `cmid` from `moduleinstance`, `idnumber` from the activity's `module.xml`. For a badge criterion the shape holds only `type`, with `cmid` and `idnumber` null, which the schema allows. The hand-written `from-mbz.json` example lists its badge criteria as activities with a `cmid` and an `idnumber`; that does not match this backup (the example's `cmid` values also differ, 106 and 107, from the backup's 28 and 29) and this PR changed only its activity `media_refs` entry (to an in-scope image path), not its completion or badge criteria. Those criteria stay illustrative and inconsistent with the real backup.

The current `from-mbz.json` example is hand-written and illustrative. It has not been generated from or validated against a real Moodle backup.

The `from-package.json` example is also hand-written and intended for contract testing.

## 5. Compatibility and Versioning

- The contract identifier remains `learnops.course-model/v1`.
- Breaking changes require a new major contract version.
- New optional fields may be introduced within v1.
- CMIDs must never be compared across different models.
- Stable activity identity is based on `idnumber`.
- Package-derived CMIDs are synthetic and local to their model.
- Null values represent unavailable or unspecified source information, not false values.
- Checker rules must distinguish between a confirmed fault and information that cannot be judged; the latter is reported as `not checked` (section 3).

## 6. Approval Status

**Numbering.** "Point N" (1 to 6) is a numbered decision in the guide's comment on issue #232 ([comment 7176861868](https://github.com/narenccode/learnops/issues/232#issuecomment-7176861868)). "Item N" is a numbered row of the checker design §12 table (`docs/design/checker.md`). Decisions in this record keep their original numbers.

The guide has confirmed the decisions in Section 1 and approved the PR-size exception for the B2 contract PR.

Student 1 has confirmed the B1-to-B2 submission completion mapping in Section 2.

**Release 0 freeze (guide, [issue #232, comment of 2026-11-26](https://github.com/narenccode/learnops/issues/232#issuecomment-7176861868), point 1).** B2 v1 freezes at Release 0 when two conditions are met: (1) the `media_refs` description is narrowed to the CK-12 scope (decision 16), and (2) the completion-criterion shape `{type, cmid, idnumber}` is read from the published Moodle 5.3 B8.1 backup (decision 18; section 4, item 3). Both conditions are satisfied by the change that records this text. The shared CK-12 test vectors (24 cases) have been created and validated (decision 16); the extractor is not implemented. Akshita confirmed the `media_refs` scope as the affected M1 owner on issue #232; her formal approval of the change and the guide's approval are given on the pull request and are not recorded here. This record does not by itself mark B2 as frozen.

The other B2 items stay as documented Release 1 limitations, decided before FR-C-01 and FR-C-03: the other completion properties, CK-03 comparison of non-integer points, `course_completion` and `badges` for packages, and CK-12 flagging of other URI schemes (section 3). Two items formerly listed here are now decided by the guide in the same comment and are no longer open: `marking_workflow` for packages (stays `null`; CK-10 reports `not checked`) and `cannot judge` against `not checked` (one state, `not checked`). The remaining Moodle verification items in section 4 (1, 2, 4, 5 and 6) are also still unverified and documented; the guide's decision names only item 3 as a freeze condition. Moodle 5.3 is the only supported version (decision 0017).

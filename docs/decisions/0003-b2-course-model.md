# 0003: B2 Course Model Decisions

**Status: Draft contract. Not yet approved or frozen.**

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
| 7 | `visible` and `completion_enabled` keys are always present and may be null. Null means the source does not specify the value; it never means false. The checker treats null as cannot judge, not as a fault. |
| 8 | Unlock dates are Unix timestamps. Package dates are converted to 00:00 in the configured site timezone. The timezone name is recorded in the model. The lab/default Indian configuration uses `Asia/Kolkata`. |
| 9 | CK-07 uses no fingerprints. Protected items are compared field by field against a supplied reference model of the template course, consistent with FR-C-05. B2 cannot inspect body text or attached files. |
| 10 | Unknown fields are accepted unless the contract explicitly prohibits them, consistent with EXT-02 and A9. |
| 11 | `source.timezone` is required and non-null for package-derived models. For `.mbz` models, it must be null because Moodle backup `course.xml` has no timezone field and its timestamps are absolute Unix timestamps. |
| 12 | `source.kind` is a closed set: `mbz` or `package`. |
| 13 | Completion tracking is a closed set: `none`, `manual`, and `automatic`, corresponding to Moodle values 0, 1, and 2. |
| 14 | Section `idnumber` is nullable. Moodle's `course_sections` table has no `idnumber` field; `.mbz` models therefore use null, and sections are matched by section number. |
| 15 | `marking_table` has the shape `{present, points_total}`. It does not contain a `valid` field; marking-table validity is the responsibility of CK-09. |
| 16 | `media_refs` is optional. If absent, CK-12 cannot judge the corresponding media references. |
| 17 | `course.total_points` is optional. For a package-derived model (`source.kind = package`), it carries the package's declared `total_points`; when that value is absent or null, CK-03 uses the B1 default of 100. For an `.mbz`-derived model (`source.kind = mbz`), it carries a target only when an independent target is supplied to the model builder. An absent or null value means there is no independent target and CK-03 returns `cannot judge`; the checker must not apply the package default or derive a target from the computed gradebook total. |
| 18 | The criterion shape `{type, cmid, idnumber}` is acceptable provisionally, pending verification against a real Moodle backup. |
| 20 | `source.timezone` is also checked at run time, because a JSON Schema cannot check a time-zone name. The schema keeps its structural rules (decisions 11 and 14). A name is valid when `zoneinfo.ZoneInfo` resolves it, which accepts `Asia/Kolkata`, aliases such as `Asia/Calcutta`, `UTC` and `Etc/GMT-5`, and rejects `UTC+5:30` and `Mars/olympus`. The configuration variable is `SITE_TIMEZONE`, listed in `.env.example` with `Asia/Kolkata` as the lab value. There is no default in code: a package-derived model needs the variable and fails closed when it is missing or invalid. A `.mbz` model still stores null. `tzdata` is pinned in the root `requirements.txt` (Apache-2.0) for systems without a time-zone database, such as Windows. The public entry point is `validate_course_model(doc)` (guide-confirmed): it validates the B2 schema, runs this run-time check and returns the existing `ValidationReport`, so a consumer cannot bypass the check. `timezone_issues()` is the helper it uses, not the entry point. The model builder does not exist yet (FR-C-01, Release 1): it must read `SITE_TIMEZONE` with `site_timezone(os.environ)`, store the result in `source.timezone` and validate the model with `validate_course_model()`. Shared code: `libs/contracts/timezones.py`. |
| 21 | CK-07 reference model (design decision; the checker does not exist yet). The reference is the B2 course model of the B8.1 template course, built from its `.mbz` backup. It is supplied per run with the checker option `--reference-model <path>`, not through an environment variable. When no reference model is supplied, CK-07 reports `not checked` for that run, not a fault, and the report says the protected items were not compared. This refines decision 9. Recorded in `docs/design/checker.md` risk 11. |
| 22 | `source.mode` is required for every source. Its values are `full` and `sections-only`, which come from PRD B1.4. A package source may use either. A `.mbz`-derived model must use `full`: the mode is the output mode, and a backup represents a whole course. The schema enforces this with the `if/then` rules on `source.kind` (`mode` required for both kinds, `const: full` for `.mbz`), and `from-mbz.json` states `"mode": "full"`. |
| 23 | Unlock rules for a course package, by mode (B1.2 rule 2; guide-confirmed on 2026-11-15). Sections are numbered in document order; the section number, `idnumber` and title are never read to decide which section is previous. An absent `unlock` equals `after: null` and `start_date: null`, and `start_date` never replaces `after`. **Full mode:** the first section must have `after` null, because a non-null value cannot name an earlier activity. Every later section must have `after` naming the previous task, which is the single assignment of the immediately preceding section; that section must hold exactly one assignment, and the validator reports the section when it holds none or more than one. **Sections-only mode:** every listed section must have `after`, a single-section package included, because a template already has the first week and a later week names the template's previous task. A well-formed reference to an activity outside the package is accepted. A reference to an activity of a later section of the package is rejected (decision 24 covers the section's own activities). After the merge, a name that matches nothing is CK-04 and a loop across sections is CK-05; those are checker rules and the contract library does not implement them. **Section-level `cm = -1`** follows decision 5 and resolves strictly before the section: the nearest earlier activity with manual or automatic tracking, which is the last tracked activity of the preceding sections. An activity inside the current section is never previous for its own section; it is still provisional until the Moodle lab check. Nested availability groups: B2 stores Moodle's availability object and does not constrain its nesting; reading groups recursively is an implementation detail of `libs/contracts/availability.py`. Shared code: `check_unlock_rules()` in `libs/contracts/course_rules.py`. |
| 24 | A sections-only section must not reference an activity of its own section. The guide: "A reference to an activity in the same section is not an earlier activity; the sections-only exception is for an activity outside the package, not one at or after the section." The validator rejects it, wherever the activity sits in that section, with the same issue as a reference to a later section. CK-05 still covers cycles across sections. |
| 25 | CK-03 uses an independent grading target (guide-confirmed, 2026-11-16). For a package model, the target is the package's declared `total_points`, with the B1 default of 100 only when the package omits it. For an `.mbz` model, including a merged course, the model builder may receive an independently declared target and must write it to `course.total_points`; a merged course remains `source.kind = mbz`. The target must never be derived from the gradebook items being checked. If no independent target is supplied, `course.total_points` remains absent or null and CK-03 returns `cannot judge` (no default of 100 for `.mbz`). The merged target includes the final project because it is part of the merged course; the intended merged total must be declared before testing when the package adds graded points. CK-03 sums `grade_item.max_grade` for graded activities, excludes ungraded activities, and compares the sum with the independent target. Its report includes the target, calculated sum, difference and items counted. This decision confirms the target handoff and calculation semantics; it does not define a builder API or input mechanism. |

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
| `marking_workflow` | Nullable boolean | Confirm whether null is appropriate for package-derived models and whether the current representation covers the required checker behaviour. |
| `course_completion` and `badges` | Null in package-derived models | Confirm how CK-10 should assess package models when these values are unavailable. |
| `fullname` and activity/section `title` | Optional | Retain as optional reporting fields unless further requirements dictate otherwise. `fullname` is never null: a Moodle course always has a full name and B1 requires one. Section and activity titles may be null because the source may not name them. |

## 4. Required Moodle Lab Verification

The following decisions are documented but must not be treated as verified Moodle behaviour until tested against real Moodle 4.5 and 5.3 installations/backups.

1. Verify `OPTION_PREVIOUS` resolution using section order followed by activity order within each section.
2. Verify the behaviour when no earlier activity has manual or automatic completion tracking.
3. Verify the criterion representation `{type, cmid, idnumber}` against real Moodle backup data.
4. Verify availability JSON structures, including completion references and numeric CMIDs.
5. Verify section ordering, section 0, grade values and other Moodle-specific assumptions using real backups.
6. Confirm the B1 submission-based completion mapping against actual Moodle behaviour.

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
- Checker rules must distinguish between a confirmed fault and information that cannot be judged.

## 6. Approval Status

The guide has confirmed the decisions in Section 1 and approved the PR-size exception for the B2 contract PR.

Student 1 has confirmed the B1-to-B2 submission completion mapping in Section 2.

The contract remains a draft until the implementation reflects these decisions, the required tests pass, outstanding review feedback is addressed, and the necessary Moodle-specific verification is completed.

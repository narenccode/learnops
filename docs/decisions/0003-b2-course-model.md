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
| 6 | Activity types use B1 names: `page`, `assignment`, `url`, `label`, and `h5p`. Other activity types retain Moodle's module name. |
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
| 17 | `course.total_points` is optional. When absent, the checker falls back to the B1 default of 100. |
| 18 | The criterion shape `{type, cmid, idnumber}` is acceptable provisionally, pending verification against a real Moodle backup. |

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
| `source.mode` | Required for package sources | Confirm whether the current mode values and requirement are correct. |
| `fullname` and activity/section `title` | Optional | Retain as optional reporting fields unless further requirements dictate otherwise. |

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

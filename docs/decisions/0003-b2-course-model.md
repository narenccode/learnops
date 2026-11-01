# 0003: B2 course model decisions

**Status: draft contract. Not approved and not frozen.** Only the first table is guide-confirmed.

## Confirmed by the guide

| # | Decision |
|---|---|
| 1 | Schema `contracts/course-model.v1.schema.json`; examples in `contracts/examples/course-model.v1/`. PRD B2 corrected to match. |
| 2 | Decisions are recorded here. `docs/traceability.md` is for requirements. |
| 3 | The `schema` value is `learnops.course-model/v1`. Changing it is a breaking change requiring v2. |
| 4 | `cmid` is required and is a Moodle course-module ID. Never compare it between models; `idnumber` is the stable identity. |
| 5 | In availability, `cm = -1` is the special previous-activity reference, handled when resolving CK-01 and CK-04. |
| 6 | Activity types use the B1 names `page`, `assignment`, `url`, `label`, `h5p`. Other types keep Moodle's module name. |
| 7 | B1 `completion: submit` maps to automatic tracking with `submit: true`. Akshita must confirm compatibility in the PR. |
| 8 | `visible` and `completion_enabled` keys are always present and may be null. Null means the source does not say, never false. The checker treats it as cannot judge, not as a fault. |
| 9 | Unlock dates are Unix timestamps. Package dates convert to 00:00 in the configured site timezone, the timezone name is recorded in the model, and the lab/default Indian configuration uses `Asia/Kolkata`. |
| 10 | CK-07 has no fingerprints. Protected items are compared field by field against a supplied reference model of the template course, the same way as FR-C-05. B2 cannot see body text or attached files. |
| 11 | Unknown fields are accepted unless the contract explicitly prohibits them (EXT-02, A9). |

## Open: proposals, not approved

| Item | Current draft | Question |
|---|---|---|
| `source.timezone` | Non-empty string; required for a package, optional for a `.mbz` | The guide confirmed recording the name, not where. It sits with `source` because it describes how the model was built, and a `.mbz` already holds timestamps. Is this location right, and what should a `.mbz` record? |
| Synthetic package `cmid` | Packages use made-up IDs from 1 | A package has no Moodle ID, yet `cmid` is required with minimum 1. Are synthetic IDs acceptable? If not, `cmid` and `from-package.json` must change, and the unlock-rule test that looks up `cm` by `cmid` too. Settle this before the freeze, as it is breaking. |
| `cm = -1` resolution | Accepted in availability, rejected as an activity's own `cmid` | Exactly which activity does Moodle pick? Verify on Moodle 4.5 and 5.3. |
| Other null values | `marking_workflow`, `course_completion`, `badges` are null in a package model | Keep null, or fill in what Studio would generate? CK-10 cannot assess a package while null. |
| `completion` structure | `{tracking, view?, submit?, use_grade?, pass_grade?}` | Only the `submit` mapping is confirmed. Is the rest right, and should `tracking` stay a closed enum? |
| `marking_table` | `{present, points_total}`, required on assignments | Right shape? Does it need a `valid` field? |
| `media_refs` | Optional | Should activities carry it for CK-12? |
| `course.total_points` | Optional, nullable | Should the model carry the CK-03 target? |
| `source` | Required; `mode` required for a package | Should the model carry it for CK-07? |
| `source.kind` | Closed enum: `mbz`, `package` | Should it stay closed? |
| Section `idnumber` | Required, nullable | Moodle sections are not known to have one. How does reverse import map them? |
| Criterion shape | `{type, cmid, idnumber}` | Is this right for CK-08? |
| `fullname`, `title` | Optional | Keep them for readable reports? |

## Not verified

Moodle behaviour assumed in this contract (section 0, decimal grades, numeric IDs in availability, no
section idnumber, the example's availability JSON) comes from general knowledge of Moodle. None of it
has been checked against a real backup on Moodle 4.5 or 5.3, and `from-mbz.json` is hand-written.

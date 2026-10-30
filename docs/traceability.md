# Traceability (PRD E4)

| Requirement | Test(s) | Demo step | Bloom level |
|---|---|---|---|

## B1 course package contract (v1), Release 0 foundation

Files: `contracts/course-package.v1.schema.json`, `contracts/examples/course-package.v1/`,
`libs/contracts/tests/test_course_package_v1.py`. B1 has no requirement ID of its own in the PRD
(it is a contract, PRD B.0), so no row in the table above maps to it.

FR-S-03 ("Validate against B1 and the checker rule library", Release 2) is deliberately not in the
table above. The tests below cover only the B1-related part of it: structure checks against the
schema. They do not implement FR-S-03, which also needs the checker rule library (Module 2) and
validation on every save in Course Studio. FR-S-03 gets its row in the pull request that
implements it.

### Enforced by the JSON Schema and covered by automated tests

Structure only. Test names are in `test_course_package_v1.py`.

| Rule | PRD | Test(s) |
|---|---|---|
| `schema` equals `learnops.course/v1`; `course` and `sections` required | B1.1 | `test_missing_required_field_is_rejected`, `test_wrong_type_or_value_is_rejected` |
| Required fields and types on course, section and activity (`type`, `idnumber`, `title`; section `number`, `activities`) | B1.1 | same two tests |
| `mode` is `full` or `sections-only` | B1.1, B1.4 | `test_wrong_type_or_value_is_rejected`, `test_example_in_sections_only_mode_is_valid` |
| `slug`, `idnumber` and `unlock.after` are lowercase ASCII with hyphens (format only, not uniqueness) | B1.1, B1.2 rule 6 | `test_invalid_identifier_is_rejected` |
| The two default protected idnumbers (`final-project`, `course-feedback`) are rejected on sections and activities, in both modes | B1.4 | `test_protected_idnumber_is_rejected` |
| An assignment has `body`, `points`, `submission` and `completion`; a page has `body` | B1.1 | `test_missing_required_field_is_rejected` |
| `unlock.start_date` is an ISO date string or null (impossible dates are rejected; an unquoted YAML date is rejected) | B1.1 | `test_invalid_start_date_is_rejected`, `test_unquoted_yaml_date_is_rejected_so_it_must_be_quoted` |
| An H5P activity has `graded: false` | B7 | `test_missing_required_field_is_rejected`, `test_wrong_type_or_value_is_rejected` |
| Unknown fields are accepted | B.0 rule 2, EXT-02 | `test_valid_variation_is_accepted` |
| The schema is valid, and the example package validates (also as `sections-only`) | B.0 rule 1 | `test_schema_is_a_valid_draft_2020_12_schema`, `test_example_package_is_valid`, `test_example_in_sections_only_mode_is_valid` |

Enforced and tested, but chosen in the schema rather than stated as a rule in the PRD (to be
confirmed by the contract reviewers): the `type` spellings `url` and `label`; `completion` limited
to `submit`; `submission` limited to `onlinetext` and `file`; `section.number` at least 1; points
as non-negative integers; non-empty titles; the shape of `body` (relative path, no `..`);
`activities` and `sections` not empty.

### Documented but not automatically enforced

No validator code for these exists yet, so nothing in the repository checks them. The schema's
`$comment` lists them too. The example package was checked against them by hand when it was
created; that check is not automated and is not committed.

| Rule | PRD | Where the PRD places it |
|---|---|---|
| One guide Page and one task Assignment per week | B1.2 rule 1 | No checker rule is named for it (CK-01…CK-13) |
| Week N unlocks when the week N-1 task is submitted; `unlock.after` names an existing earlier activity | B1.2 rule 2 | Related: CK-04, CK-05 (FR-C-03, R1) |
| Graded points sum to `total_points` | B1.2 rule 3 | CK-03 |
| Assignments use marking workflow | B1.2 rule 4 | CK-10 (not a package field) |
| Completion tracking on for every activity used in an unlock rule | B1.2 rule 5 | CK-13 |
| `idnumber`s unique within the course and never reused for a different activity | B1.2 rule 6 | CK-06 (uniqueness); "never reused" has no PRD rule |
| Marking table present and valid: markers, columns, points sum, allowed `Check` names | B1.3, C3.5 | CK-09 |
| Protected idnumbers configured beyond the two defaults; `protected_section` collision | B1.4 | CK-07 for the course model; `protected_section` has no default in the PRD |

### Not mapped

Left out because the PRD does not establish the mapping:

- **A row, demo step and Bloom level for FR-S-03.** See the note at the top of this section. PRD
  C1.12 gives levels to kinds of work (for example "Design (L6): schema, validator, generator"),
  not to individual requirements.
- **FR-S-02, FR-S-04, FR-S-07, FR-S-08, FR-C-01, FR-G-01.** They touch B1 but need code that does
  not exist yet, and the PRD does not say that schema tests count towards them.
- **C1.7 "a package containing a protected idnumber is rejected with a clear message".** The schema
  rejects the two default idnumbers; the user-facing message is not tested.
- **Requirement IDs for the contract work itself.** None in the PRD.

## B2 course model contract (v1), Release 0 foundation

**Status: draft. Not approved and not frozen.** The open decisions below are unresolved.

Files: `contracts/course-model.v1.schema.json`, `contracts/examples/course-model.v1/`,
`libs/contracts/tests/test_course_model_v1.py`. B2 has no requirement ID of its own in the PRD (it
is a contract, PRD B.0), so no row in the table at the top of this file maps to it.

FR-C-01 ("Build the course model (B2)") is deliberately not in that table. It needs the backup
parser and package reader, which do not exist yet. FR-C-01 gets its row in the pull request that
implements it.

### Open decisions

The contract is a draft with **17 unresolved decisions**. Nothing below is confirmed or approved.
Numbers are stable identifiers, not a ranking, so use the last column for priority. **Decision 6
(`cmid`) is the highest priority.**

The `OPEN DECISION` markers in the schema cover only some of these 17, so a field without a marker
is not settled. This table is the complete list.

Risk ratings use the classification in `.claude/commands/contract-change.md`, which applies PRD
B.0. After the freeze only additive, optional changes are allowed.

- **Breaking:** a rename, removal, type change, new required field or changed meaning of a field.
  It needs a new version and the guide's approval, so settle it before the freeze.
- **Changed meaning:** a breaking change where no field changes, only what a value means.
- **Additive:** can be added later as an optional field.
- **Low:** already optional and no CK rule depends on it. Removing it would still be breaking.
- **Not rated:** no repository document supports a rating.
- **Needs confirmation:** no rating has been assigned yet.

**Who confirms:** "Guide" is what this section recorded or a repository document states. "Student 1:
not stated" means no document names Student 1 for that decision. It is flagged, not guessed: PRD B.0
makes Student 1 an affected owner of any later B2 change (B2 is used by M1 and M2), but no document
says whether their confirmation is needed for this draft. The guide should settle that. "Proposed,
unconfirmed" means a suggestion from the draft review that no document supports. "Needs
confirmation" means no owner has been assigned yet.

| # | Unresolved question | Current draft | Why it matters | Who confirms | Risk after the freeze |
|---|---|---|---|---|---|
| 1 | Which schema filename is correct? | `course-model.v1.schema.json` | PRD B2 says `/contracts/course-model.v1.json`; `contracts/CLAUDE.md` and `docs/GETTING-STARTED.md` say `.schema.json`, and B1 uses that form. The PRD normally wins, so the guide must rule. The PRD is not changed here. | Guide | **Not rated:** PRD B.0 and `contract-change.md` cover fields, not filenames. Flagged for the guide. |
| 2 | Is `marking_table: {present, points_total}` the right shape, and does it need a `valid` field? | Required on assignments | The PRD lists presence only, but CK-09 also compares points. A table that parses but has wrong columns or `Check` values cannot be told apart from a valid one. | Guide; Student 1: not stated | **Breaking** if the existing fields are renamed, removed or retyped, or if a new field is required. **Additive** if `valid` is added as optional. |
| 3 | Should activities carry `media_refs`? | Optional | Not in the PRD key fields, but CK-12 needs media references. | Guide; Student 1: not stated | **Breaking** if removed, because CK-12 depends on it |
| 4 | Should the model carry `course.total_points`? | Optional, nullable | Not in the PRD key fields. CK-03 needs a target, and a `.mbz` has none, so it would come from rule configuration. | Guide; Student 1: not stated | **Breaking** if removed, because CK-03 can use it |
| 5 | Should the model carry `source: {kind, mode}`? | Required; `mode` required for a package | Not in the PRD key fields. CK-07 must not report protected items as missing from a sections-only package. | Guide; Student 1: not stated | **Breaking:** required, so removing it, or adding it as required later, is not additive |
| 6 | Should activities carry a required `cmid`? | Required | Not in the PRD key fields. Moodle availability conditions are expected to refer to activities by numeric id, not idnumber, so CK-04 and CK-05 need the mapping. Packages get synthetic ids. | Guide; Student 1: not stated | **Highest priority. Breaking:** required, so removing or weakening it is not additive |
| 7 | Should section `idnumber` stay required but nullable, and how does reverse import map sections? | Required, nullable | The PRD lists it, but Moodle sections are not known to have one. Expected to be null for a `.mbz`. | Guide and Student 1 | **Breaking:** a required field, so removing it or changing its type is not additive |
| 8 | Should a package model use `null` for values a package does not carry, or should the builder fill in what Studio would generate? | `visible`, `completion_enabled`, `marking_workflow`, `course_completion` and `badges` are null in a package model | Null invents nothing, but CK-10 then cannot assess a package. | Guide; Student 1: not stated | **Changed meaning:** filling them in later changes what a package model's values mean |
| 9 | Is `{type, cmid, idnumber}` the right criterion shape? | Used for course completion and badges | The PRD names the criteria but not their shape. CK-08 reads them. | Guide; Student 1: not stated | **Breaking** if a field is renamed, removed or retyped |
| 10 | Which activity type names should the model use, and how do B1, Moodle module names and Course Studio map to them? | B1 names (`page`, `assignment`, `url`, `label`, `h5p`); any other type keeps Moodle's module name | Moodle's module names are expected to differ from B1's. The model builder must map them, and Studio's reverse import and the FR-C-05 diff rely on the same names. | Proposed, unconfirmed: guide and Student 1 | **Breaking:** changing the meaning of a `type` value needs a new version |
| 11 | Is the `completion` structure right, and should `tracking` be a closed enum? | `{tracking, view?, submit?, use_grade?, pass_grade?}`; `tracking` is `none`, `manual` or `automatic` | The PRD says "completion rule" and gives no structure, so this shape is a proposal. CK-02 and CK-13 and the path simulation (FR-C-02) depend on it, and Studio's `completion: submit` must map onto it. | Proposed, unconfirmed: guide and Student 1 | **Breaking:** a new `tracking` value is not additive, because readers that accept only the three values would reject it |
| 12 | Should `visible` and `completion_enabled` be required but nullable? | Both keys must be present; null when the source does not carry the value (see decision 8) | Every model builder must always write these keys. If they became optional or changed meaning later, readers that expect them would break. | Proposed, unconfirmed: guide and Student 1 | **Breaking:** relaxing a required field or changing what null means is not additive |
| 13 | Is `learnops.course-model/v1` the right `schema` value? | `learnops.course-model/v1`, chosen by analogy with B1's `learnops.course/v1` | The PRD does not name it. Every reader and example checks this exact value. | Proposed, unconfirmed: guide | **Breaking:** the value is a `const`, so changing it invalidates existing documents |
| 14 | What timezone applies to unlock dates? | `from-package.json` converts B1's `start_date` as midnight UTC | B1 gives a date with no timezone, while Moodle's availability JSON is expected to hold a timestamp. The interpretation decides the moment a week opens, and FR-C-05 could report false differences between a package model and a `.mbz` model. | Guide and Student 1 (B1 owner) | **Changed meaning:** no field changes, but stored timestamps would mean something different |
| 15 | Are the limits of CK-07 protected-item change detection acceptable? | The model has no content or fingerprint for protected items | CK-07 includes a protected item being "changed". Comparing with the template model (B8.1) can only see the fields the model holds, so an edit elsewhere, such as to a description, would go undetected. The B8.3 planted errors must not assume more than this. | Guide and Student 1 (B8.1 owner) | **Additive:** an optional fingerprint could be added later, but the limit applies to CK-07 until then |
| 16 | Should the model keep optional `fullname`, section `title` and activity `title`? | Optional and not in the PRD key fields | They make checker reports readable and are not used to identify anything (activities are identified by idnumber). | Guide | **Low** |
| 17 | Should `source.kind` stay a closed enum? | Closed enum: `mbz` or `package` | A third way of building a model would need a new value. Consumers that validate against the current schema, or accept only these two values, would reject such a model, so adding a value could break them even though no field changes. | **Needs confirmation** | **Needs confirmation** |

Moodle behaviour assumed above (section 0, decimal grades, numeric ids in availability, no section
idnumber, the example's availability JSON) is from general knowledge of Moodle. **None of it has been
checked against a real backup on Moodle 4.5 or 5.3**, because the lab is not ready. `from-mbz.json`
is hand-written and illustrative.

### Project-level blocker: contract tests do not run in CI

**Needs the guide's attention.** This affects every contract, not only B2.

The `Unit tests` step in `.github/workflows/ci.yml` runs `pytest` only if
`ls -d modules/*/tests libs/*/tests` succeeds. No `modules/*/tests` folder exists, so `ls` fails and
the step skips `pytest`. The B1 and B2 contract tests are therefore not run by CI. They have been run
locally only. The gate was reproduced locally in Git Bash, not observed in a GitHub Actions run.

`.github/` is guide-owned, so `ci.yml` is not changed in this work.

### Enforced by the JSON Schema and covered by automated tests

Structural schema validation only. These tests do not implement CK-01 to CK-13. Test names are in
`test_course_model_v1.py`.

| Rule | PRD | Test(s) |
|---|---|---|
| The schema is valid Draft 2020-12 and both examples validate | B.0 | `test_schema_is_a_valid_draft_2020_12_schema`, `test_example_is_valid` |
| Required fields, types and enums on every object | B2 | `test_missing_required_field_is_rejected`, `test_wrong_type_or_value_is_rejected` |
| A package source states its mode; an assignment has marking fields, other types need none | B1.4, B2 | `test_package_source_without_mode_is_rejected`, `test_missing_required_field_is_rejected`, `test_non_assignment_needs_no_marking_fields` |
| Unknown fields are accepted at every level | B.0, EXT-02 | `test_unknown_field_is_accepted` |
| The schema accepts a broken course, with at least one sample input per CK rule and an unknown activity type. For CK-07 this covers missing protected items only (see below). | C2.3, C2.8 | `test_broken_course_still_validates`, `test_protected_idnumbers_are_allowed_unlike_b1` |
| Permitted null and absent values | B2 | `test_valid_variation_is_accepted`, `test_sections_only_package_is_valid` |
| The package example matches the B1 example | B1, B2 | `test_package_example_matches_b1_example`, `test_package_example_unlock_rule_matches_b1_example` |
| The examples contain every field in the CK-rule-to-field mapping (`CK_FIELDS` in the test file). The mapping is **proposed and unapproved**, because the PRD's rules do not name model fields. Presence only. | C2.3 | `test_examples_carry_the_fields_a_rule_needs` |

### Documented but not automatically enforced

The schema must not enforce the CK rules: a course that breaks them has to validate so that the
checker can report it. No parser, evaluator or rule engine exists yet, so no test here shows that
any rule works.

- Rules CK-01 to CK-13 (FR-C-03, Release 1).
- CK-07 beyond representation: the tests show that a course with its protected items missing can be
  represented. They do not establish detection of duplicated or changed protected items.
- Unique `cmid` values within a model (the model builder's job, FR-C-01).
- The inner form of `availability`, which belongs to Moodle.
- Comparing a package model with a `.mbz` model: `cmid` values differ, so FR-C-05 compares by
  idnumber.

### Not mapped

- **FR-C-01, FR-C-02, FR-C-03, FR-C-05.** They use B2 but need code that does not exist yet, and the
  PRD does not say that schema tests count towards them.
- **Requirement IDs for the contract work itself.** None in the PRD.

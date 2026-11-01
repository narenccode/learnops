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

**Status: draft. Not approved and not frozen.** Confirmed decisions and open items are in
`docs/decisions/0003-b2-course-model.md`.

Files: `contracts/course-model.v1.schema.json`, `contracts/examples/course-model.v1/`,
`libs/contracts/tests/test_course_model_v1.py`. B2 has no requirement ID of its own in the PRD (it
is a contract, PRD B.0), so no row in the table at the top of this file maps to it.

FR-C-01 ("Build the course model (B2)") is deliberately not in that table. It needs the backup
parser and package reader, which do not exist yet. FR-C-01 gets its row in the pull request that
implements it.

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
| A package source states its mode and its timezone (the timezone location is proposed); an assignment has marking fields, other types need none | B1.4, B2 | `test_package_source_without_mode_is_rejected`, `test_package_source_without_timezone_is_rejected`, `test_missing_required_field_is_rejected`, `test_non_assignment_needs_no_marking_fields` |
| Unknown fields are accepted at every level | B.0, EXT-02 | `test_unknown_field_is_accepted` |
| The schema accepts a broken course, with at least one sample input per CK rule and an unknown activity type. For CK-07 this covers missing protected items only (see below). | C2.3, C2.8 | `test_broken_course_still_validates`, `test_protected_idnumbers_are_allowed_unlike_b1` |
| Permitted null and absent values, and `cm = -1` in availability | B2 | `test_valid_variation_is_accepted`, `test_sections_only_package_is_valid` |
| The package example matches the B1 example, including `completion: submit` and an unlock date at 00:00 in the site timezone | B1, B2 | `test_package_example_matches_b1_example`, `test_package_example_unlock_rule_matches_b1_example` |
| The examples contain every field in the CK-rule-to-field mapping (`CK_FIELDS` in the test file). The mapping is **proposed and unapproved**, because the PRD's rules do not name model fields. Presence only. | C2.3 | `test_examples_carry_the_fields_a_rule_needs` |

### Documented but not automatically enforced

The schema must not enforce the CK rules: a course that breaks them has to validate so that the
checker can report it. No parser, evaluator or rule engine exists yet, so no test here shows that
any rule works.

- Rules CK-01 to CK-13 (FR-C-03, Release 1).
- CK-07 beyond representation: the tests show that a course with its protected items missing can be
  represented. They do not establish detection of duplicated or changed protected items. B2 holds
  no body text or attached files, so a reference-model comparison cannot see changes to them.
- Treating a null `visible` or `completion_enabled` as "cannot judge" (the checker's job), and
  resolving `cm = -1` (pending verification on Moodle 4.5 and 5.3).
- Unique `cmid` values within a model (the model builder's job, FR-C-01).
- The inner form of `availability`, which belongs to Moodle.
- Comparing a package model with a `.mbz` model: `cmid` values differ, so FR-C-05 compares by
  idnumber.

### Not mapped

- **FR-C-01, FR-C-02, FR-C-03, FR-C-05.** They use B2 but need code that does not exist yet, and the
  PRD does not say that schema tests count towards them.
- **Requirement IDs for the contract work itself.** None in the PRD.

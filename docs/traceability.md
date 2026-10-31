# Traceability (PRD E4)

| Requirement | Test(s) | Demo step | Bloom level |
|---|---|---|---|

## B1 course package contract (v1), Release 0 foundation

Files: `contracts/course-package.v1.schema.json`, `contracts/examples/course-package.v1/`,
`libs/contracts/tests/test_course_package_v1.py`; the schema stage of the package validator in
`libs/contracts/*.py` (shared validator reference EXT-09) with its tests `test_validate_course.py`
and `test_report.py`. B1 has no requirement ID of its own in the PRD (it is a contract, PRD B.0),
so no row in the table above maps to it.

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

### Enforced by validator code (`libs/contracts`) and covered by automated tests

`validate_course_document()` runs the schema on a parsed `course.yaml` and returns a report. Test
names are in `test_validate_course.py` (course.yaml as parsed data) and `test_report.py` (the
report types).

| Rule | PRD | Test(s) |
|---|---|---|
| The schema is applied to a parsed `course.yaml`; every error is reported (not only the first), in a fixed order, with its place, a message and a fix hint; an impossible calendar date and a document that is not an object are errors | B.0 rule 4, B1.1 | `test_example_document_has_no_errors`, `test_schema_errors_are_reported_with_their_place`, `test_every_schema_error_is_reported_not_only_the_first`, `test_an_impossible_calendar_date_is_rejected`, `test_a_document_that_is_not_an_object_is_an_error` |
| The two default protected idnumbers are rejected with a clear message that names the place and says what to do; the validator reports each one once | B1.4 | `test_default_protected_idnumbers_are_left_to_the_schema`, `test_default_protected_idnumber_gets_a_clear_message` |
| Rules that are not implemented are listed as "not checked" in every report, so that "no errors" is not read as "fully checked" (a design choice, not a PRD rule) | n/a | `test_held_rules_are_reported_as_not_checked_never_skipped_silently`, `test_a_document_with_weekly_structure_problems_is_not_judged_here` |
| A report is ok when it has no errors; "not checked" entries do not make it fail; issues cannot be changed after creation | n/a | `test_empty_report_is_ok`, `test_report_with_an_error_is_not_ok`, `test_not_checked_items_do_not_make_a_report_fail`, `test_issue_defaults_are_a_document_level_issue`, `test_issue_cannot_be_changed_after_creation` |

This is not FR-S-03 or FR-C-03: the checker's rules (CK-xx) work on the course model (B2), which
this library does not build.

### Documented but not automatically enforced

The validator does not check these yet, so nothing in the repository enforces them. The schema's
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
- **C1.7 "a package containing a protected idnumber is rejected with a clear message".** The
  validator reports the two default idnumbers with a clear message (tested above); the Course
  Studio screen and CLI that show it do not exist yet.
- **Requirement IDs for the contract work itself.** None in the PRD.

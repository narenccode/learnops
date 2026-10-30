# Traceability (PRD E4)

| Requirement | Test(s) | Demo step | Bloom level |
|---|---|---|---|

## B1 course package contract (v1), Release 0 foundation

Files: `contracts/course-package.v1.schema.json`, `contracts/examples/course-package.v1/`,
`libs/contracts/tests/test_course_package_v1.py`; the package validator in `libs/contracts/*.py`
with its tests `test_validate_course.py`, `test_validate_package.py` and `test_report.py`. B1 has
no requirement ID of its own in the PRD (it is a contract, PRD B.0), so no row in the table above
maps to it.

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

`validate_package()` and `validate_course_document()` run the schema first. The rules below run
only when the structure is valid; otherwise the report says they were not checked. Test names are
in `test_validate_course.py` (course.yaml as parsed data) and `test_validate_package.py` (a
package folder).

| Rule | PRD | Test(s) |
|---|---|---|
| Whole-package entry point: reads `course.yaml`, applies the schema and the rules below, reports every error with its place, a message and a fix hint; a missing or unreadable `course.yaml` is an error | B.0 rule 4, B1.1 | `test_example_package_has_no_errors`, `test_missing_course_yaml_is_an_error`, `test_unparseable_course_yaml_is_an_error`, `test_course_yaml_that_is_not_utf8_is_an_error`, `test_course_yaml_that_is_a_list_fails_the_schema`, `test_schema_errors_are_reported_with_their_place`, `test_every_schema_error_is_reported_not_only_the_first`, `test_an_impossible_calendar_date_is_rejected` |
| `idnumber`s are unique within the course; sections and activities share one namespace | B1.2 rule 6 | `test_duplicate_idnumber_is_an_error_at_the_later_use`, `test_an_idnumber_used_three_times_is_reported_for_each_extra_use`, `test_similar_idnumbers_are_not_duplicates` |
| Protected idnumbers a site adds to the two defaults are rejected on sections and activities, in both modes. The configuration is passed in by the caller; the library reads no environment variables. The two defaults stay with the schema and get a clear message | B1.4 | `test_configured_protected_idnumber_is_rejected_in_both_modes`, `test_only_an_exact_match_is_protected`, `test_a_configured_idnumber_must_be_a_valid_idnumber`, `test_configuration_is_passed_through_to_the_course_rules`, `test_default_protected_idnumber_gets_a_clear_message`, `test_default_protected_idnumbers_are_left_to_the_schema` |
| In `full` mode the `points` of the assignments add up to `total_points` (default 100) | B1.2 rule 3 | `test_points_that_do_not_add_up_are_an_error`, `test_points_above_the_total_are_an_error_too`, `test_total_points_defaults_to_100`, `test_a_custom_total_is_used`, `test_only_assignment_points_are_counted` |
| Every `body` names a file inside the package; a missing file, a folder, and a path that leaves the package (`..`, absolute, or a link) are errors | B1.1 | `test_missing_body_file_is_an_error_at_the_activity`, `test_every_missing_body_file_is_reported`, `test_body_that_is_a_folder_is_an_error`, `test_body_that_is_a_link_leaving_the_package_is_an_error`, `test_source_*` |
| Rules that are not implemented are listed as "not checked" in every report, so that "no errors" is not read as "fully checked" (a design choice, not a PRD rule) | n/a | `test_held_rules_are_reported_as_not_checked_never_skipped_silently`, `test_rules_that_need_a_sound_structure_wait_for_it`, `test_body_files_are_not_checked_while_the_structure_is_invalid` |

Chosen narrowly where the PRD is silent, and open for the guide: the points total counts
assignments only; a `sections-only` package is reported as "points not checked" and never checked
(`test_sections_only_packages_are_not_checked_for_points`); configured protected idnumbers are
added to the two defaults, they do not replace them; two activities may share one body file.
Two tests (symlinks) are skipped on Windows without developer mode and run in CI on Linux. This
is not FR-S-03 or FR-C-03: the checker's rules (CK-xx) work on the course model (B2), which this
library does not build.

### Documented but not automatically enforced

No code checks these. The schema's `$comment` still lists them, and also lists the rules in the
section above, which are now enforced by the validator (that text is a contract file and has not
been changed; see the pull request description).

| Rule | PRD | Where the PRD places it |
|---|---|---|
| One guide Page and one task Assignment per week | B1.2 rule 1 | No checker rule is named for it (CK-01…CK-13). Ownership open (Studio design §12 item 26) |
| Week N unlocks when the week N-1 task is submitted; `unlock.after` names an existing earlier activity | B1.2 rule 2 | Related: CK-04, CK-05 (FR-C-03, R1). Ownership open (item 26) |
| Graded points sum to `total_points` in a `sections-only` package, and whether other items count | B1.2 rule 3 | CK-03. Open for the guide |
| Assignments use marking workflow | B1.2 rule 4 | CK-10 (not a package field) |
| Completion tracking on for every activity used in an unlock rule | B1.2 rule 5 | CK-13 |
| `idnumber`s are never reused for a different activity | B1.2 rule 6 | Needs the previous package version (Course Studio); no PRD rule |
| Marking table present and valid: markers, columns, points sum, allowed `Check` names | B1.3, C3.5 | CK-09. Parser ownership and argument formats open (grading design Q39) |
| `protected_section` collision | B1.4 | CK-07 for the course model; `protected_section` has no default in the PRD |

### Not mapped

Left out because the PRD does not establish the mapping:

- **A row, demo step and Bloom level for FR-S-03.** See the note at the top of this section. PRD
  C1.12 gives levels to kinds of work (for example "Design (L6): schema, validator, generator"),
  not to individual requirements.
- **FR-S-02, FR-S-04, FR-S-07, FR-S-08, FR-C-01, FR-G-01.** They touch B1 but need code that does
  not exist yet, and the PRD does not say that schema tests count towards them.
- **C1.7 "a package containing a protected idnumber is rejected with a clear message".** The
  validator rejects protected idnumbers with a clear message (tested above); the Course Studio
  screen and CLI that show it do not exist yet.
- **Requirement IDs for the contract work itself.** None in the PRD.

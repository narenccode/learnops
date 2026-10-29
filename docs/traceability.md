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

## B8.4 synthetic submissions (PROVISIONAL pilot), Release 0 foundation

Files: `testdata/b8-4-synthetic-submissions/` (manifest, four schemas, six submissions),
`libs/contracts/tests/test_b8_4_dataset.py`. B8.4 is a test-data set (PRD B8) with no requirement
ID of its own, so no row in the table above maps to it. It is the dataset for the PRD C3.7
agreement criterion (G-5), which belongs to Release 4 work that does not exist yet.

### Covered by automated tests

| Rule | Source | Test(s) |
|---|---|---|
| Manifest, submission, expected-outcome and reference-grade documents validate against their schemas | Proposed format (set README, O7) | `test_schema_is_a_valid_draft_2020_12_schema`, `test_manifest_is_valid`, `test_submission_and_expected_outcome_are_valid`, `test_reference_grade_files_are_valid` |
| Each submission has a repository, a demo link and a short report | PRD B8 | `test_submission_and_expected_outcome_are_valid` |
| Submission, rubric, course package and marking table link up; points sum; only the six check names | PRD B1.3, C3.5 | `test_ids_are_unique_and_match_folders`, `test_references_resolve`, `test_rubric_sources_exist_and_match_the_course_package` |
| Expected outcomes follow the marking table, carry no scores and agree with the files | Proposed (set README) | `test_expected_outcome_follows_the_marking_table`, `test_expected_check_results_agree_with_the_files` |
| Reference-grade cross-field rules (criteria match, score range, total = sum) | PRD B8, C3.3 FR-G-03 (sum) | `test_reference_grade_rules_catch_bad_grades` |
| Across quality levels | PRD B8 | `test_pilot_covers_every_intended_level` |
| No real learner data (fictional hosts only, no email addresses, small text files) | PRD B8, C-07 | `test_no_real_hosts_or_email_addresses`, `test_files_are_small_text` |
| Provisional labelling | Set README | `test_provisional_set_marks_everything_provisional`, `test_tags_agree_with_expected_outcomes` |

### Not met yet, and not tested

- At least 30 submissions (pilot: 6) and reference grades from at least one mentor (none; Q13).
- Rubrics from B8.2 (pilot uses the B1 contract example); the Moodle form of a submission (Q32).
- Word-count and heading-matching rules are provisional (Q39). See the open decisions in
  `testdata/b8-4-synthetic-submissions/README.md`.

# Traceability (PRD E4)

| Requirement | Test(s) | Demo step | Bloom level |
|---|---|---|---|

## B1 course package contract (v1), Release 0 foundation

Files: `contracts/course-package.v1.schema.json`, `contracts/examples/course-package.v1/`,
`libs/contracts/tests/test_course_package_v1.py`; the package validator in `libs/contracts/*.py`
(shared validator reference EXT-09: the schema stage, idnumbers unique within one package,
configured protected idnumbers, and reading a package folder with its body files) with its tests
`test_validate_course.py`, `test_validate_package.py`, `test_config.py` and `test_report.py`. B1 has no requirement ID of its own in the PRD (it is a contract, PRD B.0), so
no row in the table above maps to it.

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

`validate_course_document()` runs the schema on a parsed `course.yaml`, then (when the structure
is valid) the idnumber rules, and returns a report. `validate_package()` does the same for a
package folder: it reads `course.yaml` first and, when that is valid, also checks the body files. Settings come in through `ValidationConfig`;
the library reads no environment variables. Test names are in `test_validate_course.py`
(course.yaml as parsed data), `test_validate_package.py` (a package folder), `test_config.py` (the settings object) and `test_report.py` (the
report types).

**B1.2 rule 6 has two halves, and only the first is enforced.** The validator checks that
`idnumber`s are unique *within the one package it is given*. It does not check that an idnumber is
*never reused for a different activity* across package versions: that needs information about the
previous version of the package and an owner that is not assigned yet (Studio's design proposes a
comparison with the previous version, `docs/design/studio.md` §5 "Identity", which is a
proposal and not decided). Every
report lists that half as not checked (`idnumber_reuse_not_checked`). Rule 6 is therefore not
claimed as fully implemented.

| Rule | PRD | Test(s) |
|---|---|---|
| The schema is applied to a parsed `course.yaml`; every error is reported (not only the first), in a fixed order by place (list positions in numeric order: `sections[2]` before `sections[10]`), with its place, a message and a fix hint; an impossible calendar date and a document that is not an object are errors | B.0 rule 4, B1.1 | `test_example_document_has_no_errors`, `test_schema_errors_are_reported_with_their_place`, `test_every_schema_error_is_reported_not_only_the_first`, `test_errors_are_ordered_by_number_not_by_text`, `test_an_impossible_calendar_date_is_rejected`, `test_a_document_that_is_not_an_object_is_an_error` |
| The two default protected idnumbers are rejected with a clear message that names the place and says what to do; the validator reports each one once | B1.4 | `test_default_protected_idnumbers_are_left_to_the_schema`, `test_default_protected_idnumber_gets_a_clear_message` |
| **Uniqueness within one package** (first half of rule 6): `idnumber`s are unique in the `course.yaml` being checked. Sections and activities share one namespace. The later use in document order is the error, with its exact place, and the message names the first use. Reported in both modes. Two different duplicated ids are reported in document order | B1.2 rule 6 | `test_duplicate_idnumber_is_an_error_at_the_later_use` (7 cases, each with the exact error place and first-use place, including an activity reusing an earlier or a later section id), `test_an_idnumber_used_three_times_is_reported_for_each_extra_use`, `test_two_different_duplicated_ids_are_both_reported_in_document_order`, `test_similar_idnumbers_are_not_duplicates`, `test_duplicate_idnumbers_are_an_error_in_sections_only_mode_too` |
| **Not enforced: reuse across package versions** (second half of rule 6) is listed in every report as `idnumber_reuse_not_checked`, with a message that says why (it needs the previous version of the package) | B1.2 rule 6 | `test_cross_version_reuse_of_idnumbers_is_listed_as_not_checked`, `test_held_rules_are_reported_as_not_checked_never_skipped_silently` |
| Protected idnumbers a site adds to the two defaults are rejected on sections and activities, in both modes, with the exact place, the idnumber and a fix hint. They add to the defaults and never replace them, are matched exactly, and several can be configured. The result does not depend on the order in which they were given | B1.4 | `test_configured_protected_idnumber_is_rejected_in_both_modes`, `test_the_library_reads_no_environment_variables` (also: not protected unless configured), `test_only_an_exact_match_is_protected`, `test_several_configured_ids_are_each_rejected_in_document_order`, `test_protected_and_duplicate_problems_are_both_reported`, `test_a_default_protected_id_is_always_rejected_and_reported_once` |
| `ValidationConfig` accepts a collection of valid idnumbers and keeps its own immutable `frozenset` copy (later changes to the caller's collection do not reach it; equal configurations hash alike). It refuses with a `ConfigError` that says what to fix: a bare string or bytes (which would be read one character at a time), `None` or any non-collection, a mapping, a member that is not text, and an invalid idnumber (the first bad one in sorted order is named) | B1.4 | `test_config.py`: `test_default_configuration_adds_no_protected_idnumbers`, `test_several_configured_ids_are_kept_and_the_same_id_twice_counts_once`, `test_any_collection_of_idnumbers_is_stored_as_a_frozenset`, `test_the_configuration_cannot_be_changed_after_creation`, `test_changing_the_callers_collection_later_does_not_change_the_configuration`, `test_equal_configurations_are_equal_and_hash_alike_whatever_they_were_built_from`, `test_a_configured_idnumber_must_be_a_valid_idnumber`, `test_a_bad_idnumber_message_names_the_value_and_what_to_do`, `test_something_that_is_not_a_collection_of_idnumbers_is_refused`, `test_a_member_that_is_not_text_is_refused` |
| `validate_course_document()` refuses a `config` that is not a `ValidationConfig` (a dict, a list, a string, the class itself) with a `ConfigError` that says what to pass, before the document is read; it never ignores it | B1.4 | `test_an_unsupported_config_type_is_refused_not_ignored` |
| The library reads no environment variables; validation does not change the document it is given | CLAUDE.md §2.3 | `test_the_library_reads_no_environment_variables`, `test_the_document_is_not_changed_by_validation` |
| The idnumber rules run only when the schema finds no error anywhere in the document (an unrelated schema error holds them back too, and so does a document that is not an object). The report then adds `cross_rules_not_checked`, whose text names no rule so that it stays true as more rules are implemented | n/a | `test_any_schema_error_holds_back_the_idnumber_rules`, `test_a_document_that_is_not_an_object_is_an_error` (also checks the notice), `test_the_course_level_notice_names_no_rule` (a valid document has no such notice: `test_held_rules_are_reported_as_not_checked_never_skipped_silently`) |
| Rules that are not implemented are listed as "not checked" in every report, so that "no errors" is not read as "fully checked" (a design choice, not a PRD rule). A report for a parsed document lists eight (see the next section). A report for a package lists seven, because it checked the body files | n/a | `test_held_rules_are_reported_as_not_checked_never_skipped_silently`, `test_a_document_with_weekly_structure_problems_is_not_judged_here`, `test_example_package_has_no_errors` |
| A package folder is read through a `PackageSource`; `DirectorySource` never reads outside the folder: a path with `..`, an absolute path or a link that leaves the folder is refused, a link that stays inside is followed. A refused file is never read | B1.1 | `test_source_reads_an_existing_file`, `test_source_tells_a_missing_file_from_a_folder`, `test_source_refuses_paths_that_leave_the_package`, `test_source_refuses_a_link_that_leaves_the_package`, `test_source_follows_a_link_that_stays_inside_the_package` (the two link tests run on the Linux CI) |
| `validate_package()` reads `course.yaml` from the folder. A missing file, text that is not UTF-8, bad YAML (also an unquoted impossible date), and a file that is not an object are errors with a fix hint, never an exception; an unquoted real date fails the schema | B1.1 | `test_missing_course_yaml_is_an_error`, `test_course_yaml_that_cannot_be_read_is_an_error`, `test_an_unquoted_yaml_date_is_an_error`, `test_course_yaml_that_is_not_an_object_fails_the_schema` |
| **Body files exist** (B1.1: the package is a folder with `course.yaml` plus the Markdown files; implied, not a numbered rule). Each `body` must name a file inside the package, in both modes. A missing file, a folder and a link leaving the folder are errors at the activity, in document order, after the idnumber errors. A shared body file and an activity without a body are not errors. Only existence is checked, never the content | B1.1 | `test_missing_body_file_is_an_error_at_the_activity`, `test_every_missing_body_file_is_reported_in_document_order`, `test_body_that_is_a_folder_is_an_error`, `test_body_that_is_a_link_leaving_the_package_is_an_error`, `test_a_body_file_may_be_shared_and_an_activity_may_have_no_body`, `test_duplicate_idnumbers_are_reported_before_missing_body_files`, `test_any_package_source_works_and_only_course_yaml_is_read` |
| **Unlock rule by mode** (B1.2 rule 2, guide-confirmed). "Previous" is document order; the section number, `idnumber` and title are not read. An absent `unlock` equals both fields null. Full: the first section must have `after` null (a start date is allowed), because nothing earlier exists to name; every later section needs `after` naming the single assignment of the section just before it, and that section must hold exactly one assignment, or it is reported; `start_date` is optional and never replaces `after`; the last section may hold any number of assignments. Sections-only: every listed section, a single one included, needs `after`. It may name a template activity the package lacks; that is not a package error, and a name that matches nothing after the merge is the checker's CK-04. It must not name an activity of its own section or of a later section; cycles across sections are the checker's CK-05. Only the idnumber's shape is judged, by the schema. Reported as `unlock_after_missing`, `unlock_after_not_previous_task`, `unlock_after_on_first_section`, `unlock_previous_task_count` and `unlock_after_forward_reference` | B1.2 rule 2 | `test_full_mode_first_section_is_valid_in_every_form`, `test_full_mode_first_section_must_not_have_after`, `test_full_mode_later_section_with_the_previous_task_is_valid`, `test_full_mode_later_section_without_after_is_rejected`, `test_full_mode_after_must_be_the_previous_weeks_task`, `test_full_mode_previous_section_with_two_assignments_is_reported`, `test_full_mode_previous_section_without_an_assignment_is_reported`, `test_the_last_section_may_have_any_number_of_assignments`, `test_previous_week_follows_document_order_not_the_section_number`, `test_sections_only_after_may_name_an_activity_that_only_the_template_has`, `test_sections_only_section_without_after_is_rejected`, `test_sections_only_after_naming_a_later_section_is_a_forward_reference`, `test_sections_only_a_reference_inside_its_own_section_is_rejected`, `test_sections_only_template_references_stay_accepted`, `test_sections_only_a_cycle_through_the_template_is_not_a_package_error`, `test_a_single_section_sections_only_package_still_needs_after`, `test_a_moodle_assign_type_never_reaches_the_unlock_rule`, `test_a_badly_shaped_after_is_a_schema_error_and_the_unlock_rules_wait` |
| **Availability JSON is read by type, and `cm = -1`** (B2, guide-confirmed, still provisional until verified on Moodle 4.5 and 5.3). `libs/contracts/availability.py` finds conditions by `type`, never by position, and resolves -1 to the nearest earlier activity with manual or automatic tracking; none eligible gives None. For a section's availability, "earlier" is strictly before the section: the last tracked activity of the earlier sections, never an activity inside the section itself. An index outside the model is refused with a `ValueError`, never resolved to another activity. Nested groups (`c`) are searched as an implementation detail; B2 does not constrain the nesting It does not report CK-04 | B2 | `test_condition_order_does_not_change_the_interpretation`, `test_minus_one_resolves_to_the_previous_tracked_activity`, `test_minus_one_skips_activities_without_tracking`, `test_minus_one_with_no_eligible_earlier_activity_cannot_be_met`, `test_a_section_rule_never_resolves_to_an_activity_inside_the_same_section`, `test_a_section_rule_resolves_to_the_last_tracked_activity_of_the_section_before`, `test_an_out_of_range_holder_never_returns_the_last_tracked_activity` |
| `body_files_not_checked` is listed for a parsed document (it reads no files) and for a package whose `course.yaml` could not be validated, and is left out only when the body files were checked. The idnumber rules and the settings apply to a package too, and a wrong `config` is refused before anything is read | B1.1 | `test_body_files_are_listed_as_not_checked_and_never_looked_for`, `test_body_files_are_not_checked_while_the_structure_is_invalid`, `test_the_other_course_rules_and_the_settings_also_apply_to_a_package`, `test_a_wrong_config_is_refused_before_anything_is_read` |
| A report is ok when it has no errors; "not checked" entries do not make it fail; issues cannot be changed after creation | n/a | `test_empty_report_is_ok`, `test_report_with_an_error_is_not_ok`, `test_not_checked_items_do_not_make_a_report_fail`, `test_issue_defaults_are_a_document_level_issue`, `test_issue_cannot_be_changed_after_creation` |

This is not FR-S-03 or FR-C-03: the checker's rules (CK-xx) work on the course model (B2), which
this library does not build.

### Documented but not automatically enforced

Nothing in the repository enforces these yet. Each is listed as "not checked" in every report the
validator returns (seven entries, plus the body files when they were not checked; the B1.3 row
has two of them, and rule 4 has none because it is not a package field).
The schema's `$comment` lists them too, and also lists the two parts that the validator now
enforces (rule 6 within one package, configured protected idnumbers). Updating that comment
needs a separate contract-change review and is not part of this change. The example package was
checked against these rules by hand when it was created; that check is not automated and is not
committed.

| Rule | PRD | Where the PRD places it |
|---|---|---|
| One guide Page and one task Assignment per week | B1.2 rule 1 | No checker rule is named for it (CK-01…CK-13) |
| Week N unlocks when the week N-1 task is submitted. The shape of `unlock` is enforced by validator code, by mode (see above). That `after` completes (`completion: submit`) is rule 5 below; whether a sections-only `after` resolves in the merged course is CK-04 | B1.2 rule 2 | Related: CK-04, CK-05 (FR-C-03, R1) |
| Graded points sum to `total_points` | B1.2 rule 3 | CK-03 |
| Assignments use marking workflow | B1.2 rule 4 | CK-10 (not a package field) |
| Completion tracking on for every activity used in an unlock rule | B1.2 rule 5 | CK-13 |
| An `idnumber` is never reused for a different activity (listed as `idnumber_reuse_not_checked`; uniqueness within one package is enforced above) | B1.2 rule 6, second half | The PRD states this rule. It cannot be judged from one `course.yaml`: it needs the previous package version, and no owner or checker is assigned yet (CK-06 covers duplicate or invalid idnumbers in the course model only) |
| Marking table present and valid: markers, columns, points sum, allowed `Check` names | B1.3, C3.5 | CK-09 |
| `protected_section` collision (configured protected idnumbers are enforced above) | B1.4 | `protected_section` has no default in the PRD; CK-07 covers the course model |

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

## B2 course model contract (v1), Release 0 foundation

**Status: draft. Not approved and not frozen.** Confirmed decisions and open items are in
`docs/decisions/0003-b2-course-model.md`.

Files: `contracts/course-model.v1.schema.json`, `contracts/examples/course-model.v1/`,
`libs/contracts/tests/test_course_model_v1.py`. B2 has no requirement ID of its own in the PRD (it
is a contract, PRD B.0), so no row in the table at the top of this file maps to it.

FR-C-01 ("Build the course model (B2)") is deliberately not in that table. It needs the backup
parser and package reader, which do not exist yet. FR-C-01 gets its row in the pull request that
implements it.

### B2: Enforced by the JSON Schema and covered by automated tests

Structural schema validation only. These tests do not implement CK-01 to CK-13. Test names are in
`test_course_model_v1.py`.

| Rule | PRD | Test(s) |
|---|---|---|
| The schema is valid Draft 2020-12 and both examples validate | B.0 | `test_schema_is_a_valid_draft_2020_12_schema`, `test_example_is_valid` |
| Required fields, types and enums on every object | B2 | `test_missing_required_field_is_rejected`, `test_wrong_type_or_value_is_rejected` |
| Package sources require a mode and a non-empty timezone; an `.mbz` source requires mode `full` and timezone null | B1.4, B2 | `test_package_source_without_mode_is_rejected`, `test_package_source_without_timezone_is_rejected`, `test_package_source_with_null_timezone_is_rejected`, `test_package_source_with_empty_timezone_is_rejected`, `test_example_is_valid`, `test_missing_required_field_is_rejected`, `test_wrong_type_or_value_is_rejected` |
| Assignment activities have marking fields; other activity types need none | B1.4, B2 | `test_missing_required_field_is_rejected`, `test_non_assignment_needs_no_marking_fields` |
| Unknown fields are accepted at every level | B.0, EXT-02 | `test_unknown_field_is_accepted` |
| The schema accepts a broken course, with at least one sample input per CK rule and an unknown activity type. For CK-07 this covers missing protected items only (see below). | C2.3, C2.8 | `test_broken_course_still_validates`, `test_protected_idnumbers_are_allowed_unlike_b1` |
| Permitted null and absent values, and `cm = -1` in availability | B2 | `test_valid_variation_is_accepted`, `test_sections_only_package_is_valid` |
| `source.timezone` is checked at run time with `zoneinfo.ZoneInfo`, by `validate_course_model()` (schema plus time zone, one `ValidationReport`): `Asia/Kolkata`, `Asia/Calcutta`, `UTC`, `Etc/GMT-5` pass; `UTC+5:30`, `Mars/olympus`, empty and malformed values fail; an `.mbz` null stays valid. `SITE_TIMEZONE` is required for a package model, has no default and fails closed (decision 0003 #20) | B2, B.0 rule 4 | `test_a_name_zoneinfo_resolves_is_accepted`, `test_a_name_zoneinfo_cannot_resolve_is_rejected`, `test_an_mbz_model_with_a_null_timezone_stays_valid`, `test_a_missing_site_timezone_fails_closed_and_never_defaults` |
| Activity types use B1 names. The mapping `assign` to `assignment`, `h5pactivity` to `h5p`, `page`, `url`, `label` is applied before any rule, so a source `assign` is checked as `assignment` and needs the marking fields. The raw Moodle aliases are rejected in `type`; any other type (for example `quiz`) keeps its Moodle name, is structurally valid and is reported as not checked by the checker (decision 0003 #6) | B2, C2.8 | `test_raw_moodle_alias_type_is_rejected`, `test_unknown_activity_type_is_structurally_valid`, `test_h5p_type_is_valid`, `test_assignment_type_is_valid_and_still_needs_marking_fields`, `test_non_assignment_needs_no_marking_fields` |
| `source.mode` is required for every source. A package source may use `full` or `sections-only` (values from B1.4); a `.mbz` source must use `full`, because a backup represents a whole course (decision 0003 #22) | B1.4, B2 | `test_package_source_without_mode_is_rejected`, `test_package_source_accepts_both_modes`, `test_mbz_example_states_the_full_mode`, `test_mbz_source_without_mode_is_rejected`, `test_mbz_source_with_null_mode_is_rejected`, `test_mbz_source_must_use_the_full_mode`, `test_wrong_type_or_value_is_rejected` |
| The package example matches the B1 example, including `completion: submit` and an unlock date at 00:00 in the site timezone | B1, B2 | `test_package_example_matches_b1_example`, `test_package_example_unlock_rule_matches_b1_example` |
| The examples contain every field in the CK-rule-to-field mapping (`CK_FIELDS` in the test file). The mapping is **proposed and unapproved**, because the PRD's rules do not name model fields. Presence only. | C2.3 | `test_examples_carry_the_fields_a_rule_needs` |

### B2: Documented but not automatically enforced

The schema must not enforce the CK rules: a course that breaks them has to validate so that the
checker can report it. No parser, evaluator or rule engine exists yet, so no test here shows that
any rule works.

- Rules CK-01 to CK-13 (FR-C-03, Release 1).
- Reading `SITE_TIMEZONE` and storing it in `source.timezone` when a model is built from a package: the builder (FR-C-01, Release 1) does not exist. The builder must call `site_timezone(os.environ)` and then validate the model with `validate_course_model()`, whose run-time check uses the helper `timezone_issues()` (decision 0003 #20).
- CK-07 beyond representation: the tests show that a course with its protected items missing can be
  represented. They do not establish detection of duplicated or changed protected items. B2 holds
  no body text or attached files, so a reference-model comparison cannot see changes to them.
- CK-07 reference model (design decision, not implemented; decision 0003 #21, `docs/design/checker.md`
  risk 11): the reference is the B2 model of the B8.1 template built from its `.mbz` backup, supplied
  with `--reference-model <path>`. When it is absent, CK-07 reports `not checked` for the run.
- Treating a null `visible` or `completion_enabled` as "cannot judge" (the checker's job), and
  resolving `cm = -1` by decision 0003 #5: the nearest earlier activity in course order with
  manual or automatic completion tracking. Activities without tracking are skipped. If no
  eligible activity exists, the condition cannot be met; an unresolved `-1` is reported as
  CK-04. This resolution is documented but not automatically enforced yet; Moodle 4.5 and
  5.3 lab verification remains pending.
- Unique `cmid` values within a model (the model builder's job, FR-C-01).
- The inner form of `availability`, which belongs to Moodle.
- Comparing a package model with a `.mbz` model: `cmid` values differ, so FR-C-05 compares
  activities by idnumber and sections by section number; section idnumber is ignored.

### B2: Not mapped

- **FR-C-01, FR-C-02, FR-C-03, FR-C-05.** They use B2 but need code that does not exist yet, and the
  PRD does not say that schema tests count towards them.
- **Requirement IDs for the contract work itself.** None in the PRD.

## B8.1 template course backup (test data), Release 0 foundation

Files: `testdata/b8-1-template-course/README.md` (the requirements, the proposals and the open
decisions, and a plain list of the expected protected items for the checker); the B8.1 entry in
`testdata/README.md`. B8.1 is a test data set (PRD §B8, B1.4) and has no requirement ID of its own,
so no row in the table at the top maps to it. This change is documentation only: no `.mbz`, no code
and no test exist for B8.1 yet.

| What is documented | PRD | Test(s) |
|---|---|---|
| The template course backup holds the four protected items: the final project assignment (`final-project`), the course feedback activity (`course-feedback`), the course completion criteria and the course badge. The idnumbers are the PRD defaults and are configurable. The protected section number (3) is a proposal | B8.1, B1.4 | None yet: the `.mbz` does not exist |
| A plain list of the expected protected items (idnumber, type, section, count) for the checker, which builds its model from the `.mbz` | B8.1, B1.4 | None yet |
| A sections-only backup is merged into the template and the protected items stay unchanged. The intended comparison writes down the same table for each protected item before and after the merge, with the fields type, name, idnumber, section number, points, completion setting and visibility, and the two tables must be equal (Owner, Issue #55, 2026-11-12); no check or test implements this yet. The Release 0 backup procedure is written as an untested draft | B1.4, C1.7, App-C item 2 | None yet: needs a Moodle site |
| Moodle 4.5 is the owner-confirmed build version. The owner stated that a 4.5 backup restores into the same or a newer Moodle version, including 5.3. That 4.5-to-5.3 restore is the owner's statement, not a result. The owner decided to build once on 4.5, test the restore on 4.5 and on 5.3, and not test 5.3 to 4.5, recording the Moodle version, the date and the outcome of each restore (Issue #55, 2026-11-12) | C-03 | None yet: not verified; needs Moodle lab testing on 4.5 and 5.3 |

### Not covered here

These are pending and are not claimed by this change:

- **The `.mbz` backup, its SHA-256, the release asset (tag `testdata-b8-1-v1`) and the download
  script.** None of them exists yet.
- **Moodle 4.5 and 5.3 verification:** the restore, the protected items, the completion criteria,
  the badge and the sections-only merge (PRD C1.7, App-C item 2). The owner's statement that a 4.5
  backup restores on 5.3 has not been verified.
- **The decision record for App-C item 2** (`docs/decisions/NNNN-b8-1-template-course.md`). It is
  not written; the next free number is taken when you merge, after rebasing (Owner, Issue #55). The
  owner also asks for a short, text-only results table in it that names the local evidence files;
  screenshots and logs stay local and are not committed.
- **The open decisions** in the B8.1 README (§9) are pending guide confirmation. This entry does
  not settle them.

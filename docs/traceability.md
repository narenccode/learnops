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
| Rules that are not implemented are listed as "not checked" in every report, so that "no errors" is not read as "fully checked" (a design choice, not a PRD rule). A report for a parsed document lists nine (see the next section). A report for a package lists eight, because it checked the body files | n/a | `test_held_rules_are_reported_as_not_checked_never_skipped_silently`, `test_a_document_with_weekly_structure_problems_is_not_judged_here`, `test_example_package_has_no_errors` |
| A package folder is read through a `PackageSource`; `DirectorySource` never reads outside the folder: a path with `..`, an absolute path or a link that leaves the folder is refused, a link that stays inside is followed. A refused file is never read | B1.1 | `test_source_reads_an_existing_file`, `test_source_tells_a_missing_file_from_a_folder`, `test_source_refuses_paths_that_leave_the_package`, `test_source_refuses_a_link_that_leaves_the_package`, `test_source_follows_a_link_that_stays_inside_the_package` (the two link tests run on the Linux CI) |
| `validate_package()` reads `course.yaml` from the folder. A missing file, text that is not UTF-8, bad YAML (also an unquoted impossible date), and a file that is not an object are errors with a fix hint, never an exception; an unquoted real date fails the schema | B1.1 | `test_missing_course_yaml_is_an_error`, `test_course_yaml_that_cannot_be_read_is_an_error`, `test_an_unquoted_yaml_date_is_an_error`, `test_course_yaml_that_is_not_an_object_fails_the_schema` |
| **Body files exist** (B1.1: the package is a folder with `course.yaml` plus the Markdown files; implied, not a numbered rule). Each `body` must name a file inside the package, in both modes. A missing file, a folder and a link leaving the folder are errors at the activity, in document order, after the idnumber errors. A shared body file and an activity without a body are not errors. Only existence is checked, never the content | B1.1 | `test_missing_body_file_is_an_error_at_the_activity`, `test_every_missing_body_file_is_reported_in_document_order`, `test_body_that_is_a_folder_is_an_error`, `test_body_that_is_a_link_leaving_the_package_is_an_error`, `test_a_body_file_may_be_shared_and_an_activity_may_have_no_body`, `test_duplicate_idnumbers_are_reported_before_missing_body_files`, `test_any_package_source_works_and_only_course_yaml_is_read` |
| `body_files_not_checked` is listed for a parsed document (it reads no files) and for a package whose `course.yaml` could not be validated, and is left out only when the body files were checked. The idnumber rules and the settings apply to a package too, and a wrong `config` is refused before anything is read | B1.1 | `test_body_files_are_listed_as_not_checked_and_never_looked_for`, `test_body_files_are_not_checked_while_the_structure_is_invalid`, `test_the_other_course_rules_and_the_settings_also_apply_to_a_package`, `test_a_wrong_config_is_refused_before_anything_is_read` |
| A report is ok when it has no errors; "not checked" entries do not make it fail; issues cannot be changed after creation | n/a | `test_empty_report_is_ok`, `test_report_with_an_error_is_not_ok`, `test_not_checked_items_do_not_make_a_report_fail`, `test_issue_defaults_are_a_document_level_issue`, `test_issue_cannot_be_changed_after_creation` |

This is not FR-S-03 or FR-C-03: the checker's rules (CK-xx) work on the course model (B2), which
this library does not build.

### Documented but not automatically enforced

Nothing in the repository enforces these yet. Each is listed as "not checked" in every report the
validator returns (eight entries, plus the body files when they were not checked; the B1.3 row
has two of them, and rule 4 has none because it is not a package field).
The schema's `$comment` lists them too, and also lists the two parts that the validator now
enforces (rule 6 within one package, configured protected idnumbers). Updating that comment
needs a separate contract-change review and is not part of this change. The example package was
checked against these rules by hand when it was created; that check is not automated and is not
committed.

| Rule | PRD | Where the PRD places it |
|---|---|---|
| One guide Page and one task Assignment per week | B1.2 rule 1 | No checker rule is named for it (CK-01…CK-13) |
| Week N unlocks when the week N-1 task is submitted; `unlock.after` names an existing earlier activity | B1.2 rule 2 | Related: CK-04, CK-05 (FR-C-03, R1) |
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

## B7 H5P practice output contract (v1), Release 0 foundation, DRAFT

Files: `contracts/h5p-practice.v1.md` (normative text), `contracts/h5p-practice.v1.schema.json`,
`contracts/examples/h5p-practice.v1.content-types.json`, `contracts/examples/h5p-practice.v1/`
(an example package, with no `.h5p` file), the `file` field in
`contracts/course-package.v1.schema.json`, and the tests `test_h5p_practice_v1.py` and
`test_course_package_v1.py` in `libs/contracts/tests/`. B7 has no requirement ID of its own in the
PRD (it is a contract, PRD B.0). It is used by FR-S-12 and FR-V-14 (Release 5, stretch) and by
FR-C-03 CK-11 (Release 1). No row in the table at the top maps to it.

**Status: draft, not approved, and it cannot be frozen** until the H5P library versions are
verified in the lab (PRD App-C item 5; guide's answer 5 on Issue #44). The B1 section above is on
main; the B1 `file` field added with B7 is covered in the first table below.

### Enforced by the B1 schema; tests in `test_course_package_v1.py`

| Rule | PRD | Test(s) |
|---|---|---|
| An `h5p` activity must have `graded: false` and `file` | B7, Issue #44 answer 2 | `test_missing_required_field_is_rejected`, `test_wrong_type_or_value_is_rejected`, `test_h5p_missing_field_is_named_and_only_that_field` |
| `file` is a relative path ending in lowercase `.h5p`; URLs, absolute paths, `..`, backslashes, other or upper-case extensions and an empty name are rejected | B7, C-08 | `test_h5p_file_that_is_not_a_relative_h5p_path_is_rejected` |
| `file` is not checked on other activity types (it is an unknown field there) | Issue #44 answer 2 | `test_valid_variation_is_accepted` |
| An `h5p` activity cannot take a protected idnumber | B1.4 | `test_h5p_with_a_protected_idnumber_is_rejected` |

### Enforced by the B7 schema; tests in `test_h5p_practice_v1.py`

Rows that say "example only" check the example package, not packages in general.

| Rule | PRD | Test(s) |
|---|---|---|
| The content-type schema is valid and its example validates; bad lists are rejected: invented names, other capitals, machine names, half a phrase, a name listed twice, a missing name, a wrong schema name, an empty list | B.0 rule 1 | `test_schema_is_valid_and_example_validates`, `test_invalid_content_type_list_is_rejected`, `test_missing_root_field_is_rejected`, `test_unknown_fields_are_accepted` |
| The schema enum holds exactly the four phrases PRD B7 uses, and the example lists all four; the contract text says interactive video is for lab demonstrations only (a rule of the text, not a schema field) | B7 | `test_schema_enum_and_example_hold_exactly_the_prd_phrases` |
| The schema and example have no key `version`, `library`, `libraries` or `machine_name`, no string like `H5P.<letter>`, and no key `cue`, `cues` or `ref`. Other ways to write a version are not detected | App-C item 5, B6.2 | `test_no_listed_machine_name_version_or_cue_key_is_defined` |
| Every content type is marked "to verify in the lab"; the text says it cannot be frozen, keeps its open decisions marked, and says practice is optional and never graded | B7 | `test_text_marks_versions_open_decisions_and_the_draft_rules` |
| `file` is defined in the `h5p` branch of the B1 schema only | Issue #44 answer 2 | `test_file_is_defined_in_the_h5p_branch_only` |
| Example only: the package validates against B1; its week has one Page and one Assignment; its ordinary practice item is ungraded, names a lowercase `.h5p` path that does not exist, and comes right after the guide Page | B1, B7 | `test_example_package_validates_against_b1`, `test_example_week_is_standard_with_an_optional_practice_item` |
| No `.h5p` file exists anywhere in the repository | Issue #44 answer 7 | `test_no_h5p_file_is_kept_in_the_repository` |

### Documented but not automatically enforced

| Rule | PRD | Where the PRD places it |
|---|---|---|
| An ordinary practice entry comes right after the week's guide Page, and a week has one Page and one Assignment, in a package in general | B7, B1.2 rule 1 | Needs validator code; B1.2 rule 1 is itself not enforced yet |
| Where a video checkpoint goes | B7 | Open decision; PRD B7 says "after the video" |
| A practice (H5P) activity has no grade item | B7 | CK-11 (FR-C-03, Release 1), on the course model (B2) |
| Media referenced by a full fixed URL instead of a relative path | C-08 | CK-12 (FR-C-03, Release 1) |
| The file named by `file` exists, and uses an allowed content type | B7 | No check exists; no real `.h5p` is kept in the repository |
| Interactive video only in lab demonstrations | B7 | A rule of the contract text; no check exists |
| AI-drafted items are approved by a mentor before they reach learners | C-09, FR-S-12 | A process rule of Studio, not a data rule |
| `cues.json` entries are valid | B6.2, FR-V-14 | The B6 cues schema does not exist yet. Student 4 proposes `type: "h5p"` with `ref` = the practice item's `idnumber`; this is provisional, quoted in B7 section 6, and not enforced here |

### Open decisions and not mapped

Open: H5P library versions and whether "drag-the-words or drag-and-drop / ordering" is one type
(until the lab check, App-C item 5); the `ref` kinds and the cue fields (Student 4, in the B6 cues
schema, still to come; her `h5p` + `idnumber` encoding is only a proposal); several practice items in
one week and video checkpoint placement (the guide has not decided; B7 makes no rule). Not mapped: a
row, demo step and Bloom level for FR-S-12 and FR-V-14, because the PRD does not say schema tests
count towards them. This pull request adds M2 to the B7 "Used by" row in PRD B.0 (guide, Issue #44).

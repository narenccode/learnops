# Traceability (PRD E4)

| Requirement | Test(s) | Demo step | Bloom level |
|---|---|---|---|
| EXT-09, C-08 – `media_paths` library: slug, relative-path and number validation; `validate_relative_path` is the B6.3 `$defs/relative_path` rule (B6 has no requirement ID of its own, PRD B.0) | `libs/media_paths/tests/test_validation.py`: slugs `test_valid_slugs_are_accepted`, `test_invalid_slugs_are_rejected`, `test_traversal_and_non_ascii_slugs_are_rejected`, `test_validate_slug_returns_false_for_non_strings`; relative paths `test_valid_relative_paths_are_accepted`, `test_invalid_relative_paths_are_rejected`, `test_prd_b6_2_and_other_legitimate_paths_are_accepted`, `test_colon_that_is_not_a_scheme_or_drive_is_accepted`, `test_scheme_or_drive_at_the_start_is_rejected`, `test_unsafe_relative_paths_are_rejected`, `test_validate_relative_path_returns_false_for_non_strings`; Unicode Cc and complete Cf, explicit Unicode 15.0.0 tables (guide decision) `test_control_and_format_characters_are_rejected`, `test_range_tables_are_sorted_non_overlapping_and_not_adjacent`, `test_range_tables_hold_the_unicode_15_0_counts`, `test_every_range_is_rejected_at_its_edges_and_inside`, `test_code_point_next_to_a_range_is_accepted`, `test_private_use_surrogate_and_unassigned_are_not_rejected_by_category`, `test_tables_match_the_unicode_database_of_the_running_python`, `test_mismatch_check_reports_a_new_unicode_version`, `test_mismatch_check_reports_a_character_whose_category_changed`; no `%` anywhere (guide decision) `test_percent_sign_is_rejected_anywhere`, `test_encoded_characters_without_a_percent_sign_are_accepted`; same rule as the contract `test_every_valid_shared_vector_is_accepted`, `test_every_invalid_shared_vector_is_rejected`, `test_library_and_schema_pattern_agree_on_every_code_point`; helpers `test_require_slug_returns_valid_value`, `test_require_slug_error_names_the_field`, `test_require_positive_int_returns_valid_value`, `test_require_positive_int_rejects_non_integers`, `test_require_positive_int_rejects_values_below_one`, `test_require_int_in_range_returns_valid_value`, `test_require_int_in_range_rejects_values_outside_the_range`, `test_require_int_in_range_rejects_non_integers`. Not enforced in v1 (guide decision): Windows reserved names, Unicode normalization, a maximum length | Show that `validate_relative_path` accepts `slides/001.jpg` and rejects `../720p.mp4`, `%2e%2e/720p.mp4`, `lecture%20notes.mp4`, `https://example.org/x.mp4` and paths containing U+061C or U+202E, and accepts one containing U+E000; show that `require_slug("../x", "cohort")` raises a clear error | — |
| EXT-09, C-08 – `media_paths` library: B6.4 media signing interface (`none` baseline); `sign()` accepts only paths that pass `validate_relative_path`, so no `%` (B6 has no requirement ID of its own, PRD B.0) | `libs/media_paths/tests/test_signing.py`: `test_none_signer_builds_media_url`, `test_none_signer_accepts_custom_ttl`, `test_none_signer_removes_trailing_slash_from_base_url`, `test_none_signer_implements_media_signer_interface`, `test_default_ttl_matches_prd_b6_4`, `test_none_signer_output_has_no_signature_or_expiry`, `test_valid_base_urls_are_joined_with_a_single_slash`, `test_invalid_base_urls_are_rejected`, `test_base_url_error_does_not_echo_credentials`, `test_non_string_base_url_is_rejected`, `test_sign_percent_encodes_path_characters`, `test_sign_rejects_unsafe_relative_paths`, `test_decoding_a_none_signed_url_never_yields_a_traversal`, `test_sign_uses_validate_relative_path`, `test_sign_rejects_non_integer_ttl`, `test_sign_rejects_ttl_below_one`, `test_media_signing_none_returns_none_signer`, `test_create_media_signer_reads_os_environ_by_default`, `test_planned_signing_modes_raise_not_implemented_config_error`, `test_unknown_signing_modes_raise_config_error`, `test_missing_media_signing_raises_config_error`, `test_missing_media_base_url_raises_config_error`, `test_invalid_media_base_url_raises_config_error`, `test_config_error_is_a_value_error` | Select the signer with `MEDIA_SIGNING=none` and build a plain media URL; show that `%2e%2e/720p.mp4` is refused and that `hmac`/`s3` and unknown modes give a configuration error. Only `none` is implemented (enough for the baseline per B6.4) | — |

## Contract example checking engine (PRD B.0 rule 1, E1), Release 0 foundation

Files: `libs/contracts/example_check.py`, tests in `libs/contracts/tests/test_example_check.py`.
Reference EXT-09 (the `contracts` library); the E1 "Contract" test level. This is the engine of
the repository-wide validator `validate_examples.py`, added by the next pull request, so nothing
runs it in CI yet. What is not checked yet is listed in `libs/contracts/README.md`.

| Rule | PRD | Test(s) |
|---|---|---|
| Every example (JSON or YAML) is validated against its schema, with every error reported in a fixed order | E1 | `test_check_valid_example_passes`, `test_check_invalid_example_is_one_violation_with_its_place_and_keyword`, `test_check_reports_every_error_in_a_fixed_order`, `test_check_one_failure_among_passing_examples` |
| Unreadable examples, unusable schemas (unreadable, invalid, a `$schema` that is not a string) and content nested too deeply are reported with a hint instead of a traceback. A `$ref` that cannot be resolved is reported the same way, **but only when an example reaches it** | E1, B.0 rule 4 | `test_check_unreadable_example_is_an_error`, `test_check_non_string_schema_keyword_is_an_invalid_schema`, `test_check_deeply_nested_example_is_unreadable_not_a_traceback`, `test_check_recursion_while_validating_is_reported_for_each_affected_example`, `test_check_deeply_nested_schema_is_reported_and_its_examples_not_validated`, `test_check_examples_of_an_unusable_schema_are_not_validated`, `test_check_reference_reached_by_the_last_example_leaves_none_passed`, `test_check_broken_schema_without_examples_reports_only_the_schema` |
| Known limits are stated and pinned by tests, so the documents cannot promise more than the code does: a dangling `$ref` no example reaches is not found; `date` is checked but `date-time` is not; `referencing`, imported directly, is a pinned and licensed dependency | CLAUDE.md §2.10 | `test_check_dangling_reference_in_a_branch_no_example_reaches_is_not_found`, `test_check_asserts_date_but_not_date_time`, `test_check_documented_format_lists_match_the_installed_checker`, `test_referencing_is_a_declared_pinned_dependency_with_its_licence` |

## Contract examples validate against their schemas (PRD B.0 rule 1, E1), Release 0 foundation

Files: `libs/contracts/validate_examples.py` (run by CI's "Validate contract examples" step), tests
in `libs/contracts/tests/test_validate_examples.py`. Shared validator reference EXT-09 (the
`contracts` library); this is the E1 "Contract" test level ("every example ... validates against
its schema, CI, every PR"). It does not cover "generated files" from E1, because no module
generates contract files yet. What is not checked yet is listed in `libs/contracts/README.md`. Each schema and its examples are checked by the engine
(previous section).

| Rule | PRD | Test(s) |
|---|---|---|
| Every versioned schema has at least one example | B.0 rule 1 | `test_schema_without_an_example_in_either_layout_is_an_error`, `test_no_schemas_at_all_is_an_error`, `test_several_schemas_are_each_paired_with_their_own_examples`, `test_both_example_layouts_work_alone_and_together` |
| Every example (JSON or YAML) validates against its schema; CI fails otherwise | E1 | `test_real_repository_examples_all_pass`, `test_invalid_example_names_example_schema_place_and_keyword`, `test_invalid_example_is_one_schema_violation`, `test_one_failure_among_passing_examples_still_fails`, `test_script_runs_as_ci_runs_it` |
| Unreadable examples and broken schemas are errors, never skipped | E1 | `test_unreadable_example_is_an_error`, `test_examples_of_an_unusable_schema_are_counted_but_not_validated` |
| A `$ref` that an example reaches and that cannot be resolved is reported with a hint instead of a traceback. A dangling `$ref` that no example reaches is not found (engine section) | B.0 rule 4 | `test_examples_of_an_unusable_schema_are_counted_but_not_validated` (cases `dangling-local-ref`, `external-ref`) |
| Examples in the folder layout and in the flat layout `<name>.v<N>.<suffix>.json` are both validated; `v1` never takes `v10` | B.0 rule 1 | `test_both_example_layouts_work_alone_and_together`, `test_several_schemas_are_each_paired_with_their_own_examples`, `test_invalid_example_names_example_schema_place_and_keyword` (flat case) |
| The tests on the real repository list the examples of both layouts by hand, so a contract with flat examples only (#25, #27) does not break them | B.0 rule 1 | `test_both_example_layouts_work_alone_and_together`, `test_real_repository_examples_all_pass`, `test_script_runs_as_ci_runs_it` |
| One extension rule in both layouts (any case; the stem and the suffix word stay lower case), and a missing-example message that names `.json`, `.yaml` and `.yml` | B.0 rule 1, UI-05 | `test_both_example_layouts_work_alone_and_together` (case `any-case-extension`), `test_schema_without_an_example_in_either_layout_is_an_error` |
| A link to a file outside `contracts/` is followed and reported under the link's own path (documented, not refused) | EXT-09 | `test_a_link_to_a_file_outside_contracts_is_followed_and_reported_under_the_link` |

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

## B8.5 lecture video test data set, Release 0 foundation

Files: `testdata/b8-5-lecture-videos/` (README, folder `.gitignore`, placeholder outlines and
transcripts), the B8.5 inventory in `testdata/README.md`, the guide's decision
`docs/decisions/0004-b8-5-lecture-videos.md`, and the validation test
`libs/contracts/tests/test_b8_5_dataset.py`. B8.5 is a test data set (PRD B8), not a functional
requirement, so it has no FR ID and no row in the table at the top. It is the data for PRD G-6
(caption word error rate, Release 3), App-C 7 (the error-rate target from a first baseline run)
and App-C 8 (licence or consent for every B8.5 video).

**Status: PENDING.** No lecture is recorded, no consent line is written and no transcript is
typed. The tests show that the committed placeholders are well formed and that the PENDING status
is true. They do **not** show that B8.5 or App-C 8 is met.

### Enforced by the test and covered by automated tests

The checker in `test_b8_5_dataset.py` runs on the real set (two tests, first two rows) and on
synthetic sets built in a temporary folder. Each negative case checks for its exact error
message, so an unrelated error cannot keep it passing.

| Rule | Source | Test(s) |
|---|---|---|
| The committed set has no errors: the ten fixed columns and well-formed rows, at least 5 lectures with unique `lecture-NN` ids, each cell in its documented form, outlines and transcripts that exist, a decision record with the exact consent sentence and a well-formed `## Consent lines` section, and the files Git tracks in the set folder are exactly the permitted paths | B8.5, decision 0004, set README | `test_the_real_set_has_no_errors` |
| The Status is true: both READMEs agree; COMPLETE needs no gap and a real Total line; PENDING needs something still missing and keeps the Total line PENDING; the total is checked against 1800 s once durations are filled in | B8.5 (at least 30 minutes, PRD §B8 as updated in #47), decision 0004 | `test_the_real_status_is_true` |
| A complete set passes and its table parses back unchanged; a PENDING set (also a partly filled one) has no errors | B8.5, decision 0004 | `test_a_complete_set_passes_and_parses_back`, `test_a_pending_set_has_no_errors_but_is_not_complete`, `test_a_partly_filled_pending_set_has_no_errors` |
| At least 5 lectures with unique `lecture-NN` ids; total at least 1800 s; a numeric Total line equals the sum | B8.5 (≥ 5 lectures), decision 0004 (≥ 1800 s) | `test_a_broken_complete_set_fails[four-lectures, below-1800-s, wrong-total-line, duplicate-ids]` |
| The ten fixed columns; every row has exactly as many cells as the header (a `\|` in a value, an extra or a missing cell is an error, never shifted or cut) | set README | `[wrong-columns, pipe-in-a-value, extra-trailing-cell, missing-cell]` |
| Each cell in its documented form: Duration as ASCII whole seconds above 0 (Unicode digits such as `³`, `٣٦٠`, `３６０` are rejected, never a traceback), a bare recording file name (no path or URL), 64 lowercase hex SHA-256, the lecture's own outline path, review `pending` or `checked`; a PENDING value is a gap | set README | `[pending-cell, duration-*, recording-path, recording-url, sha-short, sha-uppercase, wrong-outline-path, review-pending, review-unknown]` |
| Outline and transcript exist; one that is empty or has a line starting with `PENDING` anywhere is a placeholder; a placeholder transcript cannot be `checked`; finished text with no PENDING line passes | set README ("no `PENDING` line") | `[placeholder-*, outline-pending-on-a-later-line, transcript-pending-on-a-later-line, transcript-blank-lines-only, missing-outline]`, `test_completed_text_without_a_pending_line_is_not_a_placeholder` |
| Consent: the decision record exists, states the exact sentence and has a `## Consent lines` section; lines are well formed (name, valid date, exact sentence) and unique; a lecture's Consent cell points to an existing line with the Speaker's name (compared in full, commas included); one line per speaker; every line is used | B8.5 (written consent), App-C 8, decision 0004 | `[no-decision-record, no-consent-section, no-exact-statement, consent-*, one-speaker-two-lines, unused-consent-line]`, `test_a_speaker_name_with_a_comma_is_accepted`, `test_consent_lines_outside_the_section_are_not_counted` |
| The files Git tracks in the set folder are exactly the permitted paths (no recording, audio, draft, nested or unlisted file). Ignored or untracked local files (Thumbs.db, desktop.ini, editor swap and backup files) do not count; a failing or missing `git` is an error, never a clean result | decision 0004 (recordings never in Git), set README | `[audio-wav, audio-mp3, video-mp4, draft-transcript, nested-outline, unlisted-lecture, top-level-note]`, `test_only_the_exact_permitted_paths_are_allowed`, `test_only_files_tracked_by_git_are_inspected`, `test_a_failing_git_command_is_an_error_not_a_clean_set`, `test_missing_git_is_an_error_not_a_clean_set` |
| The Status is true: both READMEs agree; COMPLETE needs no gap and a real Total line; PENDING needs something still missing and keeps the Total line PENDING (a finished set whose Status and Total lines both still say PENDING fails) | set README | `test_a_false_status_fails` (7 cases), `test_a_finished_set_cannot_hide_behind_a_pending_total` |

Names in brackets are cases of `test_a_broken_complete_set_fails`; `*` stands for every case with
that prefix.

### Not verified (by this test or anything else in the repository)

- That a recording exists, that its duration and SHA-256 are right, that the speech is Indian
  English, or that the speaker spoke from the outline (checked by people).
- That a transcript is accurate (Harshitha's check) and which model, if any, drafted it.
- That recordings are stored as agreed, and that speakers were told about the interim storage.
- That a speaker personally wrote their consent line (shown by Git history and review).
- Any use of the set by the video pipeline or the caption error-rate measurement (G-6, App-C 7);
  no Moodle restore, checker, BigBlueButton or Moodle 4.5/5.3 integration is involved or tested.

## B6 lesson manifest contract (v1), Release 0 foundation

Files: `contracts/lesson-manifest.v1.schema.json`, `contracts/examples/lesson-manifest.v1/`
(`single-track.json`, `camera-screen.json`: one top-level file per example),
`libs/contracts/tests/test_lesson_manifest_v1.py`. B6 has no requirement ID of its own in the PRD
(it is a contract, PRD B.0), so no row in the table above maps to it.

FR-V-08 ("Write `lesson.json` (B6.3) last, only when all required files exist", Release 3) is
deliberately not in the table above. The tests below cover only the schema that FR-V-08 and the
C4.7 criterion "`lesson.json` validates against B6.3" will be checked against. FR-V-08 gets its row
in the pull request that implements it.

### Enforced by the JSON Schema and covered by automated tests

Structure only. Test names are in `test_lesson_manifest_v1.py`.

| Rule | PRD | Test(s) |
|---|---|---|
| `schema` equals `learnops.lesson/v1` | B6.3 | `test_missing_required_field_is_rejected`, `test_wrong_type_or_value_is_rejected` |
| Nine root fields required: `schema`, `course_slug`, `lesson_id`, `title`, `duration_s`, `tracks`, `captions`, `transcript`, `chapters`; `slides`, `cues`, `summary`, `source`, `processing` optional | B6.2, B6.3 | `test_schema_requires_exactly_the_nine_root_fields`, `test_missing_required_field_is_rejected`, `test_valid_variation_is_accepted` |
| Exactly one `main` track | B6.2, B6.3 | `test_invalid_track_is_rejected`, `test_example_manifest_is_valid` |
| At least one caption with `lang` exactly `en` (`hi`, `EN` or `en-US` alone is rejected), because B6.2 requires `captions.en.vtt` (guide decision) | B6.2, B6.3 | `test_captions_without_english_are_rejected`, `test_captions_with_english_are_accepted`, `test_valid_variation_is_accepted` |
| Track roles are open lowercase names (slug form); known roles `main`, `main-low`, `camera`, `screen`; others such as `audio` accepted | B6.3 | `test_invalid_track_is_rejected`, `test_added_track_with_known_or_new_lowercase_role_is_accepted`, `test_examples_use_every_known_track_role` |
| A single-track lesson stays valid when `camera` and `screen` tracks are added | C4.7, EXT-03 | `test_single_track_lesson_stays_valid_with_camera_and_screen_added` |
| Every path is relative (`$defs/relative_path`): non-empty; forward slashes only; no whitespace; no `?`, `#` or backslash; no URL scheme or drive letter; not absolute; no empty, `.` or `..` segment; no Unicode control or format character (the complete Unicode 15.0.0 categories Cc and Cf, pinned; private-use, surrogate and unassigned code points accepted; guide decision); no `%` anywhere, so no percent-encoded form however often encoded (`%2e`, `%252e`, `%25%32%65` and so on; guide decision, because the B6.4 `none` signer appends the path to the media base URL and layers may decode it; paths are never decoded). Applied to all eight path fields: the seven file paths (`tracks[].file`, `captions[].file`, `transcript`, `chapters`, `slides`, `cues`, `summary`) are relative to the lesson folder, and `lesson_id` is relative to the course folder (readers build the lesson folder's path from it). Valid and invalid cases come from the shared vectors `contracts/test-vectors/relative-path.v1.json`. The schema defines the rule; `libs/media_paths` (B6.1 folder paths, the B6.4 `relative_path` argument) is to follow the same vectors, tested in its own pull request | B6.1, B6.3, B6.4, C-08, EXT-09 | `test_path_that_is_not_relative_is_rejected`, `test_valid_relative_path_is_accepted`, `test_every_path_field_in_the_schema_is_tested`, `test_path_vectors_cover_every_rule`, `test_path_vectors_have_no_duplicates`, `test_lesson_id_that_is_not_a_relative_path_is_rejected`, `test_lesson_id_that_is_a_lesson_slug_path_is_accepted`; Cc and Cf `test_python_unicode_database_is_the_pinned_version`, `test_unicode_15_0_has_2_cc_and_21_cf_ranges`, `test_schema_rejects_exactly_cc_and_cf_among_all_code_points`, `test_every_cc_and_cf_range_is_rejected_at_its_edges_and_inside`, `test_code_point_next_to_a_cc_or_cf_range_is_accepted`, `test_private_use_surrogate_and_unassigned_are_not_rejected_by_category`, `test_every_path_field_rejects_control_and_format_characters`; percent sign `test_percent_sign_is_rejected_in_every_segment`, `test_every_path_vector_with_a_percent_sign_is_invalid` |
| `course_slug` is lowercase ASCII with hyphens | B6.1 | `test_invalid_course_slug_is_rejected` |
| Unknown fields are accepted | B.0 rule 2, EXT-02 | `test_valid_variation_is_accepted` |
| The manifest is a JSON object (an array, a string, a number or `null` is rejected) | B6.3 | `test_document_that_is_not_an_object_is_rejected` |
| The schema is valid; both examples and the PRD B6.3 example validate | B.0 rule 1 | `test_schema_is_a_valid_draft_2020_12_schema`, `test_example_manifest_is_valid`, `test_prd_example_is_valid` |

Enforced and tested, but chosen in the schema rather than stated as a rule in the PRD (to be
confirmed by the contract reviewers): `source.kind` is required inside `source` but is any non-empty string (the PRD names only
`upload`); `captions` not empty; `height` a positive integer; `duration_s` a non-negative number;
`processing.completed_at` an RFC 3339 timestamp with a time zone; non-empty strings. Tests:
`test_invalid_completed_at_is_rejected` (`completed_at`), `test_missing_required_field_is_rejected`,
`test_invalid_track_is_rejected`, `test_wrong_type_or_value_is_rejected`, `test_valid_variation_is_accepted`.

### Documented but not automatically enforced

| Rule | PRD | Where the PRD places it |
|---|---|---|
| The files the manifest names, and `poster.jpg`, exist in the lesson folder | B6.2 | FR-V-08 (R3) |
| `lesson.json` written last, only when all required files exist | B6.2 | FR-V-08 (R3) |
| `course_slug` and `lesson_id` match the folder's place in the path template | B6.1 | `libs/media_paths` (Release 0, separate pull request) |
| Calendar validity of `processing.completed_at` (for example no 31 February) | — | Only with a `date-time` format checker (`rfc3339-validator`, not installed in CI) |
| Contents of `transcript.en.json` (B5.4 shape) | B5.4, B6.2 | B5 contract (no schema in `contracts/` yet) |
| Shapes of `chapters.json`, `slides.json`, `cues.json` | B6.2 | No schema yet |
| Windows reserved names (such as `CON`, `NUL`, `COM1`) and Unicode normalization in paths: considered, not v1 rules (guide decision) | B6.3 | Not enforced in v1: the store is on Linux or S3 and no consumer compares names; a v2 discussion if a store later needs them |
| A maximum path length | B6.3 | None specified in v1 (guide decision): paths are built from bounded slugs and the store enforces its own limits |

## G-6 caption WER evaluation preparation, Release 0 foundation

Files: `libs/speech_eval/` (WER arithmetic, input validation, report, CLI),
`libs/speech_eval/tests/test_speech_eval.py`, `docs/evaluation/g6-wer-procedure.md`,
`docs/evaluation/g6-wer-report-template.md`. Requirements: PRD G-6, §C4.7 (third box), App-C 7.

**Status: PENDING.** The official G-6 evaluation has **not** been run. The B8.5 set is PENDING,
the normalisation rules and the WER target are not decided, and ADR 0002 (T8) is not approved.

| Rule | Source | Test(s) |
|---|---|---|
| WER by word edit distance (S, D, I counts); pooled WER is total errors over total reference words | ADR 0002 section 7.3 (proposed) | `test_substitutions_deletions_insertions`, `test_pooled_wer_is_not_the_mean_of_lecture_wers` |
| Inputs refused: URLs, absolute, `..` or backslash paths, media files, placeholders, empty or non-UTF-8 files, bad ids | B8.5 README, C-08, decision 0004 | `test_bad_paths_are_refused`, `test_placeholder_and_empty_files_are_refused` |
| An `official` run is refused unless the B8.5 status is COMPLETE, a normaliser is approved and every run detail and approval is filled | B8.5 README, App-C 7 | `test_official_mode_is_refused_today`, `test_official_mode_needs_run_details_and_approvals` |
| Reports say synthetic or official, and keep target and acceptance PENDING | G-6, App-C 7 | `test_a_valid_synthetic_run_loads_and_reports` |

### Not verified

- Any speech model's accuracy; the synthetic tests use made-up text only.
- That an approval cited in an official run exists (a reviewer checks it).
- Text normalisation, confidence intervals, timing accuracy and speed: not decided, not built.

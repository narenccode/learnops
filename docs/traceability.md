# Traceability (PRD E4)

| Requirement | Test(s) | Demo step | Bloom level |
|---|---|---|---|
| EXT-09, C-08 – `media_paths` library: slug, relative-path and number validation; `validate_relative_path` is the B6.3 `$defs/relative_path` rule (B6 has no requirement ID of its own, PRD B.0) | `libs/media_paths/tests/test_validation.py`: slugs `test_valid_slugs_are_accepted`, `test_invalid_slugs_are_rejected`, `test_traversal_and_non_ascii_slugs_are_rejected`, `test_validate_slug_returns_false_for_non_strings`; relative paths `test_valid_relative_paths_are_accepted`, `test_invalid_relative_paths_are_rejected`, `test_prd_b6_2_and_other_legitimate_paths_are_accepted`, `test_colon_that_is_not_a_scheme_or_drive_is_accepted`, `test_scheme_or_drive_at_the_start_is_rejected`, `test_unsafe_relative_paths_are_rejected`, `test_validate_relative_path_returns_false_for_non_strings`; Unicode Cc and complete Cf, explicit Unicode 15.0.0 tables (guide decision) `test_control_and_format_characters_are_rejected`, `test_range_tables_are_sorted_non_overlapping_and_not_adjacent`, `test_range_tables_hold_the_unicode_15_0_counts`, `test_every_range_is_rejected_at_its_edges_and_inside`, `test_code_point_next_to_a_range_is_accepted`, `test_private_use_surrogate_and_unassigned_are_not_rejected_by_category`, `test_tables_match_the_unicode_database_of_the_running_python`, `test_mismatch_check_reports_a_new_unicode_version`, `test_mismatch_check_reports_a_character_whose_category_changed`; no `%` anywhere (guide decision) `test_percent_sign_is_rejected_anywhere`, `test_encoded_characters_without_a_percent_sign_are_accepted`; same rule as the contract `test_every_valid_shared_vector_is_accepted`, `test_every_invalid_shared_vector_is_rejected`, `test_library_and_schema_pattern_agree_on_every_code_point`; helpers `test_require_slug_returns_valid_value`, `test_require_slug_error_names_the_field`, `test_require_positive_int_returns_valid_value`, `test_require_positive_int_rejects_non_integers`, `test_require_positive_int_rejects_values_below_one`, `test_require_int_in_range_returns_valid_value`, `test_require_int_in_range_rejects_values_outside_the_range`, `test_require_int_in_range_rejects_non_integers`. Not enforced in v1 (guide decision): Windows reserved names, Unicode normalization, a maximum length | Show that `validate_relative_path` accepts `slides/001.jpg` and rejects `../720p.mp4`, `%2e%2e/720p.mp4`, `lecture%20notes.mp4`, `https://example.org/x.mp4` and paths containing U+061C or U+202E, and accepts one containing U+E000; show that `require_slug("../x", "cohort")` raises a clear error | — |
| EXT-09, C-08 – `media_paths` library: B6.1 media path templates (defaults, placeholders, required and segment-separated identifying placeholders, checked once at load; slugs and numbers 1–99; output is a safe relative path; known v1 limit, guide decision: custom lesson and live-class templates are not checked against each other, so an administrator's custom templates can give a lesson and a live class the same folder, in either direction, while the defaults cannot collide; no cross-check before the freeze, to be revisited after Release 0 only if adopters need it; documented in the README) (B6 has no requirement ID of its own, PRD B.0) | `libs/media_paths/tests/test_paths.py`: `test_course_lesson_path_uses_prd_template`, `test_live_class_path_uses_prd_template`, `test_path_numbers_are_zero_padded`, `test_default_templates_match_prd_b6_1`, `test_default_templates_use_exactly_the_documented_placeholders`, `test_default_templates_are_loaded_checked_templates`, `test_posixpath_join_adds_a_file_name_to_a_folder_with_or_without_a_slash`, `test_required_placeholders_are_the_guide_decision`, `test_course_lesson_custom_template_with_documented_placeholders`, `test_live_class_custom_template_with_documented_placeholders`, `test_each_course_lesson_placeholder_is_supported`, `test_each_live_class_placeholder_is_supported`, `test_template_without_identifying_placeholder_is_rejected`, `test_identifying_placeholders_sharing_a_segment_are_rejected`, `test_identifying_placeholder_may_share_a_segment_with_numbers`, `test_missing_placeholder_error_names_every_missing_one`, `test_number_placeholders_are_optional`, `test_lessons_differing_only_by_lesson_slug_get_different_folders`, `test_template_is_checked_once_when_loaded_not_at_each_call`, `test_checked_template_cannot_be_created_unchecked`, `test_path_functions_reject_an_unloaded_template`, `test_lesson_template_is_not_accepted_for_live_class`, `test_unknown_placeholder_is_rejected_with_clear_error`, `test_lesson_placeholder_in_live_class_template_is_rejected`, `test_malformed_template_is_rejected`, `test_format_spec_or_conversion_is_rejected`, `test_escaped_literal_braces_are_allowed`, `test_template_producing_unsafe_path_is_rejected_at_load`, `test_unsafe_live_class_template_is_rejected_at_load`, `test_non_string_template_is_rejected`, `test_course_lesson_rejects_invalid_slugs`, `test_live_class_rejects_invalid_slugs_and_cohorts`, `test_cohort_in_slug_form_such_as_a_date_is_accepted`, `test_non_string_slug_is_rejected`, `test_course_lesson_rejects_non_integer_numbers`, `test_course_lesson_rejects_numbers_outside_1_to_99`, `test_course_lesson_accepts_numbers_1_and_99`, `test_live_class_rejects_non_integer_number`, `test_live_class_rejects_number_outside_1_to_99`, `test_live_class_accepts_number_99`. Not decided, so not tested: whether a custom template must end with `/` (the README says to join file names with `posixpath.join`, which handles both) | Load the default and a custom template; show that a template without `{lesson_slug}`, `{course_slug}{module_slug}/`, an unknown placeholder, a `../` slug, `module_number=100` and `module_number=True` are rejected with a clear message | — |
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
| A schema file not named `<name>.v<N>.schema.json` is reported, never skipped, so a repository with only misnamed schemas cannot pass | B.0 rule 1 | `test_misnamed_schema_is_reported_with_its_path`, `test_misnamed_schema_is_not_treated_as_valid_because_a_folder_matches`, `test_only_misnamed_schemas_never_succeed` |

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
| `body` is a path inside the package folder and follows the shared relative-path rule (C-08): the same `$defs/relative_path` pattern as B6.3, including the pinned Unicode 15.0.0 Cc and Cf ranges; the same shared vectors as B6 (every valid vector accepted and every invalid vector rejected, through `$defs/relative_path` alone and through `body` in a whole package); the B1 pattern equals the B6 pattern; with each code point placed after the first character of a one-segment name (`a<c>.mp4`), the pattern rejects exactly Cc, Cf, whitespace, `\`, `?`, `#`, `%` and `:`. The colon is rejected there only because it makes a URL scheme or drive-letter prefix (`a:`), not in every position: `notes/b:c.md` and `12:30.mp4` are valid. The pin and exhaustive tests need Python 3.12 (Unicode 15.0.0) and fail by design on another version | B1.1, C-08, B6.3 | `test_every_valid_path_vector_is_accepted`, `test_every_invalid_path_vector_is_rejected`, `test_body_accepts_every_valid_path_vector`, `test_body_rejects_every_invalid_path_vector`, `test_b1_relative_path_pattern_is_exactly_the_b6_pattern`, `test_python_unicode_database_is_the_pinned_version`, `test_unicode_15_0_has_2_cc_and_21_cf_ranges`, `test_pattern_rejects_exactly_cc_and_cf_among_all_code_points`, `test_body_that_is_not_a_relative_path_is_rejected` |
| The schema is valid, and the example package validates (also as `sections-only`) | B.0 rule 1 | `test_schema_is_a_valid_draft_2020_12_schema`, `test_example_package_is_valid`, `test_example_in_sections_only_mode_is_valid` |

Enforced and tested, but chosen in the schema rather than stated as a rule in the PRD (to be
confirmed by the contract reviewers): the `type` spellings `url` and `label`; `completion` limited
to `submit`; `submission` limited to `onlinetext` and `file`; `section.number` at least 1; points
as non-negative integers; non-empty titles; `activities` and `sections` not empty. (The shape of
`body` is no longer in this list: it is the shared relative-path rule, stated in PRD B1.1 and
listed in the table above.)

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

### B1 submission content (Q6, Q9): vectors, tests and open decisions

Files: the PRD text (B1.3 "Check formats" and the new B1.5), `contracts/test-vectors/submission.v1.json`
and `libs/contracts/tests/test_submission_vectors_v1.py`. The rules were decided by the guide on
PR #61 (2026-11-11 and 2026-11-13). The clarifications of B1.5 rule 7 and of the README rules in B1.3 were decided by the guide on PR #87 (2026-11-15), and so were the check-parsing rules, the `word_count` argument, the heading and fence rules, and the C3.5 wording (the guide's second comment of 2026-11-15). No schema, example package, validator or library code changes.
The tests check the data and the text only: no reader of submissions exists yet.

**Decided by the guide on PR #87 (2026-11-16), written in PRD B1.3.** These rules were open
decisions in the earlier head and are no longer listed as open below:

- A closing `#` sequence on a heading is removed only when a space or tab comes before it and only
  spaces or tabs follow it: `## Setup ##` is `Setup`, `## C#` is `C#`. Trailing spaces and tabs are
  removed, and the heading text is trimmed and matched exactly (still case-insensitive, as B1.3
  already says).
- A heading and a fence line may have up to three leading spaces; four or more is neither.
- A fence line needs at least three backticks or at least three tildes (the guide, 2026-11-16, 09:55
  UTC), so `` `npm install` `` is not a fence and hides no heading.
- A closing fence uses the same character as the opening fence and is at least as long; an unclosed
  fence runs to the end of the file.
- An empty `readme_sections` list, an empty name in it (`a,,b`), an empty field (`http_ok:`) and a
  trailing `;` each fail CK-09.
- Check names are lowercase and case-sensitive: `Word_Count:5` is an unknown name and fails CK-09.
  Section names stay case-insensitive.

The vectors for these rules that concern the `Check` cell (the fifteen parser cells, including the
empty pieces, the trailing `;` and the name case) are **not** in this pull request: they are
delivered in a separate follow-up pull request, as the guide decided. This pull request has only the
README heading and fence vectors.

| What is checked | PRD | Test(s) |
|---|---|---|
| The vectors file is LF JSON with a version, the submission cases and the README cases, with unique ids; each case has the exact shape and closed vocabularies; expected values are consistent (a word count equals the words of the report, a report file named as the source is in the input, a part has a value or an error, never both); the status is `derived` or `unverified-until-lab`, and only the HTML case is unverified | B1.5 | `test_vectors_file_is_lf_json_with_a_version_and_unique_case_ids`, `test_case_has_the_required_shape_and_consistent_expected_values` (every case), `test_only_the_html_case_is_unverified_until_the_lab` |
| The shape check and the duplicate-id check catch the mistakes they exist for (a missing key, the retired status `confirmed`, an unknown or repeated reason code, a wrong word count, a value with an error, a file source with no file, an HTML case marked `derived`, an unknown rule id or input key, a rule that a result cannot show, a word count that `covers` does not declare) | B1.5 | `test_the_shape_check_catches_what_it_exists_for` (one negative control for each mistake listed), `test_the_duplicate_id_check_catches_a_repeated_id` |
| `covers` says what a case shows: rules 8 and 9 are never listed (a result that lists the three parts cannot show them); the word count is listed exactly when the report has a word count; an expected error lists rule 7, an HTML case rule 5, a report from a file rule 4; rules 1 to 7 and the word count are each covered by at least one submission case | B1.5 | `test_case_has_the_required_shape_and_consistent_expected_values` (every case), `test_every_rule_a_vector_can_show_is_covered_by_a_vector` |
| The five PRD examples are the five required vectors: same text, word counts and reason codes; example 4 quotes the same report file | B1.5 | `test_prd_examples_are_the_five_required_vectors` |
| The PRD has the B1.3 check formats (`;`, spaces around a check and its argument ignored, the name before the first `:`, a cell with only `—` means no machine check, `readme_sections` with no comma or semicolon in a name, the README as `README.md` at the repository root, ATX headings with up to three leading spaces and a space or tab after the `#`, a closing `#` sequence removed only after a space or tab, trailing spaces and tabs removed, the whole heading text matched, fences of at least three backticks or three tildes with up to three leading spaces, a closing fence with the same character and at least the length, an unclosed fence running to the end of the file, Setext headings are not headings, `word_count:<n>` as one or more ASCII digits with a value of at least 1, `http_ok:demo_url` only, lowercase case-sensitive check names, an unknown name, a known check with an argument that breaks a defined format, an empty list, name or field, and a trailing `;` fail CK-09) and says what it does not define (only `command:<name>`, the `repo_file:<path>` argument, the criterion keys and other table-parsing details); the finer Markdown details are no longer listed as undefined; C3.5 says `word_count` reads the report and its list of checks is the list the tests use for `unknown_check` | B1.3, C3.5 | `test_prd_b13_has_the_check_formats_and_names_what_it_does_not_define`, `test_prd_c35_says_word_count_reads_the_report`, `test_the_c35_names_in_the_tests_are_the_names_in_the_prd` |
| The README cases (a file in `files`, a `check`, and a result of `pass`, `fail` with the missing names, or `invalid` with the unknown check) have the exact shape and a result that fits the check; together they cover the README file rule (`README.rst` is the other file name, because `readme.md` is the same file as `README.md` on a case-insensitive file system), the heading rules (a whole-text match, a closing `#` sequence only after a space or tab, a tab, trailing spaces and tabs, up to three leading spaces for a heading and for a fence, a closing fence of the same character and at least the length, tilde and unclosed fences, a single backtick that is not a fence) and the name rule, and each result kind. The unknown check must be a whole check name, not part of a longer one, and not a known C3.5 check name. They are data for the future marking-table parser: no test reads a README or finds a heading | B1.3 | `test_readme_case_has_the_required_shape_and_a_consistent_result`, `test_readme_cases_cover_the_file_the_headings_and_the_name_rule`, `test_the_readme_check_catches_what_it_exists_for` (one negative control for each mistake it lists, including a check name that only contains the unknown name, and `readme_sections:Setup;word_count:5` with the unknown check `word_count`, which must be rejected) |
| B1.5 has nine numbered rules, both reason codes, the rule 7 clarifications (labels before `Report:`, a second `Report:` line is part of the report, one error does not stop the other criteria from being graded), the "should" rule for task text and the unverified HTML note; every `covers` entry of a vector names a rule that exists; the PRD names the vectors file | B1.5 | `test_prd_b15_has_nine_numbered_rules_and_both_reason_codes`, `test_every_covers_entry_names_a_rule_the_prd_has`, `test_the_prd_mentions_the_vectors_file` |
| The open points are written down, not decided: B1.5 says "Not defined in v1", this section lists each open decision with who decides it, and no vector covers one (no carriage return, empty label value, HTML entity or link, or trailing whitespace; URLs only on `example.org`) | B1.5 | `test_prd_b15_says_what_v1_does_not_define`, `test_traceability_lists_the_open_decisions_and_who_decides_them`, `test_case_does_not_decide_an_open_point` (every case), `test_the_open_point_check_catches_what_it_exists_for` (one negative control for each kind of open point listed) |

**Not enforced (no reader exists).** The marking-table parser (Module 2, `libs/contracts`, used first
by CK-09) and the submission extractor (Module 3, Release 4) are not written; the extractor must
pass these vectors, and B8.4 (PR #31) must use the same vectors. The held rules
`marking_table_not_checked` and `check_vocabulary_not_checked` stay held. The HTML expected result
is unverified until the lab check on Moodle 4.5 and 5.3. Every other expected result is
`derived`: the rules are the guide's, but each example and its result still need a reviewer's
confirmation. The "should" rule for task text (B1.5 rule 9) is guidance and is not validated.

#### Open decisions (B1 submission content)

Not decided in this change and not turned into rules. B1.5 and B1.3 say "not defined"; no vector
covers them. The two rows marked "decided no" were answered by the guide on PR #87 (2026-11-15).

| Open decision | Who decides | In v1 for now |
|---|---|---|
| An empty label value (`Demo:` with nothing after it) | The guide | Not defined |
| Line endings and trailing blank lines (does online text reach a reader with `\r\n`?) | The guide, with Harshitha (M3) | Not defined |
| HTML details beyond rule 5: character entities, links, nested tags, non-breaking spaces | The guide, after the lab check | Not defined; the HTML vector is unverified |
| An assignment whose `submission` has only `onlinetext` or only `file` | The guide | Only the condition in rule 4 is stated |
| The argument format of `repo_file:<path>` and criterion keys (`docs/design/grading.md` §4.3b). How a check's name is split from its argument is decided: the text before the first `:` | The guide, with Shraddha's input (M2) | Not defined here |
| Whether the B1.3 bullet is enough for the marking-table parser | Shraddha (M2) | The bullet as written |
| The parser test vectors for the B1.3 check cells (the fifteen cells of the guide's comment of 2026-11-15, including Shraddha's cases for the empty pieces, the trailing `;` and the name case decided on 2026-11-16) | The guide decided: a separate follow-up pull request, as Shraddha proposed | None in this pull request: delivered in the follow-up pull request |
| Whether the vector layout fits the extractor, whether `field_missing` and `field_repeated` match the grading result vocabulary, and which extra cases to add | Harshitha (M3) | The layout as written; the cases in the file |
| A test-only reference extractor so that the vectors run now | The guide: decided no on PR #87 (2026-11-15); the extractor is Harshitha's in Release 4 and must pass the vectors | None: tests check data and text only |
| A decision record (`docs/decisions/`) for Q6 and Q9 | The guide: decided no on PR #87 (2026-11-15) | None: the decisions are on PR #61 and PR #87 and in the PRD text |

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

## B4 Moodle web-services contract (v1), Release 0 foundation

Files: `contracts/moodle-ws.v1.md` (normative rules), `contracts/moodle-ws.v1.schema.json`,
`contracts/examples/moodle-ws.v1.functions.json` (allow-list), `libs/contracts/tests/test_moodle_ws_v1.py`.
**Contract work only, draft, not verified on any Moodle site.** Guide's decisions on Q1, Q24 and
Q37: PR #27.

FR-G-01 ("Fetch assignments, the marking table and submissions … through B4") and FR-G-06 ("Write
only approved drafts to Moodle via B4"), both Release 4, are deliberately not in the table above. They
need `libs/moodle_ws` and the grading module, which do not exist yet.

### Enforced by automated tests

Test names are in `test_moodle_ws_v1.py`.

| Rule | PRD | Test(s) |
|---|---|---|
| The allow-list names exactly the PRD B4 functions, no extra, none missing, no duplicates | B4 | `test_function_names_equal_the_prd_b4_list`, `test_prd_b4_lists_the_expected_number_of_functions` |
| The allow-list and the rules text (`moodle-ws.v1.md` §2) name the same functions | B.0 rule 1 | `test_function_names_equal_the_rules_table` |
| Each entry's purpose is the PRD B4 purpose | B4 | `test_purpose_is_the_prd_purpose` |
| No parameter is listed unless the PRD names it for that function; `mod_assign_save_grade` sends `workflowstate` | B4, App-C 1 | `test_every_parameter_is_named_in_the_prd_for_its_function`, `test_the_prd_names_workflowstate_only_for_save_grade`, `test_save_grade_sends_the_workflow_state` |
| `mod_assign_set_user_flags` is not allowed: it can set `released` with only `mod/assign:grade` | Guide, 11 Nov; C-09 | `test_the_dropped_user_flags_function_is_not_listed` |
| A replacement name for a Moodle version also appears in the PRD B4 text | B4 ("replacements recorded here") | `test_a_replacement_name_is_also_in_the_prd` |
| No verification state is stored in the schema or example | Guide, Q1 | `test_invalid_document_is_rejected_at_the_expected_place` (five verified-flag cases, including capital letters) |
| Schema is valid; example validates; invalid documents fail at the expected place; unknown fields are accepted | B.0 rule 1, rule 2 | `test_schema_is_a_valid_draft_2020_12_schema`, `test_example_is_valid`, `test_invalid_document_is_rejected_at_the_expected_place`, `test_unknown_fields_are_accepted` |
| One token variable per site with a placeholder; no single `MOODLE_WS_TOKEN` | B4, SEC-03, C-06; guide, Q24 | `test_one_token_variable_per_site_with_a_placeholder` |

### Documented but not automatically enforced

| Rule | PRD |
|---|---|
| Only the functions listed in the contract are called (`libs/moodle_ws` will build its allow-list from the example; the library does not exist yet) | B4 |
| One service account per site, with a token restricted to those functions and minimum capabilities | B4, SEC-03 |
| The token is stored only in the environment | SEC-03, C-06 |
| A grade write uses workflow state `readyforrelease`, never `released`; only approved drafts are written | B4, C-09 |
| Each function exists with the parameters used on Moodle 4.5 and 5.3 (all 10 lab checks are still open) | B4, App-C 1 |

Open: when the lab Moodle sites are available (all ten checks in `moodle-ws.v1.md` §5 wait for
them; B4 cannot be frozen until they pass), and the parameter name for feedback comments on
`mod_assign_save_grade` (not in the PRD; lab check 1). Q1, Q24 and Q37 are decided (PR #27).

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
| Moodle 5.3 is the owner-confirmed build and test version for Release 0 (Issue #55, 2026-11-14 reply, which replaces the 2026-11-12 decision to build on 4.5). Every restore and the sections-only merge are tested on 5.3 only, recording the Moodle version, the date and the outcome of each restore; the `.mbz` is labelled "built on Moodle 5.3". The owner reports that Moodle documents that a backup restores into the same or a newer version only, so the 5.3 template is expected not to restore on 4.5 (the owner's report: not verified here, and the PRD does not state it). Moodle 4.5 is **not tested; waived by the guide for Release 0 (decided 2026-11-14, confirmed as a C-03 deviation 2026-11-15; scope B8.1 only)**, not recorded as passed; if PRD C-03 later needs the template on 4.5, it is rebuilt once on 4.5 | C-03 | None yet: not verified; needs Moodle lab testing on 5.3. Moodle 4.5: not tested; waived by the guide for Release 0 (decided 2026-11-14, confirmed as a C-03 deviation 2026-11-15; scope B8.1 only) |
| Deviation - C-03: the B8.1 template is built and tested on Moodle 5.3 only; 4.5 not tested, waived by the guide for Release 0 (decided 2026-11-14, confirmed as a C-03 deviation 2026-11-15; scope B8.1 only). The B8.2 restore and merge tests have their own decision, made by the guide on 2026-11-16 (A5 on PR #61, recorded there with B8.2, not here); C-03 still applies to the harness (FR-C-08) | C-03 | None (a recorded deviation, not a test) |

### Not covered here

These are pending and are not claimed by this change:

- **The `.mbz` backup, its SHA-256, the release asset (tag `testdata-b8-1-v1`) and the download
  script.** None of them exists yet.
- **Moodle 5.3 verification:** the restore, the protected items, the completion criteria, the badge
  and the sections-only merge (PRD C1.7, App-C item 2). The B8.1 owner's lab access is ready (in person, the
  owner's 2026-11-14 reply), but access is not a result and no lab verification result is recorded. **Moodle 4.5 is not tested; waived by the guide for Release 0 (decided 2026-11-14, confirmed as a C-03 deviation 2026-11-15; scope B8.1 only)**
  and is not claimed as passed.
- **The App-C item 2 results.** The decision record `docs/decisions/0009-b8-1-template-course.md`
  exists and holds the Moodle 4.5 waiver (PR #95); its number is taken again at merge, after
  rebasing (Owner, Issue #55). The results are not written. The owner asks for a short, text-only
  results table in the same file that names the local evidence files; screenshots and logs stay
  local and are not committed.
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
| Shapes of `chapters.json`, `slides.json`, `cues.json` | B6.2 | Their own schemas, see the next section |
| Windows reserved names (such as `CON`, `NUL`, `COM1`) and Unicode normalization in paths: considered, not v1 rules (guide decision) | B6.3 | Not enforced in v1: the store is on Linux or S3 and no consumer compares names; a v2 discussion if a store later needs them |
| A maximum path length | B6.3 | None specified in v1 (guide decision): paths are built from bounded slugs and the store enforces its own limits |

## App-C item 4: BigBlueButton recording metadata (Release 0 verification record)

`docs/decisions/0006-app-c-4-bbb-recording-metadata.md`. Documentation only: no code, contract or
test changed. App-C item 4 has no requirement ID of its own; it is a precondition of FR-V-09.

| What is recorded | PRD | Test(s) |
|---|---|---|
| The verification record for App-C item 4 exists with its steps, the evidence tables and the comparison with B6.1 and the B6.3 `source` field. Its status is **NOT VERIFIED**: every lab observation (metadata keys and values, the video-format output location, versions) is PENDING until T17 supplies it | App-C 4, FR-V-09, B6.1, B6.3 | None: needs the lab BigBlueButton and a Moodle site (task T17) |

## App-C item 4: BigBlueButton recording metadata and video-format output (T17)

Files: `docs/decisions/0005-app-c-4-bbb-recording-metadata.md` and
`docs/decisions/evidence/0005-app-c-4-bbb/`. Supports FR-V-09 (Release 3).

**Status: PENDING.** The lab BigBlueButton was not reachable from this session (only placeholder
configuration exists), so no server, version, recording, metadata or video-format result is
verified. The record holds a read-only check script (self-tested on synthetic data only) and a
checklist for the manual run. It does **not** show that App-C 4 or FR-V-09 is met.

## B6.2 chapters, slides and cues contracts (v1), Release 0 foundation

Files: `contracts/chapters.v1.schema.json`, `contracts/slides.v1.schema.json`,
`contracts/cues.v1.schema.json`, `contracts/examples/{chapters,slides,cues}.v1/`, the validators in
`libs/contracts/lesson_files.py` (shared validator reference EXT-09) and their tests in
`libs/contracts/tests/test_lesson_files_v1.py`. B6.2 has no requirement ID of its own in the PRD (it
is a contract, PRD B.0). It is the schema that FR-V-05, FR-V-07, FR-V-14 (Release 3 and 5, which
write the files) and FR-X-06, FR-X-07, FR-X-12 (Release 6, which read them) will be checked against,
and the data EXT-08 requires "now". None of those requirements is implemented by this change, so none
gets a row in the table at the top.

### Enforced by a JSON Schema or by the validator, and covered by automated tests

Test names are in `test_lesson_files_v1.py`. "Validator" means `lesson_files.py`.

| Rule | PRD | Test(s) |
|---|---|---|
| Each file is a bare JSON array (not an object wrapper); unknown fields accepted | B6.2, B.0, EXT-02 | `test_schema_is_a_valid_draft_2020_12_schema`, `test_a_document_that_is_not_an_array_is_rejected`, `test_unknown_fields_are_accepted` |
| Each schema has a valid top-level example, and every example validates | B.0 rule 1 | `test_each_schema_has_a_top_level_example`, `test_every_example_is_valid`, `test_examples_show_what_the_guide_decided`, `test_valid_chapter_list_is_accepted`, `test_empty_chapter_list_is_accepted_by_the_schema`, `test_valid_slide_list_is_accepted` |
| Times are numbers of seconds, fractional allowed, not strings; at least 0 and 0 itself allowed (guide, 2026-11-15) | B6.2 | `test_fractional_chapter_times_are_accepted`, `test_fractional_slide_time_is_accepted`, `test_fractional_cue_time_is_accepted`, `test_chapter_with_wrong_fields_is_rejected`, `test_slide_with_wrong_fields_is_rejected`, `test_cue_time_must_not_be_negative`, `test_times_of_zero_are_accepted`, `test_times_below_zero_are_rejected_by_the_schema` |
| A time that is NaN or infinite is rejected (Python's JSON reader accepts them; the schema does not stop NaN); an integer too large for a float (such as 10**400) is a finite number and must not crash the validators (peer review of PR #93) | B6.2 | `test_non_finite_chapter_time_is_rejected`, `test_non_finite_slide_time_is_rejected`, `test_non_finite_cue_time_is_rejected`, `test_a_huge_integer_time_does_not_crash_the_validators`, `test_a_huge_integer_time_is_still_checked_by_the_other_rules`, `test_a_float_that_is_not_finite_is_still_rejected` |
| Chapters: `end` greater than `start`; ascending order; no overlap with any earlier chapter (the largest earlier `end`); gaps and touching chapters allowed (validator, because a schema cannot compare two properties) | B6.2 | `test_chapter_end_not_after_start_is_rejected`, `test_unordered_chapters_are_rejected`, `test_overlapping_chapters_are_rejected`, `test_a_chapter_inside_another_is_an_overlap`, `test_chapters_with_the_same_start_are_an_overlap`, `test_chapter_gaps_are_accepted`, `test_chapters_that_touch_are_not_an_overlap`, `test_overlap_with_an_earlier_longer_chapter_is_reported_for_every_chapter`, `test_a_chapter_overlaps_only_if_it_starts_before_the_latest_earlier_end`, `test_one_mistake_is_reported_once`, `test_schema_alone_does_not_enforce_the_order_rules` |
| Slides: `thumb` follows the manifest relative-path rule, starts with `slides/`, ends in `.jpg`; no fixed digit count; `text` optional and unrestricted | B6.2, B6.3, C-08 | `test_slide_text_is_optional`, `test_slide_text_has_no_restriction_in_v1`, `test_slide_thumbnail_names_have_no_fixed_digit_count`, `test_slide_thumbnail_may_be_in_a_subfolder_of_slides`, `test_slide_thumbnail_outside_slides_or_not_jpg_is_rejected`, `test_slide_thumbnail_breaking_the_relative_path_rule_is_rejected`, `test_slide_thumbnail_needs_a_character_before_the_extension` |
| The relative-path and type-token patterns are the same text as in the manifest schema, and the shared path vectors pass (this includes the no-`%` rule) | B6.3, C-08 | `test_relative_path_pattern_is_the_manifest_pattern`, `test_type_token_pattern_is_the_manifest_slug_pattern`, `test_shared_path_vectors_are_accepted_and_rejected_in_slides_and_cues` |
| No `%` anywhere in a slide thumbnail or an image ref, so no percent-encoded dot or separator such as `%2e` or `%252e` (guide decision, B6.3 `relative_path`; the schemas carry the same pattern text); a `url` ref may contain percent-encoding, because C-08 does not apply to it | B6.2, B6.3, C-08 | `test_slide_thumbnail_with_a_percent_sign_is_rejected`, `test_slide_thumbnail_without_a_percent_sign_is_accepted`, `test_image_ref_with_a_percent_sign_is_rejected`, `test_url_ref_with_a_percent_sign_is_accepted`, `test_shared_path_vectors_are_accepted_and_rejected_in_slides_and_cues` |
| Chapter `title` has at least one character that is not whitespace (empty and blank titles are rejected; confirmed by the guide and implemented, [guide, PR #93 comment of 2026-11-15](https://github.com/narenccode/learnops/pull/93#issuecomment-6902711086)) | B6.2, FR-V-05, FR-X-07 | `test_empty_or_blank_chapter_title_is_rejected`, `test_chapter_title_with_a_visible_character_is_accepted` |
| Cues: `t`, `type`, `ref`, `label` required; `label` not empty (guide, 2026-11-15) and not only whitespace (confirmed by the guide and implemented, [guide, PR #93 comment of 2026-11-15](https://github.com/narenccode/learnops/pull/93#issuecomment-6902711086)); `ref` never empty for every cue type, including unknown types (confirmed by the guide and implemented); `required` optional boolean, absent means false; empty array valid | B6.2, FR-X-12 | `test_missing_required_cue_field_is_rejected`, `test_empty_or_non_string_label_is_rejected`, `test_missing_label_is_rejected`, `test_blank_label_is_rejected`, `test_label_with_a_visible_character_is_accepted`, `test_label_has_no_length_limit_in_v1`, `test_missing_required_means_false`, `test_required_true_and_false_are_accepted`, `test_non_boolean_required_is_rejected`, `test_empty_cues_array_is_accepted` |
| Cue types `h5p`, `image`, `url`; `ref` is a Moodle idnumber (EXT-06) in the B1.2 form (lowercase ASCII letters and digits, single hyphens; the pattern equals B1's `$defs/identifier`; confirmed by the guide and implemented, [guide, PR #93 comment of 2026-11-15](https://github.com/narenccode/learnops/pull/93#issuecomment-6902711086)), a relative path, an absolute `https` address (guide, 2026-11-15) with a host (scheme in any letter case; no credentials, no `@` before the path, no backslash; percent-encoding allowed; these syntax restrictions are confirmed by the guide and implemented); the url is not subject to the relative-path rule; for an unknown type `ref` is any non-empty string (confirmed by the guide and implemented) | B6.2, EXT-06, C-08, FR-X-12 | `test_all_three_known_cue_types_are_accepted`, `test_h5p_ref_that_is_an_idnumber_is_accepted`, `test_h5p_ref_that_is_not_an_idnumber_form_is_rejected`, `test_h5p_ref_that_is_empty_or_not_a_string_is_rejected`, `test_h5p_ref_pattern_is_the_b1_identifier_pattern`, `test_ref_of_an_unknown_type_is_only_a_string`, `test_ref_of_an_unknown_type_must_not_be_empty`, `test_image_ref_that_is_a_relative_path_is_accepted`, `test_image_ref_that_is_not_a_relative_path_is_rejected`, `test_absolute_https_url_is_accepted`, `test_url_that_is_not_an_absolute_https_address_is_rejected`, `test_url_with_no_host_credentials_or_backslash_is_rejected`, `test_url_with_a_host_and_percent_encoding_or_at_after_the_path_start_is_accepted`, `test_url_ref_is_not_subject_to_the_relative_path_rule` |
| `type` is lowercase ASCII letters and digits with single hyphens, the track-role slug form (underscores, dots, spaces rejected); the schema accepts any such token; a v1 reader ignores an unknown type; no separate `scenario` type (guide, 2026-11-15) | B6.2, FR-X-12 | `test_unknown_lowercase_type_is_accepted_and_ignored_by_a_v1_reader`, `test_a_cue_with_a_type_the_contract_dropped_is_not_special`, `test_malformed_or_uppercase_type_is_rejected`, `test_cue_type_in_the_track_role_slug_form_is_accepted`, `test_cue_type_with_underscore_dot_space_or_other_characters_is_rejected`, `test_cue_type_form_agrees_with_the_manifest_track_role_form`, `test_type_that_is_not_a_string_is_rejected`, `test_ref_of_an_unknown_type_is_only_a_string` |
| Every `start`, `end` and `t` in `chapters.json`, `slides.json` or `cues.json` is at most the manifest's `duration_s`, used unrounded and with no tolerance (guide, 2026-11-15, confirmed for all three files): a consumer-level cross-file rule (`check_within_duration`), not a schema rule | B6.2 | `test_schemas_do_not_check_times_against_the_duration`, `test_time_beyond_duration_is_rejected_by_the_consumer_check`, `test_time_exactly_at_the_duration_is_accepted`, `test_absent_files_are_not_checked`, `test_lesson_with_no_cues_file_has_no_readable_cues`, `test_invalid_duration_is_a_programming_error`, `test_examples_are_within_the_example_lesson_duration`, `test_duration_is_used_as_given_without_rounding`, `test_duration_check_has_no_tolerance`, `test_every_chapter_start_and_end_and_cue_t_is_checked_against_duration`, `test_a_huge_integer_duration_does_not_crash_the_duration_check`, `test_a_huge_integer_time_is_beyond_a_normal_duration`, `test_a_boolean_or_non_finite_duration_is_still_a_programming_error` |
| Every report lists what it did not check; a message names the file and place and says what to do; a path, thumbnail, url, idnumber or blank-text error does not show a regular expression | EXT-09, UI-05 | `test_reports_list_what_was_not_checked`, `test_error_messages_name_the_file_place_and_next_step`, `test_invalid_path_message_is_short_and_says_what_to_do`, `test_thumbnail_outside_slides_has_its_own_message`, `test_other_pattern_messages_say_what_to_write`, `test_a_pattern_error_keeps_its_code_and_place` |

### Documented but not automatically enforced

| Rule | PRD | Where the PRD places it |
|---|---|---|
| The thumbnail and image files exist; thumbnails are 320 px wide | B6.2 | FR-V-07 (R3), FR-V-08 |
| An `h5p` ref is the `idnumber` of an activity in the course | B6.2, B7, EXT-06 | The checker (M2) and FR-V-14 (R5) |
| A `url` is on the player's allow-list | B6.2, FR-X-12 | The player (R6) |
| Slides or cues in ascending order of `t`; chapters, slides or cues have a minimum count | B6.2 | Not decided by the guide, so nothing is required (`test_slides_and_cues_need_no_particular_order`, `test_empty_chapter_list_is_accepted_by_the_schema`) |
| Release 3 writes the three files (`cues.json` may be empty); Release 5 adds `h5p` cues; a lesson with no cues may omit the file | B6.2, EXT-08, FR-V-14 | Documented in PRD B6.2; the pipeline (R3, R5) implements it |

## B8.6 model comparison set (PROVISIONAL), Release 0 foundation

Files: `testdata/b8-6-model-comparison/` (manifest, rubric, five schemas, one transcript input,
two expected outputs, two PROPOSED mentor review forms), `libs/contracts/tests/test_b8_6_dataset.py`. B8.6 is a test-data set
(PRD B8) with no requirement ID of its own. It is the input of FR-M-03 (Release 4), which is not
implemented, so no row in the table above maps to it.

### Covered by automated tests

| Rule | Source | Test(s) |
|---|---|---|
| Manifest, rubric and expected chapters validate against their schemas | Proposed format (set README, O10) | `test_schema_is_a_valid_draft_2020_12_schema`, `test_manifest_and_rubric_are_valid`, `test_expected_chapters_are_valid_and_fit_the_transcript` |
| Fixed inputs linked to expected outputs; pending and placeholder items hold no content | PRD B8 | `test_ids_are_unique_and_references_resolve`, `test_pending_and_placeholder_items_have_no_content` |
| The grading-draft item gd-001 points at the B8.4 set (input and mentor reference grades), never copies it, stays NOT REVIEWED, cannot point outside B8.4, and its files are checked when B8.4 is in the tree (skipped, with the reason, until PR #31 merges) | PRD B8; B8.4 | `test_the_grading_draft_item_points_at_b8_4_and_never_copies_it`, `test_the_b8_4_files_exist_when_the_set_is_present`, `test_a_b8_4_path_cannot_leave_the_b8_4_set` |
| Two PROPOSED mentor review forms (grade-draft review and output review): valid schemas, invented examples validate, output-review levels equal the rubric's, a draft id never names a provider, the grade-draft example is consistent (differences, totals, band), no real review is claimed | Proposed format (set README, O2 to O5); design 11.2, Q48 | `test_review_schema_is_a_valid_draft_2020_12_schema`, `test_the_invented_review_examples_validate`, `test_output_review_levels_equal_the_rubric_levels`, `test_a_draft_id_never_names_a_provider`, `test_the_grade_draft_example_is_consistent`, `test_review_forms_reject_missing_blind_and_extra_fields`, `test_no_real_reviews_are_claimed` |
| Transcript input has the B5.4 shape and consistent times | PRD B5.4 | `test_transcript_has_the_prd_b5_4_shape_and_consistent_times`, `test_time_checks_catch_bad_transcripts`, `test_transcript_validates_against_the_b5_contract` (skipped until B5 is on `main`) |
| Expected chapters use the B6.2 shape and fit the transcript | PRD B6.2 | `test_expected_chapters_are_valid_and_fit_the_transcript`, `test_chapter_checks_catch_overlap` |
| The four FR-M-03 measures are in the rubric | PRD FR-M-03 | `test_rubric_covers_the_measures_and_tasks` |
| Provisional and not-reviewed labelling; no results claimed | Set README | `test_status_rules`, `test_reviewed_needs_a_reviewer`, `test_expected_summary_is_labelled_until_reviewed`, `test_no_results_are_claimed` |
| No real data (fictional hosts only, no email addresses, small text files) | PRD B8, C-07 | `test_files_are_small_text_with_no_real_hosts_or_email_addresses` |

### Not met yet, and not tested

- Grading-draft items (wait for B8.4 and its reference grades, Q13) and practice items (Q12).
- Reviewed expected outputs, a fixed rubric (Q48), measure definitions marked `open`, set size.
- Any comparison run or result (FR-M-03, Release 4).

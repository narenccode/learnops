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
generates contract files yet. What is still not checked is listed in `libs/contracts/README.md`. Each schema and its examples are checked by the engine
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
| An example no schema takes (a flat file or a folder) and a file that is not `.json`, `.yaml` or `.yml` are reported, never skipped; supporting files in a subfolder and hidden files are not | B.0 rule 1, E1 | `test_a_flat_file_that_no_schema_takes_is_an_orphan`, `test_an_example_folder_with_no_schema_is_an_orphan`, `test_a_file_that_is_not_json_or_yaml_is_reported`, `test_supporting_files_in_a_subfolder_and_hidden_files_are_not_reported` |
| A key repeated in one JSON or YAML object is an error (with line and column in YAML); the same key in different objects and a YAML merge key are fine | B.0 rule 1, E1 | `test_a_key_repeated_in_one_object_is_reported`, `test_the_same_key_in_different_objects_is_fine` |
| `NaN`, `Infinity` and `-Infinity` in JSON are errors; ordinary numbers still pass | B.0 rule 1, E1 | `test_json_that_python_accepts_but_json_does_not_is_reported`, `test_ordinary_json_numbers_still_pass` |

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
| Required fields and types on course, section and activity (activity `type`, `idnumber`, `title`; section `number`, `title`, `activities`). A section's `idnumber` is **not** required (next row) | B1.1 | same two tests |
| **A section's `idnumber` is optional** (guide's decision, issue #65): absent is valid, alone or on every section, in both modes, and the second example (`course-without-section-idnumber.yaml`) is the first minus the section idnumbers. A present value is still validated: wrong pattern, a type that is not text, `null` and an empty string, and the two protected defaults are all errors | B1.1, B1.2 rule 6, B1.4 | `test_example_without_section_idnumbers_is_valid`, `test_example_without_section_idnumbers_differs_from_the_main_example_only_there`, `test_section_without_idnumber_is_valid` (first section or all, both modes), `test_a_present_section_idnumber_is_still_validated`, `test_invalid_identifier_is_rejected` (empty string), `test_wrong_type_or_value_is_rejected` (`null` and a number), `test_protected_idnumber_is_rejected` |
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
| **A section without an `idnumber`** (optional, issue #65) is skipped by the idnumber rules: `iter_items` never yields it, so there is no `KeyError`, no empty idnumber, and two sections without one are not duplicates of each other (CK-06 does not report an absent idnumber). An id-less section does not hide a real duplicate elsewhere, and a section without an `idnumber` is never matched by a configured protected idnumber (a protected item is defined by its `idnumber`). A `null` or empty section `idnumber` is still a schema error. Works through `validate_package` too | B1.1, B1.2 rule 6, B1.4 | `test_iter_items_skips_a_section_without_idnumber_and_never_yields_an_empty_one`, `test_sections_without_idnumber_are_valid_and_are_not_duplicates_of_each_other` (both modes), `test_a_section_without_idnumber_does_not_hide_a_real_duplicate`, `test_a_site_protected_idnumber_is_not_matched_by_a_section_without_one`, `test_a_null_or_empty_section_idnumber_is_an_error_not_a_missing_one`, `test_a_package_without_section_idnumbers_is_valid` (both modes), `test_the_second_example_is_a_valid_package` |
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
| **Unlock rule by mode** (B1.2 rule 2, guide-confirmed). "Previous" is document order; the section number, `idnumber` and title are not read. An absent `unlock` equals both fields null. Full: the first section must have `after` null (a start date is allowed), because nothing earlier exists to name; every later section needs `after` naming the single assignment of the section just before it, and that section must hold exactly one assignment, or it is reported; `start_date` is optional and never replaces `after`; the last section may hold any number of assignments. Sections-only: every listed section, a single one included, needs `after`. It may name a template activity the package lacks; that is not a package error, and a name that matches nothing after the merge is the checker's CK-04. It must not name an activity of its own section or of a later section; cycles across sections are the checker's CK-05. Only the idnumber's shape is judged, by the schema. Reported as `unlock_after_missing`, `unlock_after_not_previous_task`, `unlock_after_on_first_section`, `unlock_previous_task_count` and `unlock_after_forward_reference` | B1.2 rule 2 | `test_full_mode_first_section_is_valid_in_every_form`, `test_full_mode_first_section_must_not_have_after`, `test_full_mode_later_section_with_the_previous_task_is_valid`, `test_full_mode_later_section_without_after_is_rejected`, `test_full_mode_after_must_be_the_previous_weeks_task`, `test_full_mode_previous_section_with_two_assignments_is_reported`, `test_full_mode_previous_section_without_an_assignment_is_reported`, `test_the_last_section_may_have_any_number_of_assignments`, `test_previous_week_follows_document_order_not_the_section_number`, `test_sections_only_after_may_name_an_activity_that_only_the_template_has`, `test_sections_only_section_without_after_is_rejected`, `test_sections_only_after_naming_a_later_section_is_a_forward_reference`, `test_sections_only_a_reference_inside_its_own_section_is_rejected`, `test_sections_only_template_references_stay_accepted`, `test_sections_only_a_cycle_through_the_template_is_not_a_package_error`, `test_a_single_section_sections_only_package_still_needs_after`, `test_a_moodle_assign_type_never_reaches_the_unlock_rule`, `test_a_badly_shaped_after_is_a_schema_error_and_the_unlock_rules_wait` |
| **Availability JSON is read by type, and `cm = -1`** (B2, guide-confirmed, still provisional until verified on Moodle 4.5 and 5.3). `libs/contracts/availability.py` finds conditions by `type`, never by position, and resolves -1 to the nearest earlier activity with manual or automatic tracking; none eligible gives None. For a section's availability, "earlier" is strictly before the section: the last tracked activity of the earlier sections, never an activity inside the section itself. An index outside the model is refused with a `ValueError`, never resolved to another activity. Nested groups (`c`) are searched as an implementation detail; B2 does not constrain the nesting It does not report CK-04 | B2 | `test_condition_order_does_not_change_the_interpretation`, `test_minus_one_resolves_to_the_previous_tracked_activity`, `test_minus_one_skips_activities_without_tracking`, `test_minus_one_with_no_eligible_earlier_activity_cannot_be_met`, `test_a_section_rule_never_resolves_to_an_activity_inside_the_same_section`, `test_a_section_rule_resolves_to_the_last_tracked_activity_of_the_section_before`, `test_an_out_of_range_holder_never_returns_the_last_tracked_activity` |
| `body_files_not_checked` is listed for a parsed document (it reads no files) and for a package whose `course.yaml` could not be validated, and is left out only when the body files were checked. The idnumber rules and the settings apply to a package too, and a wrong `config` is refused before anything is read | B1.1 | `test_body_files_are_listed_as_not_checked_and_never_looked_for`, `test_body_files_are_not_checked_while_the_structure_is_invalid`, `test_the_other_course_rules_and_the_settings_also_apply_to_a_package`, `test_a_wrong_config_is_refused_before_anything_is_read` |
| A report is ok when it has no errors; "not checked" entries do not make it fail; issues cannot be changed after creation | n/a | `test_empty_report_is_ok`, `test_report_with_an_error_is_not_ok`, `test_not_checked_items_do_not_make_a_report_fail`, `test_issue_defaults_are_a_document_level_issue`, `test_issue_cannot_be_changed_after_creation` |

This is not FR-S-03 or FR-C-03: the checker's rules (CK-xx) work on the course model (B2), which
this library does not build.

### Documented but not automatically enforced

Nothing in the repository enforces these yet. Each is listed as "not checked" in every report the
validator returns (seven B1 entries, `h5p_files_not_checked` (B7, below), plus the body files when they were not checked; the B1.3 row
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

The vectors for these rules that concern the `Check` cell (the parser cells, including the empty
pieces, the trailing `;` and the name case) are in
`contracts/test-vectors/check-cells.v1.json`; see "B1 check cells (vectors and tests)" below. This
section has only the README heading and fence vectors.

| What is checked | PRD | Test(s) |
|---|---|---|
| The vectors file is LF JSON with a version, the submission cases and the README cases, with unique ids; each case has the exact shape and closed vocabularies; expected values are consistent (a word count equals the words of the report, a report file named as the source is in the input, a part has a value or an error, never both); the status is `derived` or `unverified-until-lab`, and only the HTML case is unverified | B1.5 | `test_vectors_file_is_lf_json_with_a_version_and_unique_case_ids`, `test_case_has_the_required_shape_and_consistent_expected_values` (every case), `test_only_the_html_case_is_unverified_until_the_lab` |
| The shape check and the duplicate-id check catch the mistakes they exist for (a missing key, the retired status `confirmed`, an unknown or repeated reason code, a wrong word count, a value with an error, a file source with no file, an HTML case marked `derived`, an unknown rule id or input key, a rule that a result cannot show, a word count that `covers` does not declare) | B1.5 | `test_the_shape_check_catches_what_it_exists_for` (one negative control for each mistake listed), `test_the_duplicate_id_check_catches_a_repeated_id` |
| `covers` says what a case shows: rules 8 and 9 are never listed (a result that lists the three parts cannot show them); the word count is listed exactly when the report has a word count; an expected error lists rule 7, an HTML case rule 5, a report from a file rule 4; rules 1 to 7 and the word count are each covered by at least one submission case | B1.5 | `test_case_has_the_required_shape_and_consistent_expected_values` (every case), `test_every_rule_a_vector_can_show_is_covered_by_a_vector` |
| The five PRD examples are the five required vectors: same text, word counts and reason codes; example 4 quotes the same report file | B1.5 | `test_prd_examples_are_the_five_required_vectors` |
| The PRD has the B1.3 check formats (`;`, spaces around a check and its argument ignored, the name before the first `:`, a cell with only `—` means no machine check, `readme_sections` with no comma or semicolon in a name, the README as `README.md` at the repository root, ATX headings with up to three leading spaces and a space or tab after the `#`, a closing `#` sequence removed only after a space or tab, trailing spaces and tabs removed, the whole heading text matched, fences of at least three backticks or three tildes with up to three leading spaces, a closing fence with the same character and at least the length, an unclosed fence running to the end of the file, Setext headings are not headings, `word_count:<n>` as one or more ASCII digits with a value of at least 1, `http_ok:demo_url` only, lowercase case-sensitive check names, an unknown name, a known check with an argument that breaks a defined format, an empty list, name or field, and a trailing `;` fail CK-09) and says what it does not define (only `command:<name>`, the `repo_file:<path>` argument, the criterion keys and other table-parsing details); the finer Markdown details are no longer listed as undefined; C3.5 says `word_count` reads the report and its list of checks is the list the tests use for `unknown_check` | B1.3, C3.5 | `test_prd_b13_has_the_check_formats_and_names_what_it_does_not_define`, `test_prd_c35_says_word_count_reads_the_report`, `test_the_c35_names_in_the_tests_are_the_names_in_the_prd` |
| The README cases (a file in `files`, a `check`, and a result of `pass`, `fail` with the missing names, or `invalid` with the unknown check) have the exact shape and a result that fits the check; together they cover the README file rule (`README.rst` is the other file name, because `readme.md` is the same file as `README.md` on a case-insensitive file system), the heading rules (a whole-text match, a closing `#` sequence only after a space or tab, a tab, trailing spaces and tabs, up to three leading spaces for a heading and for a fence, a closing fence of the same character and at least the length, tilde and unclosed fences, a single backtick and a pair of tildes that are not a fence) and the name rule, and each result kind. The unknown check must be a whole check name, not part of a longer one, and not a known C3.5 check name. They are data for the future marking-table parser: no test reads a README or finds a heading | B1.3 | `test_readme_case_has_the_required_shape_and_a_consistent_result`, `test_readme_cases_cover_the_file_the_headings_and_the_name_rule`, `test_the_readme_check_catches_what_it_exists_for` (one negative control for each mistake it lists, including a check name that only contains the unknown name, and `readme_sections:Setup;word_count:5` with the unknown check `word_count`, which must be rejected) |
| B1.5 has nine numbered rules, both reason codes, the rule 7 clarifications (labels before `Report:`, a second `Report:` line is part of the report, one error does not stop the other criteria from being graded), the "should" rule for task text and the unverified HTML note; every `covers` entry of a vector names a rule that exists; the PRD names the vectors file | B1.5 | `test_prd_b15_has_nine_numbered_rules_and_both_reason_codes`, `test_every_covers_entry_names_a_rule_the_prd_has`, `test_the_prd_mentions_the_vectors_file` |
| The open points are written down, not decided: B1.5 says "Not defined in v1", this section lists each open decision with who decides it, and no vector covers one (no carriage return, empty label value, HTML entity or link, or trailing whitespace; URLs only on `example.org`) | B1.5 | `test_prd_b15_says_what_v1_does_not_define`, `test_traceability_lists_the_open_decisions_and_who_decides_them`, `test_case_does_not_decide_an_open_point` (every case), `test_the_open_point_check_catches_what_it_exists_for` (one negative control for each kind of open point listed) |

**Not enforced (no reader exists).** The marking-table parser (Module 2, `libs/contracts`, used first
by CK-09) and the submission extractor (Module 3, Release 4) are not written; the extractor must
pass these vectors, and B8.4 (PR #31) must use the same vectors. The held rules
`marking_table_not_checked` and `check_vocabulary_not_checked` stay held. The HTML expected result
is unverified until the lab check on Moodle 4.5 and 5.3. Every other expected result is
`derived`: the rules are the guide's, but each example and its result still need a reviewer's
confirmation. The "should" rule for task text (B1.5 rule 9) is guidance and is not validated.

#### B1 check cells (vectors and tests)

Files: the PRD text (B1.3 "Check formats"), `contracts/test-vectors/check-cells.v1.json` and
`libs/contracts/tests/test_check_cell_vectors_v1.py`. The rules were decided by the guide on PR #87
(2026-11-15). No schema, example package, validator or library code changes. The tests check the
data and the text only: the marking-table parser (Module 2, CK-09) does not exist yet and must pass
these vectors; there is no test-only parser.

| What is checked | PRD | Test(s) |
|---|---|---|
| The vectors file is LF JSON with a version and the twenty-three cases (five valid, two with no machine check, sixteen invalid), with unique ids; each case has the exact shape and closed vocabularies (status, result kind, rule, `covers`); the expected result fits the cell (the names of a `checks` result are the cell's check names in order, an argument is null exactly when the check has no colon, has no space at its ends and follows its B1.3 format; a `none` result is only a blank cell or the em dash; an `invalid` result is rule `CK-09` and names a whole check of the cell, not part of a name, or the empty name of an empty check) | B1.3 | `test_vectors_file_is_lf_json_with_a_version_and_unique_case_ids`, `test_case_has_the_required_shape_and_a_consistent_result` (every case), `test_the_valid_and_invalid_cases_are_the_agreed_twenty_three`, `test_the_empty_piece_cases_name_the_empty_check` |
| The cases cover each B1.3 rule they claim (`;`, spaces ignored, name before the first `:`, a blank cell and the em dash alone, lowercase case-sensitive names, the `word_count` argument, `demo_url` as the only `http_ok` field, an unknown name, a known check with a bad argument, the empty pieces) and each result kind | B1.3 | `test_the_cases_cover_every_rule_they_claim_and_each_result_kind` |
| The two cases for a leading and a doubled `;` are marked `extends-stated-rule`: B1.3 states the trailing `;`, and these apply the same reason (an empty check) to the other positions, so they need the guide's or M2's confirmation. No other case has that status | B1.3 | `test_only_the_two_unstated_positions_extend_a_stated_rule`, `test_the_shape_check_catches_what_it_exists_for` (the two status controls) |
| No case decides an open point: no space before the colon, no cell that mixes the em dash with other checks, no whitespace-only cell, no argument for `repo_clone`, no `repo_file` or `command` check. The empty pieces and the name case are decided by the PRD text, which the tests read | B1.3 | `test_case_does_not_decide_an_open_point` (every case), `test_the_open_point_check_catches_what_it_exists_for` (one negative control for each), `test_the_prd_states_the_rules_the_decided_cases_rely_on` |
| The shape check and the duplicate-id check catch the mistakes they exist for (a missing key, an unknown status, rule or result kind, a name that is not in the cell, checks in the wrong order, an argument with a space at its end or for a check with no colon, a `none` result for a cell that is not blank or the em dash, a blank cell read as an empty check, a cell of only spaces, a wrong rule, a check that is not in the cell or only part of a name, and each decided failure read as a valid check: a trailing `;`, an empty list, name or field, a capital letter in a name, `word_count:0`) | B1.3 | `test_the_shape_check_catches_what_it_exists_for` (one negative control for each), `test_the_duplicate_id_check_catches_a_repeated_id` |
| The PRD names the vectors file next to the check formats; the open decisions are listed with who decides each | B1.3 | `test_the_prd_names_the_vectors_file_next_to_the_check_formats`, `test_traceability_lists_the_check_cell_open_decisions` |

**Not enforced (no parser exists).** That a parser gives these results is not tested: the parser is
not written. Every expected result is `derived` (or `extends-stated-rule` for two cases): the rules
are the guide's, but each cell and its result still need M2's confirmation.

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
| The parser test vectors for the B1.3 check cells (the guide's comments of 2026-11-15 and 2026-11-16: the cells and Shraddha's cases for the empty pieces, the trailing `;` and the name case) | The guide decided: a separate follow-up pull request, as Shraddha proposed | Added in `contracts/test-vectors/check-cells.v1.json` (twenty-three cases; see "B1 check cells" above); they cover what B1.3 states |
| README fence and heading details that B1.3 does not state, raised in review and moved to this follow-up by the guide: a closing fence with text after it; a tab before a `#` or a fence (B1.3 counts spaces only); a backtick fence line that has another backtick later on the same line (such as ```` ```code``` text ````: CommonMark says it is not a fence, B1.3 as written makes it an opening fence that hides every later heading). The case of two tildes (`~~old~~ note`) is stated by B1.3 and has a vector | The guide; a sentence in B1.3 or "not defined" settles each (Shraddha and Harshitha raised the backtick case) | Not defined here; no vector covers them |
| A leading `;` and a doubled `;` (Harshitha's point; the guide moved it to the follow-up): B1.3 states only the trailing `;`, so the two cases apply the same reason (an empty check) to other positions and are marked `extends-stated-rule` | The guide, or Shraddha (M2) if the guide delegates; one sentence in B1.3 would settle it. **Shraddha (M2) confirmed both fail** (review comment on #110, 2026-11-17), so only the guide's agreement is left | Two vector cases, marked; they bind a parser only after confirmation |
| Which check is reported when one cell has more than one failing piece (for example `word_count:0;repo_clon`): B1.3 says each failing check fails CK-09, not which one a parser reports. M2's reference parser reports the first failing check in cell order (Shraddha, review comment on #110, 2026-11-17; raised again by Harshitha's approval) | The guide, with Shraddha (M2) | Not defined; no vector has more than one failing piece |
| Parser vectors not covered because B1.3 does not state the rule: a space before the colon (`word_count :200`); a cell that mixes the em dash with other checks (`—;word_count:5`: B1.3 defines only a cell that contains only `—`; M2's reference parser treats such a `—` as an unknown name); a `Check` cell of only spaces (a blank cell and an empty check are different); an argument for `repo_clone`; the arguments of `repo_file` and `command` | The guide, with Shraddha (M2) | Not defined here; no vector covers them |
| The names of the result kinds in the check-cell vectors (`checks`, `none`, `invalid` with rule `CK-09` and the failing check's name, or the empty name of an empty check): the file's own labels, derived by the contract owner | Shraddha (M2), who owns the parser; the guide approves | As written in the vectors file **Confirmed by Shraddha (M2)** on #110 (2026-11-17): CK-09 will return these labels |
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
- **Matching sections by number on reverse import and round trip** (B1.1, decision record
  `docs/decisions/0007-b1-optional-section-idnumber.md`; the guide's answer on issue #65). The PRD
  states it; nothing enforces it here, because it needs the reverse importer (FR-S-08, Release 2) and
  the course-model comparison (FR-C-05, Release 1). FR-C-05 compares by section number (the row for
  it is in Module 2's pull request #46), and CK-07 does not apply to a section without an `idnumber`.
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

## B4 Moodle web-services contract (v1), Release 0 foundation

Files: `contracts/moodle-ws.v1.md` (normative rules), `contracts/moodle-ws.v1.schema.json`,
`contracts/examples/moodle-ws.v1.functions.json` (allow-list), `libs/contracts/tests/test_moodle_ws_v1.py`.
**Contract work only, draft, not verified on any Moodle site.** Guide's decisions on Q1, Q24 and
Q37: PR #27. Guide's B4 findings (set_user_flags removed, save_grade parameters, read-back,
capabilities, course identification): rules §2 to §4, with Moodle source evidence in rules §7.
Guide's decisions on the eleven B4 questions (PR #64, 2026-11-12): rules §3a (R1 to R11), §3b and
§4, the PRD B4 tables and draft rule, and lab checks 13 to 16.

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
| Always-sent and optional parameters equal the PRD B4 parameter table for each function; none is in both lists; `mod_assign_save_grade` sends `workflowstate` | B4, App-C 1 | `test_every_parameter_is_named_in_the_prd_for_its_function`, `test_example_parameters_equal_the_prd_parameter_table`, `test_the_prd_names_exactly_these_parameters`, `test_no_parameter_is_both_required_and_optional`, `test_a_parameter_not_named_for_its_function_is_found`, `test_save_grade_sends_the_workflow_state` |
| `mod_assign_save_grade` has the guide's seven required and two optional parameters | B4 (guide's findings) | `test_save_grade_has_the_guides_required_and_optional_parameters` |
| "Always sent" (LearnOps's rule) is kept apart from what Moodle requires; the PRD column says "Always sent" | B4 | `test_always_sent_is_kept_apart_from_moodle_required` |
| `mod_assign_set_user_flags` is in neither the allow-list, the PRD B4 tables nor the rules table | B4 (guide's findings) | `test_set_user_flags_is_allowed_nowhere` |
| The read-back sends `assignid` and `userid`, and the rule (`lastattempt.gradingstatus` exactly `readyforrelease`, otherwise not verified) is stated in the rules and the PRD | B4 draft rule | `test_the_status_read_back_sends_assignment_and_learner`, `test_the_read_back_field_is_stated_in_the_rules_and_the_prd` |
| A write counts as done only when both the state and the grade value are confirmed; the state alone is never enough | B4 draft rule | `test_success_needs_both_the_state_and_the_grade_value` |
| The write rules are exactly R1 to R15 (guide's decisions on PR #64 and, for R12 to R14, PR #72; rules §3a) | B4 draft rule | `test_the_write_rules_are_exactly_r1_to_r15` |
| R1: `mod_assign_get_grades` is the stored-grade read-back, in the allow-list, rules §2 and the PRD tables (always sent: `assignmentids`), with the §3b matching rule | B4 draft rule | `test_r1_get_grades_is_the_stored_grade_read_back` |
| R2: `attemptnumber` is the explicit attempt, never `-1`; the read-back matches it | B4 draft rule | `test_r2_attempt_number_is_explicit_never_minus_one` |
| R3: a write is refused before sending when the state is already `readyforrelease` or `released`, and is still read back; the 4.5 / 5.3 difference is recorded for the lab; R3 holds on 5.3 and is best effort on 4.5, named in the release notes (guide, 15 Nov) | B4 draft rule | `test_r3_locked_states_are_refused_before_sending_and_still_verified` |
| R4: `viewhiddencourses`, `viewhiddendetails` and `useremail` are not granted | B4, SEC-03 | `test_r4_declared_capabilities_are_not_granted` |
| R5: suspended learners are skipped and reported as skipped; `viewsuspendedusers` is not granted | B4 | `test_r5_suspended_learners_are_skipped_and_reported` |
| R6: `viewownsubmissionsummary` stays lab check 12 | B4, App-C 1 | `test_r6_view_own_submission_summary_stays_a_lab_check` |
| R7: `mod/assign:reviewgrades` is granted on both versions | B4, SEC-03 | `test_r7_review_grades_is_granted_on_both_versions` |
| R8: a failed read-back is `NOT_VERIFIED` and the write is never repeated | B4 draft rule | `test_r8_failed_read_back_is_not_verified_and_never_rewrites` |
| R9: exact numeric match after parsing, no tolerance; range checked before writing | B4 draft rule | `test_r9_exact_numeric_match_and_range_check_before_writing` |
| R10: no submission, no grade and no access are separate outcomes, never success; other learners continue | B4 | `test_r10_missing_and_inaccessible_are_separate_outcomes` |
| R11: an uncertain write is never retried automatically; read back, the mentor decides | B4 draft rule | `test_r11_uncertain_write_is_never_retried_automatically` |
| R12: a state that cannot be read, or is none of Moodle's six marking-workflow values, is refused before anything is sent (`REFUSED_STATE_UNKNOWN`) | B4 §3a (guide, PR #72) | `test_r12_an_unreadable_or_unknown_state_is_refused_before_sending` |
| R13: marking workflow off (`graded` / `notgraded`) is refused before anything is sent (`REFUSED_WORKFLOW_OFF`); lab check 4 stays open | B4 §3a (guide, PR #72), PRD C-09 | `test_r13_marking_workflow_off_is_refused_before_sending` |
| R14: a matching read-back after a lost answer is not done until the mentor confirms it (`NEEDS_MENTOR_CONFIRMATION`) | B4 §3a (guide, PR #72) | `test_r14_a_matching_read_back_after_a_lost_answer_needs_the_mentor` |
| R15: `applytoall=0` and `addattempt=0` are always sent; any other value is refused before anything is sent | B4 §3a (guide, PR #64, 2026-11-16) | `test_r15_applytoall_and_addattempt_are_pinned_to_zero` |
| The three former open questions are rules now; each refusal is its own outcome; §6 keeps the lab-access row | B4 §3a, §6 | `test_the_three_proposals_are_rules_now_and_no_longer_open` |
| Course lookup sends `field` and `value`, by course id or shortname, never idnumber | B4 course identification | `test_course_lookup_does_not_rely_on_idnumber` |
| The capability lists (needed, never granted) are the guide's and do not overlap; a custom role is required | B4, SEC-03 | `test_the_capability_lists_are_the_guides_and_do_not_overlap`, `test_the_custom_role_rule_is_stated` |
| Every lab check in rules §5 (1 to 18) is still open on both versions, with no decision record; checks 13 to 16 name the rule they cover; checks 17 and 18 ask whether `core_course_get_contents` and `mod_assign_get_assignments` return the `idnumber` fields (guide, 15 Nov; reviewer on PR #64, 16 Nov) | App-C 1 | `test_every_lab_check_is_still_open`, `test_the_decision_lab_checks_name_their_rules` |
| The rules stay a draft (Status line `Draft`, not approved), no §2 function is marked verified, and the draft rule never allows `released`; each test fails if that text is changed | B4 draft rule, C-09, App-C 1 | `test_the_contract_is_still_a_draft_and_not_approved`, `test_no_function_is_marked_verified`, `test_a_grade_write_never_sends_released` |
| A replacement name for a Moodle version also appears in the PRD B4 text | B4 ("replacements recorded here") | `test_a_replacement_name_is_also_in_the_prd` |
| No verification state is stored in the schema or example | Guide, Q1 | `test_invalid_document_is_rejected_at_the_expected_place` (three verified-flag cases) |
| Schema is valid; example validates; invalid documents fail at the expected place; unknown fields are accepted | B.0 rule 1, rule 2 | `test_schema_is_a_valid_draft_2020_12_schema`, `test_example_is_valid`, `test_invalid_document_is_rejected_at_the_expected_place`, `test_unknown_fields_are_accepted` |
| One token variable per site with a placeholder; no single `MOODLE_WS_TOKEN` | B4, SEC-03, C-06; guide, Q24 | `test_one_token_variable_per_site_with_a_placeholder` |

### Documented but not automatically enforced

| Rule | PRD |
|---|---|
| Only the functions listed in the contract are called (`libs/moodle_ws` will build its allow-list from the example; the library does not exist yet) | B4 |
| One service account per site, with a token restricted to those functions and the capabilities in rules §4 (the lists are tested; that they are enough is lab check 9) | B4, SEC-03 |
| The token is stored only in the environment | SEC-03, C-06 |
| A grade write uses workflow state `readyforrelease`, never `released`, and counts as done only when both the state and the grade value are confirmed; the grade value is read with `mod_assign_get_grades` (R1); the write rules R1 to R15 are contract text here, and their enforcement in `libs/moodle_ws` is a separate follow-up; only approved drafts are written | B4, C-09 |
| Each function exists and behaves as expected with the parameters used on Moodle 4.5 and 5.3 (all lab checks in rules §5 are still open) | B4, App-C 1 |

Open: when the lab Moodle sites are available (all checks in `moodle-ws.v1.md` §5 wait for
them; B4 cannot be frozen until they pass), and the field for feedback comments inside `plugindata` on
`mod_assign_save_grade` (lab check 6). Q1, Q24 and Q37 are decided (PR #27); the eleven B4
questions are decided (PR #64), and so are the three that followed: the state that cannot be read before
a write, marking workflow off, and a lost answer with a matching read-back (R12 to R14, PR #72).

## B7 H5P practice output contract (v1), Release 0 foundation, DRAFT

Files: `contracts/h5p-practice.v1.md` (normative text), `contracts/h5p-practice.v1.schema.json`,
`contracts/examples/h5p-practice.v1/content-types.json` (the B7 example), the B1 example package
`contracts/examples/course-package.v1/h5p-practice.yaml` with its bodies in
`contracts/examples/course-package.v1/h5p-practice/` (no `.h5p` file), the `file` field in
`contracts/course-package.v1.schema.json`, the decision record
`docs/decisions/0008-h5p-content-types.md` (the lab check, PRD App-C item 5), and the tests
`test_h5p_practice_v1.py` and `test_course_package_v1.py` in `libs/contracts/tests/`. B7 has no
requirement ID of its own in the
PRD (it is a contract, PRD B.0). It is used by FR-S-12 and FR-V-14 (Release 5, stretch) and by
FR-C-03 CK-11 (Release 1). No row in the table at the top maps to it.

**Status: draft and not approved.** The H5P library versions were verified in the lab on 2026-11-11
(the guide's lab check, reported on this pull request; PRD App-C item 5) and are pinned in the B7
schema. Whether the open decisions below block the freeze is the guide's decision. The B1 section
above is on main; the B1 `file` field added with B7 is covered in the first table below.

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
| The content-type schema is valid and its example validates; bad lists are rejected: invented names, other capitals, the old PRD phrase or a machine name as a name, a name listed twice, a missing name, `machine_name` or `version`, a wrong or lower-case machine name, a wrong version, a `v` prefix, a version that is a number, the Drag the Words and Drag and Drop versions or libraries swapped, a wrong schema name, an empty list. Each of the five types alone is valid, and unknown fields are accepted | B.0 rule 1, B7 | `test_schema_is_valid_and_example_validates`, `test_invalid_content_type_list_is_rejected` (22 cases), `test_a_list_with_one_pinned_type_is_valid`, `test_missing_root_field_is_rejected`, `test_unknown_fields_are_accepted` |
| The schema allows exactly the five names, requires `name`, `machine_name` and `version`, and pins each name to the library and exact version of the guide's lab check (written out in the test as `PINNED`); the names are words PRD B7 uses; the example lists exactly the five pinned entries; the contract text says interactive video is for lab demonstrations only (a rule of the text, not a schema field) | B7, App-C item 5 | `test_schema_pins_exactly_the_guides_table`, `test_example_lists_exactly_the_pinned_entries` |
| The contract text table and the decision record hold the same five pairs as the test, so a swapped version in any of the four places fails; the text, the schema and this file point to the decision record | App-C item 5 | `test_contract_text_and_decision_record_agree_with_the_pins`, `test_text_schema_and_traceability_point_to_the_decision_record` |
| The schema and example define no key `cue`, `cues` or `ref` (cues belong to B6), and the text says B7 defines no second format | B6.2 | `test_no_cue_key_is_defined_and_cues_are_left_to_b6` |
| The text no longer marks a content type "to verify in the lab" and no longer lists the two decisions the lab check settled; it keeps the other open decisions marked, says each practice item uses one type, that ordering is done with Drag and Drop, that a later type is an optional entry and that a version change needs a `/contract-change`, and says practice is optional and never graded | B7 | `test_text_pins_the_types_and_keeps_only_the_open_decisions_still_open` |
| `file` is defined in the `h5p` branch of the B1 schema only | Issue #44 answer 2 | `test_file_is_defined_in_the_h5p_branch_only` |
| Example only: the package validates against B1; its week has one Page and one Assignment; its ordinary practice item is ungraded, names a lowercase `.h5p` path that does not exist, and comes right after the guide Page | B1, B7 | `test_example_package_validates_against_b1`, `test_example_week_is_standard_with_an_optional_practice_item` |
| Example layout for the shared example validator (PR #68): the B7 folder `examples/h5p-practice.v1/` holds only valid B7 documents, and the example B1 package is a top-level file in `examples/course-package.v1/` with its bodies in a subfolder, so the B1 example is untouched | B.0 rule 1, EXT-09 | `test_b7_example_folder_holds_only_b7_documents`, `test_example_package_sits_in_the_b1_example_folder` |
| No `.h5p` file exists anywhere in the repository | Issue #44 answer 7 | `test_no_h5p_file_is_kept_in_the_repository` |

### Documented but not automatically enforced

| Rule | PRD | Where the PRD places it |
|---|---|---|
| An ordinary practice entry comes right after the week's guide Page, and a week has one Page and one Assignment, in a package in general | B7, B1.2 rule 1 | Needs validator code; B1.2 rule 1 is itself not enforced yet |
| Where a video checkpoint goes | B7 | Open decision; PRD B7 says "after the video" |
| A practice (H5P) activity has no grade item | B7 | CK-11 (FR-C-03, Release 1), on the course model (B2) |
| Media referenced by a full fixed URL instead of a relative path | C-08 | CK-12 (FR-C-03, Release 1) |
| The file named by `file` exists, is valid, and uses one of the pinned libraries at its pinned version | B7 | Held rule `h5p_files_not_checked`, listed in every report; no check exists (`test_h5p_files_are_listed_as_not_checked_and_never_looked_for`) |
| Interactive video only in lab demonstrations | B7 | A rule of the contract text, named in the same held rule; no check exists |
| AI-drafted items are approved by a mentor before they reach learners | C-09, FR-S-12 | A process rule of Studio, not a data rule |
| `cues.json` entries are valid | B6.2, FR-V-14 | The B6 cues schema does not exist yet. Student 4 proposes `type: "h5p"` with `ref` = the practice item's `idnumber`; this is provisional, quoted in B7 section 6, and not enforced here |

### Open decisions and not mapped

Closed by the guide's lab check of 2026-11-11 (App-C item 5; `docs/decisions/0008-h5p-content-types.md`):
the H5P library versions, and whether "drag-the-words or drag-and-drop / ordering" is one type (it is
two entries). Open: the `ref` kinds and the cue fields (Student 4, in the B6 cues schema, still to
come; her `h5p` + `idnumber` encoding is only a proposal); several practice items in one week and
video checkpoint placement (the guide has not decided; B7 makes no rule); and whether a data field
should mark interactive video as lab-only (a question for reviewers). Not mapped: a
row, demo step and Bloom level for FR-S-12 and FR-V-14, because the PRD does not say schema tests
count towards them. This pull request adds M2 to the B7 "Used by" row in PRD B.0 (guide, Issue #44).

## B8.1 template course backup (test data), Release 0 foundation

Files: `testdata/b8-1-template-course/README.md` (the requirements, the proposals and the open
decisions, and a plain list of the expected protected items for the checker); the B8.1 entry in
`testdata/README.md`. B8.1 is a test data set (PRD §B8, B1.4) and has no requirement ID of its own,
so no row in the table at the top maps to it. No `.mbz` exists yet. The badge image and the download
script exist and are tested (the two rows below that name tests).

| What is documented | PRD | Test(s) |
|---|---|---|
| The template course backup holds the four protected items: the final project assignment (`final-project`), the course feedback activity (`course-feedback`), the course completion criteria and the course badge. The idnumbers are the PRD defaults and are configurable. The protected section number (3) is owner-confirmed (#61 A2, 2026-11-16) and stays configurable | B8.1, B1.4 | None yet: the `.mbz` does not exist |
| A plain list of the expected protected items (idnumber, type, section, count) for the checker, which builds its model from the `.mbz` | B8.1, B1.4 | None yet |
| The course badge image is a plain square PNG made by the project (`make_badge.py`, standard library only, Apache-2.0), kept with its source in the B8.1 folder; `--check` confirms the committed `badge.png` matches the script (Owner, Issue #55, 2026-11-18, P9b) | B8.1, C-11 | `test_committed_badge_matches_its_generator`, `test_badge_is_a_square_rgb_png`, `test_badge_check_catches_another_image` (negative control), `test_badge_dry_run_writes_nothing`, `test_badge_writes_a_file_that_passes_check` |
| The download script `download.py` verifies the SHA-256; `--check` (read-only) and `--dry-run` write nothing; during a download, a failed SHA-256 verification, a failed download or Ctrl+C removes the `.part` file; it refuses to run until a SHA-256 is recorded; tag `testdata-b8-1-v1`, a rebuild gets a new tag (Owner, Issue #55, 2026-11-18, P24, P33) | B8.1, root `CLAUDE.md` rule 9 | `test_no_recorded_sha_refuses_and_writes_nothing`, `test_download_verifies_and_keeps_no_partial_file`, `test_wrong_sha_removes_the_partial_file`, `test_failed_download_removes_the_partial_file`, `test_ctrl_c_removes_the_partial_file`, `test_partial_downloads_are_gitignored`, `test_check_reports_a_changed_or_missing_file`, `test_dry_run_writes_nothing`, `test_release_names_follow_the_guides_rule` (all in `libs/contracts/tests/test_b8_1_files.py`) |
| A sections-only backup is merged into the template and the protected items stay unchanged. The intended comparison writes down the same table for each protected item before and after the merge, with the fields type, name, idnumber, section number, points, completion setting and visibility, and the two tables must be equal (Owner, Issue #55, 2026-11-12); no check or test implements this yet. The Release 0 backup procedure is written as an untested draft | B1.4, C1.7, App-C item 2 | None yet: needs a Moodle site |
| Moodle 5.3 is the owner-confirmed build and test version for Release 0 (Issue #55, 2026-11-14 reply, which replaces the 2026-11-12 decision to build on 4.5). Every restore and the sections-only merge are tested on 5.3 only, recording the Moodle version, the date and the outcome of each restore; the `.mbz` is labelled "built on Moodle 5.3". The owner reports that Moodle documents that a backup restores into the same or a newer version only, so the 5.3 template is expected not to restore on 4.5 (the owner's report: not verified here, and the PRD does not state it). Moodle 4.5 is **not tested; waived for Release 0 (B8.1 only; see [0009](decisions/0009-b8-1-template-course.md) and the [register](decisions/README.md))**, not recorded as passed; if PRD C-03 later needs the template on 4.5, it is rebuilt once on 4.5 | C-03 | None yet: not verified; needs Moodle lab testing on 5.3. Moodle 4.5: not tested; waived for Release 0 (B8.1 only; see [0009](decisions/0009-b8-1-template-course.md) and the [register](decisions/README.md)) |
| Deviation - C-03: the B8.1 template is built and tested on Moodle 5.3 only; 4.5 not tested, waived for Release 0 (B8.1 only; see [0009](decisions/0009-b8-1-template-course.md) and the [register](decisions/README.md)). The B8.2 restore and merge tests have their own decision, made by the guide on 2026-11-16 (A5 on PR #61, recorded there with B8.2, not here); C-03 still applies to the harness (FR-C-08) | C-03 | None (a recorded deviation, not a test) |

### Not covered here

These are pending and are not claimed by this change:

- **The `.mbz` backup, its SHA-256 and the release asset (tag `testdata-b8-1-v1`).** None of them
  exists yet. The download script exists but refuses to run until the SHA-256 is recorded in it.
- **Moodle 5.3 verification:** the restore, the protected items, the completion criteria, the badge
  and the sections-only merge (PRD C1.7, App-C item 2). The B8.1 owner's lab access is ready (in person, the
  owner's 2026-11-14 reply), but access is not a result and no lab verification result is recorded. **Moodle 4.5 is not tested; waived for Release 0 (B8.1 only; see [0009](decisions/0009-b8-1-template-course.md) and the [register](decisions/README.md))**
  and is not claimed as passed.
- **The App-C item 2 results.** The decision record `docs/decisions/0009-b8-1-template-course.md`
  exists and holds the Moodle 4.5 waiver (PR #95); its number is taken again at merge, after
  rebasing (Owner, Issue #55). The results are not written. The owner asks for a short, text-only
  results table in the same file that names the local evidence files; screenshots and logs stay
  local and are not committed.
- **The open decisions** in the B8.1 README (§9) were answered by the guide on Issue #55
  (2026-11-18) and are recorded there. What is left is lab work (PENDING MOODLE LAB), including
  whether 5.3 keeps an unawarded badge in a users-off backup (P35).

## B8.2 sample course (test data), Release 0 foundation

Files: `testdata/b8-2-sample-course/` (`package/course.yaml` in `full` mode, eight Markdown bodies
under `package/weeks/`, and a `README.md` with the expected structure and open decisions); its
test `libs/contracts/tests/test_b8_2_dataset.py`; the entry in `testdata/README.md`; the decision record
`docs/decisions/0010-b8-2-sample-course.md`. B8.2 is a test data set (PRD §B8) with no requirement ID of its
own, so no row in the table at the top maps to it.

The dataset test checks this one package only. The rules the shared validator lists as "not checked" are
checked here for B8.2 alone, with test-local helpers: that does not enforce them for any other package, and
it is not CK-03, CK-09 or any other checker rule.

| What is checked | PRD | Test(s) |
|---|---|---|
| The package passes the shared validator (schema, idnumbers unique and not protected, body files exist) | B1.1, B1.2 rule 6 (first half), B1.4 | `test_the_shared_validator_accepts_the_package` |
| `full` mode, `total_points: 100`; four week sections numbered 4 to 7 (after the B8.1 template's sections 1 to 3; Owner, Issue #55, 2026-11-12) with idnumbers `wk-01` … `wk-04` (kept until the B1 section-idnumber change of Issue #65 is implemented) | B8, B1.1 | `test_course_is_full_mode_with_a_total_of_100` (100 for this package; the merged course's 200 is declared in the README, A6, and no test here uses it), `test_there_are_four_week_sections_numbered_4_to_7` |
| Twelve unique idnumbers following the week pattern; no default protected idnumber, no protected item and no `.mbz` in the dataset | B1.2 rule 6, B1.4 | `test_idnumbers_are_the_week_pattern_and_never_protected`, `test_no_protected_item_and_no_backup_file_is_in_the_dataset` |
| The bodies hold no links (a dataset choice so that no third-party material is pulled in; not a PRD rule) | n/a (supports C-07) | `test_bodies_hold_no_links` |
| One guide Page then one task Assignment per week | B1.2 rule 1 | `test_week_has_one_guide_page_then_one_task_assignment` (4 cases) |
| Week N unlocks after the week N-1 task, which has `completion: submit`; week 1 is open | B1.2 rule 2 | `test_week_unlocks_when_the_previous_task_is_submitted` (4 cases) |
| Each task is 25 points and the tasks add up to `total_points` | B1.2 rule 3 | `test_each_task_is_worth_25_and_the_tasks_add_up_to_the_total` |
| Each task has one valid marking table: markers, header, a valid Markdown separator row, non-empty Criterion and Full marks cells, row points add up to the assignment's points, `Check` names from C3.5; no `command:` checks are used | B1.3, C3.5 | `test_task_has_a_valid_marking_table` (4 cases), `test_the_sample_does_not_use_command_checks`, `test_the_table_check_catches_the_mistakes_it_exists_for`, `test_the_table_check_rejects_empty_cells_and_a_bad_separator` (8 negative cases), `test_the_table_check_accepts_valid_markdown_separators` (2 positive controls) |
| A task whose table has a `word_count:N` check tells the learner the report needs at least N words (weeks 1 and 4: 150 and 250) | B1.3, C3.5 (`word_count:<min>`) | `test_task_states_the_minimum_word_count` (4 cases), `test_the_word_minimum_check_catches_a_missing_or_wrong_number` (negative control) |
| Each task body explains the submission format confirmed by the guide on PR #61: `Repository:`, `Demo:` and `Report:` labels, `report.md` or `report.txt` as the report, and which part a check reads, said exactly for the checks that week's own marking table has (weeks 2 to 4 claimed checks their tables lack) | Grading design Q6 (`grading.md` §4.3a); written into B1.3 and B1.5 by PR #87 (open) | `test_task_explains_the_confirmed_submission_format` (4 cases) |
| The week sections are numbered after the template's last section (3), and do not collide with the protected section (3; confirmed by the guide on PR #61, 2026-11-16, A2; not a contract value) | B1.4 | `test_week_sections_are_numbered_after_the_templates_last_section`, `test_week_numbers_do_not_collide_with_the_protected_section`, `test_the_numbering_checks_would_catch_the_old_numbering_1_to_4` (negative control) |
| Deviation - C-03: the B8.2 restore and merge tests run on Moodle 5.3 only in Release 0; 4.5 not tested, waived for Release 0 (B8.2 restore and merge tests only; see [0010](decisions/0010-b8-2-sample-course.md) and the [register](decisions/README.md)). Reason: the only template for Release 0 is the 5.3-built one. C-03 returns in Release 1, when the template is rebuilt on 4.5. Scope: B8.2 restore and merge tests only; the B8.1 row and its record (`docs/decisions/0009-b8-1-template-course.md`) are from PR #95, merged | C-03 | None (a recorded deviation, not a test) |

### Not covered here

These need Studio, the checker or a Moodle site and are not claimed by this change:

- **PRD C1.7** "B8.2 sample course: package → `.mbz` (full) → restored on fresh 4.5 and 5.3 → M2
  checker reports 0 errors", the sections-only merge into B8.1, and the ≤ 15 min loading time.
  The `.mbz` comes from FR-S-06 and FR-S-07 (Release 2).
- **PRD C2.7** "no false errors on B8.2": needs the checker (Release 1).
- **B1.2 rules 4 and 5** (marking workflow, completion tracking): not package fields.
- Decided by the guide on PR #61 (2026-11-16): A2 (section 3 protected; weeks are sections 4 to 7), A6 (totals 100 and 200), A7 (CK-07 and CK-08 not applied on the package
  alone, applied on the merged course), A8 (theme, titles, shortname, 25-point split) and A5 (the deviation row above). Still open: A4 (pending the Moodle lab) and how the
  sections-only variant is made in Release 0. The licence (Apache-2.0) and the submission and check formats (A12, A13) were confirmed by the guide on PR #61; the formats
  are written into PRD B1.3 and B1.5 by PR #87, which is open and waits for the guide.
- The section idnumbers `wk-01` … `wk-04` are kept for now. They need updating when the B1
  section-idnumber contract change (Issue #65) is implemented.

## B8.5 lecture video test data set, Release 0 foundation

Files: `testdata/b8-5-lecture-videos/` (README, folder `.gitignore`, placeholder outlines and
transcripts), the B8.5 inventory in `testdata/README.md`, the guide's decision
`docs/decisions/0004-b8-5-lecture-videos.md`, and the validation test
`libs/contracts/tests/test_b8_5_dataset.py`. B8.5 is a test data set (PRD B8), not a functional
requirement, so it has no FR ID and no row in the table at the top. It is the data for PRD G-6
(caption word error rate, Release 3), App-C 7 (the error-rate target from a first baseline run)
and App-C 8 (licence or consent for every B8.5 video).

**Status: PENDING.** Five local recording files were identified in earlier work (their SHA-256
values are in the inventory), but no consent line is written, no duration is recorded, no
transcript is typed or reviewed, and none is accepted as B8.5 evidence. The tests show that the committed placeholders are well formed and that the PENDING status
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

## B3 LTI launch contract (v1), Release 0 foundation

Files: `contracts/lti-launch.v1.md`, `contracts/lti-launch.v1.schema.json`,
`contracts/examples/lti-launch.v1/` (`instructor-mentor.json`, `institution-administrator.json`,
`mentor-minimal-with-unknown-field.json`: valid examples only), the optional-claim vectors
`contracts/test-vectors/lti-launch-optional-claims.v1.json`, and
`libs/contracts/tests/test_lti_launch_v1.py`. Decision record: `docs/decisions/0001-lti-library.md`.
B3 has no requirement ID of its own in the PRD (it is a contract, PRD B.0), so no row in the table
at the top maps to it.

**Tests for this contract (PRD B.0 rule 3).** In Release 0 the shared contract tests listed below
are the tests that cover B3. A consuming module adds its own tests when its code that reads the
contract exists; before that, the shared contract tests cover the change. No placeholder or skipped
module tests exist, and none are planned here.

SEC-01, SEC-02, SEC-06, SEC-09, EXT-07 and FR-X-01 are deliberately not in the table at the top.
Nothing in this contract's tests implements them: the launch validation, session and refusal
behaviour belong to `libs/lti`, which does not exist yet (ADR 0001, Stage 2 not approved). Each gets
its row in the pull request that implements and tests it.

### Enforced by the JSON Schema and covered by automated tests

Structure only. Test names are in `test_lti_launch_v1.py`.

| Rule | Contract section | Test(s) |
|---|---|---|
| The schema is a valid Draft 2020-12 schema with the B3 v1 `$id` | PRD B.0 rule 1 | `test_schema_is_valid_draft_2020_12` |
| Every example validates; the examples folder holds valid examples only (JSON files, none invalid) | PRD B.0 rule 1, §11 | `test_examples_folder_has_the_required_examples`, `test_examples_folder_holds_json_files_only`, `test_every_example_is_valid` |
| Required fields at every depth: `iss`, `sub`, `deployment_id`, `message_type`, `role`, `context`, `context.id`, `resource_link`, `resource_link.id` | §4 | `test_invalid_launch_result_is_rejected_at_the_right_place` (one `missing-…` case each), `test_every_required_field_has_a_missing_case` (fails if a required field has no case), `test_dropping_a_required_field_reports_exactly_that_field` (the one error names the dropped field) |
| `message_type` is `LtiResourceLinkRequest` only | §2, §4 | `test_invalid_launch_result_is_rejected_at_the_right_place` (`wrong-message-type`) |
| `role` is one of the values in the schema's enum (currently `mentor`, `administrator`; the value set is under review, ADR 0001 OI-25) | §4, §5 | `test_both_baseline_roles_are_accepted`, `test_invalid_launch_result_is_rejected_at_the_right_place` (`role-…` cases) |
| `context.id` is a positive integer written as a string in ASCII digits: zero, negative, non-numeric, leading-zero, whitespace-padded, non-ASCII-digit and newline-containing values are rejected; no upper bound | §3.1 | `test_positive_integer_context_ids_are_accepted`, `test_invalid_launch_result_is_rejected_at_the_right_place` (`context-id-…` cases, including the trailing newline), `test_contract_markdown_quotes_the_schema_context_id_pattern` (drift guard: the contract quotes the schema's pattern) |
| Required strings are non-empty strings; `sub` and `context.id` are strings, not numbers | §4 | `test_invalid_launch_result_is_rejected_at_the_right_place` (`empty-…`, `numeric-…`, `…-not-an-object` cases) |
| `name` and `email` may be `null` or absent; an empty string is rejected. `context.title` may be omitted; an empty string and `null` are rejected | §3.2, §4 | `test_optional_fields_may_be_absent_or_null`, `test_name_and_email_are_valid_when_null`, `test_name_and_email_are_valid_when_absent`, `test_context_title_is_valid_when_omitted`, `test_invalid_launch_result_is_rejected_at_the_right_place` (`empty-name`, `empty-email`, `empty-context-title`, `null-context-title`) |
| Unknown fields are accepted | PRD B.0 rule 2, EXT-02 | `test_unknown_fields_are_accepted` |

### Optional-claim rule (§3.2): shared vectors, covered by automated tests

The vectors in `contracts/test-vectors/lti-launch-optional-claims.v1.json` state the rule as data.
The tests check the vectors and the schema side only. **No normaliser exists:** the rule is to run
once, in `libs/lti`, which has not been created and must pass the same vectors when it is added.

| Rule | Contract section | Test(s) |
|---|---|---|
| `name`, `email`: absent, `null`, empty, White_Space-only and non-string values become `null`. `context.title`: the same values are omitted, never `null` | §3.2 | `test_claim_vectors_are_well_formed`, `test_claim_vectors_cover_every_row_of_section_3_2`, `test_claim_vector_agrees_with_section_3_2`, `test_expected_result_for_every_claim_vector_is_schema_valid` (every vector × `name`, `email`, `context.title`) |
| Every other string is preserved unchanged, character for character, including white space before, after and inside | §3.2 | `test_claim_vectors_cover_every_row_of_section_3_2` (padded cases must exist), `test_expected_result_for_every_claim_vector_is_schema_valid` (UTF-8 bytes equal the input) |
| "White_Space-only" is the 25 code points of Unicode 15.0.0 White_Space, not Python's `str.isspace()`: U+001C to U+001F, U+200B, U+FEFF, U+180E and U+2060 are kept | §3.2 | `test_python_unicode_database_is_unicode_15_0`, `test_vectors_file_lists_exactly_unicode_white_space`, `test_white_space_rule_is_not_python_isspace`, `test_each_white_space_character_alone_is_absent`, `test_isspace_only_character_is_preserved`, `test_optional_claim_vectors_file_is_ascii` (the vectors file stays ASCII, so invisible characters are written as `\u` escapes) |
| A non-string value is rejected by the schema, so a result can never carry one | §3.2, §4 | `test_invalid_launch_result_is_rejected_at_the_right_place` (`numeric-name`, `object-name`, `boolean-name`, `boolean-email`, `list-email`, `numeric-email`, `numeric-context-title`, `list-context-title`) |
| The schema alone accepts a White_Space-only string (the gap the normaliser closes) | §3.2 | `test_schema_alone_accepts_a_white_space_only_string` |
| Contract text names the vectors file and the `str.isspace()` distinction (drift guard) | §3.2 | `test_contract_section_3_2_names_the_vectors_file` |

### Role mapping (§5) and identity (§6, §7): rules restated in the shared tests

These tests restate the contract rules and check them, together with the contract and PRD text.
They are not the gateway: `libs/lti` enforces the rules and must pass the same cases when it is
added.

| Rule | Contract section | Test(s) |
|---|---|---|
| §5 lists exactly the four agreed URIs and their outcomes | §5 | `test_contract_section_5_table_matches_the_agreed_role_uris` |
| Unlisted URIs ignored; Administrator over Instructor; Learner counts only when alone; refused when no recognised role remains (OI-22), in any order | §5, PRD A5 | `test_role_resolution_follows_oi_22_in_any_order`, `test_role_cases_cover_every_oi_22_row_and_every_pair_of_recognised_roles`, `test_resolved_roles_are_schema_values_and_refusals_never_are`, `test_contract_and_prd_state_the_oi_22_rule` |
| Exact matching: the short `Instructor`, `TeachingAssistant`, and case, scheme, whitespace and URN look-alikes are unlisted | §5 | `test_instructor_lookalikes_are_unlisted_and_named_nowhere_in_section_5` |
| Session `(iss, sub, context id)` and course-link key `(iss, context id)` (OI-21); issuer compared as received | §6, §7, §7.1 | `test_session_identity_changes_with_each_of_iss_sub_and_context_id`, `test_two_platforms_with_the_same_user_and_course_numbers_do_not_collide`, `test_other_fields_are_not_part_of_the_identity_or_course_link`, `test_course_link_key_has_no_user_part`, `test_issuer_is_compared_as_received_not_normalised`, `test_contract_prd_and_adr_state_the_decided_identity_and_course_link_key` |

### Documented but not automatically enforced

These rules are written in `contracts/lti-launch.v1.md`. No code enforces them today; where a
shared test restates a rule, it is listed above. They belong to `libs/lti` (not yet created). ADR 0001 §12, LTI-01 to LTI-32, lists
*proposed* acceptance tests for the launch boundary: they are not approved (Stage 2 is not
approved), none exists yet, and none is claimed as working.

| Rule | Contract section | Where it belongs |
|---|---|---|
| Signature, the version claim `https://purl.imsglobal.org/spec/lti/claim/version` (exactly `"1.3.0"`), `exp`, `aud`, `azp`, `iss`, `deployment_id`, message type, single-use nonce and state checks | §3, §8, PRD SEC-01 | `libs/lti`. The contract and PRD wording for the version claim (full URI, exactly `"1.3.0"`, validation-only, never in the result) is checked by `test_contract_and_prd_document_lti_version_as_validation_only` |
| `iss` must exactly match a registered platform (no normalisation); an unverified `iss` only locates the candidate configuration for signature verification; B4 is called only through the client bound to the configuration for the registered issuer, with no fallback to another platform's client | §7.1 | `libs/lti` and the B4 client. The B4 owner has confirmed the registered-issuer and client-binding part; the exact-match and untrusted-until-verified wording is B3's. The guide has approved the gateway as a B4 consumer, with the key `(iss, context.id)` (ADR 0001 OI-15); B4's `shared.course_link` columns are not part of that approval and are still to be agreed |
| Role-URI mapping and precedence; ignoring unlisted roles; refusal when no recognised role remains; refusal under EXT-07 | §5, §8, PRD A5, EXT-07 | `libs/lti`; each tool also refuses what it does not accept |
| Running the §3.2 normalisation of `name`, `email` and `context.title`, once, at the boundary. The rule and its vectors are tested above; no code performs it yet | §3.2 | `libs/lti` (not yet created), to be tested against `contracts/test-vectors/lti-launch-optional-claims.v1.json` |
| Session identity `(iss, sub, context id)`, two-hour idle expiry, course-context isolation | §6, §7, PRD SEC-02 | `libs/lti` and each module's authorisation |
| `name` and `email` never written to logs | §10.1, PRD SEC-06 | Every module's logging; no test yet |
| No raw ID token, nonce, state or key material reaches a module | §10 | `libs/lti` |
| LTI library dependency record: pinned artefact, licences on Python 3.12 (including the LGPL `jwcrypto`), advisory scan and version floors | ADR 0001 Appendix B V1 to V3, PRD C-11, SEC-08 | Stage 1 of ADR 0001, not approved; open item OI-26. Partial evidence only, recorded in ADR 0001 §4.1, §5.2, §5.3, §6.2 and Appendix C. Nothing is installed or pinned; `requirements.txt` does not exist |

### Requirement text changed by this pull request

Wording only. These changes carry no new tests, because no code implements the requirements yet.

| Text | Change | Tests |
|---|---|---|
| PRD A5, rules paragraph | Role URIs not listed in B3 are ignored; a launch is refused only if no recognised role remains | None yet (`libs/lti`) |
| PRD B3 table | Claims split into inspected by the gateway and exposed to modules; `iss` added; session bound to `(iss, sub, context id)`; `shared.course_link` keyed by `iss` plus context id | The structure is covered by the schema tests above; the rest belongs to `libs/lti` |
| PRD EXT-07, FR-X-01, A5 player row | Learner wording is under review (ADR 0001 OI-25); see those PRD rows and the ADR for the current state | None (not implemented) |
| PRD B.0 rule 3 | One sentence added: a consuming module adds its tests when its code that reads the contract exists; before that, the shared contract tests cover the change | Not applicable (process rule) |

## B5 model and speech interface contract (v1), Release 0 foundation

Files: `contracts/model-interface.v1.schema.json`, `contracts/examples/model-interface.v1.*.json`
(flat, one file per case), `libs/contracts/tests/test_model_interface_v1.py`. Guide decisions: `docs/decisions/0001-b5-model-interface-v1.md`.

FR-M-01 ("Shared model interface library (B5.1–B5.3)", R0) and FR-M-02 ("Speech interface library
(B5.4)", R0) are deliberately not in the table above. This work covers the data shapes and two
rules the libraries must follow. It does not implement FR-M-01 or FR-M-02, which still need the
`model.run` call, the providers themselves, one retry, versioned prompts, logging, and
`speech.transcribe`. FR-M-01 and FR-M-02 get their rows in the pull request that completes them.

### Enforced by the JSON Schema and covered by automated tests

Structure only. Test names are in `test_model_interface_v1.py`.

| Rule | PRD | Test(s) |
|---|---|---|
| `result.meta` has provider, model, input and output tokens, `latency_ms`, `cost_estimate`, `prompt_version` | B5.1, B5.3 | `test_missing_required_field_is_rejected`, `test_wrong_type_or_value_is_rejected` |
| `provider` is `local`, `hosted` or `fake` (meta and transcript meta) | B5.2, B5.4 | `test_wrong_type_or_value_is_rejected`, `test_wrong_type_or_value_is_rejected`, `test_examples_cover_every_provider` |
| Token counts and `cost_estimate` are required but may be `null` (not reported) | B5.1, B5.4 | `test_missing_required_field_is_rejected`, `test_valid_variation_is_accepted`, `test_valid_variation_is_accepted`, `test_examples_show_known_and_unknown_usage`, `test_transcript_examples_show_known_and_unknown_cost` |
| Examples follow the cost rule: local reports `0.0`, unknown usage and cost are `null` | B5.1 | `test_examples_follow_the_cost_rule` |
| A transcript has `segments` (start, end, text, words) and `meta`; each word has start, end, word | B5.4 | `test_missing_required_field_is_rejected`, `test_wrong_type_or_value_is_rejected` |
| `transcript.meta` has provider, model, `duration_s`, `latency_ms`, `cost_estimate` | B5.4 | same two tests |
| A document is either a meta record or a transcript, never neither and never both (no discriminator field) | B5 | `test_document_that_is_neither_kind_is_rejected`, `test_document_that_is_both_kinds_is_rejected` |
| `segments: []`, `words: []` and empty segment `text` are valid, and examples show each | B5.4 | `test_valid_variation_is_accepted`, `test_transcript_examples_cover_the_empty_cases` |
| An example shows times after a chunk boundary, counted from the start of the original audio | B5.4 | `test_chunked_example_keeps_times_from_the_start_of_the_audio` |
| Unknown fields are accepted (including the Q38 names and `language`, which are not part of v1) | B.0 rule 2, EXT-02 | `test_valid_variation_is_accepted`, `test_valid_variation_is_accepted` |
| By the guide's decision (15 Nov), not a rule: segments and words may arrive out of time order and a consumer sorts by `start` (PRD B5.4); no rule on times past `duration_s`, and a reader must not fail on one | B5.4, decision 0001 (10, 11) | `test_segments_out_of_time_order_pass_the_schema`, `test_a_segment_past_duration_s_passes_the_schema` |
| A segment's and a word's `end` is not below its `start` (decision 9): **not a schema rule**; the check is in PR #35 and is not merged yet, so today nothing enforces it | B5.4, decision 0001 (5, 9) | `test_segment_ending_before_it_starts_passes_the_schema`, `test_a_word_ending_before_it_starts_passes_the_schema` (record the gap) |
| The schema is valid, and every example validates against the whole schema and its definition | B.0 rule 1 | `test_schema_is_a_valid_draft_2020_12_schema`, `test_example_is_valid_against_the_whole_schema`, `test_example_is_valid_against_its_definition`, `test_every_example_file_is_listed` |

Chosen in the schema rather than stated in the PRD: token counts and `latency_ms` are non-negative
integers; seconds and `cost_estimate` are non-negative numbers; `model`, `prompt_version` and `word`
are non-empty strings; `prompt_version` has no set format.

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
| An `official` run is refused unless the B8.5 status is COMPLETE, a normaliser is approved and every run detail and approval is filled; approvals must be references and the date a real date | B8.5 README, App-C 7 | `test_official_mode_is_refused_today`, `test_official_mode_needs_run_details_and_approvals`, `test_official_approvals_must_look_like_references`, `test_official_run_date_must_be_a_real_iso_date` |
| An `official` run needs at least five lectures, from the B8.5 inventory, with the inventory's reference transcript, a consent entry and review `checked` (peer review of #103) | PRD B8.5, decision 0004 | `test_official_mode_passes_gates_only_with_everything`, `test_official_mode_refuses_fewer_than_five_lectures`, `test_official_mode_refuses_ids_outside_the_inventory`, `test_official_mode_refuses_a_reference_that_is_not_the_inventory_transcript`, `test_official_mode_needs_consent_and_checked_transcripts` |
| B5.4 JSON transcripts are read in order of `start`; an empty hypothesis is all deletions with a warning; an empty reference is refused | PRD B5.4 | `test_out_of_order_segments_are_sorted_by_start`, `test_segments_need_numeric_start_and_string_text`, `test_an_empty_hypothesis_is_all_deletions_with_a_warning`, `test_an_empty_reference_is_still_refused`, `test_cli_shows_the_empty_hypothesis_warning` |
| The report escapes pipe characters and newlines in table cells; the CLI prints a message, not a traceback, when no reference words remain | UI-05 | `test_report_escapes_table_cells`, `test_cli_prints_a_message_not_a_traceback_when_a_normaliser_empties_the_reference` |
| Reports say synthetic or official, and keep target and acceptance PENDING | G-6, App-C 7 | `test_a_valid_synthetic_run_loads_and_reports` |

### Not verified

- Any speech model's accuracy; the synthetic tests use made-up text only.
- That an approval cited in an official run exists (a reviewer checks it).
- Text normalisation, confidence intervals, timing accuracy and speed: not decided, not built.

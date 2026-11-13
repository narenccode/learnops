# Traceability (PRD E4)

| Requirement | Test(s) | Demo step | Bloom level |
|---|---|---|---|
| EXT-09, C-08 – `media_paths` library: B6.1 media path templates and the relative-path rule (B6 has no requirement ID of its own, PRD B.0) | `libs/media_paths/tests/test_paths.py`: defaults `test_course_lesson_path_uses_prd_template`, `test_live_class_path_uses_prd_template`, `test_default_templates_match_prd_b6_1`, `test_default_templates_use_exactly_the_documented_placeholders`, `test_default_templates_are_loaded_checked_templates`, `test_path_numbers_are_zero_padded`; documented placeholders `test_course_lesson_custom_template_with_documented_placeholders`, `test_live_class_custom_template_with_documented_placeholders`, `test_each_course_lesson_placeholder_is_supported`, `test_each_live_class_placeholder_is_supported`, `test_number_placeholders_are_optional`; required placeholders `test_required_placeholders_are_the_guide_decision`, `test_course_lesson_template_without_identifying_placeholder_is_rejected`, `test_live_class_template_without_identifying_placeholder_is_rejected`, `test_missing_placeholder_error_names_every_missing_one`, `test_lessons_differing_only_by_lesson_slug_get_different_folders`; checked once at load `test_template_is_checked_once_when_loaded_not_at_each_call`, `test_checked_template_cannot_be_created_unchecked`, `test_course_lesson_path_rejects_an_unloaded_template`, `test_live_class_path_rejects_an_unloaded_template`, `test_lesson_template_is_not_accepted_for_live_class`; negative templates `test_unknown_placeholder_is_rejected_with_clear_error`, `test_lesson_placeholder_in_live_class_template_is_rejected`, `test_malformed_template_is_rejected`, `test_format_spec_or_conversion_is_rejected`, `test_escaped_literal_braces_are_allowed`, `test_template_producing_unsafe_path_is_rejected_at_load`, `test_unsafe_live_class_template_is_rejected_at_load`, `test_non_string_template_is_rejected`; inputs `test_course_lesson_rejects_invalid_slugs`, `test_live_class_rejects_invalid_slugs_and_cohorts`, `test_cohort_in_slug_form_such_as_a_date_is_accepted`, `test_non_string_slug_is_rejected`, `test_course_lesson_rejects_non_integer_numbers`, `test_course_lesson_rejects_numbers_outside_1_to_99`, `test_course_lesson_accepts_numbers_1_and_99`, `test_live_class_rejects_non_integer_number`, `test_live_class_rejects_number_outside_1_to_99`, `test_live_class_accepts_number_99`. `libs/media_paths/tests/test_validation.py`: `test_valid_slugs_are_accepted`, `test_invalid_slugs_are_rejected`, `test_traversal_and_non_ascii_slugs_are_rejected`, `test_validate_slug_returns_false_for_non_strings`, `test_valid_relative_paths_are_accepted`, `test_invalid_relative_paths_are_rejected`, `test_prd_b6_2_and_other_legitimate_paths_are_accepted`, `test_colon_that_is_not_a_scheme_or_drive_is_accepted`, `test_scheme_or_drive_at_the_start_is_rejected`, `test_unsafe_relative_paths_are_rejected`, `test_control_and_format_characters_are_rejected`, `test_validate_relative_path_returns_false_for_non_strings`, `test_require_slug_returns_valid_value`, `test_require_slug_error_names_the_field`, `test_require_positive_int_returns_valid_value`, `test_require_positive_int_rejects_non_integers`, `test_require_positive_int_rejects_values_below_one`, `test_require_int_in_range_returns_valid_value`, `test_require_int_in_range_rejects_values_outside_the_range`, `test_require_int_in_range_rejects_non_integers`. Not claimed yet: the shared B6.3 vectors (`contracts/test-vectors/relative-path.v1.json`, PR #32) run through `validate_relative_path`; that test follows once PR #32 is merged. The library's rejection of control and format characters, which the B6.3 pattern accepts, is open with the guide | Load the default and a custom template; show that a template without `{lesson_slug}`, an unknown placeholder, a `../` slug, `module_number=100` and `module_number=True` are rejected with a clear message | — |
| EXT-09 – `media_paths` library: B6.4 media signing interface (`none` baseline); `sign()` accepts only relative paths (C-08) | `libs/media_paths/tests/test_signing.py`: `test_none_signer_implements_media_signer_interface`, `test_none_signer_builds_media_url`, `test_none_signer_accepts_custom_ttl`, `test_none_signer_output_has_no_signature_or_expiry`, `test_default_ttl_matches_prd_b6_4`, `test_valid_base_urls_are_joined_with_a_single_slash`, `test_none_signer_removes_trailing_slash_from_base_url`, `test_sign_percent_encodes_path_characters`; negative `test_invalid_base_urls_are_rejected`, `test_base_url_error_does_not_echo_credentials`, `test_non_string_base_url_is_rejected`, `test_sign_rejects_unsafe_relative_paths`, `test_sign_rejects_non_integer_ttl`, `test_sign_rejects_ttl_below_one`; configuration `test_media_signing_none_returns_none_signer`, `test_create_media_signer_reads_os_environ_by_default`, `test_config_error_is_a_value_error`, `test_planned_signing_modes_raise_not_implemented_config_error`, `test_unknown_signing_modes_raise_config_error`, `test_missing_media_signing_raises_config_error`, `test_missing_media_base_url_raises_config_error`, `test_invalid_media_base_url_raises_config_error` | Select the signer with `MEDIA_SIGNING=none` and build a plain media URL; show that `hmac`/`s3` and unknown modes give a configuration error. Only `none` is implemented (enough for the baseline per B6.4) | — |

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

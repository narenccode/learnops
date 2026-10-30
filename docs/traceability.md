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

## B5 model and speech interface contract (v1), Release 0 foundation

Files: `contracts/model-interface.v1.schema.json`, `contracts/examples/model-interface.v1.*.json`
(flat, one file per case), `libs/contracts/tests/test_model_interface_v1.py`, and two contract
guards in `libs/model_interface/` (`config.py`, `transcript.py`) with tests in
`libs/model_interface/tests/`. Guide decisions: `docs/decisions/0001-b5-model-interface-v1.md`.

FR-M-01 ("Shared model interface library (B5.1–B5.3)", R0) and FR-M-02 ("Speech interface library
(B5.4)", R0) are deliberately not in the table above. This work covers the data shapes and two
rules the libraries must follow. It does not implement FR-M-01 or FR-M-02, which still need the
`model.run` call, the providers themselves, one retry, versioned prompts, logging, and
`speech.transcribe`. FR-M-01 and FR-M-02 get their rows in the pull request that completes them.

### Enforced by the JSON Schema and covered by automated tests

Structure only. Test names are in `test_model_interface_v1.py`.

| Rule | PRD | Test(s) |
|---|---|---|
| `result.meta` has provider, model, input and output tokens, `latency_ms`, `cost_estimate`, `prompt_version` | B5.1, B5.3 | `test_meta_missing_required_field_is_rejected`, `test_meta_wrong_type_or_value_is_rejected` |
| `provider` is `local`, `hosted` or `fake` (meta and transcript meta) | B5.2, B5.4 | `test_meta_wrong_type_or_value_is_rejected`, `test_transcript_wrong_type_or_value_is_rejected`, `test_examples_cover_every_provider` |
| Token counts and `cost_estimate` are required but may be `null` (not reported) | B5.1, B5.4 | `test_meta_missing_required_field_is_rejected`, `test_meta_valid_variation_is_accepted`, `test_transcript_valid_variation_is_accepted`, `test_examples_show_known_and_unknown_usage`, `test_transcript_examples_show_known_and_unknown_cost` |
| Examples follow the cost rule: local reports `0.0`, unknown usage and cost are `null` | B5.1 | `test_examples_follow_the_cost_rule` |
| A transcript has `segments` (start, end, text, words) and `meta`; each word has start, end, word | B5.4 | `test_transcript_missing_required_field_is_rejected`, `test_transcript_wrong_type_or_value_is_rejected` |
| `transcript.meta` has provider, model, `duration_s`, `latency_ms`, `cost_estimate` | B5.4 | same two tests |
| A document is either a meta record or a transcript, never neither and never both (no discriminator field) | B5 | `test_document_that_is_neither_kind_is_rejected`, `test_document_that_is_both_kinds_is_rejected` |
| `segments: []`, `words: []` and empty segment `text` are valid, and examples show each | B5.4 | `test_transcript_valid_variation_is_accepted`, `test_transcript_examples_cover_the_empty_cases` |
| An example shows times after a chunk boundary, counted from the start of the original audio | B5.4 | `test_chunked_example_keeps_times_from_the_start_of_the_audio` |
| Unknown fields are accepted (including the Q38 names and `language`, which are not part of v1) | B.0 rule 2, EXT-02 | `test_meta_valid_variation_is_accepted`, `test_transcript_valid_variation_is_accepted` |
| The schema is valid, and every example validates against the whole schema and its definition | B.0 rule 1 | `test_schema_is_a_valid_draft_2020_12_schema`, `test_example_is_valid_against_the_whole_schema`, `test_example_is_valid_against_its_definition`, `test_every_example_file_is_listed` |

Chosen in the schema rather than stated in the PRD: token counts and `latency_ms` are non-negative
integers; seconds and `cost_estimate` are non-negative numbers; `model`, `prompt_version` and `word`
are non-empty strings; `prompt_version` has no set format.

### Enforced by library code and covered by automated tests

JSON Schema cannot express these; `test_segment_ending_before_it_starts_passes_the_schema` shows
the schema alone does not catch the first one.

| Rule | PRD | Code | Test(s) |
|---|---|---|---|
| Every segment's `end` is at least its `start` | B5.4 | `libs/model_interface/transcript.py` | `test_transcript.py`: `test_segment_ending_before_it_starts_is_rejected`, `test_every_bad_segment_is_reported`, `test_end_left_relative_to_its_chunk_is_rejected`, `test_zero_length_segment_is_valid`, `test_every_transcript_example_has_valid_segment_times` |
| `fake` is refused unless `LEARNOPS_ENV=test` and `MODEL_ALLOW_FAKE=true`; the flag is refused in the lab, in production and with `LEARNOPS_ENV` unset; applies to `MODEL_PROVIDER` and `SPEECH_PROVIDER` | B5.2, B5.4 | `libs/model_interface/config.py` | `test_config.py`: `test_fake_is_accepted_in_a_test_run_with_the_flag_on`, `test_fake_is_refused_without_the_test_setting`, `test_the_fake_flag_is_refused_outside_tests`, `test_the_fake_flag_is_refused_when_the_environment_is_unset`, `test_real_providers_are_accepted_everywhere`, `test_unknown_provider_is_refused`, `test_unknown_environment_is_refused`, `test_unclear_flag_value_is_refused` |

### Documented but not automatically enforced

No code checks these yet. The schema's `$comment` lists them too.

| Rule | PRD |
|---|---|
| `result.data` matches the task's `output_schema` | B5.1 |
| Invalid structured output: one retry, then a clear error, never a partial result | B5.2 |
| Model chosen by `MODEL_NAME`; keys from environment variables only | B5.2 |
| Prompts are versioned files in `libs/model_interface/prompts/` | B5.3 |
| Every call logs `meta` to `shared.model_calls`, with no raw learner content | B5.3 |
| Unknown usage and cost are written as `null`, never 0 (the schema accepts both; only the provider code knows which is true) | B5.1 |
| Times count from the start of the original audio after chunking (the schema sees only numbers) | B5.4 |
| A word ends at or after its start; segments are in time order | Not in the PRD; not decided |

## FR-M-01 shared model interface library (skeleton, partial), Release 0 foundation

Files: `libs/model_interface/` (`runner.py`, `registry.py`, `prompts.py`, `prompts/example_echo/v1.md`
(test-only), `providers/`, `call_log.py`, `errors.py`, `messages.py`), tests in
`libs/model_interface/tests/` (`test_run.py`, `test_call_logging.py`, `test_multi_provider.py`,
`test_registry_and_prompts.py`, `test_providers.py`, `test_public_api.py`), and usage notes in
`libs/model_interface/README.md`.
Builds on the B5 contract section above (PR #25) and does not change `config.py` or `transcript.py`.

FR-M-01 ("Shared model interface library (B5.1–B5.3)", R0) is still deliberately not in the table
at the top: this skeleton does not complete it. Missing: the real local transport (the lab
endpoint's protocol, design Q19), the real hosted transport (Q19), and logging `meta` to
`shared.model_calls` (migration tool and shared schema, Q36). FR-M-01 gets its row in the pull
request that completes it.

Of the B5 section's "Documented but not automatically enforced" rows, these are now enforced by
code and tested here: `result.data` matches `output_schema`; one retry then a clear error;
versioned prompt files; unknown usage written as `null` by the local provider. Logging to
`shared.model_calls` is only partly covered: every attempt is recorded (meta only) and `run()`
refuses without a logger outside a test run, but the only logger that exists is in memory.

### Enforced by library code and covered by automated tests

| Rule | PRD | Code | Test(s) |
|---|---|---|---|
| One call `run(task, inputs, output_schema)` returns validated `data` and `meta`, with no provider or logger passed, through one shared provider | B5.1 | `runner.py`, `providers/__init__.py` | `test_run.py`: `test_valid_output_returns_data_and_b5_meta`, `test_the_prd_call_shape_works_with_the_shared_fake_provider`; `test_call_logging.py`: `test_the_shared_provider_is_kept_between_calls`, `test_a_configured_provider_is_used_by_the_prd_call_shape`, `test_a_cached_fake_is_replaced_when_the_setting_changes` |
| Public call shape `import model_interface as model; model.run(task, inputs, output_schema)`; the module is `model_interface.runner` and there is no `model_interface.run` module to import by mistake | B5.1 | `__init__.py`, `runner.py` | `test_public_api.py`: `test_model_run_is_the_runner_function`, `test_model_run_takes_task_inputs_output_schema_first`, `test_from_import_gives_the_function`, `test_runner_module_imports_as_a_module`, `test_there_is_no_model_interface_run_module`, `test_every_exported_name_exists` |
| `task` is a registered task name; names are unique and well formed | B5.1 | `registry.py` | `test_registry_and_prompts.py`: `test_registered_task_can_be_looked_up`, `test_duplicate_task_name_is_refused`, `test_unregistered_task_is_refused`, `test_bad_task_name_is_refused`; `test_run.py`: `test_unregistered_task_is_refused_before_any_call` |
| `output_schema` must be the registered one; task schemas must be valid JSON Schemas and are kept as private copies | B5.1 | `registry.py`, `runner.py` | `test_output_schema_must_be_the_registered_one`, `test_invalid_schema_is_refused`, `test_registered_schema_is_a_private_copy` |
| Inputs are checked against the task's input schema before any provider call | B5.1 | `runner.py` | `test_invalid_inputs_are_refused_before_any_call` |
| Output is validated; on invalid output one retry, then `InvalidOutput`, never a partial result | B5.2 | `runner.py` | `test_invalid_output_is_retried_once`, `test_invalid_output_twice_raises_and_returns_nothing` |
| `meta` is checked against the B5 schema; unknown usage is `null`, local cost is `0.0` | B5.1 | `runner.py`, `providers/local.py` | `test_meta_that_breaks_the_b5_contract_is_refused`, `test_local_meta_reports_unknown_usage_as_null`, `test_local_keeps_unreported_usage_as_none` |
| One provider interface: local, hosted and fake give the same validated `Result`, with valid B5 `meta`, logged through the shared logger; `runner.py` has no provider-specific code | B5.1, B5.2 | `providers/base.py`, `providers/transport.py`, `runner.py` | `test_multi_provider.py`: `test_every_provider_gives_the_same_validated_result_and_logs_it`, `test_a_hosted_failure_is_logged_through_the_shared_logger` |
| Hosted provider behind an injectable transport: no URL assumed; reported cost kept; unreported cost is `None`, never 0; `MODEL_NAME` required and shown in `meta`; transport failures carry no content | B5.1, B5.2 | `providers/hosted.py`, `providers/transport.py` | `test_multi_provider.py`: `test_hosted_passes_the_request_to_its_transport_without_a_url`, `test_hosted_keeps_a_reported_cost`, `test_hosted_cost_not_reported_is_none_never_zero`, `test_local_cost_stays_zero_whatever_the_transport_reports`, `test_hosted_transport_failure_shows_no_content`, `test_hosted_needs_model_name`, `test_model_name_reaches_hosted_meta` |
| No fallback between providers: if the selected provider can't be built or reached, the call fails and no other provider is tried | B5.2 | `providers/__init__.py` | `test_multi_provider.py`: `test_a_failing_local_provider_never_tries_hosted_or_fake`, `test_a_transport_for_the_other_provider_is_never_used`, `test_the_resolver_never_catches_a_selected_provider_failure` |
| An API key comes from the environment only; a provider never holds it; it appears in no `repr()`, error or log record | B5.2, C-06 | `providers/__init__.py`, `providers/hosted.py` | `test_multi_provider.py`: `test_a_missing_key_names_the_variable`, `test_the_key_appears_in_no_repr_error_or_log_record`, `test_the_key_is_not_passed_to_the_transport` |
| Provider chosen by `MODEL_PROVIDER`; `fake` only through the `config.py` guard, against the real process environment; `hosted` refused with a clear error until a transport exists (Q19) | B5.2 | `providers/__init__.py`, `providers/fake.py` | `test_multi_provider.py`: `test_the_resolver_refuses_the_fake_outside_a_test_run_even_with_the_flag`; `test_providers.py`: `test_hosted_is_not_implemented_yet`, `test_fake_is_built_only_in_a_test_run`, `test_fake_cannot_be_built_outside_a_test_run`, `test_fake_needs_model_provider_fake_even_in_a_test_run`, `test_fake_takes_no_environment_argument`; `test_run.py`: `test_default_provider_comes_from_the_guarded_configuration`; `test_call_logging.py`: `test_the_guard_runs_again_on_every_get_provider` |
| Fake provider is deterministic by task and inputs, with failure injection | B5.2 (test use) | `providers/fake.py` | `test_fake_answers_by_task_and_inputs_whatever_the_key_order`, `test_fake_without_a_fixture_says_so`, `test_fake_plays_queued_outputs_in_order_then_repeats_the_last`, `test_fake_failure_injection_raises_once` |
| Local provider: settings from `MODEL_LOCAL_URL` and `MODEL_NAME`; request goes to an injected transport; transport failures become `ProviderUnavailable` without request content | B5.2 | `providers/local.py` | `test_local_needs_its_settings`, `test_local_passes_the_request_to_its_transport`, `test_transport_failure_becomes_provider_unavailable_without_content`, `test_local_without_a_transport_is_not_integrated_yet` |
| Provider failures are raised, not retried and not turned into output | B5.2 | `runner.py` | `test_provider_failure_is_raised_not_retried` |
| Prompts are versioned files `prompts/<task>/v<N>.md` whose `prompt_version` header names their own task and version; the highest version is used unless one is named | B5.3 | `prompts.py` | `test_example_prompt_loads_with_its_version`, `test_highest_version_is_used_unless_one_is_named`, `test_prompt_version_must_agree_with_the_file`, `test_prompt_without_header_or_text_is_refused`, `test_task_without_a_prompt_cannot_be_registered` |
| The test-only example prompt registers nothing in the shared registry | — (repository rule) | `registry.py` | `test_no_task_is_registered_in_the_shared_registry_by_the_library` |
| Call records hold `meta` only, never inputs or output | B5.3 | `call_log.py`, `runner.py` | `test_logger_records_meta_only`, `test_invalid_output_is_retried_once`, `test_failed_attempts_log_no_content` |
| Every attempt is logged, also failed ones; a provider failure and invalid `meta` are recorded with `null` usage and then raised; invalid output keeps the usage the provider reported | B5.1, B5.3 | `runner.py`, `call_log.py` | `test_call_logging.py`: `test_success_is_logged_with_b5_meta`, `test_provider_failure_is_logged_with_null_usage_and_raised`, `test_an_unexpected_provider_exception_is_logged_and_raised`, `test_failure_records_are_valid_b5_meta`, `test_invalid_meta_is_logged_with_null_usage_and_raised`, `test_a_provider_failure_on_the_retry_is_logged_as_attempt_two`, `test_invalid_output_keeps_the_usage_the_provider_reported` |
| Required logging is never skipped: outside `LEARNOPS_ENV=test`, also with it unset, `run()` refuses before any model call when no logger is configured; a test run falls back to an in-memory logger; a logger that fails stops the call from returning | B5.3 | `call_log.py`, `runner.py` | `test_call_logging.py`: `test_run_refuses_without_a_logger_outside_a_test_run`, `test_a_configured_logger_is_used_outside_a_test_run`, `test_a_logger_passed_to_the_call_is_used_outside_a_test_run`, `test_a_test_run_falls_back_to_the_in_memory_logger`, `test_the_in_memory_fallback_does_not_survive_leaving_the_test_run`, `test_a_logger_that_fails_stops_the_call_from_returning` |
| `repr()` never shows inputs, prompt text, model text or result data | B5.3, OPS-04 | `providers/base.py`, `providers/local.py`, `prompts.py`, `runner.py` | `test_call_logging.py`: `test_repr_of_a_request_shows_no_prompt_or_inputs`, `test_repr_of_a_response_shows_no_text`, `test_repr_of_a_transport_reply_shows_no_text`, `test_repr_of_a_result_shows_no_data`, `test_repr_of_a_prompt_shows_no_text` |
| Error messages never carry learner input, model output or transport detail: problems are named by their place in the schema only, and transport failures keep only the exception's class name with the original chain cut | B5.3, OPS-04 | `runner.py`, `providers/local.py`, `messages.py` | `test_run.py`: `test_invalid_output_error_shows_no_model_output`, `test_invalid_output_error_shows_no_raw_text`, `test_invalid_input_error_shows_no_learner_input`, `test_invalid_meta_error_shows_no_output`, `test_invalid_output_twice_raises_and_returns_nothing`; `test_providers.py`: `test_transport_failure_becomes_provider_unavailable_without_content` |

### Not implemented, and therefore not claimed

| Rule | PRD | Waiting for |
|---|---|---|
| Real local endpoint request | B5.2 | Q19 (lab endpoint protocol) |
| Real hosted API call through the provider's official SDK (`HostedProvider` exists; no real `HostedTransport`) | B5.2 | Q19 (provider, SDK, licence), spending-cap key (A15.5) |
| Every call logs `meta` to `shared.model_calls` (PostgreSQL logger). Until it exists, `run()` refuses outside a test run unless a logger is configured | B5.3 | Q36 (migration tool, shared schema) |
| Timeouts, transport retries and the budget guard | — | Design proposals only (grading.md §4.2) |
| Task schemas as Pydantic models | Root `CLAUDE.md` §6 ("Pydantic models for every contract and API payload"); PRD B5.1 allows "JSON Schema / Pydantic model" | OPEN DECISION for the guide: JSON Schema is used meanwhile. Adding Pydantic (planned 2.14.1, grading.md §8) changes `requirements-dev.txt`, owned by Students 1 and 2 and the guide |

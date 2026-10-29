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

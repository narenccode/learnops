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
(flat, one file per case), `libs/contracts/tests/test_model_interface_v1.py`. **Contract work only.**

FR-M-01 ("Shared model interface library (B5.1–B5.3)", R0) and FR-M-02 ("Speech interface library
(B5.4)", R0) are deliberately not in the table above. The tests below check only the data shapes the
two libraries must produce. They do not implement FR-M-01 or FR-M-02, which need
`libs/model_interface` (the `model.run` call, providers, one retry, versioned prompts, logging, and
`speech.transcribe`). That library does not exist yet. FR-M-01 and FR-M-02 get their rows in the
pull request that implements it.

### Enforced by the JSON Schema and covered by automated tests

Structure only. Test names are in `test_model_interface_v1.py`.

| Rule | PRD | Test(s) |
|---|---|---|
| `result.meta` has provider, model, input and output tokens, `latency_ms`, `cost_estimate`, `prompt_version` | B5.1, B5.3 | `test_meta_missing_required_field_is_rejected`, `test_meta_wrong_type_or_value_is_rejected` |
| `provider` is `local` or `hosted` (meta and transcript meta); also `fake` for tests (see below) | B5.2, B5.4 | `test_meta_wrong_type_or_value_is_rejected`, `test_transcript_wrong_type_or_value_is_rejected`, `test_examples_cover_every_provider` |
| Token counts and `cost_estimate` are required but may be `null` ("not known") | B5.1, B5.4 (fields); null: Student 1 proposal | `test_meta_missing_required_field_is_rejected`, `test_meta_valid_variation_is_accepted`, `test_transcript_valid_variation_is_accepted`, `test_examples_show_known_and_unknown_usage`, `test_transcript_examples_show_known_and_unknown_cost` |
| A transcript has `segments` (start, end, text, words) and `meta`; each word has start, end, word | B5.4 | `test_transcript_missing_required_field_is_rejected`, `test_transcript_wrong_type_or_value_is_rejected` |
| `transcript.meta` has provider, model, `duration_s`, `latency_ms`, `cost_estimate` | B5.4 | same two tests |
| A document is either a meta record or a transcript, never neither and never both | B5 | `test_document_that_is_neither_kind_is_rejected`, `test_document_that_is_both_kinds_is_rejected` |
| Silent audio (`segments: []`), a segment without word timings (`words: []`) and a segment with empty `text` are valid, and examples show each | B5.4 (shape); empty cases: Student 4 | `test_transcript_valid_variation_is_accepted`, `test_transcript_examples_cover_the_empty_cases` |
| Optional additions are accepted but not required: `input_hash`, `temperature`, `seed`, `cost_known` (Q38) and a transcript `language` (Student 4 proposal) | B.0 rule 2 | `test_meta_valid_variation_is_accepted`, `test_transcript_valid_variation_is_accepted` |
| Unknown fields are accepted | B.0 rule 2, EXT-02 | `test_meta_valid_variation_is_accepted`, `test_transcript_valid_variation_is_accepted` |
| The schema is valid, and every example validates (all three providers covered) | B.0 rule 1 | `test_schema_is_a_valid_draft_2020_12_schema`, `test_example_is_valid_against_the_whole_schema`, `test_example_is_valid_against_its_definition`, `test_every_example_file_is_listed`, `test_examples_cover_every_provider` |

Enforced and tested, but chosen in the schema rather than stated in the PRD (to be confirmed by the
contract reviewers):
- every field the PRD names is required; only token counts and `cost_estimate` may be `null`;
- token counts and `latency_ms` are non-negative integers;
- seconds and `cost_estimate` are non-negative numbers;
- `model`, `prompt_version` and `word` are non-empty strings; `prompt_version` has no set format;
- empty `segments`, empty `words` and empty segment `text` are allowed (asked for by Student 4, see
  below).

From Student 1's consumer review (Module 1), applied here but **not in the PRD text** and not yet
confirmed by the guide or the other B5 consumer, Module 4 (Student 4; PRD B.0 lists B5 as used by
M1, M3, M4):
- `input_tokens`, `output_tokens` and `cost_estimate` may be `null` when unknown (B5.1 names the
  fields but says nothing about unknown values). `transcript.meta.cost_estimate` follows the same
  rule ("Same rules as B5.2", B5.4).
- `fake` is a third provider value, for tests only. PRD B5.2 and B5.4 name only `local` and
  `hosted`; GETTING-STARTED §6 asks for "a fake provider for tests". If the guide keeps it, PRD B5.2
  needs a matching sentence (B.0 rule 3).

From Student 2's review (example validator compatibility), applied here; not yet confirmed by the
guide:
- examples are flat files `contracts/examples/model-interface.v1.<case>.json`, each valid against
  the whole schema; invalid documents live only in the test file;
- no `additionalProperties: false`, so unknown fields stay accepted;
- **not adopted:** a required `const` discriminator field on each document kind. The PRD names no
  such field for `result.meta` or the transcript, and making one required would add a field every
  producer must write. The two kinds stay apart through `oneOf` and their different required
  fields (tested above). Left as an open proposal.

From Student 4's review (Module 4, speech), applied here; not yet confirmed by the guide:
- `words` stays required and may be empty; `segments` may be empty; segment `text` may be empty.
  Student 4 owns B6, whose B6.2 describes `transcript.en.json` as "Segments with word timings".
- segment and word `start`/`end` are numbers of seconds from the start of the original audio file,
  also when the speech service processes it in chunks (documented in the schema).
- an optional `language` field is a proposal only: accepted as an unknown field, not defined or
  required.

Open, not decided by the schema:
- the unit or currency of `cost_estimate` (the PRD names none);
- keeping `fake` as a provider value (guide);
- a required discriminator field (Student 2 proposal, not adopted);
- defining types for the Q38 fields and for `language` (guide; Q38);
- guide confirmation of all consumer-review changes above.

### Documented but not automatically enforced

No library code exists yet, so nothing in the repository checks these. The schema's `$comment`
lists them too.

| Rule | PRD |
|---|---|
| `result.data` matches the task's `output_schema` | B5.1 |
| Invalid structured output: one retry, then a clear error, never a partial result | B5.2 |
| Provider and model chosen by `MODEL_PROVIDER` and `MODEL_NAME`; keys from environment variables only | B5.2 |
| Prompts are versioned files in `libs/model_interface/prompts/` | B5.3 |
| Every call logs `meta` to `shared.model_calls`, with no raw learner content | B5.3 |
| A segment or word ends at or after its start; segments are in time order | B5.4 |
| Segment and word times count from the start of the original audio file, also when it was processed in chunks (the schema sees only numbers) | Student 4 feedback, pending the guide; B5.4 gives no unit |
| An unknown cost is reported as `null`, never as 0, and is never summed or budgeted as 0 (the schema accepts both 0 and `null`; only the library can tell which is true) | Proposal (Student 1); B5.1 names `cost_estimate` but not unknown values |
| The `fake` provider is used only in tests and is never configured in the lab or production (the schema cannot tell where a call ran) | Proposal (Student 1; GETTING-STARTED §6); not in B5.2, pending the guide |

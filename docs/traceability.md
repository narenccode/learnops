# Traceability (PRD E4)

| Requirement | Test(s) | Demo step | Bloom level |
|---|---|---|---|

## B5 model and speech interface contract (v1), Release 0 foundation

Files: `contracts/model-interface.v1.schema.json`, `contracts/examples/model-interface.v1/`,
`libs/contracts/tests/test_model_interface_v1.py`. **Contract work only.**

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
| `provider` is `local` or `hosted` (meta and transcript meta) | B5.2, B5.4 | `test_meta_wrong_type_or_value_is_rejected`, `test_transcript_wrong_type_or_value_is_rejected` |
| A transcript has `segments` (start, end, text, words) and `meta`; each word has start, end, word | B5.4 | `test_transcript_missing_required_field_is_rejected`, `test_transcript_wrong_type_or_value_is_rejected` |
| `transcript.meta` has provider, model, `duration_s`, `latency_ms`, `cost_estimate` | B5.4 | same two tests |
| A document is either a meta record or a transcript | B5 | `test_document_that_is_neither_kind_is_rejected` |
| Unknown fields are accepted | B.0 rule 2, EXT-02 | `test_meta_valid_variation_is_accepted`, `test_transcript_valid_variation_is_accepted` |
| The schema is valid, and every example validates (both providers covered) | B.0 rule 1 | `test_schema_is_a_valid_draft_2020_12_schema`, `test_example_is_valid_against_the_whole_schema`, `test_example_is_valid_against_its_definition`, `test_every_example_file_is_listed`, `test_examples_cover_both_providers` |

Enforced and tested, but chosen in the schema rather than stated in the PRD (to be confirmed by the
contract reviewers):
- token counts and `latency_ms` are non-negative integers;
- seconds and `cost_estimate` are non-negative numbers;
- `cost_estimate` is never null;
- `model`, `prompt_version` and `word` are non-empty strings;
- every field the PRD names is required;
- `fake` is not a provider value;
- empty `segments`, empty `words` and empty segment `text` are allowed.

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

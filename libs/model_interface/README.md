# `libs/model_interface`: shared model interface (B5)

Every AI call in LearnOps goes through this library (root `CLAUDE.md` rule 6, PRD C-10). No module
calls a provider SDK directly.

**Status: partial FR-M-01 skeleton.** It is safe to build and test against with the fake provider.
It cannot call a real model yet. See [Not implemented](#not-implemented). Speech (FR-M-02) is not
built.

Contract: `contracts/model-interface.v1.schema.json`. Guide's decisions:
`docs/decisions/0001-b5-model-interface-v1.md`.

## Calling it

```python
import model_interface as model

spec = model.register_task("my_task", input_schema, output_schema)  # once, at import
result = model.run("my_task", {"text": "..."}, spec.output_schema)

result.data  # validated against the output schema
result.meta  # provider, model, input/output tokens, latency_ms, cost_estimate, prompt_version
```

`run()` does this, in order:

1. Refuses an unregistered task, or an `output_schema` that is not the registered one.
2. Checks the inputs against the input schema. Nothing is sent if they are invalid.
3. Finds the provider and the call logger. With no logger outside a test run, it refuses.
4. Calls the provider, and checks `meta` against the B5 schema.
5. Parses and checks the output. On invalid output it retries **once**, then raises
   `InvalidOutput`. Partial or invalid output is never returned.

A provider failure is not retried. Every error derives from `ModelError`, and error messages never
contain inputs, prompts or model output.

## Adding a task

1. Add a prompt file `prompts/<task>/v1.md`:

   ```text
   ---
   prompt_version: <task>/v1
   ---
   The prompt text.
   ```

   The header must name the file's own folder and version. A published version is never edited;
   a change is a new `v2.md`. The highest version is used.
2. Call `register_task(name, input_schema, output_schema)` once when your module is imported.
   Task names are unique across the repository: lowercase letters, digits and underscores.
   Pass `prompt_dir=` if your module keeps its own prompt folder.

Schemas are JSON Schemas (Draft 2020-12). Root `CLAUDE.md` §6 asks for Pydantic and PRD B5.1 allows
either; this is an open decision for the guide. `prompts/example_echo/` is test-only.

## Testing your module

The fake provider calls no model. It works only with both of these set; anything else refuses,
including `LEARNOPS_ENV` unset:

```bash
LEARNOPS_ENV=test MODEL_ALLOW_FAKE=true MODEL_PROVIDER=fake
```

```python
from model_interface import ProviderUnavailable, get_call_logger, get_provider, run

fake = get_provider()  # one shared fake, so responses set here reach run()
fake.add_response("my_task", {"text": "hi"}, {"answer": "ok"})
fake.add_response("my_task", {"text": "bad"}, "not json", {"answer": "ok"})  # played in order
fake.fail_next(ProviderUnavailable("down"))  # the next call raises this

run("my_task", {"text": "hi"}, spec.output_schema)
get_call_logger().records  # the in-memory log of this test run
```

Reset between tests with `reset_provider()` (`model_interface.providers`) and
`reset_call_logger()` (`model_interface.call_log`).

## Call logging

PRD B5.3: every call logs `meta`, with no raw learner content.

- **One record per attempt, also failed ones:** `ok`, `invalid_output`, `provider_error` or
  `invalid_meta`. A record holds only the task, attempt, outcome and `meta`.
- **Failed attempts have null usage:** `input_tokens`, `output_tokens` and `cost_estimate` are `null`
  because they are not known. They are never written as 0. Invalid output keeps the usage the
  provider reported, because the model did answer.
- **Logging is never skipped.** `run()` uses the logger set with `configure_call_logger()`, or one
  passed as `logger=`. In a test run with neither, it uses an in-memory logger. **Anywhere else,
  including with `LEARNOPS_ENV` unset, it raises `CallLoggerMissing` before any model call.**
- **If the logger itself fails,** that error is raised, so a call that could not be logged never
  returns a result.

`InMemoryCallLogger` is for tests. It is not `shared.model_calls`, and it keeps records in memory,
so do not configure it in a service to get past `CallLoggerMissing`.

## Configuration

| Variable | Meaning |
|---|---|
| `LEARNOPS_ENV` | `test`, `lab` or `production`. Unset counts as "not test". |
| `MODEL_PROVIDER` | `local`, `hosted`, or `fake` in test runs only |
| `MODEL_ALLOW_FAKE` | `true` only with `LEARNOPS_ENV=test`; anywhere else the service refuses to start |
| `MODEL_NAME`, `MODEL_LOCAL_URL` | Local provider settings |

No key or token is ever stored in the repository.

## Not implemented

| Item | Waiting for |
|---|---|
| Real request to the lab endpoint. `LocalProvider` needs an injected `LocalTransport`; none exists for the real endpoint. | Q19 (endpoint protocol) |
| Hosted provider. `MODEL_PROVIDER=hosted` raises `ProviderUnavailable`. | Q19 (provider, SDK, licence), spending-cap key |
| PostgreSQL logger for `shared.model_calls`. **Until it exists, no lab or production service can make a logged model call.** | Q36 (migration tool, shared schema) |
| Pydantic models for task schemas | Guide's decision |
| Timeouts from the environment, transport retries, budget guard | Design proposals only (`docs/design/grading.md` §4.2) |
| Speech interface `speech.transcribe` | FR-M-02 (separate work) |

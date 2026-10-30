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

## Architecture

Application code calls one function and names no provider:

```
model.run(task, inputs, output_schema)        runner.py: no provider-specific code
  |  validates inputs, output and metadata; retries invalid output once; logs every attempt
  v
Provider protocol: name, model, complete()    providers/base.py
  |-- FakeProvider                            providers/fake.py (test runs only)
  `-- TransportProvider                       providers/transport.py (shared call and error handling)
        |-- LocalProvider  -> LocalTransport  providers/local.py
        `-- HostedProvider -> HostedTransport providers/hosted.py
```

| Common part | Where | What it does |
|---|---|---|
| Invocation | `Provider.complete(request)` | The one method every provider has |
| Request | `ProviderRequest` | Task, prompt, `prompt_version`, inputs, output schema |
| Response | `ProviderResponse` | Raw text, input and output tokens, `cost_estimate`. Usage is `None` when not reported |
| Errors | `ProviderUnavailable` | Any transport failure or malformed reply, with only the exception's class name |
| Metadata and validation | `run()` | The same B5 `meta` and the same output check for every provider |
| Logging | `CallLogger` | One record per attempt, whichever provider ran |

| Provider | Responsible for | State |
|---|---|---|
| `LocalProvider` | Passing the request and `MODEL_LOCAL_URL` to its transport. Cost is `0.0` | Mock-tested. **Real endpoint pending** |
| `HostedProvider` | Passing the request to its transport. Cost is what the transport reports, `None` when it reports nothing, never 0 | Mock-tested. **Real API pending** |
| `FakeProvider` | Deterministic answers and failures for tests | Test runs only |

**Fake restrictions.** It needs `LEARNOPS_ENV=test` and `MODEL_ALLOW_FAKE=true`, and refuses to
initialise in the lab, in production or with `LEARNOPS_ENV` unset. Any object calling itself `fake`
is refused the same way. It is never a fallback.

## Choosing a provider

`MODEL_PROVIDER` picks the provider; `MODEL_NAME` names the model for local and hosted. The resolver
is `create_provider()`.

**Application services must use the configured path.** Build once at start, then only call `run()`:

```python
model.configure_provider(model.create_provider(local_transport=transport))  # at service start
model.configure_call_logger(call_logger)                                    # at service start
result = model.run("my_task", inputs, spec.output_schema)                   # everywhere else
```

Changing from local to hosted is then a setting and a restart, with no application change.

**Injection is for test runs.** With `LEARNOPS_ENV=test`, `run()` accepts any valid `provider=` and
`logger=`. Anywhere else, including with `LEARNOPS_ENV` unset, it refuses before any model call
unless they are the configured ones. So a service set up for local can't silently run on hosted,
or the reverse, and no call can miss the shared log.

- **Unknown names are refused.** `MODEL_PROVIDER` must be `local`, `hosted` or `fake`.
- **Invalid providers are refused.** `configure_provider()` and `run()` check for a callable
  `complete()`, a supported name and a model. A matching name alone isn't enough.
- **No silent replacement.** A provider that differs from `MODEL_PROVIDER` is refused, and so is a
  second provider. If the setting changes while a service runs, `get_provider()` raises instead of
  rebuilding. In tests, call `reset_provider()` between cases.
- **No fallback, ever.** If the selected provider can't be built or reached, the call fails. Local
  never falls back to hosted or fake, and nothing else is tried.
- **Credentials.** A provider never holds one, so it can't reach a `repr()`, a log record or an
  error. Mock transports need none, so no key is required to build `HostedProvider`. **The
  requirement stays for the real thing:** a real hosted transport must take its key from the
  environment only (PRD B5.2) and refuse to start without one. How it does so is pending Q19.

## Real server integration: PENDING

Nothing here has talked to a real server. The lab isn't ready, so `local` and `hosted` are tested
with mock transports only (`tests/mock_transport.py`). That proves the interface, not the servers.

When the lab endpoint and the Q19 answers exist, add a class with the `complete()` of
`LocalTransport` or `HostedTransport` that returns a `TransportReply` and raises on failure, then
pass it to `create_provider()` at service start. `run()` and application code don't change. A hosted
transport must use the provider's official SDK (PRD B5.2), and needs a licence check and the spending
cap (PRD A15.5) settled first.

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
- **Logging is never skipped.** `run()` uses the logger set with `configure_call_logger()`. In a
  test run with none, it uses an in-memory logger, and a test can pass its own as `logger=`.
  **Anywhere else, including with `LEARNOPS_ENV` unset, it raises `CallLoggerMissing` before any
  model call, and a `logger=` that isn't the configured one is refused.**
- **If the logger itself fails,** that error is raised, so a call that could not be logged never
  returns a result.

`InMemoryCallLogger` is for test runs only, and `configure_call_logger()` refuses it anywhere else:
its records never reach `shared.model_calls`.

## Configuration

| Variable | Meaning |
|---|---|
| `LEARNOPS_ENV` | `test`, `lab` or `production`. Unset counts as "not test". |
| `MODEL_PROVIDER` | `local`, `hosted`, or `fake` in test runs only |
| `MODEL_ALLOW_FAKE` | `true` only with `LEARNOPS_ENV=test`; anywhere else the service refuses to start |
| `MODEL_NAME` | The model, for local and hosted. The fake keeps its fixed `fake-model` name. |
| `MODEL_LOCAL_URL` | Local provider endpoint |
| `MODEL_HOSTED_API_KEY` | Reserved for the real hosted transport (Q19). Nothing reads it yet. |

No key or token is ever stored in the repository.

## Not implemented

| Item | Waiting for |
|---|---|
| Real request to the lab endpoint. `LocalProvider` needs an injected `LocalTransport`; none exists for the real endpoint. | Q19 (endpoint protocol) |
| Real hosted API call. `HostedProvider` needs an injected `HostedTransport`; none exists, so `MODEL_PROVIDER=hosted` raises `ProviderUnavailable`. | Q19 (provider, SDK, licence), spending-cap key |
| PostgreSQL logger for `shared.model_calls`. **Until it exists, no lab or production service can make a logged model call.** | Q36 (migration tool, shared schema) |
| Pydantic models for task schemas | Guide's decision |
| Timeouts from the environment, transport retries, budget guard | Design proposals only (`docs/design/grading.md` §4.2) |
| Speech interface `speech.transcribe` | FR-M-02 (separate work) |

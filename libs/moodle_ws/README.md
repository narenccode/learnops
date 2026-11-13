# `libs/moodle_ws`: shared Moodle web-services client (B4)

Every Moodle web-services call in LearnOps goes through this library (PRD B4, C-02). No module calls
Moodle directly.

**Status: Release 0 skeleton.** It enforces the allow-list and the draft rule, and keeps tokens out of
logs and errors. **It cannot call a real Moodle yet.** See [Not implemented](#not-implemented).

Contract: `contracts/moodle-ws.v1.md`, with the allow-list in `contracts/moodle-ws.v1.schema.json` and
`contracts/examples/moodle-ws.v1.functions.json`. Nothing in it is verified on a Moodle site yet.

## Calling it

```python
from moodle_ws import create_client

client = create_client("moodle45", transport)
answer = client.call("mod_assign_get_assignments", params)
```

`create_client()` raises `NotSupported` without a transport, because no real one exists. Tests pass
their own. `call()` returns the transport's answer unchanged.

## What it refuses, before anything is sent

- **Any function outside the allow-list.** The list is read from the contract, and matching is exact.
- **A grade write that breaks the draft rule** (B4 §3). `mod_assign_save_grade` must send
  `workflowstate` as `readyforrelease`. Any other value, or none, is refused. On that function, a key
  or value that is exactly `released`, at any depth, is also refused. `mod_assign_set_user_flags` is
  no longer in the B4 allow-list (guide's findings, PR #64), so it is refused as any other unlisted
  function. This needs no parameter names, which B4 does not list yet. A sentence containing the word,
  such as feedback text, is allowed.
- **Parameters that are not plain data**, on every function. `params` must be a mapping of text,
  numbers, booleans, `None`, lists, tuples, sets and dicts, with text or integer keys, at most 32 levels
  deep. `bytes`, `bytearray`, generators, subclasses and other objects raise `InvalidParameters`. The
  transport receives a private copy, so it cannot change the caller's data.

Parameter names are not checked. An empty `parameters` list in the contract means "not yet determined"
(B4 §2a), not "no parameters".

## Configuration

| Variable | Meaning |
|---|---|
| `MOODLE45_URL`, `MOODLE53_URL` | Site address |
| `MOODLE45_WS_TOKEN`, `MOODLE53_WS_TOKEN` | Service-account token for that site. Environment only |

A missing value, or the `CHANGE_ME` placeholder from `.env.example`, raises `MoodleConfigError`. The
error names the variable, never the value.

`SiteSettings` makes the same checks when built by hand. The version must match the site, and the URL
must be `http` or `https` with a host and no credentials, query, fragment or whitespace. `repr()` never
shows the URL.

## Tokens and logs

- `Token` shows only `***` in `repr()`, `str()` and format strings. Only a transport calls `reveal()`.
- `redact(text, tokens)` removes token values from text, as written and percent-encoded.
- `sanitize(text, tokens)` also cuts every URL to scheme and host.
- `safe_url(url)` keeps only scheme and host. Log this, never a request URL.
- `sanitize_value(value, tokens)` does the same through dicts, lists, tuples, sets and frozensets.
  Numbers, booleans and `None` pass. Other objects, `bytes`, and anything deeper than 32 levels become
  `***`.
- `RedactingFilter(tokens)` sanitizes the formatted message, its arguments, exception text, stack text
  and `extra` fields. If a record cannot be cleaned, its content is dropped and a fixed message is
  logged, so logging never raises. **It is not attached automatically.** Each service must attach it to
  each log handler, because a filter on a logger does not cover its child loggers.
- `call()` keeps the error class from a transport but replaces its text with a fixed message, and
  raises it outside the `except` block, so the original is not kept as `__cause__` or `__context__`.
  `raise ... from None` would only hide it.
- Only the token as written and percent-encoded is matched. Other encodings are not, because no
  transport requires one yet. Check this when a real transport is written.

## Errors

All derive from `MoodleError`, with a `code` and a `retryable` flag.

| Class | `code` | Retry helps? |
|---|---|---|
| `MoodleUnreachable` | `moodle_unreachable` | yes |
| `TokenInvalid` | `token_invalid` | no |
| `PermissionDenied` | `permission_denied` | no |
| `UnexpectedResponse` | `unexpected_response` | no |
| `NotSupported` | `not_supported` | no |
| `FunctionNotAllowed` | `function_not_allowed` | no |
| `WorkflowStateNotAllowed` | `workflow_state_not_allowed` | no |
| `InvalidParameters` | `invalid_parameters` | no |
| `MoodleConfigError` | `moodle_config_error` | no |

The first five are from `docs/design/grading.md` §4.1. All are library documentation, not contract
text (guide on Q37, PR #27). `call()` turns an `OSError` from a transport into `MoodleUnreachable`, and
any other exception into `UnexpectedResponse`.

## Tests

```text
pytest -q libs/moodle_ws
```

They use a scripted fake transport with no Moodle-shaped data, and opening a socket fails the test.
This shows the guards work. It shows nothing about Moodle.

## Not implemented

Each of these waits for the lab checks in `contracts/moodle-ws.v1.md` §5:

- A real transport: the endpoint, how the token is sent, and the response format.
- Mapping Moodle's error answers to these classes.
- Parameter names, apart from `workflowstate`. The parameter for feedback comments is unknown.
- Normalized models (`docs/design/grading.md` §4.1). Until they exist, `call()` returns data as is.
- The file download, and the capability list.
- A Fake Moodle built from recordings (design Q53).

No function here has been called against a real Moodle.

## Undo

This library has no CLI and stores nothing, so it has nothing to undo.

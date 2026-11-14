# `libs/moodle_ws`: shared Moodle web-services client (B4)

Every Moodle web-services call in LearnOps goes through this library (PRD B4, C-02). No module calls
Moodle directly.

**Status: Release 0 skeleton, built in steps.** This part adds the error family, the user-facing
messages, the `Token` type and the site settings. Redaction, the allow-list and the client follow in
later pull requests. **It cannot call a real Moodle.**

Contract: `contracts/moodle-ws.v1.md`, with the allow-list in `contracts/moodle-ws.v1.schema.json` and
`contracts/examples/moodle-ws.v1.functions.json`. Nothing in it is verified on a Moodle site yet.

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
text (guide on Q37, PR #27).

## Tests

```text
pytest -q libs/moodle_ws
```

Opening a socket fails the test, so no test can reach a network. This shows the guards work. It
shows nothing about Moodle.

## Undo

This library has no CLI and stores nothing, so it has nothing to undo.

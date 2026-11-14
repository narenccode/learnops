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
  function, even if an allow-list file still lists it. A sentence containing the word, such as
  feedback text, is allowed.
- **A grade write without an explicit attempt or a plain grade** (B4 R2, R9). `attemptnumber` must be
  a whole number from 0, never `-1`; `grade` must be a plain non-negative number (`84.5` or
  `"84.5"`; not `True`, `"1e2"` or `"NaN"`). Otherwise `GradeWriteNotAllowed`.
- **Parameters that are not plain data**, on every function. `params` must be a mapping of text,
  numbers, booleans, `None`, lists, tuples, sets and dicts, with text or integer keys, at most 32 levels
  deep. `bytes`, `bytearray`, generators, subclasses and other objects raise `InvalidParameters`. The
  transport receives a private copy, so it cannot change the caller's data.
- **Every direct grade write.** `call("mod_assign_save_grade", ...)` runs the guards above and then
  raises `GradeWriteNotAllowed`. A grade write is sent only through a `WriteReceipt`: sealed,
  single-use, bound to one client, holding its own copy of the checked parameters, with the guards
  above run again on that path. Only the guarded write helper may issue one, after the checks
  `call()` cannot run alone (maximum grade, locked state, marking workflow) and with a read-back.
  **That helper is added in a later pull request; until then no grade write can be sent at all.**
  This stops accidental bypass; it is not a boundary against code that imports private names, and a
  test fails if any module outside this library uses them.

Apart from `workflowstate`, `attemptnumber` and `grade` on `mod_assign_save_grade`, parameter names are
not checked. An empty `parameters` list in the contract means "not yet determined"
(B4 §2a), not "no parameters".

## Outcomes of a draft-grade write (B4 §3a, §3b)

`moodle_ws.grade_write` holds the outcome values and the pure checks the guarded write helper uses.
Nothing in it contacts Moodle; the helper itself is added in a later pull request. Only `VERIFIED` is
success (R10).

| Outcome | Meaning |
|---|---|
| `VERIFIED` | Written and read back: state `readyforrelease`, and the stored grade equals the grade sent |
| `NOT_VERIFIED` | Written, or maybe written, and not confirmed (R8, R11) |
| `NEEDS_MENTOR_CONFIRMATION` | The write's answer was lost but the read-back matches: not success until the mentor confirms (proposed) |
| `REFUSED_OUT_OF_RANGE` | Grade below 0 or above the maximum; nothing sent (R9) |
| `REFUSED_LOCKED` | State already `readyforrelease` or `released`; nothing sent (R3) |
| `REFUSED_WORKFLOW_OFF` | State `graded` or `notgraded`: marking workflow is off; nothing sent (proposed) |
| `REFUSED_STATE_UNKNOWN` | State missing, unreadable or not a known value; nothing sent (proposed) |
| `ACCESS_DENIED` | The service account may not see or grade this submission (R10) |
| `NO_SUBMISSION`, `NO_GRADE`, `SKIPPED_SUSPENDED` | Decided by the caller with `result_for()` (R5, R10) |

- `stored_grade_matches()` applies B4 §3b to a `mod_assign_get_grades` answer: exactly one entry for
  the assignment, exactly one row for the learner, the same explicit attempt (R2), and a stored grade
  that parses and equals the grade sent as an exact number (R9). Any warning fails it: stricter than
  §3b, because a warning's link to an assignment is not verified.
- `grading_status()` reads `lastattempt.gradingstatus`; it is `None` when Moodle leaves it out (R6).
- A draft is written only over an unlocked marking-workflow state: `notmarked`, `inmarking`,
  `readyforreview` or `inreview`. Matching is exact. These names come from the Moodle source (B4 §7)
  and are not lab-verified (lab check 4).

### Proposed decisions, fail closed, for the guide to confirm

The guide's decisions (R1 to R11) do not settle these. Each takes the safest choice and changes only
by the guide's decision, recorded in the contract (B4 §6):

| Case | Behaviour | Why |
|---|---|---|
| Marking workflow off (`graded` / `notgraded`) | `REFUSED_WORKFLOW_OFF`, nothing sent | The grade could reach the gradebook and the learner at once, against the PRD B4 draft rule. Lab check 4 is open |
| State missing or unknown before the write | `REFUSED_STATE_UNKNOWN`, nothing sent | LearnOps cannot show the grade is not locked (R3) |
| Answer lost, read-back matches | `NEEDS_MENTOR_CONFIRMATION`, not success | R11 says the mentor decides |
| Any warning in the `mod_assign_get_grades` answer | `NOT_VERIFIED` | Stricter than §3b |

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
| `GradeWriteNotAllowed` | `grade_write_not_allowed` | no |
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
- Parameter names, apart from `workflowstate`, `attemptnumber` and `grade`. The parameter for feedback
  comments is unknown.
- Normalized models (`docs/design/grading.md` §4.1). Until they exist, `call()` returns data as is.
- The file download, and the capability list.
- A Fake Moodle built from recordings (design Q53).

No function here has been called against a real Moodle.

## Undo

This library has no CLI and stores nothing, so it has nothing to undo.

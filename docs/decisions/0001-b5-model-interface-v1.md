# 0001. B5 model and speech interface v1: open questions answered

**Date:** 2026-10-29
**Status:** Decided by the guide (answers to the B5 review questions); this PR still needs the guide's review
**Contract:** B5 (`contracts/model-interface.v1.schema.json`), owner Student 3
**Requirements:** FR-M-01, FR-M-02 (Release 0)

## Context

The consumer reviews of B5 (Students 1, 2 and 4) left questions the PRD did not answer: the unit of
`cost_estimate`, how to report unknown usage, whether `fake` is a provider, transcript time rules,
a discriminator field, and the optional fields proposed in `docs/design/grading.md` (Q38). PRD B.0
rule 3 says the schema, examples, PRD text and tests change together, so PRD B5 changes in the
same pull request.

## Decisions and reasons

| # | Decision | Reason |
|---|---|---|
| 1 | `input_tokens`, `output_tokens` and `cost_estimate` may be `null` when the provider does not report them. Unknown is never written as 0. | A 0 that means "unknown" would make budgets and the cost comparison (FR-M-03) wrong without anyone noticing. |
| 2 | `cost_estimate` is a number in US dollars. A local model with no billed cost reports `0.0`; unknown cost is `null`. `latency_ms` and the token counts are non-negative integers, chosen in the schema and not by the PRD: a provider rounds to whole milliseconds. | One currency keeps costs comparable and summable; the zero/null split keeps "free" apart from "unknown". |
| 3 | `fake`, `local` and `hosted` stay distinct provider values. The service refuses `fake` unless an explicit test-only setting is on, and that setting cannot be on in the lab or production. | Tests need a provider that calls no model, but a fake result must never look like a real draft to a mentor. |
| 4 | `segments: []`, empty segment `text` and `words: []` are valid. | Silent audio and providers without word timings are normal, not errors. |
| 5 | All times are seconds from the start of the original audio, also with chunked processing. Every segment's `end` is at least its `start`. | Consumers (Module 4 slide index and summaries) must not need to know how the audio was split. |
| 6 | No discriminator field; keep the two-shape `oneOf`. | The PRD names no such field; adding a required one would make every producer write a field the PRD does not define. |
| 7 | Keep flat example names, for example `contracts/examples/model-interface.v1.meta-local.json`. | The layout Student 2 asked for, for the shared example validator (`libs/contracts/validate_examples.py`, in PR #68, not merged yet). |
| 8 | `input_hash`, `temperature`, `seed` and `cost_known` are not part of v1. | Not needed for v1; they can be added later as optional fields (B.0 rule 2). |
| 9 | (15 Nov) Every word's `end` is at least its `start`, the same rule as a segment. The code rule in PR #35 enforces it, with a test. | A word that ends before it starts is as wrong as a segment that does, and consumers use word times for captions. |
| 10 | (15 Nov) Time order is not guaranteed. The contract says segments and words may arrive out of order and a consumer sorts by `start` (one sentence in PRD B5.4). | Say in the contract when order is not guaranteed, so every consumer sorts instead of assuming. |
| 11 | (15 Nov) No rule on times past `duration_s`, in PR #35 or in the contract. A reader must not fail on such a time and may clamp it for display. A tighter rule later is a new decision, not v1. | A speech service can report a final word a little past the audio end. |

## How it is applied

- Schema descriptions and PRD B5.1, B5.2 and B5.4 state decisions 1 to 5.
- JSON Schema cannot compare two fields, so `end >= start` (segments, and words by decision 9) is
  not a schema rule. `libs/model_interface/transcript.py` in PR #35 (not merged) will check it,
  with a test: **today nothing enforces it.**
- Decision 3 will be enforced by `libs/model_interface/config.py` in PR #35 (not merged): **today
  nothing enforces it.** The fake provider will be accepted only with `LEARNOPS_ENV=test` and
  `MODEL_ALLOW_FAKE=true`; with the flag on and any other `LEARNOPS_ENV` (including unset), the
  service will refuse to start. Both variables are added to `.env.example` in PR #35.
- Decisions 10 and 11 are deliberately not enforced: no rule on time order (a consumer sorts by
  `start`) and no rule on times past `duration_s`. The schema accepts both, and tests record that.

# G-6 caption WER report: TEMPLATE

Copy this file for each run. Delete the instruction lines. Never paste transcript text, audio or
links to recordings. A run is either **A. synthetic software test** or **B. official model
evaluation**. Use one section only and delete the other.

## A. Synthetic software test (tests the tool; NOT G-6 evidence)

- Date / operator:
- Inputs: made-up text only (state where it came from)
- Tool version (commit):
- Result: pass / fail of `pytest libs/speech_eval`
- Statement to keep: "This is not a speech-model evaluation and says nothing about any model."

## B. Official model evaluation

**Overall status: PENDING** (change only when every item in section C is closed)

| Field | Value |
|---|---|
| Date / operator | PENDING |
| Engine, model, version, compute type | PENDING (guide confirmation, ADR 0002) |
| Decoding settings | PENDING |
| Hardware | PENDING |
| Audio sent to (location, retention) | PENDING (data-map question 4) |
| B8.5 dataset status and commit | PENDING |
| Normalisation rules (decision reference) | PENDING |
| Evaluation method (decision reference) | PENDING |
| Run description + report produced by `speech_eval` (mode `official`) | PENDING |

| Lecture | Ref words | Hyp words | S | D | I | WER |
|---|---|---|---|---|---|---|
| PENDING | | | | | | |

- Pooled WER: PENDING
- WER target (App-C 7): PENDING (set by the project after the first baseline run)
- Result against the target (PRD §C4.7): PENDING
- Limits to state: about five lectures, one speaker group, interval not computed unless approved.

## C. Blockers and approvals (as of preparation)

| # | Item | Owner | State |
|---|---|---|---|
| 1 | B8.5 set COMPLETE: recordings, consent lines, reference transcripts checked by Harshitha | Student 4, Harshitha | PENDING |
| 2 | Approval reference for the temporary 1800 s exception in decision 0004 | Guide | PENDING |
| 3 | Transcript typing and WER normalisation rules | Guide | Not decided |
| 4 | ADR 0002 (T8 speech options) approved; lab endpoint model, engine, version, word timestamps | Guide (T8 session) | PROPOSED, not approved |
| 5 | May the lab or any endpoint receive B8.5 audio? | Guide | Not decided |
| 6 | Whether a self-hosted engine may be run for the evaluation (C-12) | Guide | Not decided |
| 7 | Speech interface (B5.4) merged, to produce hypotheses | Student 3 | Not in `main` |
| 8 | WER target for G-6 | Guide / project | Not set; follows the first baseline run |
| 9 | Official evaluation method (confidence interval, term list, sensitivity check) | Guide | Proposed in ADR 0002 only |
| 10 | T9 identity: no file defines "T9" | Owner | To confirm |

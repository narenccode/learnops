# G-6 caption WER: evaluation procedure (preparation)

**Status: PENDING.** No official G-6 evaluation has been run. Nothing in this file is a result, a
target, a provider choice or an approval.

Requirements: PRD G-6, §C4.7 (third acceptance box), App-C 7, B8.5, FR-V-04, C-10.
Tool: `libs/speech_eval/` (software only; no provider is called, no model is run).

## 1. What the documents require

| Item | Source | State |
|---|---|---|
| Caption word error rate on Indian-English lectures (B8.5), "measured and reported; target fixed in Release 0" | PRD §A (G-6) | Target **not set** |
| "Caption word error rate measured on B8.5 and reported against the Release 0 target" | PRD §C4.7 | **PENDING** |
| "Caption word-error-rate target (G-6) from a first baseline run", result recorded in `docs/decisions/` | PRD App-C 7 | **PENDING** |
| Data: at least five Indian-English lectures with reference transcripts, consent or licence | PRD §B8.5, decision 0004 | Set is **COMPLETE** under the written criteria (five lectures, 2380 s, `checked` transcripts, four written consent lines; durations, hashes and file names supplied by the owner and not re-verified). The G-6 method and normalisation are not approved yet |
| Transcription only through the speech interface (B5.4) | PRD C-10, `CLAUDE.md` rule 6 | Interface not in `main` yet |
| Transcript typing rules (case, punctuation, fillers, numbers) | B8.5 README | **Not fixed**: decided with the first baseline run |
| WER method, normalisation, pooled WER, confidence interval | T8 ADR 0002 section 7 | **Proposed only**; ADR is PROPOSED, pending guide confirmation |

"T9" is not defined by that ID in any file in the repository; it is taken here to mean the G-6 /
App-C 7 baseline work described above. The owner should confirm.

## 2. Inputs the official run needs (all outside this PR)

1. A COMPLETE B8.5 set (the `**Status:**` line in `testdata/b8-5-lecture-videos/README.md`):
   recordings kept in the lab, reference transcripts checked by Harshitha, consent lines written.
2. The guide's approved evaluation method and text normalisation rules (a decision record).
3. A guide-confirmed speech engine and model (ADR 0002 approved, or the lab endpoint described).
4. Permission to send the B8.5 audio to that engine (data-map question 4; consent says "video
   stays in the lab").
5. Hypothesis transcripts produced through the speech interface, one per lecture, plus the run
   details: engine, model, engine version, hardware, decoding settings, date, operator.
6. After the run, the guide fixes the target (App-C 7); only then can a result be judged.

## 3. Procedure

1. Check the inputs: `python -m speech_eval --manifest run.json --check` (run from `libs/`, or put
   `libs` on `PYTHONPATH`).
2. Practise on made-up text with `"mode": "synthetic-test"`. This tests the tool only.
3. For the real run, set `"mode": "official"` and fill `run` and `approvals` (each approval is a
   reference to the decision or comment that grants it: `#NNN`, a `docs/decisions/NNNN-name.md`
   path or a GitHub issue or pull request address; `run.date` is a real YYYY-MM-DD date). The tool
   refuses unless the dataset status is COMPLETE, a normaliser is approved, every field is filled
   and not PENDING, and the run uses **at least five lectures that are in the B8.5 inventory**,
   each with the reference transcript the inventory lists, a consent entry and transcript review
   `checked`. The temporary exceptions in decision 0004 (four lectures, no 1800 s total) are for
   interim work and do not lower this. The tool cannot verify the cited approvals themselves; the
   reviewer does.
4. Write the report with `--output report.md` (it never overwrites). `--dry-run` prints without
   writing. Undo: delete the report file.
5. Copy the report into the decision record for App-C 7 using
   `docs/evaluation/g6-wer-report-template.md`. Never include transcript text, audio or media.

## 4. What the tool does and does not do

Does: word-level edit distance; per-lecture and pooled WER (total errors / total reference words);
reads a B5.4 JSON transcript in order of `start` (segments may arrive out of order); scores an
empty hypothesis (`segments: []`) as all deletions, WER 100%, with a visible warning (it never
drops the lecture); refuses placeholders, an empty reference, empty files, non-UTF-8, URLs, absolute or `..` paths, media files, duplicate
or malformed lecture ids; labels every report as synthetic or official; keeps target and
acceptance at PENDING.

Does not: run any model; choose or approve a normaliser (only `unnormalised-whitespace` exists,
for tests); set a target or judge acceptance; compute a confidence interval, timing accuracy or
speed (proposed in ADR 0002 section 7, not approved); handle lectures longer than about 5,000
words each (pure Python, refused with a message).

## 5. Blockers and approvals

See the report template's last section; the list is kept in one place there.

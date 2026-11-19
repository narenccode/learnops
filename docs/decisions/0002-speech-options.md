# 0002. Speech-to-text options for the Video pipeline (T8)

**Date:** 2026-11-16
**Status:** PROPOSED. **PENDING GUIDE CONFIRMATION.** The guide has not approved anything in this
record. No guide approval, comment or decision about speech engines exists in the repository, in the
PRD or in the pull requests read for this record.
**Owner:** Student 4 (Video) · **Requirements:** FR-V-04, FR-M-02, G-6, G-7, App-C 7, C-10, EXT-04, OPS-10, OPS-11
**Contracts touched:** none. This record changes no contract (PRD §B.0).

## How to read this record

Three kinds of statement are kept apart on purpose:

- **PRD / repository fact:** quoted or paraphrased from a file in this repository, with its place.
- **Published claim:** a number or statement from a project's own README, release page or vendor
  documentation, with the version it was measured on. It was **not** reproduced by LearnOps and says
  nothing yet about Indian-English lectures.
- **LearnOps result:** a measurement made by this project on B8.5. **There are none yet.** Section 7
  says how they will be made. Every "LearnOps result" cell in this record is `PENDING`.

Anything marked `PENDING` is a gap, not a finding.

## 1. Context

The Video pipeline (PRD §C4) transcribes every lesson through the speech interface:
`speech.transcribe(audio_path, language="en")` returns segments with word timings and a `meta`
block (provider, model, duration_s, latency_ms, cost_estimate) (PRD §B5.4). FR-V-04 turns that
into `transcript.en.json` and `captions.en.vtt`. Goals G-6 (caption word error rate on
Indian-English lectures, target fixed in Release 0 from a first baseline run, App-C 7) and G-7 (a
90-minute recording ready within 30 minutes of becoming available) depend on this choice.

`docs/GETTING-STARTED.md` (Student 4, item 3) asks for a comparison of speech-to-text options for
Indian-English lectures (accuracy, cost, licence, local vs hosted) in this file.

**State of the file.** The task brief said `docs/decisions/0002-speech-options.md` already exists. It
does not: it is not on `origin/main`, on any remote branch, or in any local worktree (checked
2026-11-16). This record is therefore written new, not updated.

## 2. Requirements

| # | Requirement | Source |
|---|---|---|
| R1 | Lab speech-to-text is a **Whisper-family** model reached through the speech interface | PRD §A10, §B5.4 |
| R2 | All speech-to-text goes through `libs/model_interface`; no direct provider SDK in a module | PRD C-10, `CLAUDE.md` rule 6 |
| R3 | Provider is a configuration choice (`local` or `hosted`), behind an adapter | PRD EXT-04, B5.4 |
| R4 | Output has segments and, per segment, `words: [{start, end, word}]`; times are seconds from the start of the original audio; empty `words` is valid | PRD B5.4; B5 contract, merged in PR #25 (`contracts/model-interface.v1.schema.json`) |
| R5 | A 90-minute recording is ready (captions, transcript, chapters, slide index, manifest) at most 30 minutes after it becomes available. Transcription is only one step of that budget | PRD G-7, §C4.7 |
| R6 | No module may require a local GPU; a hosted provider must be possible in production | PRD OPS-11 |
| R7 | Transcription runs in worker containers from a job queue, never in a web request | PRD OPS-10 |
| R8 | Licences MIT, BSD or Apache-2.0 (LGPL only as an unmodified library) | `CLAUDE.md` rule 10 |
| R9 | Test data only. B8.5 speakers consented to "video stays in the lab" | PRD C-07; decision 0004 consent statement |
| R10 | Data sent to a hosted AI API is limited to what the task needs and documented in the data map | PRD SEC-07 |
| R11 | Students work only inside the lab VMs and the lab AI services provided by the guide | PRD C-12 |
| R12 | Caption WER measured on B8.5 and reported against the Release 0 target | PRD §C4.7, App-C 7 |

## 3. What the lab provides: verified vs unknown

PRD §A11 says the lab has "a speech-to-text endpoint" provided by the guide. Nothing more is
recorded. `.env.example` has only a placeholder (`SPEECH_LOCAL_URL=http://ai.lab.invalid:9000`, a
reserved invalid host). No lab endpoint was contacted for this record: none is configured in this
session, and the repository holds no endpoint address, credential or lab output.

| Question | Answer | Status |
|---|---|---|
| Which speech model does the lab provide? | "Whisper-family" only (PRD §A10, §B5.4). The model name and size (tiny … large, turbo, distilled, English-only or multilingual) are not recorded anywhere | **PENDING GUIDE CONFIRMATION** |
| Which engine serves it (openai/whisper, faster-whisper, whisper.cpp, another)? | Not recorded | **PENDING GUIDE CONFIRMATION** |
| Model and engine version | Not recorded | **PENDING GUIDE CONFIRMATION** |
| Does the endpoint return word-level timestamps? | Not recorded. B5.4 requires `words`; the proposed contract allows `words: []` | **PENDING** (needs one request to the endpoint; see section 9) |
| Request format, size limit, timeout, audio format accepted, authentication | Not recorded | **PENDING GUIDE CONFIRMATION** |
| Hardware behind the endpoint (GPU or CPU, memory), concurrency | Not recorded. PRD §A11 says nothing about a GPU | **PENDING GUIDE CONFIRMATION** |
| Behaviour on a 90-minute recording | Not measured | **PENDING** (LearnOps result) |
| Is the endpoint allowed to receive B8.5 audio, and does it keep it? | Open question 4 in `docs/data-map.md`, undecided | **PENDING GUIDE CONFIRMATION** |

The lab verification of App-C 4 (BigBlueButton) is in the same position: recorded as PENDING with no
lab access (T17: PR #96 is merged and records NOT VERIFIED; PR #97 was closed as superseded by #96). This record follows the same rule: no lab fact is claimed.

## 4. Options

The three engines below all run OpenAI's Whisper model weights, so they are compatible in model
family (requirement R1). They differ in the runtime.

| | openai/whisper | faster-whisper | whisper.cpp |
|---|---|---|---|
| What it is | The reference Python / PyTorch implementation | Reimplementation on CTranslate2 | C/C++ implementation, `ggml` model format |
| Repository | `openai/whisper` | `SYSTRAN/faster-whisper` | `ggml-org/whisper.cpp` |
| Licence (GitHub metadata, 2026-11-16) | MIT | MIT | MIT |
| Latest release found | `v20250625` (2025-06-26) | `v1.2.1` (2025-10-31) | `v1.9.5` (2026-10-06) |
| Last push to default branch | 2026-08-31 | 2026-11-12 | 2026-11-13 |
| Language / install | Python, PyTorch, `ffmpeg` on the system | Python (`pip install faster-whisper`); audio decoded by bundled PyAV, no system ffmpeg | C/C++ build; `whisper-cli` reads 16-bit WAV, so convert first (for example `ffmpeg -ar 16000 -ac 1 -c:a pcm_s16le`) |
| Server mode | None in the repository | Third-party OpenAI-compatible servers exist (for example `speaches`); not part of the project | `whisper-server` example (HTTP, WAV upload) |
| GPU | CUDA via PyTorch | CUDA 12 + cuDNN 9 (current `ctranslate2`); CPU also supported | CUDA, Metal, Vulkan, ROCm, OpenVINO, Core ML; CPU supported |
| Quantisation | Not in the README | int8 / int8_float16 on CPU and GPU | Integer quantisation of `ggml` models (for example `q5_0`) |

Non-Whisper engines (for example wav2vec2 / NeMo models, hosted APIs with their own models) are
listed in section 6. They are **not** candidates for the lab engine under the PRD as written.

## 5. Evidence-based comparison

### 5.1 Word-level timestamps (verified in each project's own code or README)

| Engine | Verified | Note for B5.4 |
|---|---|---|
| openai/whisper | `transcribe(..., word_timestamps=True)` exists; `whisper/timing.py` aligns words by cross-attention and DTW | Returns word start/end per segment. Mapping to `{start, end, word}` is direct |
| faster-whisper | README: `model.transcribe("audio.mp3", word_timestamps=True)`, each `segment.words` has `start`, `end`, `word` | Direct mapping |
| whisper.cpp | `whisper-cli` has `-ml/--max-len`, `-sow/--split-on-word`, `-wt/--word-thold`, `-ojf/--output-json-full` and `-dtw` (token-level timestamps) | Timing is **token-level**; words must be assembled by the adapter (or `-ml 1 -sow`). Accuracy of these word times is **not verified** |

That a flag exists is a published fact. How accurate the word times are on Indian English is a
LearnOps question (section 7.4).

### 5.2 Published benchmark results (NOT LearnOps results)

Source: the faster-whisper README benchmark. Audio: one 13-minute English recording (780 s).
GPU rows: NVIDIA RTX 3070 Ti 8 GB, CUDA 12.4, Whisper `large-v2`, beam size 5. CPU rows: Intel
Core i7-12700K, 8 threads, Whisper `small`, beam size 5. Versions measured: openai/whisper
`v20240930`, whisper.cpp `v1.7.2`, faster-whisper `v1.1.0`. These are **older than the current
releases** in section 4. The benchmark was written by faster-whisper's maintainers.

| Engine (published run) | Precision | Time for 780 s | Memory | Real-time factor (time / audio) |
|---|---|---|---|---|
| openai/whisper, GPU large-v2 | fp16 | 2m23s | 4708 MB VRAM | 0.18 |
| whisper.cpp, GPU large-v2 (flash attention) | fp16 | 1m05s | 4127 MB VRAM | 0.083 |
| faster-whisper, GPU large-v2 | fp16 | 1m03s | 4525 MB VRAM | 0.081 |
| faster-whisper, GPU large-v2, `batch_size=8` | fp16 | 17s | 6090 MB VRAM | 0.022 |
| faster-whisper, GPU large-v2 | int8 | 59s | 2926 MB VRAM | 0.076 |
| openai/whisper, CPU small | fp32 | 6m58s | 2335 MB RAM | 0.54 |
| whisper.cpp, CPU small | fp32 | 2m05s | 1049 MB RAM | 0.16 |
| faster-whisper, CPU small | fp32 | 2m37s | 2257 MB RAM | 0.20 |
| faster-whisper, CPU small | int8 | 1m42s | 1477 MB RAM | 0.13 |
| faster-whisper, CPU small, `batch_size=8` | int8 | 51s | 3608 MB RAM | 0.065 |

Other published figures: openai/whisper README lists approximate VRAM and relative speed (A100,
English): tiny ~1 GB, base ~1 GB, small ~2 GB, medium ~5 GB, large ~10 GB, turbo ~6 GB (turbo about
8x the speed of large). whisper.cpp README lists memory of ~273 MB (tiny), ~388 MB (base), ~852 MB
(small), ~2.1 GB (medium), ~3.9 GB (large). The faster-whisper README reports a WER only for a
different pair (distil-large-v3 on "YT Commons"): 13.527 (faster-whisper) vs 14.801 (transformers).
**No published benchmark found compares the three engines' accuracy on Indian-English lectures.** The
claim "up to 4 times faster than openai/whisper for the same accuracy" is the faster-whisper
maintainers' own statement and is not independently verified here.

### 5.3 What the published numbers do and do not support

- **Speed (extrapolation, not a measurement).** Scaling the real-time factors above linearly to 90
  minutes (5400 s): faster-whisper GPU fp16 about 7 min; faster-whisper CPU `small` int8 about 12
  min; whisper.cpp CPU `small` about 14 min; openai/whisper GPU large-v2 about 16.5 min;
  openai/whisper CPU `small` about 48 min. Only the last exceeds 30 minutes by itself, and the CPU
  rows use the small model, which may be less accurate than the large models. G-7's 30-minute
  budget also has to cover chapters, summary, slide index and transcode, so a transcription step
  above about half the budget would put G-7 at risk. This is a screening estimate: it assumes the
  benchmark's hardware, a 13-minute clip and linear scaling.
- **Hardware.** OPS-11 forbids requiring a GPU, so CPU-only operation of the chosen configuration
  must be shown (section 7.5). GPU speed is a bonus, not an assumption.
- **Accuracy** between engines using the same weights is expected to be close but is not
  guaranteed: decoding settings, voice-activity filtering, quantisation and chunk handling differ.
  Not established. LearnOps measures it (section 7).

### 5.4 90-minute recordings

All three engines decode long audio in sliding 30-second windows. No source read for this record
reports behaviour on a 90-minute recording, so the following is **unverified for LearnOps**:
memory growth, repetition or dropped text on long audio, drift of word times over time, and
total latency. Whisper-family models can loop or invent text on silence or music;
openai/whisper exposes `condition_on_previous_text` and `hallucination_silence_threshold`, and
faster-whisper has a voice-activity filter (`vad_filter`, on by default only for batched
transcription); whisper.cpp has `--vad`. These are settings to test, not proven fixes. The audio
for a 90-minute lecture as 16 kHz mono 16-bit WAV is about 173 MB (5400 s x 32,000 B/s), which
matters for upload limits on a speech endpoint and for FR-V-15 retention.

### 5.5 Hosted option and OpenAI whisper-1

OpenAI's documentation. First read 2026-11-16 through search results; **re-checked on 2026-11-19
against the text of the speech-to-text guide, the deprecations page and the transcription guide**
(the statements below were confirmed; the community thread was not re-read):

- `whisper-1` is **deprecated**; it, `gpt-4o-transcribe`, `gpt-4o-mini-transcribe` and
  `gpt-4o-transcribe-diarize` are announced for removal from the API on **2027-02-26**; the
  deprecations page names `gpt-live-transcribe` or `gpt-transcribe` as replacements.
- The `timestamp_granularities[]` parameter (word and segment times) is supported **only for
  `whisper-1`**. The speech-to-text guide says existing integrations can keep using whisper-1 for
  word or segment timestamps until that date.
- No successor with word timestamps was found in the pages read. An OpenAI community thread asks
  the same question and reports no answer.

Relevance to B5.4: the contract requires per-word times, and captions and any later word-level
feature depend on them. A hosted adapter built on OpenAI would rely on a model that goes away on
2027-02-26 and has no documented word-time replacement. That is roughly 3.5 months after this
record, and Release 3 (the Video core) lies after Release 0. So an OpenAI `whisper-1` adapter
**must not be the default hosted provider** and must not be the basis of the G-6 baseline. A
different hosted provider with word timestamps is a guide decision, and the B5.4 `words` field
stays valid as `[]` for a provider that cannot give them (proposed contract decision 4).

Sources: [File transcription](https://developers.openai.com/api/docs/guides/speech-to-text),
[Deprecations](https://developers.openai.com/api/docs/deprecations),
[Transcription guide](https://developers.openai.com/api/docs/guides/transcription),
[community thread on the missing migration path](https://community.openai.com/t/deprecation-of-whisper-1-diarization-models-missing-migration-path-for-timestamps-diarization-and-srt/1413456).

Privacy: B8.5 speakers consented to "video stays in the lab" (decision 0004). Sending their audio
to any hosted API contradicts that statement unless the guide decides otherwise and the consent
wording allows it. So hosted providers are **not** used on B8.5 audio in this record's plan.

## 6. Are non-Whisper alternatives permitted?

- **Lab speech-to-text:** the PRD fixes it as "Whisper-family" (§A10, §B5.4), and
  `docs/design/video.md` §7 records "none (fixed by PRD)". A non-Whisper local model is **not**
  permitted without the guide's decision. `CLAUDE.md` §5 says to ask the guide before introducing
  anything outside the fixed stack.
- **Hosted provider:** B5.4 allows `hosted` as "a speech-to-text API" without naming a vendor, so
  a non-Whisper hosted API is not excluded by the text. Which one, and whether recordings may leave
  the lab (SEC-07, data map question 4), is not decided.
- **Distilled Whisper variants** (for example `distil-large-v3`, supported by faster-whisper) are
  Whisper-family in architecture. Whether they count under "Whisper-family" for the lab is a
  reasonable reading but is **not confirmed** by the guide.

No non-Whisper engine is evaluated here. Doing so would not change the decision, which the PRD
already limits.

## 7. Evaluation methodology (proposed; nothing run yet)

This is the plan for LearnOps results. It has not been executed: B8.5 is itself PENDING (no
lecture recorded, no consent given, no reference transcript typed;
`testdata/b8-5-lecture-videos/README.md`). **Do not use any number from section 5 as a LearnOps
result.**

### 7.1 Data

B8.5 lectures (at least five, at least 1800 s in total, Indian English, recorded by the team),
reference transcripts typed by hand or corrected from a model **outside** the comparison and
reviewed by Harshitha (decision 0004). Audio stays on the permitted machines or lab storage; it is
never committed. For the 90-minute test, a longer recording is needed. Decision 0004 does not
provide one: either concatenated B8.5 audio or a separately consented recording. That choice is
open (section 9).

### 7.2 Systems compared

Each run records: engine and version (or commit), model name and size, quantisation / compute type,
decoding settings (beam size, temperature fallback, VAD, `condition_on_previous_text`), hardware
(CPU model, threads, RAM, GPU if any), date, and who ran it. The lab endpoint is included as soon
as its details are known. Self-hosted candidates: openai/whisper, faster-whisper and whisper.cpp,
each at the same model size first, then at the size that fits the time budget.

### 7.3 WER procedure

- Metric: word error rate = (substitutions + deletions + insertions) / words in the reference,
  by word-level edit distance. Implementation: `jiwer` (GitHub metadata: Apache-2.0; the exact
  version to be pinned and its licence re-checked before adding it, as `CLAUDE.md` rule 10 requires),
  or a small own implementation if the licence check fails.
- **Pooled WER** = total errors over all lectures / total reference words (not the mean of
  per-lecture WERs). Also report per-lecture WER and the number of reference words for each.
- With only about five lectures, report a 95% bootstrap interval resampling lectures, and say that
  the interval is wide. No target is invented here: the G-6 target comes from the first baseline
  run (App-C 7) and is set by the project, not by this record.
- **Same normalisation for reference and hypothesis**, applied by one versioned function with unit
  tests, in this order: Unicode NFKC; lower case; replace apostrophes and hyphens consistently
  (hyphen to space, keep apostrophes inside words); remove other punctuation; spell numbers as
  words (the same rule on both sides; spoken-form rule for the reference); remove the fillers
  `um`, `uh`, `erm`, `hmm` from both sides; collapse whitespace. Spelling variants (British /
  American) are **not** merged silently: a reference written in one convention is compared as is,
  and the variant list used, if any, is recorded.
- Sensitivity check: also report the WER with Whisper's own English normaliser
  (`whisper/normalizers`, shipped in openai/whisper) so that readers can compare with published
  Whisper figures. The primary figure is the one above.
- Technical terms, acronyms and code identifiers: reference transcripts write them in spoken form.
  Report WER with and without a short list of domain terms to show how much comes from vocabulary.
- Not reported as WER: sentence boundaries, capitalisation, punctuation quality.

### 7.4 Word-timestamp checks

There is no reference for word times, so timing accuracy is **not** claimed. Checked automatically
on every run: every word has `end` at least `start`; times are non-negative; times are within the
audio duration (the contract allows a small overrun, so report it, do not fail); segments cover
the audio without large unexplained gaps; no repeated-text loop (same text 5+ times in a row);
and `words` is non-empty when the segment text is non-empty. Spot check by a person: 20 words per
lecture, played back at their reported times, with the share within 0.5 s reported as a sample
statement only.

### 7.5 Compute and long-audio measurements

On each configuration: wall-clock time and real-time factor, peak resident memory and VRAM, CPU
threads used, behaviour with no GPU (OPS-11), and the same measurements on the 90-minute input.
Run every measurement at least three times on an otherwise idle machine and report the median and
the range. Record whether the run completed, and whether text was dropped or repeated, by
comparing the start, middle and end of the transcript against the reference. This feeds G-7 but
does not prove it: G-7 covers the whole pipeline.

## 8. Proposed decision

**Proposed; PENDING GUIDE CONFIRMATION. Nothing here is approved.**

1. **Follow the PRD.** The lab speech engine stays Whisper-family, behind the speech interface
   (R1–R3). This record does not propose leaving that.
2. **Do not choose the lab engine.** The lab endpoint is provided by the guide, and its model,
   engine and version are unknown (section 3). Choosing one would be silently picking an
   unapproved engine, so the engine behind the lab endpoint is **PENDING GUIDE CONFIRMATION**. The
   guide is asked for the items in section 9.
3. **Keep the adapter engine-neutral.** The `local` adapter talks to the endpoint through the
   speech interface and records `meta.model` as model name + engine + version + compute type, so
   that results from different engines stay distinguishable. No engine-specific code in modules.
4. **Evaluation candidates, not a choice.** Self-hosted evaluation includes all three engines
   (section 7.2). On the published evidence the screening order for CPU-only use is
   faster-whisper int8 then whisper.cpp; openai/whisper on CPU is the slowest published run and is
   the reference for accuracy. This order is a screen from published numbers on other hardware
   and audio, and it is **not** a LearnOps result or a recommendation to adopt.
5. **No OpenAI `whisper-1` default** for the hosted provider (section 5.5). A hosted provider for
   production is a separate guide decision. It is not used on B8.5 audio.
6. **Fix the target later.** The G-6 WER target is set after the first baseline run on B8.5
   (App-C 7), not in this record.

## 9. Open questions (for the guide unless stated)

All are **PENDING GUIDE CONFIRMATION** unless noted.

1. Which Whisper-family model (name, size, English-only or multilingual, distilled or not) does the
   lab endpoint serve?
2. Which engine and which version serves it, and on what hardware (GPU or CPU, memory, concurrency)?
3. Does the endpoint return word-level timestamps? In what request and response format, with what
   audio-length and file-size limit, timeout and authentication?
4. May the lab endpoint receive B8.5 audio for the comparison, and does it keep it? (Data map,
   question 4; consent statement "video stays in the lab".)
5. Are non-Whisper local models and distilled Whisper variants permitted, or is the PRD wording
   "Whisper-family" strict?
6. Is a hosted provider permitted in production, which one, and what data may it receive (SEC-07)?
   OpenAI `whisper-1` is excluded by section 5.5 unless the guide decides otherwise.
7. May LearnOps run its own self-hosted engine (outside the lab endpoint) in a worker for the
   evaluation, given C-12 ("only inside the lab virtual machines and the lab AI services")?
8. Where does a 90-minute test recording come from, with consent? (Owner: Student 4.)
9. Which `distil` or quantised variants, if any, may be evaluated? (Follows from question 5.)
10. Is the B5 contract (merged in PR #25) the final shape for `words`, and does the guide want
    `words: []` accepted from providers without word times for G-6 purposes? (Owners: Student 3, guide.)

## 10. Trade-offs

| Choice | Gains | Costs |
|---|---|---|
| Stay Whisper-family (PRD) | One model family, same word-timing method, no new decision | A non-Whisper model with better Indian-English accuracy cannot be tried without the guide |
| Engine-neutral adapter | Engine swap is configuration (EXT-04); lab endpoint can change | Word and segment shapes differ per engine; adapter must normalise (especially whisper.cpp tokens) |
| Evaluate three engines | Evidence instead of reputation | More work and more hardware time before Release 3 |
| faster-whisper first on CPU (screen only) | Lowest published CPU time among the same-model runs, less memory than openai/whisper | Published by its own maintainers; older versions; no Indian-English result |
| whisper.cpp | Small memory, many hardware back ends, a server example | Needs WAV conversion; word times are token-level, so extra adapter code |
| openai/whisper | Reference behaviour, direct word timestamps | Slowest published CPU run; needs PyTorch and system ffmpeg; large image |
| Hosted provider | No local compute, fast | Cost per minute, recordings leave the lab (conflicts with B8.5 consent), vendor deprecation risk (whisper-1) |
| Small test set (about 30 min, five lectures) | Feasible | Wide WER interval; not a general claim about Indian English |

## 11. Consequences

- The Video module can proceed against the B5.4 interface using the fake provider; no engine is
  required to start. FR-V-04 cannot be called done against a real engine until the lab endpoint is
  confirmed and measured.
- If the lab endpoint returns no word times, `transcript.en.json` has `words: []` and any later
  feature needing word times has no data; this must be raised before Release 3.
- If a later measurement shows the 90-minute budget is missed on CPU, options are a smaller model,
  int8 quantisation, batching, or a faster host, all configuration; the PRD's G-7 target is the
  guide's to change.
- Docs follow-ups (not done here; no other file is changed by this record): `docs/data-map.md`
  question 4, `docs/design/video.md` §7 (add a line pointing to this record once the guide
  responds), and the App-C 7 baseline record.
- This record does not alter the Video design document, PR #85 or PR #93 (both merged).

## 12. Evidence and sources

PRD (§A10, §A11, §B5.4, §B6.2, §C4.3, §C4.7, App-C 7, C-07, C-10, C-12, EXT-04, OPS-10, OPS-11,
SEC-07), `docs/design/video.md`, `docs/GETTING-STARTED.md`, `docs/data-map.md`,
`docs/decisions/0004-b8-5-lecture-videos.md`, `testdata/b8-5-lecture-videos/README.md`,
`.env.example`, and the B5 contract merged in PR #25 (the merged contract is the source, not the branch).
The Video literature survey (`docs/literature-video.md`, verified entry S2 on Indian-accented English
speech recognition, PR #100) was not used for this record, which relies on the project READMEs and the
OpenAI pages below.

Published sources, read 2026-11-16:
[openai/whisper](https://github.com/openai/whisper),
[faster-whisper](https://github.com/SYSTRAN/faster-whisper) (README benchmark),
[whisper.cpp](https://github.com/ggml-org/whisper.cpp) (README, `examples/cli`, `examples/server`),
[jiwer](https://github.com/jitsi/jiwer), and the four OpenAI pages in section 5.5.
Release dates, licences and push dates come from the GitHub API. The OpenAI statements were first
taken from a web search summary and were re-checked against the page text on 2026-11-19; only the
community thread (a user report, not a source of fact) was not re-read.

## 13. Guide decision

| Item | Value |
|---|---|
| Guide decision | **PENDING GUIDE CONFIRMATION** |
| Decided by / date | — |
| Link to approval | none exists |

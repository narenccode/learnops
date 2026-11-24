# PR to-do list (Video module) — last updated 19 Nov 2026

Tick a box (`- [x]`) when you finish an item. Tags: **ME** = you, **CLAUDE** = ask Claude to do it, **GUIDE** = only the guide can do it, **PEER** = needs a peer review.

Repo: https://github.com/narenccode/learnops

---

## 1. Do first

### #98 — Speech-to-text ADR 0002 — https://github.com/narenccode/learnops/pull/98
- [ ] **CLAUDE** In `docs/decisions/0002-speech-options.md`, change the three stale "PR #25 open / not merged / unmerged" lines to "merged in PR #25" (R4, open question 10, the B5 record line). The guide's assistant asked for this.
- [ ] **CLAUDE** Push it, check that `checks` passes, then tell the guide the new head commit.
- [ ] **CLAUDE** Re-read the four OpenAI pages and fix the `whisper-1` statements (the ADR says they came from a search summary).
- [ ] **CLAUDE** Fix the "no literature survey exists" statement (S2 is merged in #100).
- [ ] **GUIDE** Approve the six points of the proposed decision, and answer the questions posted on the PR. Do not merge before this.
- [ ] **ME** Take it out of Draft, then ask for a peer review.

### B8.5 durations (no PR yet)
- [ ] **CLAUDE** Open a small PR with the stranded commit `9c6d703` (five ffprobe durations), from branch `video/b8-5-dataset-evidence`. PR #99's description says durations were recorded, but `main` still shows PENDING.

---

## 2. Re-audits against current `main`

### #104 — Release 0 evidence audit — https://github.com/narenccode/learnops/pull/104
- [ ] **CLAUDE** Rewrite the stale tables: #83, #85, #93, #96 are shown as open or excluded, but they are merged.
- [ ] **CLAUDE** Note that #103 is merged and #97 is closed.
- [ ] **CLAUDE** Fix the undefined T7/T11 labels, and cite the decision 0004 exception (#125, issue #121) instead of "PENDING".
- [ ] **GUIDE** Say what licence/consent evidence is needed for B8.5 (App-C 8). **Not asked on the PR yet.**
- [ ] **ME** Take it out of Draft, then ask for a peer review.

### #105 — Release 0 report and demo script (T19) — https://github.com/narenccode/learnops/pull/105
- [ ] **CLAUDE** Re-audit against current `main`. It still lists about ten merged PRs as open (#25, #27, #46, #54, #61, #83, #85, #93, #95, #96) and says `docs/decisions/0001` is not written.
- [ ] **CLAUDE** Re-check against the changed PRD (#113, #116).
- [ ] **GUIDE** Give T19's real acceptance criteria. **Not asked on the PR yet.**
- [ ] **ME** After #104 is in, take it out of Draft, then ask for a peer review. Merge it last.

---

## 3. Waiting for the guide's answers

### #129 — Lesson Processor demo — https://github.com/narenccode/learnops/pull/129
- [ ] **CLAUDE** Merge `main` again (the PR has conflicts).
- [ ] **CLAUDE** Fix Akshita's code items: validate `LESSON_MAX_UPLOAD_BYTES` (bare `int()`), restrict ffprobe protocols, cap and clean up the job list, add Pydantic models.
- [ ] **GUIDE** Answer the 4 questions on the PR: merge while design is Draft; web dependencies outside root `requirements.txt`; approve `ci.yml` and `.gitignore`; file map or split for 1,340 lines.
- [ ] **PEER** Akshita re-reviews after the fixes.
- [ ] **ME** Take it out of Draft after the guide answers.

### #140 — Video design document — https://github.com/narenccode/learnops/pull/140
- [ ] **GUIDE** Answer Q1–Q16 on the PR (comment is posted).
- [ ] **ME** Read every **Proposed** part and be able to explain it; tick the §14 owner box when you can.
- [ ] **CLAUDE** After #103 merged, refresh any statement that names the speech tool; update the doc with the guide's answers.
- [ ] **PEER** Ask a peer from another module to review.
- [ ] **ME** Move the document to `In review` after the peer review.

---

## 4. Needs your own work

### #106 — Literature survey P1–P8 — https://github.com/narenccode/learnops/pull/106
- [ ] **ME** Open every source P1–P8 yourself and confirm it matches the entry (all links open; titles of P1–P4 match). Then mark each as verified.
- [ ] **ME** Read P3 and P8 in full (the PR says they were only partly read).
- [ ] **ME** Add sources to reach 6 verified: technical-lecture WER and normalisation, lecture segmentation, summarisation, upload proxy limits, BBB `metadata.xml`.
- [ ] **ME** Cover the topics not yet searched: privacy and consent for recordings, captioning accessibility, Moodle video embedding.
- [ ] **ME** Take it out of Draft, then ask for a peer review.

---

## 5. Evidence that is still not a PR

- [ ] **ME** BBB lab run (App-C 4): record the real metadata keys and video-format location. Currently NOT VERIFIED (#96).
- [ ] **ME** First WER baseline (App-C 7), after the B8.5 set is complete and the guide confirms the speech engine (#98).
- [ ] **ME** B8.5 consent lines, file names, speakers and reviewed transcripts for five lectures (App-C 8).
- [ ] **ME** Decide with the guide whether to resubmit the design content from the closed PR #29 (854 lines vs 318 on `main`) in smaller PRs.
- [ ] **GUIDE** Renumber one of the two decision files both called `0001` (`0001-lti-library.md` and `0001-b5-model-interface-v1.md`).

---

## 6. Merge order, once approved

1. #98 (needs the guide first)
2. B8.5 durations PR
3. #106
4. #104
5. #129 and #140 (as the guide answers)
6. #105 last (it summarises all the others)

---

## Done

- [x] #103 WER preparation: merged
- [x] #97 closed as superseded by #96
- [x] #126 B8.5 status wording: merged
- [x] #140 design document: draft PR opened with Q1–Q16 posted to the guide
- [x] Guide questions posted on #98 and #129

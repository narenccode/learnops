# Video module owner audit (Nagashree V, `vnaags`)

**As of:** 2026-11-23, from GitHub PR state and the repository on `main`. **Scope:** the Video module (M4) and everything the owner has done or still has to do for the Release 0 freeze. **Status of this file:** a working audit for the owner. It is not a repository document, it grants nothing, and it is not an approval.

---

## 1. At a glance

| | |
|---|---|
| PRs authored under this account | 46 in total: **37 merged**, **8 closed without merging**, **1 open** (#98, Draft) |
| Video design document | `Draft` (guide's answers Q1 to Q16 recorded; the owner box in section 14 is not ticked; only the guide sets `Approved`) |
| B8.5 lecture dataset | **COMPLETE** under decision 0004 (five lectures, 2380 s, four consent lines), merged in #169 |
| Literature survey | **13 owner-verified sources** (S2 and P1 to P12) against the 6 required; coverage gaps remain; the file stays a Draft |
| Lesson Processor demo | merged (#129), a demonstration, not Release 3 |
| Release 0 freeze (whole project) | **NOT READY** per `docs/release-0/freeze-readiness-checklist.md`; B4 lab checks are the main blocker, outside the Video module |
| Video items still open | the lab facts for #98, App-C 9 lab check, design approval chain, B6 reply from Checker, B8.6 inputs, grading-design peer box, guide answers |

---

## 2. Completed

### 2.1 Design
| PR | What | State |
|---|---|---|
| #17, #24, #34 | Design skeleton, further updates, clarified unresolved decisions | merged |
| #140 | Design document draft completed, stale facts refreshed, guide questions Q1 to Q16 posted and the guide's answers recorded | merged 22 Nov |
| #28, #29 | Earlier revised design drafts | closed, superseded |

### 2.2 Contracts and shared library (B6)
| PR | What | State |
|---|---|---|
| #32 | B6.3 lesson manifest contract v1 | merged 15 Nov |
| #93 | B6.2 chapters, slides and cues contracts v1 (guide approved; rules confirmed) | merged 16 Nov |
| #84, #85, #86 | `libs/media_paths`: validation, templates, signing | merged 15 and 16 Nov |
| #155 | `libs/media_paths` README: install, configure, run, check, undo (EXT-09) | merged 22 Nov |
| #38 | Earlier media-path draft | closed, superseded |

### 2.3 Test data B8.5 (lecture videos)
| PR | What | State |
|---|---|---|
| #82, #89 | Dataset checker and synthetic validation tests | merged 15 Nov |
| #99 | Dataset evidence (hashes) | merged 16 Nov |
| #125, #126 | Guide-approved temporary exceptions recorded, evidence status corrected | merged 17 and 18 Nov |
| #104 | Release 0 dataset and acceptance evidence audit | merged 22 Nov |
| #154 | Five `ffprobe`-measured durations | merged 22 Nov |
| #169 | Five lectures: outlines, typed transcripts marked `checked`, speaker names, four written consent lines; status COMPLETE; decision 0004 approval links fixed | merged 22 Nov |
| #43 | First dataset attempt | closed, superseded |

### 2.4 Appendix C and decisions
| Item | What | State |
|---|---|---|
| #96 | App-C 4 BigBlueButton recording metadata record | merged, **NOT VERIFIED** (no lab observation) |
| #156 | App-C 9, which AI features Moodle 5.3 provides (decision 0012) | merged, **source-checked, not verified on the lab site** |
| Decision 0011 | B8.5 data handling (retention, names, transcripts, processing services) | merged |
| Decision 0013 | `libx264` exception for the demo (guide's decision of 22 Nov) | merged with #129 |
| #97 | Lab BigBlueButton verification as PENDING | closed, superseded by #96 |

### 2.5 Speech evaluation preparation
| PR | What | State |
|---|---|---|
| #103 | G-6 caption word-error-rate evaluation preparation (`libs/speech_eval`); official mode is refused today | merged 18 Nov |

### 2.6 Literature survey (T13)
| PR | What | State |
|---|---|---|
| #100 | S2 Svarah audit | merged |
| #106 | Entries P1 to P12 recorded as AI-researched, pending owner verification | merged 22 Nov |
| #194 | Owner verification of P1 to P12 recorded (13 sources against the required 6), with the P3, P7, P8 and P6 observations | merged 23 Nov |

### 2.7 Release 0 documents and demos
| PR | What | State |
|---|---|---|
| #105 | Release 0 report chapter and demonstration script | merged 22 Nov |
| #163 | Release 0 documents and D4 demo README refreshed | merged 22 Nov |
| #198 | B8.5 and #129 statements refreshed after #169 and #129 (report, checklist, demo script, design doc, traceability) | merged 23 Nov |
| #117 | D4 video paths demo | merged 16 Nov (an earlier revert #119 was closed) |
| #129 | Video Lesson Processor demo (one-PR exception from the guide; FR-V-01, FR-V-03 and FR-V-08 in part) | merged 23 Nov |

### 2.8 Merged under this account but belonging to other modules
These are not Video work. They are listed so the record is complete, and the owner has said the B8.3 ones belong to the checker module.
- **B3 LTI:** #122 (LTI library decision and security documentation review), merged.
- **B8.3 planted-error data (Checker):** #178, #179, #180, #181, #185, #193 and #201, all merged. #177 and #184 were closed.

---

## 3. Pending

### 3.1 Waiting on lab information (tomorrow, from the lab)
| Item | What is needed | Then |
|---|---|---|
| **#98**, speech-to-text ADR 0002 (Draft) | Non-secret lab facts: model and size, engine and version, hardware, request format and limits, authentication type, word timestamps, what the endpoint keeps; plus the lab image's `ffmpeg -version` output | Fill in the entries; fix the stale "B8.5 is itself PENDING" line; take it out of Draft; one peer approval; the guide confirms the status |
| **App-C 9 lab check** (decision 0012) | Someone with admin rights on the lab Moodle 5.3 site checks Site administration, AI: providers, placements, the Moodle build. Optionally the same on 4.5 | Record the result with no addresses or credentials |
| App-C 4 BBB lab verification (decision 0005/0006) | Lab BigBlueButton version and the `metadata.xml` field names | Release 3 item; optional for Release 0 |

### 3.2 Waiting on the guide
Posted on issue #186 on 23 Nov (comment 7098427808); no answer yet:
1. Which of the two decision records numbered `0001` to keep.
2. Whether the dataset alone satisfies Release 0 for WER, with the first baseline run left for Release 3.
3. Acknowledgement that Nagashree, not Harshitha, checked lecture 02.
4. Whether the owner's statements on B8.5 (durations, hashes, file names, official-set provenance, speaker briefings) are acceptable for Release 0.
5. When the lab facts for #98 can be shared.

### 3.3 Waiting on other owners
- **B6 confirmations:** Studio (Akshita) and Grading (Harshitha) confirmed no changes. **The Checker owner's reply is missing.** The freeze checklist still says the contract owners' approvals are not recorded; once all replies are in, add them to the checklist.

### 3.4 Assignments from the guide (issue #186) that name the Video owner
- **B8.6 chapter and summary inputs** (design Q12): the grading design proposes one chapters item and one summary item per B8.5 lecture. Each needs a timed transcript (B5.4 shape), expected `chapters.json` (B6.2 shape) and expected `summary.en.md`. The B8.5 transcripts have no timestamps, so the times must come from the recordings. B8.6 itself merged as a provisional set in #33.
- **Grading design peer box** (`docs/design/grading.md`, section 14, line 1239): review the design against the PRD chapter and the contracts, leave comments, wait for them to be resolved, then tick the box in a small docs PR.
- The speech-logging point (kind column) was already answered on #186 on the owner's behalf.

### 3.5 Design document approval chain (last, as the owner decided)
1. Tick the section 14 owner box in `docs/design/video.md`.
2. Open a PR moving the status to `In review`.
3. A peer reviews it; **only the guide sets `Approved`**.
4. Feature code for the Release 3 pipeline waits for `Approved`.

### 3.6 Survey follow-ups (optional; the count of 6 is already met)
- P12: whether chapter 16 defines WER and normalisation was not reported.
- P8: request parameters and response fields are from a summary, not read verbatim.
- P10: cue syntax and settings are from a summary; the owner confirmed they match.
- P4: the Springer lead (Benedetto et al.) sits behind a login and is unread.
- Coverage gaps: lecture-specific segmentation and summarisation, WER normalisation, privacy and consent for lecture recordings, Moodle video embedding, `metadata.xml` of BigBlueButton recordings.

### 3.7 Not started (Release 3 and later, not Release 0)
The video pipeline itself (FR-V-01 to FR-V-15: resumable upload, job queue and workers, transcription, chapters, summaries, slide index, Moodle integration, BigBlueButton intake). The design question Q10 (an LGPL ffmpeg build without GPL parts) stays open until the lab image's `ffmpeg -version` output is known.

---

## 4. What is verified and what is only a statement

| Claim | Basis |
|---|---|
| B8.5 data is COMPLETE under decision 0004 | The checker test (71 passed), reviewed PRs #169 and #198 |
| Durations, hashes, file names, official-set provenance (G-8), speaker briefings, transcript typing and lecture-02 check | **The owner's statements**; recorded as such; not independently verified |
| 13 literature sources verified | **The owner's statement** that each was opened and matched; a peer spot-checked several sources |
| App-C 9 | Source-checked only; **not verified on the lab site** |
| App-C 4 | **NOT VERIFIED** |
| WER (G-6) | **Nothing measured**; method and normalisation are not approved |

---

## 5. Not the Video owner's work

- CHANGELOG, `docs/releases/r0.md`, the security review, tags and the adoption test belong to the release owner and the guide.
- **B4 (Moodle web services)** is not ready to freeze: Harshitha reports all 18 lab checks open and the lab account and token waiting for the guide. Contracts freeze together, so this blocks the freeze for every module.
- The B3 question on who owns `shared.course_link` columns is open between Harshitha and the guide.

---

## 6. Suggested order

1. Send the lab-detail request; wait for the answers (3.1).
2. Wait for the guide's reply on #186 (3.2) and the Checker's B6 reply (3.3).
3. Decide with the guide whether the B8.6 inputs are needed for Release 0 (3.4), and review the grading design as peer (3.4).
4. Update #98 and decision 0012 with the lab answers.
5. Tick the owner box in the Video design and move it to `In review` (3.5).

# 0011. B8.5 data handling: retention, lab storage access, names and transcripts, processing services

**Date:** 2026-11-20
**Status:** Decided by the guide. First given on 2026-11-19 and **confirmed by the guide in his own
words, with two amendments, on 2026-11-20**. This record only writes the decisions down; it grants
nothing else.
**Source of the decision:** [comment on PR #104](https://github.com/narenccode/learnops/pull/104#issuecomment-7053519154), 2026-11-20 (the earlier
[comment](https://github.com/narenccode/learnops/pull/104#issuecomment-7008198219) of 2026-11-19 is superseded where they differ).
**Requirements:** PRD B8.5, App-C 8 (licence or consent for every B8.5 video), G-6, SEC-06, SEC-07,
C-07, C-12. The four questions are the ones listed in `docs/data-map.md` ("B8.5: open questions for
the guide"), which asked for the decision to be recorded in `docs/decisions/` first.
**Contracts touched:** none.

## Context

Decision 0004 (B8.5 lecture videos) keeps recordings out of Git and records each speaker's consent
line. It does not say how long recordings are kept, who may reach them, what happens when a speaker
withdraws, or which services process the audio. `docs/data-map.md` listed these as four open questions
and said no row may claim an answer until the decision is recorded here. The related speech-to-text
record is `docs/decisions/0002-speech-options.md` (PR #98).

## Decisions

1. **Retention (amended 2026-11-20).** Recordings, extracted audio and transcript drafts are kept
   until the **last measurement that uses B8.5** is recorded. That includes the caption word error
   rate measured on B8.5 for the Release 3 acceptance (PRD C4.7), not only the Release 0 baseline.
   Then the person who recorded the lecture deletes their local copies, Student 4 deletes the lab copies and scratch files, and the deletion
   is recorded in the evidence. If the project ends first, delete then.
2. **Lab storage access.** Only the team and the guide may reach the lab storage. There is no public
   link, and the location stays out of the repository.
3. **Names and transcripts (amended 2026-11-20).** The consent lines, the speakers' names and the
   Apache-2.0 transcripts stay in the repository as the public consent record. If a speaker
   withdraws, remove them from the current tree, record the withdrawal, and say that Git history keeps
   the earlier version. No history rewrite. One sentence is added to the briefing in decision 0004:
   before a speaker writes the consent line, they are told that a withdrawal removes the name from
   the current files but older versions stay in Git history.
4. **Processing services.** Only the lab endpoint inside the lab receives B8.5 audio; no hosted
   service receives it. Record what the endpoint keeps, and delete it after the run. What the
   endpoint keeps is **not recorded yet**: it comes with the lab facts that PR #98 is waiting for
   (`docs/decisions/0002-speech-options.md`, section 9).

## Consequences

- The four data-map rows for B8.5 and the questions section are updated by the same pull request as
  this record; no row claimed an answer before this record existed.
- Deleting the recordings happens after the last measurement that uses B8.5, the Release 3 caption
  word error rate included. The evidence must say who deleted what and when. Nothing is deleted
  yet, because no evaluation has run.
- Because Git history keeps earlier versions, a speaker who may later withdraw must be told this
  before writing the consent line; decision 0004 already requires that they are told the line is
  public.
- This record does not set the retention of the lab endpoint's own copies; it only requires that
  they be recorded and deleted after the run.

## What this record does not decide

Whether B8.5 is complete, whether a recording is an official B8.5 recording, the 1800 s total or the
five-lecture rule (both are in decision 0004, with the guide's temporary exceptions), or any
hosted provider for production (open in decision 0002).

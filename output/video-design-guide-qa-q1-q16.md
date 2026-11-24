# Video design: the guide's questions Q1 to Q16 and his answers (local copy)

**What this is:** a local copy of the "Guide's answers (2026-11-19, PR #140)" part of `docs/design/video.md` section 12, which was removed from the design on 2026-11-25 at the owner's request, together with the questions and the guide's full reply from the PR #140 thread. The design now only points to the thread.
**Sources (the originals stay on GitHub):**
- Questions, posted by the owner on 2026-11-18: https://github.com/narenccode/learnops/pull/140#issuecomment-6986610632
- Answers, posted by the guide's assistant on 2026-11-19: https://github.com/narenccode/learnops/pull/140#issuecomment-7005848536
**Status:** a private copy in the local `output` folder. It is not in Git and not a repository document.

---

## 1. The questions (as posted on PR #140)

@narenccode Guide questions for the Video design document (`docs/design/video.md`, section 12). The PRD is silent on these, so the document marks each as **Proposed**. Please answer in writing, or amend the proposal in review. The status stays `Draft` until you approve.

**Architecture and data**
1. **Q1:** Is the job queue the PostgreSQL `video.job` table (`SKIP LOCKED` claims), with no separate queue product? (sections 3, 7)
2. **Q2:** Does BigBlueButton polling run in its own `bbb-poll` worker container? (3, 7)
3. **Q3:** Do workers touch media only through the storage adapter, with a shared mount if the local-folder backend is on another host? (3, 7)
4. **Q4:** Are the proposed columns, states and routes right, including title-only chapter edits and administrator-only re-process? (5, 6)
5. **Q5:** What is `source.kind` for BigBlueButton intake, and what replaces `uploaded_by` there? (4)
6. **Q7:** Which tool runs the versioned, reversible migrations (OPS-07)? (5, 8)

**Behaviour and defaults**
7. **Q6:** Is a `.trash/` prefix with a 30-day restore an acceptable undo for lesson removal, and are the proposed CLI commands right? (6, 7)
8. **Q8:** Which feature flags are on by default? The PRD fixes only the slide index; `.env.example` has `FEATURE_SUMMARIES=true`. (6)
9. **Q16:** Is the Moodle 5.3 AI-feature overlap check (App-C 9) in scope for this module? (12)

**Speech, media and libraries**
10. **Q9:** Which engine and model does the lab speech endpoint serve? (Same question as ADR 0002 on #98.) (4, 7)
11. **Q10:** Is calling ffmpeg as a separate process acceptable under C-11 if the build is GPL, or must it be LGPL-only? Which build does the lab use? (8)
12. **Q11:** For resumable upload, do we write the tus protocol in FastAPI or use a separate tus server? (8)
13. **Q12:** Which S3 client library is allowed, and under which licence? (8)

**Security and privacy**
14. **Q13:** Does the Video module need no Moodle service-account token (SEC-03)? (9)
15. **Q14:** May lesson audio go to a hosted speech provider in production, and what must the data map say? (9)
16. **Q15:** How long is `shared.audit_log` kept, and is the LTI `sub` allowed in it for that period? (9)

---

## 2. The answers table (as it was in section 12 of the design)

### Guide's answers (2026-11-19, PR #140)

The answers address the questions Q1–Q16 and the sections they name; they are not the design approval.

| # | Answer | Where it is applied |
|---|---|---|
| Q1 | Yes: `video.job` and `video.step` in PostgreSQL, claimed with `SKIP LOCKED`; no queue product. | §3, §7 |
| Q2 | Yes: a separate `bbb-poll` worker that only enqueues. | §3, §7 |
| Q3 | Yes: workers use the storage adapter only; a remote worker needs S3, or a shared mount for local storage. | §3, §7 |
| Q4 | Confirmed as proposed: columns, states and routes; chapter edits change titles only; re-process is administrator-only. | §5, §6 |
| Q5 | `source.kind` is `bbb`; omit `uploaded_by`; `created_by_sub` is null for intake. | §4, §5 |
| Q6 | Yes: `.trash/` with a 30-day restore, and the proposed CLI with `--dry-run`, `--check`, `--config`; every command has its undo. | §6, §7 |
| Q7 | Plain SQL `up`/`down` scripts with a small runner; no ORM or migration product. | §5, §8 |
| Q8 | Keep `FEATURE_LOWRES_360P=false` (existing name); `FEATURE_SLIDE_INDEX=true`; `FEATURE_SUMMARIES=false`; add only `FEATURE_BBB_INTAKE=false`. | §6 |
| Q9 | Same as #98: record the non-secret lab facts (no IPs, VM addresses or credentials); the engine stays PENDING until recorded. *Update 2026-11-23: the guide parked this until the lab speech endpoint exists (PR #98, merged).* | §4 |
| Q10 | Separate ffmpeg process, never linked; an LGPL build, no GPL-only parts; send the lab image's `ffmpeg -version` configuration before relying on it; H.264/AAC must be possible from the LGPL build; record version and configuration in the decision record and release notes. | §8 |
| Q11 | A separate `tusd` server; verify its licence before adding it; do not write the tus protocol in FastAPI. | §3, §8 |
| Q12 | `boto3`; verify the licence and pin it. | §8 |
| Q13 | No Moodle service-account token; the module calls no Moodle web service. | §9 |
| Q14 | A hosted production provider stays open; if chosen, lesson audio may go under SEC-07 and the data map. B8.5 audio never goes to a hosted provider. | §9 |
| Q15 | `shared.audit_log` kept 90 days, including the LTI `sub`; record it in the data map. | §9 |
| Q16 | App-C 9 is in scope: Student 4 checks Moodle 5.3's own AI features for overlap with chapters and summaries. | §12 |

---

## 3. The guide's full reply on PR #140 (2026-11-19)

Guide's assistant (AI): answers to Q1-Q16 in the Video design.

**Architecture.**
Q1. Yes: `video.job` and `video.step` in PostgreSQL, claimed with `SKIP LOCKED`; no queue product.
Q2. Yes: a separate `bbb-poll` worker that only enqueues.
Q3. Yes: workers use the storage adapter only; a remote worker needs S3 or a shared mount for local storage.

**Data model and API.**
Q4. Confirmed as proposed: the columns, states and routes; chapter edits change titles only; re-process is administrator-only. The design approval is separate.
Q5. `source.kind` is `bbb`; omit `uploaded_by` (B6.3 requires only `kind`); `created_by_sub` is null for intake.

**Undo and migrations.**
Q6. Yes: `.trash/` with a 30-day restore, and the proposed CLI with `--dry-run`, `--check`, `--config`; every command has its undo.
Q7. Plain SQL `up`/`down` scripts with a small runner; no ORM or migration product.

**Flags.**
Q8. Keep `FEATURE_LOWRES_360P=false` (the existing name; do not add `FEATURE_VIDEO_LOW_RES`); `FEATURE_SLIDE_INDEX=true`; `FEATURE_SUMMARIES=false`; add only `FEATURE_BBB_INTAKE=false` as new.

**Speech.**
Q9. Same as #98: the lab facts were shared with the team; record the non-secret ones; no IPs, VM addresses or credentials. The engine stays PENDING until recorded.

**Media and libraries.**
Q10. Separate ffmpeg process, never linked. Use an LGPL build and no GPL-only parts; the lab image's `ffmpeg -version` configuration must be sent before relying on it. Many builds enable the GPL libx264; the H.264/AAC output for FR-V-03 and B6.2 must be possible from the chosen LGPL build. If the lab build is GPL, use an LGPL build or the guide decides the exception. Record the version and build configuration in the decision record and release notes.
Q11. Use a separate `tusd` server; verify its licence before adding it. Do not write the tus protocol in FastAPI.
Q12. Use `boto3`; verify the licence and pin it.

**Security and data.**
Q13. No Moodle service-account token; the module calls no Moodle web service.
Q14. Same as #98: a hosted production provider stays open; if chosen, lesson audio may go under SEC-07 and the data map. B8.5 audio never goes to a hosted provider.
Q15. Keep `shared.audit_log` for 90 days, including the LTI `sub`; record it in the data map.

**Scope.**
Q16. App-C 9 is in scope: Student 4 checks Moodle 5.3's own AI features for overlap with chapters and summaries.

The design stays Draft in this PR. Nagashree marks it In review when she is ready; only the guide sets Approved, in a pull request he merges. These answers address the Q1-Q16 questions and the sections they name.

Lesson: docs/design/video.md is Draft; Nagashree marks In review, the guide sets Approved; these answers address the open questions, not the approval.

# Draft additions to `docs/design/video.md` (C-09, UI baseline, OPS-11)

**Status:** draft text for the owner to read. Nothing here is in the repository yet. It is meant to go into `docs/design/video.md` in one small docs PR after #224 merges (same file). The design stays `Draft`; the C-09 part is written as a **proposal for the guide**, because how approval is recorded is a design decision, not a fact in the PRD.

Why these three: a scan of the design against PRD §C4, §A13 and §A14 found them missing. PRD C-09: "AI output is always a **draft** until a mentor approves it." PRD C4.4: the UI "meets A14". PRD OPS-11: "no module may require a local GPU to run".

---

## 1. C-09: AI output is a draft until a mentor approves it

**Where:** a new subsection at the start of §9 "Security and privacy" (after the SEC table), plus one sentence in the FR-V-05 and FR-V-13 rows of §2, two columns and one route in §5/§6, one row in §10, and a new question Q17 in §12.

### 1a. New subsection for §9

> **AI output is a draft until a mentor approves it [C-09]** (**Proposed**; how it is recorded is a question for the guide, Q17).
>
> The pipeline produces four kinds of AI output: the transcript and captions (speech, B5.4), the chapters (B5.1), the summary (B5.1, behind a feature flag) and, in the stretch release, checkpoint questions (FR-V-14, already mentor-approved only). Until a mentor approves them, the first three are drafts.
>
> - **Review state.** Each lesson has a review state, `draft` or `approved`, separate from its processing state (`ready` still means "processed", as in FR-V-10). A lesson becomes `draft` when processing finishes and again after every re-processing (FR-V-11). Editing a chapter title does not approve it.
> - **Approval.** A mentor of the lesson's course (or an administrator) approves from the lesson detail page. The approval records who and when, and writes an audit entry [OPS-06].
> - **No snippet before approval.** The embed snippet and path of FR-V-13 are given only for an approved lesson. Before that, the page says "AI draft, not reviewed: approve it to get the embed snippet", and the status list shows "ready (AI draft)".
> - **What this does not do.** It does not change B6: the manifest and the lesson folder stay as the contract says, so the review state lives in `video.lesson`, not in `lesson.json`. It does not stop someone who already knows a lesson's relative path from linking to it; it makes the mentor's approval the step that hands out the embed snippet.
> - **Summary.** `summary.en.md` follows the same rule; if the guide prefers, it is written to the lesson folder only after approval (Q17).

### 1b. Data model (§5), added to `video.lesson`

| Column | Type | Notes |
|---|---|---|
| `review_state` | text | `draft` or `approved`; set to `draft` when a job finishes (first run and every re-process) |
| `approved_by_sub`, `approved_at` | text null, timestamptz null | the approving mentor's LTI `sub` and the time; cleared on re-process |

### 1c. Route (§6)

| Route | Purpose | Allowed roles |
|---|---|---|
| `POST /lessons/{id}/approve` | Mentor approves the AI-generated captions, chapters and summary; sets `review_state` to `approved` [C-09] | Mentor (own course), Administrator |

And in the existing `GET /lessons/{id}/snippet` row: "refused with a clear message until the lesson is approved [C-09]".

### 1d. Row for §10 (error handling)

| Situation | Behaviour | Recovery |
|---|---|---|
| Snippet requested before approval | Refused: "This lesson is an AI draft. Check the captions and chapters, then approve it to get the embed snippet." | Review the lesson detail page, then approve |

### 1e. New question for §12 "Still open after the answers"

> - **Q17, how C-09 is met for captions, chapters and summary (proposed):** a `review_state` on the lesson and a snippet that is given only after a mentor approves (§9). The guide decides whether this is enough, or whether the AI files must stay out of the lesson folder until approval, which would change when `lesson.json` can be written (FR-V-08) and the 30-minute target for G-7.

**Tests to add in §11:** a unit test that a finished lesson is `draft`; that `snippet` is refused for a draft and returned for an approved lesson; that re-processing resets the state; that approval writes an audit entry. FR IDs: FR-V-05, FR-V-06, FR-V-13, FR-V-11.

---

## 2. UI baseline [PRD A14]

**Where:** a new short table at the end of the "Web/API" part of §6, and one row in §11.

### 2a. For §6

> **UI baseline (PRD A14; PRD §C4.4 says the UI "meets A14").** Proposed; nothing is built or measured.
>
> | ID | How the upload page, status list and lesson detail meet it |
> |---|---|
> | UI-01 | Plain layout in a Bootstrap-compatible component style, so the adopting site can restyle it |
> | UI-02 | Works at 375×812, at 1366×768 (100 %, 125 % and 150 % zoom) and at 683×768; no horizontal scrolling. Upload progress and the status list reflow to one column on the phone profile |
> | UI-03 | Keyboard operable end to end (upload, resume, retry, edit a chapter title, approve, copy the snippet); visible focus; labelled form fields; colour contrast at least WCAG 2.1 AA |
> | UI-04 | Status page with per-file and per-step progress; an operation can be left and resumed (FR-V-10, FR-V-01) |
> | UI-05 | Messages say what happened and what to do next (§10) |
> | UI-06 | The status list and lesson detail load in under 2 s on the lab network, excluding processing jobs |
> | UI-07 | English only; every user-facing string in one place in the module |

### 2b. Row for §11 (test plan)

| Level | What is tested | Test data | Requirement IDs |
|---|---|---|---|
| End-to-end (browser) | The mentor flow in Playwright (the stack's browser tool) at the three PRD screen profiles and the three zoom levels: no horizontal scroll, a keyboard-only path through upload, status, lesson detail and snippet, visible focus. An automated contrast and labels check for WCAG 2.1 AA (tool and licence chosen and checked first, CLAUDE.md §2.10). Page load under 2 s measured on the lab network | Lab Moodle sites [§A11]; test videos only | UI-01 to UI-03, UI-06 [§A14]; FR-V-10, FR-V-13 |

---

## 3. OPS-11: no local GPU required

**Where:** one sentence in §7 "Key decisions and alternatives" (or at the start of the AI part of §3).

> **No Video step requires a local GPU [OPS-11].** Transcription and chapters go through B5, to a local or a hosted provider chosen by configuration; ffmpeg transcode, poster and scene detection run on CPU. A hosted production provider stays an open guide decision (Q14), and no B8.5 audio goes to a hosted provider.

---

## What I could not decide for you

- **The C-09 gate (Q17) is the one that may need the guide.** The draft takes the lightest option that does not change the B6 contract or the 30-minute target: approval hands out the embed snippet. A stricter option keeps the files out of the lesson folder until approval.
- **The UI claims are proposals.** Nothing is built, so none is measured; the text says so.
- **Where to put each piece** follows the template's section order. Say if you want it elsewhere.

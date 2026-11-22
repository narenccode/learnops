# 0012. App-C item 9: which AI features Moodle 5.3 itself provides

**Date:** 2026-11-22
**Status:** **Source-checked; NOT verified on the lab Moodle 5.3 site.** This record reads Moodle's own
source for the 5.3 stable branch. Nobody has yet looked at the lab site's admin settings, so what is
installed and switched on there is not recorded. No scope change is decided here; the guide decides.
**Owner:** Student 4 (Video), as the guide set on draft PR #140 (Q16)
**Requirement:** PRD App-C item 9: "Which AI features Moodle 5.3 itself provides, so LearnOps doesn't
duplicate them (record any overlap and adjust scope)." App-C and §D1 assign item 9 to Release 0.
**Contracts touched:** none.
**Numbering:** `0011` is the B8.5 data-handling record, merged in PR #104; this record is `0012`.

## What was read, and how

Moodle's public source repository, branch `MOODLE_503_STABLE`, commit `1156a935ba44` (2026-11-17), whose
`public/version.php` says release `5.3.1+ (Build: 20261117)`. The Moodle documentation site refused
automated requests, so no documentation page was used. Everything below comes from files in that
commit, read with the GitHub API on 2026-11-22. Moodle is GPL software and is only read here
(C-01: Moodle is never modified).

## What Moodle 5.3 provides (from the source)

Moodle 5.3 has an AI subsystem in `public/ai`:

| Part | What the source shows |
|---|---|
| **Core actions** (`public/ai/classes/aiactions`) | Four: `generate_text`, `generate_image`, `summarise_text`, `explain_text`. Each takes a text prompt (the summarise action's constructor takes a user id, a context id and a prompt text). |
| **Placements** (`public/ai/placement`) | Two. `courseassist` lists `summarise_text` and `explain_text` (the language strings call them "AI summary" and "AI explain" of the page content). `editor` lists `generate_text` and `generate_image` (the text editor's "Generate AI content"). |
| **Provider plugins** (`public/ai/provider`) | Seven directories: `anthropic`, `awsbedrock`, `azureai`, `deepseek`, `gemini`, `ollama`, `openai`. |
| **Admin pages** | `configure.php`, `configure_providers.php`, `configure_actions.php`, `policy_acceptance_report.php`, `usage_report.php`: the administrator configures providers and actions, and there is a policy acceptance report and a usage report. |

**Not found:** no speech-to-text or transcription action, no video or audio action, and no action that
produces chapters, captions or a slide index. A GitHub code search for "transcribe" under
`public/ai` returned no result, and the four-action list above is complete for the core.

## Overlap with LearnOps

| LearnOps item | Moodle 5.3 | Overlap and what it means |
|---|---|---|
| FR-V-04 captions and transcript (speech to text) | None | **None.** |
| FR-V-05 chapters | None | **None.** |
| FR-V-06 summary of a lesson (draft file `summary.en.md`, mentor-approved, C-09) | `summarise_text` summarises the **text it is given** (in the `courseassist` placement, the course page content), on demand, inside Moodle | **Same kind of capability, different place and purpose.** Moodle's runs live, for a learner or teacher, on text in Moodle; the pipeline writes a draft file from a **video transcript** for a mentor to approve before it reaches learners. It does not replace FR-V-06 and no scope change is proposed for Video. Whether a mentor could instead ask Moodle to summarise a transcript pasted into a Page is outside this record. |
| FR-S (Course Studio, Module 1): generating course text | `generate_text`, `generate_image` in the editor | **Possible overlap for Module 1**, not for Video. Recorded for the Module 1 owner and the guide; this record does not decide it. |
| Model and speech providers (`libs/model_interface`) | Seven provider plugins configured in Moodle | **No conflict.** LearnOps does not use Moodle's AI subsystem (C-02 allows only backup and restore, web services, LTI and a browser) and keeps its own provider interface (C-10). |

## Proposed outcome (for the guide)

- **Video scope: no change proposed.** The Video features work on transcripts and video, which Moodle 5.3 does not offer.
- **Module 1:** the guide or the Module 1 owner decides whether Course Studio's text generation duplicates the editor's "Generate AI content".
- **Moodle's AI features are an administrator's choice** and may be off or unconfigured on a given site; LearnOps must not assume them (EXT-04).

## Still to do (this record is incomplete until then)

1. Someone with administrator rights on the **lab Moodle 5.3 site** checks Site administration, AI: which
   providers and placements are installed and enabled, and which Moodle build the site really runs. Record
   the result here without any address or credential.
2. Confirm the same on any production-like 5.3 site the guide names.
3. The guide approves or changes the proposed outcome.

## What this record does not claim

It does not say the lab site has these features switched on, that they work, or that Moodle 4.5 has them
(PRD C-03 still requires both versions; the AI subsystem on 4.5 was not read). It does not measure the
quality of any Moodle AI output.

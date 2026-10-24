# Module 3 — Grading assistant (owner: Student 3; also owns the model interface)

Adds to the root `CLAUDE.md`; never overrides it. Spec: PRD §C3. Release 0 (model and speech interfaces), Release 4 (grading assistant, comparison report).

## Scope
FR-G-01…08; FR-M-01…03.

## Contracts
- **Owns:** B4 Moodle web-services usage (and `libs/moodle_ws`), B5 model and speech interface (and `libs/model_interface`). Changes only via `/contract-change`.
- **Uses:** B1 marking tables, B3 LTI, B8.4 and B8.6 test sets.

## Module rules
1. **Draft-only.** Write to Moodle only drafts a mentor approved, with marking-workflow state `readyforrelease`. Never `released`. Never write unapproved drafts.
2. **Untrusted code runs only in the sandbox** (PRD §C3.5): one container per submission, no network after clone, non-root, 2 CPU / 2 GB / 10 min, read-only base, destroyed after use, on a host with no other LearnOps service. Never run learner code anywhere else, including your own machine.
3. Only the machine checks listed in PRD §C3.5 exist; unknown check names are errors.
4. Every draft shows its evidence (check results, quoted lines); no score without evidence.
5. Only the web-services functions listed in B4, with the service account's minimum capabilities. The token lives in the environment only.
6. Model interface: validated structured output; one retry on invalid output, then a clear error; log `meta` (tokens, latency, cost, prompt version) but never raw learner content. Prompts are versioned files.
7. The comparison study uses the fixed set B8.6 and the same prompts for every provider.

## Typical commands
`grading fetch --course <id> [--dry-run]` · `grading draft --assignment <id>` · `grading write --approved-only [--dry-run]` · `model-bench run --set b8.6 --provider local|hosted`

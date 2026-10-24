---
description: First-pass review of a module's design document against the PRD, contracts and template (read-only)
argument-hint: <module: studio | checker | grading | video>
---

Review `docs/design/$ARGUMENTS.md` and give the reader a **one-page verdict**. This is a first pass
to save a human's time; it is **not an approval**. **Change no file.** Never set `Status: Approved`.

1. Confirm `$ARGUMENTS` is one of `studio`, `checker`, `grading`, `video`, and that the document
   exists. If not, stop and say so.
2. Read: the document; `docs/design/TEMPLATE.md`; PRD Part A (§A7 constraints, §A9 extension rules,
   §A10 stack, §A12 operations, §A13 security); every contract in PRD Part B that this module owns or
   uses (table in §B.0); the module's chapter in PRD Part C and its releases in Part D;
   `modules/$ARGUMENTS/CLAUDE.md`; the root `CLAUDE.md`.
3. Check each item below. For every finding give the **document section** and the **PRD reference**,
   and classify it **Blocking** (must be fixed before approval) or **Advice** (worth fixing).

   **Completeness**
   - All 14 template sections are present and filled; no template instruction text is left; the
     header (module, owner, peer reviewer, releases, status) is complete.

   **Requirements**
   - Every requirement ID tagged for this module's releases in PRD Part C appears in §2 of the
     document, with an approach. List IDs that are missing, and IDs in the document that do not
     exist in the PRD.

   **Constraints and architecture**
   - Respects C-01…C-12 (no Moodle or BigBlueButton changes; only the allowed integration routes;
     Moodle 4.5 and 5.3; no secrets; relative media paths; AI output is a draft; model interface only).
   - Uses only the fixed stack; heavy work in workers (OPS-10); extension rules EXT-01…EXT-09 are
     not blocked by any choice.
   - No claim about how Moodle or BigBlueButton behaves unless it is supported by the PRD or listed in
     §12 as an open question to verify in the lab (Appendix C).

   **Contracts**
   - Only the contracts the PRD assigns to this module are provided or used; fields and functions
     referenced exist in the PRD text; no contract change is proposed without `/contract-change`.

   **Module-specific rules**
   - Every rule in `modules/$ARGUMENTS/CLAUDE.md` is met or explicitly addressed.

   **Security, privacy, operations**
   - Applicable SEC items covered; untrusted input contained; data stored or sent to AI providers is
     listed for the data map; every CLI has `--dry-run`, `--check` and an undo; every environment
     variable is listed for `.env.example`.

   **Libraries**
   - Each has a pinned version and a licence allowed by C-11 (MIT, BSD, Apache-2.0; LGPL only as an
     unmodified library). Flag any you cannot confirm.

   **Tests and measurements**
   - Every acceptance criterion in the PRD chapter (§C.x.7) is mapped to a test; every metric in the
     chapter has a stated way to measure it.

   **Work breakdown**
   - Pull requests are one requirement (or a tight group) each; the order respects dependencies;
     Release 0 foundation items are marked.

4. Output exactly this, and nothing longer than one page:
   - **Verdict:** `Ready for the guide's approval` or `Needs changes` (one line, with the number of
     Blocking items).
   - **Blocking:** numbered list (section, issue, PRD reference).
   - **Advice:** numbered list.
   - **Could not verify:** what you could not check from the repository (for example anything that
     needs the lab).
   - **For the human to decide:** two or three judgement calls only a person can make (scope,
     trade-offs, risk).
5. Remind the reader that this is a first pass and that the **guide** alone sets `Approved`.

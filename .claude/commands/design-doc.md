---
description: Draft a module's design document from the PRD, contracts and template (no code)
argument-hint: <module: studio | checker | grading | video>
---

Help the developer draft `docs/design/$ARGUMENTS.md`. This is design work: **write no code** and
change no file other than that one design document.

1. Confirm `$ARGUMENTS` is one of `studio`, `checker`, `grading`, `video`. If not, stop and ask.
2. Read, in this order: PRD Part A (§A7 constraints, §A9 extension rules, §A10 stack, §A13
   security), PRD Part B (every contract this module owns or uses, per the table in §B.0), the
   module's chapter in PRD Part C, PRD Part D (its releases), `modules/$ARGUMENTS/CLAUDE.md`, the
   root `CLAUDE.md`, and `docs/design/TEMPLATE.md`. If `docs/design/$ARGUMENTS.md` already exists,
   read it and improve it instead of starting over.
3. Before writing anything, show the developer a short outline: the requirements covered per
   release, the components you propose, the contracts used, and a list of **assumptions** and
   **open questions** (anything the PRD does not settle, and every PRD Appendix C item that needs
   the lab). **Wait for the developer's go.**
4. Then write the document, keeping the template's section numbers and filling every section.
   Rules:
   - Never invent a requirement, a contract field or a Moodle function. If you are unsure whether
     something exists, put it under §12 as an open question.
   - Design only inside the PRD's constraints (C-01…C-12) and the fixed stack. If a constraint
     seems to block the design, say so under §12; do not work around it.
   - Prefer the simplest design that meets the acceptance criteria; list alternatives you rejected
     in §7.
   - If you believe a contract needs a change, record it in §4 and §12 and stop; changes go
     through `/contract-change`.
   - Set `Status: Draft`. Never set `Approved`.
5. Finish with a checklist of what the developer must verify themselves before asking the peer
   reviewer to look at it, and remind them: **the developer owns this document** and must be able
   to explain every section.

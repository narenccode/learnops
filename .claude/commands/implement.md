---
description: Plan, then build and test one requirement (or tightly related group) in its own branch
argument-hint: <requirement id(s), e.g. FR-S-03>
---

Implement requirement(s) $ARGUMENTS following the project's plan-first process. Work in small
steps and **stop at each gate**.

## Gate 0: can this start?

1. Find each requirement ID in the PRD. Report its text, release and module. If an ID does not exist,
   stop and ask.
2. If it belongs to a module other than the developer's, say so and stop unless the developer
   confirms the owner agreed (cross-module changes must be listed in the PR).
3. Check that `docs/design/<module>.md` exists and contains `**Status:** Approved`. If not, stop:
   *"The design document for this module is not approved yet; feature code waits for it."* The only
   exception is **Release 0 foundation work** (contracts, shared libraries, CI, test data) when the
   guide has said so.
4. Check the working tree is clean and you are on a new branch named `<module>/<requirement-id>-<short-name>`
   (create it from an up-to-date `main` if needed). Never work on `main`.

## Gate 1: plan (no files changed yet)

Show the developer a plan with:
- the PRD acceptance criteria this work must satisfy;
- files to create or change (and confirmation that they are inside the developer's module and `libs/`
  only where the design document says so);
- tests to write first, with the data they use (`testdata/`);
- configuration variables, migrations and CLI flags involved (`--dry-run`, `--check`, undo);
- contracts touched (should be none; if one needs a change, stop and use `/contract-change`);
- anything unclear in the PRD or design document.

**Wait for the developer's go.**

## Gate 2: build, test first

1. Write the failing tests first; run them and show they fail for the right reason.
2. Implement the smallest change that makes them pass. Follow the root `CLAUDE.md` rules (§2 never-break
   rules, §4 architecture, §6 standards) and the module's `CLAUDE.md`.
3. Run the module's tests and show the output. Never claim something works without running it.
4. Update, in the same change: `docs/traceability.md` (requirement → test → demo step → Bloom level),
   `.env.example` if new variables are read, the module README, and `docs/data-map.md` if new data is
   stored or sent.
5. Run `/preflight` and fix what it reports.

## Gate 3: hand over

- Commit with a message that starts with the requirement ID(s).
- **Do not push.** Give the developer the push command and a pull request description using the
  repository's template, listing requirement IDs, evidence (test output) and any cross-module
  changes.
- State what was *not* done or not verified.

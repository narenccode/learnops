---
description: Run every check required before opening a pull request (definition of done)
---

Run the pre-PR checks for this repository and report results as a short table (check → pass/fail → detail).

1. `git status` and `git diff --stat main...HEAD`: list changed files; flag any change under `contracts/` or `docs/PRD.md` (needs `/contract-change`).
2. `pre-commit run --all-files` (formatting, lint, secret scan).
3. `ruff check .` and `mypy libs` for Python; `npx tsc --noEmit` and `npm run lint` in any changed front-end package.
4. `pytest` for every changed module and for `libs/`.
5. Contract validation: validate every file in `contracts/examples/` and any contract files the change produces against their schemas.
6. Requirement IDs: find the FR/NFR IDs this branch implements (branch name, commits, PR text); check each appears in `docs/traceability.md` with at least one test.
7. Configuration: if new environment variables are read in code, check they are in `.env.example` with placeholder values.

Do not fix anything automatically. Report failures with the exact command output, then ask the developer what to fix first.

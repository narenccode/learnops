# LearnOps starter kit: setting up the repository and each student's Claude Code environment

For the guide. Copy this folder's contents into the root of the new student repository, add the PRD
as `docs/PRD.md`, and follow the steps below. Nothing here contains secrets, hostnames or dates.

## 1. What is in the kit

| File | Purpose | Shared (committed)? |
|---|---|---|
| `CLAUDE.md` | Global rules for every contributor and every Claude Code session | Yes |
| `modules/*/CLAUDE.md` | Module rules, loaded automatically when Claude works in that folder | Yes |
| `contracts/CLAUDE.md` | Contract change rules, loaded when working in `contracts/` | Yes |
| `.claude/settings.json` | Team permissions (allow / ask / deny) and the guard hook | Yes |
| `.claude/hooks/guard.py` | Blocks secrets, `.env` edits, edits to Moodle/BigBlueButton code, `--no-verify`; asks before contract/PRD edits | Yes |
| `.claude/commands/preflight.md` | `/preflight`: all checks before a pull request | Yes |
| `.claude/commands/contract-change.md` | `/contract-change`: the PRD §B.0 process | Yes |
| `.claude/commands/release-check.md` | `/release-check N`: the PRD §D2 freeze checklist | Yes |
| `.gitignore`, `.editorconfig`, `.python-version`, `.nvmrc` | Hygiene and pinned versions (Python 3.12, Node 20) | Yes |
| `.env.example` | Every configuration variable, with placeholders | Yes |
| `.pre-commit-config.yaml` | Lint, format, private-key and secret scan (gitleaks), no commits to `main` | Yes |
| `.github/` | Pull-request template, code owners, CI workflow | Yes |
| `.claude/settings.local.json`, `CLAUDE.local.md`, `.env` | Personal overrides and secrets | **No** (git-ignored) |

## 2. Repository setup (guide, once)

1. Create the GitHub repository (public, Apache-2.0 licence file, README).
2. Copy the kit; add `docs/PRD.md`; create empty `docs/design/`, `docs/decisions/`, `docs/traceability.md`, `docs/data-map.md`, `testdata/README.md`.
3. `.github/CODEOWNERS` already has the team's GitHub usernames; update it if the team changes.
4. Branch protection on `main`: pull request required; 1 approval; **require review from code owners**; status check `ci` must pass; no force pushes; no deletions; include administrators.
5. Turn on GitHub **secret scanning** and **push protection**.
6. Add the students as collaborators (write access, not admin).

## 3. Each student (once, on their own machine or lab VM)

1. Their **own** Claude Code account (never shared), signed in with `claude` → login.
2. Install: Git, Python 3.12, Node 20, Docker, `pre-commit` (`pip install pre-commit`).
3. Clone the repository; run `pre-commit install`.
4. `cp .env.example .env`; fill only lab values given by the guide. Never commit `.env`.
5. Open Claude Code in the repository root, run `/memory` to confirm `CLAUDE.md` is loaded, and `/permissions` to see the team rules.
6. Run `/preflight` once on a clean checkout: everything should pass.
7. In their Claude account's privacy settings, decide on the model-training option (the code is open source, but the lab may contain test data the guide wants kept private).

Personal preferences (theme, model choice, extra allowed commands) go in `~/.claude/settings.json`
or `.claude/settings.local.json`, never in the shared `.claude/settings.json`. Project settings and
the deny rules in the shared file take precedence for safety.

## 4. Checking the guard works (guide, once)

Ask Claude in the repository to:
- write a file `test.py` that assigns `api_key` to a string starting with `sk-` followed by 30 random letters (let Claude make one up) → must be **refused**;
- edit `.env` → refused;
- edit a file under `/var/www/moodle/` on a lab VM → refused;
- edit `contracts/anything.json` → Claude must **ask** first.

## 5. Things that are easy to forget

| Item | Why it matters | Status |
|---|---|---|
| One Claude Code account per student; plan with enough usage for daily work | Terms of use; no waiting for a shared login | ☐ |
| GitHub branch protection + code owners + required CI | Without it, the rules in `CLAUDE.md` are advice only | ☐ |
| Secret scanning + push protection on GitHub | Second line of defence after the hook and gitleaks | ☐ |
| Same versions everywhere (Python 3.12, Node 20, Docker Compose v2) | "Works on my machine" problems | ☐ |
| Lab access for each student (VM accounts, network) and the lab AI service endpoints | Release 0 depends on it | ☐ |
| Hosted-API key with a hard spending cap, given outside the repo | Comparison study only | ☐ |
| Test data with licences or consent recorded in `testdata/README.md` | Legal; no real learner data | ☐ |
| A shared issue board (labels: module, release) | Tracking and traceability | ☐ |
| A short onboarding session: PRD walkthrough, `CLAUDE.md`, the three commands | Students follow the rules only if they know them | ☐ |
| Agreement that students don't add MCP servers or new tools without the guide | Keeps every environment the same | ☐ |
| Who updates this kit (the guide), and how changes are announced | Rules drift otherwise | ☐ |

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
| `.claude/commands/design-doc.md` | `/design-doc <module>`: draft a module's design document (no code) | Yes |
| `.claude/commands/review-design.md` | `/review-design <module>`: read-only first-pass review of a design document against the PRD, contracts and template, as a one-page verdict (the guide approves, never the command) | Yes |
| `.claude/commands/implement.md` | `/implement <FR-id>`: plan, test-first build and hand-over of one requirement, with an approved-design check | Yes |
| `docs/design/TEMPLATE.md` | The design-document template every module copies to `docs/design/<module>.md` | Yes |
| `docs/GETTING-STARTED.md` | Step-by-step handout for the students: links, setup, rules, first tasks per student, troubleshooting. Names are left out (the repository is public); keep it current | Yes |
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
2. Install: Git, Python 3.12, Node 20, Docker, `pre-commit` (`pip install pre-commit`), and **Claude Code 2.1.295 or later** (`claude --version`; run `claude update` if older; the guard's fail-closed setting needs it).
3. Clone the repository; run `pre-commit install`.
4. `cp .env.example .env`; fill only lab values given by the guide. Never commit `.env`.
5. Open Claude Code in the repository root, run `/memory` to confirm `CLAUDE.md` is loaded, and `/permissions` to see the team rules.
6. **Check your own settings don't turn hooks off.** Open `~/.claude/settings.json` (on Windows `C:\Users\<you>\.claude\settings.json`). It must **not** contain `"disableAllHooks": true`, which switches off every hook on your machine, including this project's guard. (This happened on the guide's own PC during the first check.) Run `/hooks` in Claude Code to see the project hook listed.
7. Run `/preflight` once on a clean checkout: everything should pass.
8. In their Claude account's privacy settings, decide on the model-training option (the code is open source, but the lab may contain test data the guide wants kept private).

Personal preferences (theme, model choice, extra allowed commands) go in `~/.claude/settings.json`
or `.claude/settings.local.json`, never in the shared `.claude/settings.json`. Project settings and
the deny rules in the shared file take precedence for safety.

## 4. Checking the guard works (guide, once)

Start Claude Code in the repository. If your own settings turn hooks off, start it with
`claude --settings '{"disableAllHooks": false}'` for this check. Then ask:
- "Use the Write tool to create `test.py` with exactly this content: `api_key = "sk-"` followed by 30 letters" (**type the 30 letters yourself** in the prompt) → must be **refused** with the guard's message ("…would write an API key…");
- "Use the Write tool to create a file named `.env` with the content `X=1`" → refused (Claude may also refuse on its own, citing CLAUDE.md; that still proves the rules, but only the first check proves the hook);
- edit a file under `/var/www/moodle/` on a lab VM → refused;
- edit `contracts/anything.json` → Claude must **ask** first.

**What the guard can and cannot see.** It reads what a tool call contains. A secret that a command
builds *while it runs* (for example a one-line script that prints a random key into a file) leaves no
key text in the command, so the guard cannot catch it. That case is caught when the file is
committed or pushed: by `pre-commit` (gitleaks), by the CI check and by GitHub push protection.
The guard is a safety net, not the only layer.

**Fail closed.** If the guard cannot start (for example no working Python on the machine) or hits an
internal error, the action is **blocked** with a message instead of silently allowed. If every edit
suddenly fails with "LearnOps guard: no working python found", install Python 3.12 and make sure
`python` or `python3` works in Git Bash.

## 5. Things that are easy to forget

| Item | Why it matters | Status |
|---|---|---|
| One Claude Code account per student; plan with enough usage for daily work | Terms of use; no waiting for a shared login | ☐ |
| GitHub branch protection + code owners + required CI | Without it, the rules in `CLAUDE.md` are advice only | ☐ |
| Secret scanning + push protection on GitHub | Second line of defence after the hook and gitleaks | ☐ |
| Same versions everywhere (Python 3.12, Node 20, Docker Compose v2, Claude Code 2.1.295+) | "Works on my machine" problems | ☐ |
| No student has `"disableAllHooks": true` in their own Claude settings | It silently switches the guard off (SETUP §3 step 6) | ☐ |
| Lab access for each student (VM accounts, network) and the lab AI service endpoints | Release 0 depends on it | ☐ |
| Hosted-API key with a hard spending cap, given outside the repo | Comparison study only | ☐ |
| Test data with licences or consent recorded in `testdata/README.md` | Legal; no real learner data | ☐ |
| A shared issue board (labels: module, release) | Tracking and traceability | ☐ |
| Review bot (`.github/workflows/pr-review.yml`): rule checks on every update, then an AI review after ONE peer approval; it posts a comment, a label and the commit status `guide-bot`. To switch it on: (1) Settings → Secrets and variables → Actions: secret `DEEPSEEK_API_KEY` (value typed by you, never in chat) and variable `DEEPSEEK_MODEL` (the model ID from your DeepSeek account); (2) merge the PR and let one student PR run it once (it creates the five labels itself); (3) only then add `guide-bot` as a required status check in the `main` ruleset. Your own PRs get `guide-bot` = success automatically. Break-glass if the bot or DeepSeek is down: your admin bypass for pull requests. Weekly: spot-check merged PRs (`gh pr list --state merged --limit 20`) | The guide only sees `rule-violation` and `needs-judgement`; routine PRs merge on peer approval plus a passing bot | ☐ |
| A short onboarding session: PRD walkthrough, `CLAUDE.md`, the six commands (`/preflight`, `/contract-change`, `/release-check`, `/design-doc`, `/review-design`, `/implement`) | Students follow the rules only if they know them | ☐ |
| You set `**Status:** Approved` in each design document yourself (a convention, not enforced by GitHub) | `/implement` stops until it sees that line | ☐ |
| Agreement that students don't add MCP servers or new tools without the guide | Keeps every environment the same | ☐ |
| Who updates this kit (the guide), and how changes are announced | Rules drift otherwise | ☐ |

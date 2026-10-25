# LearnOps — Getting started (read this first)

**For:** the four student developers. **From:** your project guide. Keep this file up to date as the project changes.
**Everything you need is in one repository:** https://github.com/narenccode/learnops

This file tells you, step by step, what to do, in what order, and what each of you does first.
Nothing here replaces the PRD; the PRD is the specification, and this is your road map.

---

## 1. Your links

| What | Where |
|---|---|
| **Repository** | https://github.com/narenccode/learnops |
| **PRD** (the specification for all four modules) | https://github.com/narenccode/learnops/blob/main/docs/PRD.md |
| **Setup guide** | `SETUP.md` in the repository (your part is §3) |
| **Project rules for you and for Claude Code** | `CLAUDE.md` (root), plus one `CLAUDE.md` in each module folder |
| **Design-document template** | `docs/design/TEMPLATE.md` |
| **Presentation outline** | the pre-project brief (a separate file from your guide) |

## 2. Your team

| # | GitHub | Your module | Your peer reviewer |
|---|---|---|---|
| Student 1 | `Akshita21-09` | **Course Studio** (PRD §C1) | `shraddha0103` |
| Student 2 | `shraddha0103` | **Course checker, role tests, integration harness** (§C2). You are also the **integration lead**. | `Akshita21-09` |
| Student 3 | `Harshithamanjunatha` | **Grading assistant + model interface** (§C3) | `vnaags` |
| Student 4 | `vnaags` | **Video pipeline** (§C4) | `Harshithamanjunatha` |

Your peer reviewer reads and approves your pull requests; you do the same for them. The guide
approves anything that touches the PRD, `CLAUDE.md`, `.claude/` or `.github/`.

---

## 3. Step-by-step setup (do these in order; about 1–2 hours)

### Step 1. Accept the repository invitation
GitHub emailed you an invitation to `narenccode/learnops`. Accept it from the email, or open
https://github.com/narenccode/learnops/invitations while signed in as the account in the table
above. Until you accept, you cannot push.

### Step 2. Install the tools

| Tool | Version | Needed |
|---|---|---|
| Git (with Git Bash on Windows) | current | now |
| Python | **3.12** | now |
| `pre-commit` | current (`python -m pip install pre-commit`) | now |
| Claude Code | **2.1.295 or later** (check with `claude --version`; update with `claude update`) | now |
| Node.js | **20** | from Release 0 |
| Docker (Desktop on Windows/Mac, Engine on Linux) with Compose v2 | current | from Release 0 |

Install Claude Code by following the official instructions at https://code.claude.com/docs.
**Use your own Claude account. Never share a login.**

On Windows, run every command in this guide in **Git Bash**.

### Step 3. Tell Git who you are

**ON YOUR COMPUTER (Git Bash):**

```bash
git config --global user.name "Your Name"
git config --global user.email "YOUR-ID+YOUR-GITHUB-USERNAME@users.noreply.github.com"
```

Your private GitHub address is on https://github.com/settings/emails (use the one ending
`@users.noreply.github.com`), so your real email isn't published in the project history.

### Step 4. Clone the repository and turn on the safety checks

**ON YOUR COMPUTER (Git Bash):**

```bash
git clone https://github.com/narenccode/learnops.git
cd learnops
python -m pip install pre-commit
pre-commit install
cp .env.example .env
```

- `pre-commit install` makes every commit run formatting, lint and a secret scan.
- `.env` is for your local settings. **Never commit it** (Git ignores it). Put only values your
  guide gave you in it. At the start, leave the placeholders.

### Step 5. Check that your own Claude settings do not switch hooks off  **(important)**
Open `~/.claude/settings.json` (on Windows `C:\Users\<you>\.claude\settings.json`). It must **not**
contain `"disableAllHooks": true`. That setting silently turns off the project's safety guard on
your computer. If it is there, remove it, or ask your guide.

### Step 6. Open Claude Code in the repository and check the setup

**ON YOUR COMPUTER (Git Bash):**

```bash
cd learnops
claude
```

- If it asks whether you trust the folder: **yes**.
- If it offers **browser tools**: **no**. The project doesn't use them.

Then type these inside Claude Code and look at the answers:

| Command | You should see |
|---|---|
| `/memory` | the root `CLAUDE.md` loaded |
| `/permissions` | the team's allow / ask / deny rules |
| `/hooks` | one `PreToolUse` hook (the guard) |

Run `/preflight`. On a fresh clone everything should pass.

### Step 7. Your first pull request: your design-document skeleton
This is a practice run of the whole workflow. Use your module name: `studio`, `checker`,
`grading` or `video`.

**ON YOUR COMPUTER (Git Bash):**

```bash
git switch -c <module>/design-doc-skeleton
cp docs/design/TEMPLATE.md docs/design/<module>.md
```

Open `docs/design/<module>.md` and:
1. delete the grey instruction block at the top;
2. fill in the header: module, owner (you), peer reviewer, release(s), and keep `**Status:** Draft`;
3. fill in §1 (Purpose and scope) in your own words after you have read your PRD chapter.

**ON YOUR COMPUTER (Git Bash):**

```bash
git add docs/design/<module>.md
git commit -m "Design document skeleton for <module>"
git push -u origin <module>/design-doc-skeleton
```

Git prints a link. Open it, click **Create pull request**, and fill in the checklist. Then:
1. wait for the **checks** to turn green;
2. ask your **peer reviewer** to review;
3. when they approve, click **Squash and merge**.

You cannot push to `main` directly: it is protected, on purpose.

### Step 8. Read the PRD (take your time; this is the real start of the project)
Read in this order. Make a list of anything unclear and send it to your guide (§8 below).

1. **Part A, all of it.** The problem, goals, users, the rules you can never break (§A7, C-01…C-12), the extension architecture (§A9), the fixed stack (§A10), security (§A13).
2. **Part B, all of it.** The shared contracts: the exact formats and interfaces between modules. All four of you depend on every one of these.
3. **Your own module chapter in Part C**, every heading.
4. **Part D** (the releases) and **Part E** (how it is tested).
5. The other three module chapters, quickly, so you know what depends on you.
6. The appendices, especially Appendix C: things to verify once the lab exists.

---

## 4. How we work

### The rules you can never break (the short version; the full list is in `CLAUDE.md` §2)
1. **Never modify Moodle or BigBlueButton.** No plugins, themes, patches or database edits. Connect only through Moodle backups, Moodle web services, LTI 1.3, a browser (tests), and BigBlueButton's API.
2. Everything must work on **Moodle 4.5 and 5.3**.
3. **No secrets in the repository.** No API keys, tokens or passwords in code, tests, docs or logs. Use environment variables, and document them in `.env.example`.
4. **Test data only.** No real learner data, real course content or real recordings.
5. **AI output is always a draft** until a mentor approves it. Tools never release grades.
6. All AI calls go through the shared model interface; never call a provider directly from a module.
7. Store media as **relative paths** only, never full URLs.
8. Every command-line tool has `--dry-run`, `--check` and a documented undo.

### Branches and pull requests
- Never commit to `main`. One branch per task: `<module>/<short-name>` (for a requirement: `<module>/<FR-id>-<short-name>`).
- Commit messages start with the requirement ID when there is one, e.g. `FR-S-03: validate marking table`.
- Every pull request: requirement IDs listed, `/preflight` passing, tests added, `docs/traceability.md` updated, your peer reviewer approved. The reviewer **runs the tests**, not just reads the code.
- Merge with **Squash and merge** only.
- **The rule-check bot.** Within a minute of opening or updating a pull request, a bot comments with a verdict and adds a label: `ready-for-guide`, `needs-rework`, `rule-violation` or `needs-judgement`. Fix the items it lists and push again (editing the description also re-checks). It checks rules only (requirement IDs, contracts, design-document status, tests, secrets), not code quality, and it never approves anything: **peer review and the guide's decision are still required.** Draft pull requests are skipped, so open one as a draft while you are still working.

### Contracts (PRD Part B)
- Until Release 0 is frozen, each owner creates their contract files in `contracts/` through a normal pull request that **all four of you approve**. Claude Code will ask permission before it touches `contracts/`; approve it when that is really your intention.
- After the freeze, contracts change only through `/contract-change` (additive and optional only).
- Never change a contract as a side effect of other work.

---

## 5. Using Claude Code the right way: design first, then build

1. **Contracts first, then design.** Draft your contracts, review each other's, then write your design document.
2. **Draft your design document with `/design-doc <module>`.** Claude shows an outline first. Read it, correct it, then let it write. **You own the document**: you must be able to explain every line to your reviewer and your guide.
3. **Design approval.** Your document goes `Draft` → `In review` (your peer) → `Approved`. **Only your guide sets `Approved`.** Before you ask your peer to look at it, run `/review-design <module>` on your own document and fix the blocking items it lists; your peer and your guide will run it too.
4. **Build one requirement at a time with `/implement <FR-id>`.** It stops if your design document is not approved. Release 0 foundation work (contracts, shared libraries, CI, test data) is allowed earlier when your guide says so.
5. **Use plan mode** for anything bigger than a small fix, and read the plan before approving it.
6. **Never trust a reference Claude gives you.** AI tools invent citations. Open and verify every reference before it goes into a document or the presentation.
7. **Don't add MCP servers or new tools** without your guide's approval. Every student's environment must stay the same.
8. **If the guard blocks something,** read its message. It is protecting a rule (a secret, `.env`, Moodle code, contracts). Don't try to work around it; ask your guide.

---

## 6. Your first two weeks: what to work on now

**No lab yet.** Moodle, BigBlueButton and the AI servers are being prepared for you. Until your guide
says the lab is ready: don't install Moodle or BigBlueButton on your own computer, and don't start
building module features. Work on contracts, design, and preparation.

### Everyone
- [ ] Setup steps 1–7 done; your design-document skeleton merged.
- [ ] PRD Parts A and B read; your own chapter read; your question list sent to the guide.
- [ ] Literature survey for **your** module (see the Bloom table in the brief): at least 6 sources, each opened and verified. Keep them in `docs/design/<module>.md` §12 or a `docs/literature-<module>.md`.
- [ ] Your contract pull requests opened (below), and the other three reviewed.
- [ ] Your part of the pre-project presentation prepared.

### Student 1 (`Akshita21-09`): Course Studio
1. **Contract B1: course package.** `contracts/course-package.v1.schema.json` plus valid examples in `contracts/examples/` (the PRD §B1 text is your starting point: structure, course pattern rules, marking-table format, protected activities and the two output modes).
2. **Contract B7: H5P practice output.** Draft `contracts/h5p-practice.v1.md`.
3. Study the Moodle backup (`.mbz`) format from the public documentation, and the limits of IMS Common Cartridge, for your literature survey.
4. Write the outline and content of the **4-week sample course** (test-data set B8.2) under `testdata/`.
5. Design document: `docs/design/studio.md` (use `/design-doc studio`).

First prompt to try in Claude Code: `/design-doc studio`

### Student 2 (`shraddha0103`): Course checker + integration lead
1. **Contract B2: course model.** `contracts/course-model.v1.schema.json` plus examples.
2. **Contract B3: LTI 1.3 launch.** `contracts/lti-launch.v1.md`, and a decision record `docs/decisions/0001-lti-library.md` comparing open-source LTI 1.3 Python libraries (maintenance, licence, features).
3. **The contract validation script** `libs/contracts/validate_examples.py`. The CI workflow already looks for it: it checks every example in `contracts/examples/` against its schema. Everyone's contract pull requests depend on this.
4. **Detail the rule catalogue** CK-01…CK-13 (PRD §C2.3) in your design document, with the list of planted errors for the test set B8.3.
5. As integration lead: at the end of week 1, run a **contract review session** with all four of you, and keep the list of decisions.
6. Design document: `docs/design/checker.md`.

First prompt to try in Claude Code: `/design-doc checker`

### Student 3 (`Harshithamanjunatha`): Grading assistant + model interface
1. **Contract B4: Moodle web-services usage.** `contracts/moodle-ws.v1.md`: the function list with parameters, the minimum capabilities, and which entries still need checking against Moodle 4.5 and 5.3 once the lab exists (PRD §B4, Appendix C).
2. **Contract B5: model and speech interface.** `contracts/model-interface.v1.schema.json` plus a **skeleton of `libs/model_interface/`**: the task registry, a local provider, a fake provider for tests, the versioned `prompts/` folder, structured-output validation, and unit tests. **No API keys anywhere.**
3. **Sandbox design** for running untrusted learner code (PRD §C3.5, SEC-04) in your design document.
4. Plan the **synthetic submissions** (test set B8.4): what a good, average and poor submission looks like; who will write reference grades.
5. Literature: automated assessment, LLM-as-grader studies, code similarity.
6. Design document: `docs/design/grading.md`.

First prompt to try in Claude Code: `/design-doc grading`

### Student 4 (`vnaags`): Video pipeline
1. **Contract B6: lesson manifest and media paths.** `contracts/lesson-manifest.v1.schema.json` plus examples, with the path template, the file list per lesson, and the reserved `camera` and `screen` track roles (PRD §B6). These make later extensions possible without rework; don't drop them.
2. **`libs/media_paths/`:** the path template, slug rules, a validator that rejects full URLs (relative paths only), and the media-signing interface with its `none` implementation (PRD §B6.4), all with unit tests.
3. Compare **speech-to-text options** for Indian-English lectures (accuracy, cost, licence, local vs hosted) in `docs/decisions/0002-speech-options.md`.
4. Plan the **lecture-video test set** (B8.5): ask faculty for short lectures recorded **with written consent**, and plan how reference transcripts will be made. Record each source and licence in `testdata/README.md`.
5. Read how BigBlueButton exposes recordings (its public documentation) for your literature survey.
6. Design document: `docs/design/video.md`.

First prompt to try in Claude Code: `/design-doc video`

---

## 7. Pre-project presentation: what to prepare

Use the brief your guide sent you. Each of you presents in this order:

1. **Problem statement**: the five problems and why they matter.
2. **Four objectives with the Bloom mapping**: your module's column of the table, phase by phase.
3. **Project brief**: the block diagram and the flow of a course through the tools; your module's place in it.
4. **Expected output**: your measured targets (PRD §A3) and what you will demonstrate.
5. **Roles and responsibilities**: who does what, including your contracts.

Your guide gives you the dates and your release commitments in person.

---

## 8. Asking questions and reporting progress

- **Anything unclear in the PRD:** open an issue in the repository titled `PRD question: …` and tell your guide. Do not guess, and don't change the PRD yourself.
- **A decision that affects the design:** write a short record in `docs/decisions/NNNN-title.md` (a few lines: decision, options, why).
- **Weekly:** a short stand-up with your guide (what is done, what is next, what is blocked), and your pull requests merged or in review.
- **Before asking for help:** run `/preflight`, read the error, and check §9 below.

## 9. If something goes wrong

| Problem | What to do |
|---|---|
| "Permission denied" or the invitation isn't in your email | Open https://github.com/narenccode/learnops/invitations while signed in as your GitHub account |
| `git push` is rejected for `main` | Expected. Create a branch and open a pull request |
| Every edit in Claude Code fails with "LearnOps guard: no working python found" | Python isn't on your path. Make sure `python --version` shows 3.12 in Git Bash, then restart Claude Code |
| The guard doesn't seem to run (a test secret is not blocked) | Check Step 5 (`disableAllHooks`) and `/hooks` |
| `pre-commit` fails on commit | Read the message; it usually fixes formatting itself. Run `git add -A` and commit again. If it flags a secret, remove it |
| CI (checks) is red | Open the failed run on the pull request page, read the first error, fix it, and push again |
| Claude Code asks to edit `contracts/`, `docs/PRD.md` or `.claude/` | That is the "ask" rule. Approve only if the change is intended and agreed; the PRD and rules are changed by your guide |
| A Claude Code command isn't found | Update Claude Code (`claude update`) and start it from the repository folder |
| You're not sure a change is allowed | Stop and ask your guide before doing it |

---

## 10. Your checklist for the end of week 1

- [ ] Invitation accepted, tools installed, `/preflight` passes on your clone
- [ ] Design-document skeleton merged; `disableAllHooks` checked
- [ ] PRD Parts A and B and your chapter read; questions sent
- [ ] Your contract pull requests open, with examples; the CI validation passes
- [ ] You have reviewed the other three students' contract pull requests
- [ ] Literature list started (each source verified)
- [ ] Presentation outline drafted

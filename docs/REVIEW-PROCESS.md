# LearnOps Review Handbook

**How your work is checked and added to the project. Written for someone who has never used GitHub.**

Read Parts 1 to 3 once, slowly. Then follow Part 4 each time you finish a piece of work. Part 8 is a
complete worked example. Part 9 lists what to do when something looks wrong.

Contents: 1 What and why · 2 Words you will meet · 3 Before you start · 4 The steps · 5 Reading the bot's comment ·
6 Being the peer reviewer · 7 The labels · 8 A worked example · 9 When something goes wrong · 10 Rules ·
11 Prompts for your Claude Code

---

## 1. What this is and why we do it

**GitHub** is a website that stores our project and remembers every change anyone ever made to it.
The project lives in one place called a **repository** ("repo"). Ours is called `learnops`.

The repository has a main copy called **`main`**. This is the official, working version of the project.
**Nobody ever changes `main` directly.** Instead:

1. You make your own copy of the work, called a **branch**, and do your changes there.
2. When your change is finished, you open a **pull request** (PR). A PR is a web page that says:
   "Please check my change, and if it is good, add it to `main`."
3. Your change is checked twice, then you add it to `main` yourself.

**The two checks**

| Check | Who | What it does |
|---|---|---|
| 1. The **review bot** | A program on GitHub | Checks the project rules within a minute, writes a comment, and puts a coloured **label** on your PR. After your peer approves, it also asks an AI for advice. |
| 2. Your **peer reviewer** | One team mate | Reads your change, runs the tests, and clicks **Approve** if it is good. |

**The guide** (your teacher) is **not** involved in normal work. The bot calls the guide only when a project
rule is broken or when a decision is needed. In that case the PR waits and the guide replies.

**Why so careful?** It stops mistakes reaching the project, it keeps every change explained and traceable, and it
teaches you the way professional teams work.

---

## 2. Words you will meet

| Word | Plain meaning |
|---|---|
| **Repository (repo)** | The project folder stored on GitHub. Ours: `learnops` |
| **`main`** | The official version of the project. Never edit it directly |
| **Branch** | Your own copy of the project to work in. One branch per task |
| **Commit** | A saved step of your work, with a short message that says what you did |
| **Push** | Sending your commits from your computer up to GitHub |
| **Pull request (PR)** | A web page on GitHub asking for your branch to be added to `main` |
| **Draft PR** | A PR marked "still working". The bot ignores drafts |
| **Ready for review** | The button that turns a draft into a normal PR and starts the checks |
| **Review bot** | The program that checks your PR. On GitHub it is called `github-actions` and has a grey **Bot** tag |
| **Peer reviewer** | The one team mate who reviews your PR (see the table in `docs/GETTING-STARTED.md`, section 2) |
| **Approve** | A peer's "yes, this is good" |
| **Label** | A coloured tag on the right side of the PR that tells you what to do next |
| **Check** | An automatic test run by GitHub. Shown as a green tick or a red cross |
| **Merge** | Adding your PR to `main`. We always use **Squash and merge**: all your small commits become one tidy entry |
| **Requirement ID** | A code like `FR-S-03` from the PRD. It says which requirement your work is for |

---

## 3. Before you start (one-time)

Do these once. If you followed `docs/GETTING-STARTED.md`, most are done.

- [ ] You accepted the invitation to the `learnops` repository (an email from GitHub; click **View invitation**, then **Accept invitation**).
- [ ] You can open `https://github.com/narenccode/learnops` and you are signed in (your profile picture shows at the top right).
- [ ] The project is on your computer (`git clone`, done in `GETTING-STARTED.md`, step 4) and `pre-commit install` was run there.
- [ ] **You get GitHub's emails.** Click your **profile picture** (top right) → **Settings** → **Notifications**. Under "Participating, @mentions and custom" tick **Email**. Then open the `learnops` page, click **Watch** (top right) and choose **Participating and @mentions**. The bot uses email to tell you what to do next.

---

## 4. The steps, one by one

The whole cycle for one piece of work. Steps 1 to 3 happen on your computer (in Claude Code or a terminal, in the
`learnops` folder). Steps 4 to 9 happen on **github.com** in your web browser.

### Step 1. Start from an up-to-date `main` and make your branch (computer)

```bash
git switch main
git pull
git switch -c studio/fr-s-03-validate-package
```

- The first two lines bring your copy of `main` up to date.
- The third creates your branch and moves you onto it. The name is `<module>/<short-description>`, for example
  `studio/fr-s-03-validate-package`.
- **Check it worked:** `git branch` shows your branch with a `*` in front.

### Step 2. Do the work and save it in commits (computer)

Work as normal (with Claude Code if you like). Save your progress often:

```bash
git add <the files you changed>
git commit -m "FR-S-03: validate the course package"
```

- Start the message with the requirement ID.
- Checks run automatically when you commit. If one fixes a file for you, the commit fails with a message: run
  `git add` on the files again and repeat the `git commit`. That is normal.

### Step 3. Send your work to GitHub (computer)

```bash
git push -u origin studio/fr-s-03-validate-package
```

- Use your own branch name. The `-u` is needed only the first time on a new branch. Later pushes are just `git push`.
- **Check it worked:** the terminal prints a long link ending in `/pull/new/...`. Your work is now on GitHub.
- **Do not push to `main`.** GitHub will refuse. That is correct.

### Step 4. Open a draft pull request (github.com)

1. Go to `https://github.com/narenccode/learnops`.
2. Click the **Pull requests** tab (below the repository name), then the green **New pull request** button.
   (Shortcut: after a push, a yellow bar saying "Compare & pull request" often appears on the repo page. Click it.)
3. Choose **base: main** on the left and **compare: your branch** on the right.
4. Click the green **Create pull request** button. **Wait.** Click the small **arrow ▾ on the right side of that
   button** and choose **Create draft pull request**. Then click the button.
5. The page has a form that is already filled in. Complete these:
   - **What and why:** one or two sentences about your change.
   - **Requirements:** the IDs, for example `FR-S-03`.
   - **Release** and **Module.**
   - **Checklist:** tick each box that is true. For a box that does not apply, tick it and add "N/A" and why. Do not tick what you have not done.
6. Click **Create draft pull request**.

**Check it worked:** your PR page opens with a grey **Draft** tag under the title. The bot ignores it for now.

Keep working. Every `git push` adds to the same PR.

### Step 5. Mark it ready (github.com)

When your work is finished:

1. Go to your PR (**Pull requests** tab, click your PR).
2. Scroll to the **bottom of the "Conversation" tab**. A box says **"This pull request is still a work in progress"**.
3. Click the green **Ready for review** button in that box.

The grey Draft tag disappears. The bot starts within a minute.

### Step 6. Read the bot's comment and act on it (github.com)

1. About a minute later, a new comment appears on your PR from **github-actions** with a grey **Bot** tag.
2. Its title is **Automated review**. Find the line that starts **Next step**. Do exactly what it says.
3. A coloured **label** also appears on the right side of the page, under **Labels**. Part 7 explains each.
4. If the comment lists problems under **Fix before merging**: fix them on your computer, then `git add`,
   `git commit` and `git push`. **The bot re-checks by itself** within a minute and updates its comment. You do not click anything.
   **Fix everything the comment lists first, then push once.** Do not push after every small fix (see the rule in Part 10).

Part 5 shows a real comment with each part explained.

### Step 7. Ask your peer reviewer to approve (github.com)

1. On your PR page, look at the right side under **Reviewers**. Several names may be listed (GitHub adds everyone who owns the files you changed). Your peer reviewer is one of them.
2. Tell your peer in your team chat: "My PR is ready: [link to your PR]". (The bot also reminds them by name if nothing happens for two days.)
3. They review it (Part 6 shows how) and approve. **One approval from one person is enough.** For design documents and other shared files in `docs/`, **any teammate who is free** can do it; it does not have to be your usual peer. For code inside a module, the approval must come from your peer reviewer (or the guide). The bot's **Next step** line tells you who can approve your PR.
4. **If you push new commits after they approved,** GitHub removes their approval (a safety rule). Ask them to look at the new changes and approve again.

### Step 8. Wait for the AI advice, if the label asks (github.com)

About a minute after your peer approves, the bot updates its comment with advice from an AI. Then the label changes:

- **`ready-to-merge`**: all done, go to Step 9.
- **`needs-rework`**: the AI found a real problem. Fix it (Step 6, point 4).

The AI **can be wrong**. If you disagree with an item, check it yourself and write a reply in a comment on the PR.

### Step 9. Merge (github.com)

Only when the label is **`ready-to-merge`**:

1. Scroll to the bottom of the **Conversation** tab.
2. The checks box must say **All checks have passed** with green ticks, including **guide-bot** and **ci / checks**.
3. Click **Squash and merge**, then **Confirm squash and merge**.
4. Your PR page turns purple and says **Merged**. If a **Delete branch** button appears, click it.

The button stays grey until everything is satisfied. That is not a fault. Read the box to see what is still missing.

### Step 10. Clean up (computer)

```bash
git switch main
git pull
git branch -d studio/fr-s-03-validate-package
```

Then go back to Step 1 for your next task.

---

## 5. Reading the bot's comment

This is the shape of a real comment. The text in brackets explains each part.

```
Automated review: Needs rework                       <- the verdict (matches the label)

Next step: Fix the items listed in the bot comment   <- DO THIS FIRST
and push. The bot re-checks by itself.

Fix before merging                                   <- must be fixed
- docs/design/studio.md: Section 2 lists no real     <- file and what is wrong
  requirement ... (PRD C1.3)                         <- where to read more

Better ways to do it (advice)                        <- optional ideas
- A checklist box is malformed ...

Could not verify                                     <- the bot could not check this
- Whether the full PRD defines goal G-1 ...             (it is not an error)

AI review: deepseek-flash, 6656 in / 1212 out        <- small print: the AI that gave the advice
Checked commit 567779e ...
```

How to use it:

- **Next step** first. Always.
- **Fix before merging:** all of these must be fixed before you can merge.
- **Advice:** read it. Fix it if you agree. You may leave it if you do not. Note why in a reply.
- **Could not verify:** nothing for you to fix. It means a person must check that part.
- The comment is **updated in place**. You will not get a new long comment after each push. When the verdict changes, the bot also writes one **short** comment that names you, and GitHub emails you.

---

## 6. If you are the peer reviewer

You review a team mate's PR and run its tests. This is the human check, and the AI does not replace it.

1. Open their PR (the link in your chat, or **Pull requests** tab → their PR).
2. **Read the description.** Does it say what was done and which requirement it covers?
3. Click the **Files changed** tab. Read what changed. Click a line's blue **+** to leave a comment on it.
4. **Run the tests on your own computer:**
   ```bash
   git fetch origin
   git switch their-branch-name
   ```
   then run `/preflight` in Claude Code. Return to your own work with `git switch your-own-branch`.
5. Click the green **Review changes** button (top right of the Files changed tab). Choose one:
   - **Comment**: notes only, no decision.
   - **Approve**: it is good. **Use this when you are satisfied.**
   - **Request changes**: something must be fixed first.
6. Click **Submit review**.

If you approve, the bot continues automatically. If you request changes, the label becomes `needs-rework`.

Review for: does it do what the requirement says; are there tests; does it break a rule in `CLAUDE.md`; would
someone else understand the code? Do not approve something you did not run or do not understand. Ask a question instead.

---

## 7. The labels

The label is on the right side of the PR page, under **Labels**. It is your signpost.

| Label | Meaning | What you do |
|---|---|---|
| `awaiting-peer` | The rule check passed | Ask a teammate who can approve to review (Step 7) |
| `needs-rework` | Something must be fixed | Read the bot comment, fix, push |
| `ready-to-merge` | Your peer approved and the bot is satisfied | **Squash and merge** (Step 9) |
| `rule-violation` | A project rule is broken | **Do not merge.** The guide decides and will reply |
| `needs-judgement` | A decision only the guide can make | **Do not merge.** The guide will reply |

Normal order for a good PR: `awaiting-peer` → `ready-to-merge`.

---

## 8. A worked example, start to finish

Maya (author) and Raj (her peer reviewer) work on requirement `FR-S-03`.

| When | Who | What happens |
|---|---|---|
| Monday 10:00 | Maya | `git switch -c studio/fr-s-03-validate`, writes code, commits, `git push -u origin ...` |
| Monday 10:20 | Maya | On GitHub: **New pull request** → **Create draft pull request**. Fills the form. Keeps working and pushing |
| Monday 15:00 | Maya | Work finished. Opens the PR, scrolls down, clicks **Ready for review** |
| Monday 15:01 | Bot | Comment appears: **Needs rework**. *Next step:* fix the items. Item: "no test file in this PR". Label `needs-rework` |
| Monday 15:30 | Maya | Adds a test, `git commit`, `git push` |
| Monday 15:31 | Bot | Comment updates to **Waiting for the peer review**. Label `awaiting-peer`. A short comment says: "@Raj, please review". Raj gets an email |
| Monday 17:00 | Raj | Opens the PR, **Files changed**, runs `/preflight`, clicks **Review changes → Approve → Submit review** |
| Monday 17:01 | Bot | The AI reviews. Comment updates: one piece of advice, no blocking items. Label `ready-to-merge`. A short comment: "@Maya the status is now Ready to merge" |
| Monday 17:05 | Maya | Opens the PR. The checks box shows green ticks. Clicks **Squash and merge → Confirm**. Done |
| Monday 17:06 | Maya | `git switch main`, `git pull`, `git branch -d studio/fr-s-03-validate` |

The guide did nothing. If at 15:01 the label had been `rule-violation`, Maya would stop and wait for the guide.

---

## 9. When something goes wrong

| What you see | What it means and what to do |
|---|---|
| **No bot comment after 5 minutes** | Is the PR still a draft? (Look for the grey Draft tag. Click **Ready for review**.) If it is not a draft, tell the guide |
| **Squash and merge is grey** | Something is still missing. Read the box above the button: it lists what (a check, the peer approval, the bot) |
| **My peer approved, but the label is still `awaiting-peer`** | Wait two minutes and refresh the page. If nothing changes, tell the guide |
| **My peer's approval disappeared** | You pushed after they approved. That is a safety rule. Ask them to approve again |
| **The bot blocks me and I am sure it is wrong** | Do not argue with it and do not try to trick it. At the bottom of your PR write a comment that starts with `@narenccode` and says: which bot item, why you think it is wrong, and your evidence (a PRD line or a test result). The guide is emailed and will either tell you what to change or approve the merge by hand. Keep working on something else meanwhile |
| **The bot says "No tests" or "traceability not updated" but my change only renames or tidies code** | In your PR description add a line `Refactor only: <one sentence on what you changed and why behaviour is the same>`. The bot then treats those two items as advice, and your reviewer must agree with your claim |
| **The bot comment says "The bot hit an internal error"** | It is the bot's fault, not yours. The guide has already been told. Carry on; the guide will reply or approve the merge by hand |
| **The bot says "AI review unavailable"** | The AI service is down or out of credit. The guide has been told and can run the review again by hand. If you do not hear back within a day, write a comment starting `@narenccode` |
| **`git push` says I cannot push to `main`** | Correct, nobody can. Make a branch (Step 1) and push that |
| **`git commit` fails and says files were modified** | Normal. A check tidied your files. Run `git add` on them again and repeat the `git commit` |
| **`git push` is rejected: "non-fast-forward" or "fetch first"** | Someone changed the branch. Run `git pull` and push again. If unsure, ask Claude (prompt below) before doing anything else |
| **The PR says "This branch has conflicts"** | Your branch and `main` changed the same lines. Ask Claude (prompt below) to help; do not guess |
| **Label is `rule-violation` or `needs-judgement`** | Do nothing except wait. The guide has been told. Do not merge |
| **The CI check (`ci / checks`) shows a red cross** | Click **Details**, read the first error in the log, fix it, push |
| **I clicked something by mistake** | Almost everything on GitHub can be undone. Do not worry. Tell the guide before you do anything else |

---

## 10. Rules to remember

- Never push to `main`. Always use a branch and a PR.
- Open the PR as a draft; click **Ready for review** only when finished.
- One piece of work per PR. Small is easier to review.
- **Push in sizeable batches, not tiny changes.** While your PR is a draft, push as often as you like: nothing is checked. After you click **Ready for review**, every push removes your peer's approval and starts a new AI review. So collect your fixes, check them yourself with `/preflight`, and push once. If you find a small mistake after your peer approved, fix it together with the next real change when you can, instead of pushing one line.
- **You** are responsible for your code. The bot and the AI can be wrong or miss things. Read every comment and test your change yourself.
- Your PR title, description and code are sent to an AI service called DeepSeek. The repository is public and uses test data only. **Never put passwords, keys or real learner data in a PR.**
- Design documents are marked `Approved` only by the guide.
- If the bot looks broken, tell the guide. Do not try to get around it.

---

## 11. Prompts for your Claude Code

Paste these into Claude Code, opened in the `learnops` folder. Replace the words in [brackets]. Always paste the
real bot comment or error; never describe it from memory. Never ask Claude to "make the bot pass": ask it to
explain and fix the real problem, and read every change before you commit it.

**Git steps, if you are unsure**
- "I finished the task [what you did]. Show me the exact git commands to commit it with a message starting with [FR-S-03], and push my branch. Explain each command in one line. Do not run them until I say."
- "My PR says 'This branch has conflicts'. Explain what that means. Then show me step by step how to bring in the latest `main` and fix the conflicts. Do not change any file until I say."

**Before you mark the PR ready**
- Run `/preflight`. It runs all the checks in one go.
- "Read my changes against `main`. Check them against `CLAUDE.md` section 2 and the PRD chapter for my module. List anything that breaks a rule, anything without tests, and anything unclear. Do not change any file."
- "Look at my changes against `main` and fill in `.github/pull_request_template.md`. Use real requirement IDs from the PRD. Mark a box N/A only if it truly does not apply, and say why. Do not tick anything you have not verified."

**When the bot comments**
- "Here is the review bot's comment on my PR: [paste it]. Explain each item in plain words, say which items block the merge and which are advice, and show me where each one applies in my files."
- "Fix the items under Fix before merging one at a time. After each fix show me the change and explain why it solves the problem. Do not touch anything else."
- "The bot says [item]. Check the PRD and my code and tell me honestly whether that is correct. Show the evidence."

**When you are the peer reviewer**
- "I am the peer reviewer for the branch [branch name]. Read the changes against `main`, check them against `CLAUDE.md` and the PRD, and run the tests. Give me a short list of what is wrong, what is risky, and what to ask the author. Do not edit any file."

**For design documents**
- `/design-doc [module]` writes a first draft. `/review-design [module]` checks it before you ask your peer.
- "Quiz me on my design document, one section at a time. Ask why I chose each approach and tell me when my answer does not match what I wrote."

**When you are stuck**
- "Here is the error: [paste it]. Explain the cause in plain words, check it against my code, and propose the smallest fix. Do not change anything until I say so."

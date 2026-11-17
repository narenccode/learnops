# LearnOps Review Handbook

**How your work is checked and added to the project. Written for someone who has never used GitHub.**

Read Parts 1 to 3 once, slowly. Then follow Part 4 each time you finish a piece of work. Part 8 is a
complete worked example. Part 9 lists what to do when something looks wrong.

Contents: 1 What and why · 2 Words you will meet · 3 Before you start · 4 The steps · 5 Reading the bot's advice ·
6 Being the peer reviewer · 7 Auto-merge · 8 A worked example · 9 When something goes wrong · 10 Rules ·
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
3. Your change is checked by the tests and by one teammate, then GitHub adds it to `main` by itself.

| Check | Who | What it does |
|---|---|---|
| 1. The **checks** | GitHub, automatically | Runs the tests, the format check and the secret scan. A red cross blocks the merge |
| 2. Your **reviewer** | One teammate | Reads your change, runs the tests, and clicks **Approve** if it is good |

The **review bot** also writes one comment with advice within a minute. It never blocks anything: your
reviewer decides what must change.

**The guide** approves design documents, reviews contract changes after Release 0 is frozen, and runs the
release checks. For everything else, ask your reviewer first. If you are still stuck, write it in the daily
check-in issue.

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
| **Draft PR** | A PR marked "still working". Nothing checks a draft |
| **Ready for review** | The button that turns a draft into a normal PR and starts the checks |
| **Review bot** | The program that checks your PR. On GitHub it is called `github-actions` and has a grey **Bot** tag |
| **Peer reviewer** | The one team mate who reviews your PR (see the table in `docs/GETTING-STARTED.md`, section 2) |
| **Approve** | A peer's "yes, this is good" |
| **Auto-merge** | A button on your PR. Once clicked, GitHub merges the PR by itself when it is approved and the checks pass |
| **Check** | An automatic test run by GitHub. Shown as a green tick or a red cross |
| **Check-in issue** | One pinned issue where each of us writes three lines a day: done, next, blocked by |
| **Merge** | Adding your PR to `main`. We always use **Squash and merge**: all your small commits become one tidy entry |
| **Requirement ID** | A code like `FR-S-03` from the PRD. It says which requirement your work is for |

---

## 3. Before you start (one-time)

Do these once. If you followed `docs/GETTING-STARTED.md`, most are done.

- [ ] You accepted the invitation to the `learnops` repository (an email from GitHub; click **View invitation**, then **Accept invitation**).
- [ ] You can open `https://github.com/narenccode/learnops` and you are signed in (your profile picture shows at the top right).
- [ ] The project is on your computer (`git clone`, done in `GETTING-STARTED.md`, step 4) and `pre-commit install` was run there.
- [ ] **You get GitHub's emails.** Click your **profile picture** (top right) → **Settings** → **Notifications**. Under "Participating, @mentions and custom" tick **Email**. Then open the `learnops` page, click **Watch** (top right) and choose **Participating and @mentions**. GitHub emails you when someone asks you to review or comments on your PR.

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

### Step 6. Read the bot's advice (github.com)

1. About a minute later a comment from **github-actions** appears, titled **Automated advice**.
2. Read the **Summary** and the **Next step** lines.
3. Fix the items under **Please fix** that you agree with. If you disagree with one, say why in a reply. The
   advice can be wrong; your reviewer decides.
4. Fix everything first, then push once. The comment updates itself after each push.

### Step 7. Ask one teammate to review, and turn on auto-merge (github.com)

1. On the right side under **Reviewers**, click the gear and pick your reviewer:
   - code inside a module: your peer (see `docs/GETTING-STARTED.md`, section 2);
   - documents in `docs/` and shared files: any teammate who is free;
   - a change in `contracts/`: an owner of a module that uses the contract (PRD §B.0 table). After
     Release 0 is frozen, the guide is also asked automatically.
2. Scroll to the bottom of the **Conversation** tab and click **Enable auto-merge**, then
   **Confirm auto-merge**. Choose **Squash and merge** if GitHub asks.
3. That is all. When the reviewer approves and the checks are green, GitHub merges your PR by itself and
   emails you.
4. If your reviewer requests changes: fix, push, and click **Re-request review** next to their name.
5. If GitHub says **This branch has conflicts**, click **Update branch** if it is offered, or ask Claude
   (prompt in Part 11). If it only says the branch is **out-of-date**, you do not need to do anything.

### Step 8. If nobody reviews within one working day

Ask another teammate who can approve (the bot's **Next step** line names them), and write it in the
check-in issue under **Blocked by**.

### Step 9. After the merge

Your PR page turns purple and says **Merged**. GitHub deletes the branch on github.com by itself.

### Step 10. Clean up (computer)

```bash
git switch main
git pull
git branch -d studio/fr-s-03-validate-package
```

Then go back to Step 1 for your next task.

---

## 5. Reading the bot's advice

```
Automated advice
This comment is advice. It never blocks merging.      <- always true
Summary: Please fix the items under Please fix ...    <- one line on the whole PR
Next step: Ask a teammate to review ...               <- who can approve, and auto-merge

Please fix                                            <- things the rule checks or the AI think are wrong
- docs/design/studio.md: Section 2 lists no real requirement ... (PRD C1.3)
Questions for your reviewer                           <- points a person should look at
Suggestions                                           <- optional ideas
Could not check                                       <- not an error; a person checks that part
```

- Read **Summary** and **Next step** first.
- The comment is updated in place after every push. It never names you, so it sends no email.

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

If you approve and the checks are green, the PR merges by itself. Review within one working day of being asked; start each work session with the reviews you owe.

Review for: does it do what the requirement says; are there tests; does it break a rule in `CLAUDE.md`; would
someone else understand the code? Do not approve something you did not run or do not understand. Ask a question instead.

---

## 7. Auto-merge

There are no labels to watch. GitHub shows the state of your PR in the box at the bottom of the
**Conversation** tab: **Review required**, **Changes requested**, **Some checks were not successful**, or
**Auto-merge enabled**. When the review and the checks are both done, the PR merges by itself.

---

## 8. A worked example, start to finish

Maya (author) and Raj (her peer reviewer) work on requirement `FR-S-03`.

| Step | Who | What happens |
|---|---|---|
| 1 | Maya | `git switch -c studio/fr-s-03-validate`, writes code, commits, pushes, opens a **draft** PR |
| 2 | Maya | Work finished: clicks **Ready for review** |
| 3 | Bot | Comment **Automated advice**: under **Please fix**, "no test file in this PR" |
| 4 | Maya | Adds a test, pushes once. The comment updates: "The rule checks found nothing to fix" |
| 5 | Maya | Picks Raj as reviewer and clicks **Enable auto-merge** |
| 6 | Raj | Opens **Files changed**, runs `/preflight`, clicks **Review changes → Approve → Submit review** |
| 7 | GitHub | The checks are green and Raj approved: the PR merges by itself. Maya gets an email |
| 8 | Maya | `git switch main`, `git pull`, `git branch -d studio/fr-s-03-validate` |

The guide did nothing, and nobody waited for a label.

---

## 9. When something goes wrong

| What you see | What it means and what to do |
|---|---|
| **My PR did not merge although it was approved** | Read the box at the bottom of the Conversation tab: a red check, a missing approval from an owner of one of the files, or auto-merge was not turned on |
| **The bot's advice is wrong** | Reply under it with one line saying why. Your reviewer decides. You do not need the guide |
| **No bot comment after 5 minutes** | Is the PR still a draft? If not, carry on: the advice is optional |
| **The bot says "No tests" or "traceability not updated" but my change only renames or tidies code** | In your PR description add a line `Refactor only: <one sentence on what you changed and why behaviour is the same>`. Your reviewer must agree with your claim |
| **`git push` says I cannot push to `main`** | Correct, nobody can. Make a branch (Step 1) and push that |
| **`git commit` fails and says files were modified** | Normal. A check tidied your files. Run `git add` on them again and repeat the `git commit` |
| **`git push` is rejected: "non-fast-forward" or "fetch first"** | Someone changed the branch. Run `git pull` and push again. If unsure, ask Claude (prompt below) before doing anything else |
| **The PR says "This branch has conflicts"** | Your branch and `main` changed the same lines. Ask Claude (prompt below) to help; do not guess |
| **The CI check (`ci / checks`) shows a red cross** | Click **Details**, read the first error in the log, fix it, push |
| **I clicked something by mistake** | Almost everything on GitHub can be undone. Do not worry. Tell the guide before you do anything else |

---

## 10. Rules to remember

- Never push to `main`. Always use a branch and a PR.
- Open the PR as a draft; click **Ready for review** only when finished.
- One piece of work per PR. Small is easier to review. Aim for about 800 changed lines or fewer.
- **Push in sizeable batches.** After **Ready for review**, each push runs the checks and the AI advice again (the AI advice runs at most five times per PR).
- **You** are responsible for your code. The bot and the AI can be wrong or miss things. Read every comment and test your change yourself.
- Your PR title, description and code are sent to an AI service called DeepSeek. The repository is public and uses test data only. **Never put passwords, keys or real learner data in a PR.**
- Design documents are marked `Approved` only by the guide.
- **At most two of your PRs are ready for review at the same time.** Finish (merge or close) one before you open the next. Drafts do not count.
- **Every PR starts from `main`.** Do not build a PR on top of another unmerged PR. If you need someone's unmerged work, review it first so it merges.
- **Review within one working day** when you are asked.
- **Write your check-in every working day** in the pinned check-in issue: done, next, blocked by.

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

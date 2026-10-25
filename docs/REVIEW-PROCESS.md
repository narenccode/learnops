# How your pull request is reviewed

One page. Keep it open the first few times you open a pull request (PR). The last section has
prompts you can paste into your own Claude Code.

## The steps

1. **Open your PR as a draft** while you are still working. The review bot ignores drafts.
2. **Click "Ready for review"** when you are done.
3. **The bot checks the rules** within a minute and writes a comment that ends with a **Next step** line. Fix what it lists and push; it re-checks by itself.
4. **Ask your one peer reviewer to approve.** One peer is enough. They run the tests, not just read the code.
5. **The AI reviews your change** right after the peer approves (DeepSeek). It gives advice; it cannot approve or merge.
6. **When the label is `ready-to-merge`, click "Squash and merge".** GitHub will not allow a merge before that.

## What the labels mean

| Label | What you do |
|---|---|
| `awaiting-peer` | Ask your peer to review |
| `needs-rework` | Fix the items in the bot comment and push |
| `ready-to-merge` | Squash and merge |
| `rule-violation` / `needs-judgement` | Do not merge. The guide decides and will reply |

## Remember

- If your PR waits too long, the bot reminds you or your peer. You do not need to chase anyone.
- Keep GitHub email notifications on for this repository.
- The AI can be wrong or miss things. **You** are responsible for your code: read the comments and test it yourself.
- Your PR title, description and code are sent to DeepSeek. The repository is public and uses test data only. Never put secrets or real learner data in a PR.
- Design documents are marked `Approved` only by the guide.
- If the bot seems broken, tell the guide. Do not work around it.

## Prompts for your Claude Code

Paste these into Claude Code in the `learnops` folder. Replace the words in [brackets]. Always paste the real bot comment or error; never describe it from memory. Never ask Claude to "make the bot pass": ask it to explain and fix the real problem, and read the change before you commit.

**Before you open the PR**
- `/preflight` runs all checks. Run it before every push.
- *Self-review:* "Read my changes against `main`. Check them against `CLAUDE.md` section 2 and the PRD chapter for my module. List anything that breaks a rule, anything without tests, and anything unclear. Do not change any file."
- *PR description:* "Look at my changes against `main` and fill in `.github/pull_request_template.md`. Use real requirement IDs from the PRD. Mark a box N/A only if it truly does not apply, and say why. Do not tick anything you have not verified."

**When the bot comments**
- *Understand it:* "Here is the review bot's comment on my PR: [paste]. Explain each item in plain words, say which items block the merge and which are advice, and show me where each one applies in my files."
- *Fix it:* "Fix the blocking items from that bot comment one at a time. After each fix show me the change and explain why it solves the problem. Do not touch anything else."
- *Question it:* "The bot says [item]. Check the PRD and my code and tell me honestly whether that is correct. Show the evidence. If the bot is wrong, I will tell the guide."

**When you are the peer reviewer**
- "I am the peer reviewer for the branch [branch name]. Read the diff against `main`, check it against `CLAUDE.md` and the PRD, and run the tests. Give me a short list of what is wrong, what is risky, and what to ask the author. Do not edit any file."

**For design documents**
- `/design-doc [module]` drafts it. `/review-design [module]` gives a first-pass verdict before you ask your peer. The guide alone sets `Approved`.
- *Check you understand it:* "Quiz me on my design document, one section at a time. Ask why I chose each approach and tell me when my answer does not match what I wrote."

**When you are stuck**
- "Here is the error: [paste]. Explain the cause in plain words, check it against my code, and propose the smallest fix. Do not change anything until I say so."

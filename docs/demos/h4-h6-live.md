# H4 and H6 — Grading, Tiers 2 and 3: the live read and the dry run

**Owner:** Harshitha
**Demo scripts:** `scripts/demos/demo_h4_live_read.py` (Tier 2), `scripts/demos/demo_h6_dry_run.py` (Tier 3)
**Plan:** `PLAN-demo-grading.md` (steps H3, H4, H6)

## 1. Purpose

- **Tier 2, the live read.** Moodle 5.3's real answers to our service account, read-only: the course, its
  users, the assignment settings (including whether marking workflow is on), the submissions and their
  status, and one submitted file.
- **Tier 3, the dry run.** The library's own pre-write checks (`write_draft_grade` in `libs/moodle_ws`) run on
  those real answers. They stop before anything is sent, and the result is printed.

Both go through the library's client and the demo's read-only connection
(`scripts/demos/readonly_connection.py`), which sends only the six read functions of B4 §2 and refuses
every other function, above all `mod_assign_save_grade`, before anything is sent. **Nothing in these scripts
can write a grade to Moodle.** This connection is demo-only, allowed by the guide. It is not the library's real
transport, which still waits for the lab checks.

Say this out loud:

- Tier 2: "These are Moodle 5.3's real answers to our service account. Read-only."
- Tier 3: "Our library's checks on real data. Nothing is sent. Writing a grade to Moodle is the next step, after
  the lab checks and the real transport."

## 2. Prerequisites

- Run from the LearnOps repository root, on the demo branch (`demo/h2-grading-tier1`, PR #139).
- Python 3.12 with the project's development requirements installed (`requirements-dev.txt`). On Windows with the
  project's virtual environment, use `.venv/Scripts/python.exe` in place of `python`.
- **Offline (anywhere, no lab):** nothing else. Add `--offline` to use the built-in fake.
- **Live (on the lab network, with the lab open), you also need three things:**
  1. `MOODLE53_URL`: the lab site address (see `.env.example`).
  2. `MOODLE53_WS_TOKEN`: the service-account token. **It is a secret** (PRD C-06). Shraddha hands it to Harshitha
     directly. Set it in the shell for this session only. Never put it in a file, a log, a screenshot, #112 or a
     pull request. It is deleted after the demo.
  3. A small config file **outside the repository** (for example in your documents folder) with the course id
     from the "Test course ready" post in #112:

     ```yaml
     course_id: 5
     # optional: only if the learners' usernames are not learner-a to learner-d
     learners:
       A: usernameforA
       B: usernameforB
       C: usernameforC
       D: usernameforD
     ```

In PowerShell, set the two variables for this window only:

```powershell
$env:MOODLE53_URL = "<the lab site address>"
$env:MOODLE53_WS_TOKEN = "<the token you were handed>"
```

## 3. Tier 2: run it

```bash
python scripts/demos/demo_h4_live_read.py --offline                          # the built-in fake
python scripts/demos/demo_h4_live_read.py --config D:/notes/h4.yaml --out D:/notes/h4-output.json   # the lab
```

It prints only facts, in six steps:

| # | Step | What it shows |
|---|---|---|
| 1 | A call with the token, and a refused call | The call succeeds. A function outside the six (`mod_assign_save_grade`) is refused and "nothing was sent" |
| 2 | Course contents | Sections and the assignments in the course |
| 3 | Enrolled users | How many students and others |
| 4 | Assignment settings | Per assignment: grading type, maximum grade, marking workflow ON or OFF |
| 5 | Submissions and status | Per learner and assignment: submission status and grading status |
| 6 | One file | `Downloaded <name>: <n> bytes`. The file's address is never printed |

The end has a **results table** (function, what came back, what was missing from our assumption) and one of the
last lines:

- Offline: `OFFLINE: built-in fake, not a live run. Nothing was written to Moodle.`
- Live: `LIVE: read-only run. Nothing was written to Moodle.`

**Save the full output locally, never in the repository.** `--out` writes it as JSON to a path of your choice; a
path inside the repository is refused before anything runs. Put only a **short results table** in a draft
decision record on your branch: which function, what came back, what was missing from our assumption. This
starts the B4 §5 lab checks 1, 2, 3, 8 and 10.

## 4. Tier 3: run it

```bash
python scripts/demos/demo_h6_dry_run.py --offline
python scripts/demos/demo_h6_dry_run.py --config D:/notes/h6.yaml --out D:/notes/h6-output.json
```

Expected, from the plan's table:

| Case | Expected | Printed |
|---|---|---|
| A: Assignment 1, submitted, no grade yet, workflow on | Allowed | `WOULD WRITE readyforrelease: allowed`, with `write attempt: stopped by the read-only connection` |
| B: Assignment 1, already Ready for release with a grade | Refused: locked (R3) | `REFUSED: locked (R3)`, with `write attempt: none (refused by the library first)` |
| D: Assignment 2, marking workflow off, submitted | Refused: workflow off | `REFUSED: workflow off` |
| C: Assignment 1, a draft, not submitted | Print what the library says. Do not predict it | `library says: <whatever it says>`, with the submission status beside it |

How to read it:

- **"WOULD WRITE" is printed only when a write attempt really reached, and was stopped by, the read-only
  connection.** If the library refuses without such an attempt, the line is `UNEXPECTED` and counts as a failure.
- **The grade** shown is a placeholder (half the maximum), used only to pass the library's checks. It is never sent.
- **Learner C.** The library decides from the grading state only; it does not look at whether the learner
  submitted. Offline it says "would write" for the draft, and the script prints a `FINDING` saying so. This is the
  library's behaviour, shown as it is. A missing submission is the caller's decision (R10). Mention it to the guide.
- If the library cannot stop before sending, **do not change the library for the demo.** Say so in #112 and show
  Tiers 1 and 2 only.

The last line is the same as for Tier 2, with `Nothing was sent` in the offline version.

## 5. Options (root CLAUDE.md §2 rule 9; PRD OPS-05)

| Option | What it does |
|---|---|
| `--offline` | Use the built-in fake lab, not the real one. Without it the script runs live and needs the settings above |
| `--dry-run` | Lists what it would do. Makes no call. With live settings it only checks that they are set |
| `--check` | Runs quietly; exit `0` when every step or result is as expected, `1` when not |
| `--config <file>` | YAML with `course_id` (a whole number), and for Tier 3 optionally `learners` |
| `--out <file>` | Saves the full output as JSON, **outside the repository** |

Exit codes: `0` as expected (a live difference from the fake is a **finding**, not a failure); `1` a step failed, a
result was not as expected, or a case could not run; `2` the demo could not run (missing settings, a bad
`--config`, an `--out` path inside the repository).

If a live step fails, the script shows what failed and the other steps still run. Show what works and say what
failed; do not hide it.

## 6. Findings, not failures (plan section 5)

The fake's answer shapes come from the Moodle source and are **not verified on a lab site**. A live answer that
differs is a finding to write in the results table, not a failure. The first live run is also the first time the
read-only connection's real HTTP code runs: the tests used fake HTTP functions. Watch for surprises such as http
versus https, a redirect (the connection refuses redirects, because one could carry the token elsewhere), or a
different error answer from Moodle.

## 7. Undo, and safety

Nothing to undo. The scripts only read; the only file written is the one named by `--out`. The token is read
from the environment, never printed, logged or saved, and a test checks this with a fake token. After the demo,
Shraddha deletes the token and disables the service account.

## 8. What this does not show

- Any grade written to Moodle, or released.
- The AI grading assistant.
- The library's real transport, which waits for the lab checks.

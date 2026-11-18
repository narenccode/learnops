# H2 — Grading, Tier 1: the draft-grade write checks, offline

**Owner:** Harshitha
**Demo script:** `scripts/demos/demo_h2_grading_tier1.py`
**Plan:** `PLAN-demo-grading.md` (Tier 1, step H2)

## 1. Purpose

Show our grading library (`libs/moodle_ws`) doing its job: before it writes a draft grade, it checks
the learner's state, and afterwards it reads the grade back. Six cases show what it refuses and what it
confirms.

**This is not a live run.** The library runs against an offline fake in
`libs/moodle_ws/tests/source_fake.py`, which behaves as the Moodle 4.5 and 5.3 **source code** says. No
Moodle site is used, no network connection is opened, no token is read, and no grade is written anywhere.
How a real site behaves is for the lab checks (B4 §5).

Say this out loud: "This is the library against a fake that follows Moodle 5.3's source. It is not a
live run."

## 2. Prerequisites

- Run from the LearnOps repository root.
- Python 3.12 with the project's development requirements installed (`requirements-dev.txt`).
- The branch has `libs/moodle_ws` (the top of the grading stack, #80).

## 3. Run it

```bash
python scripts/demos/demo_h2_grading_tier1.py
```

On Windows with the project's virtual environment, `.venv/Scripts/python.exe` in place of `python`.

Each case prints one line: the outcome, the rule behind it, and `write_sent`, followed by the library's
own message. Expected:

| # | Case | Outcome | Rule | `write_sent` |
|---|---|---|---|---|
| 1 | Learner already in state `released` | `REFUSED_LOCKED` | R3 | False |
| 2 | Learner already in state `readyforrelease` | `REFUSED_LOCKED` | R3 | False |
| 3 | State cannot be read (`lastattempt` missing) | `REFUSED_STATE_UNKNOWN` | R6 | False |
| 4 | Marking workflow is off (state `notgraded`) | `REFUSED_WORKFLOW_OFF` | workflow off | False |
| 5 | Write silently ignored, so the read-back differs | `NOT_VERIFIED` | R1 | True |
| 6 | Normal write, read back and matched | `VERIFIED` | R1 | True |

Notes for the presenter:

- **Cases 1 and 2** are both rule R3 (a locked grade is never written to). They start from the two
  locked states, `released` and `readyforrelease`.
- **`write_sent=True` (cases 5 and 6)** means the write was handed to the **fake**. Nothing reaches any
  Moodle.
- **Case 5.** The demo tells the library the assignment's maximum grade is 100, while the fake's
  maximum is 10. The library accepts a grade of 50, the fake silently ignores it (as the Moodle source
  does; lab check 15), and the read-back does not match, so the result is `NOT_VERIFIED`. In real use
  the caller reads the real maximum from the assignment (lab check 2).
- **Case 3** also covers a state the library does not know: it fails closed and writes nothing.

The last lines are `Tier 1: all 6 cases as expected.` and, exactly:

```
OFFLINE: against the Moodle 5.3 fake, not a live run
```

The exit code is `0`.

## 4. Options (root CLAUDE.md §2 rule 9; PRD OPS-05)

| Option | What it does |
|---|---|
| `--dry-run` | Prints the six cases it would run. Runs none and sends nothing |
| `--check` | Runs every case without printing; exit `0` when every case is as expected, `1` when not |
| `--config <file>` | A YAML file with one key, `moodle_version`, which must be `"5.3"` (Tier 1 is defined against the 5.3 fake) |

Exit codes: `0` every case as expected; `1` a case was not as expected (the line is marked
`NOT AS EXPECTED`); `2` the demo could not run (unreadable or wrong `--config` file).

## 5. Undo

Nothing to undo. The demo keeps everything in memory and writes no file. The tests check that the
repository is unchanged after a run (`scripts/demos/tests/test_demo_h2_grading_tier1.py`).

## 6. What this demo does not show

- Any live Moodle: Tier 2 (live read) and Tier 3 (dry run on real answers) are separate steps (H4, H6).
- Any grade written to Moodle, or released. Tools never release grades.
- The AI grading assistant.
- The library's real transport, which waits for the lab checks.

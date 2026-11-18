# D5 — Course input: a course package checked against B1

**Owner:** Student 1 — Akshita
**Demo duration:** 5 minutes
**Demo script:** `scripts/demos/demo_d5_course_input.py`

## 1. Purpose

Show that a course written as text (a B1 course package: `course.yaml` plus Markdown files) is checked
against the B1 contract before anything is built:

1. The B8.2 sample course (four weeks, `full` mode) passes, and the rules that are **not** checked yet are
   listed, never hidden.
2. Broken copies of it are rejected, each with the place, the rule, a message and a fix hint.
3. Every contract example in the repository validates.

This is the B1 validator in `libs/contracts` (Release 0). It is **not** Course Studio (Release 2) and not
the Course Checker (Module 2): no `.mbz` is built and no Moodle site is used.

## 2. Prerequisites

- Run from the LearnOps repository root.
- Python 3.12 with the project's development requirements installed (`requirements-dev.txt`).

## 3. Run it

```bash
python scripts/demos/demo_d5_course_input.py
```

On Windows with the project's virtual environment, `.venv/Scripts/python.exe` in place of `python`.

### Step 1 — the sample course passes

Expected: `RESULT: OK, no errors in the B1 checks that ran (0 errors).`, then the list of rules the
validator does not check yet (for example the week structure and the unlock chain). **"No errors"
never means "fully checked":** say this in the demo.

### Step 2 — planted errors are rejected

The script copies the package to a temporary folder **outside the repository**, once per planted error,
changes one thing in each copy, and validates it:

| # | Planted error | Expected error code |
|---|---|---|
| 1 | A week's task file is missing | `body_file_missing` (B1.1) |
| 2 | Two activities share one idnumber | `duplicate_idnumber` (B1.2 rule 6) |
| 3 | The package includes the protected `final-project` | `schema_not` (B1.4) |
| 4 | An unknown build mode | `schema_enum` (B1.1) |
| 5 | Media named by a full URL, not a relative path | `schema_pattern` (C-08) |

Each must print `REJECTED as expected`, with the place, the rule, a message and a fix hint in plain words.
For case 5 the message reads "… is not a path relative to the package folder." (plain-words messages for
schema patterns, #131, UI-05). A message longer than 240 characters would be shortened on screen and say
so; none of the five is that long.

### Step 3 — contract examples

Runs `libs/contracts/validate_examples.py`. Expected: `… 0 failed … 0 problems found.`

The last line is `D5 demo: everything as expected.` and the exit code is `0`.

## 4. Options (root CLAUDE.md §2 rule 9; PRD OPS-05)

| Option | What it does |
|---|---|
| `--dry-run` | Prints what the demo would do. Creates, validates and deletes nothing |
| `--check` | Runs every step without printing; exit `0` when every result is as expected, `1` when not |
| `--config <file>` | A YAML file with one key, `package`: a package folder relative to the repository root, to demo another package in place of B8.2 |

Exit codes: `0` everything as expected; `1` a result was not as expected (the lines are marked
`NOT AS EXPECTED`); `2` the demo could not run (missing package, unreadable `--config` file).

## 5. Undo

Nothing to undo. The demo only reads the repository; the broken copies live in a temporary folder outside
it, which is removed when the demo ends, also after an error. The tests check that the repository is
unchanged after a run (`scripts/demos/tests/test_demo_d5_course_input.py`).

## 6. What this demo does not show

- Course Studio's editor, preview or `.mbz` build (Release 2; the design is `docs/design/studio.md`).
- The Course Checker's rules CK-01 to CK-13 (Module 2).
- Anything on Moodle: no site is used.

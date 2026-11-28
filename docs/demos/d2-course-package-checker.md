# D2 — Course-package checker: `checker check <package> --json`

**Owner:** Student 2 — Shraddha (with Akshita)
**Demo duration:** 5 to 7 minutes
**Demo script:** `scripts/demos/demo_d2_course_package_checker.py`
**Answer file:** `testdata/b8-3-planted-errors/answer.yaml`
**Decision record:** [0020](../decisions/0020-cli-config-file-and-precedence.md) (the `--config` file)

## 1. Purpose and scope

One command runs the shared B1 validator (`libs/contracts`) on a course package folder and prints each error
with its place. Four copies of the B8.2 sample course, each with one planted error, are rejected.

**This is a limited B1-level demonstration. It is not the Course Checker.** The four packages are
**four B1-level cases, a subset of B8.3**, not the full CK-01 to CK-13 catalogue, and B8.3 is not complete.
D2 does not run any CK rule (FR-C-03, Release 1); it lists the thirteen as `not checked`. No `.mbz`, no Moodle
site, no browser test and no `checker diff` are involved. Nothing here shows that PRD C2.7 (100 % of the
planted errors) is met.

## 2. Prerequisites

- Run from the LearnOps repository root.
- Python 3.12 with the development requirements: `python -m pip install -r requirements-dev.txt`.
  No package is installed and no `pyproject.toml` is needed: the script puts `libs/` on the path itself, as
  the D5 demo does.

## 3. Run it

```bash
python scripts/demos/demo_d2_course_package_checker.py check testdata/b8-2-sample-course/package --json
```

On Windows with the project's virtual environment, `.venv/Scripts/python.exe` in place of `python`. The
command is `checker check <package> --json` of checker design §6.2; here it is a script, so
`python scripts/demos/demo_d2_course_package_checker.py` stands in for `checker`.

| Option | Behaviour |
|---|---|
| `<package>` | The package folder (a folder with `course.yaml`). Optional when `package:` is in the config file |
| `--json` | Print the report as JSON. Without it the report is plain text |
| `--dry-run` | Print what would be done. Reads and validates nothing; exit `0` |
| `--check` | Quiet: prints nothing; the exit code is the answer |
| `--config <file>` | YAML whose keys are option names: `package`, `json`, `dry-run`, `check`. Order: flag, config file, environment variable, default (decision 0020). D2 reads no environment variable. An unknown key or a wrong type is refused with exit `2` |

`--dry-run` and `--check` cannot be combined (exit `2`).

**Exit codes (PRD OPS-05).** `0`: no error finding. `1`: at least one error finding. `2`: the command could not
run: missing package folder, no package named, an unknown command or option, or an unreadable or invalid
`--config` file. `not checked` entries never change the exit code.

**Undo.** Nothing to undo: the command only reads the package folder and writes to standard output. It creates
no file, no temporary folder and no database row.

## 4. The report

The JSON follows the shape of checker design §3.6 as far as the B1 validator allows (the field names stay a
proposal until the guide settles §12 item 19):

```json
{
  "checker_version": "0.1.0-d2-demo",
  "input": {"kind": "package", "name": "testdata/b8-3-planted-errors/invalid-mode/package"},
  "summary": {"errors": 1, "warnings": 0, "not_checked": 23},
  "findings": [
    {"layer": "B1", "code": "schema_enum", "rule": "B1.1", "location": ["course", "mode"],
     "item": {"idnumber": null}, "message": "course.mode: 'everything' is not one of ['full', 'sections-only']",
     "fix_hint": "Change this value in course.yaml so that it matches the course package schema (...).",
     "severity": "error"}
  ],
  "not_checked": [
    {"layer": "B1", "code": "week_structure_not_checked", "rule": "B1.2 rule 1", "location": [],
     "item": {"idnumber": null}, "message": "Not checked: ...", "fix_hint": "...", "reason": "Not checked: ..."},
    {"layer": "CK", "rule": "CK-01", "location": [], "item": {"idnumber": null},
     "reason": "The package failed B1 validation, so no CK rule ran."}
  ]
}
```

- **`findings`** are the validator's errors. `location` is the path inside `course.yaml`, for example
  `["sections", 1, "activities", 0, "idnumber"]` is `sections[1].activities[0].idnumber`. `rule` is a **B1**
  rule, not a CK id. `item.idnumber` is the activity or section idnumber when the validator knows it.
  The section number and title of design §3.6 are not available from the B1 validator in D2.
- **`not_checked`**: one state, named `not checked`. It lists the B1 rules the validator does not run yet
  (eight at the time of writing) and all thirteen CK rules, which D2 does not run. A rule that applies to the
  whole package has `item.idnumber: null`. A package that fails B1 gives the reason "failed B1 validation"
  (design §3.4 boundary).
- **`summary`** counts both lists. A report always shows the error count **and** the not-checked count, for
  example `Result: 0 errors, 21 not checked`. **No report says "clean"**, because "no errors" never means "fully
  checked". Say this in the demo.

## 5. Expected results

**Clean B8.2 sample** (`testdata/b8-2-sample-course/package`): exit `0`, `Result: 0 errors, 21 not checked`
(8 B1 rules and 13 CK rules).

**Four planted-error packages** under `testdata/b8-3-planted-errors/<id>/package/`. Each is a full copy of
B8.2 with exactly one change; B8.2 itself is unchanged. Each gives exit `1` and exactly one error:

| `<id>` | The one change | Error code | B1 rule | Location |
|---|---|---|---|---|
| `missing-body` | `weeks/02-task.md` deleted | `body_file_missing` | B1.1 | `sections[1].activities[1].body` |
| `duplicate-id` | Week 2 guide (`wk-02-guide`) renamed `wk-01-guide` | `duplicate_idnumber` | B1.2 rule 6 | `sections[1].activities[0].idnumber` |
| `protected-id` | Week 4 task renamed `final-project` | `schema_not` | B1.1 (B1.4) | `sections[3].activities[1].idnumber` |
| `invalid-mode` | `course.mode: everything` | `schema_enum` | B1.1 | `course.mode` |

A package that fails B1 reports only the B1 error(s); every CK rule is `not checked` (design §3.4). The `duplicate-id`
copy renames a **guide**, not a task, on purpose: no unlock rule names a guide, so no second error appears.
Renaming `wk-02-task` also breaks week 3's `unlock.after` and gives two errors (found while reconciling the
first version with the current validator).

**The answer file**, `testdata/b8-3-planted-errors/answer.yaml`, holds for each package its `layer` (`B1`, as the
guide asked), the one planted change, the expected exit code and error count, and the validator's code, rule,
location, idnumber and exact message. The tests compare the command's output with it. The report's
`not_checked` list is not pinned there: it follows the validator.

## 6. Tests

```bash
python -m pytest scripts/demos/tests/test_demo_d2_course_package_checker.py
MYPYPATH=libs python -m mypy --strict scripts/demos/demo_d2_course_package_checker.py scripts/demos/tests/test_demo_d2_course_package_checker.py
```

They cover the clean sample, each planted package (exactly one error, and exactly one change from B8.2), the JSON
shape and counts, plain text, `--check`, `--dry-run`, `--config` (including unknown keys and wrong types), exit
code `2`, and that running the command leaves the repository unchanged.

## 7. Limits

- The B1 validator does not check everything: its `not_checked` list is shown in every report. A rule on that
  list is not a passing rule.
- Directory packages only: no `.mbz`, no `checker diff`, no role tests, no harness.
- The real `checker` command waits for the checker design to be Approved and for Release 1.

# D1 — Contract Examples Checked Against Their Schemas

**Owner:** Student 2 — Shraddha
**Demo duration:** 5–7 minutes
**Demo script:** `scripts/demos/demo_d1_contracts.py`

## 1. Purpose

Show that LearnOps checks every contract example in the repository against its JSON Schema.

This is the "Contract" test level of PRD §E1 ("Every example and generated file validates against its
schema", run in CI on every PR). The schemas and the validator live in the shared `contracts` library,
which PRD EXT-09 requires modules to import and never copy.

The demonstration has two parts:

1. Every real example passes.
2. A deliberately broken copy of one example is rejected because it violates its schema.

This is the repository-wide contract examples validator (`libs/contracts/validate_examples.py`). It is
separate from the B1 course-package validator and the future Course Checker.

## 2. Prerequisites

- Run from the LearnOps repository root.
- Python 3.12.
- Install the development requirements (they include PyYAML, which the script uses for `--config`, and
  `jsonschema`, which the validator uses):

```bash
python -m pip install -r requirements-dev.txt
```

Check the Python version:

```bash
python --version
```

## 3. Run the D1 demonstration

```bash
python scripts/demos/demo_d1_contracts.py
```

### Step 1 — Validate the real examples

The script runs `libs/contracts/validate_examples.py` on the repository's `contracts/` folder.

Verified result on the current branch (after merging `origin/main` at `ef7f438`):

- Exit code `0`.
- One `OK` line per example, then the summary:
  `26 examples found, 10 schemas: 26 passed, 0 failed, 0 not validated; 0 problems found.`

The counts change when contracts or examples are added; they are not fixed by the script. What the
script requires is exit `0`.

### Step 2 — Reject a planted error

The script copies the `contracts` folder to a temporary folder and, in the **copy**, changes the `schema`
value of `examples/lesson-manifest.v1/single-track.json` from `learnops.lesson/v1` to
`learnops.lesson/v999`. It then runs the validator on the copy.

Expected result (verified):

- Exit code `1`.
- The output names `single-track.json` and a `[const]` violation:
  `schema: 'learnops.lesson/v1' was expected [const]`.
- The summary reads `26 examples found, 10 schemas: 25 passed, 1 failed, …`.

The last line of the demo is `D1 demo: everything as expected. Repository contracts were not modified.`

## 4. Options and configuration (root `CLAUDE.md` §2 rule 9; PRD OPS-05)

| Option | What it does |
|---|---|
| `--dry-run` | Prints what the demo would do. Validates nothing, creates no temporary files, deletes nothing |
| `--check` | Runs both steps without printing; exit `0` when every result is as expected, `1` when not. A failure prints only the failing lines, to the error output |
| `--config FILE` | Reads settings from a YAML file (below) |
| `--contracts-dir DIR` | The contracts folder to use. A relative path starts at the repository root |

`--dry-run` and `--check` cannot be combined. The demo calls the validator with `--check`, which is
read-only (the validator has no mode that writes).

Exit codes: `0` everything as expected; `1` a result was not as expected (lines are marked
`NOT AS EXPECTED`); `2` the demo could not run. A message says what happened and what to do. Causes: a bad `--config`
file or missing PyYAML (needed only with `--config`); a missing contracts folder, example or validator;
a temporary folder that cannot be created or filled (including a failed copy); an example that cannot
be read or is not one JSON object; a validator that cannot start, is killed, ends with its own usage
error (exit 2) or crashes with a Python error (for example a missing `jsonschema`).

A genuine validation result is never turned into `2`: real examples that fail, or a planted error that
is not rejected as expected, are exit `1`. If a real example already failed in Step 1 and Step 2 then
cannot run, the exit code stays `1` and the Step 2 problem is printed too. If the temporary folder
cannot be removed at the end, the result still counts and a warning names the folder.

### Configuration file

One optional key:

```yaml
# demo-d1.yaml
contracts_dir: contracts   # the contracts folder; a relative path starts at the repository root
```

- The file must be YAML holding `key: value` lines. An empty file means "no settings".
- An unknown key, a value of the wrong type (`contracts_dir` must be text, not a number or a list), an
  empty value, unreadable or malformed YAML, or a file that is not found all stop the demo with a
  clear message and exit code `2`. This also applies with `--dry-run`.
- Do not put secrets in this file. There are none to configure.

Precedence, highest first:

1. Command-line option (`--contracts-dir`)
2. YAML file (`--config`, key `contracts_dir`)
3. Environment variable `LEARNOPS_D1_CONTRACTS_DIR` (listed in `.env.example`; it is not a secret)
4. Default: `contracts`

The folder you name must contain `examples/lesson-manifest.v1/single-track.json`, because that is the
example the demo breaks; otherwise the demo exits with `2`.

## 5. Undo

**Nothing persistent needs undoing.** The demo never writes into the repository. The planted error is
made only in a temporary copy of the contracts folder; the script removes that folder when it ends,
also after an error or Ctrl-C. `--dry-run` creates nothing at all. (Only an abrupt kill, such as
`kill -9`, could leave a `learnops-d1-*` folder in the system temporary directory; deleting it is safe.)

## 6. CI evidence

The validator is part of `.github/workflows/ci.yml`:

```bash
if [ -f libs/contracts/validate_examples.py ]; then python libs/contracts/validate_examples.py; fi
```

**Historical record, not a current result:** GitHub Actions run **#271** on PR **#92** passed this step
when there were 3 examples and 2 schemas (`3 passed, 0 failed`). That was before PR #92 was merged and
before the contracts grew to the current 26 examples and 10 schemas. It is kept only to show that the
step ran in CI; do not present it as the status of this branch. No CI run for the current branch is
recorded here; check the PR's Checks tab for a current one.

CI run (historical): https://github.com/narenccode/learnops/actions/runs/43827700033

## 7. Suggested presentation flow (5–7 minutes)

1. **Introduce D1 (1 minute):** Contract examples are checked against JSON Schemas (PRD §E1 "Contract").
2. **Show CI (1 minute):** Point out the validator step in `.github/workflows/ci.yml`. Say the Actions
   run in section 6 is historical; show the PR's current Checks tab if one exists.
3. **Run the demo (2–3 minutes):** Run `--dry-run` first to show the plan, then the demo: 26 real
   examples pass, then the planted error is rejected with `[const]`.
4. **Explain the result (1 minute):** The validator detects the mismatch and returns exit code `1`.
5. **Close (30 seconds):** D1 shows contract-example validation, not the B1 package validator or the
   Course Checker.

## 8. Scope and safety

- Repository test examples only; no real learner data and no secrets.
- The planted error exists only in a temporary copy. The original contract files are not modified.
- Do not commit directly to `demo-interim`; demo integration is coordinated separately.

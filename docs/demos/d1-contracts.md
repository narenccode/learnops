# D1 — Contract Examples Checked by CI

**Owner:** Student 2 — Shraddha
**Demo duration:** 5–7 minutes
**Demo script:** `scripts/demos/demo_d1_contracts.sh`

## 1. Purpose

Demonstrate that LearnOps validates repository contract examples against their JSON Schemas.

The demonstration has two parts:

1. Existing valid examples pass.
2. A deliberately modified example fails because it violates its schema.

This is the repository-wide contract examples validator. It is separate from the B1 course-package validator and the future Course Checker.

## 2. Prerequisites

- Run from the LearnOps repository root.
- Python 3.12.
- Project virtual environment activated.
- Contract validator dependencies installed.

Check the Python version:

```bash
python --version
```

## 3. Run the D1 demonstration

From the repository root, execute:

```bash
bash scripts/demos/demo_d1_contracts.sh
```

The script performs both demonstration steps automatically.

### Step 1 — Validate real examples

The script runs:

```bash
python libs/contracts/validate_examples.py
```

Expected result:

- Exit code `0`.
- All three repository examples pass.
- Summary: `3 passed, 0 failed`.

### Step 2 — Reject a planted error

The script copies the `contracts` directory to a temporary location and changes the `schema` value in the copied `single-track.json` example from `learnops.lesson/v1` to `learnops.lesson/v999`.

It then runs the validator against the temporary copy.

Expected result:

- Exit code `1`.
- The validator reports a `[const]` schema violation.
- The original repository files remain unchanged.

The script removes its temporary directory when it exits.

## 4. CI evidence

The contract examples validator is included in `.github/workflows/ci.yml`:

```bash
if [ -f libs/contracts/validate_examples.py ]; then python libs/contracts/validate_examples.py; fi
```

GitHub Actions run **#271**, on PR **#92**, completed successfully.

The `checks` job included the `Validate contract examples` step and reported:

```text
3 examples found, 2 schemas: 3 passed, 0 failed, 0 not validated; 0 problems found.
```

The run was on the PR head commit, before PR #92 was merged.

CI run: https://github.com/narenccode/learnops/actions/runs/43827700033

## 5. Suggested presentation flow (5–7 minutes)

1. **Introduce D1 (1 minute):** Explain that repository contract examples are checked against JSON Schemas.
2. **Show CI (1 minute):** Point out the validator command in `.github/workflows/ci.yml` and the successful Actions run.
3. **Run the demo (2–3 minutes):** Show valid examples passing, followed by the planted schema error being rejected.
4. **Explain the result (1 minute):** The validator detects the contract-example mismatch and returns a failing exit code.
5. **Close (30 seconds):** Clarify that D1 demonstrates contract-example validation, not the B1 package validator or the Course Checker.

## 6. Scope and safety

- Use repository test examples only; do not use real learner data or secrets.
- The planted error is made only in a temporary copy of the contracts directory.
- The original repository contract files are not modified by the demo script.
- Do not commit directly to `demo-interim`; demo integration is coordinated separately.

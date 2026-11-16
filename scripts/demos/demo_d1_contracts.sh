#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON:-python}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "ERROR: Python executable not found: $PYTHON_BIN" >&2
    exit 2
fi

if [[ ! -f "libs/contracts/validate_examples.py" ]]; then
    echo "ERROR: Contract examples validator not found." >&2
    exit 2
fi

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/learnops-d1.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "=============================================="
echo "LearnOps D1 — Contract Examples CI Demo"
echo "=============================================="
echo "Python: $("$PYTHON_BIN" --version)"
echo

echo "STEP 1: Validate the real repository examples"
echo "Expected: exit code 0"
echo "----------------------------------------------"

"$PYTHON_BIN" libs/contracts/validate_examples.py

echo
echo "PASS: Real repository examples were accepted."
echo

echo "STEP 2: Test a deliberately invalid example"
echo "Expected: exit code 1"
echo "----------------------------------------------"

if [[ ! -f "contracts/examples/lesson-manifest.v1/single-track.json" ]]; then
    echo "ERROR: Planted-error example not found." >&2
    exit 2
fi

cp -a contracts "$TMP_DIR/contracts"

"$PYTHON_BIN" - "$TMP_DIR/contracts/examples/lesson-manifest.v1/single-track.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))

# Deliberately violate the schema's required const value.
data["schema"] = "learnops.lesson/v999"

path.write_text(
    json.dumps(data, indent=2) + "\n",
    encoding="utf-8",
)
PY

NEGATIVE_LOG="$TMP_DIR/negative.log"
NEGATIVE_STATUS=0

if "$PYTHON_BIN" libs/contracts/validate_examples.py \
    --contracts-dir "$TMP_DIR/contracts" \
    >"$NEGATIVE_LOG" 2>&1; then
    NEGATIVE_STATUS=0
else
    NEGATIVE_STATUS=$?
fi

cat "$NEGATIVE_LOG"
echo

if [[ "$NEGATIVE_STATUS" -ne 1 ]]; then
    echo "ERROR: Expected exit code 1, received $NEGATIVE_STATUS."
    exit 1
fi

if ! grep -Fq "single-track.json" "$NEGATIVE_LOG"; then
    echo "ERROR: The expected example was not reported."
    exit 1
fi

if ! grep -Fq "[const]" "$NEGATIVE_LOG"; then
    echo "ERROR: The expected const violation was not reported."
    exit 1
fi

echo "PASS: The planted invalid example was rejected."
echo "PASS: The schema const violation was identified."
echo
echo "=============================================="
echo "D1 DEMO COMPLETED SUCCESSFULLY"
echo "Real examples: PASS (exit 0)"
echo "Planted error: REJECTED (exit 1)"
echo "Repository contracts were not modified."
echo "=============================================="

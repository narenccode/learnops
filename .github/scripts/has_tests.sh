#!/usr/bin/env bash
# Exit 0 when any module or library has a `tests` folder, else exit 1. Run from the repository root.
#
# CI uses this to decide whether the "Unit tests" step has anything to run. It replaces
# `ls -d modules/*/tests libs/*/tests`, which exits non-zero as soon as ONE of the two patterns
# matches nothing, so the step was silently skipped while libs/contracts/tests existed.
for dir in modules/*/tests libs/*/tests; do
    # An unmatched pattern stays a literal string, which `-d` rejects, so it is ignored.
    if [ -d "$dir" ]; then
        exit 0
    fi
done
exit 1

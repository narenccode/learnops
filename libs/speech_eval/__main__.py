"""`python -m speech_eval --manifest RUN.json [--check] [--dry-run] [--output REPORT.md]`.

--check    validate the inputs only; compute and write nothing.
--dry-run  compute and print the report; write no file.
Undo: delete the report file that --output wrote. The tool never modifies its inputs and never
overwrites an existing report.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from speech_eval.inputs import load_run
from speech_eval.report import render_report
from speech_eval.wer import evaluate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="speech_eval", description=__doc__)
    parser.add_argument(
        "--manifest", required=True, type=Path, help="run description (JSON)"
    )
    parser.add_argument("--check", action="store_true", help="validate inputs only")
    parser.add_argument(
        "--dry-run", action="store_true", help="print the report, write nothing"
    )
    parser.add_argument(
        "--output", type=Path, help="write the report here (must not exist)"
    )
    args = parser.parse_args(argv)

    run = load_run(args.manifest)
    if run.errors:
        print("Inputs are not valid. Fix these, then run again:", file=sys.stderr)
        for error in run.errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    for warning in run.warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    if args.check:
        print(f"OK: {len(run.lectures)} lecture(s) valid in mode {run.mode}.")
        return 0

    pairs = [(x.lecture_id, x.reference_text, x.hypothesis_text) for x in run.lectures]
    try:
        result = evaluate(pairs, run.normaliser)
        report = render_report(run, result)  # .wer raises for an empty reference
    except ValueError as exc:
        print(f"Cannot compute: {exc}", file=sys.stderr)
        return 1
    if args.output and not args.dry_run:
        try:
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(report)
        except FileExistsError:
            print(
                f"{args.output} already exists; choose another name or delete it.",
                file=sys.stderr,
            )
            return 1
        except OSError as exc:
            print(f"Cannot write the report: {type(exc).__name__}", file=sys.stderr)
            return 1
        print(f"Report written to {args.output}")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())

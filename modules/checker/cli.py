from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence


def _load_validator():
    # The repository has a data directory named contracts/ at its root.
    # Add libs/ first so Python imports the actual validator library.
    repo_root = Path(__file__).resolve().parents[2]
    libs_path = str(repo_root / "libs")
    if libs_path in sys.path:
        sys.path.remove(libs_path)
    sys.path.insert(0, libs_path)

    from contracts import DirectorySource, validate_package

    return DirectorySource, validate_package


def _issue_to_dict(issue) -> dict:
    return {
        "code": issue.code,
        "rule": issue.rule,
        "message": issue.message,
        "fix_hint": issue.fix_hint,
        "location": list(issue.location),
        "idnumber": issue.idnumber,
    }


def _check_package(package_path: Path) -> int:
    if not package_path.exists() or not package_path.is_dir():
        print(f"Error: package directory not found: {package_path}", file=sys.stderr)
        return 2

    DirectorySource, validate_package = _load_validator()
    report = validate_package(DirectorySource(package_path))

    result = {
        "ok": report.ok,
        "errors": [_issue_to_dict(issue) for issue in report.errors],
        "not_checked": [_issue_to_dict(issue) for issue in report.not_checked],
    }

    print(json.dumps(result, indent=2))
    return 0 if report.ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="checker")
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("check", help="validate a course package directory")
    check.add_argument(
        "package", type=Path, help="path to the course package directory"
    )
    check.add_argument(
        "--json", action="store_true", help="print the validation report as JSON"
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "check":
        if not args.json:
            parser.error("the D2 demo requires --json")
        return _check_package(args.package)

    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

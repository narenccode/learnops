"""Download the B8.1 template course backup (.mbz) from its GitHub release and check its SHA-256.

The guide's answers on Issue #55 (2026-11-18, P24 and P33): the script has `--check` (verify the
SHA-256 of the file already here; read-only) and `--dry-run` (print the target, write nothing); a
download whose SHA-256 check fails removes its partial file; a rebuild is a new asset under a new
tag, and a tag is never overwritten.

Run from the repository root:

    python testdata/b8-1-template-course/download.py            # download and verify
    python testdata/b8-1-template-course/download.py --dry-run  # print source and target only
    python testdata/b8-1-template-course/download.py --check    # verify the file already here

If the repository is private and the plain download is refused, fetch the asset with
`gh release download <tag> --pattern <asset> --dir testdata/b8-1-template-course` and run `--check`.

Undo: delete testdata/b8-1-template-course/<asset>.mbz. `*.mbz` is gitignored, so nothing reaches Git.
Exit codes: 0 = the file is here and its SHA-256 matches; 1 = the SHA-256 does not match;
2 = could not run (no SHA-256 recorded yet, no file to check, or the download failed).
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPOSITORY = "narenccode/learnops"
TAG = "testdata-b8-1-v1"  # a rebuild gets testdata-b8-1-v2; v1 is kept (guide, P24)
ASSET = "b8-1-template-course.v1.mbz"
# Recorded on 2026-11-24 from the rebuilt backup (12,612 bytes, built on Moodle 5.3+ Build 20261030; the guide's
# option 2 on issue #112); also in
# the README §1 and testdata/README.md. A rebuild is a new asset and a new tag, never an overwrite.
SHA256: str | None = "d8869a012a39ae869c54f744d6c391387534bdab2389d8a8aecfd5b481c5585d"

HERE = Path(__file__).resolve().parent
TARGET = HERE / ASSET
CHUNK = 1024 * 1024

NO_SHA = (
    "No SHA-256 is recorded for {asset} yet: the backup has not been uploaded (PENDING MOODLE LAB). "
    "Nothing was downloaded or checked."
)
DRY_RUN = "Dry run: would download {source}\n  to {target}\n  and check SHA-256 {sha}. Nothing written."
MISSING = "{target} does not exist. Run this script without --check to download it."
MATCH = "OK: {target} has the recorded SHA-256 ({sha})."
MISMATCH = (
    "SHA-256 differs for {target}: expected {expected}, got {actual}. "
    "The file is not the released backup; delete it and download it again."
)
REMOVED = "The partial download was removed; nothing is left behind."
FAILED = "Download failed ({reason}). {removed} Check the network, or use `gh release download` (see --help)."


def source_url() -> str:
    return f"https://github.com/{REPOSITORY}/releases/download/{TAG}/{ASSET}"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def check(target: Path, expected: str) -> int:
    if not target.is_file():
        print(MISSING.format(target=target), file=sys.stderr)
        return 2
    actual = sha256_of(target)
    if actual != expected:
        print(
            MISMATCH.format(target=target, expected=expected, actual=actual),
            file=sys.stderr,
        )
        return 1
    print(MATCH.format(target=target, sha=expected))
    return 0


def download(source: str, target: Path, expected: str) -> int:
    """Write to <target>.part, verify, then rename. Any failure removes the partial file."""
    partial = target.with_name(target.name + ".part")
    try:
        with urllib.request.urlopen(source, timeout=60) as response, partial.open(
            "wb"
        ) as sink:
            for block in iter(lambda: response.read(CHUNK), b""):
                sink.write(block)
    except (OSError, urllib.error.URLError, ValueError) as error:
        partial.unlink(missing_ok=True)
        print(FAILED.format(reason=error, removed=REMOVED), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        # Ctrl+C: leave nothing half-written behind, then stop as the user asked.
        partial.unlink(missing_ok=True)
        print(REMOVED, file=sys.stderr)
        raise
    actual = sha256_of(partial)
    if actual != expected:
        partial.unlink()
        print(
            MISMATCH.format(target=target, expected=expected, actual=actual),
            file=sys.stderr,
        )
        print(REMOVED, file=sys.stderr)
        return 1
    partial.replace(target)
    print(MATCH.format(target=target, sha=expected))
    return 0


def main(
    argv: list[str] | None = None,
    *,
    target: Path = TARGET,
    source: str | None = None,
    expected: str | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        description="Download the B8.1 template course backup and check its SHA-256."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="print source and target; write nothing"
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="verify the file already here; write nothing",
    )
    args = parser.parse_args(argv)

    source = source or source_url()
    expected = expected if expected is not None else SHA256
    if args.dry_run:
        print(
            DRY_RUN.format(
                source=source, target=target, sha=expected or "(not recorded yet)"
            )
        )
        return 0
    if expected is None:
        print(NO_SHA.format(asset=ASSET), file=sys.stderr)
        return 2
    if args.check:
        return check(target, expected)
    return download(source, target, expected)


if __name__ == "__main__":
    sys.exit(main())

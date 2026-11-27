"""Make a SYNTHETIC CK-08 candidate: a Moodle backup whose completion criterion points at no activity.

PRD B8.3 / C2.3 (CK-08), guide decision on issue #232 point 4: the fixture may be made by a scripted,
repeatable edit of the backup, kept with its SHA-256 before and after and labelled synthetic. Moodle
itself is never touched and cannot produce this state through its own settings.

What the edit does (and only this):
  * reads `completion.xml` in the backup, finds the one `course_completion_criteria` of type 4
    (activity completion) whose `<moduleinstance>` is the cmid of the activity with the given idnumber;
  * rewrites that `<moduleinstance>` to a cmid that no activity in the backup has;
  * updates the size of `completion.xml` in `.ARCHIVE_INDEX`;
  * copies every other archive member byte for byte. No activity is deleted or renamed.

The input backup is opened read-only and is never changed. The output is written to a new path and the
script refuses to overwrite anything. Output is deterministic (fixed gzip timestamp, member headers
copied), so the same input and options give the same SHA-256.

Modes
  (default)   build OUT and OUT.manifest.json, then verify them
  --dry-run   do all the work in memory, print what would happen, write nothing
  --check     read-only: verify an existing OUT against its manifest and the checks below
  --undo      delete OUT and its manifest (only if they are the files this script made)

Exit codes: 0 = done or check passed; 1 = a check failed; 2 = could not run (bad input, refused).

Known limits: the whole archive is read into memory, with no decompression size cap (the inputs are
small lab backups from a trusted source; do not point this at an untrusted file). `--undo` cannot prove
who made a file, only that it has the structure, hash and manifest of a generated output.

The result is a candidate, not the final CK-08 fixture: the final one must be made from the merged
B8.1 + B8.2 baseline (see docs/runbooks/b8-3-moodle-lab-offline-prep.md).
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import sys
import tarfile
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LABEL = "SYNTHETIC: scripted backup edit, not produced by Moodle (guide, issue #232 point 4)"
MANIFEST_SUFFIX = ".manifest.json"
CRITERION_TYPE_ACTIVITY = "4"
NULL = "$@NULL@$"

MSG_NO_INPUT = "Input backup not found: {path}. Download it with testdata/b8-1-template-course/download.py."
MSG_EXISTS = "Refusing to overwrite {path}. Choose a new --out, or run --undo first."
MSG_SAME = "--out must not be the input file. The input is never changed."
MSG_NO_MANIFEST = "No manifest next to {path}. Nothing to check or undo here."
MSG_UNDO_REFUSED = "Refusing to delete {path}: it is not a file this script generated ({reasons}). Nothing was deleted."


class FixtureError(Exception):
    """A problem the user can fix (bad input, ambiguous criterion)."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Member:
    info: tarfile.TarInfo
    data: bytes


def read_archive(raw: bytes) -> tuple[list[Member], int]:
    """Read a gzip'd tar into memory (backups are small). Returns members and the tar format."""
    members: list[Member] = []
    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tar:
            fmt = tar.format
            for info in tar:
                data = tar.extractfile(info).read() if info.isfile() else b""  # type: ignore[union-attr]
                members.append(Member(info, data))
    except (tarfile.TarError, OSError, EOFError, zlib.error) as exc:
        raise FixtureError(
            f"Not a readable Moodle backup (.mbz is a gzip tar): {exc}"
        ) from exc
    return members, fmt


def write_archive(members: list[Member], fmt: int) -> bytes:
    """Write members back with the original headers and a fixed gzip timestamp (repeatable)."""
    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w", format=fmt) as tar:
        for m in members:
            info = tarfile.TarInfo(m.info.name)
            for attr in (
                "mode",
                "uid",
                "gid",
                "uname",
                "gname",
                "mtime",
                "type",
                "linkname",
            ):
                setattr(info, attr, getattr(m.info, attr))
            info.size = len(m.data) if m.info.isfile() else 0
            tar.addfile(info, io.BytesIO(m.data) if m.info.isfile() else None)
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode="wb", mtime=0) as gz:
        gz.write(tar_buf.getvalue())
    return out.getvalue()


def _by_name(members: list[Member]) -> dict[str, Member]:
    return {m.info.name: m for m in members}


def activities(members: list[Member]) -> dict[str, dict[str, str]]:
    """cmid -> {dir, modname, idnumber}, found by reading the backup, never assumed."""
    files = _by_name(members)
    if "moodle_backup.xml" not in files:
        raise FixtureError(
            "moodle_backup.xml is missing: this is not a Moodle course backup."
        )
    text = files["moodle_backup.xml"].data.decode("utf-8")
    result: dict[str, dict[str, str]] = {}
    for block in re.findall(r"<activity>(.*?)</activity>", text, re.DOTALL):
        mid = re.search(r"<moduleid>(\d+)</moduleid>", block)
        mod = re.search(r"<modulename>(.*?)</modulename>", block)
        dirn = re.search(r"<directory>(.*?)</directory>", block)
        if not (mid and mod and dirn):
            continue  # the second, short <activity>name</activity> list in the settings part
        module_xml = files.get(f"{dirn.group(1)}/module.xml")
        idn = NULL
        if module_xml:
            found = re.search(
                r"<idnumber>(.*?)</idnumber>", module_xml.data.decode("utf-8")
            )
            idn = found.group(1) if found else NULL
        if mid.group(1) in result:
            raise FixtureError(
                f"moodle_backup.xml lists cmid {mid.group(1)} more than once."
            )
        result[mid.group(1)] = {
            "dir": dirn.group(1),
            "modname": mod.group(1),
            "idnumber": idn,
        }
    return result


def criteria(text: str) -> list[dict[str, str]]:
    out = []
    for m in re.finditer(
        r'<course_completion_criteria id="(\d+)">(.*?)</course_completion_criteria>',
        text,
        re.DOTALL,
    ):
        fields = dict(re.findall(r"<(\w+)>(.*?)</\1>", m.group(2), re.DOTALL))
        fields["id"] = m.group(1)
        out.append(fields)
    return out


def pick_unused_id(acts: dict[str, dict[str, str]], members: list[Member]) -> str:
    """Highest cmid in the backup plus 1000: readable, and checked again by `verify`."""
    highest = max((int(k) for k in acts), default=0)
    ids_in_dirs = [
        int(n)
        for m in members
        for n in re.findall(r"^activities/\w+?_(\d+)/", m.info.name)
    ]
    return str(max([highest, *ids_in_dirs]) + 1000)


def make_fixture(
    raw: bytes, idnumber: str, new_id: str | None
) -> tuple[bytes, dict[str, Any]]:
    members, fmt = read_archive(raw)
    files = _by_name(members)
    for needed in ("completion.xml", ".ARCHIVE_INDEX"):
        if needed not in files:
            raise FixtureError(f"{needed} is missing from the backup.")
    acts = activities(members)
    target_ids = [k for k, v in acts.items() if v["idnumber"] == idnumber]
    if len(target_ids) != 1:
        raise FixtureError(
            f"Expected exactly one activity with idnumber {idnumber!r}, found {len(target_ids)}. "
            "Pass --criterion-idnumber for an activity that exists once."
        )
    old_id = target_ids[0]
    new = new_id or pick_unused_id(acts, members)
    if new in acts or any(f"_{new}/" in m.info.name for m in members):
        raise FixtureError(
            f"cmid {new} already identifies an activity. Choose another --new-id."
        )

    before_xml = files["completion.xml"].data.decode("utf-8")
    matches = [
        c
        for c in criteria(before_xml)
        if c.get("criteriatype") == CRITERION_TYPE_ACTIVITY
        and c.get("moduleinstance") == old_id
    ]
    if len(matches) != 1:
        raise FixtureError(
            f"Expected exactly one activity-completion criterion for cmid {old_id} ({idnumber}), "
            f"found {len(matches)}."
        )
    crit_id = matches[0]["id"]
    pattern = re.compile(
        rf'(<course_completion_criteria id="{crit_id}">.*?<moduleinstance>){old_id}(</moduleinstance>)',
        re.DOTALL,
    )
    after_xml, n = pattern.subn(rf"\g<1>{new}\g<2>", before_xml, count=1)
    if n != 1:
        raise FixtureError(
            "Could not make the one planned replacement in completion.xml."
        )

    before_bytes, after_bytes = before_xml.encode("utf-8"), after_xml.encode("utf-8")
    index = files[".ARCHIVE_INDEX"].data.decode("utf-8")
    idx_pat = re.compile(
        rf"^(completion\.xml\tf\t){len(before_bytes)}(\t)", re.MULTILINE
    )
    new_index, n_idx = idx_pat.subn(rf"\g<1>{len(after_bytes)}\g<2>", index)
    if n_idx != 1:
        raise FixtureError(
            ".ARCHIVE_INDEX has no single matching entry for completion.xml."
        )

    edited = []
    for m in members:
        if m.info.name == "completion.xml":
            edited.append(Member(m.info, after_bytes))
        elif m.info.name == ".ARCHIVE_INDEX":
            edited.append(Member(m.info, new_index.encode("utf-8")))
        else:
            edited.append(m)
    out = write_archive(edited, fmt)
    manifest = {
        "label": LABEL,
        "final_ck08_fixture": False,
        "note": "Candidate made from the input backup. The final fixture needs the merged B8.1 + B8.2 baseline.",
        "script": "scripts/b8_3/ck08_make_fixture.py",
        "criterion_id": crit_id,
        "activity_idnumber": idnumber,
        "old_moduleinstance": old_id,
        "new_moduleinstance": new,
        "input_sha256": sha256(raw),
        "output_sha256": sha256(out),
        "completion_xml_sha256_before": sha256(before_bytes),
        "completion_xml_sha256_after": sha256(after_bytes),
    }
    return out, manifest


def verify(
    input_raw: bytes | None, out_raw: bytes, manifest: dict[str, Any]
) -> list[str]:
    """Return the list of problems; empty means every check passed."""
    problems: list[str] = []
    if sha256(out_raw) != manifest.get("output_sha256"):
        problems.append("output SHA-256 differs from the manifest")
    members, _ = read_archive(out_raw)
    files = _by_name(members)
    if "completion.xml" not in files or "moodle_backup.xml" not in files:
        return [
            *problems,
            "completion.xml or moodle_backup.xml is missing from the output",
        ]
    acts = activities(members)
    new, old = manifest["new_moduleinstance"], manifest["old_moduleinstance"]
    if new in acts or any(f"_{new}/" in m.info.name for m in members):
        problems.append(f"cmid {new} still resolves to an activity")
    if old not in acts:
        problems.append(f"original activity {old} is gone (it must stay)")
    text = files["completion.xml"].data.decode("utf-8")
    if sha256(files["completion.xml"].data) != manifest["completion_xml_sha256_after"]:
        problems.append("completion.xml SHA-256 differs from the manifest")
    instances = [
        c.get("moduleinstance")
        for c in criteria(text)
        if c.get("criteriatype") == CRITERION_TYPE_ACTIVITY
    ]
    if instances.count(new) != 1 or old in instances:
        problems.append(
            "the criterion list is not as planned (one criterion on the new id, none on the old)"
        )
    if input_raw is not None:
        if sha256(input_raw) != manifest["input_sha256"]:
            problems.append(
                "input SHA-256 differs from the manifest (a different backup)"
            )
        before, _ = read_archive(input_raw)
        bf = _by_name(before)
        changed = sorted(
            n
            for n in set(bf) | set(files)
            if (bf.get(n) and bf[n].data) != (files.get(n) and files[n].data)
        )
        if changed != [".ARCHIVE_INDEX", "completion.xml"]:
            problems.append(
                f"members changed: {changed}; expected only .ARCHIVE_INDEX and completion.xml"
            )
        if [m.info.name for m in before] != [m.info.name for m in members]:
            problems.append("member list or order changed")
    return problems


REQUIRED_MANIFEST = (
    "input_sha256",
    "output_sha256",
    "completion_xml_sha256_before",
    "completion_xml_sha256_after",
)
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def load_manifest(path: Path) -> dict[str, Any]:
    """Read a manifest and refuse anything that is not one this script writes."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise FixtureError(f"{path.name} is not a readable manifest: {exc}") from exc
    if not isinstance(data, dict):
        raise FixtureError(f"{path.name} is not a manifest (expected a JSON object).")
    if data.get("label") != LABEL or data.get("final_ck08_fixture") is not False:
        raise FixtureError(
            f"{path.name} is not a manifest made by this script (label missing or changed)."
        )
    for key in REQUIRED_MANIFEST:
        if not isinstance(data.get(key), str) or not SHA_RE.match(data[key]):
            raise FixtureError(f"{path.name}: {key} is missing or not a SHA-256.")
    for key in (
        "old_moduleinstance",
        "new_moduleinstance",
        "criterion_id",
        "activity_idnumber",
    ):
        if not isinstance(data.get(key), str) or not data[key]:
            raise FixtureError(f"{path.name}: {key} is missing.")
    if (
        not data["new_moduleinstance"].isdigit()
        or not data["old_moduleinstance"].isdigit()
    ):
        raise FixtureError(f"{path.name}: the cmids must be whole numbers.")
    if data["output_sha256"] == data["input_sha256"]:
        raise FixtureError(
            f"{path.name}: output and input hashes are equal, so this is not a generated output."
        )
    return data  # type: ignore[no-any-return]


def write_new(path: Path, data: bytes) -> None:
    """Create a file that must not exist (O_EXCL: also refuses an existing or dangling symlink)."""
    try:
        with open(path, "xb") as fh:
            fh.write(data)
    except FileExistsError as exc:
        raise FixtureError(MSG_EXISTS.format(path=path)) from exc
    except OSError as exc:
        raise FixtureError(f"Could not write {path.name}: {exc}") from exc


def _manifest_path(out: Path) -> Path:
    return out.with_name(out.name + MANIFEST_SUFFIX)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__.split("\n")[0],
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument("--input", type=Path, help="source backup (.mbz); opened read-only")
    p.add_argument(
        "--out", type=Path, required=True, help="new backup to write (must not exist)"
    )
    p.add_argument(
        "--criterion-idnumber",
        default="course-feedback",
        help="activity whose criterion is redirected",
    )
    p.add_argument(
        "--new-id",
        help="cmid to use (default: highest cmid + 1000, checked to be unused)",
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="plan and verify in memory; write nothing",
    )
    mode.add_argument(
        "--check", action="store_true", help="read-only: verify an existing --out"
    )
    mode.add_argument(
        "--undo", action="store_true", help="delete --out and its manifest"
    )
    a = p.parse_args(argv)
    manifest_file = _manifest_path(a.out)

    try:
        if a.undo:
            if a.input and a.input.exists() and a.out.resolve() == a.input.resolve():
                raise FixtureError(MSG_SAME)
            if a.out.is_symlink() or not a.out.is_file() or not manifest_file.is_file():
                raise FixtureError(MSG_NO_MANIFEST.format(path=a.out))
            manifest = load_manifest(manifest_file)
            out_bytes = a.out.read_bytes()
            # Delete only a file that is exactly what this script generated: hash, then full verify.
            if sha256(out_bytes) != manifest["output_sha256"]:
                reasons = ["its SHA-256 differs from the manifest"]
            else:
                reasons = verify(None, out_bytes, manifest)
            if reasons:
                raise FixtureError(
                    MSG_UNDO_REFUSED.format(path=a.out, reasons="; ".join(reasons))
                )
            a.out.unlink()
            manifest_file.unlink()
            print(
                f"Removed {a.out.name} and its manifest. The input backup was not touched."
            )
            return 0

        if a.check:
            if not a.out.is_file() or not manifest_file.is_file():
                raise FixtureError(MSG_NO_MANIFEST.format(path=a.out))
            manifest = load_manifest(manifest_file)
            src = a.input.read_bytes() if a.input and a.input.exists() else None
            problems = verify(src, a.out.read_bytes(), manifest)
            for line in problems:
                print(f"FAIL: {line}")
            if problems:
                return 1
            scope = (
                "with the input comparison"
                if src
                else "without an input comparison (no --input)"
            )
            print(f"OK: {a.out.name} passes every check {scope}. {LABEL}")
            return 0

        if a.new_id is not None and not re.fullmatch(r"[1-9]\d*", a.new_id):
            raise FixtureError("--new-id must be a positive whole number.")
        if not a.input or not a.input.is_file():
            raise FixtureError(MSG_NO_INPUT.format(path=a.input))
        if a.out.resolve() == a.input.resolve():
            raise FixtureError(MSG_SAME)
        if os.path.lexists(a.out) or os.path.lexists(manifest_file):
            raise FixtureError(MSG_EXISTS.format(path=a.out))
        raw = a.input.read_bytes()
        out, manifest = make_fixture(raw, a.criterion_idnumber, a.new_id)
        problems = verify(raw, out, manifest)
        if problems:
            for line in problems:
                print(f"FAIL: {line}")
            return 1
        summary = (
            f"criterion {manifest['criterion_id']} ({manifest['activity_idnumber']}): "
            f"moduleinstance {manifest['old_moduleinstance']} -> {manifest['new_moduleinstance']}\n"
            f"  input  SHA-256 {manifest['input_sha256']}\n  output SHA-256 {manifest['output_sha256']}"
        )
        if a.dry_run:
            print(f"Dry run, nothing written. Would change {summary}")
            return 0
        write_new(a.out, out)
        try:
            write_new(
                manifest_file, (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
            )
        except FixtureError:
            a.out.unlink()  # never leave an output without its manifest
            raise
        print(
            f"Wrote {a.out.name} and {manifest_file.name}. Changed {summary}\n  {LABEL}"
        )
        return 0
    except (FixtureError, UnicodeDecodeError, OSError) as exc:
        print(f"Cannot continue: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

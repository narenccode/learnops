#!/usr/bin/env python3
"""Make the synthetic CK-08 fixture from a COPY of the merged B8.2 + B8.1 backup (PRD B8.3, C2.3).

The guide approved this as a scripted, repeatable edit of the backup file (issue #232, point 4).
It never touches Moodle.
This is a trusted, offline test-data tool: it uses the standard-library XML parser only because it also
refuses any DOCTYPE or ENTITY declaration, unsafe paths, links, duplicates and oversized entries. Do
not reuse it for uploaded backups (the checker uses defusedxml); do not weaken these checks. It reads an input `.mbz` and writes a new one; the input is never changed.

What it does, and nothing else: in `completion.xml`, ONE criterion's `<moduleinstance>` is set to
an activity id (cmid) that no activity in the backup has. The original activity stays in the
course. No `idnumber` is added to the criterion. Every other byte of every other file is copied
unchanged, and the archive is written deterministically, so the same input gives the same output
SHA-256 every time.

    make_ck08_fixture.py --input merged.mbz --target-idnumber wk-01-task \\
        --output ck-08.synthetic.mbz               # write the fixture and its report
    make_ck08_fixture.py ... --dry-run             # do all the work, write nothing
    make_ck08_fixture.py --input merged.mbz --output ck-08.synthetic.mbz --check
                                                   # read-only: verify an existing fixture

Undo: delete the two files it wrote (`<output>` and `<output>.report.json`). The input is never
modified, so there is nothing else to restore.

Exit codes: 0 done / check passed, 1 refused or check failed, 2 usage error.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import sys
import tarfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

SUFFIX = ".synthetic.mbz"
MAX_MEMBERS = 50_000
MAX_MEMBER_BYTES = 256 * 1024 * 1024
MAX_TOTAL_BYTES = 1024 * 1024 * 1024
_FORBIDDEN_XML = re.compile(rb"<!\s*(DOCTYPE|ENTITY)", re.IGNORECASE)
_MODINSTANCE = re.compile(
    rb"<moduleinstance\b[^>]*?(?:/>|>.*?</moduleinstance\s*>)", re.DOTALL
)
_ACTIVITY_MODULE = re.compile(r"activities/([^/]+)_(\d+)/module\.xml")


class FixtureError(Exception):
    """The input cannot be used; the message says what is wrong and what to do."""


@dataclass
class Archive:
    names: list[str]  # member order, kept so the output has the same layout
    infos: dict[str, tarfile.TarInfo]
    data: dict[str, bytes]  # file members only


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_xml(data: bytes, label: str) -> ET.Element:
    """Parse backup XML. A DTD or entity declaration is refused: Moodle backups never need one."""
    if _FORBIDDEN_XML.search(data):
        raise FixtureError(
            f"{label} declares a DOCTYPE or ENTITY. Backups never do; refusing it."
        )
    try:
        return ET.fromstring(data)
    except ET.ParseError as error:
        raise FixtureError(
            f"{label} is not valid XML ({error}). Use an unmodified backup."
        ) from error


def read_archive(path: Path) -> Archive:
    """Read a .mbz (gzip tar). Refuses unsafe paths, links, duplicates and oversized members."""
    try:
        archive = tarfile.open(path, "r:gz")
    except (OSError, tarfile.TarError) as error:
        raise FixtureError(
            f"{path} is not a readable .mbz (gzip tar): {error}"
        ) from error
    result = Archive([], {}, {})
    total = 0
    with archive:
        members = archive.getmembers()
        if len(members) > MAX_MEMBERS:
            raise FixtureError(
                f"{path} has more than {MAX_MEMBERS} entries; refusing it."
            )
        for member in members:
            name = member.name
            posix = PurePosixPath(name)
            if (
                posix.is_absolute()
                or ".." in posix.parts
                or "\\" in name
                or "\x00" in name
            ):
                raise FixtureError(f"Unsafe path in the archive: {name!r}.")
            if not (member.isfile() or member.isdir()):
                raise FixtureError(
                    f"Unsupported entry (link or device) in the archive: {name!r}."
                )
            if name in result.infos:
                raise FixtureError(f"Duplicate entry in the archive: {name!r}.")
            if member.size > MAX_MEMBER_BYTES:
                raise FixtureError(
                    f"{name!r} is larger than {MAX_MEMBER_BYTES} bytes; refusing it."
                )
            total += member.size
            if total > MAX_TOTAL_BYTES:
                raise FixtureError(
                    f"{path} expands past {MAX_TOTAL_BYTES} bytes; refusing it."
                )
            result.names.append(name)
            result.infos[name] = member
            if member.isfile():
                stream = archive.extractfile(member)
                if stream is None:
                    raise FixtureError(f"Cannot read {name!r} from the archive.")
                result.data[name] = stream.read()
    return result


def discover_activities(archive: Archive) -> dict[int, dict[str, str]]:
    """cmid -> {module, idnumber}, found from the backup's own `activities/<mod>_<cmid>/` folders.

    Nothing is assumed about which ids the B8.1 reference uses: whatever the backup holds is used.
    """
    found: dict[int, dict[str, str]] = {}
    for name in sorted(archive.data):
        match = _ACTIVITY_MODULE.fullmatch(name)
        if not match:
            continue
        module, cmid = match.group(1), int(match.group(2))
        root = parse_xml(archive.data[name], name)
        declared = root.get("id") or next(
            ((c.text or "").strip() for c in root if _local(c.tag) == "id"), ""
        )
        if declared != str(cmid):
            raise FixtureError(
                f"{name}: its id is {declared!r} but its folder says {cmid}. Use an unmodified backup."
            )
        folder = name.rsplit("/", 1)[0]
        idnumbers = {
            (node.text or "").strip()
            for other, payload in archive.data.items()
            if other.startswith(folder + "/") and other.endswith(".xml")
            for node in parse_xml(payload, other).iter()
            if _local(node.tag) == "idnumber" and (node.text or "").strip()
        }
        if len(idnumbers) > 1:
            raise FixtureError(
                f"{folder} has conflicting idnumbers {sorted(idnumbers)}."
            )
        found[cmid] = {"module": module, "idnumber": next(iter(idnumbers), "")}
    if not found:
        raise FixtureError(
            "No activities/<module>_<cmid>/module.xml found. Is this a course backup?"
        )
    return found


def completion_path(archive: Archive) -> str:
    """The course-level completion file. Section and activity completion files are not touched."""
    if "course/completion.xml" not in archive.data:
        raise FixtureError(
            "course/completion.xml is missing. Is this a full course backup?"
        )
    return "course/completion.xml"


def criterion_refs(root: ET.Element) -> list[tuple[ET.Element, ET.Element]]:
    """(criterion, moduleinstance) for every moduleinstance element, in document order."""
    return [
        (criterion, ref)
        for criterion in root.iter()
        for ref in criterion
        if _local(ref.tag) == "moduleinstance"
    ]


def _find_one_target(
    pairs: list[tuple[ET.Element, ET.Element]],
    inventory: dict[int, dict[str, str]],
    idnumber: str,
) -> tuple[int, int]:
    hits = []
    for index, (criterion, ref) in enumerate(pairs):
        text = (ref.text or "").strip()
        activity = inventory.get(int(text)) if text.isdigit() else None
        if activity and activity["idnumber"] == idnumber:
            module = [
                (c.text or "").strip() for c in criterion if _local(c.tag) == "module"
            ]
            if module and module != [activity["module"]]:
                raise FixtureError(
                    f"The criterion says module {module[0]!r}; the activity is {activity['module']!r}."
                )
            hits.append((index, int(text)))
    if len(hits) != 1:
        known = sorted(a["idnumber"] for a in inventory.values() if a["idnumber"]) or [
            "(none)"
        ]
        raise FixtureError(
            f"Expected exactly one completion criterion for the activity idnumber {idnumber!r}, "
            f"found {len(hits)}. Activity idnumbers in this backup: {', '.join(known)}."
        )
    return hits[0]


def _replace_kth(raw: bytes, k: int, new_value: int) -> bytes:
    spans = list(_MODINSTANCE.finditer(raw))
    span = spans[k]
    replaced = re.sub(
        rb">(\s*)\d+(\s*)<",
        rb">\g<1>" + str(new_value).encode() + rb"\g<2><",
        span.group(),
        count=1,
    )
    if replaced == span.group():
        raise FixtureError("Could not edit the moduleinstance value in place.")
    return raw[: span.start()] + replaced + raw[span.end() :]


def write_archive(archive: Archive, data: dict[str, bytes], path: Path) -> None:
    """Same members, same order and metadata; gzip header time fixed so the output is repeatable."""
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0, filename="") as gz:
        with tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tar:
            for name in archive.names:
                info = archive.infos[name]
                if info.isfile():
                    info.size = len(data[name])
                    tar.addfile(info, io.BytesIO(data[name]))
                else:
                    tar.addfile(info)
    path.write_bytes(buffer.getvalue())


def build(
    input_path: Path, idnumber: str
) -> tuple[Archive, dict[str, bytes], dict[str, Any]]:
    if not idnumber.strip():
        raise FixtureError("--target-idnumber must not be blank.")
    archive = read_archive(input_path)
    inventory = discover_activities(archive)
    name = completion_path(archive)
    raw = archive.data[name]
    pairs = criterion_refs(parse_xml(raw, name))
    if len(_MODINSTANCE.findall(raw)) != len(pairs):
        raise FixtureError(f"{name} has an unusual layout; the edit would not be safe.")
    index, old_cmid = _find_one_target(pairs, inventory, idnumber)
    used = set(inventory) | {
        int(r.text.strip()) for _, r in pairs if (r.text or "").strip().isdigit()
    }
    new_cmid = max(used) + 1
    edited = _replace_kth(raw, index, new_cmid)
    data = dict(archive.data)
    data[name] = edited
    report = {
        "fixture": "synthetic",
        "purpose": "B8.3 CK-08: one completion criterion refers to an activity id that does not exist",
        "moodle_modified": False,
        "input_sha256": sha256(input_path.read_bytes()),
        "completion_xml": name,
        "completion_xml_sha256_before": sha256(raw),
        "completion_xml_sha256_after": sha256(edited),
        "target_activity_idnumber": idnumber,
        "target_activity_module": inventory[old_cmid]["module"],
        "old_cmid": old_cmid,
        "new_unresolved_cmid": new_cmid,
        "criterion_idnumber_added": False,
        "original_activity_kept": True,
        "activities_in_backup": len(inventory),
        "note": (
            "Built from whatever ids this backup holds. CK-07 non-triggering is NOT verified here: "
            "it needs the checker and the merged B8.2 + B8.1 backup."
        ),
    }
    return archive, data, report


def check_fixture(input_path: Path, output_path: Path) -> list[str]:
    """Read-only: list what is wrong with an existing fixture (empty = it is a valid CK-08 edit)."""
    before, after = read_archive(input_path), read_archive(output_path)
    problems: list[str] = []
    if before.names != after.names:
        problems.append("The member list or order differs from the input.")
    changed = [
        n for n in before.data if n in after.data and before.data[n] != after.data[n]
    ]
    if changed != [completion_path(before)]:
        problems.append(
            f"Expected only completion.xml to differ; changed: {changed or 'nothing'}."
        )
        return problems
    inventory = discover_activities(after)
    old = criterion_refs(parse_xml(before.data[changed[0]], "input completion.xml"))
    new = criterion_refs(parse_xml(after.data[changed[0]], "output completion.xml"))
    if len(old) != len(new):
        return [*problems, "The number of criteria changed."]
    differing = [
        i
        for i, ((_, a), (_, b)) in enumerate(zip(old, new))
        if (a.text or "") != (b.text or "")
    ]
    if len(differing) != 1:
        return [
            *problems,
            f"Expected exactly one moduleinstance to change; {len(differing)} did.",
        ]
    value = (new[differing[0]][1].text or "").strip()
    if not value.isdigit() or int(value) in inventory:
        problems.append(
            f"The new moduleinstance {value!r} must be a number that no activity has."
        )
    if discover_activities(before).keys() != inventory.keys():
        problems.append("The set of activities changed.")
    old_crit, new_crit = old[differing[0]][0], new[differing[0]][0]
    old_fields = [
        (_local(c.tag), (c.text or "").strip())
        for c in old_crit
        if _local(c.tag) != "moduleinstance"
    ]
    new_fields = [
        (_local(c.tag), (c.text or "").strip())
        for c in new_crit
        if _local(c.tag) != "moduleinstance"
    ]
    if old_fields != new_fields:  # also catches an added idnumber
        problems.append(
            "A field other than moduleinstance changed (or an idnumber was added)."
        )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Make or check the synthetic CK-08 fixture."
    )
    parser.add_argument(
        "--input", required=True, type=Path, help="merged B8.2 + B8.1 .mbz (read only)"
    )
    parser.add_argument(
        "--output", required=True, type=Path, help=f"new file; must end in {SUFFIX}"
    )
    parser.add_argument(
        "--target-idnumber", help="idnumber of the activity whose criterion is edited"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="do everything but write nothing"
    )
    mode.add_argument(
        "--check", action="store_true", help="read-only: verify an existing --output"
    )
    args = parser.parse_args(argv)
    try:
        if not args.output.name.endswith(SUFFIX):
            raise FixtureError(
                f"The output name must end in {SUFFIX} so the file is labelled synthetic."
            )
        if args.input.resolve() == args.output.resolve():
            raise FixtureError("The output must be a different file from the input.")
        if args.check:
            problems = check_fixture(args.input, args.output)
            print(
                "\n".join(problems)
                if problems
                else "OK: a valid synthetic CK-08 edit of the input."
            )
            return 1 if problems else 0
        if not args.target_idnumber:
            parser.error("--target-idnumber is required unless --check is used")
        if args.output.exists() and not args.dry_run:
            raise FixtureError(
                f"{args.output} exists. Delete it first (that is the undo); never overwritten."
            )
        archive, data, report = build(args.input, args.target_idnumber)
        if args.dry_run:
            print(json.dumps({**report, "dry_run": True}, indent=2))
            return 0
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_archive(archive, data, args.output)
        report["output_sha256"] = sha256(args.output.read_bytes())
        problems = check_fixture(args.input, args.output)
        if problems:
            args.output.unlink()
            raise FixtureError(
                "Self-check failed, output removed: " + " ".join(problems)
            )
        Path(f"{args.output}.report.json").write_text(
            json.dumps(report, indent=2) + "\n", "utf-8"
        )
        print(json.dumps(report, indent=2))
        return 0
    except FixtureError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

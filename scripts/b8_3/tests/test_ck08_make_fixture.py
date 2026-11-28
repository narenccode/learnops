"""Tests for ck08_make_fixture.py on a tiny SYNTHETIC backup built here (no Moodle, no real .mbz).

They show the script edits exactly one criterion, writes nothing in --dry-run, refuses to overwrite,
and undoes only what it made. They do not show that a checker detects CK-08 (no checker exists).
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "b8_3" / "ck08_make_fixture.py"

BACKUP_XML = """<moodle_backup><contents><activities>
<activity><moduleid>5</moduleid><sectionid>1</sectionid><modulename>assign</modulename><title>A</title><directory>activities/assign_5</directory></activity>
<activity><moduleid>6</moduleid><sectionid>1</sectionid><modulename>feedback</modulename><title>F</title><directory>activities/feedback_6</directory></activity>
</activities></contents><settings><activity>assign_5</activity></settings></moodle_backup>"""
COMPLETION = """<course_completion>
  <course_completion_criteria id="1">
    <criteriatype>4</criteriatype>
    <module>assign</module>
    <moduleinstance>5</moduleinstance>
  </course_completion_criteria>
  <course_completion_criteria id="2">
    <criteriatype>4</criteriatype>
    <module>feedback</module>
    <moduleinstance>6</moduleinstance>
  </course_completion_criteria>
</course_completion>
"""


def _mbz(
    path: Path, completion: str = COMPLETION, backup_xml: str = BACKUP_XML
) -> None:
    files = {
        "moodle_backup.xml": backup_xml,
        "completion.xml": completion,
        "activities/assign_5/module.xml": '<module id="5"><idnumber>final-project</idnumber></module>',
        "activities/feedback_6/module.xml": '<module id="6"><idnumber>course-feedback</idnumber></module>',
    }
    index = "Moodle archive file index. Count: 4\n" + "".join(
        f"{n}\tf\t{len(c.encode())}\t1\n" for n, c in files.items()
    )
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for name, text in {".ARCHIVE_INDEX": index, **files}.items():
            info = tarfile.TarInfo(name)
            data = text.encode()
            info.size, info.mtime = len(data), 1
            tar.addfile(info, io.BytesIO(data))
    path.write_bytes(gzip.compress(buf.getvalue(), mtime=0))


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    src = tmp_path / "in.mbz"
    _mbz(src)
    r = _run("--input", str(src), "--out", str(tmp_path / "out.mbz"), "--dry-run")
    assert r.returncode == 0 and "nothing written" in r.stdout.lower()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["in.mbz"]


def test_build_changes_one_criterion_and_is_repeatable(tmp_path: Path) -> None:
    src = tmp_path / "in.mbz"
    _mbz(src)
    before = src.read_bytes()
    for name in ("a.mbz", "b.mbz"):
        assert _run("--input", str(src), "--out", str(tmp_path / name)).returncode == 0
    assert src.read_bytes() == before
    assert (tmp_path / "a.mbz").read_bytes() == (tmp_path / "b.mbz").read_bytes()
    manifest = json.loads((tmp_path / "a.mbz.manifest.json").read_text())
    assert manifest["final_ck08_fixture"] is False and manifest["label"].startswith(
        "SYNTHETIC"
    )
    assert (manifest["old_moduleinstance"], manifest["new_moduleinstance"]) == (
        "6",
        "1006",
    )
    with tarfile.open(tmp_path / "a.mbz") as tar:
        text = tar.extractfile("completion.xml").read().decode()  # type: ignore[union-attr]
    assert (
        "<moduleinstance>5</moduleinstance>" in text
        and "<moduleinstance>1006</moduleinstance>" in text
    )
    assert (
        _run(
            "--input", str(src), "--out", str(tmp_path / "a.mbz"), "--check"
        ).returncode
        == 0
    )


def test_refuses_overwrite_same_path_and_unknown_idnumber(tmp_path: Path) -> None:
    src, out = tmp_path / "in.mbz", tmp_path / "out.mbz"
    _mbz(src)
    assert _run("--input", str(src), "--out", str(out)).returncode == 0
    assert _run("--input", str(src), "--out", str(out)).returncode == 2
    assert _run("--input", str(src), "--out", str(src)).returncode == 2
    assert (
        _run(
            "--input",
            str(src),
            "--out",
            str(tmp_path / "x.mbz"),
            "--criterion-idnumber",
            "nope",
        ).returncode
        == 2
    )


def test_check_fails_on_tamper_and_undo_only_removes_own_files(tmp_path: Path) -> None:
    src, out = tmp_path / "in.mbz", tmp_path / "out.mbz"
    _mbz(src)
    assert _run("--input", str(src), "--out", str(out)).returncode == 0
    good = out.read_bytes()
    out.write_bytes(good + b"x")
    assert _run("--out", str(out), "--check").returncode == 1
    r = _run("--out", str(out), "--undo")
    assert r.returncode == 2 and out.exists()
    assert (
        "its SHA-256 differs from the manifest" in r.stderr
    )  # the hash is what failed
    out.write_bytes(good)
    assert _run("--out", str(out), "--undo").returncode == 0
    assert not out.exists() and src.exists()


# --- failure cases. Each one also proves the input backup is byte-identical afterwards. ---


def _fails_and_leaves_input(
    tmp_path: Path, src: Path, *args: str
) -> subprocess.CompletedProcess[str]:
    before = src.read_bytes()
    r = _run("--input", str(src), "--out", str(tmp_path / "out.mbz"), *args)
    assert r.returncode == 2, r.stdout + r.stderr
    assert "Traceback" not in r.stderr
    assert src.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "in.mbz"
    ]  # nothing half-written
    return r


def test_malformed_archives_are_refused(tmp_path: Path) -> None:
    src = tmp_path / "in.mbz"
    for bad in (b"not a gzip at all", gzip.compress(b"plain bytes, not a tar"), b""):
        src.write_bytes(bad)
        _fails_and_leaves_input(tmp_path, src)
    _mbz(src)
    src.write_bytes(src.read_bytes()[:-40])  # truncated gzip
    _fails_and_leaves_input(tmp_path, src)


def test_missing_or_duplicate_criteria_and_activities_are_refused(
    tmp_path: Path,
) -> None:
    src = tmp_path / "in.mbz"
    no_crit = COMPLETION.replace(
        "<moduleinstance>6</moduleinstance>", "<moduleinstance>99</moduleinstance>"
    )
    _mbz(src, completion=no_crit)
    _fails_and_leaves_input(tmp_path, src)
    dup_crit = COMPLETION.replace(
        "<moduleinstance>5</moduleinstance>", "<moduleinstance>6</moduleinstance>"
    )
    _mbz(src, completion=dup_crit)
    _fails_and_leaves_input(tmp_path, src)
    dup_act = BACKUP_XML.replace("<moduleid>5</moduleid>", "<moduleid>6</moduleid>")
    _mbz(src, backup_xml=dup_act)
    _fails_and_leaves_input(tmp_path, src)
    _mbz(src, completion="<course_completion/>")
    _fails_and_leaves_input(tmp_path, src)


def test_new_id_must_be_a_whole_number_and_unused(tmp_path: Path) -> None:
    src = tmp_path / "in.mbz"
    _mbz(src)
    for bad in ("abc", "0", "-3", "1030</moduleinstance>", "5", "6"):
        _fails_and_leaves_input(tmp_path, src, "--new-id", bad)


def test_dangling_symlink_output_is_not_written_through(tmp_path: Path) -> None:
    src = tmp_path / "in.mbz"
    _mbz(src)
    target = tmp_path / "elsewhere.mbz"
    (tmp_path / "out.mbz").symlink_to(target)
    r = _run("--input", str(src), "--out", str(tmp_path / "out.mbz"))
    assert r.returncode == 2 and not target.exists()


def test_invalid_manifests_are_refused_by_check_and_undo(tmp_path: Path) -> None:
    src, out = tmp_path / "in.mbz", tmp_path / "out.mbz"
    _mbz(src)
    assert _run("--input", str(src), "--out", str(out)).returncode == 0
    manifest_file = tmp_path / "out.mbz.manifest.json"
    good = json.loads(manifest_file.read_text())
    broken = [
        "{not json",
        "[]",
        json.dumps({k: v for k, v in good.items() if k != "output_sha256"}),
        json.dumps({**good, "label": "hand written"}),
        json.dumps({**good, "new_moduleinstance": "x"}),
        json.dumps({**good, "output_sha256": good["input_sha256"]}),
    ]
    for text in broken:
        manifest_file.write_text(text)
        for mode in ("--check", "--undo"):
            r = _run("--out", str(out), mode)
            assert r.returncode == 2 and "Traceback" not in r.stderr, (text, mode)
        assert out.exists() and manifest_file.exists()


def test_undo_never_touches_the_input_even_with_a_forged_manifest(
    tmp_path: Path,
) -> None:
    src = tmp_path / "in.mbz"
    _mbz(src)
    before = src.read_bytes()
    forged = {
        "label": "SYNTHETIC: scripted backup edit, not produced by Moodle (guide, issue #232 point 4)",
        "final_ck08_fixture": False,
        "criterion_id": "2",
        "activity_idnumber": "course-feedback",
        "old_moduleinstance": "6",
        "new_moduleinstance": "1006",
        "input_sha256": "0" * 64,
        "output_sha256": hashlib.sha256(before).hexdigest(),  # points at the real input
        "completion_xml_sha256_before": "1" * 64,
        "completion_xml_sha256_after": "2" * 64,
    }
    (tmp_path / "in.mbz.manifest.json").write_text(json.dumps(forged))
    r = _run("--out", str(src), "--undo")  # content does not verify as a fixture
    assert r.returncode == 2
    assert "not a file this script generated" in r.stderr
    assert (
        "its SHA-256 differs" not in r.stderr
    )  # the hash matches; the structure fails
    assert "criterion list is not as planned" in r.stderr
    assert (
        _run("--input", str(src), "--out", str(src), "--undo").returncode == 2
    )  # same file as input
    assert src.read_bytes() == before


def test_undo_refuses_a_symlinked_output(tmp_path: Path) -> None:
    src, out = tmp_path / "in.mbz", tmp_path / "out.mbz"
    _mbz(src)
    assert _run("--input", str(src), "--out", str(out)).returncode == 0
    link = tmp_path / "link.mbz"
    link.symlink_to(out)
    (tmp_path / "link.mbz.manifest.json").write_text(
        (tmp_path / "out.mbz.manifest.json").read_text()
    )
    assert _run("--out", str(link), "--undo").returncode == 2 and out.exists()

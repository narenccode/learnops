"""CK-08 fixture maker (PRD B8.3, C2.3): tests on a SYNTHETIC backup built in a temp folder.

These prove the tool's behaviour only. They do not use the real merged B8.2 + B8.1 backup, so they
do NOT show that the real fixture avoids CK-07 or that the checker finds anything.
"""

from __future__ import annotations

import builtins
import gzip
import hashlib
import importlib.util
import io
import json
import sys
import tarfile
from pathlib import Path
from types import ModuleType

import pytest

from .helpers import ROOT

TOOL = ROOT / "testdata" / "b8-3-planted-errors" / "make_ck08_fixture.py"

COMPLETION = b"""<?xml version="1.0" encoding="UTF-8"?>
<course_completion>
  <course_completion_criteria>
    <course_completion_criterion>
      <id>1</id><course>2</course><criteriatype>4</criteriatype>
      <module>assign</module><moduleinstance>11</moduleinstance>
    </course_completion_criterion>
    <course_completion_criterion>
      <id>2</id><course>2</course><criteriatype>4</criteriatype>
      <module>page</module><moduleinstance>12</moduleinstance>
    </course_completion_criterion>
  </course_completion_criteria>
</course_completion>
"""


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("make_ck08_fixture", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["make_ck08_fixture"] = module
    # No .pyc: the dataset tests scan this folder and must not find a __pycache__ in it.
    previous, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


tool = _load()


def _module_xml(cmid: int, name: str, idnumber: str) -> bytes:
    return (
        f'<module id="{cmid}" version="1"><modulename>{name}</modulename>'
        f"<idnumber>{idnumber}</idnumber></module>"
    ).encode()


def _members(completion: bytes = COMPLETION) -> dict[str, bytes]:
    # Ids deliberately differ from the B8.1 reference ids: the tool must discover them.
    return {
        "moodle_backup.xml": b"<moodle_backup/>",
        "course/completion.xml": completion,
        "activities/assign_11/module.xml": _module_xml(11, "assign", "wk-01-task"),
        "activities/page_12/module.xml": _module_xml(12, "page", "wk-01-guide"),
        "activities/page_12/page.xml": b"<activity><page><name>Guide</name></page></activity>",
    }


def _make_mbz(
    path: Path, members: dict[str, bytes], extra: list[tarfile.TarInfo] | None = None
) -> Path:
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0) as gz, tarfile.open(
        fileobj=gz, mode="w"
    ) as tar:
        for name, payload in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            tar.addfile(info, io.BytesIO(payload))
        for info in extra or []:
            tar.addfile(info, io.BytesIO(b""))
    path.write_bytes(buffer.getvalue())
    return path


def _read(path: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    with tarfile.open(path, "r:gz") as tar:
        for member in tar.getmembers():
            stream = tar.extractfile(member) if member.isfile() else None
            if stream is not None:
                result[member.name] = stream.read()
    return result


@pytest.fixture
def source(tmp_path: Path) -> Path:
    return _make_mbz(tmp_path / "merged.mbz", _members())


def _run(*args: str) -> int:
    return int(tool.main(list(args)))


def test_one_criterion_gets_an_unused_id_and_nothing_else_changes(
    source: Path, tmp_path: Path
) -> None:
    out = tmp_path / "ck-08.synthetic.mbz"
    assert (
        _run(
            "--input",
            str(source),
            "--output",
            str(out),
            "--target-idnumber",
            "wk-01-task",
        )
        == 0
    )
    before, after = _read(source), _read(out)
    assert [n for n in before if before[n] != after[n]] == ["course/completion.xml"]
    assert (
        b"<moduleinstance>13</moduleinstance>" in after["course/completion.xml"]
    )  # max(11, 12) + 1
    assert (
        b"<moduleinstance>12</moduleinstance>" in after["course/completion.xml"]
    )  # the other is intact
    assert (
        before["course/completion.xml"].replace(b">11<", b">13<")
        == after["course/completion.xml"]
    )
    assert "activities/assign_11/module.xml" in after  # the original activity is kept
    assert (
        b"idnumber" not in after["course/completion.xml"]
    )  # none is added to the criterion


def test_ids_come_from_the_backup_not_from_fixed_reference_values(
    tmp_path: Path,
) -> None:
    members = _members(COMPLETION.replace(b">11<", b">501<").replace(b">12<", b">502<"))
    members["activities/assign_501/module.xml"] = members.pop(
        "activities/assign_11/module.xml"
    ).replace(b'id="11"', b'id="501"')
    members["activities/page_502/module.xml"] = members.pop(
        "activities/page_12/module.xml"
    ).replace(b'id="12"', b'id="502"')
    members["activities/page_502/page.xml"] = members.pop("activities/page_12/page.xml")
    src, out = _make_mbz(tmp_path / "m.mbz", members), tmp_path / "x.synthetic.mbz"
    assert (
        _run(
            "--input",
            str(src),
            "--output",
            str(out),
            "--target-idnumber",
            "wk-01-guide",
        )
        == 0
    )
    assert (
        b"<moduleinstance>503</moduleinstance>" in _read(out)["course/completion.xml"]
    )


def test_report_records_both_hashes_and_the_synthetic_label(
    source: Path, tmp_path: Path
) -> None:
    out = tmp_path / "ck-08.synthetic.mbz"
    _run(
        "--input", str(source), "--output", str(out), "--target-idnumber", "wk-01-task"
    )
    report = json.loads(Path(f"{out}.report.json").read_text("utf-8"))
    assert report["fixture"] == "synthetic" and report["moodle_modified"] is False
    assert report["input_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert report["output_sha256"] == hashlib.sha256(out.read_bytes()).hexdigest()
    assert (
        report["completion_xml_sha256_before"] != report["completion_xml_sha256_after"]
    )
    assert (
        report["criterion_idnumber_added"] is False
        and report["original_activity_kept"] is True
    )
    assert "CK-07 non-triggering is NOT verified" in report["note"]


def test_output_is_repeatable_and_input_is_untouched(
    source: Path, tmp_path: Path
) -> None:
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    first, second = tmp_path / "a.synthetic.mbz", tmp_path / "b.synthetic.mbz"
    for out in (first, second):
        assert (
            _run(
                "--input",
                str(source),
                "--output",
                str(out),
                "--target-idnumber",
                "wk-01-task",
            )
            == 0
        )
    assert first.read_bytes() == second.read_bytes()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest


def test_dry_run_writes_nothing(
    source: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "ck-08.synthetic.mbz"
    assert (
        _run(
            "--input",
            str(source),
            "--output",
            str(out),
            "--target-idnumber",
            "wk-01-task",
            "--dry-run",
        )
        == 0
    )
    assert not out.exists() and not Path(f"{out}.report.json").exists()
    assert json.loads(capsys.readouterr().out)["dry_run"] is True


def test_check_accepts_the_tools_output_and_is_read_only(
    source: Path, tmp_path: Path
) -> None:
    out = tmp_path / "ck-08.synthetic.mbz"
    _run(
        "--input", str(source), "--output", str(out), "--target-idnumber", "wk-01-task"
    )
    stamp = out.stat().st_mtime_ns
    assert _run("--input", str(source), "--output", str(out), "--check") == 0
    assert out.stat().st_mtime_ns == stamp


def test_check_rejects_a_fixture_with_a_second_change(
    source: Path, tmp_path: Path
) -> None:
    out = tmp_path / "ck-08.synthetic.mbz"
    _run(
        "--input", str(source), "--output", str(out), "--target-idnumber", "wk-01-task"
    )
    tampered = _read(out)
    tampered["activities/page_12/page.xml"] = b"<activity/>"
    bad = _make_mbz(tmp_path / "bad.synthetic.mbz", tampered)
    assert _run("--input", str(source), "--output", str(bad), "--check") == 1


def test_check_rejects_an_edit_that_points_at_a_real_activity(
    source: Path, tmp_path: Path
) -> None:
    members = _members(
        COMPLETION.replace(b">11<", b">12<", 1)
    )  # resolves: not a CK-08 edit
    bad = _make_mbz(tmp_path / "bad.synthetic.mbz", members)
    assert _run("--input", str(source), "--output", str(bad), "--check") == 1


def test_existing_output_is_never_overwritten(source: Path, tmp_path: Path) -> None:
    out = tmp_path / "ck-08.synthetic.mbz"
    out.write_bytes(b"keep me")
    assert (
        _run(
            "--input",
            str(source),
            "--output",
            str(out),
            "--target-idnumber",
            "wk-01-task",
        )
        == 1
    )
    assert out.read_bytes() == b"keep me"


def test_undo_is_deleting_the_two_outputs(source: Path, tmp_path: Path) -> None:
    out = tmp_path / "ck-08.synthetic.mbz"
    _run(
        "--input", str(source), "--output", str(out), "--target-idnumber", "wk-01-task"
    )
    out.unlink()
    Path(f"{out}.report.json").unlink()
    assert (
        _run(
            "--input",
            str(source),
            "--output",
            str(out),
            "--target-idnumber",
            "wk-01-task",
        )
        == 0
    )


@pytest.mark.parametrize("target", ["nope", "  "])
def test_unknown_or_blank_target_is_refused(
    source: Path, tmp_path: Path, target: str
) -> None:
    out = tmp_path / "ck-08.synthetic.mbz"
    assert (
        _run("--input", str(source), "--output", str(out), "--target-idnumber", target)
        == 1
    )
    assert not out.exists()


def test_two_criteria_for_one_activity_are_refused(tmp_path: Path) -> None:
    doubled = COMPLETION.replace(b">12<", b">11<")
    src = _make_mbz(tmp_path / "m.mbz", _members(doubled))
    assert (
        _run(
            "--input",
            str(src),
            "--output",
            str(tmp_path / "x.synthetic.mbz"),
            "--target-idnumber",
            "wk-01-task",
        )
        == 1
    )


def test_output_must_be_labelled_synthetic_and_differ_from_input(
    source: Path, tmp_path: Path
) -> None:
    assert (
        _run(
            "--input",
            str(source),
            "--output",
            str(tmp_path / "plain.mbz"),
            "--target-idnumber",
            "wk-01-task",
        )
        == 1
    )
    assert (
        _run(
            "--input",
            str(source),
            "--output",
            str(source),
            "--target-idnumber",
            "wk-01-task",
        )
        == 1
    )


def test_activity_folder_id_mismatch_is_refused(tmp_path: Path) -> None:
    members = _members()
    members["activities/assign_11/module.xml"] = _module_xml(99, "assign", "wk-01-task")
    src = _make_mbz(tmp_path / "m.mbz", members)
    assert (
        _run(
            "--input",
            str(src),
            "--output",
            str(tmp_path / "x.synthetic.mbz"),
            "--target-idnumber",
            "wk-01-task",
        )
        == 1
    )


@pytest.mark.parametrize("name", ["../evil.xml", "/abs.xml", "a\\b.xml"])
def test_unsafe_archive_paths_are_refused(tmp_path: Path, name: str) -> None:
    src = _make_mbz(tmp_path / "m.mbz", {**_members(), name: b"x"})
    assert (
        _run(
            "--input",
            str(src),
            "--output",
            str(tmp_path / "x.synthetic.mbz"),
            "--target-idnumber",
            "wk-01-task",
        )
        == 1
    )


def test_links_and_duplicates_are_refused(tmp_path: Path) -> None:
    link = tarfile.TarInfo("activities/link")
    link.type = tarfile.SYMTYPE
    link.linkname = "/etc/passwd"
    src = _make_mbz(tmp_path / "m.mbz", _members(), extra=[link])
    out = tmp_path / "x.synthetic.mbz"
    assert (
        _run(
            "--input", str(src), "--output", str(out), "--target-idnumber", "wk-01-task"
        )
        == 1
    )
    dup = tarfile.TarInfo("moodle_backup.xml")
    src2 = _make_mbz(tmp_path / "d.mbz", _members(), extra=[dup])
    assert (
        _run(
            "--input",
            str(src2),
            "--output",
            str(out),
            "--target-idnumber",
            "wk-01-task",
        )
        == 1
    )


def test_xml_with_an_entity_declaration_is_refused(tmp_path: Path) -> None:
    hostile = b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><course_completion>&a;</course_completion>'
    src = _make_mbz(tmp_path / "m.mbz", _members(hostile))
    assert (
        _run(
            "--input",
            str(src),
            "--output",
            str(tmp_path / "x.synthetic.mbz"),
            "--target-idnumber",
            "wk-01-task",
        )
        == 1
    )


def test_not_a_gzip_tar_is_refused(tmp_path: Path) -> None:
    bad = tmp_path / "m.mbz"
    bad.write_bytes(b"not an archive")
    assert (
        _run(
            "--input",
            str(bad),
            "--output",
            str(tmp_path / "x.synthetic.mbz"),
            "--target-idnumber",
            "wk-01-task",
        )
        == 1
    )


def _build(source: Path, out: Path) -> None:
    assert (
        _run(
            "--input",
            str(source),
            "--output",
            str(out),
            "--target-idnumber",
            "wk-01-task",
        )
        == 0
    )


def test_check_rejects_a_change_elsewhere_in_completion_xml(
    source: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Review finding 1: --check must accept only the exact expected output, byte for byte.

    The tampering below changes the SECOND criterion's text by one space, which the field-by-field
    comparison of the edited criterion alone does not see.
    """
    out = tmp_path / "ck-08.synthetic.mbz"
    _build(source, out)
    assert _run("--input", str(source), "--output", str(out), "--check") == 0
    members = _read(out)
    members["course/completion.xml"] = members["course/completion.xml"].replace(
        b"<id>2</id>", b"<id>2 </id>"
    )
    tampered = _make_mbz(tmp_path / "tampered.synthetic.mbz", members)
    capsys.readouterr()
    assert _run("--input", str(source), "--output", str(tampered), "--check") == 1
    assert "more than the one moduleinstance value" in capsys.readouterr().out


def test_existing_report_file_is_never_overwritten(
    source: Path, tmp_path: Path
) -> None:
    """Review finding 2: a leftover <output>.report.json stops the run before anything is written."""
    out = tmp_path / "ck-08.synthetic.mbz"
    report = Path(f"{out}.report.json")
    report.write_text("keep me", encoding="utf-8")
    assert (
        _run(
            "--input",
            str(source),
            "--output",
            str(out),
            "--target-idnumber",
            "wk-01-task",
        )
        == 1
    )
    assert report.read_text(encoding="utf-8") == "keep me"
    assert not out.exists()


def test_failed_report_write_removes_the_output(
    source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "ck-08.synthetic.mbz"
    real_open = builtins.open

    def failing_open(file: object, *args: object, **kwargs: object) -> object:
        if str(file).endswith(".report.json"):
            raise OSError("disk full (simulated)")
        return real_open(file, *args, **kwargs)  # type: ignore[call-overload]

    monkeypatch.setattr(builtins, "open", failing_open)
    assert (
        _run(
            "--input",
            str(source),
            "--output",
            str(out),
            "--target-idnumber",
            "wk-01-task",
        )
        == 1
    )
    monkeypatch.undo()
    assert not out.exists()
    assert not Path(f"{out}.report.json").exists()

"""B8.1 template course: the badge image and the download script (PRD B8.1; guide, Issue #55,
2026-11-18, P9b, P24, P33).

Nothing here needs Moodle or the network: the download is tested against a local file:// source.
The .mbz itself, its restore and the merge test are PENDING MOODLE LAB (see the B8.1 README).
"""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

from .helpers import ROOT

DATASET_DIR = ROOT / "testdata" / "b8-1-template-course"


def _load(name: str) -> ModuleType:
    # The folder name has hyphens, so the scripts are loaded by path, not imported.
    spec = importlib.util.spec_from_file_location(
        f"b8_1_{name}", DATASET_DIR / f"{name}.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


badge = _load("make_badge")
download = _load("download")


# --- badge image (P9b) -------------------------------------------------------------------------


def test_committed_badge_matches_its_generator() -> None:
    assert badge.main(["--check"]) == 0


def test_badge_is_a_square_rgb_png() -> None:
    data = (DATASET_DIR / "badge.png").read_bytes()
    assert data.startswith(badge.SIGNATURE)
    width, height = (
        int.from_bytes(data[16:20], "big"),
        int.from_bytes(data[20:24], "big"),
    )
    assert width == height == badge.SIZE


def test_badge_check_catches_another_image(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Negative control: --check fails for a valid PNG with other pixels, junk, or no file."""
    other = tmp_path / "other.png"
    with monkeypatch.context() as patch:
        patch.setattr(badge, "FILL", bytes((0xFF, 0x00, 0x00)))
        other.write_bytes(badge.badge_png())
    assert badge.main(["--check"], target=other) == 1
    junk = tmp_path / "junk.png"
    junk.write_bytes(badge.SIGNATURE + b"junk")
    assert badge.main(["--check"], target=junk) == 1
    assert badge.main(["--check"], target=tmp_path / "missing.png") == 1


def test_badge_dry_run_writes_nothing(tmp_path: Path) -> None:
    target = tmp_path / "badge.png"
    assert badge.main(["--dry-run"], target=target) == 0
    assert not target.exists()


def test_badge_writes_a_file_that_passes_check(tmp_path: Path) -> None:
    target = tmp_path / "badge.png"
    assert badge.main([], target=target) == 0
    assert badge.main(["--check"], target=target) == 0


# --- download script (P24, P33) -----------------------------------------------------------------


@pytest.fixture
def release(tmp_path: Path) -> tuple[str, str]:
    """A stand-in release asset on disk, as a file:// URL, and its SHA-256."""
    asset = tmp_path / "release" / "asset.mbz"
    asset.parent.mkdir()
    asset.write_bytes(b"not a real backup, test bytes only")
    return asset.as_uri(), hashlib.sha256(asset.read_bytes()).hexdigest()


def test_no_recorded_sha_refuses_and_writes_nothing(
    tmp_path: Path, release: tuple[str, str]
) -> None:
    assert download.SHA256 is None  # PENDING MOODLE LAB until the .mbz is uploaded
    target = tmp_path / "b.mbz"
    assert download.main([], target=target, source=release[0]) == 2
    assert not target.exists() and not list(tmp_path.glob("*.part"))


def test_download_verifies_and_keeps_no_partial_file(
    tmp_path: Path, release: tuple[str, str]
) -> None:
    source, sha = release
    target = tmp_path / "b.mbz"
    assert download.main([], target=target, source=source, expected=sha) == 0
    assert target.is_file() and not list(tmp_path.glob("*.part"))
    assert download.main(["--check"], target=target, expected=sha) == 0


def test_wrong_sha_removes_the_partial_file(
    tmp_path: Path, release: tuple[str, str]
) -> None:
    target = tmp_path / "b.mbz"
    assert download.main([], target=target, source=release[0], expected="0" * 64) == 1
    assert not target.exists() and not list(tmp_path.glob("*.part"))


def test_failed_download_removes_the_partial_file(tmp_path: Path) -> None:
    target = tmp_path / "b.mbz"
    missing = (tmp_path / "nowhere.mbz").as_uri()
    assert download.main([], target=target, source=missing, expected="0" * 64) == 2
    assert not target.exists() and not list(tmp_path.glob("*.part"))


def test_check_reports_a_changed_or_missing_file(
    tmp_path: Path, release: tuple[str, str]
) -> None:
    target = tmp_path / "b.mbz"
    target.write_bytes(b"something else")
    assert download.main(["--check"], target=target, expected=release[1]) == 1
    assert (
        download.main(["--check"], target=tmp_path / "none.mbz", expected=release[1])
        == 2
    )
    assert target.read_bytes() == b"something else"  # --check writes nothing


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    target = tmp_path / "b.mbz"
    assert download.main(["--dry-run"], target=target) == 0
    assert not target.exists()


def test_release_names_follow_the_guides_rule() -> None:
    assert download.TAG == "testdata-b8-1-v1"
    assert download.ASSET == "b8-1-template-course.v1.mbz"
    assert download.source_url().endswith(
        f"/releases/download/{download.TAG}/{download.ASSET}"
    )

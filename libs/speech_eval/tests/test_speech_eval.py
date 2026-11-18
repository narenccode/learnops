"""Software tests for libs/speech_eval, using made-up text only.

These tests show that the WER arithmetic, the input checks and the official-run gates work. They
are NOT a speech-model evaluation and are NOT G-6 evidence: no model, no B8.5 recording and no
real transcript is involved.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from speech_eval import edit_counts, evaluate, load_run, render_report
from speech_eval.__main__ import main
from speech_eval.inputs import OFFICIAL_NORMALISERS, dataset_inventory, dataset_status
from speech_eval.wer import NORMALISERS

REPO_ROOT = Path(__file__).resolve().parents[3]


def w(text: str) -> list[str]:
    return text.split()


# --- WER arithmetic -------------------------------------------------------------------------


def test_identical_text_has_zero_errors() -> None:
    c = edit_counts(w("a b c"), w("a b c"))
    assert (c.errors, c.wer) == (0, 0.0)


@pytest.mark.parametrize(
    ("ref", "hyp", "s", "d", "i"),
    [
        ("a b c d", "a x c d", 1, 0, 0),
        ("a b c d", "a b d", 0, 1, 0),
        ("a b c", "a b x c", 0, 0, 1),
        ("a b c", "", 0, 3, 0),
        ("a b c", "x y z", 3, 0, 0),
    ],
)
def test_substitutions_deletions_insertions(
    ref: str, hyp: str, s: int, d: int, i: int
) -> None:
    c = edit_counts(w(ref), w(hyp))
    assert (c.substitutions, c.deletions, c.insertions) == (s, d, i)
    assert c.errors == s + d + i


def test_wer_can_exceed_one() -> None:
    assert edit_counts(w("a"), w("x y z")).wer == 3.0


def test_empty_reference_is_undefined() -> None:
    with pytest.raises(ValueError, match="empty reference"):
        _ = edit_counts([], w("a")).wer


def test_pooled_wer_is_not_the_mean_of_lecture_wers() -> None:
    # lecture-01: 1 error in 1 word (100%); lecture-02: 0 errors in 9 words (0%).
    result = evaluate(
        [
            ("lecture-01", "a", "x"),
            ("lecture-02", "a b c d e f g h i", "a b c d e f g h i"),
        ]
    )
    assert result.pooled.errors == 1
    assert result.pooled.reference_words == 10
    assert result.pooled.wer == pytest.approx(
        0.1
    )  # the mean of lecture WERs would be 0.5


def test_unknown_normaliser_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown normaliser"):
        evaluate([("lecture-01", "a", "a")], "made-up")


def test_oversized_input_is_refused_not_hung() -> None:
    with pytest.raises(ValueError, match="too large"):
        edit_counts(["a"] * 6000, ["a"] * 6000)


# --- Input validation -----------------------------------------------------------------------


def make_run(tmp_path: Path, **overrides: object) -> Path:
    (tmp_path / "ref").mkdir(exist_ok=True)
    (tmp_path / "hyp").mkdir(exist_ok=True)
    (tmp_path / "ref" / "lecture-01.txt").write_text(
        "synthetic one two three\n", "utf-8"
    )
    (tmp_path / "hyp" / "lecture-01.txt").write_text(
        "synthetic one too three\n", "utf-8"
    )
    doc: dict[str, object] = {
        "format_version": 1,
        "mode": "synthetic-test",
        "normaliser": "unnormalised-whitespace",
        "lectures": [
            {
                "id": "lecture-01",
                "reference": "ref/lecture-01.txt",
                "hypothesis": "hyp/lecture-01.txt",
            }
        ],
    }
    doc.update(overrides)
    path = tmp_path / "run.json"
    path.write_text(json.dumps(doc), "utf-8")
    return path


def test_a_valid_synthetic_run_loads_and_reports(tmp_path: Path) -> None:
    run = load_run(make_run(tmp_path))
    assert run.errors == []
    result = evaluate(
        [(x.lecture_id, x.reference_text, x.hypothesis_text) for x in run.lectures]
    )
    report = render_report(run, result)
    assert "SYNTHETIC SOFTWARE TEST" in report
    assert "NOT G-6 evidence" in report
    assert "WER target (G-6): **PENDING**" in report
    assert "Acceptance result (C4.7): **PENDING**" in report
    assert "25.00%" in report
    assert "synthetic one" not in report  # counts only, never transcript text


@pytest.mark.parametrize(
    ("path", "message"),
    [
        ("https://example.invalid/a.txt", "relative"),
        ("/etc/a.txt", "relative"),
        ("C:/a.txt", "relative"),
        ("ref\\a.txt", "relative"),
        ("../a.txt", "'..'"),
        ("ref/lecture-01.wav", "no media or audio"),
        ("ref/lecture-01.mp4", "no media or audio"),
        ("ref/missing.txt", "file not found"),
    ],
)
def test_bad_paths_are_refused(tmp_path: Path, path: str, message: str) -> None:
    lecture = {
        "id": "lecture-01",
        "reference": path,
        "hypothesis": "hyp/lecture-01.txt",
    }
    run = load_run(make_run(tmp_path, lectures=[lecture]))
    assert any(message in e for e in run.errors), run.errors
    assert run.lectures == []


def test_symlink_or_junction_escape_is_refused(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "x.txt").write_text("secret words", "utf-8")
    inside = tmp_path / "inside"
    inside.mkdir()
    try:
        (inside / "link").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks not available")
    lecture = {
        "id": "lecture-01",
        "reference": "link/x.txt",
        "hypothesis": "link/x.txt",
    }
    run = load_run(make_run(inside, lectures=[lecture]))
    assert any("leaves the description file's folder" in e for e in run.errors)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("PENDING: not typed yet\n", "PENDING placeholder"),
        ("hello\nPENDING later\n", "PENDING placeholder"),
        ("   \n\n", "empty"),
    ],
)
def test_placeholder_and_empty_files_are_refused(
    tmp_path: Path, content: str, message: str
) -> None:
    path = make_run(tmp_path)
    (tmp_path / "ref" / "lecture-01.txt").write_text(content, "utf-8")
    run = load_run(path)
    assert any(message in e for e in run.errors), run.errors


def test_non_utf8_and_bad_json_are_refused(tmp_path: Path) -> None:
    path = make_run(tmp_path)
    (tmp_path / "ref" / "lecture-01.txt").write_bytes(b"\xff\xfe\x00bad")
    assert any("not UTF-8" in e for e in load_run(path).errors)
    (tmp_path / "hyp" / "lecture-01.json").write_text(
        '{"segments": [{"nope": 1}]}', "utf-8"
    )
    lecture = {
        "id": "lecture-01",
        "reference": "ref/lecture-01.txt",
        "hypothesis": "hyp/lecture-01.json",
    }
    path = make_run(tmp_path, lectures=[lecture])
    (tmp_path / "ref" / "lecture-01.txt").write_text("fine words", "utf-8")
    assert any("segments[] with start and text" in e for e in load_run(path).errors)


def test_b54_json_hypothesis_is_read(tmp_path: Path) -> None:
    segments = {
        "segments": [
            {"start": 0.0, "end": 1.0, "text": "synthetic one"},
            {"start": 1.0, "end": 2.0, "text": "too three"},
        ]
    }
    (tmp_path / "hyp").mkdir()
    (tmp_path / "hyp" / "lecture-01.json").write_text(json.dumps(segments), "utf-8")
    lecture = {
        "id": "lecture-01",
        "reference": "ref/lecture-01.txt",
        "hypothesis": "hyp/lecture-01.json",
    }
    run = load_run(make_run(tmp_path, lectures=[lecture]))
    assert run.errors == []
    assert run.lectures[0].hypothesis_text == "synthetic one too three"


def test_bad_ids_duplicates_mode_and_normaliser(tmp_path: Path) -> None:
    good = {
        "id": "lecture-01",
        "reference": "ref/lecture-01.txt",
        "hypothesis": "hyp/lecture-01.txt",
    }
    run = load_run(
        make_run(
            tmp_path,
            lectures=[good, good, {**good, "id": "intro"}],
            mode="x",
            normaliser="y",
        )
    )
    joined = " | ".join(run.errors)
    for expected in (
        "duplicate id",
        "lecture-NN",
        "mode must be",
        "normaliser must be",
    ):
        assert expected in joined


def test_bad_description_files(tmp_path: Path) -> None:
    assert load_run(tmp_path / "missing.json").errors
    bad = tmp_path / "bad.json"
    bad.write_text("not json", "utf-8")
    assert load_run(bad).errors
    bad.write_text(json.dumps({"format_version": 2}), "utf-8")
    assert "format_version" in load_run(bad).errors[0]


# --- Official-run gates ---------------------------------------------------------------------


def full_official(tmp_path: Path) -> Path:
    run = {
        k: "x"
        for k in (
            "engine",
            "model",
            "engine_version",
            "hardware",
            "decoding_settings",
            "operator",
        )
    }
    run["date"] = "2026-01-01"
    approvals = {
        k: "x"
        for k in (
            "normalisation_rules",
            "evaluation_method",
            "speech_engine_confirmed",
            "audio_use_permitted",
        )
    }
    return make_run(tmp_path, mode="official", run=run, approvals=approvals)


def test_the_repository_dataset_is_still_pending() -> None:
    # Fails on purpose the day B8.5 becomes COMPLETE: then re-check the official-run gates.
    assert dataset_status(REPO_ROOT) == "PENDING"


def test_official_mode_is_refused_today(tmp_path: Path) -> None:
    run = load_run(full_official(tmp_path), repo_root=REPO_ROOT)
    joined = " | ".join(run.errors)
    assert "no normaliser is approved yet" in joined
    assert "dataset status is PENDING, not COMPLETE" in joined
    assert (
        OFFICIAL_NORMALISERS == frozenset()
    )  # fails on purpose when someone adds one: cite the decision


def test_official_mode_needs_run_details_and_approvals(tmp_path: Path) -> None:
    path = make_run(
        tmp_path, mode="official", run={}, approvals={"normalisation_rules": "PENDING"}
    )
    run = load_run(path, REPO_ROOT)
    joined = " | ".join(run.errors)
    assert "run.engine is missing or PENDING" in joined
    assert "approvals.normalisation_rules is missing or PENDING" in joined
    assert "approvals.audio_use_permitted is missing or PENDING" in joined


def official_repo(
    tmp_path: Path,
    count: int = 5,
    consent: str = "`0004` speaker-01",
    review: str = "checked",
) -> tuple[Path, Path, dict[str, object]]:
    """A fake repository with a COMPLETE B8.5 inventory, and an official run description."""
    root = tmp_path / "repo"
    data = root / "testdata" / "b8-5-lecture-videos"
    (root / "hyp").mkdir(parents=True)
    rows, lectures = [], []
    for n in range(1, count + 1):
        lid = f"lecture-{n:02d}"
        folder = data / "lectures" / lid
        folder.mkdir(parents=True)
        (folder / "transcript.en.txt").write_text("reference words here\n", "utf-8")
        (root / "hyp" / f"{lid}.txt").write_text("reference word here\n", "utf-8")
        transcript = f"b8-5-lecture-videos/lectures/{lid}/transcript.en.txt"
        rows.append(
            f"| {lid} | T | S | 60 | f | abc | `{transcript}` | `{transcript}` "
            f"| {consent} | {review} |"
        )
        lectures.append(
            {
                "id": lid,
                "reference": f"testdata/{transcript}",
                "hypothesis": f"hyp/{lid}.txt",
            }
        )
    header = (
        "| ID | Title | Speaker | Duration | File | SHA | Outline | Transcript "
        "| Consent | Review |"
    )
    rule = "|---|---|---|---|---|---|---|---|---|---|"
    # The real layout: the set README holds the Status line and no lecture rows; the inventory
    # table is in testdata/README.md.
    (data / "README.md").write_text(
        "**Status: COMPLETE.**\n\nThe inventory is the table in testdata/README.md.\n",
        "utf-8",
    )
    (root / "testdata" / "README.md").write_text(
        "# Test data\n\n" + "\n".join([header, rule, *rows]) + "\n", "utf-8"
    )
    doc: dict[str, object] = {
        "format_version": 1,
        "mode": "official",
        "normaliser": "unnormalised-whitespace",
        "lectures": lectures,
        "run": {
            "engine": "e",
            "model": "m",
            "engine_version": "1",
            "hardware": "h",
            "decoding_settings": "d",
            "date": "2026-11-20",
            "operator": "o",
        },
        "approvals": {
            "normalisation_rules": "docs/decisions/0011-normalisation.md",
            "evaluation_method": "#98",
            "speech_engine_confirmed": "#98",
            "audio_use_permitted": "https://github.com/o/r/issues/1#issuecomment-2",
        },
    }
    return root, root / "run.json", doc


def official_errors(
    root: Path, path: Path, doc: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> list[str]:
    monkeypatch.setattr(
        "speech_eval.inputs.OFFICIAL_NORMALISERS",
        frozenset({"unnormalised-whitespace"}),
    )
    path.write_text(json.dumps(doc), "utf-8")
    return load_run(path, repo_root=root).errors


def first_lecture(doc: dict[str, object]) -> dict[str, str]:
    lectures = doc["lectures"]
    assert isinstance(lectures, list)
    first: dict[str, str] = lectures[0]
    return first


def test_the_real_repository_inventory_is_parsed() -> None:
    # Regression test: the inventory table is in testdata/README.md, not in the set README.
    inventory = dataset_inventory(REPO_ROOT)
    assert inventory is not None
    assert sorted(inventory) == [f"lecture-{n:02d}" for n in range(1, 6)]
    for lecture_id, row in inventory.items():
        folder = f"b8-5-lecture-videos/lectures/{lecture_id}"
        assert row["transcript"] == f"{folder}/transcript.en.txt"
        assert set(row) == {"transcript", "consent", "review"}
        assert row["consent"] and row["review"]  # PENDING today; never empty
    assert (REPO_ROOT / "testdata" / inventory["lecture-01"]["transcript"]).is_file()


def test_the_fixture_has_the_real_two_file_layout(tmp_path: Path) -> None:
    root, _, _ = official_repo(tmp_path)
    assert (
        dataset_inventory(root) is not None and len(dataset_inventory(root) or {}) == 5
    )
    set_readme = root / "testdata" / "b8-5-lecture-videos" / "README.md"
    assert "| lecture-" not in set_readme.read_text("utf-8")
    assert dataset_status(root) == "COMPLETE"


def test_official_mode_passes_gates_only_with_everything(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Simulate the future state: a COMPLETE inventory of five checked lectures and an approved
    # normaliser. Every other test below removes exactly one of these conditions.
    root, path, doc = official_repo(tmp_path)
    assert official_errors(root, path, doc, monkeypatch) == []
    run = load_run(path, repo_root=root)
    result = evaluate(
        [(x.lecture_id, x.reference_text, x.hypothesis_text) for x in run.lectures]
    )
    report = render_report(run, result)
    assert "OFFICIAL RUN" in report
    assert "Acceptance result (C4.7): **PENDING**" in report  # the tool never decides


def test_official_mode_refuses_fewer_than_five_lectures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for count in (1, 4):
        root, path, doc = official_repo(tmp_path / f"c{count}", count=count)
        errors = official_errors(root, path, doc, monkeypatch)
        assert any("at least 5 lectures" in e for e in errors), errors


def test_official_mode_refuses_ids_outside_the_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, path, doc = official_repo(tmp_path)
    first_lecture(doc)["id"] = "lecture-09"
    errors = official_errors(root, path, doc, monkeypatch)
    assert any("lecture-09 is not in the B8.5 inventory" in e for e in errors), errors


def test_official_mode_refuses_a_reference_that_is_not_the_inventory_transcript(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, path, doc = official_repo(tmp_path)
    (root / "my-reference.txt").write_text("some other words\n", "utf-8")
    first_lecture(doc)["reference"] = "my-reference.txt"
    errors = official_errors(root, path, doc, monkeypatch)
    assert any("reference must be the transcript" in e for e in errors), errors


@pytest.mark.parametrize(
    ("consent", "review", "message"),
    [
        ("PENDING", "checked", "no consent entry"),
        ("`0004` speaker-01", "pending", "transcript review is not 'checked'"),
    ],
)
def test_official_mode_needs_consent_and_checked_transcripts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    consent: str,
    review: str,
    message: str,
) -> None:
    root, path, doc = official_repo(tmp_path, consent=consent, review=review)
    errors = official_errors(root, path, doc, monkeypatch)
    assert any(message in e for e in errors), errors


@pytest.mark.parametrize(
    "value", ["ok", "x", "see the chat", "#", "docs/decisions/x.md"]
)
def test_official_approvals_must_look_like_references(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    root, path, doc = official_repo(tmp_path)
    approvals = doc["approvals"]
    assert isinstance(approvals, dict)
    approvals["evaluation_method"] = value
    errors = official_errors(root, path, doc, monkeypatch)
    assert any("approvals.evaluation_method must be a reference" in e for e in errors)


@pytest.mark.parametrize("value", ["x", "2026-13-45", "2026-1-1", "20/11/2026"])
def test_official_run_date_must_be_a_real_iso_date(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    root, path, doc = official_repo(tmp_path)
    run = doc["run"]
    assert isinstance(run, dict)
    run["date"] = value
    errors = official_errors(root, path, doc, monkeypatch)
    assert any("run.date must be a real date" in e for e in errors), errors


def test_report_escapes_table_cells(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, path, doc = official_repo(tmp_path)
    run = doc["run"]
    assert isinstance(run, dict)
    run["operator"] = "a|b\nc"
    assert official_errors(root, path, doc, monkeypatch) == []
    loaded = load_run(path, repo_root=root)
    result = evaluate(
        [(x.lecture_id, x.reference_text, x.hypothesis_text) for x in loaded.lectures]
    )
    assert "| operator | a\\|b c |" in render_report(loaded, result)


# --- B5.4 transcripts: order and emptiness --------------------------------------------------


def hypothesis_json(tmp_path: Path, document: object) -> Path:
    (tmp_path / "hyp").mkdir(exist_ok=True)
    (tmp_path / "hyp" / "lecture-01.json").write_text(json.dumps(document), "utf-8")
    lecture = {
        "id": "lecture-01",
        "reference": "ref/lecture-01.txt",
        "hypothesis": "hyp/lecture-01.json",
    }
    return make_run(tmp_path, lectures=[lecture])


def test_out_of_order_segments_are_sorted_by_start(tmp_path: Path) -> None:
    # PRD B5.4: segments may arrive out of order; a consumer sorts them by start.
    segments = [
        {"start": 2.0, "end": 3.0, "text": "too three"},
        {"start": 0.0, "end": 2.0, "text": "synthetic one"},
    ]
    run = load_run(hypothesis_json(tmp_path, {"segments": segments}))
    assert run.errors == []
    assert run.lectures[0].hypothesis_text == "synthetic one too three"
    (tmp_path / "ref" / "lecture-01.txt").write_text("synthetic one too three", "utf-8")
    run = load_run(tmp_path / "run.json")
    result = evaluate(
        [(x.lecture_id, x.reference_text, x.hypothesis_text) for x in run.lectures]
    )
    assert result.pooled.wer == 0.0


@pytest.mark.parametrize(
    "document",
    [
        {"segments": [{"start": "0", "text": "a"}]},
        {"segments": [{"start": True, "text": "a"}]},
        {"segments": [{"text": "a"}]},
        {"segments": [{"start": 0, "text": 5}]},
        {"segments": [{"start": float("nan"), "text": "a"}]},
        {"segments": [{"start": float("inf"), "text": "a"}]},
    ],
)
def test_segments_need_numeric_start_and_string_text(
    tmp_path: Path, document: object
) -> None:
    run = load_run(hypothesis_json(tmp_path, document))
    assert any("lecture-01 hypothesis" in e for e in run.errors), run.errors


@pytest.mark.parametrize(
    "document", [{"segments": []}, {"segments": [{"start": 0, "text": ""}]}]
)
def test_an_empty_hypothesis_is_all_deletions_with_a_warning(
    tmp_path: Path, document: object
) -> None:
    run = load_run(hypothesis_json(tmp_path, document))
    assert run.errors == []
    assert any("scored as all deletions" in w for w in run.warnings)
    result = evaluate(
        [(x.lecture_id, x.reference_text, x.hypothesis_text) for x in run.lectures]
    )
    assert result.pooled.deletions == 4 and result.pooled.wer == 1.0
    assert "## Warnings" in render_report(run, result)


def test_an_empty_reference_is_still_refused(tmp_path: Path) -> None:
    path = hypothesis_json(tmp_path, {"segments": []})
    (tmp_path / "ref" / "lecture-01.txt").write_text("  \n", "utf-8")
    assert any("reference: file is empty" in e for e in load_run(path).errors)


# --- CLI ------------------------------------------------------------------------------------


def test_cli_check_dry_run_and_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = make_run(tmp_path)
    assert main(["--manifest", str(path), "--check"]) == 0
    assert "OK: 1 lecture(s)" in capsys.readouterr().out

    out = tmp_path / "report.md"
    assert main(["--manifest", str(path), "--output", str(out), "--dry-run"]) == 0
    assert not out.exists()
    assert "SYNTHETIC SOFTWARE TEST" in capsys.readouterr().out

    assert main(["--manifest", str(path), "--output", str(out)]) == 0
    assert out.read_text("utf-8").startswith("# G-6 caption WER report")
    assert (
        main(["--manifest", str(path), "--output", str(out)]) == 1
    )  # never overwrites
    assert "already exists" in capsys.readouterr().err


def test_cli_refuses_invalid_input(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = make_run(tmp_path, mode="official")
    assert main(["--manifest", str(path)]) == 1
    assert "Inputs are not valid" in capsys.readouterr().err


def test_cli_prints_a_message_not_a_traceback_when_a_normaliser_empties_the_reference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setitem(NORMALISERS, "strip-all", lambda text: [])
    path = make_run(tmp_path, normaliser="strip-all")
    assert main(["--manifest", str(path), "--dry-run"]) == 1
    assert "Cannot compute" in capsys.readouterr().err


def test_cli_shows_the_empty_hypothesis_warning(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = hypothesis_json(tmp_path, {"segments": []})
    assert main(["--manifest", str(path), "--check"]) == 0
    assert "Warning:" in capsys.readouterr().err

"""Read and validate an evaluation run description and its transcript files.

The run description is a small JSON file local to this tool. It is NOT a contract (PRD B.0).

    {
      "format_version": 1,
      "mode": "synthetic-test" | "official",
      "normaliser": "unnormalised-whitespace",
      "lectures": [{"id": "lecture-01", "reference": "ref/lecture-01.txt",
                    "hypothesis": "hyp/lecture-01.txt"}],
      "run": {"engine": "...", "model": "...", "engine_version": "...", "hardware": "...",
              "decoding_settings": "...", "date": "YYYY-MM-DD", "operator": "..."},
      "approvals": {"normalisation_rules": "<reference>", "evaluation_method": "<reference>",
                    "speech_engine_confirmed": "<reference>", "audio_use_permitted": "<reference>"}
    }

`run` and `approvals` are required only for `official`. Paths are relative to the description
file, are never URLs or absolute, and never leave its folder. Only `.txt` (plain text) and `.json`
(B5.4 transcript: `segments[].text`) are read; media files are refused. Errors are collected, not
raised one at a time, and messages never contain transcript text.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from speech_eval.wer import NORMALISERS

MODES = ("synthetic-test", "official")
FORMAT_VERSION = 1
MAX_FILE_BYTES = 5_000_000
READABLE_SUFFIXES = (".txt", ".json")
LECTURE_ID = re.compile(r"^lecture-\d{2}$")
RUN_FIELDS = (
    "engine",
    "model",
    "engine_version",
    "hardware",
    "decoding_settings",
    "date",
    "operator",
)
APPROVAL_FIELDS = (
    "normalisation_rules",
    "evaluation_method",
    "speech_engine_confirmed",
    "audio_use_permitted",
)
# Normalisers the guide has approved for an official run. None yet: the rules are decided with the
# first baseline run (App-C 7). Adding a name here needs that decision, cited in the PR.
OFFICIAL_NORMALISERS: frozenset[str] = frozenset()
DATASET_README = Path("testdata") / "b8-5-lecture-videos" / "README.md"
_STATUS_LINE = re.compile(r"^\*\*Status:\s*([A-Z]+)\b", re.MULTILINE)


@dataclass(frozen=True)
class LectureInput:
    lecture_id: str
    reference_text: str
    hypothesis_text: str


@dataclass
class EvalRun:
    mode: str
    normaliser: str
    lectures: list[LectureInput] = field(default_factory=list)
    run: dict[str, str] = field(default_factory=dict)
    approvals: dict[str, str] = field(default_factory=dict)
    dataset_status: str | None = None
    errors: list[str] = field(default_factory=list)


def _is_pending(value: object) -> bool:
    return (
        not isinstance(value, str)
        or not value.strip()
        or value.strip().upper().startswith("PENDING")
    )


def dataset_status(repo_root: Path) -> str | None:
    """The `**Status: X**` line of the B8.5 set README, or None when it cannot be read."""
    try:
        text = (repo_root / DATASET_README).read_text("utf-8")
    except OSError:
        return None
    match = _STATUS_LINE.search(text)
    return match.group(1) if match else None


def _check_path(raw: object, what: str, errors: list[str]) -> str | None:
    if not isinstance(raw, str) or not raw:
        errors.append(f"{what}: path must be a non-empty string")
        return None
    if (
        re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", raw)
        or raw.startswith(("/", "\\"))
        or "\\" in raw
    ):
        errors.append(
            f"{what}: path must be relative, with forward slashes, and not a URL"
        )
        return None
    if ".." in Path(raw).parts:
        errors.append(f"{what}: path must not contain '..'")
        return None
    if not raw.lower().endswith(READABLE_SUFFIXES):
        errors.append(
            f"{what}: only {', '.join(READABLE_SUFFIXES)} files are read (no media or audio)"
        )
        return None
    return raw


def _read_text(base: Path, rel: str, what: str, errors: list[str]) -> str | None:
    path = (base / rel).resolve()
    if not path.is_relative_to(base.resolve()):
        errors.append(f"{what}: path leaves the description file's folder")
        return None
    if not path.is_file():
        errors.append(f"{what}: file not found")
        return None
    if path.stat().st_size > MAX_FILE_BYTES:
        errors.append(f"{what}: file is larger than {MAX_FILE_BYTES} bytes")
        return None
    try:
        raw = path.read_text("utf-8")
    except UnicodeDecodeError:
        errors.append(f"{what}: file is not UTF-8 text")
        return None
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(raw)
            text = " ".join(seg["text"] for seg in data["segments"])
        except (ValueError, KeyError, TypeError):
            errors.append(f"{what}: JSON must have segments[].text strings (PRD B5.4)")
            return None
    else:
        text = raw
    if any(line.lstrip().startswith("PENDING") for line in text.splitlines()):
        errors.append(
            f"{what}: still a PENDING placeholder; it must not be used for a measurement"
        )
        return None
    if not text.strip():
        errors.append(f"{what}: file is empty")
        return None
    return text


def _str_fields(
    data: object, names: tuple[str, ...], what: str, errors: list[str]
) -> dict[str, str]:
    out: dict[str, str] = {}
    if not isinstance(data, dict):
        errors.append(f"official run needs a '{what}' object")
        return out
    for name in names:
        value = data.get(name)
        if _is_pending(value):
            errors.append(f"official run: {what}.{name} is missing or PENDING")
        else:
            out[name] = str(value).strip()
    return out


def load_run(description: Path, repo_root: Path | None = None) -> EvalRun:
    """Load and validate; inspect `.errors` (empty means usable)."""
    errors: list[str] = []
    try:
        data: Any = json.loads(description.read_text("utf-8"))
    except (OSError, ValueError) as exc:
        return EvalRun(
            "", "", errors=[f"cannot read the run description: {type(exc).__name__}"]
        )
    if not isinstance(data, dict) or data.get("format_version") != FORMAT_VERSION:
        return EvalRun("", "", errors=[f"format_version must be {FORMAT_VERSION}"])

    mode, normaliser = data.get("mode"), data.get("normaliser")
    if mode not in MODES:
        errors.append(f"mode must be one of {MODES}")
    if normaliser not in NORMALISERS:
        errors.append(f"normaliser must be one of {sorted(NORMALISERS)}")
    result = EvalRun(str(mode), str(normaliser))

    lectures = data.get("lectures")
    if not isinstance(lectures, list) or not lectures:
        errors.append("lectures must be a non-empty list")
        lectures = []
    seen: set[str] = set()
    base = description.parent
    for index, entry in enumerate(lectures):
        entry = entry if isinstance(entry, dict) else {}
        lecture_id = entry.get("id")
        label = f"lectures[{index}]"
        if not isinstance(lecture_id, str) or not LECTURE_ID.match(lecture_id):
            errors.append(f"{label}: id must look like lecture-NN")
            continue
        if lecture_id in seen:
            errors.append(f"{label}: duplicate id {lecture_id}")
            continue
        seen.add(lecture_id)
        texts = []
        for key in ("reference", "hypothesis"):
            rel = _check_path(entry.get(key), f"{lecture_id} {key}", errors)
            texts.append(
                _read_text(base, rel, f"{lecture_id} {key}", errors) if rel else None
            )
        if texts[0] is not None and texts[1] is not None:
            result.lectures.append(LectureInput(lecture_id, texts[0], texts[1]))

    if mode == "official":
        result.run = _str_fields(data.get("run"), RUN_FIELDS, "run", errors)
        result.approvals = _str_fields(
            data.get("approvals"), APPROVAL_FIELDS, "approvals", errors
        )
        if normaliser not in OFFICIAL_NORMALISERS:
            errors.append(
                "official run: no normaliser is approved yet (rules are decided with the first "
                "baseline run, App-C 7)"
            )
        root = repo_root or Path(__file__).resolve().parents[2]
        result.dataset_status = dataset_status(root)
        if result.dataset_status != "COMPLETE":
            errors.append(
                f"official run: the B8.5 dataset status is {result.dataset_status or 'unreadable'}, "
                "not COMPLETE"
            )
    result.errors = errors
    return result

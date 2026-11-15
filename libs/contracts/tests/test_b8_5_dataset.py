"""B8.5 lecture video set (PRD B8): the inventory in testdata/README.md and its files.

The method is the guide's decision (docs/decisions/0004-b8-5-lecture-videos.md): at least 5 short
technical lectures in Indian English, approximately 30 minutes in total (acceptance threshold:
at least 1800 s), transcripts checked by Harshitha, and one consent line per speaker, written by
the speaker, with the exact sentence. A speaker who gives several lectures writes one line; each
lecture's Consent cell points to it (`0004` speaker-NN). The B8.5 table in testdata/README.md is
the only list of lectures; this file parses it directly.

A set is PENDING (placeholders allowed) or COMPLETE (every value real). Problems come in two
kinds: errors are wrong in any state; gaps are what is still missing. The Status line must be
true: COMPLETE with any gap fails, and so does PENDING with no gap.

CHECKED by this module's checker (the real set is tested here):
  * errors: the ten fixed columns; every row has exactly as many cells as the header (a `|`
    inside a value is reported, never silently shifted or cut); at least 5 rows with unique
    `lecture-NN` ids; every cell in its documented form (PENDING or: ASCII whole seconds, a bare
    file name, 64 lowercase hex SHA-256, the lecture's own outline/transcript path, `0004`
    speaker-NN, pending/checked); referenced files exist; a placeholder transcript is not
    `checked`; the decision record states the exact sentence and has a `## Consent lines`
    section whose lines are unique and well formed (PENDING or name, valid date, exact
    sentence); a referenced consent line exists and carries the lecture's Speaker name; one
    speaker has one consent line; the files Git tracks in the set folder are exactly the
    permitted paths (no recording, audio, draft, nested or unlisted file; ignored or untracked
    local files such as Thumbs.db do not count, and a failing `git ls-files` is an error);
  * gaps: any PENDING value; a transcript not checked; an outline or transcript that is empty or
    has a line starting with PENDING anywhere in it; a missing decision record; consent not
    given yet; a consent line no lecture uses; a total below 1800 s or a numeric Total line that
    is not the sum;
  * the status: both READMEs give the same status; COMPLETE needs no gap and a real Total line;
    PENDING needs a gap other than the Total line itself and keeps the Total line PENDING;
  * not yet in this file: tests that run the checker on broken, partly filled and complete
    synthetic sets, and on Git inspection itself. Until they are added, only the real set is tested.

NOT automated, and therefore NOT claimed:
  * that a recording exists, that its duration or SHA-256 is right, that the speech is Indian
    English, or that the speaker spoke from the outline (checked by people);
  * that recordings are kept as agreed (not synced or backed up to a cloud service, not shared),
    or that speakers were told about the interim storage;
  * that a transcript is accurate (Harshitha's check), or which model, if any, drafted it;
  * that the speaker personally wrote their consent line (shown by Git history and review).
"""

from __future__ import annotations

import datetime
import re
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TESTDATA_DIR = ROOT / "testdata"
SET_NAME = "b8-5-lecture-videos"
DECISION_RECORD = ROOT / "docs" / "decisions" / "0004-b8-5-lecture-videos.md"

COLUMNS = (
    "ID",
    "Title",
    "Speaker",
    "Duration (s)",
    "Recording file (lab only)",
    "SHA-256",
    "Outline",
    "Transcript",
    "Consent",
    "Transcript review",
)
FILLED_BY_HAND = COLUMNS[1:6]  # PENDING until the recording and the speaker are known
MIN_LECTURES = 5
MIN_TOTAL_S = 1800
PENDING = "PENDING"
CONSENT_SENTENCE = (
    "used to test speech recognition; video stays in the lab; "
    "transcript published under Apache-2.0"
)
TOP_LEVEL_FILES = ("README.md", ".gitignore")
LECTURE_FILES = ("outline.md", "transcript.en.txt")

LECTURE_ID_RE = re.compile(r"^lecture-\d{2}$")
# ASCII only: str.isdigit() also accepts "³" (which int() then rejects with a traceback) and
# "٣٦٠" or "３６０" (which int() silently reads as 360).
WHOLE_SECONDS_RE = re.compile(r"[0-9]+")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
STATUS_RE = re.compile(r"^- \*\*Status:\*\* (\w+)\.", re.MULTILINE)
SET_STATUS_RE = re.compile(r"^\*\*Status: (\w+)\.\*\*", re.MULTILINE)
TOTAL_RE = re.compile(r"^\*\*Total recorded duration:\*\* (.+)$", re.MULTILINE)
CONSENT_CELL_RE = re.compile(r"^0004 (speaker-\d{2})$")
CONSENT_LINE_RE = re.compile(r"^- (speaker-\d{2}): (.+)$", re.MULTILINE)
# The name ends at ", <YYYY-MM-DD>: \"", so a name may itself contain commas ("Rao, Asha").
CONSENT_GIVEN_RE = re.compile(
    r'^(?P<name>\S.*?), (?P<date>\d{4}-\d{2}-\d{2}): "(?P<sentence>[^"]*)"$'
)


@dataclass(frozen=True)
class Inventory:
    status: str
    header: tuple[str, ...]
    rows: tuple[
        dict[str, str], ...
    ]  # only rows with exactly one cell per header column
    total: str
    malformed: tuple[str, ...] = ()  # one message per row with a different cell count


@dataclass(frozen=True)
class DataSet:
    inventory: Inventory
    set_status: str  # the Status line of the set's own README
    testdata_dir: Path
    decision: str | None  # the decision record's text; None if it does not exist
    files: tuple[str, ...]  # the set folder's committed files, relative to it (POSIX)

    @property
    def set_dir(self) -> Path:
        return self.testdata_dir / SET_NAME


# --- parsing -------------------------------------------------------------------------------


def level2_section(text: str, heading: str) -> str | None:
    """From the `## <heading>` line up to the next level-2 heading."""
    match = re.search(rf"^## {heading}.*?(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return None if match is None else match.group(0)


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_inventory(readme_text: str) -> Inventory:
    section = level2_section(readme_text, r"B8\.5 ")
    assert section is not None, "testdata/README.md has no '## B8.5' section"
    status = STATUS_RE.search(section)
    total = TOTAL_RE.search(section)
    table = [line for line in section.splitlines() if line.startswith("| ")]
    assert (
        status and total and table
    ), "B8.5 needs a Status line, the table, a Total line"
    header = tuple(split_row(table[0]))
    rows: list[dict[str, str]] = []
    malformed: list[str] = []
    for number, line in enumerate(table[1:], start=1):
        cells = split_row(line)
        if len(cells) == len(header):
            rows.append(dict(zip(header, cells, strict=True)))
        else:
            # Kept out of `rows`: a shifted row would only produce misleading cell errors.
            malformed.append(
                f"table row {number} ({cells[0]!r}): {len(cells)} cells, the header has "
                f"{len(header)}; a value must not contain '|'"
            )
    return Inventory(
        status.group(1), header, tuple(rows), total.group(1).strip(), tuple(malformed)
    )


def consent_entries(decision: str) -> list[tuple[str, str]] | None:
    """(speaker id, rest of line) for each consent line; None without the section."""
    section = level2_section(decision, r"Consent lines\s*$")
    if section is None:
        return None
    return [(m.group(1), m.group(2).strip()) for m in CONSENT_LINE_RE.finditer(section)]


def unquote(cell: str) -> str:
    return cell.replace("`", "").strip()


def is_placeholder(path: Path) -> bool:
    """Empty, or any line starts with PENDING: a completed file has no PENDING line."""
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    return not any(lines) or any(line.startswith(PENDING) for line in lines)


def is_whole_seconds(text: str) -> bool:
    return WHOLE_SECONDS_RE.fullmatch(text) is not None


def is_iso_date(text: str) -> bool:
    try:
        datetime.date.fromisoformat(text)
    except ValueError:
        return False
    return True


def total_text(seconds: int) -> str:
    return f"{seconds} s ({seconds // 60} min {seconds % 60} s)"


# --- checks --------------------------------------------------------------------------------


class GitInspectionError(RuntimeError):
    """`git ls-files` could not list the set folder; never read as an empty, clean folder."""


def tracked_files(set_dir: Path) -> tuple[str, ...]:
    """The files Git tracks in the set folder, relative to it.

    Git's index, not the disk: ignored or untracked local files (Thumbs.db, desktop.ini, editor
    swap and backup files) are not part of the committed set and must not fail the check.
    """
    hint = "Run the tests with Git installed, inside a clone of the repository."
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--", "."],
            cwd=set_dir,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise GitInspectionError(f"cannot run git in {set_dir}: {exc}. {hint}") from exc
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise GitInspectionError(
            f"git ls-files failed in {set_dir} (exit {result.returncode}): {stderr}. {hint}"
        )
    # -z: paths are NUL-separated, unquoted, and relative to cwd (the set folder).
    return tuple(sorted(p for p in result.stdout.decode("utf-8").split("\0") if p))


def unexpected_files(files: Iterable[str], lecture_ids: list[str]) -> list[str]:
    """Every committed file that is not at one of the exact permitted paths."""
    permitted = set(TOP_LEVEL_FILES) | {
        f"lectures/{lid}/{name}" for lid in lecture_ids for name in LECTURE_FILES
    }
    return sorted(path for path in files if path not in permitted)


def check(ds: DataSet) -> tuple[list[str], list[str]]:
    """(errors, gaps) for a data set. Errors are wrong in any state; gaps block COMPLETE."""
    inv = ds.inventory
    if inv.header != COLUMNS:
        return [f"table columns are {list(inv.header)}, expected {list(COLUMNS)}"], []
    errors: list[str] = list(inv.malformed)
    gaps: list[str] = []
    ids = [row.get("ID", "") for row in inv.rows]
    if len(ids) < MIN_LECTURES:
        errors.append(f"{len(ids)} lectures listed, at least {MIN_LECTURES} needed")
    if len(set(ids)) != len(ids):
        errors.append(f"duplicate lecture ids: {ids}")
    consents = check_consent_record(ds.decision, errors, gaps)
    for row in inv.rows:
        check_row(ds, row, consents, errors, gaps)
    check_speakers(inv.rows, consents, errors, gaps)
    check_total(inv, gaps)
    errors += [
        f"not permitted in the set folder: {p}" for p in unexpected_files(ds.files, ids)
    ]
    return errors, gaps


def check_consent_record(
    decision: str | None, errors: list[str], gaps: list[str]
) -> dict[str, str | None]:
    """Speaker id -> name for given consent, None for PENDING."""
    if decision is None:
        gaps.append(
            "decision record docs/decisions/0004-b8-5-lecture-videos.md is missing"
        )
        return {}
    # The quoted statement line itself: the sentence inside consent lines does not count.
    if not re.search(rf"^> {re.escape(CONSENT_SENTENCE)}$", decision, re.MULTILINE):
        errors.append("decision record does not state the exact consent sentence")
    entries = consent_entries(decision)
    if entries is None:
        errors.append("decision record has no '## Consent lines' section")
        return {}
    consents: dict[str, str | None] = {}
    for sid, rest in entries:
        given = CONSENT_GIVEN_RE.match(rest)
        if sid in consents:
            errors.append(f"{sid}: more than one consent line")
        elif rest == PENDING:
            consents[sid] = None
        elif (
            given
            and given["sentence"] == CONSENT_SENTENCE
            and is_iso_date(given["date"])
        ):
            consents[sid] = given["name"].strip()
        else:
            errors.append(f'{sid}: must read <name>, <YYYY-MM-DD>: "<exact sentence>"')
    return consents


def check_row(
    ds: DataSet,
    row: dict[str, str],
    consents: dict[str, str | None],
    errors: list[str],
    gaps: list[str],
) -> None:
    lid = row["ID"]  # parse_inventory() keeps only rows with one cell per column
    if not LECTURE_ID_RE.match(lid):
        errors.append(f"row {lid!r}: needs an id like lecture-01")
        return
    pending = [column for column in FILLED_BY_HAND if row[column] == PENDING]
    if pending:
        gaps.append(f"{lid}: {', '.join(pending)} still {PENDING}")
    if not row["Title"] or not row["Speaker"]:
        errors.append(f"{lid}: Title and Speaker must not be empty (write {PENDING})")
    duration = row["Duration (s)"]
    if duration != PENDING and not (is_whole_seconds(duration) and int(duration) > 0):
        errors.append(f"{lid}: Duration (s) must be whole seconds: {duration!r}")
    if row["Recording file (lab only)"] != PENDING and re.search(
        r"[/\\:]", row["Recording file (lab only)"]
    ):
        errors.append(f"{lid}: Recording file must be a file name only, no path or URL")
    if row["SHA-256"] != PENDING and not SHA256_RE.match(row["SHA-256"]):
        errors.append(f"{lid}: SHA-256 must be 64 lowercase hex characters")
    for column, name in (
        ("Outline", "outline.md"),
        ("Transcript", "transcript.en.txt"),
    ):
        expected = f"{SET_NAME}/lectures/{lid}/{name}"
        path = ds.testdata_dir / expected
        if unquote(row[column]) != expected:
            errors.append(f"{lid}: {column} must be `{expected}`")
        elif not path.is_file():
            errors.append(f"{lid}: {expected} does not exist")
        elif is_placeholder(path):
            gaps.append(f"{lid}: {name} is still a placeholder")
            if name == "transcript.en.txt" and row["Transcript review"] == "checked":
                errors.append(f"{lid}: a placeholder transcript cannot be checked")
    review = row["Transcript review"]
    if review not in ("pending", "checked"):
        errors.append(
            f"{lid}: Transcript review must be pending or checked: {review!r}"
        )
    elif review == "pending":
        gaps.append(f"{lid}: transcript not checked by Harshitha yet")
    check_consent_cell(lid, row, consents, ds.decision is not None, errors, gaps)


def check_consent_cell(
    lid: str,
    row: dict[str, str],
    consents: dict[str, str | None],
    record_exists: bool,
    errors: list[str],
    gaps: list[str],
) -> None:
    cell = unquote(row["Consent"])
    match = CONSENT_CELL_RE.match(cell)
    if cell == PENDING:
        gaps.append(f"{lid}: no consent line referenced yet")
    elif match is None:
        errors.append(f"{lid}: Consent must be {PENDING} or `0004` speaker-NN")
    elif record_exists and match.group(1) not in consents:
        errors.append(f"{lid}: {match.group(1)} has no line under '## Consent lines'")
    elif consents.get(match.group(1)) is None:
        gaps.append(f"{lid}: {match.group(1)} has not given consent yet")
    elif row["Speaker"] not in (PENDING, consents[match.group(1)]):
        errors.append(f"{lid}: the consent name differs from the Speaker column")


def check_speakers(
    rows: tuple[dict[str, str], ...],
    consents: dict[str, str | None],
    errors: list[str],
    gaps: list[str],
) -> None:
    """One consent line per speaker, and every consent line is used by a lecture."""
    lines_by_speaker: dict[str, set[str]] = {}
    used: set[str] = set()
    for row in rows:
        match = CONSENT_CELL_RE.match(unquote(row.get("Consent", "")))
        if match is None:
            continue
        used.add(match.group(1))
        if row.get("Speaker", PENDING) != PENDING:
            lines_by_speaker.setdefault(row["Speaker"], set()).add(match.group(1))
    for speaker, sids in sorted(lines_by_speaker.items()):
        if len(sids) > 1:
            errors.append(
                f"{speaker}: one consent line per speaker, found {sorted(sids)}"
            )
    gaps += [
        f"{sid}: consent line not used by any lecture"
        for sid in sorted(set(consents) - used)
    ]


def check_total(inv: Inventory, gaps: list[str]) -> None:
    durations = [row.get("Duration (s)", PENDING) for row in inv.rows]
    if not all(is_whole_seconds(d) for d in durations):
        return  # PENDING or invalid durations are already reported
    total = sum(int(d) for d in durations)
    if total < MIN_TOTAL_S:
        gaps.append(f"total duration {total} s is below {MIN_TOTAL_S} s")
    # A PENDING Total line is a status marker, not missing evidence: counting it as a gap would
    # let a finished set keep saying PENDING. status_problems() judges it against the Status.
    if inv.total != PENDING and inv.total != total_text(total):
        gaps.append(f"Total line says {inv.total!r}, expected {total_text(total)!r}")


def status_problems(ds: DataSet, gaps: list[str]) -> list[str]:
    status = ds.inventory.status
    if status not in (PENDING, "COMPLETE"):
        return [f"Status must be PENDING or COMPLETE, not {status!r}"]
    if ds.set_status != status:
        return [
            f"the set README says {ds.set_status}, testdata/README.md says {status}"
        ]
    if status == "COMPLETE" and gaps:
        return ["Status is COMPLETE but the set is not:", *gaps]
    if status == "COMPLETE" and ds.inventory.total == PENDING:
        return [f"Status is COMPLETE but the Total line still says {PENDING}"]
    if status == PENDING and not gaps:
        return ["nothing is missing any more: change both Status lines to COMPLETE"]
    if status == PENDING and ds.inventory.total != PENDING:
        return [f"a PENDING set keeps the Total line as {PENDING}"]
    return []


def problems(ds: DataSet) -> list[str]:
    errors, gaps = check(ds)
    return errors + status_problems(ds, gaps)


# --- the real set --------------------------------------------------------------------------


def real_data_set() -> DataSet:
    set_readme = (TESTDATA_DIR / SET_NAME / "README.md").read_text(encoding="utf-8")
    set_status = SET_STATUS_RE.search(set_readme)
    assert (
        set_status is not None
    ), f"{SET_NAME}/README.md needs a '**Status: ...**' line"
    return DataSet(
        inventory=parse_inventory(
            (TESTDATA_DIR / "README.md").read_text(encoding="utf-8")
        ),
        set_status=set_status.group(1),
        testdata_dir=TESTDATA_DIR,
        decision=(
            DECISION_RECORD.read_text(encoding="utf-8")
            if DECISION_RECORD.is_file()
            else None
        ),
        files=tracked_files(TESTDATA_DIR / SET_NAME),
    )


def test_the_real_set_has_no_errors() -> None:
    errors, _ = check(real_data_set())
    assert errors == []


def test_the_real_status_is_true() -> None:
    ds = real_data_set()
    assert status_problems(ds, check(ds)[1]) == []

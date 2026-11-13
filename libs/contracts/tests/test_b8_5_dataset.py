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

AUTOMATED here:
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
  * all of the above on synthetic sets, built as README and decision-record text and parsed back.

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
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

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


# --- synthetic sets ------------------------------------------------------------------------

SHA = "a" * 64
GIVEN = f'2026-11-02: "{CONSENT_SENTENCE}"'
# Three speakers for five lectures: Speaker A and Speaker C each give two, with one line each.
SPEAKERS = (
    ("Speaker A", 1),
    ("Speaker A", 1),
    ("Speaker B", 2),
    ("Speaker C", 3),
    ("Speaker C", 3),
)


@dataclass(frozen=True)
class Draft:
    """A synthetic set, written out by build() as files plus README and decision-record text."""

    rows: tuple[dict[str, str], ...]
    consent_lines: tuple[str, ...]  # without the leading "- "
    status: str = "COMPLETE"
    set_status: str | None = None  # None: the same as status
    total: str | None = None  # None: the correct total of the rows
    header: tuple[str, ...] = COLUMNS
    placeholders: tuple[str, ...] = ()  # paths in the set folder written as PENDING
    texts: tuple[tuple[str, str], ...] = ()  # (path in the set folder, exact file text)
    missing: tuple[str, ...] = ()  # lecture files not written
    extra_files: tuple[str, ...] = ()  # other files written into the set folder
    record: bool = True
    statement: bool = True
    section: bool = True

    def cell(self, index: int, column: str, value: str) -> Draft:
        rows = [dict(row) for row in self.rows]
        rows[index][column] = value
        return replace(self, rows=tuple(rows))


def complete_draft() -> Draft:
    rows = tuple(
        {
            "ID": f"lecture-{n:02d}",
            "Title": f"Synthetic title {n}",
            "Speaker": name,
            "Duration (s)": "360",  # 5 x 360 s = 1800 s, exactly the minimum
            "Recording file (lab only)": f"lecture-{n:02d}.mp4",
            "SHA-256": SHA,
            "Outline": f"`{SET_NAME}/lectures/lecture-{n:02d}/outline.md`",
            "Transcript": f"`{SET_NAME}/lectures/lecture-{n:02d}/transcript.en.txt`",
            "Consent": f"`0004` speaker-{sid:02d}",
            "Transcript review": "checked",
        }
        for n, (name, sid) in enumerate(SPEAKERS, start=1)
    )
    lines = tuple(
        f"speaker-{sid:02d}: {name}, {GIVEN}" for name, sid in dict(SPEAKERS).items()
    )
    return Draft(rows=rows, consent_lines=lines)


def pending_draft() -> Draft:
    rows = tuple(
        {
            **row,
            **dict.fromkeys(FILLED_BY_HAND, PENDING),
            "Consent": PENDING,
            "Transcript review": "pending",
        }
        for row in complete_draft().rows
    )
    placeholders = tuple(
        f"lectures/{row['ID']}/{name}" for row in rows for name in LECTURE_FILES
    )
    return Draft(rows, (), PENDING, total=PENDING, placeholders=placeholders)


def render_readme(d: Draft) -> str:
    durations = [row.get("Duration (s)", "") for row in d.rows]
    computed = (
        total_text(sum(map(int, durations)))
        if all(map(is_whole_seconds, durations))
        else PENDING
    )
    total = (
        d.total or computed
    )  # a deliberately bad duration must not crash the builder
    lines = [
        "## B8.5 Lecture videos (synthetic)",
        "",
        f"- **Status:** {d.status}. Synthetic set.",
        "",
        f"| {' | '.join(d.header)} |",
        f"|{'---|' * len(d.header)}",
        # A row without a column's key gets no cell at all, so a short row can be written.
        *(f"| {' | '.join(row[c] for c in d.header if c in row)} |" for row in d.rows),
        "",
        f"**Total recorded duration:** {total}",
        "",
        "## Next section",
    ]
    return "\n".join(lines) + "\n"


def render_decision(d: Draft) -> str:
    statement = f"> {CONSENT_SENTENCE}\n\n" if d.statement else ""
    heading = "## Consent lines" if d.section else "## Consent"
    example = '`- speaker-NN: <name>, <YYYY-MM-DD>: "..."`'
    lines = "".join(f"- {line}\n" for line in d.consent_lines)
    return f"## Consent statement\n\n{statement}{heading}\n\n{example}\n\n{lines}"


def build(tmp_path: Path, d: Draft) -> DataSet:
    set_dir = tmp_path / SET_NAME
    texts = dict(d.texts)
    for row in d.rows:
        for name in LECTURE_FILES:
            relative = f"lectures/{row['ID']}/{name}"
            if relative in d.missing:
                continue
            text = texts.get(relative) or (
                "PENDING: placeholder\n"
                if relative in d.placeholders
                else "Synthetic.\n"
            )
            (set_dir / relative).parent.mkdir(parents=True, exist_ok=True)
            (set_dir / relative).write_text(text, encoding="utf-8")
    for relative in d.extra_files:
        (set_dir / relative).parent.mkdir(parents=True, exist_ok=True)
        (set_dir / relative).write_bytes(b"\x00")
    return DataSet(
        inventory=parse_inventory(render_readme(d)),
        set_status=d.set_status or d.status,
        testdata_dir=tmp_path,
        decision=render_decision(d) if d.record else None,
        # Not a Git repository: every file written here stands for a committed one.
        # tracked_files() itself is tested on a real repository further down.
        files=tuple(
            sorted(
                p.relative_to(set_dir).as_posix()
                for p in set_dir.rglob("*")
                if p.is_file()
            )
        ),
    )


def assert_reported(found: list[str], expected: str) -> None:
    """The exact message, so that an unrelated problem cannot keep a negative test passing."""
    assert expected in found, f"expected {expected!r} among {found}"


def test_a_complete_set_passes_and_parses_back(tmp_path: Path) -> None:
    draft = complete_draft()
    ds = build(tmp_path, draft)
    assert ds.inventory.rows == draft.rows
    assert len(draft.consent_lines) == 3  # three speakers, five lectures
    assert problems(ds) == []


def test_a_pending_set_has_no_errors_but_is_not_complete(tmp_path: Path) -> None:
    ds = build(tmp_path, pending_draft())
    errors, gaps = check(ds)
    assert errors == []
    assert gaps != []
    assert status_problems(ds, gaps) == []


def test_a_partly_filled_pending_set_has_no_errors(tmp_path: Path) -> None:
    draft = replace(pending_draft(), consent_lines=(f"speaker-01: Speaker A, {GIVEN}",))
    draft = draft.cell(0, "Speaker", "Speaker A").cell(
        0, "Consent", "`0004` speaker-01"
    )
    assert problems(build(tmp_path, draft.cell(0, "Duration (s)", "412"))) == []


STILL_PENDING = "nothing is missing any more: change both Status lines to COMPLETE"

# Each case: how to make the draft, and the exact message its check must produce.
STATUS_CASES: dict[str, tuple[Callable[[], Draft], str]] = {
    "pending-set-claims-complete": (
        lambda: replace(pending_draft(), status="COMPLETE"),
        "Status is COMPLETE but the set is not:",
    ),
    "complete-set-still-pending": (
        lambda: replace(complete_draft(), status=PENDING),
        STILL_PENDING,
    ),
    "complete-set-still-pending-with-pending-total": (
        lambda: replace(complete_draft(), status=PENDING, total=PENDING),
        STILL_PENDING,
    ),
    "complete-status-with-pending-total": (
        lambda: replace(complete_draft(), total=PENDING),
        f"Status is COMPLETE but the Total line still says {PENDING}",
    ),
    "pending-set-with-numeric-total": (
        lambda: replace(pending_draft(), total="1800 s (30 min 0 s)"),
        f"a PENDING set keeps the Total line as {PENDING}",
    ),
    "readmes-disagree": (
        lambda: replace(complete_draft(), set_status=PENDING),
        "the set README says PENDING, testdata/README.md says COMPLETE",
    ),
    "unknown-status": (
        lambda: replace(complete_draft(), status="DONE"),
        "Status must be PENDING or COMPLETE, not 'DONE'",
    ),
}


@pytest.mark.parametrize(
    ("make", "expected"), STATUS_CASES.values(), ids=STATUS_CASES.keys()
)
def test_a_false_status_fails(
    tmp_path: Path, make: Callable[[], Draft], expected: str
) -> None:
    assert_reported(problems(build(tmp_path, make())), expected)


def test_a_finished_set_cannot_hide_behind_a_pending_total(tmp_path: Path) -> None:
    """Regression: all evidence in, both Status lines and the Total line still PENDING."""
    ds = build(tmp_path, replace(complete_draft(), status=PENDING, total=PENDING))
    assert check(ds) == ([], [])
    assert problems(ds) == [STILL_PENDING]


def first_line(d: Draft, line: str) -> Draft:
    return replace(d, consent_lines=(line, *d.consent_lines[1:]))


def extra(*paths: str) -> tuple[Callable[[Draft], Draft], str]:
    return (
        lambda d: replace(d, extra_files=paths),
        f"not permitted in the set folder: {paths[0]}",
    )


def text_of(relative: str, text: str) -> Callable[[Draft], Draft]:
    return lambda d: replace(d, texts=((relative, text),))


def without(index: int, column: str) -> Callable[[Draft], Draft]:
    """Row `index` written with one cell fewer than the header."""

    def mutate(d: Draft) -> Draft:
        rows = [dict(row) for row in d.rows]
        del rows[index][column]
        return replace(d, rows=tuple(rows))

    return mutate


def whole_seconds(value: str) -> tuple[Callable[[Draft], Draft], str]:
    return (
        lambda d: d.cell(0, "Duration (s)", value),
        f"lecture-01: Duration (s) must be whole seconds: {value!r}",
    )


LATER_PENDING = "Real first line.\nPENDING: rest not typed yet\n"
MUST_READ = 'speaker-01: must read <name>, <YYYY-MM-DD>: "<exact sentence>"'
RECORDING_NAME_ONLY = (
    "lecture-01: Recording file must be a file name only, no path or URL"
)
SHA_FORM = "lecture-01: SHA-256 must be 64 lowercase hex characters"
IDS = [f"lecture-0{n}" for n in range(1, 6)]

# Each case: how to break a complete draft, and the exact message its check must produce.
BROKEN: dict[str, tuple[Callable[[Draft], Draft], str]] = {
    # count and duration
    "four-lectures": (
        lambda d: replace(
            d, rows=tuple({**r, "Duration (s)": "450"} for r in d.rows[:4])
        ),
        "4 lectures listed, at least 5 needed",
    ),
    "below-1800-s": (
        lambda d: d.cell(0, "Duration (s)", "359"),
        "total duration 1799 s is below 1800 s",
    ),
    "wrong-total-line": (
        lambda d: replace(d, total="1900 s (31 min 40 s)"),
        "Total line says '1900 s (31 min 40 s)', expected '1800 s (30 min 0 s)'",
    ),
    # inventory cells and structure
    "pending-cell": (
        lambda d: d.cell(2, "Title", PENDING),
        f"lecture-03: Title still {PENDING}",
    ),
    "duration-text": whole_seconds("6 min"),
    "duration-zero": whole_seconds("0"),
    "duration-negative": whole_seconds("-360"),
    "duration-plus-sign": whole_seconds("+360"),
    "duration-decimal": whole_seconds("360.5"),
    # Unicode digits: "³" used to crash int(); the other two were silently read as 360.
    "duration-superscript": whole_seconds("³"),
    "duration-superscript-in-number": whole_seconds("36⁰"),
    "duration-arabic-indic-digits": whole_seconds("٣٦٠"),
    "duration-fullwidth-digits": whole_seconds("３６０"),
    "recording-path": (
        lambda d: d.cell(0, "Recording file (lab only)", "share/l1.mp4"),
        RECORDING_NAME_ONLY,
    ),
    "recording-url": (
        lambda d: d.cell(
            0, "Recording file (lab only)", "https://example.invalid/l1.mp4"
        ),
        RECORDING_NAME_ONLY,
    ),
    "sha-short": (lambda d: d.cell(0, "SHA-256", "ABC"), SHA_FORM),
    "sha-uppercase": (lambda d: d.cell(0, "SHA-256", SHA.upper()), SHA_FORM),
    "wrong-outline-path": (
        lambda d: d.cell(0, "Outline", f"`{SET_NAME}/lectures/lecture-02/outline.md`"),
        f"lecture-01: Outline must be `{SET_NAME}/lectures/lecture-01/outline.md`",
    ),
    "review-pending": (
        lambda d: d.cell(0, "Transcript review", "pending"),
        "lecture-01: transcript not checked by Harshitha yet",
    ),
    "review-unknown": (
        lambda d: d.cell(0, "Transcript review", "approved"),
        "lecture-01: Transcript review must be pending or checked: 'approved'",
    ),
    "duplicate-ids": (
        lambda d: replace(d, rows=(*d.rows, d.rows[0])),
        f"duplicate lecture ids: {[*IDS, 'lecture-01']}",
    ),
    "wrong-columns": (
        lambda d: replace(d, header=COLUMNS[:-1]),
        f"table columns are {list(COLUMNS[:-1])}, expected {list(COLUMNS)}",
    ),
    # malformed rows: never shifted or cut silently
    "pipe-in-a-value": (
        lambda d: d.cell(0, "Title", "Pipes | in a title"),
        "table row 1 ('lecture-01'): 11 cells, the header has 10; "
        "a value must not contain '|'",
    ),
    # The old parser cut this row back to ten valid-looking cells and passed it.
    "extra-trailing-cell": (
        lambda d: d.cell(1, "Transcript review", "checked | surplus"),
        "table row 2 ('lecture-02'): 11 cells, the header has 10; "
        "a value must not contain '|'",
    ),
    "missing-cell": (
        without(2, "Transcript review"),
        "table row 3 ('lecture-03'): 9 cells, the header has 10; "
        "a value must not contain '|'",
    ),
    # transcript and outline files
    "placeholder-outline": (
        lambda d: replace(d, placeholders=("lectures/lecture-03/outline.md",)),
        "lecture-03: outline.md is still a placeholder",
    ),
    "placeholder-transcript": (
        lambda d: replace(d, placeholders=("lectures/lecture-03/transcript.en.txt",)),
        "lecture-03: transcript.en.txt is still a placeholder",
    ),
    "placeholder-transcript-checked": (
        lambda d: replace(d, placeholders=("lectures/lecture-03/transcript.en.txt",)),
        "lecture-03: a placeholder transcript cannot be checked",
    ),
    "outline-pending-on-a-later-line": (
        text_of("lectures/lecture-03/outline.md", LATER_PENDING),
        "lecture-03: outline.md is still a placeholder",
    ),
    "transcript-pending-on-a-later-line": (
        text_of("lectures/lecture-03/transcript.en.txt", LATER_PENDING),
        "lecture-03: transcript.en.txt is still a placeholder",
    ),
    "transcript-blank-lines-only": (
        text_of("lectures/lecture-03/transcript.en.txt", "\n  \n\n"),
        "lecture-03: transcript.en.txt is still a placeholder",
    ),
    "missing-outline": (
        lambda d: replace(d, missing=("lectures/lecture-02/outline.md",)),
        f"lecture-02: {SET_NAME}/lectures/lecture-02/outline.md does not exist",
    ),
    # consent record
    "no-decision-record": (
        lambda d: replace(d, record=False),
        "decision record docs/decisions/0004-b8-5-lecture-videos.md is missing",
    ),
    "no-consent-section": (
        lambda d: replace(d, section=False),
        "decision record has no '## Consent lines' section",
    ),
    "no-exact-statement": (
        lambda d: replace(d, statement=False),
        "decision record does not state the exact consent sentence",
    ),
    "consent-cell-format": (
        lambda d: d.cell(0, "Consent", "lecture-01"),
        f"lecture-01: Consent must be {PENDING} or `0004` speaker-NN",
    ),
    "consent-cell-unknown-speaker": (
        lambda d: d.cell(0, "Consent", "`0004` speaker-09"),
        "lecture-01: speaker-09 has no line under '## Consent lines'",
    ),
    "consent-not-given": (
        lambda d: first_line(d, "speaker-01: PENDING"),
        "lecture-01: speaker-01 has not given consent yet",
    ),
    "consent-sentence-changed": (
        lambda d: first_line(
            d, f'speaker-01: Speaker A, 2026-11-02: "{CONSENT_SENTENCE}."'
        ),
        MUST_READ,
    ),
    "consent-date-invalid": (
        lambda d: first_line(
            d, f'speaker-01: Speaker A, 2026-13-40: "{CONSENT_SENTENCE}"'
        ),
        MUST_READ,
    ),
    "consent-name-differs": (
        lambda d: first_line(d, f"speaker-01: Someone Else, {GIVEN}"),
        "lecture-01: the consent name differs from the Speaker column",
    ),
    "consent-line-twice": (
        lambda d: replace(d, consent_lines=(*d.consent_lines, d.consent_lines[0])),
        "speaker-01: more than one consent line",
    ),
    "one-speaker-two-lines": (
        lambda d: replace(
            d.cell(1, "Consent", "`0004` speaker-04"),
            consent_lines=(*d.consent_lines, f"speaker-04: Speaker A, {GIVEN}"),
        ),
        "Speaker A: one consent line per speaker, found ['speaker-01', 'speaker-04']",
    ),
    "unused-consent-line": (
        lambda d: replace(
            d, consent_lines=(*d.consent_lines, f"speaker-04: Speaker D, {GIVEN}")
        ),
        "speaker-04: consent line not used by any lecture",
    ),
    # files that must not be in the set folder
    "audio-wav": extra("lectures/lecture-01/lecture-01.wav"),
    "audio-mp3": extra("lectures/lecture-01/lecture-01.mp3"),
    "video-mp4": extra("lectures/lecture-01/lecture-01.mp4"),
    "draft-transcript": extra("lectures/lecture-01/draft.txt"),
    "nested-outline": extra("lectures/lecture-01/sub/outline.md"),
    "unlisted-lecture": extra("lectures/lecture-09/outline.md"),
    "top-level-note": extra("notes.md"),
}


@pytest.mark.parametrize(("mutate", "expected"), BROKEN.values(), ids=BROKEN.keys())
def test_a_broken_complete_set_fails(
    tmp_path: Path, mutate: Callable[[Draft], Draft], expected: str
) -> None:
    assert_reported(problems(build(tmp_path, mutate(complete_draft()))), expected)


def test_a_speaker_name_with_a_comma_is_accepted(tmp_path: Path) -> None:
    draft = first_line(complete_draft(), f"speaker-01: Rao, Asha, {GIVEN}")
    draft = draft.cell(0, "Speaker", "Rao, Asha").cell(1, "Speaker", "Rao, Asha")
    assert problems(build(tmp_path, draft)) == []
    mismatch = draft.cell(
        1, "Speaker", "Rao"
    )  # still compared in full, not cut at the comma
    assert_reported(
        problems(build(tmp_path / "mismatch", mismatch)),
        "lecture-02: the consent name differs from the Speaker column",
    )


def test_completed_text_without_a_pending_line_is_not_a_placeholder(
    tmp_path: Path,
) -> None:
    text = (
        "First point.\n\nThe request stays pending until it is reviewed.\nLast point.\n"
    )
    draft = replace(
        complete_draft(),
        texts=(
            ("lectures/lecture-01/outline.md", text),
            ("lectures/lecture-01/transcript.en.txt", text),
        ),
    )
    assert problems(build(tmp_path, draft)) == []


def test_consent_lines_outside_the_section_are_not_counted() -> None:
    decision = "## Decision\n\n- speaker-01: PENDING\n\n" + render_decision(
        complete_draft()
    )
    entries = consent_entries(decision)
    assert entries is not None
    assert [sid for sid, _ in entries] == ["speaker-01", "speaker-02", "speaker-03"]


def test_only_the_exact_permitted_paths_are_allowed(tmp_path: Path) -> None:
    ds = build(tmp_path, replace(complete_draft(), extra_files=TOP_LEVEL_FILES))
    assert unexpected_files(ds.files, [r["ID"] for r in ds.inventory.rows]) == []
    assert unexpected_files(ds.files, ["lecture-01"]) == [
        f"lectures/lecture-0{n}/{name}" for n in range(2, 6) for name in LECTURE_FILES
    ]


def run_git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def test_only_files_tracked_by_git_are_inspected(tmp_path: Path) -> None:
    run_git(tmp_path, "init", "-q")
    set_dir = tmp_path / SET_NAME
    committed = ("README.md", "lectures/lecture-01/outline.md", "notes.md")
    local_only = (
        "Thumbs.db",
        "desktop.ini",
        "lectures/lecture-01/.outline.md.swp",
        "lectures/lecture-01/outline.md~",
        "lectures/lecture-01/lecture-01.wav",
    )
    for relative in (*committed, *local_only):
        (set_dir / relative).parent.mkdir(parents=True, exist_ok=True)
        (set_dir / relative).write_text("x\n", encoding="utf-8")
    run_git(tmp_path, "add", "--", *(f"{SET_NAME}/{p}" for p in committed))

    files = tracked_files(set_dir)

    assert (
        files == committed
    )  # sorted, relative to the set folder, local files left out
    assert unexpected_files(files, ["lecture-01"]) == ["notes.md"]  # still caught


def test_a_failing_git_command_is_an_error_not_a_clean_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(
            ["git"], 128, b"", b"fatal: not a git repository"
        )

    monkeypatch.setattr(subprocess, "run", failing)
    with pytest.raises(GitInspectionError, match="git ls-files failed .*exit 128"):
        tracked_files(tmp_path)


def test_missing_git_is_an_error_not_a_clean_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def missing(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise FileNotFoundError("git")

    monkeypatch.setattr(subprocess, "run", missing)
    with pytest.raises(GitInspectionError, match="cannot run git"):
        tracked_files(tmp_path)

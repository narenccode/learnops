"""B8.4 synthetic submissions (PRD B8): the PROVISIONAL pilot set and its proposed format.

The set lives in testdata/b8-4-synthetic-submissions/. Its format (manifest, submission,
expected-outcome and reference-grade schemas) is a Release 0 proposal by Student 3 and is not yet
agreed (see that folder's README, "Open decisions").

AUTOMATED here:
  * the four schemas are valid Draft 2020-12 schemas; the manifest, every submission.yaml and
    every expected.yaml validate; any reference-grade file validates (none exists yet);
  * manifest ids are unique and match the submission folders one to one; rubric,
    near_duplicate_of and resubmission_of references resolve;
  * each rubric's course package and task body exist, the assignment idnumber is in the course
    package with that body, the body holds exactly one marking table (B1.3) whose points sum to
    the assignment's points and whose checks use only the six names of PRD C3.5;
  * each expected.yaml lists exactly the marking-table criteria and checks, in order, carries no
    score, and its expected check results agree with the files and hosting settings (rules in
    predict_check below; word counting and heading matching are PROVISIONAL rules);
  * a provisional set marks every rubric and submission provisional; ambiguous and edge-case
    tags agree with the expected outcomes;
  * synthetic-data guards: every URL is on a reserved .invalid host, no email address, no file
    over 64 KiB, learner references are placeholders (schema pattern);
  * the pilot covers all four intended levels.

NOT automated, and therefore NOT claimed:
  * PRD B8 size (at least 30 submissions) and reference grades from at least one mentor. The
    pilot has 6 and no reference grades (mentor not named, design Q13). These are release-gate
    checks to add when the set is complete;
  * that a submission extractor (Module 3) reads these files: the reader below is a stand-in, checked against the shared vectors;
  * the Moodle form of a submission as editor HTML (B1.5 rule 5 is unverified until the lab check);
  * machine-check behaviour on real infrastructure (lab git server and demo stubs, not ready);
  * the marking-table parse below is a stand-in for the shared parser planned in libs/contracts
    (design §4.3b); it is not that parser.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
SET_DIR = ROOT / "testdata" / "b8-4-synthetic-submissions"
SCHEMA_DIR = SET_DIR / "schemas"
SUBMISSIONS_DIR = SET_DIR / "submissions"
REFERENCE_GRADES_DIR = SET_DIR / "reference-grades"

SCHEMA_NAMES = ("manifest", "submission", "expected-outcome", "reference-grade")
CHECK_NAMES = {
    "repo_clone",
    "repo_file",
    "readme_sections",
    "command",
    "http_ok",
    "word_count",
}
LEVELS = {"strong", "partial", "weak", "incorrect"}
MAX_FILE_BYTES = 64 * 1024
TABLE_START = "<!-- marking-table v1 -->"
TABLE_END = "<!-- /marking-table -->"
NO_CHECK = "—"

Doc = dict[str, Any]


# --- helpers -------------------------------------------------------------------------------


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_schema(name: str) -> Doc:
    loaded: Doc = json.loads(
        (SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8")
    )
    return loaded


def errors(validator: Draft202012Validator, instance: Any) -> list[str]:
    return [
        f"{list(e.absolute_path)}: {e.message}" for e in validator.iter_errors(instance)
    ]


def parse_marking_table(body: str) -> list[tuple[str, int, list[str]]]:
    """(criterion, points, checks) rows of the single B1.3 table. Stand-in, see docstring."""
    assert body.count(TABLE_START) == 1, "expected exactly one marking table"
    assert body.count(TABLE_END) == 1, "expected exactly one marking-table end marker"
    inside = body.split(TABLE_START, 1)[1].split(TABLE_END, 1)[0]
    lines = [line.strip() for line in inside.strip().splitlines()]
    assert lines[0] == "| Criterion | Points | Full marks when | Check |", lines[0]
    rows = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        assert len(cells) == 4, line
        name, points, _full_marks_when, check_cell = cells
        checks = (
            [] if check_cell == NO_CHECK else [c.strip() for c in check_cell.split(";")]
        )
        rows.append((name, int(points), checks))
    return rows


SUBMISSION_VECTORS = ROOT / "contracts" / "test-vectors" / "submission.v1.json"
LABEL_LINE = re.compile(r"^ *(repository|demo|report):(.*)$", re.IGNORECASE)
FENCE_LINE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
ATX_LINE = re.compile(r"^ {0,3}(#{1,6})([ \t].*)?$")


def read_submission(onlinetext: str, files: dict[str, str]) -> dict[str, Doc]:
    """Stand-in reader for PRD B1.5 rules 1 to 7, plain online text only (rule 5, editor HTML, is
    unverified until the lab). It is NOT the submission extractor of Module 3: it exists so that
    expected.yaml can be derived from the files, and it is checked against every plain case of the
    shared vectors in contracts/test-vectors/submission.v1.json (see the tests below)."""
    lines = onlinetext.split("\n")
    found: dict[str, list[str]] = {"repository": [], "demo": []}
    report_at: int | None = None
    first = ""
    for index, line in enumerate(lines):
        match = LABEL_LINE.match(line)
        if match is None:
            continue
        label = match.group(1).lower()
        if label == "report":
            report_at, first = index, match.group(2)
            break
        found[label].append(match.group(2).strip())
    parts: dict[str, Doc] = {}
    for label, values in found.items():
        if not values:
            parts[label] = {"error": "field_missing"}
        elif len(values) > 1:
            parts[label] = {"error": "field_repeated"}
        else:
            parts[label] = {"value": values[0]}
    if report_at is not None:
        text = "\n".join([first.lstrip(" "), *lines[report_at + 1 :]]).strip()
        parts["report"] = {
            "value": text,
            "source": "onlinetext",
            "words": len(text.split()),
        }
        return parts
    for name in ("report.md", "report.txt"):
        if name in files:
            text = files[name]
            parts["report"] = {
                "value": text,
                "source": name,
                "words": len(text.split()),
            }
            return parts
    parts["report"] = {"error": "field_missing"}
    return parts


def readme_headings(text: str) -> set[str]:
    """Heading texts of a README by PRD B1.3 (the readme_cases of the shared vectors): ATX headings
    of 1 to 6 # with at most three leading spaces, a closing # sequence after a space or tab removed,
    surrounding spaces and tabs removed; headings inside a fenced block (``` or ~~~, at most three
    leading spaces, closed by the same character at least as long, or running to the end) and Setext
    headings do not count. Compared case-insensitively."""
    headings: set[str] = set()
    fence: str | None = None
    for line in text.split("\n"):
        opening = FENCE_LINE.match(line)
        if fence is not None:
            if (
                opening
                and opening.group(1)[0] == fence[0]
                and len(opening.group(1)) >= len(fence)
                and not opening.group(2).strip()
            ):
                fence = None
            continue
        if opening and not (opening.group(1)[0] == "`" and "`" in opening.group(2)):
            fence = opening.group(1)
            continue
        atx = ATX_LINE.match(line)
        if atx:
            body = (atx.group(2) or "").strip(" \t")
            body = re.sub(r"(?:^|[ \t]+)#+$", "", body).strip(" \t")
            headings.add(body.lower())
    return headings


def readme_sections_result(argument: str, readme: str) -> Doc:
    wanted = [name.strip() for name in argument.split(",")]
    have = readme_headings(readme)
    missing = [name for name in wanted if name.lower() not in have]
    return {"result": "fail", "missing": missing} if missing else {"result": "pass"}


def submission_files(folder: Path, submission: Doc) -> dict[str, str]:
    return {
        name: (folder / name).read_text(encoding="utf-8")
        for name in submission.get("files", [])
    }


def parts_of(folder: Path, submission: Doc) -> dict[str, Doc]:
    return read_submission(
        submission["onlinetext"], submission_files(folder, submission)
    )


def predict_check(check: str, folder: Path, submission: Doc) -> str:
    """Expected result of one check from the files and hosting settings (PROVISIONAL rules)."""
    name, _, arg = check.partition(":")
    hosting = submission["hosting"]
    repo = folder / submission["repo_dir"]
    parts = parts_of(folder, submission)
    if name == "http_ok":
        if "error" in parts["demo"]:
            return "error"  # B1.5 rule 7: the label is missing or repeated
        return "fail" if hosting["demo_stub"] == "none" else "pass"
    if name == "word_count":
        if "error" in parts["report"]:
            return "error"
        return "pass" if parts["report"]["words"] >= int(arg) else "fail"
    if "error" in parts["repository"]:
        return "error"  # the repository link cannot be read, so nothing needs the clone
    if not hosting["publish_repo"]:
        # Nothing to clone: the clone itself fails, anything that needs the clone cannot run.
        return "fail" if name == "repo_clone" else "error"
    if name == "repo_clone":
        return "pass"
    if name == "repo_file":
        return "pass" if (repo / arg).is_file() else "fail"
    if name == "readme_sections":
        readme = repo / "README.md"
        text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
        return str(readme_sections_result(arg, text)["result"])
    if name == "command":
        return "undetermined"  # no check config exists yet (design Q33)
    raise AssertionError(f"unknown check name {name!r}")


def find_keys(node: Any, keys: set[str]) -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key in keys:
                found.append(str(key))
            found.extend(find_keys(value, keys))
    elif isinstance(node, list):
        for item in node:
            found.extend(find_keys(item, keys))
    return found


def reference_grade_problems(
    grade: Doc, rubric_rows: list[tuple[str, int, list[str]]]
) -> list[str]:
    """Cross-field rules for a reference grade that JSON Schema cannot express."""
    problems = []
    names = [c["criterion"] for c in grade["criteria"]]
    if names != [row[0] for row in rubric_rows]:
        problems.append(f"criteria {names} do not match the marking table")
    for criterion, (_, points, _) in zip(grade["criteria"], rubric_rows, strict=False):
        if criterion["score"] > points:
            problems.append(f"{criterion['criterion']}: score above {points}")
    if grade["total"] != sum(c["score"] for c in grade["criteria"]):
        problems.append("total is not the sum of the criterion scores")
    return problems


# --- fixtures ------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def validators() -> dict[str, Draft202012Validator]:
    return {name: Draft202012Validator(load_schema(name)) for name in SCHEMA_NAMES}


@pytest.fixture(scope="module")
def manifest() -> Doc:
    loaded: Doc = load_yaml(SET_DIR / "manifest.yaml")
    return loaded


@pytest.fixture(scope="module")
def rubrics(manifest: Doc) -> dict[str, Doc]:
    return {r["id"]: r for r in manifest["rubrics"]}


@pytest.fixture(scope="module")
def tables(rubrics: dict[str, Doc]) -> dict[str, list[tuple[str, int, list[str]]]]:
    return {
        rid: parse_marking_table((ROOT / r["task_body"]).read_text(encoding="utf-8"))
        for rid, r in rubrics.items()
    }


def submission_ids() -> list[str]:
    return [s["id"] for s in load_yaml(SET_DIR / "manifest.yaml")["submissions"]]


# --- schemas and documents -----------------------------------------------------------------


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_schema_is_a_valid_draft_2020_12_schema(name: str) -> None:
    Draft202012Validator.check_schema(load_schema(name))


def test_manifest_is_valid(
    validators: dict[str, Draft202012Validator], manifest: Doc
) -> None:
    assert errors(validators["manifest"], manifest) == []


@pytest.mark.parametrize("sid", submission_ids())
def test_submission_and_expected_outcome_are_valid(
    sid: str, validators: dict[str, Draft202012Validator], manifest: Doc
) -> None:
    folder = SUBMISSIONS_DIR / sid
    submission = load_yaml(folder / "submission.yaml")
    expected = load_yaml(folder / "expected.yaml")
    assert errors(validators["submission"], submission) == []
    assert errors(validators["expected-outcome"], expected) == []
    entry = next(s for s in manifest["submissions"] if s["id"] == sid)
    assert submission["id"] == sid
    assert expected["submission_id"] == sid
    assert expected["rubric"] == entry["rubric"]
    for name in submission.get("files", []):
        assert (folder / name).is_file(), name
    # B1.5 rule 4: a report file is used only when the online text has no Report: section.
    has_report_section = (
        "error" not in parts_of(folder, {**submission, "files": []})["report"]
    )
    assert not (has_report_section and submission.get("files")), sid
    assert (folder / submission["repo_dir"]).is_dir()


def test_reference_grade_files_are_valid(
    validators: dict[str, Draft202012Validator],
    manifest: Doc,
    tables: dict[str, list[tuple[str, int, list[str]]]],
) -> None:
    by_id = {s["id"]: s for s in manifest["submissions"]}
    for path in sorted(REFERENCE_GRADES_DIR.rglob("*.yaml")):
        grade = load_yaml(path)
        assert errors(validators["reference-grade"], grade) == [], path
        assert grade["submission_id"] in by_id, path
        assert grade["rubric"] == by_id[grade["submission_id"]]["rubric"], path
        assert reference_grade_problems(grade, tables[grade["rubric"]]) == [], path


def test_reference_grade_rules_catch_bad_grades(
    validators: dict[str, Draft202012Validator],
    tables: dict[str, list[tuple[str, int, list[str]]]],
) -> None:
    # In-memory only: no reference grade is written to the repository until a mentor grades.
    rows = tables["b8-2-wk-02-task"]
    grade: Doc = {
        "schema": "learnops.testdata.b8-4.reference-grade/v1",
        "submission_id": "s001",
        "rubric": "b8-2-wk-02-task",
        "mentor_ref": "mentor-01",
        "graded_at": "2026-11-01",
        "blind_to_drafts": True,
        "criteria": [{"criterion": n, "score": p, "reason": "x"} for n, p, _ in rows],
        "total": sum(p for _, p, _ in rows),
    }
    assert errors(validators["reference-grade"], grade) == []
    assert reference_grade_problems(grade, rows) == []

    # Score above the criterion's points, total kept consistent: only the range rule fires.
    grade["criteria"][0]["score"] += 1
    grade["total"] += 1
    assert [p for p in reference_grade_problems(grade, rows) if "score above" in p]

    grade["total"] += 1
    assert "total is not the sum of the criterion scores" in reference_grade_problems(
        grade, rows
    )

    grade["criteria"] = grade["criteria"][1:]
    assert any("do not match" in p for p in reference_grade_problems(grade, rows))

    grade["mentor_ref"] = "Dr. Real Name"
    assert errors(validators["reference-grade"], grade) != []


# --- links between submissions, rubrics and expected outcomes ------------------------------


def test_ids_are_unique_and_match_folders(manifest: Doc) -> None:
    ids = [s["id"] for s in manifest["submissions"]]
    assert len(ids) == len(set(ids))
    rubric_ids = [r["id"] for r in manifest["rubrics"]]
    assert len(rubric_ids) == len(set(rubric_ids))
    folders = {p.name for p in SUBMISSIONS_DIR.iterdir() if p.is_dir()}
    assert folders == set(ids)


def test_references_resolve(manifest: Doc, rubrics: dict[str, Doc]) -> None:
    ids = {s["id"] for s in manifest["submissions"]}
    for s in manifest["submissions"]:
        assert s["rubric"] in rubrics, s["id"]
        for field in ("near_duplicate_of", "resubmission_of"):
            if field in s:
                assert s[field] in ids and s[field] != s["id"], (s["id"], field)


def test_rubric_sources_exist_and_match_the_course_package(
    rubrics: dict[str, Doc], tables: dict[str, list[tuple[str, int, list[str]]]]
) -> None:
    for rid, rubric in rubrics.items():
        package = ROOT / rubric["course_package"]
        course = load_yaml(package)
        activities = [a for sec in course["sections"] for a in sec["activities"]]
        matches = [
            a for a in activities if a["idnumber"] == rubric["assignment_idnumber"]
        ]
        assert len(matches) == 1, rid
        assignment = matches[0]
        assert assignment["type"] == "assignment", rid
        assert (package.parent / assignment["body"]).resolve() == (
            ROOT / rubric["task_body"]
        ).resolve()
        assert sum(points for _, points, _ in tables[rid]) == assignment["points"], rid
        for _, _, checks in tables[rid]:
            for check in checks:
                assert check.partition(":")[0] in CHECK_NAMES, (rid, check)


@pytest.mark.parametrize("sid", submission_ids())
def test_expected_outcome_follows_the_marking_table(
    sid: str, tables: dict[str, list[tuple[str, int, list[str]]]]
) -> None:
    expected = load_yaml(SUBMISSIONS_DIR / sid / "expected.yaml")
    rows = tables[expected["rubric"]]
    assert [c["criterion"] for c in expected["criteria"]] == [
        name for name, _, _ in rows
    ]
    for criterion, (_, _, checks) in zip(expected["criteria"], rows, strict=True):
        assert [c["check"] for c in criterion["checks"]] == checks, criterion[
            "criterion"
        ]
    assert find_keys(expected, {"score", "points", "total", "grade"}) == []


@pytest.mark.parametrize("sid", submission_ids())
def test_expected_check_results_agree_with_the_files(sid: str) -> None:
    folder = SUBMISSIONS_DIR / sid
    submission = load_yaml(folder / "submission.yaml")
    expected = load_yaml(folder / "expected.yaml")
    for criterion in expected["criteria"]:
        for check in criterion["checks"]:
            predicted = predict_check(check["check"], folder, submission)
            assert check["expected"] == predicted, (
                criterion["criterion"],
                check["check"],
            )


# --- provisional labelling and tags --------------------------------------------------------


def test_provisional_set_marks_everything_provisional(
    manifest: Doc, rubrics: dict[str, Doc]
) -> None:
    for rubric in rubrics.values():
        if rubric["task_body"].startswith("contracts/examples/"):
            # A contract example is never the B8.2 sample course.
            assert rubric["provisional"] is True, rubric["id"]
    if manifest["status"] == "provisional":
        assert all(r["provisional"] for r in rubrics.values())
        assert all(s["provisional"] for s in manifest["submissions"])
        for s in manifest["submissions"]:
            assert (
                load_yaml(SUBMISSIONS_DIR / s["id"] / "expected.yaml")["provisional"]
                is True
            )


def test_tags_agree_with_expected_outcomes(manifest: Doc) -> None:
    for s in manifest["submissions"]:
        expected = load_yaml(SUBMISSIONS_DIR / s["id"] / "expected.yaml")
        judgements = {c["judgement"] for c in expected["criteria"]}
        results = {
            c["expected"] for crit in expected["criteria"] for c in crit["checks"]
        }
        tags = set(s["edge_cases"])
        assert s["ambiguous"] == ("ambiguous" in judgements), s["id"]
        assert ("ambiguous_judgement" in tags) == s["ambiguous"], s["id"]
        assert ("near_duplicate" in tags) == ("near_duplicate_of" in s), s["id"]
        assert ("command_check_undetermined" in tags) == ("undetermined" in results), s[
            "id"
        ]


@pytest.mark.parametrize("sid", submission_ids())
def test_every_edge_case_tag_agrees_with_the_files(sid: str, manifest: Doc) -> None:
    """The tags that the files and hosting settings can decide (review of #31). `off_topic` and the
    reading behind `check_passes_but_criterion_unmet` are the author's judgement, so they are not
    derived here; the second one is only checked to be possible (see below)."""
    folder = SUBMISSIONS_DIR / sid
    entry = next(s for s in manifest["submissions"] if s["id"] == sid)
    submission = load_yaml(folder / "submission.yaml")
    expected = load_yaml(folder / "expected.yaml")
    tags = set(entry["edge_cases"])
    hosting = submission["hosting"]
    repo = folder / submission["repo_dir"]
    checks = [
        (crit["criterion"], c["check"], c["expected"])
        for crit in expected["criteria"]
        for c in crit["checks"]
    ]

    def failed(name: str) -> bool:
        return any(c.split(":")[0] == name and e == "fail" for _, c, e in checks)

    readme_exists = (repo / "README.md").is_file()
    if hosting["publish_repo"]:
        assert ("readme_missing" in tags) == (not readme_exists), sid
    assert ("readme_section_missing" in tags) == (
        hosting["publish_repo"] and readme_exists and failed("readme_sections")
    ), sid
    assert ("demo_unreachable" in tags) == (hosting["demo_stub"] == "none"), sid
    assert ("report_under_word_count" in tags) == failed("word_count"), sid
    assert ("repo_not_cloneable" in tags) == (not hosting["publish_repo"]), sid
    parts = parts_of(folder, submission)
    missing = {
        k for k in ("repository", "demo") if parts[k].get("error") == "field_missing"
    }
    report_lines = parts["report"].get("value", "").split("\n")[1:]
    inside = {
        m.group(1).lower()
        for m in map(LABEL_LINE.match, report_lines)
        if m and m.group(1).lower() in missing
    }
    assert ("label_repeated" in tags) == any(
        parts[k].get("error") == "field_repeated" for k in ("repository", "demo")
    ), sid
    assert ("label_inside_report" in tags) == bool(inside), sid
    assert ("label_missing" in tags) == bool(missing - inside), sid
    if "check_passes_but_criterion_unmet" in tags:
        # At least one criterion has checks that all pass while the author judged it not met.
        assert any(
            crit["checks"]
            and all(c["expected"] == "pass" for c in crit["checks"])
            and crit["judgement"] in {"partly_meets", "does_not_meet"}
            for crit in expected["criteria"]
        ), sid


SCORE_FIELDS = ("score", "points", "total", "grade")


def expected_outcome_with(level: str, field: str) -> Doc:
    """A valid expected outcome (s001) with one score field added at one level."""
    doc: Doc = load_yaml(SUBMISSIONS_DIR / "s001" / "expected.yaml")
    if level == "document":
        doc[field] = 1
    elif level == "criterion":
        doc["criteria"][0][field] = 1
    else:
        doc["criteria"][0]["checks"][0][field] = 1
    return doc


@pytest.mark.parametrize("field", SCORE_FIELDS)
@pytest.mark.parametrize("level", ["document", "criterion", "check"])
def test_a_score_field_is_rejected_at_every_level(
    validators: dict[str, Draft202012Validator], level: str, field: str
) -> None:
    doc = expected_outcome_with(level, field)
    assert errors(validators["expected-outcome"], doc) != [], (level, field)


@pytest.mark.parametrize("value", [None, 0, "10", {"x": 1}])
def test_a_score_field_is_rejected_whatever_its_value(
    validators: dict[str, Draft202012Validator], value: Any
) -> None:
    doc = expected_outcome_with("criterion", "points")
    doc["criteria"][0]["points"] = value
    assert errors(validators["expected-outcome"], doc) != []


def test_a_valid_expected_outcome_is_still_accepted(
    validators: dict[str, Draft202012Validator],
) -> None:
    doc: Doc = load_yaml(SUBMISSIONS_DIR / "s001" / "expected.yaml")
    assert errors(validators["expected-outcome"], doc) == []


def _vectors() -> Doc:
    loaded: Doc = json.loads(SUBMISSION_VECTORS.read_text(encoding="utf-8"))
    return loaded


PLAIN_CASES = [
    c for c in _vectors()["cases"] if c["input"]["onlinetext_format"] == "plain"
]
README_CASES = [
    c for c in _vectors()["readme_cases"] if c["expected"]["result"] != "invalid"
]


@pytest.mark.parametrize("case", PLAIN_CASES, ids=[c["id"] for c in PLAIN_CASES])
def test_the_stand_in_reader_gives_the_expected_parts_of_every_plain_vector(
    case: Doc,
) -> None:
    """The reader below the pilot is only trusted as far as it agrees with the shared vectors."""
    files = {f["name"]: f["text"] for f in case["input"]["files"]}
    parts = read_submission(case["input"]["onlinetext"], files)
    assert parts == case["expected"], case["id"]


@pytest.mark.parametrize("case", README_CASES, ids=[c["id"] for c in README_CASES])
def test_the_stand_in_heading_rule_gives_the_expected_result_of_every_readme_vector(
    case: Doc,
) -> None:
    check = case["check"]
    assert check.startswith("readme_sections:")
    readme = next(f["text"] for f in case["files"] if f["name"] == "README.md")
    # Only a README.md at the repository root is read (B1.3); the vector says what is there.
    assert readme_sections_result(check.partition(":")[2], readme) == case["expected"]


def test_the_pilot_exercises_the_b15_forms_and_failures(manifest: Doc) -> None:
    sources: set[str] = set()
    errors_seen: set[str] = set()
    for s in manifest["submissions"]:
        folder = SUBMISSIONS_DIR / s["id"]
        parts = parts_of(folder, load_yaml(folder / "submission.yaml"))
        sources.add(parts["report"]["source"])
        errors_seen |= {p["error"] for p in parts.values() if "error" in p}
    assert sources == {"onlinetext", "report.md"}  # a Report: section and a report file
    assert errors_seen == {"field_missing", "field_repeated"}


def test_pilot_covers_every_intended_level(manifest: Doc) -> None:
    assert {s["intended_level"] for s in manifest["submissions"]} == LEVELS


# --- synthetic-data guards -----------------------------------------------------------------

URL = re.compile(r"\bhttps?://([^/\s\"'`)>\]]+)")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9.-]+")


def set_files() -> list[Path]:
    return sorted(p for p in SET_DIR.rglob("*") if p.is_file())


def test_files_are_small_text() -> None:
    for path in set_files():
        assert path.stat().st_size <= MAX_FILE_BYTES, path
        path.read_text(encoding="utf-8")  # raises on binary content


def test_no_real_hosts_or_email_addresses() -> None:
    for path in set_files():
        if path.parent == SCHEMA_DIR:
            continue  # "$schema" URLs name the JSON Schema dialect, not data
        text = path.read_text(encoding="utf-8")
        for host in URL.findall(text):
            assert host.endswith(".invalid"), (path, host)
        assert EMAIL.findall(text) == [], path

"""Integration tests for the PROPOSED shared.course_link table (docs/design/shared-course-link.md).

What these tests do: run the SQL of the design document's `sql up` and `sql down` blocks on a real
PostgreSQL 16 server and check that the table behaves as the document's sections 3 to 5 state. The
SQL is read from the document, so the document and the tests cannot drift apart.

What they do NOT show: that a launch writes a row (no gateway exists), that Moodle returns the data
the design expects, or anything about Moodle 4.5 or 5.3. The design is a proposal; its open questions
(Q-A to Q-I) are not decided by these tests.

Server: a throwaway container from the official `postgres:16` image, started with the Docker CLI and
reached with `docker exec ... psql`, so no Python database driver is needed. The container publishes
no port and uses trust authentication inside it; it holds test data only and is removed afterwards.
When the Docker CLI or daemon is not usable, the database tests skip and say why; the tests that
only read the design document still run.
"""

from __future__ import annotations

import re
import secrets
import shutil
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DESIGN_DOC = ROOT / "docs" / "design" / "shared-course-link.md"
INTEGRATION_DOC = ROOT / "docs" / "design" / "b3-module-integration.md"
IMAGE = "postgres:16"

# The B3 contract section 3.1 values for context.id.
VALID_CONTEXT_IDS = ["1", "42", "1000000", "9" * 40]
INVALID_CONTEXT_IDS = [
    ("empty", ""),
    ("zero", "0"),
    ("negative", "-5"),
    ("plus-sign", "+5"),
    ("non-numeric", "abc"),
    ("decimal", "4.2"),
    ("exponent", "1e3"),
    ("leading-zero", "007"),
    ("leading-space", " 42"),
    ("trailing-space", "42 "),
    ("internal-space", "4 2"),
    ("trailing-newline", "42" + chr(10)),
    ("leading-newline", chr(10) + "42"),
    ("internal-newline", "4" + chr(10) + "2"),
    ("arabic-indic-digits", chr(0x664) + chr(0x662)),
    ("fullwidth-digits", chr(0xFF14) + chr(0xFF12)),
]


def _design_text() -> str:
    return DESIGN_DOC.read_text(encoding="utf-8")


def _flat(text: str) -> str:
    return " ".join(text.split())


def _sql_block(label: str) -> str:
    """The body of the fenced block that starts with ```sql <label> in the design document."""
    match = re.search(rf"```sql {label}\n(.*?)\n```", _design_text(), flags=re.DOTALL)
    assert match is not None, f"the design document has no 'sql {label}' block"
    return match.group(1)


def _quote(value: str) -> str:
    """A SQL string literal. Test values only; PostgreSQL standard strings, so no backslash rule."""
    return "'" + value.replace("'", "''") + "'"


@dataclass(frozen=True)
class Result:
    ok: bool
    output: str
    error: str
    sqlstate: str | None


class Postgres:
    """A running container and a way to send SQL to it with psql."""

    def __init__(self, container: str) -> None:
        self.container = container

    def run(self, sql: str) -> Result:
        script = "\\set VERBOSITY verbose\n" + sql + "\n"
        done = subprocess.run(
            [
                "docker", "exec", "-i", self.container,
                "psql", "-X", "-q", "-U", "postgres", "-d", "postgres",
                "-v", "ON_ERROR_STOP=1", "-At", "-f", "-",
            ],
            input=script,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            check=False,
        )  # fmt: skip
        found = re.search(r"ERROR:\s+([0-9A-Z]{5}):", done.stderr)
        return Result(
            ok=done.returncode == 0,
            output=done.stdout.strip(),
            error=done.stderr.strip(),
            sqlstate=found.group(1) if found else None,
        )


def _docker_unusable_reason() -> str | None:
    if shutil.which("docker") is None:
        return "the docker command is not installed"
    probe = subprocess.run(
        ["docker", "info", "--format", "{{.ServerVersion}}"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if probe.returncode != 0:
        return "the Docker daemon is not running or not reachable"
    return None


@pytest.fixture(scope="session")
def server() -> Iterator[Postgres]:
    reason = _docker_unusable_reason()
    if reason is not None:
        pytest.skip(f"no PostgreSQL for the course-link tests: {reason}")
    name = "learnops-test-pg-" + secrets.token_hex(4)
    started = subprocess.run(
        [
            "docker", "run", "-d", "--rm", "--name", name,
            "-e", "POSTGRES_HOST_AUTH_METHOD=trust",
            IMAGE,
        ],
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )  # fmt: skip
    if started.returncode != 0:
        pytest.skip(f"could not start {IMAGE}: {started.stderr.strip()[:200]}")
    try:
        postgres = Postgres(name)
        for _ in range(60):  # the image restarts the server once while it initialises
            probe = postgres.run("SELECT 1;")
            if probe.ok and probe.output == "1":
                break
            subprocess.run(
                ["docker", "exec", name, "sleep", "1"], check=False, capture_output=True
            )
        else:
            pytest.skip("the PostgreSQL container did not become ready in time")
        version = postgres.run("SHOW server_version_num;")
        assert version.ok and version.output.startswith("16"), version.output
        yield postgres
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, check=False)


@pytest.fixture
def pg(server: Postgres) -> Postgres:
    """The server with an empty `shared` schema (the migration assumes the schema exists)."""
    reset = server.run("DROP SCHEMA IF EXISTS shared CASCADE; CREATE SCHEMA shared;")
    assert reset.ok, reset.error
    return server


@pytest.fixture
def migrated(pg: Postgres) -> Postgres:
    applied = pg.run(_sql_block("up"))
    assert applied.ok, applied.error
    return pg


def _insert(
    iss: str = "https://moodle.example.org",
    context_id: str = "42",
    site_id: str = "moodle53",
    moodle_course_id: str = "42",
    shortname: str = "DEMO-101",
) -> str:
    return (
        "INSERT INTO shared.course_link "
        "(iss, context_id, site_id, moodle_course_id, course_shortname) VALUES "
        f"({_quote(iss)}, {_quote(context_id)}, {_quote(site_id)}, {moodle_course_id}, "
        f"{_quote(shortname)});"
    )


UNIQUE_VIOLATION = "23505"
CHECK_VIOLATION = "23514"
NOT_NULL_VIOLATION = "23502"
FOREIGN_KEY_VIOLATION = "23503"


# Migration (PRD OPS-07: versioned and reversible; Grading design 5.3: down drops only what up made)


def test_up_creates_the_table_in_the_shared_schema(migrated: Postgres) -> None:
    found = migrated.run(
        "SELECT table_schema || '.' || table_name FROM information_schema.tables "
        "WHERE table_name = 'course_link';"
    )
    assert found.output == "shared.course_link"


def test_down_removes_only_the_course_link_table(migrated: Postgres) -> None:
    assert migrated.run("CREATE TABLE shared.audit_log (id int);").ok
    assert migrated.run(_sql_block("down")).ok
    left = migrated.run(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'shared' "
        "ORDER BY 1;"
    )
    assert left.output == "audit_log"


def test_up_down_up_round_trip_works(pg: Postgres) -> None:
    for step in ("up", "down", "up"):
        applied = pg.run(_sql_block(step))
        assert applied.ok, (step, applied.error)
    assert pg.run(_insert()).ok


def test_up_twice_is_refused_not_silently_repeated(migrated: Postgres) -> None:
    again = migrated.run(_sql_block("up"))
    assert not again.ok and again.sqlstate == "42P07"  # duplicate_table


# Identity (PRD B3: keyed by iss plus context id; contract 7.1: iss compared as received)


def test_same_issuer_and_context_id_twice_is_refused(migrated: Postgres) -> None:
    assert migrated.run(_insert()).ok
    second = migrated.run(_insert(shortname="OTHER"))
    assert not second.ok and second.sqlstate == UNIQUE_VIOLATION
    assert "course_link_identity" in second.error


def test_same_context_id_from_two_issuers_is_two_rows(migrated: Postgres) -> None:
    """Moodle course ids repeat across sites (ADR 0001 OI-21), so the issuer separates them."""
    assert migrated.run(_insert(iss="https://moodle-a.example.org")).ok
    assert migrated.run(_insert(iss="https://moodle-b.example.org")).ok
    assert migrated.run("SELECT count(*) FROM shared.course_link;").output == "2"


def test_same_issuer_with_two_context_ids_is_two_rows(migrated: Postgres) -> None:
    assert migrated.run(_insert(context_id="42", moodle_course_id="42")).ok
    assert migrated.run(_insert(context_id="43", moodle_course_id="43")).ok


@pytest.mark.parametrize(
    "other_iss",
    ["https://moodle.example.org/", "HTTPS://MOODLE.EXAMPLE.ORG"],
    ids=["trailing-slash", "upper-case"],
)
def test_issuers_that_differ_only_in_form_are_different_identities(
    migrated: Postgres, other_iss: str
) -> None:
    """Contract 7.1: no trimming, case folding or trailing-slash normalisation. Whether such an
    issuer is registered is the gateway's check, not the table's."""
    assert migrated.run(_insert(iss="https://moodle.example.org")).ok
    assert migrated.run(_insert(iss=other_iss)).ok


def test_empty_issuer_is_refused(migrated: Postgres) -> None:
    result = migrated.run(_insert(iss=""))
    assert not result.ok and result.sqlstate == CHECK_VIOLATION
    assert "course_link_iss_not_empty" in result.error


# context_id: the B3 contract 3.1 rule


@pytest.mark.parametrize("context_id", VALID_CONTEXT_IDS)
def test_context_ids_the_contract_accepts_are_accepted(
    migrated: Postgres, context_id: str
) -> None:
    result = migrated.run(_insert(context_id=context_id))
    assert result.ok, result.error


@pytest.mark.parametrize(
    "context_id",
    [value for _, value in INVALID_CONTEXT_IDS],
    ids=[i for i, _ in INVALID_CONTEXT_IDS],
)
def test_context_ids_the_contract_refuses_are_refused(
    migrated: Postgres, context_id: str
) -> None:
    result = migrated.run(_insert(context_id=context_id))
    assert not result.ok and result.sqlstate == CHECK_VIOLATION, result.error
    assert "course_link_context_id_format" in result.error


# The other columns


@pytest.mark.parametrize("site_id", ["moodle45", "moodle53"])
def test_the_two_lab_sites_are_accepted(migrated: Postgres, site_id: str) -> None:
    assert migrated.run(_insert(site_id=site_id)).ok


@pytest.mark.parametrize(
    "site_id", ["moodle44", "moodle54", "Moodle45", "", "moodle45 "]
)
def test_any_other_site_id_is_refused(migrated: Postgres, site_id: str) -> None:
    result = migrated.run(_insert(site_id=site_id))
    assert not result.ok and result.sqlstate == CHECK_VIOLATION
    assert "course_link_site_id_known" in result.error


@pytest.mark.parametrize("course_id", ["0", "-1"])
def test_a_course_id_of_zero_or_below_is_refused(
    migrated: Postgres, course_id: str
) -> None:
    result = migrated.run(_insert(moodle_course_id=course_id))
    assert not result.ok and result.sqlstate == CHECK_VIOLATION
    assert "course_link_moodle_course_id_positive" in result.error


def test_an_empty_shortname_is_refused(migrated: Postgres) -> None:
    result = migrated.run(_insert(shortname=""))
    assert not result.ok and result.sqlstate == CHECK_VIOLATION
    assert "course_link_shortname_not_empty" in result.error


@pytest.mark.parametrize(
    "column", ["iss", "context_id", "site_id", "moodle_course_id", "course_shortname"]
)
def test_no_identifying_column_is_nullable(migrated: Postgres, column: str) -> None:
    columns = {
        "iss": "'i'",
        "context_id": "'1'",
        "site_id": "'moodle53'",
        "moodle_course_id": "1",
        "course_shortname": "'s'",
    }
    names = list(columns)
    values = [("NULL" if name == column else columns[name]) for name in names]
    result = migrated.run(
        f"INSERT INTO shared.course_link ({', '.join(names)}) VALUES ({', '.join(values)});"
    )
    assert not result.ok and result.sqlstate == NOT_NULL_VIOLATION


def test_id_and_timestamps_are_filled_in(migrated: Postgres) -> None:
    assert migrated.run(_insert()).ok
    row = migrated.run(
        "SELECT id IS NOT NULL, created_at IS NOT NULL, last_confirmed_at IS NOT NULL, "
        "created_at = last_confirmed_at FROM shared.course_link;"
    )
    assert row.output == "t|t|t|t"


def test_each_row_gets_its_own_id(migrated: Postgres) -> None:
    assert migrated.run(_insert(context_id="1", moodle_course_id="1")).ok
    assert migrated.run(_insert(context_id="2", moodle_course_id="2")).ok
    assert (
        migrated.run("SELECT count(DISTINCT id) FROM shared.course_link;").output == "2"
    )


def test_the_site_and_course_index_exists_for_grading_lookups(
    migrated: Postgres,
) -> None:
    found = migrated.run(
        "SELECT indexdef FROM pg_indexes WHERE schemaname = 'shared' "
        "AND indexname = 'course_link_site_course';"
    )
    assert "(site_id, moodle_course_id)" in found.output
    assert (
        "UNIQUE" not in found.output
    )  # Q-G is open: the pair is not unique in the proposal


# The first-launch upsert (design 5.5): id and created_at stay, last_confirmed_at moves


def test_a_repeated_launch_keeps_the_id_and_refreshes_the_confirmation(
    migrated: Postgres,
) -> None:
    assert migrated.run(_insert(shortname="OLD-NAME")).ok
    before = migrated.run("SELECT id, created_at FROM shared.course_link;").output
    again = migrated.run(
        "SELECT pg_sleep(0.05); "
        "INSERT INTO shared.course_link "
        "(iss, context_id, site_id, moodle_course_id, course_shortname) VALUES "
        "('https://moodle.example.org', '42', 'moodle53', 42, 'NEW-NAME') "
        "ON CONFLICT (iss, context_id) DO UPDATE SET "
        "course_shortname = EXCLUDED.course_shortname, last_confirmed_at = now();"
    )
    assert again.ok, again.error
    after = migrated.run("SELECT id, created_at FROM shared.course_link;").output
    assert after == before
    row = migrated.run(
        "SELECT course_shortname, last_confirmed_at > created_at, count(*) OVER () "
        "FROM shared.course_link;"
    )
    assert row.output == "NEW-NAME|t|1"


# Consumer contract (design 5.2 and 5.3): modules refer to the row by id


def test_a_module_table_can_refer_to_a_link_but_not_to_an_unknown_one(
    migrated: Postgres,
) -> None:
    """A throwaway table shaped like studio.package (docs/design/studio.md section 5); it is not
    the real module table."""
    assert migrated.run(_insert()).ok
    assert migrated.run(
        "CREATE SCHEMA studio_probe; CREATE TABLE studio_probe.package ("
        "id serial PRIMARY KEY, course_link_id uuid NOT NULL REFERENCES shared.course_link (id), "
        "slug text NOT NULL, UNIQUE (course_link_id, slug));"
    ).ok
    known = migrated.run(
        "INSERT INTO studio_probe.package (course_link_id, slug) "
        "SELECT id, 'week-1' FROM shared.course_link;"
    )
    assert known.ok, known.error
    unknown = migrated.run(
        "INSERT INTO studio_probe.package (course_link_id, slug) "
        "VALUES ('00000000-0000-0000-0000-000000000000', 'x');"
    )
    assert not unknown.ok and unknown.sqlstate == FOREIGN_KEY_VIOLATION


def test_a_link_that_a_module_refers_to_cannot_be_deleted(migrated: Postgres) -> None:
    assert migrated.run(_insert()).ok
    assert migrated.run(
        "CREATE SCHEMA studio_probe; CREATE TABLE studio_probe.package ("
        "id serial PRIMARY KEY, course_link_id uuid NOT NULL REFERENCES shared.course_link (id));"
        "INSERT INTO studio_probe.package (course_link_id) SELECT id FROM shared.course_link;"
    ).ok
    deleted = migrated.run("DELETE FROM shared.course_link;")
    assert not deleted.ok and deleted.sqlstate == FOREIGN_KEY_VIOLATION


# The design documents themselves (these run without a database)


def test_the_design_document_has_both_sql_blocks() -> None:
    assert "CREATE TABLE shared.course_link" in _sql_block("up")
    assert _sql_block("down").strip() == "DROP TABLE shared.course_link;"


def test_the_design_document_is_a_draft_and_claims_no_approval() -> None:
    text = _flat(_design_text())
    assert "**Status:** Draft." in text
    assert "Nothing in this document is approved or lab-verified." in text
    assert "**Status:** Approved" not in text


@pytest.mark.parametrize("question", ["Q-A", "Q-B", "Q-C", "Q-D", "Q-E"])
def test_the_open_questions_are_listed_as_unresolved(question: str) -> None:
    text = _design_text()
    section = text.split("## 7. Unresolved questions", 1)[1].split("## 8.", 1)[0]
    assert f"| {question} |" in section


def test_the_design_states_the_decided_identity_and_the_lookup_rules() -> None:
    text = _flat(_design_text())
    assert "`(iss, context id)`" in text
    assert "`(iss, sub, context id)`" in text
    assert "`core_course_get_courses_by_field` with `field=id`" in text
    assert "`idnumber` must not be used" in text


def test_the_design_says_b4_response_fields_are_not_lab_verified() -> None:
    text = _flat(_design_text())
    assert "raw response fields" in text and "not lab-verified" in text


def test_the_integration_note_lists_the_findings_and_changes_no_module_design() -> None:
    text = _flat(INTEGRATION_DOC.read_text(encoding="utf-8"))
    for finding in ("F-1", "F-2", "F-3", "F-4", "F-5", "F-6"):
        assert f"| {finding} |" in text
    assert "It changes none of them." in text
    assert "Nothing below has been sent." in text

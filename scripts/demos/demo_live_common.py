"""Shared helpers for the live demo scripts, Tier 2 and Tier 3 (PLAN-demo-grading.md, H3).

`connect()` gives a library client over the read-only connection (scripts/demos/readonly_connection.py):
either offline, against the built-in fake site, or live, against the lab named by the environment
variables MOODLE53_URL and MOODLE53_WS_TOKEN (B4 §1). Nothing here reads, prints or stores the token.
`Recorder` collects what a script printed and the raw answers, and saves them OUTSIDE the repository.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import yaml

ROOT = Path(__file__).resolve().parents[2]
# The repository has a data folder named contracts/ at its root. Put libs/ first so that imports
# find the libraries, not that folder.
sys.path.insert(0, str(ROOT / "libs"))

from demo_fake_site import FAKE_TOKEN, FAKE_URL, FakeSite  # noqa: E402
from moodle_ws import (  # noqa: E402
    MoodleClient,
    MoodleConfigError,
    Site,
    SiteSettings,
    Token,
    load_site,
)
from readonly_connection import ReadOnlyTransport  # noqa: E402

MOODLE_VERSION: Final = "5.3"

# --- all user-facing text in one place (root CLAUDE.md §6) ---------------------------------

MISSING_SETTINGS = (
    "Live mode needs two environment variables: MOODLE53_URL (the lab site address) and "
    "MOODLE53_WS_TOKEN (the service token; keep it secret). One is missing or not valid. Set "
    "them in this shell, or run with --offline to use the built-in fake instead."
)
OUTPUT_INSIDE_REPOSITORY = (
    "The output path {path} is inside the repository. The full output of a live run is kept "
    "outside it. Name a folder elsewhere, for example in your documents folder."
)
OUTPUT_NOT_WRITTEN = (
    "The output could not be saved to {path}: {reason}. Name another path."
)
ERR_CONFIG = (
    "The --config file {path} could not be used: {reason}. Use a YAML file with the key "
    "course_id (a whole number above zero) and, for the dry run, optionally learners."
)
DESCRIBE_OFFLINE = "Moodle 5.3 fake (offline), read-only connection"
DESCRIBE_LIVE = "Moodle 5.3 lab (live), read-only connection"


class DemoError(Exception):
    """A problem the person running a demo can fix. The message says what to do next."""


@dataclass
class Connection:
    client: MoodleClient
    transport: ReadOnlyTransport
    settings: SiteSettings
    offline: bool
    fake: FakeSite | None


def connect(offline: bool, environ: Mapping[str, str] | None = None) -> Connection:
    """Build the client. This opens no network connection and makes no call."""
    transport: ReadOnlyTransport
    if offline:
        fake = FakeSite()
        settings = SiteSettings(
            Site.MOODLE53, MOODLE_VERSION, FAKE_URL, Token(FAKE_TOKEN)
        )
        transport = ReadOnlyTransport(post=fake.post, get=fake.get)
        return Connection(
            MoodleClient(settings, transport), transport, settings, True, fake
        )
    try:
        settings = load_site(Site.MOODLE53, environ)
    except MoodleConfigError:
        settings = None  # not raised here, so the library's message (and its context) is dropped
    if settings is None:
        raise DemoError(MISSING_SETTINGS)
    transport = ReadOnlyTransport()
    return Connection(
        MoodleClient(settings, transport), transport, settings, False, None
    )


def describe(connection: Connection) -> str:
    """One line for the screen. Never the site address, never the token."""
    return DESCRIBE_OFFLINE if connection.offline else DESCRIBE_LIVE


class Recorder:
    """What a script printed and the raw answers it got, saved together at the end."""

    def __init__(self) -> None:
        self.lines: list[str] = []
        self.answers: dict[str, Any] = {}

    def line(self, text: str) -> None:
        self.lines.append(text)

    def note(self, name: str, answer: Any) -> None:
        self.answers[name] = answer

    def save(self, path: Path) -> None:
        target = Path(path).resolve()
        if target.is_relative_to(ROOT.resolve()):
            raise DemoError(OUTPUT_INSIDE_REPOSITORY.format(path=path))
        document = {"lines": self.lines, "answers": self.answers}
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps(document, indent=2, ensure_ascii=True), encoding="utf-8"
            )
        except OSError as error:
            raise DemoError(
                OUTPUT_NOT_WRITTEN.format(path=path, reason=type(error).__name__)
            ) from None


def read_config(path: Path | None) -> dict[str, Any]:
    """The --config file as a mapping (empty when there is none)."""
    if path is None:
        return {}
    try:
        loaded = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise DemoError(
            ERR_CONFIG.format(path=path, reason=type(error).__name__)
        ) from None
    if not isinstance(loaded, dict):
        raise DemoError(ERR_CONFIG.format(path=path, reason="it is not a mapping"))
    return loaded


def course_id_from(config: Mapping[str, Any]) -> int | None:
    """`course_id` from the config: None when absent, an error when it is not a whole number."""
    if "course_id" not in config:
        return None
    course = config["course_id"]
    if type(course) is not int or course <= 0:
        raise DemoError(
            ERR_CONFIG.format(
                path="", reason="course_id must be a whole number above zero"
            )
        )
    return course


def check_output_path(out: Path | None) -> None:
    """Refuse an --out path inside the repository, before any work is done."""
    if out is not None and Path(out).resolve().is_relative_to(ROOT.resolve()):
        raise DemoError(OUTPUT_INSIDE_REPOSITORY.format(path=out))

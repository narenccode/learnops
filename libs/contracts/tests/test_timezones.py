"""The site time zone of a B2 course model (decision 0003 #20, guide-confirmed).

A name is valid when `zoneinfo.ZoneInfo` resolves it. `Asia/Calcutta` is an alias that some
systems do not have in their own database, so it needs the pinned `tzdata` package from the root
requirements.txt; CI installs it. There is no model builder yet (FR-C-01, Release 1), so these
tests cover the shared check and the SITE_TIMEZONE reader that the builder will call.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

import contracts
from contracts import (
    ConfigError,
    is_known_timezone,
    messages,
    site_timezone,
    timezone_issues,
)

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = json.loads(
    (ROOT / "contracts" / "course-model.v1.schema.json").read_text(encoding="utf-8")
)
EXAMPLES = ROOT / "contracts" / "examples" / "course-model.v1"

Doc = dict[str, Any]
PLACE = ("source", "timezone")

ACCEPTED = ["Asia/Kolkata", "Asia/Calcutta", "UTC", "Etc/GMT-5", "Europe/London"]
REJECTED = [
    "UTC+5:30",
    "Mars/olympus",
    "",
    " ",
    "Asia/Kolkata ",  # nothing is trimmed
    "Asia",  # a folder of zones, not a zone
    "../etc/passwd",
    "/etc/localtime",
    "a\x00b",
]


def model(name: str) -> Doc:
    loaded: Doc = json.loads((EXAMPLES / name).read_text(encoding="utf-8"))
    return copy.deepcopy(loaded)


# --- the check on source.timezone -----------------------------------------------------------


@pytest.mark.parametrize("name", ACCEPTED)
def test_a_name_zoneinfo_resolves_is_accepted(name: str) -> None:
    package = model("from-package.json")
    package["source"]["timezone"] = name
    assert is_known_timezone(name)
    assert timezone_issues(package) == []


@pytest.mark.parametrize("name", REJECTED)
def test_a_name_zoneinfo_cannot_resolve_is_rejected(name: str) -> None:
    package = model("from-package.json")
    package["source"]["timezone"] = name
    (issue,) = timezone_issues(package)
    assert issue.code == "timezone_unknown" and issue.rule == "B2"
    assert issue.location == PLACE
    assert messages.where(PLACE) in issue.message and repr(name) in issue.message
    assert "SITE_TIMEZONE" in issue.fix_hint and "UTC+5:30" in issue.fix_hint


@pytest.mark.parametrize("value", [1, True, 5.5, ["Asia/Kolkata"], {"a": 1}])
def test_a_timezone_that_is_not_text_is_never_known(value: object) -> None:
    assert not is_known_timezone(value)
    package = model("from-package.json")
    package["source"]["timezone"] = value
    assert [i.code for i in timezone_issues(package)] == ["timezone_unknown"]


def test_the_package_example_passes_the_schema_and_the_runtime_check() -> None:
    package = model("from-package.json")
    assert list(Draft202012Validator(SCHEMA).iter_errors(package)) == []
    assert timezone_issues(package) == []


def test_an_mbz_model_with_a_null_timezone_stays_valid() -> None:
    mbz = model("from-mbz.json")
    assert mbz["source"] == {"kind": "mbz", "mode": "full", "timezone": None}
    assert list(Draft202012Validator(SCHEMA).iter_errors(mbz)) == []
    assert timezone_issues(mbz) == []


def test_the_runtime_check_does_not_replace_the_schema_rules() -> None:
    # The schema still refuses a null timezone for a package and a zone for an .mbz; the runtime
    # check leaves those to it and judges only a name.
    validator = Draft202012Validator(SCHEMA)
    package = model("from-package.json")
    package["source"]["timezone"] = None
    assert timezone_issues(package) == []
    assert [tuple(e.absolute_path) for e in validator.iter_errors(package)] == [PLACE]
    mbz = model("from-mbz.json")
    mbz["source"]["timezone"] = "Asia/Kolkata"
    assert timezone_issues(mbz) == []
    assert [tuple(e.absolute_path) for e in validator.iter_errors(mbz)] == [PLACE]


@pytest.mark.parametrize("value", [None, [], "x", 3, {}, {"source": 1}, {"source": {}}])
def test_a_model_without_the_expected_shape_gives_no_timezone_issue(
    value: object,
) -> None:
    assert timezone_issues(value) == []  # the schema reports the shape


def test_the_model_is_not_changed_by_the_check() -> None:
    package = model("from-package.json")
    before = copy.deepcopy(package)
    timezone_issues(package)
    assert package == before


# --- SITE_TIMEZONE: required, never defaulted -----------------------------------------------


@pytest.mark.parametrize("name", ACCEPTED)
def test_a_configured_site_timezone_is_returned_as_set(name: str) -> None:
    assert site_timezone({"SITE_TIMEZONE": name}) == name


@pytest.mark.parametrize(
    "environ",
    [{}, {"SITE_TIMEZONE": ""}, {"SITE_TIMEZONE": "   "}, {"OTHER": "Asia/Kolkata"}],
    ids=["unset", "empty", "blank", "other variable only"],
)
def test_a_missing_site_timezone_fails_closed_and_never_defaults(
    environ: dict[str, str],
) -> None:
    with pytest.raises(ConfigError) as caught:
        site_timezone(environ)
    text = str(caught.value)
    assert "SITE_TIMEZONE is not set" in text
    assert ".env.example" in text and "There is no default" in text


@pytest.mark.parametrize("name", ["UTC+5:30", "Mars/olympus", "Asia/Kolkata "])
def test_an_invalid_site_timezone_fails_closed(name: str) -> None:
    with pytest.raises(ConfigError, match="not a time zone name"):
        site_timezone({"SITE_TIMEZONE": name})


def test_the_library_does_not_read_the_process_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SITE_TIMEZONE", "Asia/Kolkata")
    with pytest.raises(ConfigError):
        site_timezone({})  # only the mapping given counts


def test_the_configured_zone_is_the_one_stored_in_a_package_model() -> None:
    # What the future builder must do: read the zone once, store it, and the model then passes.
    package = model("from-package.json")
    package["source"]["timezone"] = site_timezone({"SITE_TIMEZONE": "Asia/Calcutta"})
    assert package["source"]["timezone"] == "Asia/Calcutta"
    assert list(Draft202012Validator(SCHEMA).iter_errors(package)) == []
    assert timezone_issues(package) == []


def test_the_names_are_exported_from_the_package() -> None:
    for name in ("site_timezone", "timezone_issues", "is_known_timezone"):
        assert hasattr(contracts, name), name

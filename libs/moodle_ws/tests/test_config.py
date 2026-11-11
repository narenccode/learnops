"""One token per site, from the environment only (B4 §1, guide on Q24)."""

from __future__ import annotations

from typing import Any

import pytest

from moodle_ws import MoodleConfigError, Site, load_site

URL = "https://site.invalid"
ENV = {
    "MOODLE45_URL": URL,
    "MOODLE45_WS_TOKEN": "made-up-45",
    "MOODLE53_URL": URL,
    "MOODLE53_WS_TOKEN": "made-up-53",
}


@pytest.mark.parametrize(
    ("site", "version", "value"),
    [(Site.MOODLE45, "4.5", "made-up-45"), (Site.MOODLE53, "5.3", "made-up-53")],
)
def test_each_site_has_its_own_token(site: Site, version: str, value: str) -> None:
    settings = load_site(site, ENV)
    assert settings.moodle_version == version
    assert settings.token.reveal() == value


def test_each_site_ignores_the_other_sites_token() -> None:
    environ = {key: value for key, value in ENV.items() if key != "MOODLE45_WS_TOKEN"}
    assert load_site(Site.MOODLE53, environ).token.reveal() == "made-up-53"
    with pytest.raises(MoodleConfigError, match="MOODLE45_WS_TOKEN"):
        load_site(Site.MOODLE45, environ)


def test_the_old_shared_variable_is_never_looked_up() -> None:
    class Recording(dict[str, str]):
        asked: set[str] = set()

        def get(self, key: str, default: Any = None) -> Any:
            self.asked.add(key)
            return super().get(key, default)

        def __getitem__(self, key: str) -> str:
            self.asked.add(key)
            return super().__getitem__(key)

    environ = Recording(ENV)
    load_site(Site.MOODLE45, environ)
    load_site(Site.MOODLE53, environ)
    assert "MOODLE_WS_TOKEN" not in Recording.asked
    assert Recording.asked == set(ENV)


def test_a_placeholder_url_is_refused_without_showing_the_token() -> None:
    with pytest.raises(MoodleConfigError, match="MOODLE45_URL") as caught:
        load_site(Site.MOODLE45, {**ENV, "MOODLE45_URL": "CHANGE_ME"})
    assert "made-up-45" not in str(caught.value)


def test_a_site_name_can_be_a_string() -> None:
    assert load_site("moodle53", ENV).site is Site.MOODLE53


def test_an_unknown_site_is_refused() -> None:
    with pytest.raises(MoodleConfigError, match="not a Moodle site") as caught:
        load_site("moodle40", ENV)
    assert caught.value.__context__ is None


def test_the_old_shared_variable_is_not_read() -> None:
    with pytest.raises(MoodleConfigError, match="MOODLE45_WS_TOKEN"):
        load_site(Site.MOODLE45, {"MOODLE45_URL": URL, "MOODLE_WS_TOKEN": "made-up"})


@pytest.mark.parametrize("variable", ["MOODLE45_URL", "MOODLE45_WS_TOKEN"])
def test_a_missing_setting_is_named(variable: str) -> None:
    environ = {key: value for key, value in ENV.items() if key != variable}
    with pytest.raises(MoodleConfigError, match=variable):
        load_site(Site.MOODLE45, environ)


@pytest.mark.parametrize("value", ["", "   "])
def test_a_blank_token_counts_as_missing(value: str) -> None:
    with pytest.raises(MoodleConfigError, match="not set"):
        load_site(Site.MOODLE45, {**ENV, "MOODLE45_WS_TOKEN": value})


def test_the_placeholder_is_refused() -> None:
    with pytest.raises(MoodleConfigError, match="placeholder"):
        load_site(Site.MOODLE45, {**ENV, "MOODLE45_WS_TOKEN": "CHANGE_ME"})


def test_the_environment_is_the_default_source(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in ENV.items():
        monkeypatch.setenv(name, value)
    assert load_site(Site.MOODLE45).token.reveal() == "made-up-45"


def test_a_configuration_error_never_shows_a_value() -> None:
    with pytest.raises(MoodleConfigError) as caught:
        load_site(Site.MOODLE45, {"MOODLE45_WS_TOKEN": "made-up-45"})
    assert "made-up-45" not in str(caught.value)

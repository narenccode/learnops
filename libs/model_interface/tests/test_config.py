"""Fake-provider rule (PRD B5.2, B5.4; docs/decisions/0001-b5-model-interface-v1.md).

fake is accepted only with LEARNOPS_ENV=test and MODEL_ALLOW_FAKE=true; the flag itself is refused
in the lab, in production and when LEARNOPS_ENV is unset. Both provider variables follow the rule.
"""

from __future__ import annotations

import pytest

from model_interface.config import (
    ConfigError,
    ProviderVariable,
    fake_provider_allowed,
    provider_from_env,
)

VARIABLES: tuple[ProviderVariable, ...] = ("MODEL_PROVIDER", "SPEECH_PROVIDER")
TEST_ON = {"LEARNOPS_ENV": "test", "MODEL_ALLOW_FAKE": "true"}


@pytest.mark.parametrize("variable", VARIABLES)
def test_fake_is_accepted_in_a_test_run_with_the_flag_on(
    variable: ProviderVariable,
) -> None:
    assert provider_from_env({**TEST_ON, variable: "fake"}, variable) == "fake"


@pytest.mark.parametrize("variable", VARIABLES)
@pytest.mark.parametrize(
    "env",
    [
        {},
        {"LEARNOPS_ENV": "test"},
        {"LEARNOPS_ENV": "test", "MODEL_ALLOW_FAKE": "false"},
        {"LEARNOPS_ENV": "lab"},
        {"LEARNOPS_ENV": "production"},
        {"MODEL_ALLOW_FAKE": "false"},
    ],
    ids=repr,
)
def test_fake_is_refused_without_the_test_setting(
    variable: ProviderVariable, env: dict[str, str]
) -> None:
    with pytest.raises(ConfigError, match="fake provider is turned off"):
        provider_from_env({**env, variable: "fake"}, variable)


@pytest.mark.parametrize("environment", ["lab", "production", ""])
def test_the_fake_flag_is_refused_outside_tests(environment: str) -> None:
    """Even with a real provider chosen: a lab or production service must not start with it."""
    env = {
        "LEARNOPS_ENV": environment,
        "MODEL_ALLOW_FAKE": "true",
        "MODEL_PROVIDER": "local",
    }
    with pytest.raises(ConfigError, match="for automated tests only"):
        provider_from_env(env, "MODEL_PROVIDER")


def test_the_fake_flag_is_refused_when_the_environment_is_unset() -> None:
    with pytest.raises(ConfigError, match="LEARNOPS_ENV is 'unset'"):
        fake_provider_allowed({"MODEL_ALLOW_FAKE": "true"})


@pytest.mark.parametrize("variable", VARIABLES)
@pytest.mark.parametrize("provider", ["local", "hosted"])
@pytest.mark.parametrize(
    "env",
    [{}, {"LEARNOPS_ENV": "lab"}, {"LEARNOPS_ENV": "production"}, TEST_ON],
    ids=repr,
)
def test_real_providers_are_accepted_everywhere(
    variable: ProviderVariable, provider: str, env: dict[str, str]
) -> None:
    assert provider_from_env({**env, variable: provider}, variable) == provider


@pytest.mark.parametrize("value", ["", "Fake", "openai", " "])
def test_unknown_provider_is_refused(value: str) -> None:
    with pytest.raises(ConfigError, match="not a provider"):
        provider_from_env({"MODEL_PROVIDER": value}, "MODEL_PROVIDER")


@pytest.mark.parametrize("environment", ["staging", "Test", "prod"])
def test_unknown_environment_is_refused(environment: str) -> None:
    with pytest.raises(ConfigError, match="not an environment"):
        fake_provider_allowed({"LEARNOPS_ENV": environment})


@pytest.mark.parametrize("flag", ["1", "yes", "on"])
def test_unclear_flag_value_is_refused(flag: str) -> None:
    with pytest.raises(ConfigError, match="'true' or 'false'"):
        fake_provider_allowed({"LEARNOPS_ENV": "test", "MODEL_ALLOW_FAKE": flag})

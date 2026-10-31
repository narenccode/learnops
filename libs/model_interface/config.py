"""Provider selection from environment variables (PRD B5.2, B5.4).

The fake provider calls no model, so a fake result reaching a mentor would look like a real draft.
The guide's rule (docs/decisions/0001-b5-model-interface-v1.md): fake is refused unless the
test-only setting is on, and that setting is refused in the lab and in production. An unset
LEARNOPS_ENV counts as "not test", so a forgotten variable can never let fake through.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final, Literal, get_args

Provider = Literal["local", "hosted", "fake"]
ProviderVariable = Literal["MODEL_PROVIDER", "SPEECH_PROVIDER"]

PROVIDERS: Final[tuple[Provider, ...]] = get_args(Provider)
ENVIRONMENTS: Final = ("test", "lab", "production")
ENV_VARIABLE: Final = "LEARNOPS_ENV"
ALLOW_FAKE_VARIABLE: Final = "MODEL_ALLOW_FAKE"
TEST_ENVIRONMENT: Final = "test"

# User-facing messages (PRD UI-05): what happened, then what to do next.
UNKNOWN_PROVIDER: Final = (
    "{variable} is '{value}', which is not a provider. Set it to one of: {allowed}."
)
UNKNOWN_ENVIRONMENT: Final = "LEARNOPS_ENV is '{value}', which is not an environment. Set it to one of: {allowed}."
BAD_FLAG: Final = "MODEL_ALLOW_FAKE is '{value}'. Set it to 'true' or 'false'."
FAKE_FLAG_OUTSIDE_TESTS: Final = (
    "MODEL_ALLOW_FAKE is on but LEARNOPS_ENV is '{env}'. The fake provider is for automated "
    "tests only: remove MODEL_ALLOW_FAKE here, or set LEARNOPS_ENV=test in a test run."
)
FAKE_NOT_ALLOWED: Final = (
    "{variable} is 'fake', but the fake provider is turned off. Use 'local' or 'hosted', or, "
    "in an automated test run only, set LEARNOPS_ENV=test and MODEL_ALLOW_FAKE=true."
)


class ConfigError(ValueError):
    """The provider configuration is invalid; the service must not start with it."""


def fake_provider_allowed(env: Mapping[str, str]) -> bool:
    """True only with LEARNOPS_ENV=test and MODEL_ALLOW_FAKE=true.

    Raises ConfigError for an unknown environment or flag value, and when the flag is on outside
    tests, so a lab or production service refuses to start instead of quietly ignoring it.
    """
    environment = env.get(ENV_VARIABLE, "").strip()
    if environment and environment not in ENVIRONMENTS:
        raise ConfigError(
            UNKNOWN_ENVIRONMENT.format(
                value=environment, allowed=", ".join(ENVIRONMENTS)
            )
        )
    flag = env.get(ALLOW_FAKE_VARIABLE, "false").strip().lower()
    if flag not in ("true", "false"):
        raise ConfigError(BAD_FLAG.format(value=flag))
    if flag == "true" and environment != TEST_ENVIRONMENT:
        raise ConfigError(FAKE_FLAG_OUTSIDE_TESTS.format(env=environment or "unset"))
    return flag == "true"


def provider_from_env(env: Mapping[str, str], variable: ProviderVariable) -> Provider:
    """The provider named by MODEL_PROVIDER or SPEECH_PROVIDER, after the fake-provider rule."""
    allow_fake = fake_provider_allowed(env)
    value = env.get(variable, "").strip()
    for provider in PROVIDERS:
        if value == provider:
            if provider == "fake" and not allow_fake:
                raise ConfigError(FAKE_NOT_ALLOWED.format(variable=variable))
            return provider
    raise ConfigError(
        UNKNOWN_PROVIDER.format(
            variable=variable, value=value, allowed=", ".join(PROVIDERS)
        )
    )

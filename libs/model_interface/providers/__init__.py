"""Provider selection (PRD B5.2).

create_provider() builds the provider named by MODEL_PROVIDER. get_provider() returns one shared
provider, which is what run() uses when a call passes none, so the PRD call shape
model.run(task, inputs, output_schema) keeps one fake provider and its responses between calls.

Both read the real process environment through config.provider_from_env, and get_provider() does
so on every call, so the fake-provider rule (decision record 0001 #3) applies to every caller even
after a provider is cached. The real local and hosted transports are not implemented yet (design
Q19).

There is no fallback and no silent switch. Each setting has one branch and nothing here catches a
failure, so if the selected provider cannot be built or reached the call fails. The shared provider
is never replaced behind the caller's back: a provider that disagrees with MODEL_PROVIDER, or a
second one, is refused.

Application services use the configured path: build with create_provider(), set it once at start
with configure_provider(), and call model.run(task, inputs, output_schema). Passing another
provider to run() is for test runs only, and resolve_provider() refuses it anywhere else.
"""

from __future__ import annotations

import os

from .. import messages
from ..call_log import is_test_run
from ..config import PROVIDERS, ConfigError, fake_provider_allowed, provider_from_env
from ..errors import ProviderUnavailable
from .base import Provider, ProviderRequest, ProviderResponse
from .fake import FakeProvider
from .hosted import HostedProvider, HostedTransport
from .local import LocalProvider, LocalTransport
from .transport import TransportError, TransportProvider, TransportReply

__all__ = [
    "FakeProvider",
    "HostedProvider",
    "HostedTransport",
    "LocalProvider",
    "LocalTransport",
    "Provider",
    "ProviderRequest",
    "ProviderResponse",
    "TransportError",
    "TransportProvider",
    "TransportReply",
    "configure_provider",
    "create_provider",
    "ensure_provider",
    "get_provider",
    "reset_provider",
    "resolve_provider",
]

_shared: Provider | None = None


def _invalid(provider: object, reason: str) -> ConfigError:
    return ConfigError(
        messages.INVALID_PROVIDER.format(kind=type(provider).__name__, reason=reason)
    )


def ensure_provider(provider: object) -> Provider:
    """The provider, if it really is one; otherwise ConfigError.

    A name alone proves nothing. The object must have a callable complete(), a supported name and
    a model. One calling itself "fake" also needs a test run, because a look-alike never went
    through FakeProvider's own guard.
    """
    if not isinstance(provider, Provider):
        raise _invalid(provider, "it needs name, model and complete()")
    if not callable(provider.complete):
        raise _invalid(provider, "complete is not callable")
    if provider.name not in PROVIDERS:
        raise _invalid(provider, f"its name must be one of {', '.join(PROVIDERS)}")
    if not isinstance(provider.model, str) or not provider.model.strip():
        raise _invalid(provider, "its model is empty")
    if provider.name == "fake" and not fake_provider_allowed(os.environ):
        raise _invalid(provider, "fake is for automated test runs only")
    return provider


def create_provider(
    *,
    local_transport: LocalTransport | None = None,
    hosted_transport: HostedTransport | None = None,
) -> Provider:
    """The provider named by MODEL_PROVIDER, after the fake-provider rule.

    Only the selected provider's transport is used. A transport is required for local and hosted
    until the protocol and the SDK are decided (Q19).
    """
    selected = provider_from_env(os.environ, "MODEL_PROVIDER")
    if selected == "fake":
        return FakeProvider()
    if selected == "hosted":
        if hosted_transport is None:
            raise ProviderUnavailable(messages.HOSTED_NOT_INTEGRATED)
        return HostedProvider(
            model=os.environ.get("MODEL_NAME", ""), transport=hosted_transport
        )
    if local_transport is None:
        raise ProviderUnavailable(messages.LOCAL_NOT_INTEGRATED)
    return LocalProvider(
        url=os.environ.get("MODEL_LOCAL_URL", ""),
        model=os.environ.get("MODEL_NAME", ""),
        transport=local_transport,
    )


def _mismatch(configured: str, selected: str) -> ConfigError:
    return ConfigError(
        messages.PROVIDER_MISMATCH.format(configured=configured, selected=selected)
    )


def configure_provider(provider: Provider) -> None:
    """Set the shared provider once, at service start, for example with create_provider(...).

    Refused: anything ensure_provider() refuses, a provider that disagrees with MODEL_PROVIDER, and
    a different provider when one is already set. Setting the same object again is harmless.
    """
    global _shared
    checked = ensure_provider(provider)
    selected = provider_from_env(os.environ, "MODEL_PROVIDER")
    if checked.name != selected:
        raise _mismatch(checked.name, selected)
    if _shared is not None and _shared is not checked:
        raise ConfigError(messages.PROVIDER_ALREADY_SET)
    _shared = checked


def reset_provider() -> None:
    """Forget the shared provider. For tests only, so it is not exported by model_interface."""
    global _shared
    _shared = None


def get_provider() -> Provider:
    """The shared provider, built on first use; the guard runs on every call.

    A shared provider that no longer matches MODEL_PROVIDER is an error, never a silent rebuild.
    """
    global _shared
    selected = provider_from_env(os.environ, "MODEL_PROVIDER")
    if _shared is None:
        _shared = create_provider()
    elif _shared.name != selected:
        raise _mismatch(_shared.name, selected)
    return _shared


def resolve_provider(provider: Provider | None) -> Provider:
    """The provider for one call.

    Passing one is for tests. Outside a test run a passed provider must agree with MODEL_PROVIDER
    and be the configured object, so a service cannot silently run on anything else.
    """
    if provider is None:
        return get_provider()
    checked = ensure_provider(provider)
    if is_test_run():
        return checked
    selected = provider_from_env(os.environ, "MODEL_PROVIDER")
    if checked.name != selected:
        raise _mismatch(checked.name, selected)
    if checked is not _shared:
        raise ConfigError(messages.PROVIDER_NOT_CONFIGURED)
    return checked

"""Provider selection (PRD B5.2).

create_provider() builds the provider named by MODEL_PROVIDER. get_provider() returns one shared
provider, which is what run() uses when a call passes none, so the PRD call shape
model.run(task, inputs, output_schema) keeps one fake provider and its responses between calls.

Both read the real process environment through config.provider_from_env, and get_provider() does
so on every call, so the fake-provider rule (decision record 0001 #3) applies to every caller even
after a provider is cached. The real local and hosted transports are not implemented yet (design
Q19).

There is no fallback. Each setting has one branch and nothing here catches a failure, so if the
selected provider cannot be built or reached the call fails; another provider is never tried.
"""

from __future__ import annotations

import os
from typing import Final

from .. import messages
from ..config import ConfigError, provider_from_env
from ..errors import ProviderUnavailable
from .base import Provider, ProviderRequest, ProviderResponse
from .fake import FakeProvider
from .hosted import HostedProvider, HostedTransport
from .local import LocalProvider, LocalTransport
from .transport import TransportError, TransportProvider, TransportReply

HOSTED_KEY_VARIABLE: Final = "MODEL_HOSTED_API_KEY"

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
    "get_provider",
    "reset_provider",
]

_shared: Provider | None = None


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
        # Only checked: the key's value is never stored here, nor shown in this error.
        if not os.environ.get(HOSTED_KEY_VARIABLE, "").strip():
            raise ConfigError(
                messages.MISSING_SETTING.format(variable=HOSTED_KEY_VARIABLE)
            )
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


def configure_provider(provider: Provider) -> None:
    """Set the shared provider, for example create_provider(local_transport=...)."""
    global _shared
    _shared = provider


def reset_provider() -> None:
    """Forget the shared provider. For tests."""
    global _shared
    _shared = None


def get_provider() -> Provider:
    """The shared provider, built on first use; the guard runs on every call."""
    global _shared
    selected = provider_from_env(os.environ, "MODEL_PROVIDER")
    if _shared is None or _shared.name != selected:
        _shared = create_provider()
    return _shared

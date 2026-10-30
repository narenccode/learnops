"""Provider selection (PRD B5.2).

create_provider() builds the provider named by MODEL_PROVIDER. get_provider() returns one shared
provider, which is what run() uses when a call passes none, so the PRD call shape
model.run(task, inputs, output_schema) keeps one fake provider and its responses between calls.

Both read the real process environment through config.provider_from_env, and get_provider() does
so on every call, so the fake-provider rule (decision record 0001 #3) applies to every caller even
after a provider is cached. The hosted provider and the real local transport are not implemented
yet (design Q19).
"""

from __future__ import annotations

import os

from .. import messages
from ..config import provider_from_env
from ..errors import ProviderUnavailable
from .base import Provider, ProviderRequest, ProviderResponse
from .fake import FakeProvider
from .local import LocalProvider, LocalTransport, TransportError, TransportReply

__all__ = [
    "FakeProvider",
    "LocalProvider",
    "LocalTransport",
    "Provider",
    "ProviderRequest",
    "ProviderResponse",
    "TransportError",
    "TransportReply",
    "configure_provider",
    "create_provider",
    "get_provider",
    "reset_provider",
]

_shared: Provider | None = None


def create_provider(*, local_transport: LocalTransport | None = None) -> Provider:
    """The provider named by MODEL_PROVIDER, after the fake-provider rule.

    local_transport is required for the local provider until the lab protocol is decided (Q19).
    """
    selected = provider_from_env(os.environ, "MODEL_PROVIDER")
    if selected == "fake":
        return FakeProvider()
    if selected == "hosted":
        raise ProviderUnavailable(messages.HOSTED_NOT_IMPLEMENTED)
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

"""Provider selection (PRD B5.2): create_provider() is the one way to get a provider.

It reads the real process environment through config.provider_from_env, so the fake-provider rule
(decision record 0001 #3) applies to every caller. The hosted provider and the real local transport
are not implemented yet (design Q19).
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
    "create_provider",
]


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

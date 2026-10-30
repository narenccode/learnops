"""Hosted provider: one hosted model API (PRD B5.2), behind an injectable transport.

The hosted provider and its SDK are NOT chosen (design Q19), so this module does not guess them. A
HostedTransport does the actual request through the provider's official SDK; none is implemented
yet, and tests inject a fake transport. The transport takes no URL, because how a hosted API is
addressed depends on that SDK.

This class holds no API key and does not require one, so mock transports need no credential. The
requirement itself stays: the real transport must take its key from the environment only (PRD
B5.2) and must refuse to start without it. How it does so is pending Q19.

Cost is what the transport reports; if it reports none, cost is None and never 0 (decision record
0001 #1).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from .. import messages
from ..config import Provider
from .base import ProviderRequest
from .transport import DEFAULT_TIMEOUT_S, TransportProvider, TransportReply


class HostedTransport(Protocol):
    def complete(
        self,
        *,
        model: str,
        prompt: str,
        inputs: Mapping[str, Any],
        output_schema: Mapping[str, Any],
        timeout_s: float,
    ) -> TransportReply: ...


class HostedProvider(TransportProvider):
    unreachable_message = messages.HOSTED_UNREACHABLE

    def __init__(
        self,
        *,
        model: str,
        transport: HostedTransport,
        timeout_s: float = DEFAULT_TIMEOUT_S,
    ) -> None:
        super().__init__(model=model, timeout_s=timeout_s)
        self._transport = transport

    @property
    def name(self) -> Provider:
        return "hosted"

    def _send(self, request: ProviderRequest) -> TransportReply:
        return self._transport.complete(
            model=self._model,
            prompt=request.prompt,
            inputs=request.inputs,
            output_schema=request.output_schema,
            timeout_s=self._timeout_s,
        )

    def _cost(self, reply: TransportReply) -> float | None:
        return reply.cost_estimate

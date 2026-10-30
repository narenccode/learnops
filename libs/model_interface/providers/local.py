"""Local provider: the lab model endpoint (PRD B5.2), behind an injectable transport.

The endpoint's wire protocol is NOT decided (design Q19, needs the lab), so this module does not
guess it. A LocalTransport does the actual request; none is implemented yet. Tests inject a fake
transport. When Q19 is answered, the real transport is added here and create_provider() uses it;
LocalProvider and run() do not change.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final, Protocol

from .. import messages
from ..config import ConfigError, Provider
from .base import ProviderRequest
from .transport import DEFAULT_TIMEOUT_S, TransportProvider, TransportReply

# A local model has no billed cost (decision record 0001 #2).
LOCAL_COST_USD: Final = 0.0


class LocalTransport(Protocol):
    def complete(
        self,
        *,
        url: str,
        model: str,
        prompt: str,
        inputs: Mapping[str, Any],
        output_schema: Mapping[str, Any],
        timeout_s: float,
    ) -> TransportReply: ...


class LocalProvider(TransportProvider):
    unreachable_message = messages.LOCAL_UNREACHABLE

    def __init__(
        self,
        *,
        url: str,
        model: str,
        transport: LocalTransport,
        timeout_s: float = DEFAULT_TIMEOUT_S,
    ) -> None:
        if not url.strip():
            raise ConfigError(
                messages.MISSING_SETTING.format(variable="MODEL_LOCAL_URL")
            )
        super().__init__(model=model, timeout_s=timeout_s)
        self._url = url
        self._transport = transport

    @property
    def name(self) -> Provider:
        return "local"

    def _send(self, request: ProviderRequest) -> TransportReply:
        return self._transport.complete(
            url=self._url,
            model=self._model,
            prompt=request.prompt,
            inputs=request.inputs,
            output_schema=request.output_schema,
            timeout_s=self._timeout_s,
        )

    def _cost(self, reply: TransportReply) -> float | None:
        return LOCAL_COST_USD

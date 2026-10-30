"""Local provider: the lab model endpoint (PRD B5.2), behind an injectable transport.

The endpoint's wire protocol is NOT decided (design Q19, needs the lab), so this module does not
guess it. A LocalTransport does the actual request; none is implemented yet. Tests inject a fake
transport. When Q19 is answered, the real transport is added here and create_provider() uses it;
LocalProvider and run() do not change.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Final, Protocol

from .. import messages
from ..config import ConfigError, Provider
from ..errors import ProviderUnavailable
from .base import ProviderRequest, ProviderResponse

DEFAULT_TIMEOUT_S: Final = 120.0  # starting value from design §6.3; tune in the lab
# A local model has no billed cost (decision record 0001 #2).
LOCAL_COST_USD: Final = 0.0


@dataclass(frozen=True)
class TransportReply:
    text: str = field(repr=False)  # repr() must never carry model output (PRD B5.3)
    input_tokens: int | None = None  # None: the endpoint did not report usage
    output_tokens: int | None = None


class TransportError(Exception):
    """The transport could not get an answer (unreachable, timeout, bad status)."""


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


class LocalProvider:
    def __init__(
        self,
        *,
        url: str,
        model: str,
        transport: LocalTransport,
        timeout_s: float = DEFAULT_TIMEOUT_S,
    ) -> None:
        for variable, value in (("MODEL_LOCAL_URL", url), ("MODEL_NAME", model)):
            if not value.strip():
                raise ConfigError(messages.MISSING_SETTING.format(variable=variable))
        self._url = url
        self._model = model
        self._transport = transport
        self._timeout_s = timeout_s

    @property
    def name(self) -> Provider:
        return "local"

    @property
    def model(self) -> str:
        return self._model

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        try:
            reply = self._transport.complete(
                url=self._url,
                model=self._model,
                prompt=request.prompt,
                inputs=request.inputs,
                output_schema=request.output_schema,
                timeout_s=self._timeout_s,
            )
        except Exception as error:  # any transport failure, not only TransportError
            # Only the exception's class name is kept. Its message and the chained original could
            # hold the URL, the request or learner content, so the chain is cut (from None).
            raise ProviderUnavailable(
                messages.LOCAL_UNREACHABLE.format(detail=type(error).__name__)
            ) from None
        return ProviderResponse(
            text=reply.text,
            input_tokens=reply.input_tokens,
            output_tokens=reply.output_tokens,
            cost_estimate=LOCAL_COST_USD,
        )

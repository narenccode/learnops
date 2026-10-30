"""What the local and hosted providers share (PRD B5.2).

Both reach a model through an injected transport. TransportProvider.complete() is the one place
that calls a transport and handles its failure, so the two providers cannot drift apart. A subclass
supplies only what differs: how it calls its transport, its cost, and its "unreachable" message.

A provider never holds an API key. The real hosted transport reads its key from the environment
(PRD B5.2), so a key cannot appear in a provider's repr(), in a log record or in an error.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar, Final

from .. import messages
from ..config import ConfigError, Provider
from ..errors import ProviderUnavailable
from .base import ProviderRequest, ProviderResponse

DEFAULT_TIMEOUT_S: Final = 120.0  # starting value from design §6.3; tune in the lab


@dataclass(frozen=True)
class TransportReply:
    text: str = field(repr=False)  # repr() must never carry model output (PRD B5.3)
    input_tokens: int | None = None  # None: the endpoint did not report usage
    output_tokens: int | None = None
    # US dollars. None: not reported, and never assumed to be 0.
    cost_estimate: float | None = None


class TransportError(Exception):
    """The transport could not get an answer (unreachable, timeout, bad status)."""


class TransportProvider(ABC):
    unreachable_message: ClassVar[str]

    def __init__(self, *, model: str, timeout_s: float = DEFAULT_TIMEOUT_S) -> None:
        if not model.strip():
            raise ConfigError(messages.MISSING_SETTING.format(variable="MODEL_NAME"))
        self._model = model
        self._timeout_s = timeout_s

    @property
    @abstractmethod
    def name(self) -> Provider: ...

    @property
    def model(self) -> str:
        return self._model

    @abstractmethod
    def _send(self, request: ProviderRequest) -> TransportReply:
        """Call this provider's transport."""

    @abstractmethod
    def _cost(self, reply: TransportReply) -> float | None:
        """This provider's cost for one reply, in US dollars; None when not known."""

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        try:
            reply = self._send(request)
        except Exception as error:  # any transport failure, not only TransportError
            # Only the exception's class name is kept. Its message and the chained original could
            # hold a URL, the request or learner content, so the chain is cut (from None).
            raise ProviderUnavailable(
                self.unreachable_message.format(detail=type(error).__name__)
            ) from None
        return ProviderResponse(
            text=reply.text,
            input_tokens=reply.input_tokens,
            output_tokens=reply.output_tokens,
            cost_estimate=self._cost(reply),
        )

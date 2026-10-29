"""The interface every model provider implements (PRD B5.2)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from ..config import Provider as ProviderName


@dataclass(frozen=True)
class ProviderRequest:
    task: str
    prompt: str
    prompt_version: str
    inputs: Mapping[str, Any]
    output_schema: Mapping[str, Any]


@dataclass(frozen=True)
class ProviderResponse:
    """Raw model text plus usage. None means "not reported", never 0 (decision record 0001 #1)."""

    text: str
    input_tokens: int | None
    output_tokens: int | None
    cost_estimate: float | None  # US dollars (decision record 0001 #2)


class Provider(Protocol):
    @property
    def name(self) -> ProviderName: ...

    @property
    def model(self) -> str: ...

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        """One model call. Raises ProviderUnavailable when the model cannot be reached."""
        ...

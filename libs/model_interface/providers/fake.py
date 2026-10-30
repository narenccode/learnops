"""Deterministic fake provider for automated tests (PRD B5.2; decision record 0001 #3).

It calls no model, so a fake result reaching a mentor would look like a real draft. Every
construction therefore goes through the existing guard in config.py, against the real process
environment: provider_from_env(os.environ, "MODEL_PROVIDER") must return "fake", which it does only
with LEARNOPS_ENV=test and MODEL_ALLOW_FAKE=true. No argument can switch the guard off, and a
mapping passed in by the caller is never consulted.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections import deque
from collections.abc import Mapping
from typing import Any, Final

from .. import messages
from ..config import ConfigError, Provider, provider_from_env
from ..errors import ModelError, ProviderUnavailable
from .base import ProviderRequest, ProviderResponse

FAKE_MODEL: Final = "fake-model"

# A str is sent as raw model text, for example to test output that is not JSON.
Output = Mapping[str, Any] | str


def input_key(inputs: Mapping[str, Any]) -> str:
    """Stable key for a set of inputs: sha256 of canonical JSON."""
    canonical = json.dumps(
        inputs, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class FakeProvider:
    def __init__(self) -> None:
        # Raises ConfigError unless LEARNOPS_ENV=test and MODEL_ALLOW_FAKE=true.
        selected = provider_from_env(os.environ, "MODEL_PROVIDER")
        if selected != "fake":
            raise ConfigError(messages.FAKE_NOT_SELECTED.format(value=selected))
        self._responses: dict[tuple[str, str], deque[Output]] = {}
        self._failures: deque[ModelError] = deque()
        self.requests: list[ProviderRequest] = []

    @property
    def name(self) -> Provider:
        return "fake"

    @property
    def model(self) -> str:
        return FAKE_MODEL

    def add_response(
        self, task: str, inputs: Mapping[str, Any], *outputs: Output
    ) -> None:
        """Queue outputs for one task and input set; the last one repeats once the rest are used."""
        queue = self._responses.setdefault((task, input_key(inputs)), deque())
        queue.extend(outputs)

    def fail_next(self, error: ModelError) -> None:
        """The next complete() call raises this error instead of answering."""
        self._failures.append(error)

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        self.requests.append(request)
        if self._failures:
            raise self._failures.popleft()
        queue = self._responses.get((request.task, input_key(request.inputs)))
        if not queue:
            raise ProviderUnavailable(
                messages.FAKE_NO_FIXTURE.format(task=request.task)
            )
        output = queue.popleft() if len(queue) > 1 else queue[0]
        text = output if isinstance(output, str) else json.dumps(output)
        # Matches contracts/examples/model-interface.v1.meta-fake.json: no model, no billed cost.
        return ProviderResponse(
            text=text, input_tokens=0, output_tokens=0, cost_estimate=0.0
        )

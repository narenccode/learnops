"""A scripted transport. It holds no Moodle-shaped data, so it encodes no guess about Moodle (Q53)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from moodle_ws import SiteSettings


@dataclass
class FakeTransport:
    answer: Any = "scripted answer"
    failure: Exception | None = None
    calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def call(
        self, settings: SiteSettings, function: str, params: Mapping[str, Any]
    ) -> Any:
        self.calls.append((function, dict(params)))
        if self.failure is not None:
            raise self.failure
        return self.answer

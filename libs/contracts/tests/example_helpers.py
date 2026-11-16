"""Shared fixtures for the contract-example tests: a small schema and a contracts-tree builder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# A small schema with a required string, an integer and an ISO date, like B1's start_date.
SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {"type": "string"},
        "count": {"type": "integer"},
        "start_date": {"type": ["string", "null"], "format": "date"},
        "items": {"type": "array", "items": {"type": "string"}},
    },
}
PREFIX = "contracts/examples/"
THING = "contracts/thing.v1.schema.json"
GOOD = '{"name": "a"}'
Files = dict[str, str | bytes]


def make_tree(
    tmp_path: Path,
    examples: Files | None = None,
    *,
    raw: Files | None = None,
    schema: dict[str, Any] | str | None = SCHEMA,
) -> Path:
    """A contracts folder with the schema thing.v1 and its examples.

    `examples` are files inside `examples/thing.v1/` (the folder layout); `raw` are files placed
    anywhere below `examples/` (flat examples such as `thing.v1.x.json`, other schemas' folders)."""
    contracts = tmp_path / "contracts"
    (contracts / "examples").mkdir(parents=True)
    if schema is not None:
        text = schema if isinstance(schema, str) else json.dumps(schema)
        (contracts / "thing.v1.schema.json").write_text(text, encoding="utf-8")
    files = {f"thing.v1/{rel}": c for rel, c in (examples or {}).items()} | (raw or {})
    for rel, content in files.items():
        target = contracts / "examples" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content if isinstance(content, bytes) else content.encode())
    return contracts


def with_ref(ref: str) -> dict[str, Any]:
    """SCHEMA with a property `link` that is a `$ref` to `ref`."""
    return {**SCHEMA, "properties": {**SCHEMA["properties"], "link": {"$ref": ref}}}

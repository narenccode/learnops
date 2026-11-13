"""The B4 allow-list, read from the contract so contract and code cannot drift apart (guide on Q1).

The `parameters` of an entry are not enforced: an empty list means "not yet determined", never "no
parameters" (B4 §2a), so refusing on it would block calls the lab has not checked yet.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

from jsonschema import Draft202012Validator

from . import messages
from .errors import FunctionNotAllowed, MoodleConfigError, NotSupported

_CONTRACTS: Final = Path(__file__).resolve().parents[2] / "contracts"
EXAMPLE_PATH: Final = _CONTRACTS / "examples" / "moodle-ws.v1.functions.json"
SCHEMA_PATH: Final = _CONTRACTS / "moodle-ws.v1.schema.json"


@dataclass(frozen=True)
class AllowList:
    # Function name -> Moodle version -> replacement name on that version.
    functions: Mapping[str, Mapping[str, str]]
    moodle_versions: frozenset[str]

    def resolve(self, function: str, moodle_version: str) -> str:
        """The name to call on that version. Matching is exact on purpose."""
        if moodle_version not in self.moodle_versions:
            raise NotSupported(messages.VERSION_NOT_SUPPORTED)
        replacements = self.functions.get(function)
        if replacements is None:
            raise FunctionNotAllowed(messages.FUNCTION_NOT_ALLOWED)
        return replacements.get(moodle_version, function)


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    raise MoodleConfigError(messages.ALLOW_LIST_UNREADABLE.format(file=path.name))


def _moodle_versions(schema: Any, schema_path: Path) -> frozenset[str]:
    """The versions B4 supports, from the schema, so they are not repeated in code."""
    try:
        function = schema["$defs"]["function"]["properties"]
        item = function["replacements"]["items"]["properties"]
        return frozenset(item["moodle_version"]["enum"])
    except (KeyError, TypeError):
        pass
    raise MoodleConfigError(messages.ALLOW_LIST_INVALID.format(file=schema_path.name))


def load_allowlist(
    path: Path = EXAMPLE_PATH, schema_path: Path = SCHEMA_PATH
) -> AllowList:
    document = _read_json(path)
    schema = _read_json(schema_path)
    moodle_versions = _moodle_versions(schema, schema_path)
    if not Draft202012Validator(schema).is_valid(document):
        raise MoodleConfigError(messages.ALLOW_LIST_INVALID.format(file=path.name))
    functions: dict[str, Mapping[str, str]] = {}
    for entry in document["functions"]:
        name = entry["name"]
        if name in functions:
            raise MoodleConfigError(
                messages.ALLOW_LIST_DUPLICATE.format(file=path.name, function=name)
            )
        replacements = {
            item["moodle_version"]: item["name"]
            for item in entry.get("replacements", [])
        }
        functions[name] = MappingProxyType(replacements)
    return AllowList(MappingProxyType(functions), moodle_versions)

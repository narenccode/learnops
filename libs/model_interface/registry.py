"""Task registry (PRD B5.1: "registered task name").

Each task name maps to its input schema, its output schema and its current prompt. Task names are
unique across the repository; each module registers its own tasks and owns their prompt folders
(design proposal, grading.md §4.2).

OPEN DECISION (guide): schemas are JSON Schemas (Draft 2020-12). PRD B5.1 allows this ("JSON
Schema / Pydantic model"), but root CLAUDE.md §6 requires "Pydantic models for every contract and
API payload", and grading.md §4.2 and §8 plan Pydantic 2.14.1. Pydantic is not installed, and
adding it changes requirements-dev.txt (owned by Students 1 and 2 and the guide), so nothing here
assumes it until the guide decides.
"""

from __future__ import annotations

import copy
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from . import messages
from .errors import DuplicateTask, InvalidTaskName, SchemaMismatch, UnregisteredTask
from .prompts import PROMPTS_DIR, Prompt, load_prompt

TASK_NAME: Final = re.compile(r"^[a-z][a-z0-9_]*$")

Schema = Mapping[str, Any]


@dataclass(frozen=True)
class TaskSpec:
    name: str
    input_schema: Schema
    output_schema: Schema
    prompt: Prompt


def _checked_schema(task: str, which: str, schema: Schema) -> dict[str, Any]:
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        detail = f"{error.validator} at {list(error.absolute_path) or 'top level'}"
        raise SchemaMismatch(
            messages.BAD_TASK_SCHEMA.format(which=which, task=task, detail=detail)
        ) from None
    # A private copy, so a caller changing its dict later cannot change the registered task.
    return copy.deepcopy(dict(schema))


class TaskRegistry:
    def __init__(self) -> None:
        self._tasks: dict[str, TaskSpec] = {}

    def register(
        self,
        name: str,
        input_schema: Schema,
        output_schema: Schema,
        prompt_dir: Path | None = None,
    ) -> TaskSpec:
        """Register a task; the prompt folder defaults to prompts/<name>/."""
        if not TASK_NAME.match(name):
            raise InvalidTaskName(messages.BAD_TASK_NAME.format(task=name))
        if name in self._tasks:
            raise DuplicateTask(messages.DUPLICATE_TASK.format(task=name))
        spec = TaskSpec(
            name=name,
            input_schema=_checked_schema(name, "input", input_schema),
            output_schema=_checked_schema(name, "output", output_schema),
            prompt=load_prompt(name, prompt_dir or PROMPTS_DIR / name),
        )
        self._tasks[name] = spec
        return spec

    def get(self, name: str) -> TaskSpec:
        try:
            return self._tasks[name]
        except KeyError:
            raise UnregisteredTask(
                messages.UNREGISTERED_TASK.format(task=name)
            ) from None

    def names(self) -> list[str]:
        return sorted(self._tasks)


DEFAULT_REGISTRY: Final = TaskRegistry()


def register_task(
    name: str,
    input_schema: Schema,
    output_schema: Schema,
    prompt_dir: Path | None = None,
) -> TaskSpec:
    """Register a task in the shared registry used by run()."""
    return DEFAULT_REGISTRY.register(name, input_schema, output_schema, prompt_dir)


def get_task(name: str) -> TaskSpec:
    return DEFAULT_REGISTRY.get(name)

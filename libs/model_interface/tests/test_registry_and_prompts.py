"""Task registry (PRD B5.1) and versioned prompt files (PRD B5.3)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from model_interface.errors import (
    DuplicateTask,
    InvalidTaskName,
    PromptError,
    SchemaMismatch,
    UnregisteredTask,
)
from model_interface.prompts import PROMPTS_DIR, load_prompt
from model_interface.registry import DEFAULT_REGISTRY, TaskRegistry

from .echo_task import ECHO_INPUT, ECHO_OUTPUT


def write_prompt(folder: Path, name: str, header: str, text: str = "Say hi.") -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(f"---\n{header}\n---\n{text}\n", encoding="utf-8")


# --- registry ------------------------------------------------------------------------------


def test_registered_task_can_be_looked_up(registry: TaskRegistry) -> None:
    spec = registry.get("example_echo")
    assert spec.output_schema == ECHO_OUTPUT
    assert spec.prompt.prompt_version == "example_echo/v1"
    assert registry.names() == ["example_echo"]


def test_duplicate_task_name_is_refused(registry: TaskRegistry) -> None:
    with pytest.raises(DuplicateTask, match="already registered"):
        registry.register("example_echo", ECHO_INPUT, ECHO_OUTPUT)


def test_unregistered_task_is_refused(registry: TaskRegistry) -> None:
    with pytest.raises(UnregisteredTask, match="'grade_draft' is not registered"):
        registry.get("grade_draft")


@pytest.mark.parametrize("name", ["", "Echo", "1echo", "echo-task", "echo task"])
def test_bad_task_name_is_refused(name: str) -> None:
    with pytest.raises(InvalidTaskName):
        TaskRegistry().register(name, ECHO_INPUT, ECHO_OUTPUT)


@pytest.mark.parametrize("which", ["input", "output"])
def test_invalid_schema_is_refused(which: str) -> None:
    bad = {"type": "not-a-type"}
    schemas = {"input": ECHO_INPUT, "output": ECHO_OUTPUT, which: bad}
    with pytest.raises(SchemaMismatch, match=f"The {which} schema"):
        TaskRegistry().register("example_echo", schemas["input"], schemas["output"])


def test_registered_schema_is_a_private_copy() -> None:
    output = {**ECHO_OUTPUT, "properties": {"echo": {"type": "string"}}}
    spec = TaskRegistry().register("example_echo", ECHO_INPUT, output)
    output["properties"]["echo"]["type"] = "integer"
    assert spec.output_schema["properties"]["echo"]["type"] == "string"


def test_task_without_a_prompt_cannot_be_registered(tmp_path: Path) -> None:
    with pytest.raises(PromptError, match="No prompt file"):
        TaskRegistry().register(
            "example_echo", ECHO_INPUT, ECHO_OUTPUT, prompt_dir=tmp_path
        )


def test_no_task_is_registered_in_the_shared_registry_by_the_library() -> None:
    """The example prompt is test-only: importing the library registers nothing."""
    assert DEFAULT_REGISTRY.names() == []


# --- prompts -------------------------------------------------------------------------------


def test_example_prompt_loads_with_its_version() -> None:
    prompt = load_prompt("example_echo", PROMPTS_DIR / "example_echo")
    assert (prompt.version, prompt.prompt_version) == (1, "example_echo/v1")
    assert prompt.text.startswith("TEST-ONLY EXAMPLE PROMPT")


def test_highest_version_is_used_unless_one_is_named(tmp_path: Path) -> None:
    write_prompt(tmp_path, "v1.md", "prompt_version: demo/v1", "old")
    write_prompt(tmp_path, "v2.md", "prompt_version: demo/v2", "new")
    assert load_prompt("demo", tmp_path).text == "new"
    assert load_prompt("demo", tmp_path, version=1).text == "old"
    with pytest.raises(PromptError):
        load_prompt("demo", tmp_path, version=3)


@pytest.mark.parametrize(
    ("name", "header", "detail"),
    [
        (
            "v2.md",
            "prompt_version: demo/v1",
            "expected 'demo/v2'",
        ),  # copied file, old header
        ("v1.md", "prompt_version: other/v1", "expected 'demo/v1'"),  # wrong task
        ("v1.md", "version: demo/v1", "prompt_version is 'None'"),  # header key missing
        ("v1.md", "prompt_version demo/v1", "is not 'key: value'"),
        ("v01.md", "prompt_version: demo/v1", "not v<N>.md"),
        ("draft.md", "prompt_version: demo/v1", "not v<N>.md"),
    ],
)
def test_prompt_version_must_agree_with_the_file(
    tmp_path: Path, name: str, header: str, detail: str
) -> None:
    write_prompt(tmp_path, name, header)
    with pytest.raises(PromptError, match=re.escape(detail)):
        load_prompt("demo", tmp_path)


def test_prompt_without_header_or_text_is_refused(tmp_path: Path) -> None:
    (tmp_path / "v1.md").write_text("Say hi.\n", encoding="utf-8")
    with pytest.raises(PromptError, match="header block is missing"):
        load_prompt("demo", tmp_path)
    write_prompt(tmp_path, "v1.md", "prompt_version: demo/v1", "")
    with pytest.raises(PromptError, match="prompt text is empty"):
        load_prompt("demo", tmp_path)

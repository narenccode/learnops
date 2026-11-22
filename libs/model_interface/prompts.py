"""Versioned prompt files (PRD B5.3): prompts/<task>/v<N>.md with a prompt_version header.

A file starts with a header block:

    ---
    prompt_version: <task>/v<N>
    ---
    <prompt text>

The header must name the file's own folder and version, so a copied file that kept its old
header is refused instead of being logged under the wrong version. A published version is never
edited; a change is a new v<N+1>.md file. The layout is the design proposal (grading.md §4.2).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from . import messages
from .errors import PromptError

PROMPTS_DIR: Final = Path(__file__).resolve().parent / "prompts"
VERSION_FILE: Final = re.compile(r"^v([1-9][0-9]*)\.md$")
HEADER_FENCE: Final = "---"


@dataclass(frozen=True)
class Prompt:
    task: str
    version: int
    prompt_version: str  # "<task>/v<N>", the value logged in result.meta
    text: str = field(repr=False)  # repr() must never carry prompt text (PRD B5.3)


def _bad(path: Path, detail: str) -> PromptError:
    return PromptError(
        messages.BAD_PROMPT_FILE.format(path=path.as_posix(), detail=detail)
    )


def read_prompt_file(path: Path, task: str) -> Prompt:
    """Parse one prompt file and check that its header agrees with its folder and file name."""
    match = VERSION_FILE.match(path.name)
    if not match:
        raise _bad(path, "the file name is not v<N>.md")
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != HEADER_FENCE or HEADER_FENCE not in lines[1:]:
        raise _bad(path, "the '---' header block is missing")
    end = lines.index(HEADER_FENCE, 1)
    header: dict[str, str] = {}
    for line in lines[1:end]:
        key, sep, value = line.partition(":")
        if not sep:
            raise _bad(path, f"header line '{line}' is not 'key: value'")
        header[key.strip()] = value.strip()
    expected = f"{task}/v{match.group(1)}"
    found = header.get("prompt_version")
    if found != expected:
        raise _bad(path, f"prompt_version is '{found}', expected '{expected}'")
    text = "\n".join(lines[end + 1 :]).strip()
    if not text:
        raise _bad(path, "the prompt text is empty")
    return Prompt(
        task=task, version=int(match.group(1)), prompt_version=expected, text=text
    )


def load_prompt(task: str, folder: Path, version: int | None = None) -> Prompt:
    """The given version of a task's prompt, or the highest version when version is None.

    Every .md file in the folder is checked, so a bad file is found at registration, not later.
    """
    paths = sorted(folder.glob("*.md")) if folder.is_dir() else []
    prompts = [read_prompt_file(path, task) for path in paths]
    if not prompts:
        raise PromptError(
            messages.NO_PROMPT.format(task=task, folder=folder.as_posix())
        )
    if version is None:
        return max(prompts, key=lambda p: p.version)
    for prompt in prompts:
        if prompt.version == version:
            return prompt
    raise PromptError(messages.NO_PROMPT.format(task=task, folder=folder.as_posix()))

#!/usr/bin/env python3
"""PreToolUse guard for LearnOps (see CLAUDE.md §2).

Blocks:  secrets written into files or commands; edits to .env; edits to Moodle/BigBlueButton code;
         `git commit --no-verify`.
Asks:    edits to contracts/ and docs/PRD.md (they follow PRD §B.0).
Reads the hook event as JSON on stdin and answers with a JSON decision on stdout.
Never raises: on any internal error it allows the action and lets normal permissions apply.
"""

import json
import re
import sys

SECRET_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9_\-]{20,}"), "an API key (sk-…)"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "an AWS access key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "a private key"),
    (re.compile(r"ghp_[A-Za-z0-9]{30,}"), "a GitHub token"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"), "a Slack token"),
    (
        re.compile(
            r"(?i)\b(api[_-]?key|secret|password|token)\b\s*[:=]\s*['\"][^'\"\s]{12,}['\"]"
        ),
        "a hard-coded secret value",
    ),
]

PROTECTED_CODE_DIRS = (
    "/var/www/moodle",
    "/var/www/html",
    "/usr/share/bigbluebutton",
    "/usr/local/bigbluebutton",
)

ASK_PATHS = ("contracts/", "docs/PRD.md")


def decide(decision: str, reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    sys.exit(0)


def find_secret(text: str):
    for pattern, label in SECRET_PATTERNS:
        if pattern.search(text or ""):
            return label
    return None


def written_text(tool: str, data: dict) -> str:
    if tool == "Write":
        return data.get("content", "")
    if tool == "Edit":
        return data.get("new_string", "")
    if tool == "MultiEdit":
        return "\n".join(e.get("new_string", "") for e in data.get("edits", []))
    if tool == "NotebookEdit":
        return data.get("new_source", "")
    return ""


def main() -> None:
    event = json.load(sys.stdin)
    tool = event.get("tool_name", "")
    data = event.get("tool_input", {}) or {}

    if tool == "Bash":
        cmd = data.get("command", "")
        if "--no-verify" in cmd and "git" in cmd:
            decide("deny", "Skipping git hooks is not allowed (CLAUDE.md §8).")
        label = find_secret(cmd)
        if label:
            decide(
                "deny",
                f"The command contains {label}. Use environment variables (CLAUDE.md §2.3).",
            )
        return

    path = (data.get("file_path") or data.get("notebook_path") or "").replace("\\", "/")
    name = path.rsplit("/", 1)[-1]

    if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
        decide(
            "deny",
            "Never edit .env files; document variables in .env.example (CLAUDE.md §2.3).",
        )

    if any(path.startswith(d + "/") or path == d for d in PROTECTED_CODE_DIRS):
        decide(
            "deny", "Moodle and BigBlueButton must stay unmodified (CLAUDE.md §2.1)."
        )

    label = find_secret(written_text(tool, data))
    if label:
        decide(
            "deny",
            f"This change would write {label} into a file. Use environment variables (CLAUDE.md §2.3).",
        )

    if any(p in path for p in ASK_PATHS):
        decide(
            "ask",
            "This is a shared contract or the PRD. Change it only through /contract-change (PRD §B.0).",
        )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)

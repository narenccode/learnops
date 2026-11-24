"""Interactive bot that answers from the garden rules by keyword match."""

from pathlib import Path

RULES = Path(__file__).with_name("rules.md").read_text(encoding="utf-8")
LINES = [line for line in RULES.splitlines() if line and not line.startswith("#")]


def reply(question: str) -> str:
    for word in question.lower().split():
        for line in LINES:
            if len(word) > 3 and word in line.lower():
                return line
    return "I don't know."


if __name__ == "__main__":
    while (question := input("> ")) != "quit":
        print(reply(question))

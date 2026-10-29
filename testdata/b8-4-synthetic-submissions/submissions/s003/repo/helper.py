"""Reply with the handbook paragraph that has the most words in common with the question."""

import sys
from pathlib import Path

SOURCE = Path(__file__).with_name("handbook.md")


def blocks(content: str) -> list[str]:
    return [
        b.strip() for b in content.split("\n\n") if b.strip() and not b.startswith("#")
    ]


def respond(query: str, content: str) -> str:
    terms = set(query.lower().split())
    top = max(blocks(content), key=lambda b: len(terms & set(b.lower().split())))
    if not terms & set(top.lower().split()):
        return "Sorry, the handbook does not say."
    return top


if __name__ == "__main__":
    print(respond(" ".join(sys.argv[1:]), SOURCE.read_text(encoding="utf-8")))

"""Answer a question with the handbook paragraph that shares the most words with it."""

import sys
from pathlib import Path

HANDBOOK = Path(__file__).with_name("handbook.md")


def paragraphs(text: str) -> list[str]:
    return [
        p.strip() for p in text.split("\n\n") if p.strip() and not p.startswith("#")
    ]


def answer(question: str, text: str) -> str:
    words = set(question.lower().split())
    best = max(paragraphs(text), key=lambda p: len(words & set(p.lower().split())))
    if not words & set(best.lower().split()):
        return "Sorry, the handbook does not say."
    return best


if __name__ == "__main__":
    print(answer(" ".join(sys.argv[1:]), HANDBOOK.read_text(encoding="utf-8")))

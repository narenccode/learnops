"""Answer a question from faq.md by word overlap. Synthetic test content."""

import sys
from pathlib import Path


def paragraphs() -> list[str]:
    text = Path(__file__).with_name("faq.md").read_text(encoding="utf-8")
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def answer(question: str) -> str:
    asked = set(question.lower().split())
    best = max(paragraphs(), key=lambda p: len(asked & set(p.lower().split())))
    if not asked & set(best.lower().split()):
        return "I do not know. Please ask about the food bank."
    return best


if __name__ == "__main__":
    print(answer(" ".join(sys.argv[1:])))

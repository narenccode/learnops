"""Returns the handbook paragraph that shares the most words with the question."""


def answer(question: str, paragraphs: list[str]) -> str:
    words = set(question.lower().split())
    return max(paragraphs, key=lambda p: len(words & set(p.lower().split())))

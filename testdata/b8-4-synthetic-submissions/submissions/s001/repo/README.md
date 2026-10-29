# Handbook assistant

A small assistant that answers questions about the fictional Zephyr Lane Tool Library handbook
(`handbook.md`). It finds the handbook paragraph that shares the most words with the question and
returns it.

## Setup

1. Install Python 3.12.
2. No other packages are needed.

## Usage

```
python assistant.py "How long can I borrow a drill?"
```

The assistant prints the best matching paragraph, or says it does not know.

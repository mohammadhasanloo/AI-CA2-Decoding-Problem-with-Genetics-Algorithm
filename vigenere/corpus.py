"""Reference vocabulary, and the words a candidate decoding produces."""

from __future__ import annotations

import re
from pathlib import Path

WORD_PATTERN = re.compile(r"[a-z]+")


def words(text: str) -> list[str]:
    """Lowercase alphabetic runs. Everything else is a separator."""
    return WORD_PATTERN.findall(text.lower())


def vocabulary(text: str) -> set[str]:
    """The set of distinct words in a reference text."""
    return set(words(text))


def load_vocabulary(path: Path | str) -> set[str]:
    return vocabulary(Path(path).read_text(encoding="utf-8", errors="ignore"))

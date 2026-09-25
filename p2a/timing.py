"""Find when a phrase is spoken inside a paragraph."""
from __future__ import annotations

import re

from .backends import Words


def _norm(word: str) -> str:
    return re.sub(r"[^a-z0-9]", "", word.lower())


def phrase_start(text: str, phrase: str, duration: float, words: Words) -> float:
    """Seconds into the paragraph at which `phrase` begins.

    Uses word timestamps when available, otherwise assumes speech is uniform over the
    characters of the paragraph. Raises ValueError if the phrase is not in the text.
    """
    target = [_norm(w) for w in phrase.split()]
    target = [t for t in target if t]
    if not target:
        raise ValueError("empty phrase")
    if words:
        spoken = [(_norm(w), s) for w, s, _ in words]
        spoken = [(w, s) for w, s in spoken if w]
        for i in range(len(spoken) - len(target) + 1):
            if [w for w, _ in spoken[i:i + len(target)]] == target:
                return spoken[i][1]
    # fallback: character position, matched on normalized words of the text
    text_words = text.split()
    normed = [_norm(w) for w in text_words]
    for i in range(len(normed) - len(target) + 1):
        if normed[i:i + len(target)] == target:
            chars_before = len(" ".join(text_words[:i]))
            return duration * chars_before / max(len(text), 1)
    raise ValueError(f"phrase {phrase!r} not found in paragraph: {text[:80]}...")

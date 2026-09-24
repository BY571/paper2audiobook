"""Parse a markdown audiobook script into speakable chunks.

Format:
    ---
    title: ...
    authors: ...
    ---
    ## Section heading      (not spoken, adds a longer pause before the next chunk)
    Paragraph text.         (one synthesis unit, short pause after)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import yaml

SECTION_PAUSE = 1.2
PARAGRAPH_PAUSE = 0.5


@dataclass
class Chunk:
    text: str
    pause_after: float


@dataclass
class Script:
    meta: dict = field(default_factory=dict)
    chunks: list[Chunk] = field(default_factory=list)

    @property
    def word_count(self) -> int:
        return sum(len(c.text.split()) for c in self.chunks)


def parse(source: str) -> Script:
    meta, body = _split_front_matter(source)
    chunks: list[Chunk] = []
    for block in re.split(r"\n\s*\n", body.strip()):
        block = block.strip()
        if not block:
            continue
        if block.startswith("#"):
            if chunks:
                chunks[-1].pause_after = SECTION_PAUSE
            continue
        text = " ".join(line.strip() for line in block.splitlines())
        chunks.append(Chunk(text=text, pause_after=PARAGRAPH_PAUSE))
    if chunks:
        chunks[-1].pause_after = 0.0
    return Script(meta=meta, chunks=chunks)


def _split_front_matter(source: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", source, re.DOTALL)
    if not m:
        return {}, source
    meta = yaml.safe_load(m.group(1)) or {}
    return meta, source[m.end():]

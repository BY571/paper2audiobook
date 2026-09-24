import numpy as np

from p2a import audio, script
from p2a.cli import synthesize

SAMPLE = """---
title: Test Paper
authors: A. Author
---

## Opening

First paragraph
spans two lines.

Second paragraph.

## Next section

Third paragraph.
"""


class FakeBackend:
    name = "fake"
    rate = 8000

    def synth(self, text):
        n = len(text.split())  # one tenth of a second per word
        t = np.arange(int(0.1 * n * self.rate)) / self.rate
        return np.sin(2 * np.pi * 440 * t).astype(np.float32), self.rate


def test_parse_sections_and_pauses():
    scr = script.parse(SAMPLE)
    assert scr.meta["title"] == "Test Paper"
    assert [c.text for c in scr.chunks] == [
        "First paragraph spans two lines.",
        "Second paragraph.",
        "Third paragraph.",
    ]
    assert [c.pause_after for c in scr.chunks] == [script.PARAGRAPH_PAUSE, script.SECTION_PAUSE, 0.0]
    assert scr.word_count == 9


def test_parse_without_front_matter():
    scr = script.parse("Just one paragraph.")
    assert scr.meta == {} and len(scr.chunks) == 1


def test_assemble_duration_includes_pauses():
    scr = script.parse(SAMPLE)
    pieces, rate = synthesize(scr, FakeBackend(), log=lambda *_: None)
    samples = audio.assemble(pieces, rate)
    expected = 0.1 * 9 + script.PARAGRAPH_PAUSE + script.SECTION_PAUSE
    assert abs(audio.duration(samples, rate) - expected) < 1e-3


def test_write_mp3(tmp_path):
    out = tmp_path / "x.mp3"
    audio.write_mp3(np.zeros(8000, dtype=np.float32), 8000, out, title="T", artist="A")
    assert out.exists() and out.stat().st_size > 0

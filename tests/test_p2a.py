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
    voice = "v"
    speed = 1.0
    rate = 8000

    def synth(self, text):
        n = len(text.split())  # one tenth of a second per word
        t = np.arange(int(0.1 * n * self.rate)) / self.rate
        return np.sin(2 * np.pi * 440 * t).astype(np.float32), self.rate, None


def test_parse_sections_and_pauses():
    scr = script.parse(SAMPLE)
    assert scr.meta["title"] == "Test Paper"
    assert [c.text for c in scr.chunks] == [
        "First paragraph spans two lines.",
        "Second paragraph.",
        "Third paragraph.",
    ]
    assert [c.pause_after for c in scr.chunks] == [script.PARAGRAPH_PAUSE, script.SECTION_PAUSE, 0.0]
    assert [c.section for c in scr.chunks] == ["Opening", "Opening", "Next section"]
    assert scr.word_count == 9


def test_parse_without_front_matter():
    scr = script.parse("Just one paragraph.")
    assert scr.meta == {} and len(scr.chunks) == 1


def test_assemble_duration_includes_pauses(tmp_path):
    scr = script.parse(SAMPLE)
    pieces, rate = synthesize(scr, FakeBackend(), cache_dir=tmp_path, log=lambda *_: None)
    samples = audio.assemble(pieces, rate)
    expected = 0.1 * 9 + script.PARAGRAPH_PAUSE + script.SECTION_PAUSE
    assert abs(audio.duration(samples, rate) - expected) < 1e-3
    assert len(list(tmp_path.glob("*.wav"))) == 3  # one cached wav per paragraph


def test_cache_hit_skips_synthesis(tmp_path):
    from p2a import cache

    class Counting(FakeBackend):
        calls = 0

        def synth(self, text):
            Counting.calls += 1
            return super().synth(text)

    b = Counting()
    cache.synth_cached(b, "hello world", tmp_path)
    cache.synth_cached(b, "hello world", tmp_path)
    assert Counting.calls == 1


def test_write_mp3(tmp_path):
    out = tmp_path / "x.mp3"
    audio.write_mp3(np.zeros(8000, dtype=np.float32), 8000, out, title="T", artist="A")
    assert out.exists() and out.stat().st_size > 0


def test_phrase_timing_with_and_without_words():
    from p2a.timing import phrase_start

    text = "First we build the model. Then we add hand-coded rules on top."
    words = [(w, i * 0.5, i * 0.5 + 0.4) for i, w in enumerate(text.replace(".", "").split())]
    assert phrase_start(text, "hand-coded rules", 6.0, words) == 8 * 0.5
    est = phrase_start(text, "hand-coded rules", 6.0, None)
    assert 3.5 < est < 4.5  # proportional to character position
    import pytest

    with pytest.raises(ValueError):
        phrase_start(text, "not there", 6.0, words)


def test_cache_stores_word_timings(tmp_path):
    from p2a import cache

    class Timed(FakeBackend):
        def synth(self, text):
            s, r, _ = super().synth(text)
            return s, r, [(w, i * 0.1, i * 0.1 + 0.1) for i, w in enumerate(text.split())]

    wav = cache.synth_cached(Timed(), "one two three", tmp_path)
    assert cache.load_words(wav) == [("one", 0.0, 0.1), ("two", 0.1, 0.2), ("three", 0.2, 0.3)]

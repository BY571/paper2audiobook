"""Manim base class that narrates a p2a script paragraph by paragraph.

Usage in scenes/<slug>.py:

    from p2a.video import *          # manim namespace + PaperScene

    class Video(PaperScene):
        def construct(self):
            with self.narrate() as n:            # paragraph 1
                self.play(Write(Text("Title")), run_time=2)
                self.wait(n.remaining)
            with self.narrate() as n:            # paragraph 2
                ...

Each narrate() consumes the next paragraph of the script (in order) and plays its audio.
The script, backend and voice are passed by `p2a --video` through environment variables.
"""
from __future__ import annotations

import json
import os
import sys
import textwrap
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from manim import *  # noqa: F401,F403  (re-exported for scene files)
from manim import Scene, config, logger
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.base import SpeechService

from . import cache, script, timing
from .backends import Backend, Words, make_backend

BACKGROUND = "#101418"
SMALL, BODY, HEADING, TITLE = 24, 32, 40, 48   # font sizes; nothing on screen should be below SMALL
PALETTE = {
    "blue": "#58C4DD",
    "yellow": "#FFD35A",
    "red": "#FC6255",
    "green": "#83C167",
    "grey": "#8A8F98",
    "white": "#ECECEC",
}


def label(text: str, size: int = BODY, color: str = PALETTE["white"], **kw) -> Text:
    """A text label. Keep on-screen text to a few words."""
    return Text(text, font_size=size, color=color, **kw)


class P2ASpeechService(SpeechService):
    def __init__(self, backend: Backend, cache_dir: Path):
        super().__init__(cache_dir=str(cache_dir))
        self.backend = backend
        self.last_words: Words = None

    def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
        wav = cache.synth_cached(self.backend, text, Path(self.cache_dir), log=logger.info)
        self.last_words = cache.load_words(wav)
        return {"input_text": text, "original_audio": wav.name}


@dataclass
class Narration:
    index: int
    text: str
    section: str
    duration: float
    _tracker: object
    _scene: object
    _words: Words = None

    @property
    def elapsed(self) -> float:
        return float(self._scene.renderer.time) - self._tracker.start_t

    @property
    def remaining(self) -> float:
        """Seconds of narration left. Use as the run_time of your last animation or wait."""
        return self._tracker.get_remaining_duration()

    def time_of(self, phrase: str) -> float:
        """Seconds into this paragraph at which the voice starts saying `phrase`."""
        return timing.phrase_start(self.text, phrase, self.duration, self._words)

    def until(self, phrase: str, lead: float = 0.0) -> float:
        """Wait until the voice reaches `phrase` (minus `lead` seconds). Returns how long it waited.
        Use it to reveal a thing at the moment it is mentioned:

            n.until("hand-coded rules"); self.play(FadeIn(rules_box), run_time=0.6)
        """
        wait = max(self.time_of(phrase) - lead - self.elapsed, 0.0)
        self._scene.wait(wait)
        return wait


class PaperScene(VoiceoverScene):
    """Reads the script named by P2A_SCRIPT; narrates paragraphs in order via narrate()."""

    def setup(self):
        script_path = os.environ.get("P2A_SCRIPT")
        if not script_path:
            raise SystemExit("P2A_SCRIPT is not set. Render with `p2a <script.md> --video`.")
        self.script = script.parse(Path(script_path).read_text())
        self.meta = self.script.meta
        backend = make_backend(
            os.environ.get("P2A_BACKEND", "kokoro"),
            os.environ.get("P2A_VOICE") or None,
            float(os.environ.get("P2A_SPEED", "1.0")),
        )
        cache_dir = Path(os.environ.get("P2A_CACHE", str(cache.DEFAULT_CACHE_DIR)))
        self.set_speech_service(P2ASpeechService(backend, cache_dir), create_subcaption=False)
        self.camera.background_color = BACKGROUND
        self._next = 0
        self._timeline: list[dict] = []

    @contextmanager
    def narrate(self):
        i = self._next
        if i >= len(self.script.chunks):
            raise RuntimeError(f"narrate() called {i + 1} times but the script has {len(self.script.chunks)} paragraphs")
        chunk = self.script.chunks[i]
        self._next += 1
        logger.info(f"[{i + 1}/{len(self.script.chunks)}] {chunk.section}: {chunk.text[:60]}...")
        with self.voiceover(text=chunk.text) as tracker:
            self._timeline.append({"index": i, "section": chunk.section, "start": tracker.start_t, "end": tracker.end_t})
            yield Narration(i, chunk.text, chunk.section, tracker.duration, tracker, self, self.speech_service.last_words)
        if chunk.pause_after:
            self.safe_wait(chunk.pause_after)

    def wait(self, duration=1.0, *args, **kwargs):
        """Like Scene.wait, but a zero or sub-frame duration is a no-op instead of an error,
        so `self.wait(n.remaining)` is always safe."""
        if duration > 1 / config.frame_rate:
            super().wait(duration, *args, **kwargs)

    def tear_down(self):
        n, total = self._next, len(self.script.chunks)
        if n < total:
            msg = f"Scene narrated {n} of {total} paragraphs. Every paragraph needs a narrate() block."
            print(msg, file=sys.stderr)
            raise RuntimeError(msg)
        if os.environ.get("P2A_TIMELINE"):
            Path(os.environ["P2A_TIMELINE"]).write_text(json.dumps(self._timeline))
        super().tear_down()

    # Small helpers that keep scene files short.

    def title_card(self, n: Narration):
        """Standard opening: paper title (wrapped) and authors."""
        title = Text("\n".join(textwrap.wrap(str(self.meta.get("title", "")), 42)), font_size=TITLE, color=PALETTE["white"], line_spacing=0.9)
        authors = Text(str(self.meta.get("authors", "")), font_size=SMALL, color=PALETTE["grey"])
        for t in (title, authors):
            if t.width > 12:
                t.scale_to_fit_width(12)
        group = VGroup(title, authors).arrange(DOWN, buff=0.6)
        self.play(Write(title), run_time=min(2, n.duration * 0.4))
        self.play(FadeIn(authors), run_time=min(1, n.duration * 0.2))
        self.wait(n.remaining - 0.5)
        self.play(FadeOut(group), run_time=0.5)

    def section_title(self, text: str, run_time: float = 0.5) -> Mobject:
        """Small label in the top-left corner that persists across a section."""
        lbl = Text(text, font_size=SMALL, color=PALETTE["grey"]).to_corner(UL)
        self.play(FadeIn(lbl), run_time=run_time)
        return lbl

    def clear_all(self, run_time: float = 0.5):
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=run_time)

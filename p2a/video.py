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

import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from manim import *  # noqa: F401,F403  (re-exported for scene files)
from manim import Scene, config, logger
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.base import SpeechService

from . import cache, script
from .backends import Backend, make_backend

BACKGROUND = "#101418"
PALETTE = {
    "blue": "#58C4DD",
    "yellow": "#FFD35A",
    "red": "#FC6255",
    "green": "#83C167",
    "grey": "#8A8F98",
    "white": "#ECECEC",
}


class P2ASpeechService(SpeechService):
    def __init__(self, backend: Backend, cache_dir: Path):
        super().__init__(cache_dir=str(cache_dir))
        self.backend = backend

    def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
        wav = cache.synth_cached(self.backend, text, Path(self.cache_dir), log=logger.info)
        return {"input_text": text, "original_audio": wav.name}


@dataclass
class Narration:
    index: int
    text: str
    section: str
    duration: float
    _tracker: object

    @property
    def remaining(self) -> float:
        """Seconds of narration left. Use as the run_time of your last animation or wait."""
        return self._tracker.get_remaining_duration()


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

    @contextmanager
    def narrate(self):
        i = self._next
        if i >= len(self.script.chunks):
            raise RuntimeError(f"narrate() called {i + 1} times but the script has {len(self.script.chunks)} paragraphs")
        chunk = self.script.chunks[i]
        self._next += 1
        logger.info(f"[{i + 1}/{len(self.script.chunks)}] {chunk.section}: {chunk.text[:60]}...")
        with self.voiceover(text=chunk.text) as tracker:
            yield Narration(i, chunk.text, chunk.section, tracker.duration, tracker)
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
        super().tear_down()

    # Small helpers that keep scene files short.

    def title_card(self, n: Narration):
        """Standard opening: paper title and authors."""
        title = Text(str(self.meta.get("title", "")), font_size=40, color=PALETTE["white"]).scale_to_fit_width(12)
        authors = Text(str(self.meta.get("authors", "")), font_size=24, color=PALETTE["grey"]).scale_to_fit_width(11)
        group = VGroup(title, authors).arrange(DOWN, buff=0.5)
        self.play(Write(title), run_time=min(2, n.duration * 0.4))
        self.play(FadeIn(authors), run_time=min(1, n.duration * 0.2))
        self.wait(n.remaining - 0.5)
        self.play(FadeOut(group), run_time=0.5)

    def section_title(self, text: str, run_time: float = 1.0) -> Mobject:
        """Small label in the top-left corner that persists across a section."""
        label = Text(text, font_size=22, color=PALETTE["grey"]).to_corner(UL)
        self.play(FadeIn(label), run_time=run_time)
        return label

    def clear_all(self, run_time: float = 0.5):
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=run_time)

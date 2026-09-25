"""Renders a two-paragraph scene at low quality with the silent backend. Needs manim installed."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

manim = pytest.importorskip("manim")

SCRIPT = """---
title: Video Test
authors: Nobody
---

## One

Four words are spoken here.

## Two

And here five more words spoken.
"""

SCENE = """
from p2a.video import *

class Video(PaperScene):
    def construct(self):
        with self.narrate() as n:
            self.title_card(n)
        with self.narrate() as n:
            dot = Dot(color=PALETTE["blue"])
            self.play(FadeIn(dot), run_time=0.5)
            n.until("five more")
            self.play(dot.animate.shift(RIGHT), run_time=0.3)
            self.wait(n.remaining)
"""

MISSING = SCENE.replace("        with self.narrate() as n:\n            dot", "        if False:\n            dot")


def _render(tmp_path: Path, scene_src: str) -> subprocess.CompletedProcess:
    (tmp_path / "scenes").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "t.md").write_text(SCRIPT)
    (tmp_path / "scenes" / "t.py").write_text(scene_src)
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])}
    return subprocess.run(
        [sys.executable, "-m", "p2a.cli", "scripts/t.md", "--video", "-q", "low", "--backend", "silent"],
        cwd=tmp_path, env=env, capture_output=True, text=True,
    )


def test_video_renders_and_matches_narration(tmp_path):
    r = _render(tmp_path, SCENE)
    assert r.returncode == 0, r.stdout + r.stderr
    out = tmp_path / "output" / "t.mp4"
    assert out.exists()
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
        capture_output=True, text=True, check=True,
    )
    # 9 words at 2.5 words/s = 3.6 s narration, plus one section pause, plus short transitions
    assert 4.0 < float(probe.stdout) < 8.0
    assert "Motion report" in r.stdout


def test_missing_narrate_block_fails(tmp_path):
    r = _render(tmp_path, MISSING)
    assert r.returncode != 0
    assert "narrated 1 of 2 paragraphs" in r.stdout + r.stderr

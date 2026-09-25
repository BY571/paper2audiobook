"""Post-render check: where does the picture stand still, and where is it empty?"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

FPS = 2
W, H = 160, 90
STATIC_WARN = 10.0   # seconds without visible change
EMPTY_WARN = 2.0     # seconds with (almost) nothing on screen


def frames(video: Path) -> np.ndarray:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={FPS},scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        capture_output=True, check=True,
    ).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W)


def analyse(video: Path, timeline: list[dict]) -> list[str]:
    """timeline: [{"index", "section", "start", "end"}, ...] from PaperScene. Returns warning lines."""
    fr = frames(video).astype(np.int16)
    body = fr.copy()
    body[:, :12, :40] = 0                       # ignore the corner section label
    lit = (body > 45).reshape(len(fr), -1).sum(axis=1)
    changed = (np.abs(np.diff(fr, axis=0)) > 20).sum(axis=(1, 2))   # pixels that changed between frames
    warnings = []
    for p in timeline:
        a, b = int(p["start"] * FPS), min(int(p["end"] * FPS), len(fr))
        if b - a < 2:
            continue
        static, s_at = _longest_run(changed[a:b - 1] < 25)
        empty, e_at = _longest_run(lit[a:b] < 15)
        static, s_at, empty, e_at = static / FPS, s_at / FPS, empty / FPS, e_at / FPS
        tag = f"paragraph {p['index'] + 1} ({p['section']}, {p['end'] - p['start']:.0f}s)"
        if static >= STATIC_WARN:
            warnings.append(f"{tag}: nothing moved for {static:.0f}s, from {s_at:.0f}s to {s_at + static:.0f}s into the paragraph")
        if empty >= EMPTY_WARN:
            warnings.append(f"{tag}: screen empty for {empty:.1f}s, starting {e_at:.0f}s in")
    return warnings


def _longest_run(mask: np.ndarray) -> tuple[int, int]:
    """(length, start index) of the longest run of True."""
    best = run = 0
    best_at = start = 0
    for i, m in enumerate(mask):
        if m:
            if run == 0:
                start = i
            run += 1
            if run > best:
                best, best_at = run, start
        else:
            run = 0
    return best, best_at


def load_timeline(path: Path) -> list[dict]:
    return json.loads(path.read_text())

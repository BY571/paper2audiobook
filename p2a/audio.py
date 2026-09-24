"""Assemble synthesized chunks into one MP3."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf


def assemble(pieces: list[tuple[np.ndarray, float]], rate: int) -> np.ndarray:
    """pieces: [(samples, pause_after_seconds), ...] -> one float32 array."""
    out = []
    for samples, pause in pieces:
        out.append(samples)
        if pause > 0:
            out.append(np.zeros(int(pause * rate), dtype=np.float32))
    return np.concatenate(out) if out else np.zeros(0, dtype=np.float32)


def write_mp3(samples: np.ndarray, rate: int, out: Path, title: str = "", artist: str = "") -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        sf.write(tmp.name, samples, rate)
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", tmp.name, "-codec:a", "libmp3lame", "-q:a", "2"]
        if title:
            cmd += ["-metadata", f"title={title}"]
        if artist:
            cmd += ["-metadata", f"artist={artist}"]
        subprocess.run(cmd + [str(out)], check=True)


def duration(samples: np.ndarray, rate: int) -> float:
    return len(samples) / rate

"""Per-paragraph audio cache shared by audio and video modes."""
from __future__ import annotations

import hashlib
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from .backends import Backend

DEFAULT_CACHE_DIR = Path(".cache/p2a")
RETRIES = 3


def cache_key(backend: Backend, text: str) -> str:
    raw = f"{backend.name}|{backend.voice}|{backend.speed}|{' '.join(text.split())}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def synth_cached(backend: Backend, text: str, cache_dir: Path = DEFAULT_CACHE_DIR, log=print) -> Path:
    """Synthesize text with the backend unless a cached WAV exists. Returns the WAV path."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{cache_key(backend, text)}.wav"
    if path.exists():
        return path
    for attempt in range(1, RETRIES + 1):
        try:
            samples, rate = backend.synth(text)
            break
        except Exception as e:  # noqa: BLE001
            if attempt == RETRIES:
                raise RuntimeError(f"synthesis failed after {RETRIES} attempts: {e}") from e
            log(f"  retry {attempt}: {e}")
            time.sleep(attempt)
    sf.write(path, samples, rate)
    return path


def load(path: Path) -> tuple[np.ndarray, int]:
    samples, rate = sf.read(path, dtype="float32")
    return samples, rate

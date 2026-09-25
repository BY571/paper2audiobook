"""Per-paragraph audio cache shared by audio and video modes.

Each paragraph becomes <hash>.wav and, when the backend reports word timings, <hash>.json
holding [[word, start, end], ...] in seconds.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from .backends import Backend, Words

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
            samples, rate, words = backend.synth(text)
            break
        except Exception as e:  # noqa: BLE001
            if attempt == RETRIES:
                raise RuntimeError(f"synthesis failed after {RETRIES} attempts: {e}") from e
            log(f"  retry {attempt}: {e}")
            time.sleep(attempt)
    if words:
        path.with_suffix(".json").write_text(json.dumps([[w, round(s, 4), round(e, 4)] for w, s, e in words]))
    sf.write(path, samples, rate)
    return path


def load(path: Path) -> tuple[np.ndarray, int]:
    samples, rate = sf.read(path, dtype="float32")
    return samples, rate


def load_words(wav_path: Path) -> Words:
    p = wav_path.with_suffix(".json")
    if not p.exists():
        return None
    return [(w, s, e) for w, s, e in json.loads(p.read_text())]

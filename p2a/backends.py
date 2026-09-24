"""Text-to-speech backends. Each returns (samples as float32 mono, sample_rate)."""
from __future__ import annotations

import io
import os
from typing import Protocol

import numpy as np


class Backend(Protocol):
    name: str
    voice: str
    speed: float

    def synth(self, text: str) -> tuple[np.ndarray, int]: ...


class KokoroBackend:
    """Local model, runs on CPU or GPU. Voices: af_heart, af_bella, am_adam, bm_george, ..."""

    name = "kokoro"

    def __init__(self, voice: str = "af_heart", speed: float = 1.0):
        from kokoro import KPipeline  # slow import, keep it lazy

        self.voice = voice
        self.speed = speed
        self.pipeline = KPipeline(lang_code=voice[0], repo_id="hexgrad/Kokoro-82M")

    def synth(self, text: str) -> tuple[np.ndarray, int]:
        parts = [audio for _, _, audio in self.pipeline(text, voice=self.voice, speed=self.speed)]
        samples = np.concatenate([np.asarray(p, dtype=np.float32) for p in parts])
        return samples, 24000


class OpenAIBackend:
    """OpenAI TTS. Needs OPENAI_API_KEY. Voices: alloy, echo, fable, onyx, nova, shimmer."""

    name = "openai"

    def __init__(self, voice: str = "alloy", speed: float = 1.0, model: str = "gpt-4o-mini-tts"):
        if not os.environ.get("OPENAI_API_KEY"):
            raise SystemExit("OPENAI_API_KEY is not set. Export it or use --backend kokoro.")
        from openai import OpenAI

        self.client = OpenAI()
        self.voice = voice
        self.speed = speed
        self.model = model

    def synth(self, text: str) -> tuple[np.ndarray, int]:
        import soundfile as sf

        resp = self.client.audio.speech.create(
            model=self.model, voice=self.voice, input=text, speed=self.speed, response_format="wav"
        )
        samples, rate = sf.read(io.BytesIO(resp.content), dtype="float32")
        if samples.ndim > 1:
            samples = samples.mean(axis=1)
        return samples, rate


class SilentBackend:
    """Silence lasting as long as the text would take to read. For fast video timing previews."""

    name = "silent"
    WORDS_PER_SECOND = 2.5

    def __init__(self, voice: str = "none", speed: float = 1.0):
        self.voice = voice
        self.speed = speed

    def synth(self, text: str) -> tuple[np.ndarray, int]:
        rate = 24000
        seconds = len(text.split()) / (self.WORDS_PER_SECOND * self.speed)
        return np.zeros(int(seconds * rate), dtype=np.float32), rate


DEFAULT_VOICE = {"kokoro": "af_heart", "openai": "alloy", "silent": "none"}


def make_backend(name: str, voice: str | None, speed: float) -> Backend:
    voice = voice or DEFAULT_VOICE[name]
    if name == "kokoro":
        return KokoroBackend(voice=voice, speed=speed)
    if name == "openai":
        return OpenAIBackend(voice=voice, speed=speed)
    if name == "silent":
        return SilentBackend(voice=voice, speed=speed)
    raise SystemExit(f"Unknown backend {name!r}. Choose from: {', '.join(DEFAULT_VOICE)}")

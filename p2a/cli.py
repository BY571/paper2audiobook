"""p2a: synthesize a markdown audiobook script into an MP3, or render a Manim video for it."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

from . import audio, cache, script
from .backends import DEFAULT_VOICE, Backend, make_backend

QUALITY_FLAGS = {"low": "-ql", "medium": "-qm", "high": "-qh"}


def synthesize(scr: script.Script, backend: Backend, cache_dir: Path = cache.DEFAULT_CACHE_DIR, log=print) -> tuple[list, int]:
    pieces, rate = [], None
    for i, chunk in enumerate(scr.chunks, 1):
        log(f"[{i}/{len(scr.chunks)}] {chunk.text[:60]}...")
        try:
            samples, rate = cache.load(cache.synth_cached(backend, chunk.text, cache_dir, log=log))
        except RuntimeError as e:
            raise SystemExit(f"Paragraph {i}: {e}") from e
        pieces.append((samples, chunk.pause_after))
    return pieces, rate


def render_video(script_path: Path, out: Path, backend: str, voice: str | None, speed: float, quality: str) -> None:
    scene_file = Path("scenes") / f"{script_path.stem}.py"
    if not scene_file.exists():
        sys.exit(f"{scene_file} not found. Write a scene file with `class Video(PaperScene)`, see VIDEO.md.")
    media_dir = cache.DEFAULT_CACHE_DIR / "manim"
    env = {
        **os.environ,
        "P2A_SCRIPT": str(script_path),
        "P2A_BACKEND": backend,
        "P2A_VOICE": voice or DEFAULT_VOICE[backend],
        "P2A_SPEED": str(speed),
        "P2A_CACHE": str(cache.DEFAULT_CACHE_DIR),
    }
    cmd = [sys.executable, "-m", "manim", "render", QUALITY_FLAGS[quality], "--media_dir", str(media_dir), "-o", out.stem, str(scene_file), "Video"]
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True, env=env)
    candidates = sorted(media_dir.glob(f"videos/{scene_file.stem}/*/{out.stem}.mp4"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        sys.exit("manim finished but no mp4 was found")
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(candidates[-1], out)
    print(f"\nWrote {out}")


def main(argv: list[str] | None = None) -> None:
    warnings.filterwarnings("ignore")  # torch deprecation noise from inside kokoro
    p = argparse.ArgumentParser(prog="p2a", description="Turn an audiobook script (markdown) into an MP3 or a Manim video.")
    p.add_argument("script", type=Path, help="markdown script, see GUIDELINES.md")
    p.add_argument("-o", "--out", type=Path, help="output file (default: output/<script-stem>.mp3 or .mp4)")
    p.add_argument("--backend", choices=list(DEFAULT_VOICE), default="kokoro")
    p.add_argument("--voice", help=f"voice name (defaults: {DEFAULT_VOICE})")
    p.add_argument("--speed", type=float, default=1.0)
    p.add_argument("--video", action="store_true", help="render scenes/<script-stem>.py with manim instead of an MP3")
    p.add_argument("-q", "--quality", choices=list(QUALITY_FLAGS), default="high", help="video quality (low = 480p preview)")
    args = p.parse_args(argv)

    scr = script.parse(args.script.read_text())
    if not scr.chunks:
        sys.exit(f"{args.script}: no paragraphs found")

    if args.video:
        out = args.out or Path("output") / f"{args.script.stem}.mp4"
        render_video(args.script, out, args.backend, args.voice, args.speed, args.quality)
        return

    out = args.out or Path("output") / f"{args.script.stem}.mp3"
    backend = make_backend(args.backend, args.voice, args.speed)
    pieces, rate = synthesize(scr, backend)
    samples = audio.assemble(pieces, rate)
    meta = scr.meta
    audio.write_mp3(samples, rate, out, title=str(meta.get("title", "")), artist=str(meta.get("authors", "")))

    mins, secs = divmod(int(audio.duration(samples, rate)), 60)
    print(f"\nWrote {out}  ({mins}:{secs:02d}, {scr.word_count} words, {len(scr.chunks)} paragraphs)")


if __name__ == "__main__":
    main()

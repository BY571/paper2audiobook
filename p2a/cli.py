"""p2a: synthesize a markdown audiobook script into an MP3."""
from __future__ import annotations

import argparse
import sys
import time
import warnings
from pathlib import Path

from . import audio, script
from .backends import DEFAULT_VOICE, Backend, make_backend

RETRIES = 3


def synthesize(scr: script.Script, backend: Backend, log=print) -> tuple[list, int]:
    pieces, rate = [], None
    for i, chunk in enumerate(scr.chunks, 1):
        log(f"[{i}/{len(scr.chunks)}] {chunk.text[:60]}...")
        for attempt in range(1, RETRIES + 1):
            try:
                samples, rate = backend.synth(chunk.text)
                break
            except Exception as e:  # noqa: BLE001
                if attempt == RETRIES:
                    raise SystemExit(f"Paragraph {i} failed after {RETRIES} attempts: {e}") from e
                log(f"  retry {attempt}: {e}")
                time.sleep(attempt)
        pieces.append((samples, chunk.pause_after))
    return pieces, rate


def main(argv: list[str] | None = None) -> None:
    warnings.filterwarnings("ignore")  # torch deprecation noise from inside kokoro
    p = argparse.ArgumentParser(prog="p2a", description="Turn an audiobook script (markdown) into an MP3.")
    p.add_argument("script", type=Path, help="markdown script, see GUIDELINES.md")
    p.add_argument("-o", "--out", type=Path, help="output mp3 (default: output/<script-stem>.mp3)")
    p.add_argument("--backend", choices=list(DEFAULT_VOICE), default="kokoro")
    p.add_argument("--voice", help=f"voice name (defaults: {DEFAULT_VOICE})")
    p.add_argument("--speed", type=float, default=1.0)
    args = p.parse_args(argv)

    scr = script.parse(args.script.read_text())
    if not scr.chunks:
        sys.exit(f"{args.script}: no paragraphs found")
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

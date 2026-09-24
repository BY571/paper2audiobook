# paper2audiobook

Turn a research paper into a 10 to 15 minute audiobook you can listen to on a walk.

An agent (Claude Code, Codex, Gemini CLI, or similar) reads the paper, decides what matters,
and writes a spoken-word script following [GUIDELINES.md](GUIDELINES.md). A small tool in this
repo turns that script into an MP3. The agent does the reading and thinking. The tool does
the voice.

## Usage

Open this repo in your agent and say:

> make me an audiobook of https://arxiv.org/abs/2403.12345

The agent follows [AGENTS.md](AGENTS.md): downloads the PDF, reads it, writes
`scripts/<slug>.md`, runs `uv run p2a scripts/<slug>.md`, and hands you `output/<slug>.mp3`.

## What the audiobook covers

The problem, the core idea, how it differs from current approaches, how the mechanism works,
what was tested and what was not, headline results, and a longer section on downsides and
open problems. It ends with a one-minute recap. No equations, no figure references, nothing
that only makes sense on paper. Read the PDF afterwards if you want the details.

## Video

The same script can become an animated explainer in the 3Blue1Brown style. The agent writes a
Manim scene file next to the script, one animation block per paragraph, and the tool renders
it with the narration synced automatically. See [VIDEO.md](VIDEO.md).

```
uv run p2a scripts/example-script.md --video              # 1080p, output/example-script.mp4
uv run p2a scripts/example-script.md --video -q low --backend silent   # fast timing preview
```

## Setup

```
uv sync
```

Needs `ffmpeg` on the PATH. For video mode also install the Pango and Cairo headers first
(`sudo apt install libcairo2-dev libpango1.0-dev` on Ubuntu), since Manim compiles against them.
If the build fails with `cannot find -lpango-1.0` and you have Anaconda on your PATH, its bundled
compiler is being picked up; run `CC=/usr/bin/gcc uv sync` instead. Kokoro, the default voice model, runs locally and downloads about
300 MB on first use. On Linux with an NVIDIA GPU it uses CUDA, otherwise CPU.

## Synthesizing a script yourself

```
uv run p2a scripts/example-script.md                      # kokoro, local
uv run p2a scripts/example-script.md --voice am_adam      # different local voice
uv run p2a scripts/example-script.md --backend openai     # needs OPENAI_API_KEY
uv run p2a scripts/example-script.md --speed 1.15 -o out.mp3
```

Kokoro voices: `af_heart`, `af_bella`, `af_sky`, `am_adam`, `am_michael`, `bf_emma`, `bm_george`
and more; the first letter is language (a: American, b: British). OpenAI voices: `alloy`, `echo`,
`fable`, `onyx`, `nova`, `shimmer`.

`--backend silent` produces silence timed to the text, useful for checking video timing quickly.

## Tests

```
uv run pytest
```

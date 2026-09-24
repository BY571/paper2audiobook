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

## Setup

```
uv sync
```

Needs `ffmpeg` on the PATH. Kokoro, the default voice model, runs locally and downloads about
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

## Tests

```
uv run pytest
```

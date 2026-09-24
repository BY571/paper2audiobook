# Instructions for agents

This repo turns a research paper into a short audiobook. You read the paper and write the
script. The tool here turns the script into an MP3. You do the thinking; the tool does the
voice.

A typical request looks like: "make me an audiobook of https://arxiv.org/abs/2403.12345".

## Workflow

1. **Get the paper.** For an arXiv link, download the PDF:
   `curl -L https://arxiv.org/pdf/<id> -o papers/<id>.pdf`
   For a local PDF, copy or reference it as is. Then read the PDF directly with your own
   PDF reading ability. Read all of it, including the appendix, before writing anything.

2. **Write the script** to `scripts/<short-slug>.md` following [GUIDELINES.md](GUIDELINES.md)
   exactly: the front matter, the nine sections, the writing rules. Use a short slug derived
   from the title, like `scripts/dreamer-v3.md`. See `scripts/example-script.md`.

3. **Self-check.** Run the checklist at the end of GUIDELINES.md against your script and fix
   every item that fails. Pay particular attention to the experiments section saying what was
   not tested, and the downsides section.

4. **Synthesize.**
   ```
   uv run p2a scripts/<short-slug>.md
   ```
   Output goes to `output/<short-slug>.mp3`. The command prints duration and word count.
   Options: `--backend openai` (needs `OPENAI_API_KEY`), `--voice <name>`, `--speed 1.1`.
   If the user did not say which backend, use the default (kokoro, local).

5. **Report.** Give the user the MP3 path, the duration, and three sentences: what the paper
   does, its main result, and its main limitation.

6. **Video, only if asked.** Follow [VIDEO.md](VIDEO.md): write `scenes/<short-slug>.py`, preview
   with `uv run p2a scripts/<short-slug>.md --video -q low --backend silent`, then render with
   `uv run p2a scripts/<short-slug>.md --video`. Output is `output/<short-slug>.mp4`.

## Setup (once per machine)

```
uv sync
```

Requires `ffmpeg` on the PATH. Kokoro downloads its model on first use (about 300 MB) and
runs on GPU if available, otherwise CPU. Video mode needs the Pango and Cairo development
headers (`apt install libcairo2-dev libpango1.0-dev` on Debian/Ubuntu) before `uv sync`.

## Rules

- Do not put equations, symbols, or figure references in the script. The listener cannot see.
- Do not skip the appendix when reading. Limitations often hide there.
- Do not invent results. If the paper does not report a comparison, do not claim one.
- Keep scripts in `scripts/` and scenes in `scenes/` so the user can re-render later.
- `papers/` and `output/` are gitignored. `scripts/` is committed.

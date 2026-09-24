# Video guidelines

Video mode turns the same script into an animated explainer in the style of 3Blue1Brown:
dark background, a few colours, one idea on screen at a time, diagrams that build up as the
narration mentions each piece. The narration is the script. You only add pictures.

Write the audiobook script first and get it right. Then write `scenes/<slug>.py`.

## How the scene file works

```python
from p2a.video import *          # manim namespace, PaperScene, PALETTE

class Video(PaperScene):
    def construct(self):
        with self.narrate() as n:            # paragraph 1 of the script
            self.title_card(n)
        with self.narrate() as n:            # paragraph 2
            box = RoundedRectangle(width=4, height=2, color=PALETTE["blue"])
            label = Text("policy", font_size=32).move_to(box)
            self.play(Create(box), Write(label), run_time=2)
            self.wait(n.remaining)           # hold until the narration ends
        ...
```

Rules the tool enforces:

- Each `with self.narrate() as n:` block plays the next paragraph, in script order. The number
  of blocks must equal the number of paragraphs. The render fails otherwise.
- `n.duration` is the paragraph's length in seconds. `n.remaining` is how much of it is left
  right now. `n.text` and `n.section` are there if you need them.
- The block waits for the narration to finish before moving on, so animations that are shorter
  than the paragraph are fine. Animations longer than the paragraph push the next paragraph
  later; keep the total animation time inside a block under `n.duration`.
- If a block ends by fading things out, put `self.wait(max(n.remaining - 0.6, 0))` before the
  fade. Otherwise the screen goes dark while the voice is still talking. This is the most
  common mistake; the silent preview makes it easy to spot.

Helpers on `PaperScene`: `title_card(n)` for the opening paragraph, `section_title(text)` for a
small persistent corner label, `clear_all()` to fade everything out. `PALETTE` has blue, yellow,
red, green, grey, white. Background is set for you.

## Style

- Dark background, light strokes. Use `PALETTE` colours only. One accent colour per concept
  and keep it consistent: if the policy network is blue in one section it is blue everywhere.
- One idea on screen at a time. When the narration moves to a new idea, transform or fade the
  old one out. Do not accumulate.
- Build diagrams piece by piece, in the order the narration mentions the pieces. Use `n.remaining`
  splits: if a paragraph names three components, show each after roughly a third of the time.
- Prefer shapes, arrows, and short labels over sentences. On-screen text is at most a few words.
  Never put a paragraph of text on screen. Never show an equation unless the narration is about
  the shape of that equation, which the audiobook guideline already discourages.
- Motion should mean something. Transform an object when the narration says it changes. Move
  data along an arrow when the narration says it flows. Do not animate for decoration.
- The mechanism section is where the video earns its keep. Spend most of your effort there.
  Results can be a single bar chart or a number growing on screen. The recap can reuse the
  mechanism diagram at small scale.
- Figures from the paper are allowed when a diagram would take too long to redraw. Crop them
  with `pdftoppm -f <page> -l <page> -r 150 -png papers/<id>.pdf /tmp/fig` and load with
  `ImageMobject`. Keep them for at most one paragraph each.
- Use `Text`, not `Tex`, for labels. `MathTex` needs LaTeX and is rarely needed.

## Workflow

1. Write and check the audiobook script as usual.
2. Write `scenes/<slug>.py`. Start by pasting one `narrate()` block per paragraph with only
   `self.wait(n.remaining)` inside, so the structure is right, then fill in visuals.
3. Preview fast: `uv run p2a scripts/<slug>.md --video -q low --backend silent`. Silent audio
   with estimated timing, 480p, renders in a minute or two. Fix errors here.
4. Real render: `uv run p2a scripts/<slug>.md --video`. Kokoro audio, 1080p. Several minutes.
5. Output is `output/<slug>.mp4`. Report the path and duration.

## Self-check

1. Same number of `narrate()` blocks as script paragraphs, in the same order?
2. Does the mechanism section animate how the parts interact, not just label them?
3. Is any text on screen longer than a short phrase? Shorten it.
4. Does anything stay on screen after the narration has moved on from it?
5. Are colours consistent per concept across the whole video?
6. Did the low quality preview render without errors and without a paragraph where the screen is empty?

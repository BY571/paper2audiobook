# Video guidelines

Video mode turns the same script into an animated explainer in the style of 3Blue1Brown. The
narration is the script, unchanged. You add the pictures. The bar is not "a slide per
paragraph". It is: the picture changes with the sentences, the mechanism is shown moving, and a
viewer with the sound off could still follow the argument.

Write the audiobook script first and get it right. Then write `scenes/<slug>.py`.

## How the scene file works

```python
from p2a.video import *          # manim namespace, PaperScene, label(), PALETTE, font sizes

class Video(PaperScene):
    def construct(self):
        with self.narrate() as n:            # paragraph 1 of the script
            self.title_card(n)
        with self.narrate() as n:            # paragraph 2
            box = RoundedRectangle(width=5, height=2.4, color=PALETTE["blue"])
            self.play(Create(box), run_time=1)
            n.until("hand-coded rules")      # wait until the voice says this
            self.play(Write(label("hand-coded rules").next_to(box, DOWN)), run_time=0.8)
            n.until("transaction cost")
            self.play(Indicate(box, color=PALETTE["red"]))
        ...
```

What the tool guarantees:

- Each `with self.narrate() as n:` block plays the next paragraph, in script order. The number
  of blocks must equal the number of paragraphs or the render fails.
- The block holds the last frame until the narration ends. Animations shorter than the paragraph
  are fine. Animations longer than the paragraph delay everything after them; the motion report
  will not catch that, so keep the sum of your `run_time`s under `n.duration`.
- `n.until("phrase")` waits until the voice reaches that phrase. With Kokoro it uses the model's
  word timestamps, so it is accurate to a fraction of a second. With other backends it estimates
  from the phrase's position in the paragraph. The phrase must appear in the paragraph verbatim
  (punctuation and case ignored) or the render fails, which catches typos early.
- `n.duration`, `n.elapsed`, `n.remaining`, `n.text`, `n.section` are available. `n.time_of(phrase)`
  returns the second at which a phrase starts without waiting.
- After the render, the tool prints a motion report: for each paragraph, the longest stretch in
  which nothing on screen changed and any stretch in which the screen was empty. Treat every
  line of it as a defect to fix.

Helpers: `title_card(n)` for the opening paragraph, `section_title(text)` for a small persistent
corner label, `clear_all()` to fade everything out, `label(text, size, color)` for text. Font size
constants `SMALL, BODY, HEADING, TITLE` are 24, 32, 40, 48. `PALETTE` has blue, yellow, red,
green, grey, white. The background is set for you.

## Pacing

This is where most first attempts fail. A diagram that appears in the first three seconds and
then sits still for thirty is a slide, not an animation.

- **Something changes on screen at least every eight seconds.** Use `n.until(...)` to tie each
  change to the sentence that motivates it. A paragraph with five sentences should have roughly
  five visual beats.
- **Never start a block empty.** The first thing on screen appears in the first second of the
  paragraph, before any `n.until`. If the first phrase you want to sync to is ten seconds in,
  put up the frame it will land in (an axis, a grid, a heading) immediately.
- **Reveal in narration order.** When the voice names three components, the three components
  appear one at a time as they are named, not all at once at the start.
- **Emphasis counts as motion.** When the voice returns to something already on screen,
  `Indicate` it, recolour it, or grow it briefly. When the voice describes data flowing, move a
  dot or a copy of the data along the arrow.
- **Do not fade out early.** If a block ends by fading things out, put
  `self.wait(max(n.remaining - 0.6, 0))` before the fade, or use `n.until` on the paragraph's
  last phrase. Otherwise the screen goes dark while the voice is still talking.
- Never rely on fixed fractions like `n.duration * 0.3` to guess when a sentence starts. That is
  what `n.until` is for.

## Continuity

- **Within a section, transform; between sections, clear.** Keep the central diagram of the
  section on screen and change it: highlight a part, zoom into it with `self.play(diagram.animate.scale(...))`,
  replace a part with `ReplacementTransform`. Cut to black only when the section changes.
- The mechanism section should have one anchor diagram of the whole system, built in the first
  paragraph that describes it, and every later paragraph in that section should visibly touch
  the part of the anchor it explains, even if it also opens a detail view beside it.
- The recap should bring the anchor diagram back, not draw something new.

## Composition

- **Fill the frame.** The main object of a paragraph is 8 to 12 Manim units wide (the frame is
  about 14 wide and 8 tall). Small diagrams centred in empty space look like a thumbnail.
- **Text at `BODY` or larger.** `SMALL` only for axis ticks and the corner label. A viewer on a
  phone must be able to read every label.
- **At most a few words per label.** No sentences on screen. If you need a sentence to explain a
  picture, the picture is wrong.
- **No text-only screens.** A list of phrases is not a visual. Each item in a list needs its own
  small picture: an icon, a mini diagram, a number that grows. This applies with full force to
  the "not tested" paragraph and to every downside in the conclusion, which is exactly where
  first attempts degrade into bullet points.
- **Real numbers, real axes.** Charts show the paper's numbers with axes a viewer can read
  (write "1×, 10×, 100×", not "0, 1, 2" on a log axis). A sketched curve that is not from the
  paper must be labelled "schematic" on screen.
- **One accent colour per concept, everywhere.** If the policy network is blue in the idea
  section it is blue in the mechanism, the results and the recap.
- Figures from the paper are allowed when a diagram would take too long to redraw. Crop them
  with `pdftoppm -f <page> -l <page> -r 150 -png papers/<id>.pdf /tmp/fig` and load with
  `ImageMobject`. Keep each for at most one paragraph.
- Use `Text`, not `Tex`, for labels. `MathTex` needs LaTeX and is rarely needed.

## Workflow

1. Write and check the audiobook script as usual.
2. Write `scenes/<slug>.py`. Start with one `narrate()` block per paragraph containing only
   `self.wait(n.remaining)`, so the structure is right, then fill in visuals section by section.
3. Preview fast: `uv run p2a scripts/<slug>.md --video -q low --backend silent`. Silent audio
   with estimated timing, 480p, about a minute for a 15 minute video. Fix errors here.
4. Read the motion report. Fix every paragraph it names, then preview again. Repeat until the
   report is clean.
5. Real render: `uv run p2a scripts/<slug>.md --video`. Kokoro audio, exact phrase timing,
   1080p. About ten minutes. Read the motion report once more, since real timing differs a
   little from the silent estimate.
6. Look at the result. `ffmpeg -i output/<slug>.mp4 -vf "fps=1/10,scale=480:270,tile=4x3" sheet%02d.png`
   gives contact sheets of the whole video. Check them against the self-check below.
7. Output is `output/<slug>.mp4`. Report the path, duration and what the motion report said.

## Self-check

1. Same number of `narrate()` blocks as script paragraphs, in the same order?
2. Is the motion report clean: no paragraph with more than ten seconds of stillness, no empty
   screen?
3. Are reveals tied to sentences with `n.until`, not guessed fractions?
4. Does the mechanism section have an anchor diagram that persists and gets touched by each
   paragraph, and does at least one paragraph show data moving through it?
5. Is there any screen that is only text? Any label longer than a few words? Any text below
   `BODY` size other than ticks and the corner label?
6. Does every downside in the conclusion have its own picture?
7. Do charts show the paper's numbers with readable axes, and is every schematic curve labelled?
8. Is the main object in each paragraph at least 8 units wide?
9. Are colours consistent per concept across the whole video?
10. On the contact sheets, does anything overlap, run off the frame, or sit on top of other text?

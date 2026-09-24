"""Video for scripts/deep-portfolio-management.md. One narrate() block per paragraph, in order."""
from p2a.video import *  # noqa: F401,F403

BLUE, YELLOW, RED, GREEN, GREY, WHITE = (PALETTE[k] for k in ("blue", "yellow", "red", "green", "grey", "white"))
COINS = 11


def label(text, size=28, color=WHITE, **kw):
    return Text(text, font_size=size, color=color, **kw)


def box(text, color=BLUE, w=3.0, h=1.0, size=26):
    r = RoundedRectangle(width=w, height=h, corner_radius=0.15, color=color)
    t = label(text, size=size).scale_to_fit_width(min(w - 0.4, label(text, size=size).width))
    return VGroup(r, t.move_to(r))


def weight_bar(weights, width=6.0, height=0.6, colors=None):
    """Horizontal bar split proportionally to weights (a portfolio)."""
    colors = colors or [BLUE, YELLOW, GREEN, RED, GREY] * 3
    parts, x = VGroup(), -width / 2
    for w, c in zip(weights, colors):
        seg = Rectangle(width=width * w, height=height, fill_color=c, fill_opacity=0.85, stroke_width=1, stroke_color=WHITE)
        seg.move_to([x + width * w / 2, 0, 0])
        parts.add(seg)
        x += width * w
    return parts


def price_grid(rows=COINS, cols=12, cell=0.22, color=BLUE):
    g = VGroup(*[Square(cell, stroke_width=0.8, stroke_color=color, fill_opacity=0.15, fill_color=color) for _ in range(rows * cols)])
    return g.arrange_in_grid(rows=rows, cols=cols, buff=0.03)


def pipeline(scale=1.0):
    """Price block + previous weights -> shared evaluators -> softmax -> weights. Used in three places."""
    grid = price_grid(rows=COINS, cols=8)
    grid_label = label("price history", 20, GREY).next_to(grid, DOWN, buff=0.15)
    evals = VGroup(*[RoundedRectangle(width=1.4, height=0.28, corner_radius=0.08, color=BLUE, fill_opacity=0.3, fill_color=BLUE) for _ in range(COINS)])
    evals.arrange(DOWN, buff=0.05).next_to(grid, RIGHT, buff=1.0)
    ev_label = label("identical evaluators", 20, GREY).next_to(evals, DOWN, buff=0.15)
    soft = box("softmax", YELLOW, w=1.6, h=0.8, size=22).next_to(evals, RIGHT, buff=1.0)
    out = weight_bar([0.3, 0.2, 0.15, 0.15, 0.1, 0.1], width=2.4, height=0.5).rotate(-PI / 2).next_to(soft, RIGHT, buff=0.9)
    out_label = label("new weights", 20, GREY).next_to(out, DOWN, buff=0.15)
    thin = dict(buff=0.05, stroke_width=1.5, max_tip_length_to_length_ratio=0.15, color=GREY)
    arrows = VGroup(
        *[Arrow([grid.get_right()[0], ev.get_y(), 0], ev.get_left(), **thin) for ev in evals],
        *[Arrow(ev.get_right(), soft.get_left(), **thin) for ev in evals],
        Arrow(soft.get_right(), out.get_left(), buff=0.1, color=YELLOW),
    )
    prev = weight_bar([0.3, 0.2, 0.15, 0.15, 0.1, 0.1], width=1.8, height=0.35).next_to(evals, UP, buff=0.9)
    prev_label = label("previous weights", 18, GREY).next_to(prev, UP, buff=0.1)
    prev_arrow = Arrow(prev.get_bottom(), evals.get_top(), buff=0.1, color=GREEN)
    g = VGroup(grid, grid_label, arrows, evals, ev_label, soft, out, out_label, prev, prev_label, prev_arrow)
    g.scale(scale).move_to(ORIGIN)
    g.parts = dict(grid=grid, evals=evals, soft=soft, out=out, prev=prev, prev_arrow=prev_arrow, arrows=arrows,
                   labels=VGroup(grid_label, ev_label, out_label, prev_label))
    return g


class Video(PaperScene):
    def construct(self):
        # ---------------- Opening ----------------
        with self.narrate() as n:  # 1
            self.title_card(n)

        # ---------------- The problem ----------------
        with self.narrate() as n:  # 2 pot of money split across assets, re-decided each period
            sec = self.section_title("The problem")
            bar = weight_bar([0.4, 0.25, 0.2, 0.15])
            cap = label("one pot, many assets", 30).next_to(bar, UP, buff=0.6)
            self.play(FadeIn(cap), Create(bar), run_time=2)
            ticks = VGroup(*[Line(UP * 0.15, DOWN * 0.15, color=GREY).shift(RIGHT * x) for x in np.linspace(-3, 3, 7)])
            tl = Line(LEFT * 3.2, RIGHT * 3.2, color=GREY).shift(DOWN * 1.5)
            ticks.shift(DOWN * 1.5)
            tl_label = label("every period: re-allocate, pay fees", 22, GREY).next_to(tl, DOWN, buff=0.3)
            self.play(Create(tl), Create(ticks), FadeIn(tl_label), run_time=1.5)
            for ws in ([0.2, 0.4, 0.25, 0.15], [0.3, 0.2, 0.1, 0.4], [0.5, 0.1, 0.2, 0.2]):
                self.play(Transform(bar, weight_bar(ws)), run_time=1.2)
                self.wait(0.6)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(bar, cap, tl, ticks, tl_label), run_time=0.5)

        with self.narrate() as n:  # 3 existing approaches and their flaws
            a = box("hand-made\nmodel strategies", GREY, w=4, h=1.4, size=24).shift(LEFT * 3.2 + UP * 1)
            b = box("predict prices,\nthen hand-coded rules", GREY, w=4.4, h=1.4, size=24).shift(RIGHT * 3.2 + UP * 1)
            self.play(FadeIn(a), run_time=1)
            self.wait(n.duration * 0.12)
            fa = label("only as good as the model", 22, RED).next_to(a, DOWN, buff=0.4)
            self.play(FadeIn(fa), run_time=0.8)
            self.wait(n.duration * 0.15)
            self.play(FadeIn(b), run_time=1)
            self.wait(n.duration * 0.15)
            fb = VGroup(label("prices are hard to predict", 22, RED), label("rules can't learn about fees", 22, RED)).arrange(DOWN, buff=0.2).next_to(b, DOWN, buff=0.4)
            self.play(FadeIn(fb[0]), run_time=0.8)
            self.wait(n.duration * 0.15)
            self.play(FadeIn(fb[1]), run_time=0.8)
            self.wait(n.remaining - 0.6)
            self.play(FadeOut(a, b, fa, fb), run_time=0.5)

        with self.narrate() as n:  # 4 RL priors: single asset discrete; DQN discrete; actor-critic unstable
            c1 = VGroup(box("buy", GREEN, 1.2, 0.7), box("hold", GREY, 1.2, 0.7), box("sell", RED, 1.2, 0.7)).arrange(RIGHT, buff=0.3)
            c1l = label("prior RL: one asset, three actions", 24, GREY).next_to(c1, UP, buff=0.4)
            g1 = VGroup(c1, c1l).shift(UP * 2)
            self.play(FadeIn(g1), run_time=1)
            self.wait(n.duration * 0.2)
            grid = VGroup(*[Square(0.3, color=GREY, stroke_width=1) for _ in range(30)]).arrange_in_grid(3, 10, buff=0.05)
            gl = label("discretised weights: risky, scales badly", 24, GREY).next_to(grid, UP, buff=0.3)
            g2 = VGroup(grid, gl).shift(DOWN * 0.3)
            self.play(FadeIn(g2), run_time=1)
            self.wait(n.duration * 0.25)
            actor = box("actor", BLUE, 1.6, 0.8)
            critic = box("critic", RED, 1.6, 0.8)
            ac = VGroup(actor, critic).arrange(RIGHT, buff=1.2).shift(DOWN * 2.6)
            acl = label("actor-critic: two networks, unstable", 24, GREY).next_to(ac, DOWN, buff=0.3)
            self.play(FadeIn(ac, acl), run_time=1)
            self.play(Wiggle(ac, scale_value=1.15, rotation_angle=0.03 * TAU), run_time=1.5)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(g1, g2, ac, acl), run_time=0.5)

        with self.narrate() as n:  # 5 wants: four ticks
            wants = VGroup(*[label(t, 30) for t in ("continuous weights", "fees inside the objective", "any number of assets", "stable, no critic")]).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
            ticks = VGroup(*[label("✓", 32, GREEN).next_to(w, LEFT, buff=0.4) for w in wants])
            VGroup(wants, ticks).move_to(ORIGIN)
            for w, t in zip(wants, ticks):
                self.play(FadeIn(w, t), run_time=0.6)
                self.wait(max((n.duration - 3) / 4 - 0.6, 0.1))
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(wants, ticks, sec), run_time=0.5)

        # ---------------- The idea ----------------
        with self.narrate() as n:  # 6 the pipeline, built piece by piece
            sec = self.section_title("The idea")
            p = pipeline(0.9)
            k = p.parts
            self.play(FadeIn(k["grid"], k["labels"][0]), run_time=1)
            self.play(FadeIn(k["prev"], k["labels"][3]), run_time=0.8)
            self.wait(n.duration * 0.12)
            self.play(Create(k["arrows"]), FadeIn(k["evals"], k["labels"][1], k["prev_arrow"]), run_time=1.5)
            self.play(FadeIn(k["soft"]), FadeIn(k["out"], k["labels"][2]), run_time=1)
            self.wait(n.duration * 0.15)
            note = label("reward computed exactly from history  →  no critic, no exploration", 22, YELLOW).to_edge(DOWN, buff=0.6)
            self.play(FadeIn(note), run_time=0.8)
            self.wait(n.duration * 0.2)
            hl = VGroup(*[SurroundingRectangle(m, color=c, buff=0.12) for m, c in ((k["evals"], BLUE), (k["prev"], GREEN))])
            self.play(Create(hl), run_time=1)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(p, note, hl, sec), run_time=0.5)

        # ---------------- Where it sits ----------------
        with self.narrate() as n:  # 7 integrated net remembers coin identity -> per-asset evaluators
            sec = self.section_title("Where it sits")
            grid = price_grid(rows=6, cols=8).shift(LEFT * 3.5)
            big = box("one integrated\nnetwork", GREY, 3, 1.4).shift(RIGHT * 1.5)
            arr = Arrow(grid.get_right(), big.get_left(), color=GREY)
            self.play(FadeIn(grid, big), Create(arr), run_time=1.2)
            self.wait(n.duration * 0.2)
            bad = SurroundingRectangle(grid[8 * 2:8 * 3], color=RED, buff=0.02)
            badl = label("bad history → never buys it again", 22, RED).next_to(grid, DOWN, buff=0.4)
            self.play(Create(bad), FadeIn(badl), run_time=1)
            self.wait(n.duration * 0.3)
            evals = VGroup(*[RoundedRectangle(width=2.2, height=0.32, corner_radius=0.08, color=BLUE, fill_opacity=0.3, fill_color=BLUE) for _ in range(6)]).arrange(DOWN, buff=0.08).move_to(big)
            el = label("asset-agnostic evaluators", 22, BLUE).next_to(evals, DOWN, buff=0.3)
            self.play(ReplacementTransform(big, evals), FadeOut(bad, badl), FadeIn(el), run_time=1.5)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(grid, evals, el, arr), run_time=0.5)

        with self.narrate() as n:  # 8 Moody & Saffell recurrent memory vs portfolio memory
            chain = VGroup(*[Square(0.6, color=GREY) for _ in range(6)]).arrange(RIGHT, buff=0.8).shift(UP * 1.2)
            arrs = VGroup(*[Arrow(chain[i].get_right(), chain[i + 1].get_left(), buff=0.05, color=GREY) for i in range(5)])
            cl = label("recurrent memory: sequential, gradients vanish", 24, GREY).next_to(chain, UP, buff=0.4)
            self.play(FadeIn(chain, cl), Create(arrs), run_time=1.2)
            back = VGroup(*[Arrow(chain[i + 1].get_bottom() + DOWN * 0.1, chain[i].get_bottom() + DOWN * 0.1, color=RED, stroke_width=4 * (0.55 ** (5 - i)), max_tip_length_to_length_ratio=0.12) for i in range(5)])
            self.play(Create(back), run_time=1.5)
            self.wait(n.duration * 0.25)
            stack = VGroup(*[Rectangle(width=0.5, height=1.2, color=GREEN, fill_opacity=0.25, fill_color=GREEN) for _ in range(10)]).arrange(RIGHT, buff=0.08).shift(DOWN * 1.5)
            sl = label("portfolio memory: a stack, read and overwrite, batches in parallel", 24, GREEN).next_to(stack, DOWN, buff=0.4)
            self.play(FadeIn(stack, sl), run_time=1.2)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(chain, arrs, cl, back, stack, sl), run_time=0.5)

        with self.narrate() as n:  # 9 head to head vs a dozen classical strategies
            names = ["Anticor", "OLMAR", "PAMR", "CWMR", "RMR", "ONS", "UP", "EG", "CORN", "M0", "WMAMR", "BK"]
            small = VGroup(*[box(t, GREY, 1.7, 0.6, 20) for t in names]).arrange_in_grid(3, 4, buff=0.2).shift(LEFT * 2.5)
            ours = box("EIIE", BLUE, 2.2, 1.2, 30).shift(RIGHT * 4)
            vs = label("same data, same fees", 22, YELLOW).next_to(ours, DOWN, buff=0.4)
            self.play(LaggedStart(*[FadeIn(b) for b in small], lag_ratio=0.1), run_time=2)
            self.play(FadeIn(ours, vs), run_time=1)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(small, ours, vs, sec), run_time=0.5)

        # ---------------- How it works ----------------
        with self.narrate() as n:  # 10 setup: 30-min periods, 12 slots
            sec = self.section_title("How it works")
            tl = NumberLine(x_range=[0, 8, 1], length=9, color=GREY, include_ticks=True).shift(UP * 1.5)
            tll = label("30-minute periods", 24, GREY).next_to(tl, UP, buff=0.3)
            self.play(Create(tl), FadeIn(tll), run_time=1.2)
            coins = VGroup(Circle(0.3, color=YELLOW, fill_opacity=0.5, fill_color=YELLOW), *[Circle(0.3, color=BLUE, fill_opacity=0.3, fill_color=BLUE) for _ in range(COINS)]).arrange(RIGHT, buff=0.25).shift(DOWN * 0.8)
            btc = label("BTC = cash", 20, YELLOW).next_to(coins[0], DOWN, buff=0.25)
            cl = label("11 most-traded coins, ranked before the test", 22, GREY).next_to(coins, DOWN, buff=0.7)
            self.play(LaggedStart(*[GrowFromCenter(c) for c in coins], lag_ratio=0.08), run_time=1.5)
            self.play(FadeIn(btc, cl), run_time=0.8)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(tl, tll, coins, btc, cl), run_time=0.5)

        with self.narrate() as n:  # 11 price tensor 11 x 50 x 3, normalised by last close, flat fill
            layers = VGroup(*[price_grid(rows=COINS, cols=14, color=c) for c in (GREEN, YELLOW, BLUE)])
            for i, l in enumerate(layers):
                l.shift(RIGHT * 0.25 * i + UP * 0.25 * i)
            layers.move_to(LEFT * 2)
            names = VGroup(*[label(t, 20, c) for t, c in (("low", GREEN), ("high", YELLOW), ("close", BLUE))]).arrange(DOWN, aligned_edge=LEFT, buff=0.15).next_to(layers, RIGHT, buff=0.8)
            rows = label("11 coins", 22, GREY).next_to(layers, LEFT, buff=0.3)
            cols = label("last 50 periods, about a day", 22, GREY).next_to(layers, DOWN, buff=0.5)
            self.play(FadeIn(layers[2], rows, cols), run_time=1)
            self.play(FadeIn(layers[1], layers[0], names), run_time=1)
            self.wait(n.duration * 0.25)
            last = VGroup(*[layers[2][r * 14 + 13] for r in range(COINS)])
            norm = label("÷ latest close  →  last column = 1", 22, WHITE).next_to(cols, DOWN, buff=0.35)
            self.play(Indicate(last, color=WHITE, scale_factor=1.1), FadeIn(norm), run_time=1.5)
            self.wait(n.duration * 0.25)
            flat = label("missing history: flat fake prices", 22, GREY).next_to(norm, DOWN, buff=0.4)
            self.play(FadeIn(flat), run_time=0.8)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(layers, names, rows, cols, norm, flat), run_time=0.5)

        with self.narrate() as n:  # 12 EIIE: rows independent, shared weights, softmax
            p = pipeline(0.9)
            k = p.parts
            self.play(FadeIn(k["grid"], k["labels"][0]), run_time=0.8)
            self.wait(n.duration * 0.1)
            self.play(Create(k["arrows"][:COINS]), FadeIn(k["evals"], k["labels"][1]), run_time=1.5)
            self.wait(n.duration * 0.1)
            x0, x1 = k["grid"].get_left()[0], k["evals"].get_right()[0]
            walls = VGroup(*[DashedLine([x0, y, 0], [x1, y, 0], color=RED, stroke_width=1.2, dash_length=0.08)
                             for y in [(k["evals"][i].get_bottom()[1] + k["evals"][i + 1].get_top()[1]) / 2 for i in range(COINS - 1)]])
            wl = label("nothing crosses rows until the end", 22, RED).to_edge(DOWN, buff=0.6)
            self.play(Create(walls), FadeIn(wl), run_time=1.2)
            self.wait(n.duration * 0.15)
            shared = label("shared weights", 22, BLUE).next_to(k["evals"], UP, buff=0.3)
            self.play(LaggedStart(*[Indicate(e, color=WHITE, scale_factor=1.05) for e in k["evals"]], lag_ratio=0.05), FadeIn(shared), run_time=1.5)
            self.wait(n.duration * 0.15)
            self.play(Create(k["arrows"][COINS:]), FadeIn(k["soft"], k["out"], k["labels"][2]), FadeOut(walls, wl), run_time=1.5)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(p, shared), run_time=0.5)

        with self.narrate() as n:  # 13 three evaluator types, previous weights injected before scoring
            row = price_grid(rows=1, cols=14, cell=0.3).shift(UP * 2.3)
            rl = label("one coin's history", 20, GREY).next_to(row, LEFT, buff=0.3)
            self.play(FadeIn(row, rl), run_time=0.8)
            kern = SurroundingRectangle(row[0:3], color=YELLOW, buff=0.03)
            kl = label("CNN: kernel height 1, slides along time", 22, YELLOW).next_to(row, DOWN, buff=0.35)
            self.play(Create(kern), FadeIn(kl), run_time=0.8)
            self.play(kern.animate.move_to(row[11:14]), run_time=1.5, rate_func=linear)
            self.wait(n.duration * 0.12)
            cells = VGroup(*[Square(0.45, color=GREEN) for _ in range(6)]).arrange(RIGHT, buff=0.5).shift(DOWN * 0.2)
            carr = VGroup(*[Arrow(cells[i].get_right(), cells[i + 1].get_left(), buff=0.03, color=GREEN, max_tip_length_to_length_ratio=0.2) for i in range(5)])
            cl = label("RNN / LSTM: a small recurrent net over the same history", 22, GREEN).next_to(cells, DOWN, buff=0.35)
            self.play(FadeIn(cells, cl), Create(carr), run_time=1.2)
            self.wait(n.duration * 0.2)
            score = box("score", BLUE, 1.6, 0.7, 22).shift(DOWN * 2.6 + LEFT * 1.5)
            prev = weight_bar([0.3, 0.2, 0.15, 0.15, 0.1, 0.1], width=1.6, height=0.35).shift(DOWN * 2.6 + RIGHT * 2.2)
            pa = Arrow(prev.get_left(), score.get_right(), buff=0.1, color=GREEN)
            pl = label("previous weights join just before scoring", 20, GREY).next_to(VGroup(score, prev), DOWN, buff=0.25)
            self.play(FadeIn(score, prev, pl), Create(pa), run_time=1)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(row, rl, kern, kl, cells, carr, cl, score, prev, pa, pl), run_time=0.5)

        with self.narrate() as n:  # 14 three consequences
            items = VGroup(*[label(t, 28) for t in ("training time grows linearly with coins", "every window is used 11 times", "swap coins in and out without retraining")]).arrange(DOWN, aligned_edge=LEFT, buff=0.7).shift(RIGHT * 0.5)
            icons = VGroup(
                VGroup(*[Rectangle(width=0.18, height=0.2 + 0.12 * i, color=BLUE, fill_opacity=0.5, fill_color=BLUE) for i in range(6)]).arrange(RIGHT, buff=0.06, aligned_edge=DOWN),
                label("×11", 30, YELLOW),
                VGroup(Circle(0.2, color=BLUE, fill_opacity=0.3, fill_color=BLUE), Circle(0.2, color=RED, fill_opacity=0.3, fill_color=RED)).arrange(RIGHT, buff=0.1),
            )
            for ic, it in zip(icons, items):
                ic.next_to(it, LEFT, buff=0.6)
            VGroup(items, icons).move_to(ORIGIN)
            for ic, it in zip(icons, items):
                self.play(FadeIn(ic, it), run_time=0.7)
                self.wait(max((n.duration - 2.7) / 3 - 0.7, 0.1))
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(items, icons), run_time=0.5)

        with self.narrate() as n:  # 15 transaction cost: shrink factor, fixed-point iteration
            before = weight_bar([0.4, 0.3, 0.3], width=5).shift(UP * 1.8 + LEFT * 3)
            after = weight_bar([0.2, 0.5, 0.3], width=5 * 0.92).shift(UP * 1.8 + RIGHT * 3.3)
            arr = Arrow(before.get_right(), after.get_left(), color=YELLOW)
            al = label("rebalance: ×μ, 0.25% per trade", 22, YELLOW).next_to(arr, UP, buff=0.2)
            self.play(FadeIn(before), run_time=0.6)
            self.play(Create(arr), FadeIn(al, after), run_time=1.2)
            self.wait(n.duration * 0.2)
            line = NumberLine(x_range=[0, 1, 0.25], length=8, include_numbers=True, color=GREY, font_size=20).shift(DOWN * 0.8)
            ll = label("μ depends on itself  →  iterate, converges from any start", 22, GREY).next_to(line, DOWN, buff=0.6)
            self.play(Create(line), FadeIn(ll), run_time=1)
            target = 0.92
            dot = Dot(line.n2p(0.5), color=YELLOW)
            self.play(FadeIn(dot), run_time=0.3)
            x = 0.5
            for _ in range(5):
                x = x + (target - x) * 0.6
                self.play(dot.animate.move_to(line.n2p(x)), run_time=0.5)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(before, after, arr, al, line, ll, dot), run_time=0.5)

        with self.narrate() as n:  # 16 state, action, reward
            s = box("state:\nprice block + previous weights", GREY, 5.4, 1.3, 24).shift(UP * 2)
            a = box("action:\nnew weights", BLUE, 5.4, 1.3, 24)
            r = box("reward:\nlog growth after fees", YELLOW, 5.4, 1.3, 24).shift(DOWN * 2)
            for m, frac in ((s, 0.25), (a, 0.2), (r, 0.2)):
                self.play(FadeIn(m), run_time=0.7)
                self.wait(n.duration * frac)
            avg = label("objective = average log return over the window", 22, WHITE).next_to(r, RIGHT, buff=0.6).scale_to_fit_width(5)
            self.play(FadeIn(avg), run_time=0.7)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(s, a, r, avg), run_time=0.5)

        with self.narrate() as n:  # 17 full exploitation: prices don't react, gradient ascent on reward
            ax = Axes(x_range=[0, 10, 1], y_range=[0, 4, 1], x_length=7, y_length=3, axis_config={"color": GREY, "include_ticks": False}).shift(UP * 0.8)
            xs = np.linspace(0, 10, 60)
            ys = 2 + 0.8 * np.sin(xs) + 0.15 * xs + 0.3 * np.sin(3.1 * xs)
            price = ax.plot_line_graph(xs, ys, add_vertex_dots=False, line_color=BLUE)
            pl = label("prices: fixed history, unaffected by the agent", 22, BLUE).next_to(ax, UP, buff=0.2)
            self.play(Create(ax), Create(price), FadeIn(pl), run_time=1.5)
            self.wait(n.duration * 0.2)
            acts = VGroup(*[weight_bar([0.5, 0.3, 0.2], width=1.2, height=0.25).move_to(ax.c2p(2 + 2 * i, 0.4)) for i in range(4)])
            al = label("any allocation can be scored exactly on the same slice", 22, YELLOW).next_to(ax, DOWN, buff=0.3)
            self.play(LaggedStart(*[FadeIn(a) for a in acts], lag_ratio=0.2), FadeIn(al), run_time=1.5)
            self.wait(n.duration * 0.2)
            conc = VGroup(label("no critic", 26, GREEN), label("no exploration", 26, GREEN), label("plain gradient ascent on reward", 26, GREEN)).arrange(RIGHT, buff=0.8).to_edge(DOWN, buff=0.7)
            self.play(LaggedStart(*[FadeIn(c) for c in conc], lag_ratio=0.3), run_time=1.5)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(ax, price, pl, acts, al, conc), run_time=0.5)

        with self.narrate() as n:  # 18 portfolio vector memory: read before window, overwrite window
            cells = VGroup(*[Rectangle(width=0.45, height=1.1, color=GREEN, fill_opacity=0.15, fill_color=GREEN) for _ in range(16)]).arrange(RIGHT, buff=0.06)
            ml = label("portfolio vector memory: one allocation per period", 24, GREEN).next_to(cells, UP, buff=0.5)
            self.play(FadeIn(cells, ml), run_time=1)
            self.wait(n.duration * 0.15)
            win = SurroundingRectangle(cells[6:11], color=BLUE, buff=0.05)
            wl = label("training window", 20, BLUE).next_to(win, DOWN, buff=0.2)
            read = cells[5].copy().set_fill(RED, 0.7)
            rl = label("read", 20, RED).next_to(read, UP, buff=0.2)
            self.play(Create(win), FadeIn(wl), run_time=0.8)
            self.play(FadeIn(read, rl), run_time=0.6)
            self.wait(n.duration * 0.2)
            net = box("network", BLUE, 1.8, 0.7, 22).next_to(win, UP, buff=1.2).shift(RIGHT * 2)
            a1 = Arrow(read.get_top(), net.get_left(), color=RED, buff=0.1)
            self.play(FadeIn(net), Create(a1), run_time=0.8)
            over = VGroup(*[c.copy().set_fill(BLUE, 0.6) for c in cells[6:11]])
            a2 = Arrow(net.get_bottom(), win.get_top(), color=BLUE, buff=0.1)
            ol = label("overwrite", 20, BLUE).next_to(wl, DOWN, buff=0.1)
            self.play(Create(a2), FadeIn(over, ol), run_time=1)
            self.wait(n.duration * 0.15)
            par = label("batches read and write different windows → parallel, no gradient through memory", 20, GREY).to_edge(DOWN, buff=0.6)
            self.play(FadeIn(par), run_time=0.8)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(cells, ml, win, wl, read, rl, net, a1, over, a2, ol, par), run_time=0.5)

        with self.narrate() as n:  # 19 online stochastic batch learning
            tl = NumberLine(x_range=[0, 20, 1], length=11, color=GREY, include_ticks=True).shift(DOWN * 0.5)
            now = label("now", 20, YELLOW).next_to(tl.n2p(20), DOWN, buff=0.2)
            tll = label("training set keeps growing", 24, GREY).to_edge(UP, buff=1.0)
            self.play(Create(tl), FadeIn(now, tll), run_time=1)
            new = Rectangle(width=0.5, height=0.35, color=YELLOW, fill_opacity=0.6, fill_color=YELLOW).move_to(tl.n2p(20.3) + UP * 0.35)
            self.play(GrowFromEdge(new, LEFT), run_time=0.6)
            self.wait(n.duration * 0.15)
            bars = VGroup(*[Rectangle(width=0.4, height=0.15 + 2.0 * (0.85 ** (19 - i)), color=BLUE, fill_opacity=0.4, fill_color=BLUE).move_to(tl.n2p(i + 0.5) + UP * 0.05, aligned_edge=DOWN) for i in range(20)])
            bl = label("start of a batch is sampled with decaying probability: recent data more often", 20, BLUE).next_to(tl, DOWN, buff=0.9)
            self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.03), FadeIn(bl), run_time=1.5)
            self.wait(n.duration * 0.2)
            wins = VGroup(*[SurroundingRectangle(VGroup(*bars[s:s + 4]), color=GREEN, buff=0.03) for s in (15, 11, 16)])
            wl = label("consecutive windows, may overlap", 20, GREEN).next_to(bl, DOWN, buff=0.2)
            self.play(LaggedStart(*[Create(w) for w in wins], lag_ratio=0.3), FadeIn(wl), run_time=1.5)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(tl, now, tll, new, bars, bl, wins, wl, sec), run_time=0.5)

        # ---------------- Experiments ----------------
        with self.narrate() as n:  # 20 three backtests on a timeline
            sec = self.section_title("Experiments")
            tl = NumberLine(x_range=[2014.5, 2017.5, 0.5], length=11, color=GREY, include_numbers=True, decimal_number_config={"num_decimal_places": 0}, numbers_to_include=[2015, 2016, 2017], font_size=22)
            self.play(Create(tl), run_time=1)
            tests = [(2016.68, 2016.83), (2016.94, 2017.08), (2017.18, 2017.32)]
            for i, (a, b) in enumerate(tests):
                train = Rectangle(width=tl.n2p(a)[0] - tl.n2p(2014.6 + 0.2 * i)[0], height=0.3, color=GREY, fill_opacity=0.25, fill_color=GREY).move_to((tl.n2p(2014.6 + 0.2 * i) + tl.n2p(a)) / 2 + UP * (1.2 - 0.5 * i))
                test = Rectangle(width=tl.n2p(b)[0] - tl.n2p(a)[0], height=0.3, color=BLUE, fill_opacity=0.7, fill_color=BLUE).move_to((tl.n2p(a) + tl.n2p(b)) / 2 + UP * (1.2 - 0.5 * i))
                tlab = label(f"test {i + 1}", 18, BLUE).next_to(test, RIGHT, buff=0.15)
                self.play(FadeIn(train, test, tlab), run_time=0.7)
                self.wait(n.duration * 0.12)
            leg = VGroup(label("training, about 2 years of 30-minute data", 20, GREY), label("back-test, about 50 days", 20, BLUE)).arrange(DOWN, aligned_edge=LEFT, buff=0.15).to_edge(DOWN, buff=0.7)
            self.play(FadeIn(leg), run_time=0.7)
            self.wait(max(n.remaining - 0.6, 0))
            self.clear_all()
            sec = self.section_title("Experiments", run_time=0.1)

        with self.narrate() as n:  # 21 baselines
            ours = VGroup(*[box(t, BLUE, 2.0, 0.7, 24) for t in ("CNN", "basic RNN", "LSTM")]).arrange(RIGHT, buff=0.3).shift(UP * 2.2)
            ol = label("three ensemble networks", 20, BLUE).next_to(ours, UP, buff=0.2)
            self.play(FadeIn(ours, ol), run_time=0.8)
            self.wait(n.duration * 0.1)
            prev = box("earlier integrated CNN", GREY, 4, 0.7, 22).shift(UP * 0.8)
            bench = VGroup(*[box(t, YELLOW, 2.6, 0.6, 20) for t in ("best stock (hindsight)", "uniform buy & hold", "constant rebalance")]).arrange(RIGHT, buff=0.25).shift(DOWN * 0.4)
            self.play(FadeIn(prev), run_time=0.6)
            self.wait(n.duration * 0.1)
            self.play(FadeIn(bench), run_time=0.8)
            self.wait(n.duration * 0.15)
            classic = VGroup(*[box(t, GREY, 1.5, 0.5, 18) for t in ("Anticor", "OLMAR", "PAMR", "RMR", "ONS", "UP", "EG", "CORN", "CWMR", "M0", "WMAMR", "BK")]).arrange_in_grid(2, 6, buff=0.15).shift(DOWN * 1.9)
            cl = label("a dozen classical strategies, same frequency and fees", 20, GREY).next_to(classic, DOWN, buff=0.2)
            self.play(LaggedStart(*[FadeIn(b) for b in classic], lag_ratio=0.05), FadeIn(cl), run_time=1.5)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(ours, ol, prev, bench, classic, cl), run_time=0.5)

        with self.narrate() as n:  # 22 metrics
            m = VGroup(*[label(t, 30) for t in ("final value ÷ starting value", "Sharpe ratio", "maximum drawdown")]).arrange(DOWN, buff=0.6)
            self.play(LaggedStart(*[FadeIn(x) for x in m], lag_ratio=0.4), run_time=2)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(m), run_time=0.5)

        with self.narrate() as n:  # 23 not tested
            head = label("not tested", 34, RED).shift(UP * 2.8)
            items = VGroup(*[label(t, 26, GREY) for t in ("other markets: stocks, futures, FX", "live trading", "slippage or market impact", "other periods or portfolio sizes", "variance across seeds", "any actor-critic baseline")]).arrange(DOWN, aligned_edge=LEFT, buff=0.35).shift(DOWN * 0.3)
            self.play(FadeIn(head), run_time=0.6)
            for it in items:
                self.play(FadeIn(it), run_time=0.5)
                self.wait(max((n.duration - 4) / 6 - 0.5, 0.1))
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(head, items, sec), run_time=0.5)

        # ---------------- Results ----------------
        with self.narrate() as n:  # 24 headline numbers: bar chart per test
            sec = self.section_title("Results")
            data = {"CNN": (29.7, 8.0, 31.7), "RNN": (13.3, 4.6, 47.1), "LSTM": (6.7, 4.1, 21.2), "best stock": (1.2, 1.4, 4.6)}
            colors = [BLUE, GREEN, YELLOW, GREY]
            charts = VGroup()
            for t in range(3):
                ch = BarChart(values=[np.log10(v[t]) for v in data.values()], y_range=[0, 2, 1], y_length=2.6, x_length=3.2, bar_colors=colors, bar_names=None, y_axis_config={"include_numbers": False, "include_ticks": False})
                nums = VGroup(*[label(f"{v[t]:.0f}×", 18, c).next_to(bar, UP, buff=0.08) for v, bar, c in zip(data.values(), ch.bars, colors)])
                title = label(f"test {t + 1}", 22, GREY).next_to(ch, DOWN, buff=0.2)
                charts.add(VGroup(ch, nums, title))
            charts.arrange(RIGHT, buff=0.8).shift(UP * 0.2)
            leg = VGroup(*[VGroup(Square(0.25, color=c, fill_opacity=0.8, fill_color=c), label(k, 20, GREY)).arrange(RIGHT, buff=0.15) for k, c in zip(data, colors)]).arrange(RIGHT, buff=0.6).to_edge(DOWN, buff=0.6)
            self.play(FadeIn(leg), run_time=0.6)
            for c in charts:
                self.play(FadeIn(c), run_time=1.2)
                self.wait(n.duration * 0.2)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(charts, leg), run_time=0.5)

        with self.narrate() as n:  # 25 top three on value and Sharpe, but not drawdown
            podium = VGroup(*[box(t, BLUE, 2.4, 0.8, 24) for t in ("1  CNN / RNN", "2  RNN / CNN", "3  LSTM")]).arrange(DOWN, buff=0.2).shift(LEFT * 3.2)
            pl = label("final value and Sharpe: all three tests", 22, BLUE).next_to(podium, UP, buff=0.3)
            self.play(FadeIn(podium, pl), run_time=1)
            self.wait(n.duration * 0.3)
            ax = Axes(x_range=[0, 10, 1], y_range=[0, 3, 1], x_length=4.5, y_length=2.6, axis_config={"color": GREY, "include_ticks": False}).shift(RIGHT * 3.2)
            xs = np.linspace(0, 10, 80)
            ys = 1 + 0.2 * xs - 0.9 * np.exp(-((xs - 6) ** 2) / 0.6)
            curve = ax.plot_line_graph(xs, ys, add_vertex_dots=False, line_color=RED)
            dl = label("max drawdown 20% to 50%", 22, RED).next_to(ax, UP, buff=0.2)
            self.play(Create(ax), Create(curve), FadeIn(dl), run_time=1.5)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(podium, pl, ax, curve, dl, sec), run_time=0.5)

        # ---------------- Conclusion and downsides ----------------
        with self.narrate() as n:  # 26 what holds up
            sec = self.section_title("Conclusion")
            good = VGroup(*[box(t, GREEN, 4.2, 0.9, 22) for t in ("asset-agnostic shared evaluators", "previous weights fed back in", "exact transaction-cost iteration", "no critic on fixed history")]).arrange_in_grid(2, 2, buff=0.4)
            self.play(LaggedStart(*[FadeIn(g) for g in good], lag_ratio=0.3), run_time=2.5)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(good), run_time=0.5)

        caveats = VGroup()

        def add_caveat(text):
            item = label(text, 26).set_color(WHITE)
            if caveats:
                caveats.set_color(GREY)
                item.next_to(caveats, DOWN, aligned_edge=LEFT, buff=0.4)
            else:
                item.move_to(UP * 2.2 + LEFT * 0.5)
            caveats.add(item)
            self.play(FadeIn(item), run_time=0.7)

        with self.narrate() as n:  # 27 "be careful"
            warn = label("the empirical claims need care", 34, YELLOW)
            self.play(FadeIn(warn), run_time=0.8)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(warn), run_time=0.5)

        with self.narrate() as n:  # 28
            add_caveat("1  zero slippage, zero market impact, in thin altcoin markets")
        with self.narrate() as n:  # 29
            add_caveat("2  all three windows inside the 2016–17 crypto boom")
        with self.narrate() as n:  # 30
            add_caveat("3  three windows, one run each, no ablation")
        with self.narrate() as n:  # 31
            add_caveat("4  myopic objective: no planning beyond one period")
        with self.narrate() as n:  # 32
            add_caveat("5  drawdowns of 20 to 50 percent in fifty days")
        with self.narrate() as n:  # 33 reproductions
            add_caveat("6  practitioner reimplementations did not reproduce these returns")
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(caveats), run_time=0.5)

        with self.narrate() as n:  # 34 open problems
            centre = box("EIIE", BLUE, 2.0, 0.9, 28)
            outs = VGroup(*[box(t, GREY, 3.4, 0.9, 20) for t in ("learn market impact\nfrom live records", "other markets", "longer horizon\nwithout instability")])
            outs[0].shift(LEFT * 4.5 + DOWN * 1.8)
            outs[1].shift(DOWN * 2.2)
            outs[2].shift(RIGHT * 4.5 + DOWN * 1.8)
            arrows = VGroup(*[Arrow(centre.get_bottom(), o.get_top(), color=GREY, buff=0.1) for o in outs])
            self.play(FadeIn(centre), run_time=0.6)
            self.play(LaggedStart(*[AnimationGroup(Create(a), FadeIn(o)) for a, o in zip(arrows, outs)], lag_ratio=0.4), run_time=2)
            self.wait(max(n.remaining - 0.6, 0))
            self.play(FadeOut(centre, outs, arrows, sec), run_time=0.5)

        # ---------------- Recap ----------------
        with self.narrate() as n:  # 35 five rows plus the small pipeline
            sec = self.section_title("Recap")
            rows = [("problem", "allocate across many assets from prices, with fees, no critic"),
                    ("approach", "policy outputs weights; gradient ascent on realised log return"),
                    ("mechanism", "shared per-asset evaluators + softmax, weight memory, online batches"),
                    ("performance", "4× to 47× in three 50-day crypto back-tests"),
                    ("downside", "zero slippage, one booming market, one run per window")]
            table = VGroup(*[VGroup(label(k, 24, YELLOW), label(v, 22)).arrange(RIGHT, buff=0.5, aligned_edge=UP) for k, v in rows])
            table.arrange(DOWN, aligned_edge=LEFT, buff=0.45).to_edge(LEFT, buff=0.8).shift(UP * 0.3)
            for r in table:
                r[1].scale_to_fit_width(min(r[1].width, 9.5))
            p = pipeline(0.42).to_corner(DR, buff=0.5)
            self.play(FadeIn(p), run_time=1)
            for r in table:
                self.play(FadeIn(r), run_time=0.8)
                self.wait(max((n.duration - 8) / 5 - 0.8, 0.2))
            self.wait(max(n.remaining - 1.0, 0))
            self.play(FadeOut(table, p, sec), run_time=1.0)

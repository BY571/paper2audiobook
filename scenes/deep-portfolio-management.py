"""Video for scripts/deep-portfolio-management.md. One narrate() block per paragraph, in order.

Colour code, used everywhere: blue = the policy network and its evaluators, green = the portfolio
memory / previous weights, yellow = softmax and money / weights, red = fees, flaws and caveats,
grey = other people's methods and data.
"""
from p2a.video import *  # noqa: F401,F403

BLUE, YELLOW, RED, GREEN, GREY, WHITE = (PALETTE[k] for k in ("blue", "yellow", "red", "green", "grey", "white"))
PURPLE = "#9B7BDB"
COINS = 11
SEG_COLORS = [BLUE, YELLOW, GREEN, RED, GREY, PURPLE] * 3

# Real numbers from Table 2 of the paper (final value as a multiple of the start; max drawdown %).
FAPV = {"CNN": (29.7, 8.0, 31.7), "RNN": (13.3, 4.6, 47.1), "LSTM": (6.7, 4.1, 21.2),
        "best coin": (1.22, 1.40, 4.59), "RMR": (0.127, 0.090, 7.01)}
MDD = {"CNN": (22, 22, 41), "RNN": (24, 26, 39), "LSTM": (28, 32, 49), "rebalance": (27, 19, 16)}
COL = {"CNN": BLUE, "RNN": GREEN, "LSTM": YELLOW, "best coin": GREY, "RMR": PURPLE, "rebalance": GREY}


# ----------------------------------------------------------------------------- building blocks

def pill(text, color=GREY, size=BODY, pad=0.35):
    t = label(text, size)
    r = RoundedRectangle(width=t.width + 2 * pad, height=t.height + 2 * pad, corner_radius=0.2, color=color)
    return VGroup(r, t.move_to(r))


def weight_bar(weights, width=8.0, height=0.8, vertical=False):
    parts, x = VGroup(), -width / 2
    for w, c in zip(weights, SEG_COLORS):
        seg = Rectangle(width=width * w, height=height, fill_color=c, fill_opacity=0.85, stroke_width=1, stroke_color=WHITE)
        seg.move_to([x + width * w / 2, 0, 0])
        parts.add(seg)
        x += width * w
    if vertical:
        parts.rotate(-PI / 2)
    return parts


def price_grid(rows=COINS, cols=10, cell=0.3, color=BLUE):
    g = VGroup(*[Square(cell, stroke_width=0.8, stroke_color=color, fill_opacity=0.18, fill_color=color) for _ in range(rows * cols)])
    return g.arrange_in_grid(rows=rows, cols=cols, buff=0.04)


def sparkline(points, width=3.0, height=1.2, color=BLUE):
    pts = np.array(points, dtype=float)
    pts = (pts - pts.min()) / max(pts.max() - pts.min(), 1e-6)
    xs = np.linspace(-width / 2, width / 2, len(pts))
    return VMobject(color=color, stroke_width=3).set_points_as_corners([[x, (p - 0.5) * height, 0] for x, p in zip(xs, pts)])


def coin(color=BLUE, r=0.32, text=None):
    c = Circle(r, color=color, fill_opacity=0.35, fill_color=color)
    return VGroup(c, label(text, SMALL, color).move_to(c)) if text else c


def cross(mobj, color=RED):
    return Cross(mobj, stroke_color=color, stroke_width=5, scale_factor=1.1)


def pipeline(scale=1.0, evaluators=True):
    """The anchor diagram: price block + previous weights -> evaluators -> softmax -> new weights."""
    grid = price_grid(rows=COINS, cols=8, cell=0.32)
    grid_l = label("price history", SMALL, GREY).next_to(grid, DOWN, buff=0.2)
    if evaluators:
        net = VGroup(*[RoundedRectangle(width=2.2, height=0.36, corner_radius=0.1, color=BLUE, fill_opacity=0.35, fill_color=BLUE) for _ in range(COINS)])
        net.arrange(DOWN, buff=0.06)
        net_l = label("identical evaluators", SMALL, GREY)
    else:
        net = VGroup(RoundedRectangle(width=2.6, height=3.2, corner_radius=0.2, color=BLUE, fill_opacity=0.25, fill_color=BLUE))
        net_l = label("policy network", SMALL, GREY)
    net.next_to(grid, RIGHT, buff=1.4)
    net_l.next_to(net, DOWN, buff=0.2)
    soft = pill("softmax", YELLOW, SMALL).next_to(net, RIGHT, buff=1.3)
    out = weight_bar([0.3, 0.2, 0.15, 0.15, 0.1, 0.1], width=3.6, height=0.7, vertical=True).next_to(soft, RIGHT, buff=1.2)
    out_l = label("new weights", SMALL, GREY).next_to(out, DOWN, buff=0.2)
    thin = dict(buff=0.06, stroke_width=1.6, max_tip_length_to_length_ratio=0.12, color=GREY)
    if evaluators:
        a_in = VGroup(*[Arrow([grid.get_right()[0], m.get_y(), 0], m.get_left(), **thin) for m in net])
        a_mid = VGroup(*[Arrow(m.get_right(), soft.get_left(), **thin) for m in net])
    else:
        a_in = VGroup(Arrow(grid.get_right(), net.get_left(), buff=0.1, color=GREY))
        a_mid = VGroup(Arrow(net.get_right(), soft.get_left(), buff=0.1, color=GREY))
    a_out = Arrow(soft.get_right(), out.get_left(), buff=0.1, color=YELLOW)
    prev = weight_bar([0.3, 0.2, 0.15, 0.15, 0.1, 0.1], width=2.6, height=0.45).next_to(net, UP, buff=1.1)
    prev_l = label("previous weights", SMALL, GREEN).next_to(prev, UP, buff=0.12)
    a_prev = Arrow(prev.get_bottom(), net.get_top(), buff=0.1, color=GREEN)
    g = VGroup(grid, grid_l, a_in, net, net_l, a_mid, soft, a_out, out, out_l, prev, prev_l, a_prev)
    g.scale(scale).move_to(ORIGIN)
    g.parts = dict(grid=grid, grid_l=grid_l, a_in=a_in, net=net, net_l=net_l, a_mid=a_mid, soft=soft, a_out=a_out,
                   out=out, out_l=out_l, prev=prev, prev_l=prev_l, a_prev=a_prev)
    return g


def log_axis(x_left, x_right, y_bottom, height=4.2):
    """A vertical log axis from 0.1x to 100x with readable tick labels. Returns (group, y_of)."""

    def y_of(v):
        return y_bottom + height * (np.log10(v) + 1) / 3

    axis = Line([x_left, y_bottom, 0], [x_left, y_bottom + height, 0], color=GREY)
    ticks = VGroup()
    for v, t in ((0.1, "0.1×"), (1, "1×"), (10, "10×"), (100, "100×")):
        y = y_of(v)
        ticks.add(DashedLine([x_left, y, 0], [x_right, y, 0], color=GREY, stroke_width=1, dash_length=0.1, stroke_opacity=0.5),
                  label(t, SMALL, GREY).next_to([x_left, y, 0], LEFT, buff=0.15))
    return VGroup(axis, ticks), y_of


def rect(w, h, color, opacity=0.8):
    return Rectangle(width=w, height=h, color=color, fill_opacity=opacity, fill_color=color, stroke_width=1)


class Video(PaperScene):
    def hold(self, n, fade=0.0):
        self.wait(max(n.remaining - fade, 0))

    def fade_all_but(self, keep=(), run_time=0.5):
        keep_ids = set()
        for m in keep:
            keep_ids.add(id(m))
            keep_ids.update(id(s) for s in m.get_family())
        gone = [m for m in self.mobjects if id(m) not in keep_ids]
        if gone:
            self.play(*[FadeOut(m) for m in gone], run_time=run_time)

    def construct(self):
        # ================================================================== 1 Opening
        with self.narrate() as n:
            title = Text("A Deep Reinforcement Learning Framework\nfor the Financial Portfolio Management Problem", font_size=TITLE, line_spacing=0.9).scale_to_fit_width(12.5)
            authors = label("Zhengyao Jiang · Dixing Xu · Jinjun Liang", BODY, GREY)
            head = VGroup(title, authors).arrange(DOWN, buff=0.5).shift(UP * 1.7)
            self.play(Write(title), run_time=2.2)
            n.until("by Zhengyao")
            self.play(FadeIn(authors), run_time=0.8)
            tags = VGroup(pill("methods paper", GREY), pill("preprint, 2017", GREY)).arrange(RIGHT, buff=0.5).next_to(head, DOWN, buff=0.9)
            n.until("methods paper")
            self.play(FadeIn(tags[0]), run_time=0.5)
            self.play(FadeIn(tags[1]), run_time=0.5)
            n.until("directly output portfolio weights")
            bar = weight_bar([0.35, 0.25, 0.2, 0.2], width=6, height=0.6).next_to(tags, DOWN, buff=0.7)
            self.play(GrowFromCenter(bar), run_time=0.8)
            n.until("cryptocurrency exchange")
            btc = coin(YELLOW, 0.4, "₿").next_to(bar, RIGHT, buff=0.6)
            self.play(GrowFromCenter(btc), run_time=0.5)
            self.hold(n, 0.5)
            self.clear_all(0.5)

        # ================================================================== 2 The problem
        with self.narrate() as n:
            sec = self.section_title("The problem")
            pot = weight_bar([0.4, 0.25, 0.2, 0.15], width=10, height=1.0).shift(UP * 0.8)
            pot_l = label("one pot of money, split across assets").next_to(pot, UP, buff=0.5)
            self.play(FadeIn(pot_l), GrowFromCenter(pot), run_time=1.2)
            n.until("growing the pot")
            self.play(pot.animate.scale(1.08), run_time=0.6)
            n.until("fixed intervals")
            tl = NumberLine(x_range=[0, 6, 1], length=10, color=GREY).shift(DOWN * 1.4)
            cursor = Triangle(color=YELLOW, fill_opacity=1, fill_color=YELLOW).scale(0.18).rotate(PI).next_to(tl.n2p(0), UP, buff=0.05)
            self.play(Create(tl), FadeIn(cursor), run_time=1.0)
            n.until("recent prices")
            spark = sparkline([1, 1.2, 0.9, 1.4, 1.3, 1.7, 1.5], width=3, height=1, color=GREY).next_to(tl, DOWN, buff=0.6).shift(LEFT * 3.5)
            self.play(Create(spark), run_time=0.8)
            n.until("new allocation")
            self.play(cursor.animate.next_to(tl.n2p(1), UP, buff=0.05), Transform(pot, weight_bar([0.2, 0.4, 0.25, 0.15], width=10.8, height=1.0).shift(UP * 0.8)), run_time=1.0)
            n.until("pays fees")
            fee = pill("fee", RED, SMALL).next_to(spark, RIGHT, buff=3.5)
            self.play(Transform(pot, weight_bar([0.2, 0.4, 0.25, 0.15], width=10.3, height=1.0).shift(UP * 0.8)), FadeIn(fee, shift=UP * 0.3), run_time=0.8)
            k = 2
            while n.remaining > 3.0:
                ws = [[0.3, 0.2, 0.1, 0.4], [0.5, 0.1, 0.2, 0.2], [0.25, 0.25, 0.25, 0.25]][k % 3]
                self.play(cursor.animate.next_to(tl.n2p(min(k, 6)), UP, buff=0.05), Transform(pot, weight_bar(ws, width=10.3 - 0.2 * (k - 1), height=1.0).shift(UP * 0.8)), Indicate(fee, color=RED, scale_factor=1.15), run_time=1.2)
                self.wait(0.8)
                k += 1
            self.hold(n, 0.5)
            self.fade_all_but([sec])

        # ================================================================== 3 existing approaches
        with self.narrate() as n:
            fam = VGroup(pill("follow the winner", GREY), pill("follow the loser", GREY), pill("match patterns", GREY)).arrange(RIGHT, buff=0.5).shift(UP * 2.3)
            hdr = label("existing approaches", BODY, GREY).next_to(fam, UP, buff=0.4)
            self.play(FadeIn(hdr), run_time=0.5)
            n.until("follow the winner")
            self.play(FadeIn(fam[0]), run_time=0.5)
            n.until("follow the loser")
            self.play(FadeIn(fam[1]), run_time=0.5)
            n.until("match patterns")
            self.play(FadeIn(fam[2]), run_time=0.5)
            n.until("hand-made financial models")
            model = pill("hand-made model", GREY).next_to(fam, DOWN, buff=0.5)
            arr1 = VGroup(*[Arrow(f.get_bottom(), model.get_top(), buff=0.08, color=GREY, stroke_width=2) for f in fam])
            self.play(FadeIn(model), Create(arr1), run_time=0.8)
            n.until("as well as the model fits")
            flaw1 = label("only as good as the model", SMALL, RED).next_to(model, DOWN, buff=0.2)
            self.play(FadeIn(flaw1, shift=UP * 0.2), Indicate(model, color=RED), run_time=0.8)
            n.until("deep learning approaches")
            dl = VGroup(pill("predict prices", BLUE), pill("hand-coded rules", GREY), pill("trade", YELLOW)).arrange(RIGHT, buff=1.2).shift(DOWN * 0.7)
            arr2 = VGroup(Arrow(dl[0].get_right(), dl[1].get_left(), buff=0.1, color=GREY), Arrow(dl[1].get_right(), dl[2].get_left(), buff=0.1, color=GREY))
            self.play(FadeIn(dl[0]), run_time=0.5)
            n.until("hand-coded layer")
            self.play(Create(arr2[0]), FadeIn(dl[1]), Create(arr2[1]), FadeIn(dl[2]), run_time=1.0)
            n.until("hard to predict")
            pred = sparkline([1, 1.1, 1.3, 1.5, 1.7], width=2.2, height=0.8, color=BLUE).next_to(dl[0], DOWN, buff=0.4)
            real = sparkline([1, 1.1, 0.8, 0.6, 0.9], width=2.2, height=0.8, color=WHITE).move_to(pred)
            self.play(Create(pred), run_time=0.5)
            self.play(Create(real), run_time=0.6)
            flaw2 = label("prediction ≠ reality", SMALL, RED).next_to(pred, DOWN, buff=0.15)
            self.play(FadeIn(flaw2), run_time=0.4)
            n.until("transaction costs")
            fee = pill("fee", RED, SMALL).next_to(dl[1], DOWN, buff=0.5)
            x = cross(fee)
            flaw3 = label("rules can't learn about fees", SMALL, RED).next_to(fee, DOWN, buff=0.35)
            self.play(FadeIn(fee), Create(x), FadeIn(flaw3), run_time=0.8)
            self.hold(n, 0.5)
            self.fade_all_but([sec])

        # ================================================================== 4 RL priors
        with self.narrate() as n:
            rl = pill("reinforcement learning: actions from reward", BLUE, SMALL).shift(UP * 3.0)
            self.play(FadeIn(rl), run_time=0.6)
            n.until("buy, hold, or sell")
            btns = VGroup(pill("buy", GREEN), pill("hold", GREY), pill("sell", RED)).arrange(RIGHT, buff=0.4).shift(UP * 0.5 + LEFT * 3.5)
            one = coin(BLUE, 0.4).next_to(btns, UP, buff=0.4)
            self.play(FadeIn(one), LaggedStart(*[FadeIn(b) for b in btns], lag_ratio=0.3), run_time=1.0)
            n.until("does not generalise")
            many = VGroup(*[coin(BLUE, 0.25) for _ in range(6)]).arrange(RIGHT, buff=0.15).next_to(btns, DOWN, buff=0.5)
            self.play(FadeIn(many), run_time=0.5)
            self.play(Create(cross(many)), run_time=0.5)
            n.until("Deep Q-learning")
            grid = VGroup(*[Square(0.32, color=GREY, stroke_width=1) for _ in range(9)]).arrange_in_grid(3, 3, buff=0.06).shift(UP * 0.6 + RIGHT * 3.5)
            gl = label("discrete actions", SMALL, GREY).next_to(grid, UP, buff=0.3)
            self.play(FadeIn(grid, gl), run_time=0.6)
            n.until("scales badly")
            big = VGroup(*[Square(0.18, color=GREY, stroke_width=1) for _ in range(64)]).arrange_in_grid(8, 8, buff=0.04).move_to(grid)
            self.play(ReplacementTransform(grid, big), run_time=0.8)
            self.play(Create(cross(big)), run_time=0.4)
            n.until("Actor-critic")
            actor, critic = pill("actor", BLUE), pill("critic", RED)
            ac = VGroup(actor, critic).arrange(RIGHT, buff=1.4).shift(DOWN * 2.2)
            loop = VGroup(Arrow(actor.get_right(), critic.get_left(), buff=0.1, color=GREY).shift(UP * 0.15), Arrow(critic.get_left(), actor.get_right(), buff=0.1, color=GREY).shift(DOWN * 0.15))
            self.play(FadeIn(ac), Create(loop), run_time=0.8)
            n.until("unstable")
            self.play(Wiggle(ac, scale_value=1.15, rotation_angle=0.04 * TAU), run_time=1.5)
            self.hold(n, 0.5)
            self.fade_all_but([sec])

        # ================================================================== 5 what the paper wants
        with self.narrate() as n:
            items = VGroup(label("continuous weights"), label("fees inside the objective"), label("any number of assets"), label("stable, no critic")).arrange(DOWN, aligned_edge=LEFT, buff=0.7).shift(RIGHT * 1.5)
            want = label("what the paper wants", BODY, YELLOW).to_edge(UP, buff=1.0)
            self.play(FadeIn(want), run_time=0.4)
            crit = pill("critic", RED, SMALL, 0.2)
            icons = VGroup(weight_bar([0.4, 0.3, 0.3], width=2.2, height=0.4),
                           pill("fee", RED, SMALL, 0.2),
                           VGroup(*[coin(BLUE, 0.18) for _ in range(7)]).arrange(RIGHT, buff=0.08),
                           VGroup(crit, cross(crit)))
            for ic, it in zip(icons, items):
                ic.next_to(it, LEFT, buff=0.8)
            for phrase, ic, it in zip(("continuous portfolio weights", "transaction cost", "any number of assets", "without a critic"), icons, items):
                n.until(phrase)
                self.play(FadeIn(ic, it, shift=RIGHT * 0.3), run_time=0.6)
            self.hold(n, 0.5)
            self.clear_all(0.5)

        # ================================================================== 6 the idea
        with self.narrate() as n:
            sec = self.section_title("The idea")
            p = pipeline(0.85, evaluators=False).shift(UP * 0.5)
            k = p.parts
            self.play(FadeIn(k["grid"], k["grid_l"]), run_time=0.7)
            n.until("recent price history")
            self.play(Indicate(k["grid"], color=WHITE, scale_factor=1.02), run_time=0.8)
            n.until("current allocation")
            self.play(FadeIn(k["prev"], k["prev_l"]), run_time=0.6)
            n.until("directly outputs")
            self.play(Create(k["a_in"]), FadeIn(k["net"], k["net_l"]), Create(k["a_prev"]), run_time=0.8)
            self.play(Create(k["a_mid"]), FadeIn(k["soft"]), Create(k["a_out"]), FadeIn(k["out"], k["out_l"]), run_time=0.8)
            n.until("computed exactly")
            note = label("reward is exact, from history", BODY, YELLOW).to_edge(DOWN, buff=0.5)
            self.play(FadeIn(note), run_time=0.6)
            n.until("no critic")
            critic = pill("critic", RED, SMALL, 0.2).next_to(note, LEFT, buff=1.0)
            self.play(FadeIn(critic), Create(cross(critic)), run_time=0.6)
            n.until("no exploration")
            expl = pill("explore", RED, SMALL, 0.2).next_to(note, RIGHT, buff=1.0)
            self.play(FadeIn(expl), Create(cross(expl)), run_time=0.6)
            n.until("identical per-asset sub-networks")
            evals = VGroup(*[RoundedRectangle(width=2.2, height=0.36, corner_radius=0.1, color=BLUE, fill_opacity=0.35, fill_color=BLUE) for _ in range(COINS)]).arrange(DOWN, buff=0.06).scale(0.85).move_to(k["net"])
            ev_l = label("identical evaluators", SMALL, GREY).move_to(k["net_l"])
            self.play(ReplacementTransform(k["net"], evals), ReplacementTransform(k["net_l"], ev_l), run_time=1.0)
            n.until("memory of past allocations")
            self.play(Indicate(k["prev"], color=GREEN, scale_factor=1.2), Indicate(k["a_prev"], color=GREEN), run_time=1.0)
            n.until("online mini-batch")
            tl = VGroup(*[Square(0.22, color=GREEN, fill_opacity=0.4, fill_color=GREEN) for _ in range(10)]).arrange(RIGHT, buff=0.06).next_to(k["grid"], UP, buff=0.9)
            tl_l = label("keeps training while trading", SMALL, GREEN).next_to(tl, UP, buff=0.12)
            self.play(LaggedStart(*[GrowFromCenter(s) for s in tl], lag_ratio=0.1), FadeIn(tl_l), run_time=1.0)
            self.hold(n, 0.5)
            self.clear_all(0.5)

        # ================================================================== 7 earlier integrated net
        with self.narrate() as n:
            grid = price_grid(rows=6, cols=10, cell=0.34).shift(LEFT * 3.8)
            sec = Text("Where it sits", font_size=SMALL, color=GREY).to_corner(UL)
            self.play(FadeIn(sec), FadeIn(grid), run_time=0.5)
            names = VGroup(*[label(t, SMALL, GREY) for t in ("ETH", "XMR", "LTC", "DASH", "XRP", "FCT")])
            for nm, row in zip(names, range(6)):
                nm.next_to(grid[row * 10], LEFT, buff=0.25)
            big = pill("one integrated\nnetwork", GREY, BODY, 0.5).shift(RIGHT * 1.5)
            arr = Arrow(grid.get_right(), big.get_left(), buff=0.15, color=GREY)
            out = weight_bar([0.3, 0.2, 0.2, 0.1, 0.1, 0.1], width=3.0, height=0.5, vertical=True).next_to(big, RIGHT, buff=1.2)
            arr2 = Arrow(big.get_right(), out.get_left(), buff=0.1, color=GREY)
            n.until("one integrated")
            self.play(FadeIn(big, out), Create(arr), Create(arr2), run_time=1.0)
            n.until("learns the identity")
            self.play(LaggedStart(*[FadeIn(nm, shift=RIGHT * 0.2) for nm in names], lag_ratio=0.1), run_time=1.0)
            n.until("did badly in the past")
            row = VGroup(*grid[20:30])
            bad = SurroundingRectangle(row, color=RED, buff=0.03)
            fall = sparkline([1.5, 1.3, 1.0, 0.7, 0.5], width=2.2, height=0.8, color=RED).next_to(grid, DOWN, buff=0.5)
            self.play(Create(bad), Create(fall), names[2].animate.set_color(RED), run_time=0.8)
            n.until("refuses to invest")
            zero = label("0", BODY, RED).next_to(out[2], RIGHT, buff=0.2)
            self.play(out[2].animate.set_fill(RED, 0.9), FadeIn(zero), run_time=0.6)
            n.until("clearly rising")
            rise = sparkline([0.5, 0.6, 0.9, 1.3, 1.7], width=2.2, height=0.8, color=GREEN).move_to(fall)
            self.play(ReplacementTransform(fall, rise), run_time=0.8)
            self.play(Indicate(zero, color=RED, scale_factor=1.4), run_time=0.8)
            n.until("asset-agnostic")
            evals = VGroup(*[RoundedRectangle(width=2.4, height=0.36, corner_radius=0.1, color=BLUE, fill_opacity=0.35, fill_color=BLUE) for _ in range(6)]).arrange(DOWN, buff=0.08).move_to(big)
            el = label("asset-agnostic", SMALL, BLUE).next_to(evals, DOWN, buff=0.2)
            self.play(ReplacementTransform(big, evals), FadeOut(names, bad, zero), out[2].animate.set_fill(GREEN, 0.9), FadeIn(el), run_time=1.2)
            self.hold(n, 0.5)
            self.fade_all_but([sec])

        # ================================================================== 8 recurrent memory vs portfolio memory
        with self.narrate() as n:
            chain = VGroup(*[Square(0.7, color=GREY) for _ in range(7)]).arrange(RIGHT, buff=0.7).shift(UP * 1.6)
            fwd = VGroup(*[Arrow(chain[i].get_right(), chain[i + 1].get_left(), buff=0.05, color=GREY) for i in range(6)])
            cl = label("recurrent memory", BODY, GREY).next_to(chain, UP, buff=0.4)
            self.play(FadeIn(chain), Create(fwd), run_time=1.0)
            n.until("recurrent memory")
            self.play(FadeIn(cl), run_time=0.5)
            n.until("vanishing gradients")
            back = VGroup(*[Arrow(chain[i + 1].get_bottom() + DOWN * 0.15, chain[i].get_bottom() + DOWN * 0.15, color=RED, stroke_width=6 * (0.6 ** (5 - i)), max_tip_length_to_length_ratio=0.15) for i in range(6)])
            self.play(LaggedStart(*[Create(a) for a in reversed(back)], lag_ratio=0.15), run_time=1.5)
            n.until("sequential")
            sweep = Square(0.7, color=YELLOW, stroke_width=5).move_to(chain[0])
            self.play(FadeIn(sweep), run_time=0.2)
            for i in range(1, 7):
                self.play(sweep.animate.move_to(chain[i]), run_time=0.25)
            n.until("cannot be parallelised")
            self.play(FadeOut(sweep), Create(cross(chain)), run_time=0.5)
            n.until("portfolio memory")
            stack = VGroup(*[rect(0.55, 1.3, GREEN, 0.25) for _ in range(12)]).arrange(RIGHT, buff=0.08).shift(DOWN * 1.6)
            sl = label("portfolio memory", BODY, GREEN).next_to(stack, DOWN, buff=0.4)
            self.play(FadeIn(stack, sl), run_time=0.8)
            n.until("without those costs")
            reads = VGroup(*[SurroundingRectangle(VGroup(*stack[s:s + 3]), color=BLUE, buff=0.04) for s in (1, 5, 9)])
            par = label("read in parallel", SMALL, BLUE).next_to(stack, UP, buff=0.3)
            self.play(Create(reads), FadeIn(par), run_time=0.8)
            self.hold(n, 0.5)
            self.fade_all_but([sec])

        # ================================================================== 9 baselines and no reaction
        with self.narrate() as n:
            names = ["Anticor", "OLMAR", "PAMR", "CWMR", "RMR", "ONS", "UP", "EG", "CORN", "M0", "WMAMR", "BK"]
            small = VGroup(*[pill(t, GREY, SMALL, 0.2) for t in names]).arrange_in_grid(3, 4, buff=0.25).shift(LEFT * 3 + UP * 1.2)
            ours = pill("EIIE", BLUE, HEADING).shift(RIGHT * 4 + UP * 1.2)
            self.play(FadeIn(ours), run_time=0.5)
            n.until("dozen published strategies")
            self.play(LaggedStart(*[FadeIn(b) for b in small], lag_ratio=0.08), run_time=1.6)
            n.until("same data")
            data = sparkline([1, 1.3, 1.1, 1.6, 1.4, 1.9, 2.4, 2.1], width=11, height=1.0, color=GREY).shift(DOWN * 1.4)
            dl = label("same prices, same fees", SMALL, GREY).next_to(data, DOWN, buff=0.3)
            self.play(Create(data), FadeIn(dl), run_time=1.0)
            n.until("actor-critic family")
            ac = VGroup(pill("actor", BLUE, SMALL, 0.2), pill("critic", RED, SMALL, 0.2)).arrange(RIGHT, buff=0.4).next_to(ours, DOWN, buff=0.6)
            self.play(FadeIn(ac), Create(cross(ac)), run_time=0.7)
            n.until("does not react")
            poke = Dot(color=YELLOW, radius=0.12).move_to(data.get_center() + UP * 1.2)
            self.play(FadeIn(poke), run_time=0.2)
            self.play(poke.animate.move_to(data.point_from_proportion(0.5)), run_time=0.5)
            self.play(Indicate(data, color=GREY, scale_factor=1.0), run_time=0.6)
            static = label("prices don't move", SMALL, YELLOW).next_to(poke, UP, buff=0.2)
            self.play(FadeIn(static), run_time=0.4)
            self.hold(n, 0.5)
            self.clear_all(0.5)

        # ================================================================== 10 setup
        with self.narrate() as n:
            sec = self.section_title("How it works")
            tl = NumberLine(x_range=[0, 12, 1], length=11, color=GREY).shift(UP * 2.0)
            tl_l = label("thirty-minute periods").next_to(tl, UP, buff=0.3)
            self.play(Create(tl), run_time=0.8)
            n.until("thirty-minute periods")
            self.play(FadeIn(tl_l), run_time=0.5)
            n.until("twelve things")
            coins = VGroup(coin(YELLOW, 0.36, "₿"), *[coin(BLUE, 0.36) for _ in range(COINS)]).arrange(RIGHT, buff=0.3).shift(DOWN * 0.4)
            self.play(LaggedStart(*[GrowFromCenter(c) for c in coins], lag_ratio=0.06), run_time=1.2)
            n.until("Bitcoin as the cash")
            cash = label("cash", SMALL, YELLOW).next_to(coins[0], DOWN, buff=0.25)
            self.play(Indicate(coins[0], color=YELLOW, scale_factor=1.3), FadeIn(cash), run_time=0.8)
            n.until("most traded by volume")
            vols = VGroup(*[rect(0.5, 0.3 + 1.4 * (0.82 ** i), BLUE, 0.35).next_to(c, DOWN, buff=0.35) for i, c in enumerate(coins[1:])])
            vl = label("30-day volume", SMALL, GREY).next_to(vols, DOWN, buff=0.25)
            self.play(LaggedStart(*[GrowFromEdge(v, UP) for v in vols], lag_ratio=0.05), FadeIn(vl), run_time=1.0)
            n.until("before the test window")
            test = rect(3.5, 0.35, BLUE, 0.6).move_to(tl.n2p(9.5))
            rank = Triangle(color=YELLOW, fill_opacity=1, fill_color=YELLOW).scale(0.18).rotate(PI).next_to(tl.n2p(7.5), UP, buff=0.05)
            tl2 = label("test", SMALL, BLUE).next_to(test, UP, buff=0.1)
            rl = label("ranking taken here", SMALL, YELLOW).next_to(rank, UP, buff=0.1).shift(LEFT * 1.0)
            self.play(FadeIn(test, tl2), FadeOut(tl_l), run_time=0.6)
            self.play(FadeIn(rank, rl), run_time=0.6)
            self.hold(n, 0.5)
            self.fade_all_but([sec])

        # ================================================================== 11 the input block
        with self.narrate() as n:
            layers = VGroup(*[price_grid(rows=COINS, cols=14, cell=0.3, color=c) for c in (GREEN, YELLOW, BLUE)])
            for i, l in enumerate(layers):
                l.shift(RIGHT * 0.3 * i + UP * 0.3 * i)
            layers.move_to(LEFT * 1.8 + UP * 0.2)
            rows_l = label("11 coins", BODY, GREY).next_to(layers, LEFT, buff=0.4)
            self.play(FadeIn(layers[2]), run_time=0.6)
            n.until("small block of numbers")
            self.play(Indicate(layers[2], color=WHITE, scale_factor=1.02), run_time=0.8)
            n.until("eleven coins")
            self.play(FadeIn(rows_l), LaggedStart(*[Indicate(VGroup(*layers[2][r * 14:(r + 1) * 14]), color=WHITE, scale_factor=1.0) for r in range(COINS)], lag_ratio=0.08), run_time=1.5)
            names = VGroup(*[label(t, BODY, c) for t, c in (("close", BLUE), ("high", YELLOW), ("low", GREEN))]).arrange(DOWN, aligned_edge=LEFT, buff=0.2).next_to(layers, RIGHT, buff=1.0)
            n.until("closing")
            self.play(FadeIn(names[0]), run_time=0.4)
            n.until("highest")
            self.play(FadeIn(layers[1], names[1]), run_time=0.5)
            n.until("lowest")
            self.play(FadeIn(layers[0], names[2]), run_time=0.5)
            n.until("fifty periods")
            cols_l = label("last 50 periods, about a day", BODY, GREY).next_to(layers, DOWN, buff=0.5)
            self.play(FadeIn(cols_l), run_time=0.5)
            n.until("divided by")
            last = VGroup(*[layers[2][r * 14 + 13] for r in range(COINS)])
            ones = VGroup(*[label("1", SMALL, WHITE).move_to(c) for c in last])
            norm = label("÷ latest close", BODY, WHITE).next_to(names, DOWN, buff=0.8)
            self.play(Indicate(last, color=WHITE, scale_factor=1.15), FadeIn(norm), run_time=1.0)
            self.play(FadeIn(ones), run_time=0.5)
            n.until("did not exist yet")
            row = VGroup(*layers[2][9 * 14:10 * 14])
            flat = Line(row.get_left(), row.get_right(), color=WHITE, stroke_width=3)
            fl = label("flat fake prices", SMALL, WHITE).next_to(flat, DOWN, buff=0.1)
            self.play(Create(flat), FadeIn(fl), run_time=0.7)
            n.until("decaying fake prices")
            decay = sparkline([1, 0.8, 0.65, 0.5, 0.4, 0.3], width=2.6, height=0.9, color=RED).next_to(names, RIGHT, buff=1.2).shift(UP * 0.3)
            dl = label("decaying: net learned to avoid", SMALL, RED).next_to(decay, DOWN, buff=0.15)
            self.play(Create(decay), FadeIn(dl), run_time=0.7)
            self.play(Create(cross(decay)), run_time=0.4)
            self.hold(n, 0.5)
            self.fade_all_but([sec])

        # ================================================================== 12 the anchor: evaluators
        with self.narrate() as n:
            anchor = pipeline(1.0)
            k = anchor.parts
            self.play(FadeIn(k["grid"], k["grid_l"]), run_time=0.5)
            n.until("identical independent evaluators")
            self.play(Create(k["a_in"]), LaggedStart(*[FadeIn(e) for e in k["net"]], lag_ratio=0.05), FadeIn(k["net_l"]), run_time=1.2)
            n.until("never flows between coins")
            x0, x1 = k["grid"].get_left()[0], k["net"].get_right()[0]
            walls = VGroup(*[DashedLine([x0, y, 0], [x1, y, 0], color=RED, stroke_width=1.5, dash_length=0.1)
                             for y in [(k["net"][i].get_bottom()[1] + k["net"][i + 1].get_top()[1]) / 2 for i in range(COINS - 1)]])
            wl = label("nothing crosses rows", BODY, RED).next_to(k["net"], UP, buff=0.5)
            self.play(Create(walls), FadeIn(wl), run_time=1.0)
            n.until("own small evaluator")
            path = VGroup(*[k["grid"][3 * 8 + c] for c in range(8)])
            self.play(Indicate(path, color=WHITE, scale_factor=1.0), Indicate(k["a_in"][3], color=WHITE), Indicate(k["net"][3], color=WHITE), run_time=1.2)
            n.until("share the same weights")
            sw = label("shared weights", BODY, BLUE).move_to(wl)
            self.play(ReplacementTransform(wl, sw), FadeOut(walls), LaggedStart(*[Indicate(e, color=WHITE, scale_factor=1.05) for e in k["net"]], lag_ratio=0.05), run_time=1.2)
            n.until("single score")
            scores = VGroup(*[label(s, SMALL, BLUE).next_to(e, RIGHT, buff=0.15) for s, e in zip(("0.8", "0.1", "0.4", "0.6", "0.2", "0.3", "0.9", "0.1", "0.5", "0.2", "0.4"), k["net"])])
            self.play(LaggedStart(*[FadeIn(s, shift=RIGHT * 0.2) for s in scores], lag_ratio=0.05), run_time=1.0)
            n.until("learned bias for cash")
            cash = pill("cash bias", YELLOW, SMALL, 0.15).next_to(k["soft"], UP, buff=0.6)
            ca = Arrow(cash.get_bottom(), k["soft"].get_top(), buff=0.08, color=YELLOW)
            self.play(FadeIn(cash), Create(ca), run_time=0.6)
            n.until("softmax")
            self.play(FadeOut(scores), Create(k["a_mid"]), FadeIn(k["soft"]), run_time=1.0)
            n.until("sum to one")
            self.play(Create(k["a_out"]), GrowFromEdge(k["out"], UP), FadeIn(k["out_l"]), run_time=0.8)
            one = label("= 1", SMALL, YELLOW).next_to(k["out"], UP, buff=0.15)
            self.play(FadeIn(one), run_time=0.4)
            self.hold(n, 0.5)
            self.play(FadeOut(sw, cash, ca, one), run_time=0.4)
            # shrink the anchor into the corner; it stays there for the rest of the section
            self.play(anchor.animate.scale(0.34).to_corner(UR, buff=0.35), run_time=1.0)

        # ================================================================== 13 three evaluator types
        with self.narrate() as n:
            hl = SurroundingRectangle(k["net"], color=YELLOW, buff=0.08)
            self.play(Create(hl), run_time=0.4)
            row = price_grid(rows=1, cols=14, cell=0.42).shift(UP * 2.0 + LEFT * 2.2)
            rl = label("one coin, 50 periods", SMALL, GREY).next_to(row, UP, buff=0.2)
            self.play(FadeIn(row, rl), run_time=0.6)
            n.until("convolutional one")
            kern = SurroundingRectangle(VGroup(*row[0:3]), color=YELLOW, buff=0.04)
            kl = label("CNN kernel: height one, slides along time", SMALL, YELLOW).next_to(row, DOWN, buff=0.3)
            self.play(Create(kern), FadeIn(kl), run_time=0.6)
            n.until("time axis")
            self.play(kern.animate.move_to(VGroup(*row[11:14])), run_time=1.6, rate_func=linear)
            n.until("basic recurrent one")
            cells = VGroup(*[Square(0.5, color=GREEN) for _ in range(7)]).arrange(RIGHT, buff=0.6).next_to(kl, DOWN, buff=0.8)
            carr = VGroup(*[Arrow(cells[i].get_right(), cells[i + 1].get_left(), buff=0.03, color=GREEN, max_tip_length_to_length_ratio=0.25) for i in range(6)])
            cl = label("RNN over the same history", BODY, GREEN).next_to(cells, DOWN, buff=0.3)
            self.play(FadeIn(cells, cl), run_time=0.5)
            self.play(LaggedStart(*[Create(a) for a in carr], lag_ratio=0.15), run_time=1.0)
            n.until("long short-term memory")
            gates = VGroup(*[Circle(0.1, color=GREEN, fill_opacity=1, fill_color=GREEN).move_to(c.get_corner(UR)) for c in cells])
            ll = label("LSTM: same, with gates", BODY, GREEN).move_to(cl)
            self.play(FadeIn(gates), ReplacementTransform(cl, ll), run_time=0.7)
            n.until("previous period's portfolio weights")
            score = pill("score", BLUE, SMALL, 0.2).next_to(ll, DOWN, buff=0.9).shift(LEFT * 1.5)
            prev = weight_bar([0.3, 0.2, 0.15, 0.15, 0.1, 0.1], width=2.0, height=0.4).next_to(score, RIGHT, buff=1.6)
            pa = Arrow(prev.get_left(), score.get_right(), buff=0.1, color=GREEN)
            pl = label("previous weights join just before scoring", SMALL, GREEN).next_to(VGroup(score, prev), DOWN, buff=0.25)
            self.play(FadeIn(score, prev, pl), Create(pa), Indicate(k["prev"], color=GREEN, scale_factor=1.3), run_time=1.0)
            n.until("reluctant to move money")
            same = weight_bar([0.3, 0.2, 0.15, 0.15, 0.1, 0.1], width=2.0, height=0.4).next_to(score, LEFT, buff=1.2)
            eq = label("≈", BODY, YELLOW).move_to((same.get_right() + score.get_left()) / 2)
            self.play(FadeIn(same, eq), run_time=0.6)
            self.hold(n, 0.5)
            self.fade_all_but([sec, anchor, hl])

        # ================================================================== 14 three consequences
        with self.narrate() as n:
            n.until("linearly")
            bars = VGroup(*[rect(0.4, 0.3 + 0.3 * i, BLUE, 0.5) for i in range(8)]).arrange(RIGHT, buff=0.15, aligned_edge=DOWN).shift(UP * 1.4 + LEFT * 3.2)
            bl = label("training time vs number of coins", SMALL).next_to(bars, DOWN, buff=0.3)
            self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.1), FadeIn(bl), run_time=1.2)
            n.until("eleven times")
            win = price_grid(rows=1, cols=8, cell=0.3).shift(DOWN * 0.6 + RIGHT * 2.0)
            copies = VGroup(*[win.copy().shift(DOWN * 0.12 * i + RIGHT * 0.12 * i).set_opacity(0.5) for i in range(1, 6)])
            x11 = label("×11", HEADING, YELLOW).next_to(win, RIGHT, buff=0.8)
            wl = label("every window used once per coin", SMALL).next_to(copies, DOWN, buff=0.35)
            self.play(FadeIn(win), run_time=0.4)
            self.play(LaggedStart(*[FadeIn(c) for c in copies], lag_ratio=0.1), FadeIn(x11, wl), run_time=1.0)
            n.until("swap coins")
            coins = VGroup(*[coin(BLUE, 0.3) for _ in range(6)]).arrange(RIGHT, buff=0.3).shift(DOWN * 2.3 + LEFT * 3.2)
            sl = label("swap coins in and out, no retraining", SMALL).next_to(coins, DOWN, buff=0.3)
            self.play(FadeIn(coins, sl), run_time=0.6)
            new = coin(RED, 0.3).move_to(coins[2]).shift(UP * 1.2)
            self.play(FadeIn(new), run_time=0.3)
            self.play(coins[2].animate.shift(DOWN * 1.2).set_opacity(0), new.animate.move_to(coins[2]), run_time=0.8)
            self.hold(n, 0.5)
            self.fade_all_but([sec, anchor, hl])

        # ================================================================== 15 transaction cost
        with self.narrate() as n:
            self.play(Transform(hl, SurroundingRectangle(k["out"], color=YELLOW, buff=0.08)), run_time=0.5)
            n.until("quarter of a percent")
            fee = pill("0.25% per trade", RED).shift(UP * 2.4 + LEFT * 2)
            self.play(FadeIn(fee), run_time=0.5)
            n.until("shrinks the portfolio")
            before = weight_bar([0.4, 0.3, 0.3], width=5.0, height=0.8).shift(UP * 0.7 + LEFT * 4.2)
            after = weight_bar([0.2, 0.5, 0.3], width=5.0 * 0.92, height=0.8).shift(UP * 0.7 + RIGHT * 1.4)
            arr = Arrow(before.get_right(), after.get_left(), buff=0.15, color=YELLOW)
            mu = label("× μ", BODY, YELLOW).next_to(arr, UP, buff=0.1)
            self.play(FadeIn(before), run_time=0.4)
            self.play(Create(arr), FadeIn(mu), run_time=0.5)
            self.play(GrowFromEdge(after, LEFT), run_time=0.6)
            n.until("both sides of its own definition")
            loop = VGroup(pill("μ", YELLOW, BODY, 0.25), pill("how much is traded", GREY, SMALL, 0.2))
            loop.arrange(RIGHT, buff=1.6).shift(DOWN * 0.9 + LEFT * 2.5)
            l1 = Arrow(loop[0].get_right(), loop[1].get_left(), buff=0.1, color=GREY).shift(UP * 0.15)
            l2 = Arrow(loop[1].get_left(), loop[0].get_right(), buff=0.1, color=GREY).shift(DOWN * 0.15)
            self.play(FadeIn(loop), Create(l1), Create(l2), run_time=0.8)
            n.until("iteratively")
            line = NumberLine(x_range=[0, 1, 0.25], length=7, include_numbers=True, color=GREY, font_size=24).shift(DOWN * 2.6)
            self.play(Create(line), run_time=0.6)
            dot = Dot(line.n2p(0.2), color=YELLOW, radius=0.11)
            self.play(FadeIn(dot), run_time=0.2)
            x = 0.2
            for _ in range(5):
                x = x + (0.92 - x) * 0.55
                self.play(dot.animate.move_to(line.n2p(x)), run_time=0.35)
            n.until("any starting guess")
            dot2 = Dot(line.n2p(1.0), color=GREEN, radius=0.11)
            self.play(FadeIn(dot2), run_time=0.2)
            x = 1.0
            for _ in range(5):
                x = x + (0.92 - x) * 0.55
                self.play(dot2.animate.move_to(line.n2p(x)), run_time=0.35)
            n.until("fixed number of iterations")
            t1 = label("training: fixed steps", SMALL, GREY).next_to(line, DOWN, buff=0.35).shift(LEFT * 2.5)
            self.play(FadeIn(t1), run_time=0.4)
            n.until("until it stops changing")
            t2 = label("back-test: until converged", SMALL, GREY).next_to(line, DOWN, buff=0.35).shift(RIGHT * 2.5)
            self.play(FadeIn(t2), run_time=0.4)
            self.hold(n, 0.5)
            self.fade_all_but([sec, anchor, hl])

        # ================================================================== 16 state, action, reward
        with self.narrate() as n:
            self.play(FadeOut(hl), anchor.animate.scale(0.62 / 0.34).move_to(UP * 0.9), run_time=1.0)
            n.until("state")
            s_box = SurroundingRectangle(VGroup(k["grid"], k["prev"]), color=GREY, buff=0.15)
            s_l = label("state", BODY, GREY).next_to(s_box, LEFT, buff=0.2)
            self.play(Create(s_box), FadeIn(s_l), run_time=0.7)
            n.until("action")
            a_box = SurroundingRectangle(k["out"], color=YELLOW, buff=0.15)
            a_l = label("action", BODY, YELLOW).next_to(a_box, UP, buff=0.1)
            self.play(Create(a_box), FadeIn(a_l), run_time=0.7)
            n.until("reward for a period")
            r = pill("reward = log growth after fees", YELLOW, SMALL, 0.2).to_edge(DOWN, buff=0.5)
            self.play(FadeIn(r, shift=UP * 0.3), run_time=0.6)
            n.until("average")
            seq = VGroup(*[rect(0.35, 0.2 + 0.5 * abs(np.sin(i)), YELLOW, 0.5) for i in range(8)]).arrange(RIGHT, buff=0.1, aligned_edge=DOWN).next_to(r, UP, buff=0.3).shift(LEFT * 4.0)
            avg = Line(seq.get_left(), seq.get_right(), color=WHITE).move_to(seq.get_center())
            al = label("average", SMALL, WHITE).next_to(seq, UP, buff=0.1)
            self.play(FadeIn(seq, al), run_time=0.6)
            n.until("final wealth")
            self.play(Create(avg), run_time=0.6)
            n.until("different lengths comparable")
            seq2 = VGroup(*[rect(0.35, 0.2 + 0.5 * abs(np.sin(i)), YELLOW, 0.5) for i in range(4)]).arrange(RIGHT, buff=0.1, aligned_edge=DOWN).next_to(r, UP, buff=0.3).shift(RIGHT * 4.5)
            eq = label("≈", BODY, WHITE).move_to((seq.get_right() + seq2.get_left()) / 2)
            self.play(FadeIn(seq2, eq), run_time=0.6)
            self.hold(n, 0.5)
            self.play(FadeOut(s_box, s_l, a_box, a_l, r, seq, avg, al, seq2, eq), run_time=0.4)
            self.play(anchor.animate.scale(0.34 / 0.62).to_corner(UR, buff=0.35), run_time=0.8)

        # ================================================================== 17 full exploitation
        with self.narrate() as n:
            ax = Axes(x_range=[0, 10, 1], y_range=[0, 4, 1], x_length=8.5, y_length=3.2, axis_config={"color": GREY, "include_ticks": False}).shift(UP * 0.9 + LEFT * 1.5)
            xs = np.linspace(0, 10, 80)
            ys = 2 + 0.8 * np.sin(xs) + 0.15 * xs + 0.3 * np.sin(3.1 * xs)
            price = ax.plot_line_graph(xs, ys, add_vertex_dots=False, line_color=BLUE)
            pl = label("fixed price history", BODY, BLUE).next_to(ax, UP, buff=0.1)
            self.play(Create(ax), Create(price), FadeIn(pl), run_time=1.2)
            n.until("important simplification")
            key = pill("the key assumption", YELLOW, SMALL, 0.2).next_to(ax, RIGHT, buff=0.3).shift(UP * 1.0)
            self.play(FadeIn(key), run_time=0.5)
            n.until("too small to move the market")
            poke = VGroup(Dot(color=YELLOW, radius=0.22), label("trade", SMALL, YELLOW)).arrange(DOWN, buff=0.1).move_to(ax.c2p(5, 0.4))
            self.play(FadeIn(poke), run_time=0.3)
            self.play(poke.animate.move_to(ax.c2p(5, ys[40] - 0.35)), run_time=0.6)
            self.play(Indicate(price, color=WHITE, scale_factor=1.0), run_time=0.6)
            self.play(FadeOut(poke, key), run_time=0.3)
            n.until("computed exactly")
            acts = VGroup(*[weight_bar([0.5, 0.3, 0.2], width=1.4, height=0.3).move_to(ax.c2p(1.5 + 2.3 * i, 0.5)) for i in range(4)])
            vals = VGroup(*[label(v, SMALL, YELLOW).next_to(a, DOWN, buff=0.1) for v, a in zip(("+0.4", "−0.1", "+0.7", "+0.2"), acts)])
            self.play(LaggedStart(*[AnimationGroup(FadeIn(a), FadeIn(v)) for a, v in zip(acts, vals)], lag_ratio=0.25), run_time=1.5)
            n.until("every possible action")
            self.play(LaggedStart(*[Indicate(a, color=WHITE, scale_factor=1.15) for a in acts], lag_ratio=0.2), run_time=1.2)
            n.until("for free")
            free = label("for free", SMALL, YELLOW).next_to(vals, DOWN, buff=0.15)
            self.play(FadeIn(free), run_time=0.4)
            n.until("value function")
            critic = pill("critic", RED, SMALL, 0.2).to_edge(DOWN, buff=1.1).shift(LEFT * 4.5)
            self.play(FadeIn(critic), Create(cross(critic)), run_time=0.6)
            n.until("need to explore")
            expl = pill("explore", RED, SMALL, 0.2).to_edge(DOWN, buff=1.1).shift(LEFT * 1.5)
            self.play(FadeIn(expl), Create(cross(expl)), run_time=0.6)
            n.until("gradient ascent")
            ga = pill("gradient ascent on reward", GREEN, SMALL, 0.2).to_edge(DOWN, buff=1.1).shift(RIGHT * 2.5)
            up = Arrow(ga.get_top(), ga.get_top() + UP * 0.9, color=GREEN, buff=0.05)
            self.play(FadeIn(ga), GrowArrow(up), run_time=0.7)
            n.until("Adam")
            adam = label("Adam, mini-batches", SMALL, GREY).next_to(ga, DOWN, buff=0.2)
            self.play(FadeIn(adam), run_time=0.4)
            n.until("weight initialisation")
            dice = label("only randomness: initial weights", SMALL, GREY).next_to(anchor, DOWN, buff=0.15)
            self.play(FadeIn(dice), Indicate(k["net"], color=WHITE, scale_factor=1.05), run_time=0.8)
            self.hold(n, 0.5)
            self.fade_all_but([sec, anchor])

        # ================================================================== 18 portfolio vector memory
        with self.narrate() as n:
            hl = SurroundingRectangle(k["prev"], color=GREEN, buff=0.08)
            self.play(Create(hl), run_time=0.4)
            n.until("portfolio vector memory")
            cells = VGroup(*[rect(0.55, 1.4, GREEN, 0.15) for _ in range(16)]).arrange(RIGHT, buff=0.08).shift(DOWN * 0.3 + LEFT * 0.8)
            ml = label("portfolio vector memory", BODY, GREEN).to_edge(UP, buff=1.0).to_edge(LEFT, buff=1.0)
            self.play(FadeIn(cells, ml), run_time=0.8)
            n.until("uniform weights")
            fills = VGroup(*[weight_bar([0.25, 0.25, 0.25, 0.25], width=1.2, height=0.4, vertical=True).move_to(c) for c in cells])
            self.play(LaggedStart(*[FadeIn(f) for f in fills], lag_ratio=0.03), run_time=0.8)
            n.until("reads the allocation")
            win = SurroundingRectangle(VGroup(*cells[6:11]), color=BLUE, buff=0.05)
            wl = label("training window", SMALL, BLUE).next_to(win, DOWN, buff=0.2)
            read = cells[5].copy().set_fill(RED, 0.7)
            rl = label("read", SMALL, RED).next_to(read, UP, buff=0.15)
            self.play(Create(win), FadeIn(wl), run_time=0.6)
            self.play(FadeIn(read, rl), run_time=0.5)
            net = pill("network", BLUE, SMALL, 0.2).next_to(win, UP, buff=1.3).shift(LEFT * 2.5)
            a1 = Arrow(read.get_top(), net.get_left(), color=RED, buff=0.1)
            self.play(FadeIn(net), Create(a1), run_time=0.6)
            n.until("overwrites")
            a2 = Arrow(net.get_bottom(), win.get_top(), color=BLUE, buff=0.1)
            newf = VGroup(*[weight_bar([0.4, 0.3, 0.2, 0.1], width=1.2, height=0.4, vertical=True).move_to(c) for c in cells[6:11]])
            self.play(Create(a2), *[Transform(fills[i], newf[i - 6]) for i in range(6, 11)], run_time=0.9)
            n.until("converges")
            final = VGroup(*[weight_bar([0.1 + 0.05 * (i % 4), 0.3, 0.2, 0.5 - 0.05 * (i % 4)], width=1.2, height=0.4, vertical=True).move_to(c) for i, c in enumerate(cells)])
            self.play(*[Transform(fills[i], final[i]) for i in range(16)], run_time=1.2)
            n.until("in parallel")
            win2 = SurroundingRectangle(VGroup(*cells[0:5]), color=BLUE, buff=0.05)
            win3 = SurroundingRectangle(VGroup(*cells[11:16]), color=BLUE, buff=0.05)
            pl = label("batches on different windows run in parallel", SMALL, BLUE).next_to(cells, DOWN, buff=0.8)
            self.play(Create(win2), Create(win3), FadeIn(pl), run_time=0.8)
            n.until("never have to flow back")
            back = Arrow(cells[10].get_bottom() + DOWN * 0.15, cells[6].get_bottom() + DOWN * 0.15, color=RED, buff=0)
            self.play(Create(back), run_time=0.4)
            self.play(Create(cross(back)), run_time=0.4)
            self.hold(n, 0.5)
            self.fade_all_but([sec, anchor])

        # ================================================================== 19 online stochastic batch learning
        with self.narrate() as n:
            tl = NumberLine(x_range=[0, 20, 1], length=10.5, color=GREY).shift(DOWN * 0.6 + LEFT * 1.2)
            tll = label("training set keeps growing", BODY, GREY).to_edge(UP, buff=1.0).shift(LEFT * 1.5)
            n.until("training set grows")
            self.play(Create(tl), FadeIn(tll), run_time=0.8)
            n.until("new period is added")
            new = rect(0.5, 0.4, YELLOW, 0.7).move_to(tl.n2p(20.3) + UP * 0.4)
            nl = label("now", SMALL, YELLOW).next_to(new, DOWN, buff=1.0)
            self.play(GrowFromEdge(new, LEFT), FadeIn(nl), run_time=0.6)
            n.until("geometrically decaying")
            bars = VGroup(*[rect(0.36, 0.12 + 2.0 * (0.85 ** (19 - i)), BLUE, 0.4).move_to(tl.n2p(i + 0.5) + UP * 0.05, aligned_edge=DOWN) for i in range(20)])
            bl = label("probability a batch starts here", SMALL, BLUE).next_to(bars, UP, buff=0.2).shift(LEFT * 2)
            self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.03), FadeIn(bl), run_time=1.2)
            n.until("recent data is chosen more often")
            picks = VGroup(*[SurroundingRectangle(VGroup(*bars[s:s + 4]), color=GREEN, buff=0.03) for s in (15, 12, 16)])
            self.play(LaggedStart(*[Create(w) for w in picks], lag_ratio=0.3), run_time=1.2)
            n.until("consecutive windows")
            wide = SurroundingRectangle(VGroup(*bars[8:12]), color=YELLOW, buff=0.03).shift(DOWN * 1.0)
            wl2 = label("50 periods", SMALL, YELLOW).next_to(wide, LEFT, buff=0.2)
            self.play(Create(wide), FadeIn(wl2), run_time=0.6)
            n.until("overlap by all but one")
            self.play(FadeOut(wide, wl2), run_time=0.3)
            o1 = SurroundingRectangle(VGroup(*bars[5:9]), color=YELLOW, buff=0.03).shift(DOWN * 1.0)
            o2 = SurroundingRectangle(VGroup(*bars[6:10]), color=YELLOW, buff=0.03).shift(DOWN * 1.35)
            ol = label("two distinct batches", SMALL, YELLOW).next_to(o2, DOWN, buff=0.15)
            self.play(Create(o1), Create(o2), FadeIn(ol), run_time=0.8)
            n.until("pre-training before the test")
            pre = SurroundingRectangle(VGroup(*bars[0:14]), color=GREY, buff=0.05)
            prl = label("pre-train", SMALL, GREY).next_to(pre, UP, buff=0.1)
            self.play(Create(pre), FadeIn(prl), run_time=0.6)
            n.until("continued learning")
            self.play(FadeOut(pre, prl), Indicate(new, color=WHITE, scale_factor=1.4), run_time=0.8)
            n.until("thirty online training steps")
            cnt = label("30 steps per new period", BODY, GREEN).next_to(nl, DOWN, buff=0.3).shift(LEFT * 1.5)
            self.play(FadeIn(cnt), run_time=0.5)
            self.hold(n, 0.5)
            self.clear_all(0.5)

        # ================================================================== 20 the back-tests
        with self.narrate() as n:
            sec = self.section_title("Experiments")
            n.until("Poloniex")
            ex = pill("Poloniex · quoted in ₿", YELLOW).shift(UP * 2.6)
            self.play(FadeIn(ex), run_time=0.5)
            tl = NumberLine(x_range=[2014.5, 2017.6, 0.5], length=11.5, color=GREY, include_numbers=True, decimal_number_config={"num_decimal_places": 0}, numbers_to_include=[2015, 2016, 2017], font_size=24).shift(DOWN * 1.8)
            n.until("three back-tests")
            self.play(Create(tl), run_time=0.8)
            tests = [(2016.68, 2016.83, "September to October 2016"), (2016.94, 2017.08, "December 2016"), (2017.18, 2017.32, "March to April 2017")]
            trains = []
            for i, (a, b, phrase) in enumerate(tests):
                n.until(phrase)
                y = 1.0 - 0.55 * i
                test = rect(tl.n2p(b)[0] - tl.n2p(a)[0], 0.35, BLUE).move_to((tl.n2p(a) + tl.n2p(b)) / 2 + UP * y)
                tlab = label(f"test {i + 1}", SMALL, BLUE).next_to(test, RIGHT, buff=0.15)
                self.play(FadeIn(test, tlab), run_time=0.5)
                trains.append((a, y, i))
            n.until("own training set")
            tr = VGroup(*[rect(tl.n2p(a)[0] - tl.n2p(2014.6 + 0.25 * i)[0], 0.35, GREY, 0.3).move_to((tl.n2p(2014.6 + 0.25 * i) + tl.n2p(a)) / 2 + UP * y) for a, y, i in trains])
            trl = label("training data, up to the test", SMALL, GREY).next_to(tr[2], DOWN, buff=0.15)
            self.play(LaggedStart(*[GrowFromEdge(t, RIGHT) for t in tr], lag_ratio=0.2), FadeIn(trl), run_time=1.0)
            n.until("cross-validation window")
            cv = rect(tl.n2p(2016.49)[0] - tl.n2p(2016.35)[0], 0.35, YELLOW).move_to((tl.n2p(2016.35) + tl.n2p(2016.49)) / 2 + UP * 1.55)
            cvl = label("hyperparameters chosen here", SMALL, YELLOW).next_to(cv, LEFT, buff=0.2)
            self.play(FadeIn(cv, cvl), run_time=0.6)
            self.hold(n, 0.5)
            self.fade_all_but([sec])

        # ================================================================== 21 baselines
        with self.narrate() as n:
            ours = VGroup(*[pill(t, BLUE, SMALL, 0.22) for t in ("CNN", "basic RNN", "LSTM")]).arrange(RIGHT, buff=0.3).shift(UP * 2.5)
            ol = label("three ensemble networks", SMALL, BLUE).next_to(ours, UP, buff=0.15)
            self.play(FadeIn(ours, ol), run_time=0.6)
            n.until("earlier integrated")
            prev = pill("earlier integrated CNN", GREY, SMALL, 0.22).shift(UP * 1.8)
            self.play(FadeIn(prev), run_time=0.5)
            n.until("three benchmarks")
            bench = VGroup(*[pill(t, YELLOW, SMALL, 0.22) for t in ("best coin in hindsight", "buy and hold", "constant rebalance")]).arrange(RIGHT, buff=0.3).shift(UP * 0.2)
            bl = label("benchmarks", SMALL, YELLOW).next_to(bench, UP, buff=0.15)
            self.play(FadeIn(bl), run_time=0.3)
            for phrase, b in zip(("best stock", "uniform buy and hold", "constant rebalancing"), bench):
                n.until(phrase)
                self.play(FadeIn(b), run_time=0.4)
            classic = [("Anticor", "Anticor"), ("OLMAR", "online moving average"), ("PAMR", "passive aggressive"), ("RMR", "robust median"),
                       ("ONS", "online Newton"), ("UP", "universal portfolios"), ("EG", "exponentiated gradient")]
            boxes = VGroup(*([pill(t, GREY, SMALL, 0.2) for t, _ in classic] + [pill(t, GREY, SMALL, 0.2) for t in ("CWMR", "CORN", "M0", "WMAMR", "BK")])).arrange_in_grid(2, 6, buff=0.25).shift(DOWN * 1.2)
            cl = label("a dozen classical strategies, same fees", SMALL, GREY).next_to(boxes, DOWN, buff=0.35)
            for (t, phrase), b in zip(classic, boxes):
                n.until(phrase)
                self.play(FadeIn(b), run_time=0.35)
            n.until("several others")
            self.play(LaggedStart(*[FadeIn(b) for b in boxes[7:]], lag_ratio=0.1), FadeIn(cl), run_time=0.8)
            n.until("same commission")
            fee = pill("0.25%", RED, SMALL, 0.15).next_to(cl, RIGHT, buff=0.4)
            self.play(FadeIn(fee), run_time=0.4)
            self.hold(n, 0.5)
            self.fade_all_but([sec])

        # ================================================================== 22 metrics
        with self.narrate() as n:
            g = VGroup(rect(0.5, 1.8, YELLOW, 0.6), rect(0.5, 0.5, GREY, 0.6)).arrange(RIGHT, buff=0.2, aligned_edge=DOWN)
            g_l = label("final ÷ start", BODY).next_to(g, DOWN, buff=0.3)
            sh = VGroup(Line(LEFT, RIGHT, color=YELLOW), DashedLine(LEFT + UP * 0.5, RIGHT + UP * 0.5, color=GREY), DashedLine(LEFT + DOWN * 0.5, RIGHT + DOWN * 0.5, color=GREY))
            sh_l = label("Sharpe: return ÷ wobble", BODY).next_to(sh, DOWN, buff=0.3)
            dd = sparkline([1, 1.3, 1.6, 1.2, 0.9, 1.4, 1.8], width=2.4, height=1.6, color=RED)
            dd_l = label("max drawdown", BODY).next_to(dd, DOWN, buff=0.3)
            cols = VGroup(VGroup(g, g_l), VGroup(sh, sh_l), VGroup(dd, dd_l)).arrange(RIGHT, buff=1.6)
            for phrase, c in zip(("final portfolio value", "Sharpe ratio", "maximum drawdown"), cols):
                n.until(phrase)
                self.play(FadeIn(c), run_time=0.5)
            self.hold(n, 0.5)
            self.fade_all_but([sec])

        # ================================================================== 23 what is not tested
        with self.narrate() as n:
            head = label("not tested", HEADING, RED).to_edge(UP, buff=1.0)
            self.play(FadeIn(head), run_time=0.5)
            grid = VGroup()

            def item(icon, text, phrase):
                g = VGroup(icon, label(text, SMALL)).arrange(DOWN, buff=0.2)
                n.until(phrase)
                grid.add(g)
                grid.arrange_in_grid(rows=2, cols=3, buff=(0.9, 0.7)).move_to(DOWN * 0.4)
                self.play(FadeIn(g), run_time=0.5)

            one = VGroup(pill("Poloniex", GREY, SMALL, 0.15), pill("NYSE", GREY, SMALL, 0.15), pill("FX", GREY, SMALL, 0.15)).arrange(RIGHT, buff=0.15)
            one.add(cross(one[1]), cross(one[2]))
            item(one, "one exchange, one asset class", "one exchange")
            live_p = pill("live", GREEN, SMALL, 0.2)
            item(VGroup(live_p, cross(live_p)), "no live trading", "live trading")
            slip = VGroup(DashedLine(LEFT * 0.9, RIGHT * 0.9, color=GREY), Dot(color=YELLOW).shift(RIGHT * 0.6))
            item(slip, "fills at last price, any size", "zero slippage")
            n.until("regardless of size")
            big_order = Dot(color=YELLOW, radius=0.45).move_to(slip[1])
            self.play(Transform(slip[1], big_order), run_time=0.6)
            fixed = VGroup(pill("30 min", GREY, SMALL, 0.15), pill("12 assets", GREY, SMALL, 0.15)).arrange(RIGHT, buff=0.15)
            item(fixed, "never varied", "trading period is fixed")
            seeds = VGroup(Dot(color=BLUE, radius=0.12), Line(UP * 0.5, DOWN * 0.5, color=GREY, stroke_opacity=0.3))
            item(seeds, "one run, no error bars", "random seeds")
            ac = VGroup(pill("actor", BLUE, SMALL, 0.15), pill("critic", RED, SMALL, 0.15)).arrange(RIGHT, buff=0.15)
            item(VGroup(ac, cross(ac)), "no actor-critic baseline", "no actor-critic")
            self.hold(n, 0.5)
            self.clear_all(0.5)

        # ================================================================== 24 headline results
        with self.narrate() as n:
            sec = self.section_title("Results")
            axis, y_of = log_axis(-6.0, 6.4, -2.6, height=4.6)
            self.play(Create(axis), run_time=0.8)
            groups_x = {0: -4.4, 1: -0.2, 2: 4.0}
            titles = VGroup(*[label(f"test {i + 1}", SMALL, GREY).move_to([groups_x[i], -3.0, 0]) for i in range(3)])
            self.play(FadeIn(titles), run_time=0.4)
            order = ["CNN", "RNN", "LSTM", "best coin", "RMR"]
            bw = 0.55

            def bar(name, t):
                v = FAPV[name][t]
                x = groups_x[t] + (order.index(name) - 2) * (bw + 0.12)
                r = rect(bw, max(y_of(v) - y_of(0.1), 0.02), COL[name], 0.85)
                r.move_to([x, y_of(0.1), 0], aligned_edge=DOWN)
                txt = f"{v:.0f}×" if v >= 3 else (f"{v:.1f}×" if v >= 0.5 else f"{v:.2f}×")
                return VGroup(r, label(txt, SMALL, COL[name]).next_to(r, UP, buff=0.08))

            legend = VGroup(*[VGroup(Square(0.25, color=COL[k_], fill_opacity=0.85, fill_color=COL[k_]), label(k_, SMALL, GREY)).arrange(RIGHT, buff=0.12) for k_ in order]).arrange(RIGHT, buff=0.5).to_edge(UP, buff=1.0)
            self.play(FadeIn(legend), run_time=0.4)
            for phrase, name, t in (("about thirty", "CNN", 0), ("thirteen", "RNN", 0), ("about seven", "LSTM", 0), ("twenty percent", "best coin", 0), ("lost money", "RMR", 0)):
                n.until(phrase)
                b = bar(name, t)
                self.play(GrowFromEdge(b[0], DOWN), FadeIn(b[1]), run_time=0.6)
            n.until("quarter percent fee")
            feep = pill("0.25% every 30 min", RED, SMALL, 0.15).move_to([groups_x[0], 2.1, 0])
            self.play(FadeIn(feep), run_time=0.5)
            n.until("second back-test")
            bs = [bar(nm, 1) for nm in order]
            self.play(LaggedStart(*[AnimationGroup(GrowFromEdge(b[0], DOWN), FadeIn(b[1])) for b in bs], lag_ratio=0.15), run_time=1.5)
            n.until("In the third")
            bs = [bar(nm, 2) for nm in order[:4]]
            self.play(LaggedStart(*[AnimationGroup(GrowFromEdge(b[0], DOWN), FadeIn(b[1])) for b in bs], lag_ratio=0.15), run_time=1.5)
            n.until("four and a half")
            self.play(Indicate(bs[3][0], color=WHITE, scale_factor=1.1), run_time=0.8)
            n.until("robust median reversion")
            b = bar("RMR", 2)
            self.play(GrowFromEdge(b[0], DOWN), FadeIn(b[1]), run_time=0.6)
            self.hold(n, 0.5)
            self.fade_all_but([sec])

        # ================================================================== 25 Sharpe, drawdown, the earlier net
        with self.narrate() as n:
            podium = VGroup(*[VGroup(rect(1.4, h, c, 0.7), label(t, SMALL, c)).arrange(DOWN, buff=0.15) for h, c, t in ((2.0, BLUE, "CNN"), (1.6, GREEN, "RNN"), (1.2, YELLOW, "LSTM"))]).arrange(RIGHT, buff=0.3, aligned_edge=DOWN).shift(LEFT * 4 + UP * 0.2)
            pl = label("value and Sharpe: top three, every test", SMALL, GREY).next_to(podium, DOWN, buff=0.3)
            self.play(FadeIn(pl), run_time=0.4)
            n.until("top three positions")
            self.play(LaggedStart(*[GrowFromEdge(p[0], DOWN) for p in podium], lag_ratio=0.2), FadeIn(VGroup(*[p[1] for p in podium])), run_time=1.2)
            n.until("maximum drawdown")
            names = ["CNN", "RNN", "LSTM", "rebalance"]
            gx = {0: 1.6, 1: 3.6, 2: 5.6}
            bars, labels = [], VGroup()
            for t in range(3):
                for j, nm in enumerate(names):
                    r = rect(0.4, MDD[nm][t] / 100 * 5.0, COL[nm]).move_to([gx[t] + (j - 1.5) * 0.46, 1.6, 0], aligned_edge=UP)
                    bars.append(r)
                labels.add(label(f"test {t + 1}", SMALL, GREY).move_to([gx[t], -2.0, 0]))
            ddl = label("worst peak-to-trough loss", SMALL, RED).move_to([3.6, 2.1, 0])
            top = Line([0.6, 1.6, 0], [6.6, 1.6, 0], color=GREY)
            self.play(Create(top), FadeIn(ddl, labels), LaggedStart(*[GrowFromEdge(m, UP) for m in bars], lag_ratio=0.05), run_time=1.5)
            n.until("nearly fifty percent")
            fifty = label("49%", SMALL, RED).next_to(bars[10], DOWN, buff=0.08)
            self.play(Indicate(bars[10], color=RED, scale_factor=1.1), FadeIn(fifty), run_time=0.8)
            n.until("constant rebalancing benchmark")
            reb = VGroup(*[bars[t * 4 + 3] for t in range(3)])
            rl = label("rebalance: safer", SMALL, GREY).next_to(labels, DOWN, buff=0.4)
            self.play(Indicate(reb, color=WHITE, scale_factor=1.1), FadeIn(rl), run_time=0.8)
            n.until("earlier integrated network")
            old = pill("earlier integrated CNN: 1.6× to 4.5×", GREY, SMALL, 0.2).next_to(pl, DOWN, buff=0.6)
            self.play(FadeIn(old), run_time=0.5)
            self.hold(n, 0.5)
            self.clear_all(0.5)

        # ================================================================== 26 what holds up
        with self.narrate() as n:
            sec = self.section_title("Conclusion")
            holds = label("what holds up", BODY, GREEN).to_edge(UP, buff=1.0)
            self.play(FadeIn(holds), run_time=0.4)
            crit = pill("critic", RED, SMALL, 0.12)
            icons = VGroup(
                VGroup(*[RoundedRectangle(width=1.4, height=0.22, corner_radius=0.06, color=BLUE, fill_opacity=0.4, fill_color=BLUE) for _ in range(4)]).arrange(DOWN, buff=0.06),
                VGroup(weight_bar([0.4, 0.3, 0.3], width=1.4, height=0.3), Arrow(ORIGIN, DOWN * 0.7, color=GREEN)).arrange(DOWN, buff=0.1),
                VGroup(*[Dot(color=YELLOW, radius=0.06 + 0.02 * i).shift(RIGHT * 0.3 * i) for i in range(5)]),
                VGroup(crit, cross(crit)),
            )
            texts = ["asset-agnostic shared evaluators", "previous weights fed back in", "exact iterative transaction cost", "no critic on a fixed history"]
            cards = VGroup(*[VGroup(ic, label(t, SMALL, GREEN)).arrange(DOWN, buff=0.3) for ic, t in zip(icons, texts)]).arrange_in_grid(2, 2, buff=(1.2, 0.9)).shift(DOWN * 0.2)
            for phrase, c in zip(("Asset-agnostic evaluators", "feeding the previous allocation", "exact iterative treatment", "without a critic"), cards):
                n.until(phrase)
                self.play(FadeIn(c), run_time=0.6)
            self.hold(n, 0.5)
            self.fade_all_but([sec])

        # ================================================================== 27 but
        with self.narrate() as n:
            big = label("30×", 96, BLUE)
            q = label("?", 96, YELLOW).next_to(big, RIGHT, buff=0.4)
            self.play(FadeIn(big), run_time=0.5)
            n.until("reasons to be careful")
            self.play(FadeIn(q, shift=DOWN * 0.3), run_time=0.5)
            self.hold(n, 0.5)
            self.fade_all_but([sec])

        # caveat list on the left grows across paragraphs 28 to 33; each gets a picture on the right
        caveats = VGroup()

        def add_caveat(text):
            item = label(text, SMALL, WHITE)
            if caveats:
                caveats.set_color(GREY)
                item.next_to(caveats, DOWN, aligned_edge=LEFT, buff=0.3)
            else:
                item.to_edge(LEFT, buff=0.7).shift(UP * 2.6)
            caveats.add(item)
            self.play(FadeIn(item), run_time=0.5)

        # ================================================================== 28 slippage
        with self.narrate() as n:
            add_caveat("1  zero slippage and market impact")
            n.until("zero slippage")
            ax = Axes(x_range=[0, 6, 1], y_range=[0, 4, 1], x_length=5.5, y_length=3.0, axis_config={"color": GREY, "include_ticks": False}).shift(RIGHT * 3.3 + UP * 0.3)
            last = DashedLine(ax.c2p(0, 2), ax.c2p(6, 2), color=GREY)
            ll = label("last price", SMALL, GREY).next_to(last, UP, buff=0.1).shift(LEFT * 1.5)
            self.play(Create(ax), Create(last), FadeIn(ll), run_time=0.8)
            n.until("small-cap altcoins")
            book = VGroup(*[rect(0.25, 0.15 + 0.1 * abs(3 - i), GREY, 0.4).move_to(ax.c2p(1 + 0.7 * i, 2)) for i in range(7)])
            bl = label("thin order book", SMALL, GREY).next_to(book, DOWN, buff=0.8)
            self.play(FadeIn(book, bl), run_time=0.6)
            n.until("slippage is worst")
            fill = Dot(color=RED, radius=0.12).move_to(ax.c2p(3, 2))
            self.play(FadeIn(fill), run_time=0.2)
            self.play(fill.animate.move_to(ax.c2p(3, 3.2)), run_time=0.6)
            fl = label("real fill", SMALL, RED).next_to(fill, RIGHT, buff=0.15)
            self.play(FadeIn(fl), run_time=0.3)
            n.until("on paper")
            paper = pill("30× on paper", BLUE, SMALL, 0.2).next_to(ax, DOWN, buff=0.5)
            self.play(FadeIn(paper), run_time=0.5)
            self.hold(n, 0.5)
            self.fade_all_but([sec, caveats])

        # ================================================================== 29 the boom
        with self.narrate() as n:
            add_caveat("2  one booming market")
            n.until("cryptocurrency boom")
            ax = Axes(x_range=[0, 10, 1], y_range=[0, 5, 1], x_length=6.0, y_length=3.2, axis_config={"color": GREY, "include_ticks": False}).shift(RIGHT * 3.3 + UP * 0.2)
            xs = np.linspace(0, 10, 60)
            curve = ax.plot_line_graph(xs, 0.3 + 0.045 * xs ** 2 + 0.25 * np.sin(2 * xs), add_vertex_dots=False, line_color=YELLOW)
            cl = label("crypto market 2016–17, schematic", SMALL, GREY).next_to(ax, UP, buff=0.1)
            self.play(Create(ax), Create(curve), FadeIn(cl), run_time=1.0)
            wins = VGroup(*[Rectangle(width=0.8, height=3.2, color=BLUE, fill_opacity=0.2, fill_color=BLUE, stroke_width=0).move_to(ax.c2p(x, 2.5)) for x in (6.2, 7.8, 9.3)])
            self.play(FadeIn(wins), run_time=0.6)
            n.until("no bear market")
            bear = ax.plot_line_graph(xs, 4.5 - 0.35 * xs + 0.2 * np.sin(2 * xs), add_vertex_dots=False, line_color=RED)
            nb = label("no bear market", SMALL, RED).next_to(ax, LEFT, buff=0.3)
            self.play(Create(bear), FadeIn(nb), run_time=0.6)
            self.play(bear.animate.set_stroke(opacity=0.15), run_time=0.5)
            n.until("one market")
            one = pill("Poloniex only", GREY, SMALL, 0.2).next_to(ax, DOWN, buff=0.5)
            self.play(FadeIn(one), run_time=0.5)
            self.hold(n, 0.5)
            self.fade_all_but([sec, caveats])

        # ================================================================== 30 thin evaluation
        with self.narrate() as n:
            add_caveat("3  three windows, one run each, no ablation")
            n.until("Three windows")
            dots = VGroup(*[Dot(color=BLUE, radius=0.16).shift(RIGHT * 1.4 * i) for i in range(3)]).shift(RIGHT * 3.3 + UP * 1.8)
            self.play(LaggedStart(*[GrowFromCenter(d) for d in dots], lag_ratio=0.2), run_time=0.8)
            n.until("no confidence intervals")
            bars = VGroup(*[Line(d.get_center() + UP * 0.6, d.get_center() + DOWN * 0.6, color=GREY, stroke_opacity=0.5) for d in dots])
            self.play(Create(bars), run_time=0.4)
            self.play(Create(cross(bars)), run_time=0.4)
            n.until("no ablation")
            comps = VGroup(pill("evaluators", BLUE, SMALL, 0.15), pill("memory", GREEN, SMALL, 0.15), pill("online", YELLOW, SMALL, 0.15)).arrange(RIGHT, buff=0.25).shift(RIGHT * 3.3 + UP * 0.2)
            qs = VGroup(*[label("?", HEADING, GREY).next_to(c, DOWN, buff=0.1) for c in comps])
            self.play(FadeIn(comps), run_time=0.5)
            self.play(FadeIn(qs), run_time=0.4)
            for phrase, c in zip(("ensemble structure", "portfolio memory versus", "online learning"), comps):
                n.until(phrase)
                self.play(Indicate(c, color=WHITE, scale_factor=1.15), run_time=0.7)
            n.until("long short-term memory version")
            two = VGroup(rect(0.6, 0.9, YELLOW, 0.7), rect(0.6, 1.8, GREEN, 0.7)).arrange(RIGHT, buff=0.3, aligned_edge=DOWN).shift(RIGHT * 0.8 + DOWN * 2.0)
            tl = VGroup(label("LSTM", SMALL, YELLOW), label("RNN", SMALL, GREEN)).arrange(RIGHT, buff=0.35).next_to(two, DOWN, buff=0.1)
            self.play(FadeIn(two, tl), run_time=0.6)
            n.until("markets repeating themselves")
            rep_ = sparkline([1, 1.4, 0.8, 1.3, 1, 1.4, 0.8, 1.3], width=2.4, height=0.9, color=GREY).next_to(two, RIGHT, buff=0.6).shift(UP * 0.5)
            rql = label("history repeats?", SMALL, GREY).next_to(rep_, UP, buff=0.1)
            self.play(Create(rep_), FadeIn(rql), run_time=0.8)
            n.until("same hyperparameters")
            same = label("same hyperparameters", SMALL, RED).next_to(rep_, DOWN, buff=0.2)
            self.play(FadeIn(same), run_time=0.5)
            self.hold(n, 0.5)
            self.fade_all_but([sec, caveats])

        # ================================================================== 31 myopic
        with self.narrate() as n:
            add_caveat("4  myopic: one period ahead")
            n.until("myopic")
            tl = NumberLine(x_range=[0, 8, 1], length=6.5, color=GREY).shift(RIGHT * 3.3 + UP * 1.0)
            agent = Triangle(color=BLUE, fill_opacity=1, fill_color=BLUE).scale(0.2).rotate(PI).next_to(tl.n2p(2), UP, buff=0.05)
            horizon = Arrow(tl.n2p(2) + DOWN * 0.4, tl.n2p(3) + DOWN * 0.4, color=YELLOW, buff=0)
            hl = label("sees one step", SMALL, YELLOW).next_to(horizon, DOWN, buff=0.15)
            self.play(Create(tl), FadeIn(agent), run_time=0.7)
            self.play(GrowArrow(horizon), FadeIn(hl), run_time=0.6)
            n.until("discount of zero")
            future = VGroup(*[Dot(tl.n2p(x), color=GREY, radius=0.08) for x in range(4, 9)])
            fl = label("future: weight zero", SMALL, GREY).next_to(future, UP, buff=0.3)
            self.play(FadeIn(future, fl), run_time=0.6)
            self.play(future.animate.set_opacity(0.2), run_time=0.6)
            n.until("critic network as future work")
            ac = VGroup(pill("actor", BLUE, SMALL, 0.15), pill("critic", RED, SMALL, 0.15)).arrange(RIGHT, buff=0.5).shift(RIGHT * 3.3 + DOWN * 1.6)
            al = label("would bring back what they avoided", SMALL, RED).next_to(ac, DOWN, buff=0.25)
            self.play(FadeIn(ac, al), run_time=0.7)
            self.hold(n, 0.5)
            self.fade_all_but([sec, caveats])

        # ================================================================== 32 drawdowns
        with self.narrate() as n:
            add_caveat("5  drawdowns of 20 to 50 percent")
            n.until("drawdowns")
            ax = Axes(x_range=[0, 10, 1], y_range=[0, 4, 1], x_length=6.0, y_length=3.0, axis_config={"color": GREY, "include_ticks": False}).shift(RIGHT * 3.3 + UP * 0.4)
            xs = np.linspace(0, 10, 80)
            ys = 1 + 0.3 * xs - 1.8 * np.exp(-((xs - 6) ** 2) / 0.8)
            curve = ax.plot_line_graph(xs, ys, add_vertex_dots=False, line_color=RED)
            cl = label("equity, schematic", SMALL, GREY).next_to(ax, UP, buff=0.1)
            self.play(Create(ax), Create(curve), FadeIn(cl), run_time=1.0)
            n.until("fifty percent")
            top, bot = ax.c2p(5.0, 1 + 0.3 * 5.0), ax.c2p(6.0, ys[48])
            drop = VGroup(DashedLine(top, [top[0], bot[1], 0], color=RED), label("−50%", BODY, RED).next_to([top[0], (top[1] + bot[1]) / 2, 0], LEFT, buff=0.15))
            self.play(Create(drop[0]), FadeIn(drop[1]), run_time=0.6)
            n.until("risk control")
            shield = pill("risk control", GREY, SMALL, 0.2).next_to(ax, DOWN, buff=0.5)
            self.play(FadeIn(shield), Create(cross(shield)), run_time=0.6)
            self.hold(n, 0.5)
            self.fade_all_but([sec, caveats])

        # ================================================================== 33 reproductions
        with self.narrate() as n:
            add_caveat("6  reimplementations did not reproduce it")
            n.until("reimplemented many times")
            ax = Axes(x_range=[0, 10, 1], y_range=[0, 4, 1], x_length=6.0, y_length=3.0, axis_config={"color": GREY, "include_ticks": False}).shift(RIGHT * 3.3 + UP * 0.4)
            xs = np.linspace(0, 10, 60)
            paper = ax.plot_line_graph(xs, 0.5 + 0.03 * xs ** 2, add_vertex_dots=False, line_color=BLUE)
            pl = label("paper", SMALL, BLUE).next_to(ax.c2p(10, 3.5), LEFT, buff=0.1)
            self.play(Create(ax), Create(paper), FadeIn(pl), run_time=0.9)
            n.until("later data")
            rng = np.random.default_rng(3)
            others = VGroup(*[ax.plot_line_graph(xs, np.clip(1 + 0.05 * rng.normal(size=60).cumsum() - 0.03 * xs, 0.05, 4), add_vertex_dots=False, line_color=GREY) for _ in range(8)])
            ol = label("reimplementations, later data", SMALL, GREY).next_to(ax, DOWN, buff=0.4)
            self.play(LaggedStart(*[Create(o) for o in others], lag_ratio=0.1), FadeIn(ol), run_time=1.5)
            n.until("method's logic")
            ok = label("the mechanism is sound; the returns are the claim in doubt", SMALL, YELLOW).next_to(ol, DOWN, buff=0.3)
            self.play(FadeIn(ok), run_time=0.5)
            self.hold(n, 0.5)
            self.clear_all(0.5)

        # ================================================================== 34 open problems
        with self.narrate() as n:
            sec = self.section_title("Open problems")
            mini = pipeline(0.5).shift(UP * 1.6)
            self.play(FadeIn(mini), run_time=0.8)
            outs = VGroup(pill("market impact\nfrom live records", GREY, SMALL, 0.3), pill("other markets", GREY, SMALL, 0.3), pill("longer horizon,\nstill stable", GREY, SMALL, 0.3))
            outs[0].shift(LEFT * 4.5 + DOWN * 2.0)
            outs[1].shift(DOWN * 2.3)
            outs[2].shift(RIGHT * 4.5 + DOWN * 2.0)
            for phrase, o in zip(("live trading records", "different microstructure", "longer horizon"), outs):
                n.until(phrase)
                a = Arrow(mini.get_bottom(), o.get_top(), color=GREY, buff=0.15)
                self.play(Create(a), FadeIn(o), run_time=0.7)
            self.hold(n, 0.5)
            self.clear_all(0.5)

        # ================================================================== 35 recap
        with self.narrate() as n:
            sec = self.section_title("Recap", run_time=0.3)
            anchor = pipeline(0.72).shift(UP * 0.9)
            k = anchor.parts
            pot = weight_bar([0.4, 0.25, 0.2, 0.15], width=5, height=0.6).shift(UP * 0.9)
            fee = pill("fee", RED, SMALL, 0.15).next_to(pot, RIGHT, buff=0.4)
            self.play(FadeIn(pot, fee), run_time=0.5)
            n.until("hand-coded decision layer")
            hc = pill("hand-coded rules", GREY, SMALL, 0.15).next_to(pot, LEFT, buff=0.4)
            hcx = cross(hc)
            self.play(FadeIn(hc), Create(hcx), run_time=0.6)
            n.until("The approach is")
            self.play(FadeOut(pot, fee, hc, hcx), FadeIn(anchor), run_time=1.0)
            n.until("outputs portfolio weights")
            ob = SurroundingRectangle(k["out"], color=YELLOW, buff=0.15)
            self.play(Create(ob), run_time=0.6)
            n.until("gradient ascent")
            up = Arrow(k["net"].get_bottom() + DOWN * 1.2, k["net"].get_bottom() + DOWN * 0.15, color=GREEN, buff=0, stroke_width=8)
            ul = label("reward ↑", SMALL, GREEN).next_to(up, RIGHT, buff=0.15)
            self.play(GrowArrow(up), FadeIn(ul), FadeOut(ob), run_time=0.6)
            n.until("computed exactly")
            gb = SurroundingRectangle(k["grid"], color=WHITE, buff=0.1)
            self.play(Create(gb), FadeOut(up, ul), run_time=0.6)
            self.play(FadeOut(gb), run_time=0.4)
            n.until("identical weight-sharing evaluators")
            self.play(Indicate(k["net"], color=WHITE, scale_factor=1.05), run_time=1.0)
            n.until("joined by a softmax")
            self.play(Indicate(k["soft"], color=WHITE, scale_factor=1.2), run_time=0.8)
            n.until("memory of past allocations")
            self.play(Indicate(k["prev"], color=GREEN, scale_factor=1.3), Indicate(k["a_prev"], color=GREEN), run_time=1.0)
            n.until("online mini-batch")
            tl = VGroup(*[Square(0.2, color=GREEN, fill_opacity=0.4, fill_color=GREEN) for _ in range(10)]).arrange(RIGHT, buff=0.05).next_to(k["grid"], UP, buff=0.5)
            self.play(LaggedStart(*[GrowFromCenter(s) for s in tl], lag_ratio=0.08), run_time=0.8)
            n.until("four and forty seven")
            res = VGroup(label("4×", HEADING, BLUE), label("to", BODY, GREY), label("47×", HEADING, BLUE)).arrange(RIGHT, buff=0.3).move_to([-4.6, -2.3, 0])
            rl = label("three 50-day back-tests", SMALL, GREY).next_to(res, DOWN, buff=0.1)
            self.play(FadeIn(res, rl), run_time=0.7)
            downs = VGroup(pill("zero slippage", RED, SMALL, 0.12), pill("one booming market", RED, SMALL, 0.12), pill("one run per window", RED, SMALL, 0.12)).arrange(RIGHT, buff=0.2).move_to([2.5, -2.6, 0])
            for phrase, d in zip(("zero slippage", "single booming market", "one run each"), downs):
                n.until(phrase)
                self.play(FadeIn(d), run_time=0.5)
            n.until("transaction cost derivation")
            mu = pill("μ", YELLOW, SMALL, 0.15).next_to(k["out"], UP, buff=0.3)
            self.play(FadeIn(mu), run_time=0.5)
            n.until("network layouts")
            self.play(Indicate(k["net"], color=WHITE, scale_factor=1.05), run_time=0.8)
            n.until("upper bound")
            final = label("upper bound, not an expectation", BODY, YELLOW).to_edge(DOWN, buff=0.25)
            self.play(FadeIn(final), run_time=0.6)
            self.hold(n, 1.0)
            self.clear_all(1.0)

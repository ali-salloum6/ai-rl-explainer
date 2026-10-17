from common import *

# ---------------------------------------------------------------- the real curve y^2 = x^3 - 3x + 3
CA, CB = -3.0, 3.0
Y_MAX = 4.0


def f(x):
    return x ** 3 + CA * x + CB


X0 = float(min(r.real for r in np.roots([1, 0, CA, CB]) if abs(r.imag) < 1e-9))
X_TOP = float(max(r.real for r in np.roots([1, 0, CA, CB - Y_MAX ** 2]) if abs(r.imag) < 1e-9))


def ec_add(p, q):
    (x1, y1), (x2, y2) = p, q
    if abs(x1 - x2) < 1e-12:
        lam = (3 * x1 * x1 + CA) / (2 * y1)
    else:
        lam = (y2 - y1) / (x2 - x1)
    x3 = lam * lam - x1 - x2
    return (x3, lam * (x1 - x3) - y1)


P1 = (-0.96, float(np.sqrt(f(-0.96))))
Q1 = (1.05, -float(np.sqrt(f(1.05))))
SUM = ec_add(P1, Q1)                     # P + Q
THIRD = (SUM[0], -SUM[1])                # third intersection of the secant
MULT = {1: P1}
for _k in range(2, 14):
    MULT[_k] = ec_add(MULT[_k - 1], P1)  # kP over the reals
HOPS_IN_VIEW = [k for k in range(5, 14) if abs(MULT[k][1]) < 3.6 and X0 <= MULT[k][0] < 3.0]

# ---------------------------------------------------------------- the same curve mod 79
FP = 79
FF_PTS = [(x, y) for x in range(FP) for y in range(FP) if (y * y - (x ** 3 - 3 * x + 3)) % FP == 0]


def ff_add(p, q):
    if p is None:
        return q
    if q is None:
        return p
    (x1, y1), (x2, y2) = p, q
    if x1 == x2 and (y1 + y2) % FP == 0:
        return None
    if p == q:
        lam = (3 * x1 * x1 - 3) * pow(2 * y1, -1, FP) % FP
    else:
        lam = (y2 - y1) * pow(x2 - x1, -1, FP) % FP
    x3 = (lam * lam - x1 - x2) % FP
    return (x3, (lam * (x1 - x3) - y1) % FP)


G_FF = (29, 17)
D_SECRET = 25
FF_MULT = [G_FF]
for _ in range(D_SECRET - 1):
    FF_MULT.append(ff_add(FF_MULT[-1], G_FF))
Q_FF = FF_MULT[-1]

# ---------------------------------------------------------------- P-256 domain parameters
P256 = {
    "p": 2 ** 256 - 2 ** 224 + 2 ** 192 + 2 ** 96 - 1,
    "b": 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B,
    "Gx": 0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296,
    "Gy": 0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5,
    "n": 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551,
}
assert (P256["Gy"] ** 2 - (P256["Gx"] ** 3 - 3 * P256["Gx"] + P256["b"])) % P256["p"] == 0


def hex_abbrev(n: int, head=2, tail=1) -> str:
    groups = hexgroups(f"{n:064X}").split()
    return " ".join(groups[:head]) + " … " + " ".join(groups[-tail:])


# A sample 256-bit private key, shown only to illustrate its size.
D_SAMPLE = int.from_bytes(__import__("hashlib").sha256(b"an example private key").digest(), "big") % P256["n"]

RIGHT_X = 3.35  # centre of the right-hand text column


def glow_dot(pos, color, r=0.085):
    return VGroup(Dot(pos, radius=r * 2.1, color=color, fill_opacity=0.22), Dot(pos, radius=r, color=color))


def clipped_line(axes, p, q, color=FG, width=3, opacity=0.9, x_rng=(-3.0, 3.5), y_rng=(-4.0, 4.0)):
    """Segment of the infinite line through p and q that lies inside the axes box."""
    (x1, y1), (x2, y2) = p, q
    dx, dy = x2 - x1, y2 - y1
    lo, hi = -1e9, 1e9
    for p0, d, (mn, mx) in ((x1, dx, x_rng), (y1, dy, y_rng)):
        if abs(d) < 1e-12:
            continue
        t1, t2 = (mn - p0) / d, (mx - p0) / d
        lo, hi = max(lo, min(t1, t2)), min(hi, max(t1, t2))
    a = axes.c2p(x1 + lo * dx, y1 + lo * dy)
    b = axes.c2p(x1 + hi * dx, y1 + hi * dy)
    return Line(a, b, stroke_color=color, stroke_width=width, stroke_opacity=opacity)


def num_badge(n, color=CLAUDE):
    c = Circle(radius=0.2, stroke_color=color, stroke_width=2, fill_color=FAINT, fill_opacity=1)
    return VGroup(c, Mono(str(n), 22, color, weight=BOLD).move_to(c))


class EllipticCurves(VOScene):
    def make_axes(self):
        axes = Axes(x_range=[-3, 3.5, 1], y_range=[-4, 4, 1], x_length=5.33, y_length=6.56, tips=False,
                    axis_config={"color": DIM, "stroke_width": 2, "include_ticks": True, "tick_size": 0.05})
        axes.move_to(LEFT * 3.3 + DOWN * 0.2)
        tmax = np.sqrt(X_TOP - X0)
        curve = ParametricFunction(
            lambda t: axes.c2p(X0 + t * t, np.sign(t) * np.sqrt(max(f(X0 + t * t), 0.0))),
            t_range=[-tmax, tmax, 0.004], stroke_color=BLUE, stroke_width=5)
        return axes, curve

    def construct(self):
        self.chapter(3, "Elliptic curves")
        P = lambda pt: self.axes.c2p(*pt)

        # ---------------------------------------------------------- e1: the equation and its shape
        with self.vo("e1") as v:
            title = B("elliptic curve", 64, BLUE).move_to(UP * 1.6)
            self.play(FadeIn(title, shift=0.15 * UP), run_time=0.8)
            eq = M(r"y^2 = x^3 + {{a}}x + {{b}}", size=88, colors={"a": TEAL, "b": YELLOW}).move_to(DOWN * 0.1)
            v.wait_until("eq", offset=-0.2)
            self.play(Write(eq), run_time=1.6)
            ell = Ellipse(width=2.4, height=1.3, stroke_color=MUTED, stroke_width=5)
            cross = cross_mark(RED, 1.2, 10).move_to(ell)
            not_lab = label("not an ellipse", 30, RED).next_to(ell, DOWN, buff=0.25)
            g_ell = VGroup(ell, cross, not_lab).move_to(DOWN * 2.45)
            v.wait_until("shape", offset=-0.2)
            self.play(Create(ell), run_time=0.6)
            self.play(Create(cross), FadeIn(not_lab, shift=0.1 * UP), run_time=0.5)

            self.axes, curve = self.make_axes()
            axes = self.axes
            eq_r = M(r"y^2 = x^3 - 3x + 3", size=50).move_to(RIGHT * RIGHT_X + UP * 3.05)
            ab = label("a = −3,  b = 3", 28).next_to(eq_r, DOWN, buff=0.2)
            v.wait_until("draw", offset=-0.4)
            self.play(FadeOut(VGroup(title, g_ell)), eq.animate.scale(0.57).move_to(eq_r), run_time=0.7)
            self.play(TransformMatchingShapes(eq, eq_r), FadeIn(ab), Create(axes), run_time=0.7)
            self.play(Create(curve), run_time=1.5, rate_func=smooth)

        # ---------------------------------------------------------- e2: P + Q
        with self.vo("e2") as v:
            head = B("Adding two points", 40).move_to(RIGHT * RIGHT_X + UP * 1.75)
            self.play(FadeIn(head, shift=0.1 * UP), run_time=0.6)
            dp, dq = glow_dot(P(P1), YELLOW), glow_dot(P(Q1), PINK)
            lp = M("P", size=44, color=YELLOW).next_to(dp, UL, buff=0.05)
            lq = M("Q", size=44, color=PINK).next_to(dq, LEFT, buff=0.15)
            v.wait_until("pq", offset=-0.2)
            self.play(FadeIn(dp, scale=0.5), FadeIn(lp), run_time=0.45)
            self.play(FadeIn(dq, scale=0.5), FadeIn(lq), run_time=0.45)

            steps = VGroup()
            for i, txt in enumerate(["Line through P and Q", "It hits the curve again", "Reflect across the x-axis"]):
                row = VGroup(num_badge(i + 1), T(txt, 30)).arrange(RIGHT, buff=0.25)
                steps.add(row)
            steps.arrange(DOWN, aligned_edge=LEFT, buff=0.42).next_to(head, DOWN, buff=0.55)
            steps.set_x(RIGHT_X)
            secant = clipped_line(axes, P1, Q1, FG, 3, 0.85)
            v.wait_until("line", offset=-0.2)
            self.play(Create(secant), FadeIn(steps[0], shift=0.1 * RIGHT), run_time=0.9)

            ring = Circle(radius=0.13, stroke_color=FG, stroke_width=3).move_to(P(THIRD))
            dthird = Dot(P(THIRD), radius=0.075, color=FG)
            v.wait_until("third", offset=-0.2)
            self.play(FadeIn(dthird, scale=0.5), Create(ring), FadeIn(steps[1], shift=0.1 * RIGHT), run_time=0.6)
            self.play(Flash(P(THIRD), color=FG, line_length=0.18, flash_radius=0.25), run_time=0.5)

            refl = DashedLine(P(THIRD), P(SUM), stroke_color=MUTED, stroke_width=3, dash_length=0.12)
            dsum = glow_dot(P(SUM), GREEN)
            lsum = M("P+Q", size=44, color=GREEN).next_to(dsum, LEFT, buff=0.15)
            v.wait_until("reflect", offset=-0.2)
            self.play(Create(refl), FadeIn(steps[2], shift=0.1 * RIGHT), run_time=0.8)
            self.play(TransformFromCopy(dthird, dsum), run_time=0.6)
            res = M(r"\Rightarrow\ P + Q", size=46, color=GREEN).next_to(steps, DOWN, buff=0.5).set_x(RIGHT_X)
            v.wait_until("sum", offset=-0.2)
            self.play(FadeIn(lsum, shift=0.1 * DOWN), FadeIn(res, shift=0.1 * UP), run_time=0.6)

        # ---------------------------------------------------------- e3: doubling
        with self.vo("e3") as v:
            P2 = MULT[2]
            T2 = (P2[0], -P2[1])
            head2 = B("Doubling: P + P", 40).move_to(head)
            self.play(FadeOut(VGroup(dq, lq, secant, ring, dthird, refl, dsum, lsum, steps, res)),
                      FadeOut(head, shift=0.15 * UP), FadeIn(head2, shift=0.15 * UP), run_time=0.6)
            tangent = clipped_line(axes, P1, (P1[0] + 1.0, P1[1] + (3 * P1[0] ** 2 + CA) / (2 * P1[1])), ORANGE, 3, 0.9)
            tan_txt = VGroup(num_badge(1, ORANGE), T("Tangent line at P", 30)).arrange(RIGHT, buff=0.25)
            tan_txt.next_to(head2, DOWN, buff=0.55).set_x(RIGHT_X)
            v.wait_until("tangent", offset=-0.2)
            self.play(Create(tangent), FadeIn(tan_txt, shift=0.1 * RIGHT), run_time=0.8)
            dt2 = Dot(P(T2), radius=0.075, color=FG)
            self.play(FadeIn(dt2, scale=0.5), Flash(P(T2), color=FG, line_length=0.15, flash_radius=0.22), run_time=0.5)
            refl2 = DashedLine(P(T2), P(P2), stroke_color=MUTED, stroke_width=3, dash_length=0.12)
            d2 = glow_dot(P(P2), ORANGE)
            l2 = M("2P", size=44, color=ORANGE).next_to(d2, RIGHT, buff=0.15)
            two_txt = VGroup(num_badge(2, ORANGE), T("Reflect", 30), M(r"\Rightarrow 2P", size=40, color=ORANGE))
            two_txt.arrange(RIGHT, buff=0.25).next_to(tan_txt, DOWN, buff=0.42, aligned_edge=LEFT)
            v.wait_until("twoP", offset=-0.3)
            self.play(Create(refl2), FadeIn(two_txt, shift=0.1 * RIGHT), run_time=0.5)
            self.play(TransformFromCopy(dt2, d2), FadeIn(l2), run_time=0.5)

        # ---------------------------------------------------------- e4: a real addition; 3P, 4P, ...
        with self.vo("e4") as v:
            head3 = B("It really is addition", 40).move_to(head2)
            self.play(FadeOut(VGroup(tangent, dt2, refl2, tan_txt, two_txt)), FadeOut(head2, shift=0.15 * UP),
                      FadeIn(head3, shift=0.15 * UP), run_time=0.6)
            rows = [
                (r"P + \mathcal{O} = P", "a zero: the “point at infinity”"),
                (r"P + (-P) = \mathcal{O}", "every point has a negative"),
                (r"P + Q = Q + P", "order doesn't matter"),
            ]
            chips = VGroup()
            for tex, txt in rows:
                chips.add(VGroup(M(tex, size=44), label(txt, 28, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.12))
            chips.arrange(DOWN, aligned_edge=LEFT, buff=0.38).next_to(head3, DOWN, buff=0.5).set_x(RIGHT_X)
            neg = (P1[0], -P1[1])
            dneg = Dot(P(neg), radius=0.075, color=YELLOW, fill_opacity=0.0).set_stroke(YELLOW, 3)
            lneg = M("-P", size=40, color=YELLOW).next_to(dneg, LEFT, buff=0.12)
            vline = DashedLine(P((P1[0], 3.9)), P((P1[0], -3.9)), stroke_color=YELLOW, stroke_width=2,
                               stroke_opacity=0.6, dash_length=0.1)
            v.wait_until("props", offset=-0.2)
            self.play(FadeIn(chips[0], shift=0.1 * RIGHT), run_time=0.5)
            self.wait(1.2)
            self.play(FadeIn(chips[1], shift=0.1 * RIGHT), Create(vline), FadeIn(dneg), FadeIn(lneg), run_time=0.7)
            self.wait(1.1)
            self.play(FadeIn(chips[2], shift=0.1 * RIGHT), run_time=0.5)

            hops = VGroup()
            prev = MULT[2]
            dots_k = {}
            for k, mark, lab_dir in ((3, "p3", RIGHT), (4, "p4", LEFT)):
                pt = MULT[k]
                arc = CurvedArrow(P(prev), P(pt), angle=-PI / 3, color=ORANGE, stroke_width=3, tip_length=0.16)
                dk = glow_dot(P(pt), ORANGE)
                lk = M(f"{k}P", size=40, color=ORANGE).next_to(dk, lab_dir, buff=0.15)
                dots_k[k] = VGroup(dk, lk)
                hops.add(arc)
                v.wait_until(mark, offset=-0.25)
                if k == 3:
                    self.play(FadeOut(VGroup(vline, dneg, lneg)), Create(arc), FadeIn(dk, scale=0.5), FadeIn(lk),
                              run_time=0.55)
                else:
                    self.play(Create(arc), FadeIn(dk, scale=0.5), FadeIn(lk), run_time=0.55)
                prev = pt
            v.wait_until("leap", offset=-0.2)
            extra = VGroup()
            anims = []
            for k in HOPS_IN_VIEW:
                pt = MULT[k]
                arc = ArcBetweenPoints(P(prev), P(pt), angle=-PI / 3, stroke_color=ORANGE, stroke_width=2,
                                       stroke_opacity=0.6)
                dk = Dot(P(pt), radius=0.06, color=ORANGE)
                extra.add(arc, dk)
                anims.append(Succession(Create(arc, run_time=0.25), FadeIn(dk, scale=0.4, run_time=0.12)))
                prev = pt
            self.play(Succession(*anims), run_time=0.37 * len(anims))

        # ---------------------------------------------------------- e5: double-and-add
        with self.vo("e5") as v:
            curve_grp = VGroup(axes, curve, dp, lp, d2, l2, dots_k[3], dots_k[4], hops, extra)
            self.play(FadeOut(curve_grp, shift=0.3 * LEFT), FadeOut(VGroup(head3, chips, eq_r, ab)), run_time=0.7)
            big = M(r"10^{15} \cdot P", size=72).move_to(UP * 2.75)
            quad = label("a quadrillion times P", 28).next_to(big, DOWN, buff=0.15)
            self.play(FadeIn(big, shift=0.1 * DOWN), FadeIn(quad), run_time=0.7)

            names = ["P", "2P", "4P", "8P", "16P", r"\cdots", r"2^{49}P"]
            chain = VGroup()
            for i, nm in enumerate(names):
                chain.add(M(nm, size=46, color=ORANGE if i else YELLOW))
            chain.arrange(RIGHT, buff=1.05).move_to(UP * 0.85)
            arrows, x2s = VGroup(), VGroup()
            for a_, b_ in zip(chain[:-1], chain[1:]):
                ar = Arrow(a_.get_right(), b_.get_left(), buff=0.15, stroke_width=3, color=MUTED,
                           max_tip_length_to_length_ratio=0.3, tip_length=0.16)
                arrows.add(ar)
                x2s.add(Mono("×2", 26, MUTED).next_to(ar, UP, buff=0.06))
            v.wait_until("dbl", offset=-0.2)
            self.play(FadeIn(chain[0]), run_time=0.2)
            for i in range(len(arrows)):
                self.play(GrowArrow(arrows[i]), FadeIn(x2s[i]), FadeIn(chain[i + 1], shift=0.1 * RIGHT), run_time=0.27)

            bits = f"{10 ** 15:b}"
            bit_row = Mono(bits, 26, MUTED).move_to(DOWN * 0.45)
            if bit_row.width > 12.6:
                bit_row.scale_to_fit_width(12.6)
            bit_lab = label("10¹⁵ in binary: for every bit, double; for every 1, also add P", 26)
            bit_lab.next_to(bit_row, DOWN, buff=0.22)
            self.play(FadeIn(bit_row), FadeIn(bit_lab), run_time=0.5)
            ones = [i for i, ch in enumerate(bits) if ch == "1"]
            self.play(LaggedStart(*[bit_row[i].animate.set_color(ORANGE) for i in ones], lag_ratio=0.12), run_time=1.0)

            good = VGroup(check_mark(GREEN, 0.45, 8), B("49 doublings + 19 additions", 36, GREEN)).arrange(RIGHT, buff=0.25)
            bad_t = B("1,000,000,000,000,000 additions", 36, RED)
            bad = VGroup(cross_mark(RED, 0.4, 8), bad_t).arrange(RIGHT, buff=0.25)
            cmp_ = VGroup(good, bad).arrange(DOWN, buff=0.35, aligned_edge=LEFT).move_to(DOWN * 2.55)
            strike = Line(bad_t.get_left(), bad_t.get_right(), stroke_color=RED, stroke_width=4)
            v.wait_until("fifty", offset=-0.2)
            self.play(FadeIn(good, shift=0.1 * UP), run_time=0.6)
            self.play(FadeIn(bad, shift=0.1 * UP), run_time=0.6)
            self.play(Create(strike), run_time=0.4)
            self.wait(0.8)
            self.play(Indicate(good, color=GREEN, scale_factor=1.06), run_time=0.9)

        # ---------------------------------------------------------- e6: modulo a prime
        with self.vo("e6") as v:
            axes2, curve2 = self.make_axes()
            eq_real = M(r"y^2 = x^3 - 3x + 3", size=50).move_to(RIGHT * RIGHT_X + UP * 3.05)
            self.play(FadeOut(VGroup(big, quad, chain, arrows, x2s, bit_row, bit_lab, cmp_, strike)),
                      FadeIn(VGroup(axes2, curve2), shift=0.3 * RIGHT), FadeIn(eq_real), run_time=0.9)
            eq_mod = M(r"y^2 \equiv x^3 - 3x + 3 \pmod{79}", size=46).move_to(eq_real).set_x(RIGHT_X)
            p_lab = label("79 is a prime", 28).next_to(eq_mod, DOWN, buff=0.2)
            v.wait_until("mod", offset=-0.2)
            self.play(TransformMatchingShapes(eq_real, eq_mod), run_time=0.9)
            self.play(FadeIn(p_lab), run_time=0.4)

            side = 6.45
            frame = Square(side, stroke_color=DIM, stroke_width=2).move_to(LEFT * 3.3 + DOWN * 0.2)
            o = frame.get_corner(DL)
            step = side / (FP - 1)
            ff = lambda pt: o + RIGHT * pt[0] * step + UP * pt[1] * step
            self.ff = ff
            ticks = VGroup(Mono("0", 22, MUTED).next_to(o, DL, buff=0.08),
                           Mono("78", 22, MUTED).next_to(frame.get_corner(DR), DOWN, buff=0.1),
                           Mono("78", 22, MUTED).next_to(frame.get_corner(UL), LEFT, buff=0.1),
                           M("x", size=34, color=MUTED).next_to(frame, DOWN, buff=0.12),
                           M("y", size=34, color=MUTED).next_to(frame, LEFT, buff=0.15))
            src = [curve2.point_from_proportion(i / (len(FF_PTS) - 1)) for i in range(len(FF_PTS))]
            src.sort(key=lambda q: (q[1], q[0]))
            tgt = sorted(FF_PTS, key=lambda q: (q[1], q[0]))
            particles = VGroup(*[Dot(s, radius=0.055, color=BLUE) for s in src])
            ff_dots = VGroup(*[Dot(ff(q), radius=0.055, color=BLUE) for q in tgt])
            self.ff_index = {q: i for i, q in enumerate(tgt)}
            v.wait_until("cloud", offset=-0.2)
            self.play(FadeIn(particles, run_time=0.4), curve2.animate(run_time=0.6).set_stroke(opacity=0.0))
            self.play(LaggedStart(*[p.animate.move_to(ff_dots[i].get_center()) for i, p in enumerate(particles)],
                                  lag_ratio=0.01),
                      FadeOut(axes2), FadeIn(frame), FadeIn(ticks), run_time=2.0)
            self.remove(curve2)
            count = label("82 points  +  the point at infinity", 26).next_to(frame, UP, buff=0.12)
            self.play(FadeIn(count), run_time=0.4)

            fh = B("Same formulas, mod 79", 36).move_to(RIGHT * RIGHT_X + UP * 1.35)
            forms = VGroup(
                M(r"\lambda = \frac{y_2 - y_1}{x_2 - x_1}", size=42),
                M(r"x_3 = \lambda^2 - x_1 - x_2", size=42),
                M(r"y_3 = \lambda\,(x_1 - x_3) - y_1", size=42),
            ).arrange(DOWN, buff=0.3, aligned_edge=LEFT).next_to(fh, DOWN, buff=0.4).set_x(RIGHT_X)
            div = label("(dividing means multiplying\nby an inverse, mod 79)", 26).next_to(forms, DOWN, buff=0.3)
            div.set_x(RIGHT_X)
            v.wait_until("same", offset=-0.2)
            self.play(FadeIn(fh, shift=0.1 * UP), LaggedStart(*[FadeIn(m, shift=0.1 * RIGHT) for m in forms],
                                                             lag_ratio=0.3), run_time=1.1)
            self.play(FadeIn(div), run_time=0.4)

        # ---------------------------------------------------------- e7: Q = d * G
        with self.vo("e7") as v:
            self.play(FadeOut(VGroup(fh, forms, div)), run_time=0.4)
            gpos = ff(G_FF)
            dG = glow_dot(gpos, PURPLE, 0.075)
            lG = M("G", size=46, color=PURPLE).next_to(dG, DOWN, buff=0.1)
            g_txt = VGroup(MT(f'{span("G", PURPLE, True)} = the base point', 36),
                           label("everyone agrees on it", 26)).arrange(DOWN, buff=0.12)
            g_txt.move_to(RIGHT * RIGHT_X + UP * 1.55)
            v.wait_until("G", offset=-0.2)
            self.play(FadeIn(dG, scale=0.4), FadeIn(lG), FadeIn(g_txt, shift=0.1 * UP), run_time=0.6)

            lock = icon_padlock(GOLD, 0.5)
            d_val = M(r"{{d}} = 25", size=60, colors={"d": GOLD})
            d_row = VGroup(d_val, lock, label("secret", 28, GOLD)).arrange(RIGHT, buff=0.25)
            d_row.next_to(g_txt, DOWN, buff=0.4).set_x(RIGHT_X)
            v.wait_until("d", offset=-0.2)
            self.play(FadeIn(d_row, shift=0.1 * UP), run_time=0.6)

            q_eq = M(r"{{Q}} = {{d}} \cdot {{G}}", size=60, colors=VAR_COLORS).next_to(d_row, DOWN, buff=0.35)
            q_eq.set_x(RIGHT_X)
            trail = VGroup()
            hop_anims = []
            for a_, b_ in zip(FF_MULT[:-1], FF_MULT[1:]):
                seg = Line(ff(a_), ff(b_), stroke_color=PURPLE, stroke_width=2, stroke_opacity=0.55)
                trail.add(seg)
                hop_anims.append(Create(seg))
            hopper = Dot(gpos, radius=0.09, color=YELLOW)
            v.wait_until("Q", offset=-0.2)
            self.play(FadeIn(q_eq, shift=0.1 * UP), FadeIn(hopper), run_time=0.35)
            for seg, b_ in zip(trail, FF_MULT[1:]):
                self.play(Create(seg), hopper.animate.move_to(ff(b_)), run_time=1 / 15, rate_func=linear)
            dQ = glow_dot(ff(Q_FF), BLUE, 0.075)
            lQ = M("Q", size=46, color=BLUE).next_to(dQ, UP, buff=0.1)
            self.play(FadeOut(hopper), FadeIn(dQ, scale=0.4), FadeIn(lQ), trail.animate.set_stroke(opacity=0.25),
                      run_time=0.35)

            ds = str(D_SAMPLE)
            real_lab = label(f"a real private key d ({len(ds)} digits):", 26)
            d_lines = VGroup(*[Mono(ds[i:i + 26], 26, GOLD) for i in range(0, len(ds), 26)])
            d_lines.arrange(DOWN, buff=0.1, aligned_edge=LEFT)
            d_blk = VGroup(real_lab, d_lines).arrange(DOWN, buff=0.18, aligned_edge=LEFT).next_to(q_eq, DOWN, buff=0.4)
            d_blk.set_x(RIGHT_X)
            v.wait_until("digits", offset=-0.2)
            self.play(FadeIn(real_lab), LaggedStart(*[FadeIn(l, shift=0.05 * RIGHT) for l in d_lines], lag_ratio=0.3),
                      run_time=0.8)
            steps_t = MT(f'{span("→", GREEN)} {span("~256 doublings + additions", GREEN, True)}', 30)
            steps_t.next_to(d_blk, DOWN, buff=0.3).set_x(RIGHT_X)
            v.wait_until("steps", offset=-0.2)
            self.play(FadeIn(steps_t, shift=0.1 * UP), run_time=0.6)

        # ---------------------------------------------------------- e8: going back is hopeless
        with self.vo("e8") as v:
            self.play(FadeOut(VGroup(g_txt, d_row, d_blk, steps_t)), q_eq.animate.move_to(RIGHT * RIGHT_X + UP * 1.6),
                      run_time=0.5)
            back = CurvedArrow(dQ.get_center(), dG.get_center(), angle=PI / 3, color=RED, stroke_width=5,
                               tip_length=0.25)
            qmark = B("?", 64, RED).move_to(back.point_from_proportion(0.5) + UL * 0.35)
            q2d = M(r"{{Q}} \;\longrightarrow\; {{d}}\,?", size=60, colors={"Q": BLUE, "d": GOLD})
            q2d.move_to(RIGHT * RIGHT_X + UP * 0.6)
            ecdlp = T("Elliptic Curve\nDiscrete Logarithm Problem", 32, RED, weight=BOLD, line_spacing=0.9)
            ecdlp.next_to(q2d, DOWN, buff=0.35).set_x(RIGHT_X)
            v.wait_until("ecdlp")
            self.play(Create(back), FadeIn(qmark, scale=0.5), run_time=0.8)
            self.play(FadeIn(q2d, shift=0.1 * UP), run_time=0.5)
            self.play(FadeIn(ecdlp, shift=0.1 * UP), run_time=0.6)
            toy = label("only 83 points here: just try them all", 26).next_to(ecdlp, DOWN, buff=0.4).set_x(RIGHT_X)
            self.wait(0.8)
            self.play(FadeIn(toy), run_time=0.5)

            tag = pill("ECDLP", RED, size=26)
            top = VGroup(q2d.copy(), tag).arrange(RIGHT, buff=0.35).move_to(RIGHT * RIGHT_X + UP * 1.75)
            p256 = MT(f'{span("P-256", BLUE, True)}: about 10<sup>77</sup> points', 34)
            att = MT(f'best attack: about {span("2<sup>128</sup>", YELLOW, True)} steps', 34)
            digits = f"{2 ** 128:,}"
            cut = digits.index(",", len(digits) // 2 - 2) + 1
            big = VGroup(Mono(digits[:cut], 24, YELLOW), Mono(digits[cut:], 24, YELLOW)).arrange(DOWN, buff=0.08)
            col = VGroup(p256, att, big).arrange(DOWN, buff=0.24).next_to(top, DOWN, buff=0.4).set_x(RIGHT_X)
            v.wait_until("twoto", offset=-0.6)
            self.play(FadeOut(VGroup(q_eq, toy, ecdlp)), q2d.animate.move_to(top[0]), FadeIn(tag, shift=0.1 * LEFT),
                      run_time=0.6)
            self.play(FadeIn(p256, shift=0.1 * UP), run_time=0.45)
            self.play(FadeIn(att, shift=0.1 * UP), run_time=0.45)
            self.play(LaggedStart(*[AddTextLetterByLetter(l, time_per_char=0.02) for l in big], lag_ratio=0.5),
                      run_time=1.0)

            calc = MT(f'10<sup>9</sup> computers × 10<sup>9</sup> steps/s', 32, FG)
            yrs = B("≈ 10 trillion years", 46, RED)
            uni = label("≈ 780 × the age of the universe", 28)
            blk = VGroup(calc, yrs, uni).arrange(DOWN, buff=0.18).next_to(big, DOWN, buff=0.4).set_x(RIGHT_X)
            v.wait_until("years", offset=-0.2)
            self.play(FadeIn(calc, shift=0.1 * UP), run_time=0.6)
            self.play(FadeIn(yrs, scale=0.8), run_time=0.6)
            self.play(FadeIn(uni), run_time=0.4)
            self.wait(1.0)
            self.play(Wiggle(qmark, scale_value=1.25), Indicate(yrs, color=RED, scale_factor=1.05), run_time=1.0)

        # ---------------------------------------------------------- e9: keys and the public standard
        with self.vo("e9") as v:
            self.play(FadeOut(VGroup(back, qmark, q2d, tag, p256, att, big, calc, yrs, uni)), run_time=0.5)
            k_priv = VGroup(M(r"{{d}}", size=64, colors=VAR_COLORS), icon_key(GOLD, 1.0),
                            B("private key", 40, GOLD)).arrange(RIGHT, buff=0.35)
            k_pub = VGroup(M(r"{{Q}}", size=64, colors=VAR_COLORS), icon_key(BLUE, 1.0),
                           B("public key", 40, BLUE)).arrange(RIGHT, buff=0.35)
            keys = VGroup(k_priv, k_pub).arrange(DOWN, buff=0.7, aligned_edge=LEFT).move_to(RIGHT * RIGHT_X + UP * 0.6)
            sub_priv = label("keep it secret", 26).next_to(k_priv, DOWN, buff=0.12, aligned_edge=LEFT).shift(RIGHT * 0.75)
            sub_pub = label("share it with the world", 26).next_to(k_pub, DOWN, buff=0.12, aligned_edge=LEFT).shift(RIGHT * 0.75)
            v.wait_until("priv")
            self.play(FadeIn(k_priv, shift=0.1 * UP), FadeIn(sub_priv), run_time=0.6)
            v.wait_until("pub", offset=-0.2)
            self.play(FadeIn(k_pub, shift=0.1 * UP), FadeIn(sub_pub), Indicate(dQ, color=BLUE, scale_factor=1.6),
                      run_time=0.7)

            plot = VGroup(frame, ticks, particles, count, trail, dG, lG, dQ, lQ, eq_mod, p_lab)
            v.wait_until("params", offset=-0.3)
            self.play(FadeOut(plot), FadeOut(VGroup(keys, sub_priv, sub_pub)), run_time=0.6)
            rows_spec = [
                ("p", "FFFFFFFF 00000001 … FFFFFFFF", "the prime"),
                ("a", "-3", ""),
                ("b", "5AC635D8 AA3A93E7 … 27D2604B", ""),
                ("G", "(6B17D1F2 …,  4FE342E2 …)", "the base point"),
                ("n", "FFFFFFFF 00000000 … FC632551", "number of points"),
            ]
            assert hexgroups(f"{P256['b']:064X}").startswith("5AC635D8 AA3A93E7")
            assert f"{P256['n']:064X}".endswith("FC632551") and f"{P256['Gy']:064X}".startswith("4FE342E2")
            rows = VGroup()
            for name, val, note in rows_spec:
                nm = M(name, size=48, color=YELLOW if name == "b" else VAR_COLORS.get(name, FG))
                eqs = M("=", size=42, color=MUTED)
                vt = Mono(val, 30, FG)
                row = VGroup(nm, eqs, vt)
                if note:
                    row.add(label(note, 28))
                rows.add(row)
            name_x = -5.3
            for r in rows:
                r[0].set_x(name_x)
                r[1].set_x(name_x + 0.6)
                r[2].next_to(r[1], RIGHT, buff=0.3)
                if len(r) > 3:
                    r[3].next_to(r[2], RIGHT, buff=0.4)
            rows.arrange(DOWN, buff=0.5, aligned_edge=LEFT)
            c_title = VGroup(B("P-256", 50, BLUE), label("the public standard everyone shares", 32, FG))
            c_title.arrange(RIGHT, buff=0.4)
            content = VGroup(c_title, rows).arrange(DOWN, buff=0.55)
            card = SurroundingRectangle(content, buff=0.45, corner_radius=0.18, color=DIM, stroke_width=1.5)
            card.set_fill(PANEL, 1)
            VGroup(card, content).move_to(DOWN * 0.15)
            self.play(FadeIn(card), FadeIn(c_title, shift=0.1 * DOWN), run_time=0.6)
            for i, r in enumerate(rows):
                self.play(FadeIn(r, shift=0.1 * RIGHT), run_time=0.45)
                self.wait(0.55)

            b_row = rows[2]
            hl = SurroundingRectangle(b_row, color=YELLOW, buff=0.14, corner_radius=0.1, stroke_width=4)
            mag = icon_magnifier(YELLOW, 0.3)
            where = label("where did b\ncome from?", 28, YELLOW)
            callout = VGroup(mag, where).arrange(RIGHT, buff=0.2).next_to(hl, RIGHT, buff=0.35)
            v.wait_until("hide", offset=-0.3)
            self.play(Create(hl), b_row.animate.set_color(YELLOW), run_time=0.6)
            self.play(FadeIn(callout, shift=0.1 * LEFT), run_time=0.5)

        self.clear_all()

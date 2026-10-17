from common import *
from s01_signatures import one_way_street

P_SMALL = 101
POWERS = [(e, pow(3, e, P_SMALL)) for e in range(1, 101)]  # 3 is a primitive root mod 101

# A real example with big numbers: a 309-digit prime p, a 300-digit exponent k, r = 3^k mod p.
BIG_K = ("209419624610999602155894258313228296808917571002526782347869393785419116665376017267848259109094"
         "471104686522982005977927935259684079234000405824079898261240529069593396641909233382519926038738"
         "267972766447619724655052156821685481465952557675265463409927201676963436500626176037749437143295531176338457")
BIG_R = ("244944469511101375900855871399280680721953339167949987815848836670839440836427123759163561337246"
         "901504093770831518882976847963411679302070581855160280367579615577235199801624958878870184614880"
         "824714469670091047002810929109385162048611045842192543850237442485713213403164112184138375787764239421159422215889412")

CLOCK_C = LEFT * 3.3 + DOWN * 0.25
CLOCK_R = 2.45


def hour_dir(h: float) -> np.ndarray:
    a = PI / 2 - h * TAU / 12
    return np.array([np.cos(a), np.sin(a), 0.0])


def ring_dir(v: float, p: int = P_SMALL) -> np.ndarray:
    a = PI / 2 - v * TAU / p
    return np.array([np.cos(a), np.sin(a), 0.0])


def digit_block(digits: str, per_line=20, lines=3, size=26, color=MUTED) -> VGroup:
    rows = [digits[i * per_line:(i + 1) * per_line] for i in range(lines)]
    rows[-1] = rows[-1][:-1] + "…"
    return VGroup(*[Mono(r, size, color) for r in rows]).arrange(DOWN, buff=0.1, aligned_edge=LEFT)


def bolt(color=GREEN, h=0.4) -> Polygon:
    pts = [(0.15, 0.5), (-0.25, -0.05), (0.0, -0.05), (-0.15, -0.5), (0.25, 0.08), (0.0, 0.08)]
    return Polygon(*[np.array([x, y, 0.0]) for x, y in pts], fill_color=color, fill_opacity=1,
                   stroke_width=0).scale_to_fit_height(h)


class ClockArithmetic(VOScene):
    def construct(self):
        self.chapter(2, "Clock arithmetic")
        C, R = CLOCK_C, CLOCK_R

        # ---------------------------------------------------------- k1: the clock
        with self.vo("k1") as v:
            face = Circle(radius=R, stroke_color=FG, stroke_width=4, fill_color=PANEL, fill_opacity=1).move_to(C)
            minute_ticks = VGroup(*[Line(C + hour_dir(i / 5) * R * 0.94, C + hour_dir(i / 5) * R * 0.98,
                                         stroke_color=DIM, stroke_width=1.5) for i in range(60) if i % 5])
            ticks = VGroup(*[Line(C + hour_dir(h) * R * 0.86, C + hour_dir(h) * R * 0.98, stroke_color=FG,
                                  stroke_width=4) for h in range(12)])
            nums = VGroup(*[T(str(12 if h == 0 else h), 40, FG, weight=BOLD).move_to(C + hour_dir(h) * R * 0.72)
                            for h in range(12)])
            hand = Line(C, C + hour_dir(0) * R * 0.55, stroke_color=YELLOW, stroke_width=10)
            hub = Dot(C, radius=0.11, color=YELLOW)
            self.play(FadeIn(face), Create(ticks), FadeIn(minute_ticks), run_time=0.8)
            self.play(LaggedStart(*[FadeIn(n, scale=0.7) for n in nums], lag_ratio=0.06), FadeIn(hand), FadeIn(hub),
                      run_time=1.0)

            eq = M("9", "+", "5", "=", "14", size=84).move_to(RIGHT * 3.4 + UP * 1.2)
            eq[0].set_color(YELLOW)
            v.wait_until("nine", offset=-0.2)
            self.play(Rotate(hand, angle=PI / 2, about_point=C), nums[9].animate.set_color(YELLOW).scale(1.2),
                      FadeIn(eq[0], shift=0.1 * UP), run_time=0.7)

            trail = Arc(radius=R * 0.88, start_angle=PI / 2 - 9 * TAU / 12, angle=-5 * TAU / 12, arc_center=C,
                        stroke_color=CLAUDE, stroke_width=9)
            v.wait_until("move", offset=-0.2)
            self.play(Rotate(hand, angle=-5 * TAU / 12, about_point=C), Create(trail),
                      LaggedStart(*[Indicate(nums[h], color=CLAUDE, scale_factor=1.3) for h in (10, 11, 0, 1, 2)],
                                  lag_ratio=0.5),
                      FadeIn(eq[1:3], shift=0.1 * UP), run_time=1.4)
            v.wait_until("two", offset=-0.2)
            strike = Line(eq[4].get_corner(DL) + LEFT * 0.05, eq[4].get_corner(UR) + RIGHT * 0.05,
                          stroke_color=RED, stroke_width=7)
            two = M("2", size=84, color=GREEN).next_to(eq[4], RIGHT, buff=0.45)
            self.play(FadeIn(eq[3:5], shift=0.1 * UP), nums[2].animate.set_color(GREEN).scale(1.2), run_time=0.5)
            self.play(Create(strike), FadeIn(two, shift=0.1 * LEFT), run_time=0.6)
            v.wait_until("wrap", offset=-0.2)
            loop = Arc(radius=R * 1.13, start_angle=PI / 2 + 0.55, angle=-1.1, arc_center=C, stroke_color=CLAUDE,
                       stroke_width=6).add_tip(tip_length=0.28)
            wrap_lab = T("numbers wrap around", 38, CLAUDE).next_to(VGroup(eq, two), DOWN, buff=0.6)
            self.play(Create(loop), FadeIn(wrap_lab, shift=0.1 * UP), run_time=0.8)

        # ---------------------------------------------------------- k2: mod notation
        with self.vo("k2") as v:
            modeq = M(r"9 + 5 \equiv 2", r"\pmod{12}", size=72).move_to(RIGHT * 3.25 + UP * 1.2)
            modeq[1].set_color(CLAUDE)
            v.wait_until("eq", offset=-0.2)
            self.play(FadeOut(VGroup(eq, strike, two), shift=0.3 * UP), FadeOut(wrap_lab), run_time=0.5)
            self.play(Write(modeq), run_time=1.1)
            self.wait(1.0)
            self.play(Circumscribe(modeq[1], color=CLAUDE, buff=0.1), run_time=1.0)
            rem = M(r"14 = 1 \times 12 + ", "2", size=64).next_to(modeq, DOWN, buff=0.9)
            rem[1].set_color(YELLOW)
            box = SurroundingRectangle(rem[1], color=YELLOW, buff=0.12, corner_radius=0.08)
            rlab = T("remainder", 34, YELLOW).next_to(box, DOWN, buff=0.25)
            v.wait_until("rem", offset=-0.2)
            self.play(Write(rem), run_time=1.0)
            self.play(Create(box), FadeIn(rlab, shift=0.1 * UP), run_time=0.6)

        # ---------------------------------------------------------- k3: a prime modulus
        with self.vo("k3") as v:
            ring_ticks = VGroup(*[Line(C + ring_dir(i) * R * (0.9 if i % 10 == 0 else 0.94), C + ring_dir(i) * R * 0.99,
                                       stroke_color=FG if i % 10 == 0 else MUTED, stroke_width=3 if i % 10 == 0 else 1.5)
                                  for i in range(P_SMALL)])
            prime_lab = T("a prime instead of 12", 40, FG).move_to(RIGHT * 3.25 + UP * 1.2)
            v.wait_until("prime", offset=-0.2)
            self.play(FadeOut(VGroup(modeq, rem, box, rlab), shift=0.3 * UP), FadeOut(VGroup(nums, hand, hub, trail, loop)),
                      run_time=0.6)
            self.play(ReplacementTransform(VGroup(*ticks, *minute_ticks), ring_ticks), FadeIn(prime_lab, shift=0.1 * UP),
                      run_time=1.2)
            p_lab = M(r"p = 101", size=60, color=YELLOW).move_to(C)
            ring_nums = VGroup(*[T(str(n), 26, MUTED).move_to(C + ring_dir(n) * R * 1.13) for n in (0, 25, 50, 75)])
            v.wait_until("p", offset=-0.2)
            self.play(FadeIn(p_lab, scale=0.8), FadeIn(ring_nums), FadeOut(prime_lab), run_time=0.7)

            rows = VGroup()
            dots = VGroup()
            for e, val in POWERS[:5]:
                rhs = f"{3 ** e}" if e < 5 else r"243 \equiv 41"
                rows.add(M(f"3^{{{e}}} = {rhs}", size=52))
            rows.arrange(DOWN, buff=0.32, aligned_edge=LEFT).move_to(RIGHT * 3.0 + DOWN * 0.1)
            v.wait_until("pow", offset=-0.2)
            for i, (e, val) in enumerate(POWERS[:4]):
                d = Dot(C + ring_dir(val) * R * 0.99, radius=0.11, color=ORANGE)
                lab = T(str(val), 28, ORANGE, weight=BOLD).move_to(C + ring_dir(val) * R * 0.78)
                dots.add(VGroup(d, lab))
                self.play(FadeIn(rows[i], shift=0.1 * RIGHT), FadeIn(d, scale=2), FadeIn(lab), run_time=0.45)
                self.wait(0.55)

            v.wait_until("wrap", offset=-0.3)
            rows[4].set_color(FG)
            spiral = ParametricFunction(lambda t: C + ring_dir(t) * R * (0.55 + 0.44 * t / 243), t_range=[0, 243, 0.25],
                                        stroke_color=ORANGE, stroke_width=4, stroke_opacity=0.85)
            mover = Dot(spiral.get_start(), radius=0.12, color=YELLOW)
            first = rows[4][0][:6]  # "3^5 = 243"
            self.play(FadeIn(first, shift=0.1 * RIGHT), run_time=0.4)
            self.play(Create(spiral), MoveAlongPath(mover, spiral), run_time=2.2, rate_func=linear)
            land = VGroup(Dot(C + ring_dir(41) * R * 0.99, radius=0.13, color=YELLOW),
                          T("41", 30, YELLOW, weight=BOLD).move_to(C + ring_dir(41) * R * 0.78))
            self.play(ReplacementTransform(mover, land[0]), FadeIn(land[1]), FadeIn(rows[4][0][6:], shift=0.1 * RIGHT),
                      spiral.animate.set_stroke(opacity=0.35), run_time=0.6)
            laps = T("2 full laps + 41", 30, MUTED).next_to(rows, DOWN, buff=0.4).align_to(rows, LEFT)
            self.play(FadeIn(laps), run_time=0.4)

        # ---------------------------------------------------------- k4: plot all powers
        with self.vo("k4") as v:
            axes = Axes(x_range=[0, 100, 10], y_range=[0, 100, 25], x_length=10.4, y_length=4.9,
                        axis_config={"color": DIM, "stroke_width": 2, "include_tip": False},
                        tips=False).move_to(RIGHT * 0.45 + DOWN * 0.45)
            xl = M("k", size=44).next_to(axes.x_axis, RIGHT, buff=0.2)
            yl = M(r"3^k \bmod 101", size=40).next_to(axes.y_axis, UP, buff=0.2).shift(RIGHT * 0.6)
            ticks_lab = VGroup(*[T(str(n), 26, MUTED).next_to(axes.c2p(n, 0), DOWN, buff=0.2) for n in (0, 50, 100)],
                               *[T(str(n), 26, MUTED).next_to(axes.c2p(0, n), LEFT, buff=0.2) for n in (50, 100)])
            pts = [axes.c2p(e, val) for e, val in POWERS]
            sdots = VGroup(*[Dot(pt, radius=0.065, color=YELLOW if i < 5 else BLUE) for i, pt in enumerate(pts)])
            v.wait_until("plot", offset=-0.2)
            self.play(FadeOut(VGroup(face, ring_ticks, ring_nums, p_lab, dots, land, spiral, rows, laps)),
                      Create(axes), FadeIn(xl), FadeIn(yl), FadeIn(ticks_lab), run_time=0.7)
            self.play(LaggedStart(*[FadeIn(d, scale=2) for d in sdots], lag_ratio=0.06), run_time=1.3)
            zig = VMobject(stroke_color=BLUE, stroke_width=1.6, stroke_opacity=0.45).set_points_as_corners(pts)
            noise = B("no pattern to follow", 38, MUTED).move_to(UP * 3.05)
            v.wait_until("random", offset=-0.1)
            self.play(Create(zig), FadeIn(noise, shift=0.1 * DOWN), run_time=1.8, rate_func=linear)

        # ---------------------------------------------------------- k5: easy one way, hard the other
        with self.vo("k5") as v:
            lbox = panel(2.6, 1.6).move_to(LEFT * 4.5 + UP * 1.2)
            rbox = panel(3.5, 1.6).move_to(RIGHT * 4.1 + UP * 1.2)
            kk = M("k", size=72).move_to(lbox)
            rr = M(r"3^k \bmod p", size=58).move_to(rbox)
            fwd = Arrow(lbox.get_right() + UP * 0.38, rbox.get_left() + UP * 0.38, buff=0.15, color=GREEN, stroke_width=7,
                        max_tip_length_to_length_ratio=0.08, tip_length=0.3)
            easy = B("easy", 36, GREEN).next_to(fwd, UP, buff=0.15)
            v.wait_until("fwd", offset=0.0)
            self.play(FadeOut(VGroup(axes, xl, yl, ticks_lab, sdots, zig, noise)), run_time=0.5)
            self.play(FadeIn(lbox), FadeIn(rbox), Write(kk), Write(rr), run_time=0.7)
            self.play(GrowArrow(fwd), FadeIn(easy, shift=0.1 * DOWN), run_time=0.6)
            kblock = digit_block(BIG_K, 18).next_to(lbox, DOWN, buff=0.4)
            klab = label("k: 300 digits", 28, FG).next_to(kblock, DOWN, buff=0.2)
            rblock = digit_block(BIG_R, 18).next_to(rbox, DOWN, buff=0.4)
            rlab = label("result: 309 digits", 28, FG).next_to(rblock, DOWN, buff=0.2)
            self.play(LaggedStart(*[FadeIn(row, shift=0.1 * DOWN) for row in kblock], lag_ratio=0.25), FadeIn(klab),
                      run_time=1.0)
            pulse = Dot(fwd.get_start(), radius=0.1, color=GREEN)
            self.play(MoveAlongPath(pulse, Line(fwd.get_start(), fwd.get_end())), run_time=0.35, rate_func=rush_into)
            self.remove(pulse)
            fast = VGroup(bolt(GREEN, 0.4), B("a few milliseconds", 32, GREEN)).arrange(RIGHT, buff=0.14)
            fast.next_to(fwd, UP, buff=0.15)
            self.play(FadeIn(rblock, run_time=0.25), FadeIn(rlab), Flash(rbox.get_left(), color=GREEN, flash_radius=0.4),
                      FadeOut(easy, shift=0.1 * UP), FadeIn(fast, shift=0.1 * UP), run_time=0.5)

            bwd = Arrow(rbox.get_left() + DOWN * 0.38, lbox.get_right() + DOWN * 0.38, buff=0.15, color=RED, stroke_width=7,
                        max_tip_length_to_length_ratio=0.08, tip_length=0.3)
            qk = M("?", size=84, color=RED).move_to(lbox)
            v.wait_until("bwd", offset=-0.2)
            self.play(GrowArrow(bwd), FadeOut(kblock), FadeOut(klab), run_time=0.6)
            self.play(Transform(kk, qk), lbox.animate.set_stroke(RED, 2), run_time=0.5)
            tries = VGroup()
            trying = T("trying k = 1, 2, 3, …", 30, RED).next_to(bwd, DOWN, buff=0.35)
            bar_bg = RoundedRectangle(width=4.2, height=0.2, corner_radius=0.1, fill_color=FAINT, fill_opacity=1,
                                      stroke_color=DIM, stroke_width=1).next_to(trying, DOWN, buff=0.25)
            bar = RoundedRectangle(width=0.06, height=0.2, corner_radius=0.03, fill_color=RED, fill_opacity=1,
                                   stroke_width=0).align_to(bar_bg, LEFT).align_to(bar_bg, DOWN)
            self.play(FadeIn(trying), FadeIn(bar_bg), FadeIn(bar), run_time=0.5)
            tries.add(trying, bar_bg, bar)
            dlp = B("the discrete logarithm problem", 46, RED).move_to(DOWN * 2.85)
            v.wait_until("dlp", offset=-0.2)
            self.play(Write(dlp), bar.animate.stretch_to_fit_width(0.1, about_edge=LEFT), run_time=1.0)
            lock = icon_padlock(RED, 0.62).move_to(bwd.point_from_proportion(0.82) + UP * 0.02)
            lock_bg = Circle(radius=0.48, fill_color=BG, fill_opacity=1, stroke_color=RED, stroke_width=3).move_to(lock)
            v.wait_until("hard", offset=-0.2)
            self.play(FadeIn(lock_bg, scale=0.6), FadeIn(lock, scale=0.6), run_time=0.5)
            self.play(Indicate(dlp, color=RED, scale_factor=1.06), run_time=0.8)

        # ---------------------------------------------------------- k6: back to the street
        with self.vo("k6") as v:
            street = one_way_street(11.0).scale(0.85).move_to(UP * 0.85)
            title = B("our one-way street", 44).move_to(UP * 3.05)
            easy2 = B("easy", 32, GREEN).next_to(street.fwd, UP, buff=0.15).shift(RIGHT * 2.8)
            hard2 = B("hard", 32, RED).next_to(street.road, DOWN, buff=0.2).set_x(street.bwd.get_center()[0] + 0.8)
            v.wait_until("street", offset=-0.2)
            self.play(FadeOut(VGroup(lbox, rbox, kk, rr, fwd, fast, rblock, rlab, bwd, tries, dlp, lock, lock_bg)),
                      run_time=0.5)
            self.play(FadeIn(street), FadeIn(title, shift=0.1 * DOWN), FadeIn(easy2), FadeIn(hard2), run_time=0.8)
            curve = mini_curve(BLUE, 1.3, stroke=5)
            curve_lab = B("Elliptic curves: even harder to reverse", 36, BLUE)
            ec = VGroup(curve, curve_lab).arrange(RIGHT, buff=0.45).move_to(DOWN * 2.2)
            v.wait_until("harder", offset=-0.2)
            self.play(Create(curve), FadeIn(curve_lab, shift=0.1 * LEFT), run_time=0.9)
            self.play(street.barrier.animate.stretch(1.25, 1).stretch(1.6, 0), Indicate(hard2, color=RED), run_time=0.6)

        self.clear_all()

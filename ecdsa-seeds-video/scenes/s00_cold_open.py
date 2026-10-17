from common import *

SEED = "C49D3608 86E70493 6A6678E1 139D26B7 819F7E90"


class ColdOpen(VOScene):
    def construct(self):
        # ---------------------------------------------------------- c1: the number
        with self.vo("c1") as v:
            seed = Mono(SEED, 48, FG, weight=BOLD)
            seed.scale_to_fit_width(min(seed.width, 12.8))
            glow = soft_glow(seed, BLUE)
            self.play(AddTextLetterByLetter(seed, time_per_char=0.045), run_time=1.8)
            self.add(glow)
            self.play(FadeIn(glow), run_time=0.6)
            years = Mono("1999  ──────────▶  2026", 30, MUTED).next_to(seed, DOWN, buff=0.6)
            v.wait_until("years")
            self.play(FadeIn(years, shift=0.1 * UP), run_time=0.8)

        # ---------------------------------------------------------- c2: where it lives
        with self.vo("c2") as v:
            name = B("P-256", 72, BLUE).move_to(UP * 2.95)
            tag = pill("SEED", MUTED, size=22)
            small_seed = Mono(SEED, 30, FG, weight=BOLD)
            row = VGroup(tag, small_seed).arrange(RIGHT, buff=0.3).move_to(UP * 1.75)
            eq = M(r"y^2 = x^3 - 3x + {{b}} \pmod{p}", size=60, colors={"b": YELLOW}).move_to(DOWN * 0.15)
            b_part = [p for p in eq.submobjects if getattr(p, "tex_string", "").strip() == "b"][0]
            v.wait_until("p256", offset=-0.3)
            self.play(FadeOut(years), FadeOut(glow), ReplacementTransform(seed, small_seed), FadeIn(tag),
                      FadeIn(name, shift=0.2 * DOWN), run_time=0.9)
            self.play(Write(eq), run_time=1.0)
            arr = arrow(small_seed.get_bottom() + DOWN * 0.05, b_part.get_top() + UP * 0.08, color=YELLOW, buff=0.05)
            via = label("SHA-1", 24, YELLOW).next_to(arr, RIGHT, buff=0.15)
            self.play(GrowArrow(arr), FadeIn(via), Indicate(b_part, color=YELLOW, scale_factor=1.4), run_time=0.8)

            specs = [("lock", icon_padlock(GREEN, 1.15), "HTTPS"),
                     ("key", icon_key(GOLD, 1.7), "Passkeys"),
                     ("chip", icon_chip(TEAL, 1.15), "Phone secure chip")]
            icons = VGroup()
            for _, ic, txt in specs:
                slot = Rectangle(width=3.2, height=1.3).set_opacity(0)
                ic.move_to(slot)
                lab = label(txt, 30, FG).next_to(slot, DOWN, buff=0.2)
                icons.add(VGroup(slot, ic, lab))
            icons.arrange(RIGHT, buff=0.6).move_to(DOWN * 2.5)
            for (mark, _, _), g in zip(specs, icons):
                v.wait_until(mark, offset=-0.2)
                self.play(FadeIn(g[1], scale=0.6), FadeIn(g[2], shift=0.1 * UP), run_time=0.5)

        # ---------------------------------------------------------- c3: nobody knows
        with self.vo("c3") as v:
            self.play(FadeOut(icons, shift=0.2 * DOWN), FadeOut(VGroup(name, eq, arr, via, tag)),
                      small_seed.animate.scale_to_fit_width(12.4).move_to(UP * 1.6), run_time=0.8)
            origin = MT(f'origin: {span("unknown", RED, True)}', 40, MUTED).next_to(small_seed, DOWN, buff=0.5)
            v.wait_until("q", offset=-0.2)
            self.play(FadeIn(origin, shift=0.1 * UP), run_time=0.6)
            qs = VGroup(*[B("?", s, c) for s, c in ((130, RED), (80, MUTED), (60, DIM))])
            qs[0].move_to(RIGHT * 5.7 + UP * 2.9).rotate(12 * DEGREES)
            qs[1].move_to(LEFT * 6.0 + UP * 2.8).rotate(-15 * DEGREES)
            qs[2].move_to(RIGHT * 6.1 + DOWN * 2.4).rotate(8 * DEGREES)
            self.play(LaggedStart(*[FadeIn(q, scale=0.5) for q in qs], lag_ratio=0.25), run_time=0.9)
            crowd_l = VGroup(*[icon_person(BLUE, 0.95) for _ in range(3)]).arrange(RIGHT, buff=0.18)
            crowd_r = VGroup(*[icon_person(MUTED, 0.95) for _ in range(2)]).arrange(RIGHT, buff=0.18)
            lab_l = label("the cryptographers", 28, BLUE).next_to(crowd_l, DOWN, buff=0.2)
            lab_r = label("its creators", 28, MUTED).next_to(crowd_r, DOWN, buff=0.2)
            gl = VGroup(crowd_l, lab_l).move_to(LEFT * 2.8 + DOWN * 2.0)
            gr = VGroup(crowd_r, lab_r).move_to(RIGHT * 2.8 + DOWN * 2.0)
            ql = B("?", 52, BLUE).next_to(crowd_l, UP, buff=0.15)
            qr = B("?", 52, MUTED).next_to(crowd_r, UP, buff=0.15)
            v.wait_until("crypto", offset=-0.2)
            self.play(FadeIn(gl, shift=0.1 * UP), FadeIn(ql, shift=0.1 * DOWN), run_time=0.6)
            v.wait_until("nobody", offset=-0.2)
            self.play(FadeIn(gr, shift=0.1 * UP), FadeIn(qr, shift=0.1 * DOWN), run_time=0.6)

        # ---------------------------------------------------------- c4: suspicion
        with self.vo("c4") as v:
            self.play(FadeOut(VGroup(gl, gr, ql, qr, origin, qs)),
                      small_seed.animate.scale_to_fit_width(8.6).move_to(UP * 3.05), run_time=0.7)
            door = icon_door(RED, 2.3)
            door_lab = label("a backdoor?", 32, RED).next_to(door, DOWN, buff=0.3)
            g_door = VGroup(door, door_lab)
            quote = T("“A Riddle Wrapped\nin an Enigma”", 40, FG, weight=BOLD, line_spacing=1.0)
            who = label("Koblitz & Menezes, 2015", 26)
            q_card = boxed(VGroup(quote, who).arrange(DOWN, buff=0.35), DIM, buff=0.4)
            b_title = B("BOUNTY", 28, GOLD)
            b_amt = B("$36,864", 58, FG)
            b_sub = label("for the seeds' origin", 24)
            b_card = boxed(VGroup(b_title, b_amt, b_sub).arrange(DOWN, buff=0.2), GOLD, buff=0.35)
            row3 = VGroup(g_door, q_card, b_card).arrange(RIGHT, buff=0.6).move_to(DOWN * 0.25)
            if row3.width > 12.6:
                row3.scale_to_fit_width(12.6)
            v.wait_until("door", offset=-0.2)
            self.play(FadeIn(door, shift=0.2 * RIGHT), FadeIn(door_lab), run_time=0.7)
            v.wait_until("riddle", offset=-0.3)
            self.play(FadeIn(q_card, shift=0.15 * UP), run_time=0.8)
            v.wait_until("bounty", offset=-0.2)
            self.play(FadeIn(b_card, shift=0.15 * UP), run_time=0.7)
            st = stamp("UNCLAIMED", RED, 34).next_to(b_card, DOWN, buff=-0.15)
            v.wait_until("unclaimed", offset=-0.1)
            self.play(FadeIn(st, scale=1.6), run_time=0.3, rate_func=rush_into)
            self.play(Wiggle(st, scale_value=1.05, rotation_angle=0.02 * TAU), run_time=0.5)

        # ---------------------------------------------------------- c5: October 2026
        with self.vo("c5") as v:
            self.play(FadeOut(VGroup(g_door, q_card, b_card, st, small_seed)), run_time=0.6)
            date = Mono("October 16, 2026", 44, MUTED).move_to(UP * 2.2)
            v.wait_until("date", offset=-0.2)
            self.play(FadeIn(date, shift=0.1 * DOWN), run_time=0.6)
            anth = label("Anthropic research", 32, FG).next_to(date, DOWN, buff=0.3)
            v.wait_until("anth", offset=-0.2)
            self.play(FadeIn(anth, shift=0.1 * DOWN), run_time=0.5)
            claude = B("Claude", 110, CLAUDE)
            solved = T("solved the mystery", 46, FG).next_to(claude, DOWN, buff=0.3)
            g = VGroup(claude, solved).move_to(DOWN * 0.15)
            v.wait_until("claude", offset=-0.2)
            self.play(FadeIn(claude, scale=0.9), run_time=0.6)
            self.play(FadeIn(solved, shift=0.1 * UP), run_time=0.5)
            sw = icon_stopwatch(CLAUDE, 0.55)
            t30 = B("< 30 minutes", 46, CLAUDE)
            fast = VGroup(sw, t30).arrange(RIGHT, buff=0.35).next_to(g, DOWN, buff=0.55)
            v.wait_until("fast", offset=-0.2)
            self.play(FadeIn(fast, shift=0.1 * UP), Rotate(sw[4], -PI, about_point=sw[0].get_center()),
                      run_time=0.9)

        # ---------------------------------------------------------- c6: the answer
        with self.vo("c6") as v:
            self.play(FadeOut(VGroup(date, anth, g, fast)), run_time=0.5)
            seed3 = Mono(SEED, 34, MUTED).move_to(DOWN * 1.3)
            self.play(FadeIn(seed3), run_time=0.5)
            words = VGroup(B("“It's", 84), B("just", 84), B("timestamps.”", 84, YELLOW)).arrange(RIGHT, buff=0.38)
            words.move_to(UP * 0.8)
            v.wait_until("pause", offset=0.05)
            self.sfx("chime", note=81)
            self.play(LaggedStart(*[FadeIn(w, shift=0.2 * UP) for w in words], lag_ratio=0.35), run_time=1.1)
            ts = Mono("1997-08-16  01:52:34 UTC", 40, YELLOW, weight=BOLD).move_to(seed3)
            self.play(Transform(seed3, ts), run_time=1.2)

        # ---------------------------------------------------------- c7: roadmap
        with self.vo("c7") as v:
            qa = pill("Why is that so satisfying?", FG, size=40)
            qb = pill("How did an AI find it?", CLAUDE, size=40)
            qrow = VGroup(qa, qb).arrange(DOWN, buff=0.45).move_to(UP * 0.3)
            self.play(FadeOut(VGroup(seed3, words), shift=0.2 * UP), run_time=0.6)
            self.play(FadeIn(qa, shift=0.1 * UP), run_time=0.5)
            self.play(FadeIn(qb, shift=0.1 * UP), run_time=0.5)
            items = [("r1", "Digital\nsignatures", icon_key(GOLD, 1.5)),
                     ("r2", "Elliptic\ncurves", mini_curve(BLUE, 1.25)),
                     ("r3", "The ECDSA\nalgorithm", M(r"{{s}} = {{k}}^{-1}({{e}}+{{r}}{{d}})", size=38, colors=VAR_COLORS)),
                     ("r4", "The seed\nmystery", icon_magnifier(CLAUDE, 0.5))]
            cards = VGroup()
            for i, (mark, title, ic) in enumerate(items):
                box = panel(3.05, 3.5)
                num = Mono(f"{i + 1}", 28, CLAUDE, weight=BOLD).move_to(box.get_corner(UL) + RIGHT * 0.34 + DOWN * 0.34)
                ic.move_to(box.get_center() + UP * 0.55)
                if ic.width > 2.6:
                    ic.scale_to_fit_width(2.6)
                if ic.height > 1.5:
                    ic.scale_to_fit_height(1.5)
                t = T(title, 32, FG, weight=BOLD, line_spacing=0.9).move_to(box.get_center() + DOWN * 0.95)
                cards.add(VGroup(box, num, ic, t))
            cards.arrange(RIGHT, buff=0.3).move_to(DOWN * 0.7)
            for i, ((mark, _, _), c) in enumerate(zip(items, cards)):
                v.wait_until(mark, offset=-0.2)
                if i == 0:
                    self.play(qrow.animate.arrange(RIGHT, buff=0.5).scale(0.8).move_to(UP * 2.75),
                              FadeIn(c, shift=0.2 * UP), run_time=0.6)
                else:
                    self.play(FadeIn(c, shift=0.2 * UP), run_time=0.45)
            self.play(cards[3][0].animate.set_stroke(CLAUDE, 3), run_time=0.4)

        # ---------------------------------------------------------- title sting
        self.play(FadeOut(VGroup(cards, qrow), shift=0.2 * UP), run_time=0.6)
        title = B("IT'S JUST TIMESTAMPS", 80, FG)
        sub = T("How Claude solved the 25-year mystery of the NIST curve seeds", 34, MUTED)
        bar = Line(LEFT, RIGHT, stroke_color=CLAUDE, stroke_width=5).set_width(2.2)
        tg = VGroup(title, bar, sub).arrange(DOWN, buff=0.45)
        if sub.width > 12.5:
            sub.scale_to_fit_width(12.5)
        self.sfx("chime", note=74)
        self.play(FadeIn(title, shift=0.2 * UP), GrowFromCenter(bar), run_time=0.9)
        self.play(FadeIn(sub, shift=0.1 * UP), run_time=0.6)
        self.wait(2.2)
        self.play(FadeOut(tg), run_time=0.7)

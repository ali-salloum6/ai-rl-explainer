from common import *


class Meaning(VOScene):
    def construct(self):
        self.chapter(9, "So, is ECDSA broken?")

        # ---------------------------------------------------------- m1: no
        with self.vo("m1") as v:
            q = B("Is ECDSA broken?", 64, FG).move_to(UP * 1.2)
            self.play(FadeIn(q, shift=0.1 * UP), run_time=0.6)
            no = B("No.", 120, GREEN).move_to(DOWN * 0.6)
            sub = label("not an attack  ·  not a weakness  ·  nothing to patch", 30, MUTED).next_to(no, DOWN, buff=0.3)
            v.wait_until("no", offset=-0.15)
            self.play(FadeIn(no, scale=1.3), run_time=0.5)
            self.play(FadeIn(sub, shift=0.1 * UP), run_time=0.5)
            icons = VGroup(
                VGroup(icon_key(GOLD, 1.6), label("passkeys", 28, FG)).arrange(DOWN, buff=0.3),
                VGroup(icon_padlock(GREEN, 1.2), label("HTTPS", 28, FG)).arrange(DOWN, buff=0.3),
                VGroup(icon_chip(TEAL, 1.2), label("secure chip", 28, FG)).arrange(DOWN, buff=0.3),
            ).arrange(RIGHT, buff=1.4).move_to(DOWN * 0.4)
            for g in icons:
                g[1].align_to(icons[0][1], DOWN)
            v.wait_until("items", offset=-0.2)
            self.play(VGroup(q, no, sub).animate.scale(0.6).to_edge(UP, buff=0.35), run_time=0.6)
            self.play(LaggedStart(*[FadeIn(g, shift=0.15 * UP) for g in icons], lag_ratio=0.25), run_time=1.0)
            shield = icon_shield(GREEN, 1.3).next_to(icons, DOWN, buff=0.45)
            same = B("as secure as yesterday", 40, GREEN).next_to(shield, RIGHT, buff=0.35)
            VGroup(shield, same).move_to(DOWN * 2.75)
            v.wait_until("same", offset=-0.2)
            self.play(FadeIn(shield, scale=0.7), FadeIn(same, shift=0.1 * LEFT), run_time=0.7)

        # ---------------------------------------------------------- m2: fear vs reality
        with self.vo("m2") as v:
            good = pill("good news", GREEN, size=34).move_to(UP * 3.1)
            self.play(FadeOut(VGroup(q, no, sub, icons, shield, same)), FadeIn(good, shift=0.1 * DOWN), run_time=0.6)
            lp = panel(6.2, 5.2).move_to(LEFT * 3.3 + DOWN * 0.45)
            rp = panel(6.2, 5.2).move_to(RIGHT * 3.3 + DOWN * 0.45)
            lt = B("THE FEAR", 30, RED).move_to(lp.get_top() + DOWN * 0.45)
            rt = B("THE REALITY", 30, GREEN).move_to(rp.get_top() + DOWN * 0.45)
            rng = np.random.default_rng(3)
            cloud = VGroup(*[Dot(lp.get_center() + np.array([rng.uniform(-2.6, 2.6), rng.uniform(-1.45, 1.25), 0]),
                                 radius=0.04, color=DIM) for _ in range(260)])
            pick = Dot(lp.get_center() + np.array([1.2, -0.3, 0]), radius=0.12, color=RED)
            ring = Circle(radius=0.3, color=RED, stroke_width=4).move_to(pick)
            lcap = label("one seed hand-picked\nfrom a huge search?", 28, FG).move_to(lp.get_bottom() + UP * 0.65)
            v.wait_until("fear", offset=-0.2)
            self.play(FadeIn(lp), FadeIn(lt), run_time=0.5)
            self.play(LaggedStart(*[FadeIn(d) for d in cloud], lag_ratio=0.004), run_time=1.2)
            self.play(FadeIn(pick, scale=2), Create(ring), FadeIn(lcap), run_time=0.7)
            code = VGroup(
                MT(f'{span("srand48", BLUE)}({span("871696354", ORANGE)})', 30, FG, font=MONO),
                MT(f'candidate {span("#1842", CLAUDE, True)}', 30, FG, font=MONO),
                Mono("C49D3608 86E70493", 28, YELLOW, weight=BOLD),
                Mono("6A6678E1 139D26B7 819F7E90", 28, YELLOW, weight=BOLD),
            ).arrange(DOWN, buff=0.22).move_to(rp.get_center() + UP * 0.35)
            arrows = VGroup(*[Arrow(code[i].get_bottom(), code[i + 1].get_top(), buff=0.04, color=MUTED,
                                    stroke_width=3, max_tip_length_to_length_ratio=0.35) for i in (0, 1)])
            rcap = label("a clock-seeded generator\nanyone can re-run", 28, FG).move_to(rp.get_bottom() + UP * 0.65)
            ok = check_mark(GREEN, 0.5).next_to(code[3], DOWN, buff=0.2)
            v.wait_until("repro", offset=-0.2)
            self.play(FadeIn(rp), FadeIn(rt), run_time=0.5)
            self.play(FadeIn(code[0]), run_time=0.4)
            self.play(GrowArrow(arrows[0]), FadeIn(code[1]), run_time=0.5)
            self.play(GrowArrow(arrows[1]), FadeIn(code[2:]), run_time=0.5)
            self.play(Create(ok), FadeIn(rcap), run_time=0.5)

        # ---------------------------------------------------------- m3: thirty bits of freedom
        with self.vo("m3") as v:
            who = MT(f'{span("Filippo Valsorda", FG, True)}  ·  who ran the bounty', 32, MUTED).move_to(UP * 3.0)
            self.play(FadeOut(VGroup(good, lp, rp, lt, rt, cloud, pick, ring, lcap, code, arrows, rcap, ok)),
                      FadeIn(who, shift=0.1 * DOWN), run_time=0.7)
            r1 = VGroup(T("any second of 1997–1998", 38, FG), M(r"\approx 6.3\times10^{7} \approx 2^{26}", size=50))
            r2 = VGroup(T("any of the first 16 valid candidates", 38, FG), M(r"\times\ 16 = 2^{4}", size=50))
            r3 = VGroup(B("total freedom", 40, YELLOW), M(r"\approx 2^{30}", size=60, color=YELLOW))
            for r in (r1, r2, r3):
                r.arrange(RIGHT, buff=0.5)
            rows = VGroup(r1, r2, r3).arrange(DOWN, buff=0.45, aligned_edge=RIGHT).move_to(UP * 0.7)
            line = Line(rows.get_left() + DOWN * 0.0, rows.get_right(), stroke_color=DIM, stroke_width=2)
            line.next_to(r3, UP, buff=0.22).set_x(rows.get_x())
            v.wait_until("anyts", offset=-0.2)
            self.play(FadeIn(r1, shift=0.1 * UP), run_time=0.6)
            v.wait_until("cands", offset=-0.2)
            self.play(FadeIn(r2, shift=0.1 * UP), run_time=0.6)
            v.wait_until("bits", offset=-0.2)
            self.play(Create(line), FadeIn(r3, shift=0.1 * UP), run_time=0.6)
            bits = VGroup(*[Square(0.3, stroke_color=YELLOW, stroke_width=1.5, fill_color=YELLOW, fill_opacity=0.35)
                            for _ in range(30)]).arrange(RIGHT, buff=0.05).move_to(DOWN * 1.75)
            bl = label("barely 30 bits of wiggle room", 32, YELLOW).next_to(bits, DOWN, buff=0.3)
            self.play(LaggedStart(*[FadeIn(b, scale=0.5) for b in bits], lag_ratio=0.03), FadeIn(bl), run_time=1.0)
            little = label("far too little to aim for a rare, secret class of weak curves", 30, FG)
            little.next_to(bl, DOWN, buff=0.3)
            v.wait_until("little", offset=-0.2)
            self.play(FadeIn(little, shift=0.1 * UP), run_time=0.6)

        # ---------------------------------------------------------- m4: open questions
        with self.vo("m4") as v:
            hdr = B("Still open", 54, FG).move_to(UP * 2.9)
            self.play(FadeOut(VGroup(who, rows, line, bits, bl, little)), FadeIn(hdr, shift=0.1 * DOWN), run_time=0.6)

            def item(text, sub):
                qm = B("?", 54, YELLOW)
                body = VGroup(T(text, 36, FG, weight=BOLD), label(sub, 28)).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
                return VGroup(qm, body).arrange(RIGHT, buff=0.4)

            i1 = item("Why skip candidate #876?", "the P-256 run passed over a curve that also qualified")
            i2 = item("B-163's seed", "the fifth binary seed fits nothing tried so far")
            i3 = item("Most base points", "G for P-224, P-256, P-384, P-521 and the binary curves")
            items = VGroup(i1, i2, i3).arrange(DOWN, buff=0.55, aligned_edge=LEFT).move_to(DOWN * 0.35)
            strip = VGroup(*[Square(0.16, stroke_width=0, fill_color=DIM, fill_opacity=1) for _ in range(24)])
            strip.arrange(RIGHT, buff=0.04)
            v.wait_until("skip", offset=-0.2)
            self.play(FadeIn(i1, shift=0.1 * RIGHT), run_time=0.6)
            v.wait_until("b163", offset=-0.2)
            self.play(FadeIn(i2, shift=0.1 * RIGHT), run_time=0.6)
            v.wait_until("bp", offset=-0.2)
            self.play(FadeIn(i3, shift=0.1 * RIGHT), run_time=0.6)

        # ---------------------------------------------------------- m5: the bounty
        with self.vo("m5") as v:
            amt = boxed(VGroup(B("BOUNTY", 26, GOLD), B("$36,864", 60, FG)).arrange(DOWN, buff=0.15), GOLD, buff=0.35)
            amt.move_to(LEFT * 3.8 + UP * 0.3)
            isrg = boxed(VGroup(B("Internet Security", 36, FG), B("Research Group", 36, FG)).arrange(DOWN, buff=0.1),
                         GREEN, buff=0.35).move_to(RIGHT * 3.2 + UP * 0.3)
            arr = Arrow(amt.get_right(), isrg.get_left(), buff=0.25, color=GREEN, stroke_width=6)
            self.play(FadeOut(VGroup(hdr, items)), FadeIn(amt, shift=0.1 * RIGHT), run_time=0.6)
            self.play(GrowArrow(arr), FadeIn(isrg, shift=0.1 * LEFT), run_time=0.7)
            le = VGroup(icon_padlock(GREEN, 0.6), label("the nonprofit behind Let's Encrypt", 32, FG)).arrange(RIGHT, buff=0.3)
            le.next_to(isrg, DOWN, buff=0.45).set_x(0)
            v.wait_until("le", offset=-0.2)
            self.play(FadeIn(le, shift=0.1 * UP), run_time=0.6)

        # ---------------------------------------------------------- m6: how it was solved
        with self.vo("m6") as v:
            hdr = B("How it was solved", 52, FG).move_to(UP * 3.0)
            self.play(FadeOut(VGroup(amt, isrg, arr, le)), FadeIn(hdr, shift=0.1 * DOWN), run_time=0.6)
            bar = Line(LEFT * 5.5, RIGHT * 5.5, stroke_color=DIM, stroke_width=6).move_to(UP * 1.05)
            y0 = T("1997", 26, MUTED).next_to(bar.get_left(), DOWN, buff=0.2)
            y1 = T("2026", 26, MUTED).next_to(bar.get_right(), DOWN, buff=0.2)
            texts = ("Give Bob and Jerry a raise", "Bob and Jerry rule", "Give Jerry a raise", "Jerry and Bob rule!")
            phrases = VGroup(*[T(f"“{p}”", 26, MUTED) for p in texts])
            spots = [LEFT * 3.4 + UP * 2.15, RIGHT * 2.6 + UP * 2.15, LEFT * 1.9 + UP * 1.6, RIGHT * 3.6 + UP * 1.6]
            for p, spot in zip(phrases, spots):
                p.move_to(spot)
            xs = VGroup(*[cross_mark(RED, 0.22, 4).next_to(p, RIGHT, buff=0.12) for p in phrases])
            hunt = label("25+ years hunting for a phrase", 30, FG).next_to(bar, DOWN, buff=0.25)
            v.wait_until("phrase", offset=-0.2)
            self.play(Create(bar), FadeIn(y0), FadeIn(y1), FadeIn(hunt), run_time=0.6)
            self.play(LaggedStart(*[AnimationGroup(FadeIn(p, shift=0.1 * UP), FadeIn(x)) for p, x in zip(phrases, xs)],
                                  lag_ratio=0.25), run_time=1.2)
            qa = MT(f'{span("Claude", CLAUDE, True)} asked a better question', 36, FG).move_to(DOWN * 0.15)
            v.wait_until("better", offset=-0.2)
            self.play(FadeIn(qa, shift=0.1 * UP), run_time=0.5)
            q1 = T("not  “what was hashed?”", 36, MUTED).move_to(DOWN * 1.05)
            v.wait_until("q1", offset=-0.2)
            self.play(FadeIn(q1), run_time=0.4)
            strike = Line(q1.get_left(), q1.get_right(), stroke_color=RED, stroke_width=4)
            self.play(Create(strike), run_time=0.3)
            q2 = B("“What would 1990s software actually do?”", 40, CLAUDE).move_to(DOWN * 1.9)
            v.wait_until("q2", offset=-0.2)
            self.play(FadeIn(q2, shift=0.1 * UP), run_time=0.6)
            steps = VGroup(pill("scanner", FG, size=26), pill("lattice (LLL)", FG, size=26),
                           pill("rewind to srand48", FG, size=26), pill("< 30 min", CLAUDE, size=26))
            steps.arrange(RIGHT, buff=0.35).move_to(DOWN * 3.0)
            v.wait_until("thirty", offset=-0.2)
            self.play(LaggedStart(*[FadeIn(s_, shift=0.1 * RIGHT) for s_ in steps], lag_ratio=0.25), run_time=1.0)

        # ---------------------------------------------------------- m7: both ways + the lesson
        with self.vo("m7") as v:
            both = B("It cuts both ways", 48, FG).move_to(UP * 3.0)
            ways = VGroup(pill("audit", BLUE, size=30), DoubleArrow(LEFT, RIGHT, color=MUTED, stroke_width=4, buff=0).set_width(1.4),
                          pill("attack", RED, size=30)).arrange(RIGHT, buff=0.2).next_to(both, DOWN, buff=0.3)
            self.play(FadeOut(VGroup(hdr, bar, y0, y1, phrases, xs, hunt, qa, q1, strike, q2, steps)),
                      FadeIn(both, shift=0.1 * DOWN), run_time=0.6)
            self.play(FadeIn(ways, shift=0.1 * UP), run_time=0.5)
            mag = icon_magnifier(CLAUDE, 0.5)
            chips = VGroup(pill("old standards", FG, size=28), pill("firmware", FG, size=28),
                           pill("software we all rely on", FG, size=28)).arrange(RIGHT, buff=0.3)
            row = VGroup(mag, chips).arrange(RIGHT, buff=0.55).move_to(UP * 0.75)
            wr = label("weak-randomness detector", 26, CLAUDE).next_to(mag, DOWN, buff=0.2)
            if wr.get_left()[0] < -6.5:
                wr.shift(RIGHT * (-6.5 - wr.get_left()[0]))
            v.wait_until("hides", offset=-0.2)
            self.play(FadeIn(mag, scale=0.7), FadeIn(wr), run_time=0.5)
            self.play(LaggedStart(*[FadeIn(c, shift=0.1 * RIGHT) for c in chips], lag_ratio=0.3), run_time=0.9)
            home = mag.get_center()
            self.play(mag.animate.move_to(chips[2].get_center()), run_time=1.0)
            self.play(mag.animate.move_to(home), run_time=0.6)
            sh = VGroup(icon_shield(BLUE, 0.9), label("a tool for defenders", 30, BLUE)).arrange(RIGHT, buff=0.3)
            sh.move_to(DOWN * 0.6 + RIGHT * 1.2)
            v.wait_until("defenders", offset=-0.2)
            self.play(FadeIn(sh, shift=0.1 * UP), run_time=0.6)
            lesson = label("cryptography's oldest lesson", 30, MUTED).move_to(DOWN * 1.45)
            v.wait_until("lesson", offset=-0.2)
            self.play(FadeIn(lesson), run_time=0.5)
            big = MT(f'For keys and nonces, {span("randomness is everything.", YELLOW, True)}', 44, FG)
            big.move_to(DOWN * 2.2)
            if big.width > 12.8:
                big.scale_to_fit_width(12.8)
            v.wait_until("everything", offset=-0.2)
            self.play(FadeIn(big, shift=0.1 * UP), run_time=0.6)
            clockline = VGroup(icon_clock(FG, 0.35, hour=1, minute=52), B("A clock is not a secret.", 44, FG))
            clockline.arrange(RIGHT, buff=0.3).move_to(DOWN * 3.15)
            v.wait_until("clock", offset=-0.2)
            self.play(FadeIn(clockline, shift=0.1 * UP), run_time=0.6)

        # ---------------------------------------------------------- m8: the ending
        with self.vo("m8") as v:
            door = icon_door(RED, 2.0).move_to(LEFT * 3.2 + UP * 0.2)
            nob = label("not a backdoor", 32, RED).next_to(door, DOWN, buff=0.3)
            self.play(FadeOut(VGroup(both, ways, mag, wr, chips, sh, lesson, big, clockline)), FadeIn(door), FadeIn(nob),
                      run_time=0.7)
            x = cross_mark(RED, 1.6, 10).move_to(door)
            self.play(Create(x), run_time=0.5)
            clk = icon_clock(FG, 1.25, hour=1, minute=52, numbers=True).move_to(RIGHT * 3.2 + UP * 0.2)
            cl = label("01:52:34 UTC · August 16, 1997", 30, YELLOW).next_to(clk, DOWN, buff=0.3)
            v.wait_until("fin", offset=-0.2)
            self.play(FadeOut(VGroup(door, nob, x), shift=0.3 * LEFT), FadeIn(clk, shift=0.3 * LEFT),
                      FadeIn(cl), run_time=0.8)
            rt = v.left(1.0)
            self.sfx("ticks", duration=rt + 1.5)
            self.play(Rotate(clk.hand_m, angle=-TAU / 60 * 3, about_point=clk.face.get_center()),
                      run_time=rt, rate_func=linear)

        # ---------------------------------------------------------- end card
        self.play(FadeOut(VGroup(clk, cl)), run_time=0.6)
        title = B("IT'S JUST TIMESTAMPS", 72, FG)
        bar = Line(LEFT, RIGHT, stroke_color=CLAUDE, stroke_width=5).set_width(2.2)
        srcs = VGroup(
            label("Sources", 26, FG),
            label("Anthropic, “Claude reveals ECDSA curve origins” (Oct 16, 2026)", 24),
            label("F. Valsorda, “The NIST Elliptic Curves Seeds Bounty Has Been Claimed” (2026)", 24),
            label("N. Koblitz & A. Menezes, “A Riddle Wrapped in an Enigma” (2015)", 24),
            label("NIST FIPS 186-2 (2000) · ANSI X9.62 (1999)", 24),
        ).arrange(DOWN, buff=0.16)
        end = VGroup(title, bar, srcs).arrange(DOWN, buff=0.5)
        self.sfx("chime", note=74)
        self.play(FadeIn(title, shift=0.2 * UP), GrowFromCenter(bar), run_time=0.9)
        self.play(FadeIn(srcs, shift=0.1 * UP), run_time=0.8)
        self.wait(4.0)
        self.play(FadeOut(end), run_time=1.0)

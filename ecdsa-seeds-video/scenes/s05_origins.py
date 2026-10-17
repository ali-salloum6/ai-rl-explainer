from common import *

SEED = "C49D3608 86E70493 6A6678E1 139D26B7 819F7E90"
C_HEX = ("7efba166 2985be94 03cb055c 75d4f7e0", "ce8d84a9 c5114abc af317768 0104fa0d")   # SHA-1 expansion of SEED
B_HEX = ("5ac635d8 aa3a93e7 b3ebbd55 769886bc", "651d06b0 cc53b0f6 3bce3c3e 27d2604b")   # P-256's b

# Small curves y^2 = x^3 + a x + b (mod p) with their real point counts (incl. the point at infinity).
CARDS = [
    (79, -3, 3, None), (67, -3, 1, "anomalous"), (83, -4, 6, None), (89, 0, 1, "supersingular"),
    (89, -3, 4, None), (97, -5, 4, "smooth"), (97, -3, 6, None), (103, -1, 5, None),
]
TRAP_TEXT = {
    "anomalous": ("67 points = p", "anomalous"),
    "supersingular": ("90 points = p + 1", "supersingular"),
    "smooth": ("108 = 2²·3³ points", "smooth order"),
}
# SHA-1 of guesses at Solinas's phrase (computed; none matches the seed).
GUESSES = [
    ("Give Bob and Jerry a raise", "3F7EBC0A"), ("Give Bob and Jerry a raise.", "23D81B34"),
    ("Bob and Jerry rule", "9727936F"), ("Give Jerry a raise", "FE72B6F9"),
    ("give bob and jerry a raise", "4EF62C6F"), ("Bob and Jerry rule!", "6B29880A"),
]
NIST_SEEDS = ["3045AE6F C8422F64 ED579528 D38120EA E12196D5", "BD713447 99D5C7FC DC45B59F A3B9AB8F 6A948BC5",
              "C49D3608 86E70493 6A6678E1 139D26B7 819F7E90", "A335926A A319A27A 1D00896A 6773A482 7ACDAC73",
              "D09E8800 291CB853 96CC6717 393284AA A0DA64BA"]


def curve_points(p, a, b):
    sq = {}
    for y in range(p):
        sq.setdefault(y * y % p, []).append(y)
    return [(x, y) for x in range(p) for y in sq.get((x ** 3 + a * x + b) % p, [])]


def eq_tex(a, b):
    t = "y^2 = x^3"
    if a:
        t += (" - " if a < 0 else " + ") + ("" if abs(a) == 1 else str(abs(a))) + "x"
    if b:
        t += (" - " if b < 0 else " + ") + str(abs(b))
    return t


def scatter(p, a, b, size=1.6, dot=0.024, color=BLUE):
    pts = curve_points(p, a, b)
    g = VGroup(*[Dot(np.array([(x / (p - 1) - 0.5) * size, (y / (p - 1) - 0.5) * size, 0]), radius=dot, color=color)
                 for x, y in pts])
    return g


def curve_card(p, a, b, w=3.05, h=2.95, color=BLUE):
    box = panel(w, h)
    sc = scatter(p, a, b, size=1.55, color=color).move_to(box.get_center() + UP * 0.38)
    eqm = M(eq_tex(a, b), size=30).next_to(sc, DOWN, buff=0.2)
    md = label(f"mod {p}", 26, MUTED).next_to(eqm, DOWN, buff=0.08)
    card = VGroup(box, sc, eqm, md)
    card.box, card.sc = box, sc
    return card


def random_card(rng, color=BLUE):
    primes = [71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113]
    while True:
        p = int(rng.choice(primes))
        a, b = int(rng.integers(-6, 7)), int(rng.integers(1, 12))
        if (4 * a ** 3 + 27 * b * b) % p:
            return curve_card(p, a, b, color=color)


class CurveOrigins(VOScene):
    def construct(self):
        self.chapter(5, "Where do curves come from?")

        # ------------------------------------------------------------ o1: not every curve is safe
        with self.vo("o1") as v:
            cards = VGroup(*[curve_card(p, a, b) for p, a, b, _ in CARDS]).arrange_in_grid(2, 4, buff=(0.25, 0.3))
            cards.move_to(DOWN * 0.05)
            self.play(LaggedStart(*[FadeIn(c, shift=0.15 * UP) for c in cards], lag_ratio=0.12), run_time=1.6)

            def trap_overlay(card, kind, color=RED):
                l1, l2 = TRAP_TEXT[kind]
                txt = VGroup(B(l1, 26, FG), B(l2, 26, color)).arrange(DOWN, buff=0.1)
                bg = RoundedRectangle(width=card.box.width - 0.3, height=txt.height + 0.35, corner_radius=0.1,
                                      fill_color=BG, fill_opacity=0.88, stroke_color=color, stroke_width=1.5)
                bg.move_to(card.sc)
                txt.move_to(bg)
                return VGroup(bg, txt)

            anom = cards[1]
            ov_a = trap_overlay(anom, "anomalous")
            broken = B("broken almost instantly", 30, RED)
            v.wait_until("weak", offset=-0.2)
            self.play(anom.box.animate.set_stroke(RED, 4), anom.sc.animate.set_color(RED),
                      *[c.animate.set_opacity(0.35) for i, c in enumerate(cards) if i != 1], run_time=0.6)
            self.play(FadeIn(ov_a, scale=0.9), run_time=0.5)
            broken.next_to(cards, UP, buff=0.2).align_to(anom, LEFT).shift(LEFT * 0.4)
            self.play(FadeIn(broken, shift=0.1 * DOWN), run_time=0.5)

            known = [(3, "supersingular"), (5, "smooth")]
            exp_t = v.at("weak") + 0.62 * (v.at("secret") - v.at("weak"))
            if exp_t - self.time > 0.02:
                self.wait(exp_t - self.time)
            ovs = []
            for idx, kind in known:
                ovs.append(trap_overlay(cards[idx], kind))
            self.play(*[cards[i].animate.set_opacity(1) for i, _ in known],
                      *[cards[i].box.animate.set_stroke(RED, 4) for i, _ in known],
                      *[cards[i].sc.animate.set_color(RED) for i, _ in known],
                      FadeOut(broken), run_time=0.5)
            self.play(*[FadeIn(o, scale=0.9) for o in ovs], run_time=0.5)
            avoid = B("known traps: avoided", 30, RED).next_to(cards, UP, buff=0.2)
            self.play(FadeIn(avoid, shift=0.1 * DOWN), run_time=0.4)

            target = cards[6]
            v.wait_until("secret", offset=-0.2)
            q = B("?", 96, YELLOW).move_to(target.sc)
            dash = DashedVMobject(target.box.copy().set_stroke(YELLOW, 4), num_dashes=40)
            unknown = B("an unknown trap?", 30, YELLOW).next_to(cards, UP, buff=0.2)
            self.play(target.animate.set_opacity(1), FadeIn(dash), FadeIn(q, scale=0.5),
                      ReplacementTransform(avoid, unknown), run_time=0.7)
            self.play(Indicate(q, color=YELLOW, scale_factor=1.15), run_time=0.7)

        # ------------------------------------------------------------ o2: search for a weak one
        with self.vo("o2") as v:
            others = VGroup(*[c for i, c in enumerate(cards) if i != 6], ov_a, *ovs, unknown)
            self.play(FadeOut(others), FadeOut(VGroup(dash, q)), target.animate.scale(1.35).move_to(DOWN * 0.5), run_time=0.7)
            odds = B("1 in 1,000,000,000", 60, YELLOW).move_to(UP * 2.75)
            sub = label("curves with your secret weakness", 30, MUTED).next_to(odds, DOWN, buff=0.15)
            v.wait_until("billion", offset=-0.2)
            self.play(FadeIn(odds, shift=0.1 * DOWN), FadeIn(sub), run_time=0.6)

            rng = np.random.default_rng(11)
            reel = [random_card(rng).scale(1.35).move_to(target) for _ in range(12)]
            counts = ["1", "17", "4,096", "65,536", "1,048,576", "16,777,216", "94,371,840", "268,435,456",
                      "536,870,912", "811,000,413", "973,412,778", "999,999,999"]
            ctr_lab = label("curves tested:", 30, MUTED)
            ctr = Mono("0", 34, FG)
            ctr_g = VGroup(ctr_lab, ctr).arrange(RIGHT, buff=0.25).move_to(DOWN * 3.2)
            v.wait_until("search", offset=-0.2)
            self.play(FadeIn(ctr_g), run_time=0.3)
            cur = target
            for i, (card, n) in enumerate(zip(reel, counts)):
                new_ctr = Mono(n, 34, FG).move_to(ctr, aligned_edge=LEFT)
                self.remove(cur, ctr)
                self.add(card, new_ctr)
                cur, ctr = card, new_ctr
                self.wait(0.07 + 0.02 * i)
            final = random_card(np.random.default_rng(3)).scale(1.35).move_to(target)
            final_ctr = Mono("1,000,000,000", 34, YELLOW).move_to(ctr, aligned_edge=LEFT)
            self.remove(cur, ctr)
            self.add(final, final_ctr)
            weak_lab = B("secretly weak", 30, RED).next_to(final, RIGHT, buff=0.4)
            self.play(final.sc.animate.set_color(RED), final.box.animate.set_stroke(RED, 3), FadeIn(weak_lab), run_time=0.5)
            self.play(final.sc.animate.set_color(BLUE), final.box.animate.set_stroke(DIM, 1.5), run_time=0.6)

            st = stamp("STANDARD", GOLD, 50).move_to(final.get_center() + DOWN * 0.25)
            v.wait_until("publish", offset=-0.2)
            self.play(FadeIn(st, scale=1.8), run_time=0.3, rate_func=rush_into)
            self.play(Wiggle(st, scale_value=1.04, rotation_angle=0.015 * TAU), run_time=0.5)

        # ------------------------------------------------------------ o3: the standards timeline
        with self.vo("o3") as v:
            self.play(FadeOut(VGroup(final, final_ctr, ctr_lab, st, weak_lab, odds, sub)), run_time=0.5)
            line = Line(LEFT * 5.8, RIGHT * 5.8, stroke_color=DIM, stroke_width=4).move_to(UP * 0.9)
            xs = (-4.4, 0.0, 4.4)
            nodes = VGroup(*[Dot([x, 0.9, 0], radius=0.14, color=c) for x, c in zip(xs, (RED, TEAL, BLUE))])
            years = VGroup(*[B(y, 44, c).next_to(n, UP, buff=0.3) for y, c, n in
                             zip(("1997–98", "1999", "2000"), (RED, TEAL, BLUE), nodes)])
            descs = [VGroup(B("NSA", 34, FG), label("generates the curves", 28, MUTED)),
                     VGroup(B("ANSI X9.62", 34, FG), label("banking standard", 28, MUTED)),
                     VGroup(B("NIST FIPS 186-2", 34, FG), label("federal signatures", 28, MUTED))]
            for d, n in zip(descs, nodes):
                d.arrange(DOWN, buff=0.1).next_to(n, DOWN, buff=0.35)
            v.wait_until("nsa", offset=0.0)
            self.play(Create(line), run_time=0.7)
            self.play(FadeIn(nodes[0], scale=0.5), FadeIn(years[0], shift=0.1 * DOWN), FadeIn(descs[0]), run_time=0.6)
            family = VGroup(*[mini_curve(c, 0.55, a=a, b=b, stroke=3) for c, a, b in
                              ((BLUE, -3, 3), (TEAL, -2, 2), (PURPLE, -3, 4), (GREEN, -1, 2), (YELLOW, -3, 5))])
            family.arrange(RIGHT, buff=0.18).next_to(descs[0], DOWN, buff=0.35)
            self.play(LaggedStart(*[FadeIn(f, shift=0.1 * UP) for f in family], lag_ratio=0.15), run_time=0.9)
            v.wait_until("ansi", offset=-0.2)
            self.play(FadeIn(nodes[1], scale=0.5), FadeIn(years[1], shift=0.1 * DOWN), FadeIn(descs[1]), run_time=0.6)
            chips = VGroup(*[pill(n, BLUE if n == "P-256" else FG, size=28, mono=True)
                             for n in ("P-192", "P-224", "P-256", "P-384", "P-521")]).arrange(RIGHT, buff=0.25)
            chips.move_to(DOWN * 2.6)
            v.wait_until("fips", offset=-0.2)
            self.play(FadeIn(nodes[2], scale=0.5), FadeIn(years[2], shift=0.1 * DOWN), FadeIn(descs[2]), run_time=0.6)
            self.play(ReplacementTransform(family, chips), run_time=0.8)
            self.play(chips[2].animate.scale(1.2), Indicate(chips[2], color=BLUE, scale_factor=1.0), run_time=0.6)

        # ------------------------------------------------------------ o4: verifiably random
        with self.vo("o4") as v:
            self.play(FadeOut(VGroup(line, nodes, years, *descs, *[c for i, c in enumerate(chips) if i != 2])),
                      chips[2].animate.scale(1 / 1.2).move_to(UP * 2.95 + LEFT * 5.0), run_time=0.7)
            curve_eq = M(r"y^2 = x^3 - 3x + {{b}}", size=58, colors={"b": YELLOW}).next_to(chips[2], RIGHT, buff=0.5)
            b_part = [p for p in curve_eq.submobjects if getattr(p, "tex_string", "").strip() == "b"][0]
            self.play(Write(curve_eq), run_time=0.8)
            vr = B("“verifiably random”", 44, YELLOW).move_to(UP * 1.85)
            v.wait_until("vr", offset=-0.2)
            self.play(FadeIn(vr, shift=0.1 * DOWN), run_time=0.6)
            not_hand = label("b is not picked by hand", 28, YELLOW).next_to(curve_eq, RIGHT, buff=0.4)
            self.play(Indicate(b_part, color=YELLOW, scale_factor=1.5), FadeIn(not_hand), run_time=0.8)

            seed_row = VGroup(pill("SEED", MUTED, size=24), Mono(SEED, 32, FG, weight=BOLD)).arrange(RIGHT, buff=0.3)
            seed_row.move_to(UP * 0.75)
            sha = boxed(B("SHA-1", 28, TEAL), TEAL, buff=0.16)
            c_vals = VGroup(*[Mono(t, 28, TEAL) for t in C_HEX]).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
            c_row = VGroup(M("c =", size=44, color=TEAL), c_vals).arrange(RIGHT, buff=0.3).move_to(DOWN * 0.75)
            a_sha = Arrow(seed_row.get_bottom(), c_row.get_top(), buff=0.12, color=MUTED, stroke_width=4,
                          max_tip_length_to_length_ratio=0.3)
            sha.next_to(a_sha, RIGHT, buff=0.25)
            v.wait_until("sha", offset=-0.2)
            self.play(FadeOut(vr), FadeIn(seed_row, shift=0.1 * DOWN), run_time=0.5)
            self.play(GrowArrow(a_sha), FadeIn(sha, scale=0.8), run_time=0.5)
            self.play(FadeIn(c_row, shift=0.1 * DOWN), run_time=0.6)

            rel = boxed(M(r"b^2 \cdot c \equiv -27 \pmod{p}", size=36), YELLOW, buff=0.15)
            b_vals = VGroup(*[Mono(t, 28, YELLOW) for t in B_HEX]).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
            b_row = VGroup(M("b =", size=44, color=YELLOW), b_vals).arrange(RIGHT, buff=0.3).move_to(DOWN * 2.6)
            a_rel = Arrow(c_row.get_bottom(), b_row.get_top(), buff=0.12, color=MUTED, stroke_width=4,
                          max_tip_length_to_length_ratio=0.3)
            rel.next_to(a_rel, RIGHT, buff=0.25)
            v.wait_until("b", offset=-0.2)
            self.play(GrowArrow(a_rel), FadeIn(rel, scale=0.9), run_time=0.5)
            self.play(FadeIn(b_row, shift=0.1 * DOWN), run_time=0.6)
            fly = b_row[0][0][0].copy()
            self.play(fly.animate.move_to(b_part).scale(1.2), run_time=0.8)
            self.play(FadeOut(fly), Indicate(b_part, color=YELLOW, scale_factor=1.5), run_time=0.6)

        # ------------------------------------------------------------ o5: the catch
        with self.vo("o5") as v:
            back = Arrow(c_row.get_top() + LEFT * 0.55, seed_row.get_bottom() + LEFT * 0.55, buff=0.12, color=RED,
                         stroke_width=5, max_tip_length_to_length_ratio=0.3)
            no = cross_mark(RED, 0.32, 7).move_to(back.get_center())
            no_lab = label("can't run it backwards", 28, RED).next_to(back, LEFT, buff=0.25)
            v.wait_until("oneway", offset=0.0)
            self.play(GrowArrow(back), run_time=0.6)
            self.play(FadeIn(no, scale=1.5), FadeIn(no_lab, shift=0.1 * LEFT), run_time=0.5)
            ok_b = VGroup(check_mark(GREEN, 0.4, 7), label("nobody chose b on purpose", 28, GREEN)).arrange(RIGHT, buff=0.15)
            ok_b.next_to(not_hand, DOWN, buff=0.3).align_to(not_hand, LEFT)
            self.play(FadeIn(ok_b, shift=0.1 * UP), run_time=0.5)

            but = B("But…", 72, FG)
            v.wait_until("catch", offset=-0.2)
            self.play(FadeOut(VGroup(back, no, no_lab, ok_b, not_hand, rel, a_rel, b_row, c_row, a_sha, sha,
                                     seed_row, curve_eq, chips[2])), run_time=0.5)
            self.play(FadeIn(but, scale=0.8), run_time=0.4)
            l_out = VGroup(cross_mark(RED, 0.36, 7), T("you can't choose the output…", 40, FG)).arrange(RIGHT, buff=0.3)
            l_in = VGroup(check_mark(YELLOW, 0.42, 7), T("…but you can try many inputs", 40, YELLOW)).arrange(RIGHT, buff=0.3)
            lines = VGroup(l_out, l_in).arrange(DOWN, buff=0.45, aligned_edge=LEFT).move_to(DOWN * 0.9)
            t_out = v.at("catch") + 0.45 * (v.at("tries") - v.at("catch"))
            if t_out - self.time > 0.02:
                self.wait(t_out - self.time)
            self.play(but.animate.shift(UP * 1.1), FadeIn(l_out, shift=0.1 * UP), run_time=0.5)

            rng = np.random.default_rng(42)
            n_rows = 6
            seeds = VGroup(*[Mono(" ".join("".join(rng.choice(list("0123456789ABCDEF"), 8)) for _ in range(2)) + " …",
                                  32, FG) for _ in range(n_rows)])
            seeds.arrange(DOWN, buff=0.36, aligned_edge=LEFT).move_to(LEFT * 3.0 + DOWN * 0.45)
            shas = VGroup(*[label("SHA-1  →", 28, TEAL).next_to(s_, RIGHT, buff=0.45) for s_ in seeds])
            crng = np.random.default_rng(8)
            minis = VGroup()
            for s_ in seeds:
                p = int(crng.choice([47, 53, 59, 61]))
                a, b = int(crng.integers(-4, 4)), int(crng.integers(1, 9))
                while (4 * a ** 3 + 27 * b * b) % p == 0:
                    b += 1
                minis.add(scatter(p, a, b, size=0.6, dot=0.016, color=BLUE))
            for m, sh in zip(minis, shas):
                m.next_to(sh, RIGHT, buff=0.35)
            verdicts = VGroup(*[label("fine", 30, MUTED).next_to(m, RIGHT, buff=0.35) for m in minis])
            pick = 4
            verdicts[pick].become(B("weak!", 30, RED).move_to(verdicts[pick], aligned_edge=LEFT))
            many = B("try a billion seeds, keep the one you like", 40, YELLOW).move_to(UP * 2.7)
            v.wait_until("tries", offset=-0.35)
            self.play(FadeIn(l_in, shift=0.1 * UP), run_time=0.4)
            self.wait(0.6)
            self.play(FadeOut(VGroup(but, l_out, l_in)), FadeIn(many, shift=0.1 * DOWN), run_time=0.5)
            self.play(LaggedStart(*[FadeIn(VGroup(s_, sh, m, vd), shift=0.1 * UP)
                                    for s_, sh, m, vd in zip(seeds, shas, minis, verdicts)], lag_ratio=0.15), run_time=1.4)
            sel = SurroundingRectangle(VGroup(seeds[pick], verdicts[pick]), color=RED, buff=0.12, corner_radius=0.08)
            self.play(Create(sel), minis[pick].animate.set_color(RED), run_time=0.6)

            check_q = VGroup(B("Is the seed itself explained?", 38, FG))
            check_q.move_to(DOWN * 2.95)
            v.wait_until("explain", offset=-0.2)
            self.play(FadeOut(VGroup(many, seeds, shas, minis, verdicts, sel)), run_time=0.5)
            p256_seed = VGroup(pill("P-256 SEED", BLUE, size=26), Mono(SEED, 32, FG, weight=BOLD)).arrange(RIGHT, buff=0.3)
            if p256_seed.width > 12.6:
                p256_seed.scale_to_fit_width(12.6)
            p256_seed.move_to(UP * 1.0)
            check_q.move_to(DOWN * 0.4)
            self.play(FadeIn(p256_seed, shift=0.1 * DOWN), FadeIn(check_q, shift=0.1 * UP), run_time=0.7)
            ans = VGroup(cross_mark(RED, 0.5, 9), B("no explanation at all", 40, RED)).arrange(RIGHT, buff=0.3)
            ans.next_to(check_q, DOWN, buff=0.5)
            v.wait_until("none", offset=-0.2)
            self.play(FadeIn(ans, shift=0.1 * UP), run_time=0.6)
            qm = B("?", 90, RED).next_to(p256_seed, UP, buff=0.25)
            self.play(FadeIn(qm, scale=0.5), run_time=0.5)

        # ------------------------------------------------------------ o6: Snowden and Dual_EC_DRBG
        with self.vo("o6") as v:
            self.play(FadeOut(VGroup(p256_seed, check_q, ans, qm)), run_time=0.5)
            bar = Line(LEFT * 5, RIGHT * 5, stroke_color=DIM, stroke_width=6).move_to(DOWN * 0.3)
            y0, y1 = B("2000", 36, MUTED).next_to(bar, LEFT, buff=0.3), B("2013", 36, MUTED).next_to(bar, RIGHT, buff=0.3)
            prog = Line(bar.get_left(), bar.get_left(), stroke_color=MUTED, stroke_width=6)
            few = VGroup(*[icon_person(MUTED, 0.85) for _ in range(3)]).arrange(RIGHT, buff=0.2).next_to(bar, UP, buff=0.6)
            few_q = label("a few experts wondered", 32, MUTED).next_to(few, UP, buff=0.25)
            self.play(FadeIn(VGroup(bar, y0, y1)), FadeIn(few), FadeIn(few_q), run_time=0.6)
            self.play(prog.animate.put_start_and_end_on(bar.get_left(), bar.get_right()), run_time=v.until("snowden", 0.5))

            card_year = B("2013", 84, RED)
            card_t = B("Snowden documents", 40, FG)
            card_s = T("point to an NSA backdoor\nin a NIST standard", 34, MUTED, line_spacing=1.0)
            card = boxed(VGroup(card_year, card_t, card_s).arrange(DOWN, buff=0.25), RED, buff=0.4)
            card.move_to(DOWN * 0.1)
            v.wait_until("snowden", offset=-0.2)
            self.play(FadeOut(VGroup(bar, prog, y0, y1, few, few_q)), FadeIn(card, shift=0.2 * UP), run_time=0.8)

            drbg = Mono("Dual_EC_DRBG", 44, ORANGE, weight=BOLD)
            drbg_s = label("a random number generator", 30, MUTED)
            dg = VGroup(drbg, drbg_s).arrange(DOWN, buff=0.15).move_to(RIGHT * 3.2 + UP * 2.4)
            v.wait_until("dualec", offset=-0.2)
            self.play(card.animate.move_to(LEFT * 3.2 + DOWN * 0.1), FadeIn(dg, shift=0.1 * DOWN), run_time=0.7)

            cloud_pts = curve_points(79, -3, 3)
            frame = RoundedRectangle(width=3.0, height=3.0, corner_radius=0.15, fill_color=PANEL, fill_opacity=1,
                                     stroke_color=BLUE, stroke_width=2).move_to(RIGHT * 1.75 + DOWN * 0.55)

            def to_s(pt):
                return frame.get_center() + np.array([(pt[0] / 78 - 0.5) * 2.6, (pt[1] / 78 - 0.5) * 2.6, 0])

            dots = VGroup(*[Dot(to_s(pt), radius=0.03, color=MUTED) for pt in cloud_pts])
            on = label("runs on P-256", 30, BLUE).next_to(frame, RIGHT, buff=0.3).shift(UP * 0.6)
            v.wait_until("samecurve", offset=-0.2)
            self.play(FadeIn(frame), FadeIn(dots, lag_ratio=0.01), FadeIn(on), run_time=0.8)
            P_pt, Q_pt = cloud_pts[10], cloud_pts[57]
            Pd = Dot(to_s(P_pt), radius=0.09, color=YELLOW)
            Qd = Dot(to_s(Q_pt), radius=0.09, color=YELLOW)
            Pl = M("P", size=40, color=YELLOW).next_to(Pd, UL, buff=0.05)
            Ql = M("Q", size=40, color=YELLOW).next_to(Qd, UR, buff=0.05)
            link = DashedLine(Pd.get_center(), Qd.get_center(), color=RED, stroke_width=3, dash_length=0.08)
            link_q = B("?", 44, RED).move_to(link.get_center() + RIGHT * 0.25 + UP * 0.15)
            cap = label("two unexplained\nconstants", 30, YELLOW).next_to(on, DOWN, buff=0.4).align_to(on, LEFT)
            v.wait_until("consts", offset=-0.2)
            self.play(FadeIn(Pd, scale=2), FadeIn(Qd, scale=2), FadeIn(Pl), FadeIn(Ql), run_time=0.5)
            self.play(Create(link), FadeIn(link_q), FadeIn(cap), run_time=0.6)

        # ------------------------------------------------------------ o7: suspicion
        with self.vo("o7") as v:
            self.play(FadeOut(VGroup(card, dg, frame, dots, on, Pd, Qd, Pl, Ql, link, link_q, cap)), run_time=0.5)
            wall = VGroup(*[Mono(s_, 30, MUTED) for s_ in NIST_SEEDS]).arrange(DOWN, buff=0.35).move_to(UP * 0.1)
            v.wait_until("sus", offset=-0.2)
            self.play(LaggedStart(*[FadeIn(w, shift=0.1 * UP) for w in wall], lag_ratio=0.15), run_time=0.9)
            qs = VGroup(*[B("?", 40, RED).next_to(w, RIGHT, buff=0.3) for w in wall])
            self.play(LaggedStart(*[AnimationGroup(w.animate.set_color(RED), FadeIn(q_, scale=0.5))
                                    for w, q_ in zip(wall, qs)], lag_ratio=0.25), run_time=1.6)
            quote = B("“I no longer trust the constants.”", 48, FG)
            who = label("Bruce Schneier, 2013", 30, MUTED)
            qcard = boxed(VGroup(quote, who).arrange(DOWN, buff=0.3), FG, buff=0.45, fill=PANEL)
            v.wait_until("schneier", offset=-0.2)
            self.play(wall.animate.set_opacity(0.25), qs.animate.set_opacity(0.25), FadeIn(qcard, scale=0.95), run_time=0.7)

        # ------------------------------------------------------------ o8: Jerry Solinas
        with self.vo("o8") as v:
            self.play(FadeOut(VGroup(wall, qs, qcard)), run_time=0.5)
            jerry = icon_person(MUTED, 1.4)
            j_name = B("Jerry Solinas", 50, FG)
            j_role = label("NSA mathematician", 30, MUTED)
            j_card = VGroup(jerry, VGroup(j_name, j_role).arrange(DOWN, buff=0.12, aligned_edge=LEFT)).arrange(RIGHT, buff=0.45)
            j_card.move_to(UP * 2.4)
            v.wait_until("jerry", offset=-0.2)
            self.play(FadeIn(j_card, shift=0.1 * DOWN), run_time=0.7)
            fam = label("“Solinas primes”: built for fast arithmetic", 30, PURPLE)
            prime = M(r"p = 2^{256} - 2^{224} + 2^{192} + 2^{96} - 1", size=52)
            pg = VGroup(fam, prime).arrange(DOWN, buff=0.25).move_to(UP * 0.35)
            v.wait_until("prime", offset=-0.2)
            self.play(FadeIn(fam, shift=0.1 * UP), run_time=0.5)
            self.play(Write(prime), run_time=1.0)
            p_tag = label("P-256's prime", 28, BLUE).next_to(prime, RIGHT, buff=0.3)
            self.play(FadeIn(p_tag), run_time=0.4)

            bub = icon_bubble(T("“Give Bob and Jerry a raise”", 34, FG), color=FG, tail="left")
            bub.move_to(LEFT * 2.8 + DOWN * 1.65)
            hsh = VGroup(label("SHA-1", 26, TEAL), Mono("3F7EBC0A B4866C84 …", 30, TEAL)).arrange(DOWN, buff=0.1)
            hsh.next_to(bub, RIGHT, buff=1.0)
            a_h = arrow(bub.get_right(), hsh.get_left(), buff=0.15)
            v.wait_until("phrase", offset=-0.2)
            self.play(FadeOut(pg), FadeOut(p_tag), FadeIn(bub, shift=0.1 * UP), run_time=0.7)
            self.play(GrowArrow(a_h), FadeIn(hsh, shift=0.1 * RIGHT), run_time=0.6)
            neq = VGroup(M(r"\neq", size=56, color=RED), Mono("C49D3608 …", 30, FG)).arrange(RIGHT, buff=0.25)
            neq.next_to(hsh, DOWN, buff=0.3)
            self.play(FadeIn(neq, shift=0.1 * UP), run_time=0.5)

            lost = VGroup(VGroup(cross_mark(RED, 0.35, 6), label("details: forgotten", 30, RED)).arrange(RIGHT, buff=0.2),
                          VGroup(cross_mark(RED, 0.35, 6), label("original code: never found", 30, RED)).arrange(RIGHT, buff=0.2))
            lost.arrange(DOWN, buff=0.25, aligned_edge=LEFT).move_to(RIGHT * 2.7 + UP * 0.55)
            v.wait_until("lost", offset=-0.2)
            self.play(LaggedStart(*[FadeIn(l_, shift=0.1 * LEFT) for l_ in lost], lag_ratio=0.5), run_time=1.0)

        # ------------------------------------------------------------ o9: the hunt and the bounty
        with self.vo("o9") as v:
            self.play(FadeOut(VGroup(j_card, bub, a_h, hsh, neq, lost)), run_time=0.5)
            rows = VGroup()
            for phrase, h in GUESSES:
                rows.add(VGroup(Mono(f'"{phrase}"', 28, FG), Mono(f"→ {h}…", 28, TEAL), cross_mark(RED, 0.3, 6)))
            for r_ in rows:
                r_[1].next_to(r_[0], RIGHT, buff=0.35)
                r_[2].next_to(r_[1], RIGHT, buff=0.3)
            rows.arrange(DOWN, buff=0.22, aligned_edge=LEFT).move_to(UP * 0.4)
            more = label("…and countless more", 30, MUTED).next_to(rows, DOWN, buff=0.35)
            v.wait_until("hunt", offset=0.0)
            self.play(LaggedStart(*[FadeIn(r_, shift=0.1 * UP) for r_ in rows], lag_ratio=0.22), run_time=2.2)
            self.play(FadeIn(more), run_time=0.4)

            rip = VGroup(B("Jerry Solinas", 44, FG), label("passed away in 2023", 32, MUTED)).arrange(DOWN, buff=0.2)
            v.wait_until("rip", offset=-0.2)
            self.play(FadeOut(VGroup(rows, more)), run_time=0.5)
            self.play(FadeIn(rip, shift=0.1 * UP), run_time=0.7)

            p_head = B("BOUNTY", 40, GOLD)
            p_what = label("for the NIST curve seeds", 30, FG)
            p_by = label("posted by Filippo Valsorda, 2023", 28, MUTED)
            amt = B("$12,288", 66, FG)
            poster_inner = VGroup(p_head, p_what, amt, p_by).arrange(DOWN, buff=0.25)
            poster = boxed(poster_inner, GOLD, buff=0.45).move_to(LEFT * 3.0 + DOWN * 0.1)
            v.wait_until("bounty", offset=-0.2)
            self.play(FadeOut(rip), FadeIn(poster[0]), FadeIn(p_head), FadeIn(p_what), FadeIn(p_by), run_time=0.7)
            v.wait_until("amount", offset=-0.2)
            self.play(FadeIn(amt, scale=0.8), run_time=0.6)
            times3 = B("× 3", 50, GREEN)
            donated = label("if donated to charity", 28, GREEN)
            total = B("$36,864", 66, GREEN)
            right = VGroup(times3, donated, total).arrange(DOWN, buff=0.2).move_to(RIGHT * 4.0)
            right.set_y(poster.get_y())
            a_t = arrow(poster.get_right(), [right.get_left()[0], poster.get_y(), 0], color=GREEN, buff=0.25)
            v.wait_until("triple", offset=-0.2)
            self.play(GrowArrow(a_t), FadeIn(times3), FadeIn(donated), run_time=0.6)
            self.play(FadeIn(total, scale=0.8), run_time=0.6)

            yr = B("2023", 56, MUTED).next_to(right, DOWN, buff=0.6)
            v.wait_until("years", offset=-0.2)
            self.play(FadeIn(yr), run_time=0.3)
            for y_ in ("2024", "2025", "2026"):
                ny = B(y_, 56, MUTED).move_to(yr)
                self.play(FadeOut(yr, shift=0.3 * UP), FadeIn(ny, shift=0.3 * UP), run_time=0.3)
                yr = ny
            st = stamp("UNCLAIMED", RED, 44).next_to(poster, DOWN, buff=-0.25)
            v.wait_until("unclaimed", offset=-0.15)
            self.play(FadeIn(st, scale=1.8), run_time=0.3, rate_func=rush_into)
            self.play(Wiggle(st, scale_value=1.04, rotation_angle=0.015 * TAU), run_time=0.5)

        self.wait(0.8)
        self.clear_all()

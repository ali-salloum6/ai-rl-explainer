from datetime import datetime, timezone

from common import *

# ------------------------------------------------------------------ real data
LCG_A, LCG_C, MASK48 = 0x5DEECE66D, 0xB, (1 << 48) - 1
P256_SEED = "C49D360886E704936A6678E1139D26B7819F7E90"


def p256_states() -> list[int]:
    """The 20 lrand48 states behind P-256's seed: srand48(1997-08-16 01:52:34 UTC), candidate 1842."""
    t = int(datetime(1997, 8, 16, 1, 52, 34, tzinfo=timezone.utc).timestamp())
    x, out, n = (t << 16) | 0x330E, [], 1842
    for i in range(20 * n):
        x = (LCG_A * x + LCG_C) & MASK48
        if i >= 20 * (n - 1):
            out.append(x)
    return out


STATES = p256_states()
assert "".join(f"{x >> 40:02X}" for x in STATES) == P256_SEED
BYTES = [P256_SEED[i:i + 2] for i in range(0, 40, 2)]

# Ten seeds whose recovered states use lrand48() >> 23 (the top 8 bits of each state).
TEN = ["P-192", "P-224", "P-256", "P-384", "P-521", "prime192v2", "prime192v3", "prime239v1", "prime239v2",
       "prime239v3"]

# 2D lattice used for the LLL picture: good basis u, v; bad basis is a unimodular mix of them.
U, V = np.array([3, 1]), np.array([-1, 2])
BAD1, BAD2 = 2 * U + V, 3 * U + 2 * V              # (5, 4) and (7, 7): det 7 like (u, v), 6° apart


def gauss_steps(b1, b2):
    """Lagrange–Gauss reduction (LLL in 2D): list of (op, mu, b1, b2) after each operation."""
    b1, b2 = np.array(b1), np.array(b2)
    steps = []
    while True:
        mu = int(round(np.dot(b1, b2) / np.dot(b1, b1)))
        if mu:
            b2 = b2 - mu * b1
            steps.append(("sub", mu, b1.copy(), b2.copy()))
        if np.dot(b2, b2) < np.dot(b1, b1):
            b1, b2 = b2, b1
            steps.append(("swap", 0, b1.copy(), b2.copy()))
        else:
            return steps


STEPS = gauss_steps(BAD1, BAD2)
GOOD1, GOOD2 = STEPS[-1][2], STEPS[-1][3]            # (-1, 2) and (-3, -1)
assert {tuple(GOOD1), tuple(GOOD2)} == {(-1, 2), (-3, -1)}


def cells48(top_bits: str, unknown="?", cell=0.245, gap=0.012, size=17) -> VGroup:
    """A 48-bit register whose first len(top_bits) cells are known; the rest show `unknown`."""
    g = VGroup()
    for i in range(48):
        known = i < len(top_bits)
        sq = Square(cell, stroke_color=BLUE if known else DIM, stroke_width=1.2 if known else 1,
                    fill_color=BLUE if known else FAINT, fill_opacity=0.18 if known else 1)
        ch = top_bits[i] if known else unknown
        g.add(VGroup(sq, Mono(ch, size, FG if known else MUTED).move_to(sq)))
    return g.arrange(RIGHT, buff=gap)


def byte_tile(hx: str, color=FG, size=30) -> VGroup:
    t = Mono(hx, size, color, weight=BOLD)
    r = RoundedRectangle(width=0.78, height=0.58, corner_radius=0.08, fill_color=FAINT, fill_opacity=1,
                         stroke_color=DIM, stroke_width=1.2)
    t.move_to(r)
    return VGroup(r, t)


class Lattice(VOScene):
    def construct(self):
        self.chapter(7, "Lattices")

        # ---------------------------------------------------------- l1: prime seeds keep 8 bits
        with self.vo("l1") as v:
            names = VGroup(*[pill(n, BLUE if n == "P-256" else MUTED, size=28, mono=True)
                             for n in ["P-192", "P-224", "P-256", "P-384", "P-521"]]).arrange(RIGHT, buff=0.3)
            names.move_to(UP * 3.15)
            self.play(LaggedStart(*[FadeIn(n, shift=0.1 * DOWN) for n in names], lag_ratio=0.15), run_time=0.9)
            tiles = VGroup(*[byte_tile(b) for b in BYTES]).arrange_in_grid(rows=2, cols=10, buff=(0.14, 0.16))
            tiles.move_to(UP * 1.75)
            seed_lab = label("P-256 seed  ·  20 bytes", 26, BLUE).next_to(tiles, DOWN, buff=0.18).align_to(tiles, LEFT)
            self.play(names[2].animate.scale(1.1), LaggedStart(*[FadeIn(t, shift=0.1 * UP) for t in tiles],
                                                                 lag_ratio=0.06), FadeIn(seed_lab), run_time=1.5)

            same_gen = MT(f'same generator: {span("lrand48()", CLAUDE, True)}', 28, MUTED, font=SANS)
            same_gen.next_to(tiles, DOWN, buff=0.18).align_to(tiles, RIGHT)
            self.wait(max(0.0, v.at("trim") - self.time - 3.0))
            self.play(Indicate(names[2], color=BLUE, scale_factor=1.12), run_time=0.8)
            self.play(FadeIn(same_gen, shift=0.1 * UP), run_time=0.6)

            full = format(STATES[0], "048b")
            reg = bit_cells(full, cell=0.245, gap=0.012, on=FG, off=MUTED, digit_size=17).move_to(DOWN * 0.45)
            reg_lab = MT(f'state  ·  {span("48 bits", FG, True)}', 28, MUTED).next_to(reg, UP, buff=0.22).align_to(reg, LEFT)
            reg_hex = Mono(f"0x{STATES[0]:012X}", 28, MUTED).next_to(reg, UP, buff=0.22).align_to(reg, RIGHT)
            v.wait_until("trim", offset=-0.3)
            self.play(FadeIn(reg_lab), FadeIn(reg_hex), LaggedStart(*[FadeIn(c) for c in reg], lag_ratio=0.015),
                      run_time=1.0)
            top8 = VGroup(*reg[:8])
            shift_lab = Mono("lrand48() >> 23  =  top 8 bits", 28, BLUE).next_to(reg, DOWN, buff=0.45)
            self.play(top8.animate.set_color(BLUE), FadeIn(shift_lab, shift=0.1 * UP), run_time=0.6)

            v.wait_until("show", offset=-0.2)
            hi = SurroundingRectangle(tiles[0], color=BLUE, buff=0.06, corner_radius=0.1, stroke_width=3)
            flying = top8.copy()
            self.play(Transform(flying, tiles[0][1].copy().set_color(BLUE)), Create(hi), run_time=0.9)
            self.remove(flying)
            tiles[0][1].set_color(BLUE)
            br_known = Brace(top8, DOWN, buff=0.1, color=BLUE)
            known_lab = label("8 bits shown", 28, BLUE).next_to(br_known, DOWN, buff=0.1)
            self.play(FadeOut(shift_lab), GrowFromCenter(br_known), FadeIn(known_lab), run_time=0.6)

            rest = VGroup(*reg[8:])
            q_cells = cells48("", cell=0.245)[8:].move_to(rest)
            for c in q_cells:
                c[0].set_fill(YELLOW, 0.1).set_stroke(YELLOW, 1)
                c[1].set_color(YELLOW)
            br_hid = Brace(rest, DOWN, buff=0.1, color=YELLOW)
            hid_lab = label("40 hidden bits", 28, YELLOW).next_to(br_hid, DOWN, buff=0.1)
            v.wait_until("hide", offset=-0.2)
            self.play(ReplacementTransform(rest, q_cells), FadeOut(reg_hex), GrowFromCenter(br_hid),
                      FadeIn(hid_lab), run_time=0.9)

        # ---------------------------------------------------------- l2: why lattices
        with self.vo("l2") as v:
            tril = pill("2⁴⁰ ≈ 1.1 trillion possibilities", YELLOW, size=28).next_to(hid_lab, DOWN, buff=0.2)
            self.play(FadeIn(tril, shift=0.1 * UP), run_time=0.6)

            # which 8 bits? slide the visible window along the register
            v.wait_until("which", offset=-0.2)
            window = SurroundingRectangle(top8, color=BLUE, buff=0.05, stroke_width=4, corner_radius=0.05)
            which = B("which 8?", 30, BLUE).next_to(window, UP, buff=0.12)
            self.play(FadeOut(VGroup(br_known, known_lab, br_hid, hid_lab, tril, reg_lab)), Create(window),
                      FadeIn(which), run_time=0.6)
            step = reg[1].get_center()[0] - reg[0].get_center()[0]
            self.play(VGroup(window, which).animate.shift(RIGHT * 40 * step), run_time=1.6,
                      rate_func=rate_functions.ease_in_out_sine)
            self.play(VGroup(window, which).animate.shift(LEFT * 40 * step), run_time=1.3,
                      rate_func=rate_functions.ease_in_out_sine)
            self.play(FadeOut(which), FadeOut(window), run_time=0.3)

            eq1 = M(r"x_i", r"=", r"{{h_i}}\cdot 2^{40}", r"+", r"{{\ell_i}}", size=54,
                    colors={"h_i": BLUE, r"\ell_i": YELLOW}).move_to(UP * 0.85)
            h_part = [p for p in eq1.submobjects if getattr(p, "tex_string", "").strip() == "h_i"][0]
            l_part = [p for p in eq1.submobjects if getattr(p, "tex_string", "").strip() == r"\ell_i"][0]
            h_lab = label("known: a seed byte", 26, BLUE).next_to(h_part, DOWN, buff=0.3).shift(LEFT * 0.3)
            l_lab = label("small: < 2⁴⁰", 26, YELLOW).next_to(l_part, DOWN, buff=0.3).shift(RIGHT * 0.2)
            v.wait_until("write", offset=-0.6)
            reg_now = VGroup(top8, q_cells)
            self.play(FadeOut(VGroup(names, tiles, seed_lab, same_gen, hi)), reg_now.animate.move_to(UP * 2.45),
                      run_time=0.6)
            self.play(Write(eq1), run_time=0.9)
            self.play(FadeIn(h_lab, shift=0.1 * UP), FadeIn(l_lab, shift=0.1 * UP), run_time=0.5)

            eq2 = M(r"x_{i+1} \equiv a\,x_i + c \pmod{2^{48}}", size=50).move_to(DOWN * 0.75)
            lin = label("linear", 28, CLAUDE).next_to(eq2, RIGHT, buff=0.4)
            v.wait_until("linear", offset=-0.2)
            self.play(Write(eq2), run_time=1.0)
            self.play(FadeIn(lin, shift=0.1 * UP), Circumscribe(eq2, color=CLAUDE, buff=0.12), run_time=0.9)

            # small unknowns + linear equations -> lattice
            mini = VGroup(*[Dot(np.array([i * 0.32 + j * 0.12, j * 0.3, 0]), radius=0.045, color=FG)
                            for i in range(-3, 4) for j in range(-2, 3)])
            arrow_in = MT(f'small unknowns + linear equations  →  {span("lattice", CLAUDE, True)}', 32, FG)
            res = VGroup(arrow_in, mini.scale(0.85)).arrange(RIGHT, buff=0.5).move_to(DOWN * 2.45)
            v.wait_until("for", offset=-0.2)
            self.play(FadeIn(arrow_in, shift=0.1 * UP), run_time=0.6)
            self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in mini], lag_ratio=0.02), run_time=0.8)

        # ---------------------------------------------------------- l3: what a lattice is
        with self.vo("l3") as v:
            self.play(FadeOut(VGroup(top8, q_cells, eq1, h_lab, l_lab, eq2, lin, arrow_in, mini)),
                      run_time=0.6)
            s = 0.34
            O = np.array([-3.4, -2.4, 0])
            PX = 4.3  # centre of the text panel on the right

            def P(vec):
                return O + s * np.array([vec[0], vec[1], 0])

            pts = []
            for i in range(-12, 13):
                for j in range(-12, 13):
                    q = P(i * U + j * V)
                    if -6.55 <= q[0] <= 1.55 and -3.45 <= q[1] <= 3.45:
                        pts.append(q)
            pts.sort(key=lambda q: np.linalg.norm(q - O))
            dots = VGroup(*[Dot(q, radius=0.05, color=FG, fill_opacity=0.75) for q in pts])
            o_dot = Dot(O, radius=0.08, color=FG)
            self.play(LaggedStart(*[FadeIn(d, scale=0.3) for d in dots], lag_ratio=0.012), FadeIn(o_dot),
                      run_time=1.6)
            title = B("A lattice", 44, FG).move_to(RIGHT * PX + UP * 2.9)
            sub = T("a perfectly regular grid", 28, MUTED).next_to(title, DOWN, buff=0.2)
            self.play(FadeIn(title, shift=0.1 * LEFT), FadeIn(sub), run_time=0.6)

            def vec_arrow(vec, color, start=None):
                st = O if start is None else start
                return Arrow(st, st + s * np.array([vec[0], vec[1], 0]), buff=0, color=color, stroke_width=6,
                             max_tip_length_to_length_ratio=0.3, max_stroke_width_to_length_ratio=14, tip_length=0.17)

            u_arr, v_arr = vec_arrow(U, BLUE), vec_arrow(V, BLUE)
            u_lab = M(r"b_1", size=36, color=BLUE).next_to(u_arr.get_end(), DR, buff=0.05)
            v_lab = M(r"b_2", size=36, color=BLUE).next_to(v_arr.get_end(), UL, buff=0.05)
            v.wait_until("basis", offset=-0.2)
            self.play(GrowArrow(u_arr), GrowArrow(v_arr), FadeIn(u_lab), FadeIn(v_lab), run_time=0.8)
            combo_eq = M(r"\text{point} = m\,b_1 + n\,b_2", size=40, color=FG).move_to(RIGHT * PX + UP * 1.3)
            combo_lab = label("m, n: whole numbers", 28, MUTED).next_to(combo_eq, DOWN, buff=0.2)
            self.play(Write(combo_eq), FadeIn(combo_lab), run_time=0.8)
            # walk to 3·b1 + 2·b2, tip to tail
            path = VGroup()
            cur = O.copy()
            for vec in (U, U, U, V, V):
                a = vec_arrow(vec, YELLOW, start=cur).set_stroke(width=4)
                path.add(a)
                cur = a.get_end()
            target = Dot(cur, radius=0.11, color=YELLOW)
            walk_lab = M(r"3\,b_1 + 2\,b_2", size=34, color=YELLOW).next_to(target, UR, buff=0.08)
            self.play(LaggedStart(*[GrowArrow(a) for a in path], lag_ratio=0.6), run_time=1.6)
            self.play(FadeIn(target, scale=1.6), FadeIn(walk_lab), run_time=0.4)

            bad1, bad2 = vec_arrow(BAD1, RED), vec_arrow(BAD2, RED)
            bad_par = Polygon(O, P(BAD1), P(BAD1 + BAD2), P(BAD2), fill_color=RED, fill_opacity=0.15,
                              stroke_color=RED, stroke_width=1.5)
            bad_lab = VGroup(B("bad basis", 32, RED), T("long, nearly parallel", 28, FG)).arrange(DOWN, buff=0.1)
            bad_lab.move_to(RIGHT * PX + DOWN * 0.3)
            v.wait_until("bad", offset=-0.2)
            self.play(FadeOut(VGroup(path, target, walk_lab)), FadeOut(VGroup(u_arr, v_arr, u_lab, v_lab)),
                      run_time=0.4)
            self.play(GrowArrow(bad1), GrowArrow(bad2), FadeIn(bad_par), FadeIn(bad_lab, shift=0.1 * LEFT),
                      run_time=1.0)
            ang = Angle(Line(O, P(BAD1)), Line(O, P(BAD2)), radius=1.35, color=YELLOW, stroke_width=3)
            deg = np.degrees(np.arctan2(BAD2[1], BAD2[0]) - np.arctan2(BAD1[1], BAD1[0]))
            ang_lab = Mono(f"{deg:.0f}°", 26, YELLOW).next_to(ang, RIGHT, buff=0.22).shift(DOWN * 0.3)
            self.wait(0.6)
            self.play(Create(ang), FadeIn(ang_lab), run_time=0.7)

            good1, good2 = vec_arrow(GOOD1, GREEN), vec_arrow(GOOD2, GREEN)
            good_par = Polygon(O, P(GOOD1), P(GOOD1 + GOOD2), P(GOOD2),
                               fill_color=GREEN, fill_opacity=0.22, stroke_color=GREEN, stroke_width=1.5)
            good_lab = VGroup(B("good basis", 32, GREEN), T("short, nearly\nperpendicular", 28, FG, line_spacing=0.9))
            good_lab.arrange(DOWN, buff=0.1).move_to(RIGHT * PX + DOWN * 1.75)
            same = label("same lattice · same area", 26, MUTED).next_to(good_lab, DOWN, buff=0.25)
            v.wait_until("good", offset=-0.2)
            self.play(GrowArrow(good1), GrowArrow(good2), FadeIn(good_par), FadeIn(good_lab, shift=0.1 * LEFT),
                      run_time=1.0)
            self.play(FadeIn(same), run_time=0.4)

        # ---------------------------------------------------------- l4: LLL
        with self.vo("l4") as v:
            self.play(FadeOut(VGroup(good1, good2, good_par, good_lab, same, bad_lab, combo_eq, combo_lab, title, sub,
                                     ang, ang_lab)),
                      run_time=0.6)
            year = Mono("1982", 40, MUTED).move_to(RIGHT * (PX - 1.2) + UP * 2.95)
            self.play(FadeIn(year, shift=0.1 * DOWN), run_time=0.5)
            people = VGroup()
            for first, last in (("Arjen", "Lenstra"), ("Hendrik", "Lenstra"), ("László", "Lovász")):
                f = T(first, 28, MUTED)
                l = T(last, 28, FG, weight=BOLD)
                people.add(VGroup(f, l).arrange(RIGHT, buff=0.15, aligned_edge=DOWN))
            people.arrange(DOWN, buff=0.16, aligned_edge=LEFT).next_to(year, DOWN, buff=0.3).align_to(year, LEFT)
            for i, person in enumerate(people):
                self.wait(max(0.0, v.at("lll") + 1.4 + 1.25 * i - self.time))
                self.play(FadeIn(person, shift=0.1 * RIGHT), run_time=0.45)
            lll = B("LLL", 64, YELLOW).next_to(year, RIGHT, buff=0.45).align_to(year, DOWN).shift(DOWN * 0.05)
            initials = VGroup(*[person[1][0] for person in people])
            self.wait(max(0.0, v.at("reduce") - 2.0 - self.time))
            self.play(initials.animate.set_color(YELLOW), run_time=0.4)
            self.play(TransformFromCopy(initials, lll), run_time=0.7)
            head = VGroup(year, lll)
            who = people
            b1_lab = M(r"b_1", size=36, color=RED).next_to(bad1.get_end(), DR, buff=0.06)
            b2_lab = M(r"b_2", size=36, color=RED).next_to(bad2.get_end(), UL, buff=0.06)
            self.play(FadeIn(b1_lab), FadeIn(b2_lab), Indicate(VGroup(bad1, bad2), color=RED, scale_factor=1.03),
                      run_time=0.6)

            log = VGroup()
            log_anchor = RIGHT * 2.75 + UP * 0.45
            v.wait_until("reduce", offset=-0.3)
            arr1, arr2 = bad1, bad2
            par = bad_par
            for op, mu, nb1, nb2 in STEPS:
                if op == "sub":
                    sign = "-" if mu > 0 else "+"
                    entry = M(rf"b_2 \leftarrow b_2 {sign} {abs(mu)}\,b_1", size=34, color=FG)
                else:
                    entry = T("swap", 28, MUTED)
                if len(log):
                    entry.next_to(log, DOWN, buff=0.13, aligned_edge=LEFT)
                else:
                    entry.move_to(log_anchor, aligned_edge=LEFT)
                log.add(entry)
                if op == "sub":
                    new2 = vec_arrow(nb2, ORANGE)
                    new_par = Polygon(O, P(nb1), P(nb1 + nb2), P(nb2), fill_color=ORANGE, fill_opacity=0.15,
                                      stroke_color=ORANGE, stroke_width=1.5)
                    self.play(Transform(arr2, new2), Transform(par, new_par), FadeIn(entry, shift=0.1 * RIGHT),
                              b2_lab.animate.next_to(new2.get_end(), UL, buff=0.05).set_color(ORANGE),
                              arr1.animate.set_color(ORANGE), b1_lab.animate.set_color(ORANGE), run_time=0.75)
                else:
                    arr1, arr2 = arr2, arr1
                    self.play(FadeIn(entry, shift=0.1 * RIGHT), b1_lab.animate.next_to(arr1.get_end(), UL, buff=0.05),
                              b2_lab.animate.next_to(arr2.get_end(), DR, buff=0.05), run_time=0.45)
            done = MT(f'{span("done", GREEN, True)}  ✓', 30, FG)
            done.next_to(log, DOWN, buff=0.18, aligned_edge=LEFT)
            final_par = Polygon(O, P(GOOD1), P(GOOD1 + GOOD2), P(GOOD2),
                                fill_color=GREEN, fill_opacity=0.22, stroke_color=GREEN, stroke_width=1.5)
            self.play(VGroup(arr1, arr2, b1_lab, b2_lab).animate.set_color(GREEN), Transform(par, final_par),
                      FadeIn(done, shift=0.1 * RIGHT), run_time=0.6)
            mantra = B("subtract · swap · repeat", 30, YELLOW).move_to(RIGHT * (PX + 0.1) + DOWN * 3.2)
            v.wait_until("steps", offset=-0.1)
            self.play(FadeIn(mantra, shift=0.1 * UP), run_time=0.6)

        # ---------------------------------------------------------- l5: the payoff
        with self.vo("l5") as v:
            self.play(FadeOut(VGroup(dots, o_dot, arr1, arr2, par, b1_lab, b2_lab, log, done, mantra, head, who)),
                      run_time=0.6)
            mat = M(r"\begin{bmatrix} 1 & a & a^2 & a^3 \\ 0 & M & 0 & 0 \\ 0 & 0 & M & 0 \\ 0 & 0 & 0 & M \end{bmatrix}",
                    size=40, color=FG)
            mat_lab = label("the generator's equations", 26, MUTED).next_to(mat, DOWN, buff=0.2)
            mod_lab = M(r"M = 2^{48}", size=32, color=MUTED).next_to(mat_lab, DOWN, buff=0.12)
            g_mat = VGroup(mat, mat_lab, mod_lab).move_to(LEFT * 4.35 + UP * 1.35)
            box = boxed(B("LLL", 44, YELLOW), YELLOW, buff=0.3).move_to(LEFT * 0.9 + UP * 1.55)
            a1 = Arrow(g_mat.get_right() + UP * 0.2, box.get_left(), buff=0.2, color=MUTED, stroke_width=4)
            self.play(FadeIn(g_mat, shift=0.2 * RIGHT), run_time=0.8)
            self.play(GrowArrow(a1), FadeIn(box, scale=0.9), run_time=0.6)

            hid = [x & ((1 << 40) - 1) for x in STATES[:3]]
            vec = M(r"\begin{bmatrix} \ell_0 \\ \ell_1 \\ \ell_2 \\ \vdots \end{bmatrix}", size=40, color=YELLOW)
            vals = VGroup(*[Mono(f"0x{h:010X}", 28, GREEN) for h in hid] + [Mono("…", 28, GREEN)])
            vals.arrange(DOWN, buff=0.22, aligned_edge=LEFT)
            out = VGroup(vec, vals).arrange(RIGHT, buff=0.35).move_to(RIGHT * 3.9 + UP * 1.4)
            a2 = Arrow(box.get_right(), vec.get_left(), buff=0.2, color=MUTED, stroke_width=4)
            sv_lab = label("a short vector", 26, YELLOW).next_to(vec, UP, buff=0.15)
            v.wait_until("short", offset=-0.2)
            self.play(GrowArrow(a2), FadeIn(vec, shift=0.1 * RIGHT), FadeIn(sv_lab), run_time=0.7)
            self.play(LaggedStart(*[FadeIn(x, shift=0.1 * RIGHT) for x in vals], lag_ratio=0.25), run_time=0.9)

            state = MT(f'{span("C4", BLUE, True)}{span(f"{hid[0]:010X}", GREEN, True)}', 40, FG, font=MONO)
            state_lab = label("first state, fully recovered", 26, MUTED)
            st_g = VGroup(Mono("x₀ = 0x", 40, MUTED), state).arrange(RIGHT, buff=0.05)
            st_all = VGroup(st_g, state_lab).arrange(DOWN, buff=0.15).move_to(DOWN * 0.75)
            self.play(FadeIn(st_all, shift=0.1 * UP), run_time=0.6)

            ecdsa = MT(f'The same tool breaks ECDSA when nonces {span("k", ORANGE, True)} are biased:\n'
                       f'it recovers the private key {span("d", GOLD, True)}', 30, FG, line_spacing=1.1)
            ecdsa_box = boxed(ecdsa, DIM, buff=0.25).move_to(DOWN * 2.15)
            v.wait_until("biased", offset=-0.2)
            self.play(FadeIn(ecdsa_box, shift=0.1 * UP), run_time=0.7)
            self.wait(1.2)
            self.play(Circumscribe(ecdsa_box, color=ORANGE, buff=0.05), run_time=1.2)

            lock = icon_padlock(GREEN, 0.9)
            unlocked = T("random number generator: unlocked", 32, GREEN)
            ul = VGroup(lock, unlocked).arrange(RIGHT, buff=0.35).move_to(DOWN * 3.25)
            v.wait_until("unlock", offset=-0.3)
            self.play(FadeIn(ul, shift=0.1 * UP), run_time=0.5)
            shackle = VGroup(lock[0], lock[1])
            self.play(shackle.animate.shift(UP * 0.18).rotate(-25 * DEGREES, about_point=lock[0][1].get_bottom()),
                      run_time=0.5)

        # ---------------------------------------------------------- l6: every window
        with self.vo("l6") as v:
            self.play(FadeOut(VGroup(g_mat, box, a1, a2, vec, vals, sv_lab, st_all, ecdsa_box, ul)), run_time=0.45)
            cols, rows = 41, 10
            cw, ch, gap = 0.19, 0.27, 0.02
            grid = VGroup()
            for r in range(rows):
                row = VGroup(*[Rectangle(width=cw, height=ch, stroke_width=0, fill_color=FAINT, fill_opacity=1)
                               for _ in range(cols)]).arrange(RIGHT, buff=gap)
                grid.add(row)
            grid.arrange(DOWN, buff=0.06).move_to(UP * 0.85 + RIGHT * 0.45)
            names = VGroup(*[Mono(n, 24, MUTED) for n in TEN])
            for n, row in zip(names, grid):
                n.next_to(row, LEFT, buff=0.25)
            ax = label("bit position of the 8 kept bits", 26, MUTED).next_to(grid, DOWN, buff=0.45)
            t0 = Mono("0", 22, MUTED).next_to(grid[-1][0], DOWN, buff=0.12)
            t40 = Mono("40", 22, MUTED).next_to(grid[-1][-1], DOWN, buff=0.12)
            head = T("Run the solver at every window", 34, FG).move_to(UP * 3.3)
            self.play(FadeIn(head), FadeIn(names), FadeIn(grid), FadeIn(VGroup(ax, t0, t40)), run_time=0.55)
            scan = Rectangle(width=cw + 0.04, height=grid.height + 0.12, stroke_color=YELLOW, stroke_width=3)
            scan.move_to(grid[0][0]).align_to(grid, UP).shift(UP * 0.06)
            self.add(scan)
            sweep = [AnimationGroup(scan.animate.set_x(grid[0][c].get_x()),
                                    *[grid[r][c].animate.set_fill(RED, 0.28) for r in range(rows)])
                     for c in range(cols - 1)]
            self.play(Succession(*sweep), run_time=1.25, rate_func=linear)
            self.play(scan.animate.set_x(grid[0][-1].get_x()), run_time=0.1)

            v.wait_until("lit", offset=-0.2)
            last = VGroup(*[row[-1] for row in grid])
            top_lab = MT(f'{span("top 8 bits", GREEN, True)} = lrand48() &gt;&gt; 23', 28, FG)
            top_lab.next_to(grid, UP, buff=0.25).align_to(grid, RIGHT)
            self.play(last.animate.set_fill(GREEN, 1), scan.animate.set_stroke(GREEN), FadeIn(top_lab, shift=0.1 * DOWN),
                      run_time=0.8)

            nist_br = Brace(VGroup(*names[:5]), LEFT, buff=0.12, color=BLUE)
            ansi_br = Brace(VGroup(*names[5:]), LEFT, buff=0.12, color=PURPLE)
            nist_l = label("NIST", 26, BLUE).rotate(PI / 2).next_to(nist_br, LEFT, buff=0.1)
            ansi_l = label("ANSI", 26, PURPLE).rotate(PI / 2).next_to(ansi_br, LEFT, buff=0.1)
            v.wait_until("ten", offset=-0.2)
            self.play(VGroup(*names[:5]).animate.set_color(BLUE), GrowFromCenter(nist_br), FadeIn(nist_l), run_time=0.6)
            self.play(VGroup(*names[5:]).animate.set_color(PURPLE), GrowFromCenter(ansi_br), FadeIn(ansi_l), run_time=0.6)

            regen = MT(f'each 48-bit state regenerates {span("160 / 160", GREEN, True)} seed bits', 32, FG)
            p256 = Mono(f"0x{STATES[0]:012X}  →  " + " ".join(P256_SEED[i:i + 8] for i in range(0, 40, 8)), 24, MUTED)
            rg = VGroup(regen, p256).arrange(DOWN, buff=0.16).next_to(ax, DOWN, buff=0.28)
            v.wait_until("regen", offset=-0.2)
            self.play(FadeOut(VGroup(t0, t40)), FadeIn(regen, shift=0.1 * UP), run_time=0.6)
            self.play(FadeIn(p256, shift=0.1 * UP), run_time=0.6)

            fluke = pill("odds of a fluke: < 1 in 2¹⁰⁰", YELLOW, size=30).next_to(rg, DOWN, buff=0.25)
            v.wait_until("accident", offset=-0.2)
            self.play(FadeIn(fluke, scale=0.85), run_time=0.6)

        self.clear_all()

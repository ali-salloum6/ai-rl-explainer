from common import *

# A real P-256 signature over the message shown on screen (demo key and nonce derived
# from fixed strings; verified with u1*G + u2*Q). Only prefixes are displayed.
MSG = "Pay Bob $100"
E_HEX = "ab08a25e535550241188537da46324a9137e8b80b38f2e965da5b59fb5addaff"  # SHA-256(MSG)
R_HEX = "13e8bead7dfe11521f0e3f831f9d98a9db9995dfb63f79dda4162e0e55368259"
S_HEX = "8bb735d94535a2217e6427c1cc1461b85c31afb5c473d9828ca60a48e7a0a4b2"
QX_HEX = "328d9cf2efa1e12578e698d6997ac9469649c9779ed065651b873b662e633731"

ALICE = PINK
BOB = BLUE

WHITE_R = "#FFFFFF"  # R is drawn in pure white so it can be found again by colour


def _hx(c):
    return ManimColor(c).to_hex()[1:].upper()


_MACROS = {
    "vd": (GOLD, "d"), "vQ": (BLUE, "Q"), "vk": (ORANGE, "k"), "vkinv": (ORANGE, "k^{-1}"),
    "ve": (TEAL, "e"), "vea": (TEAL, "e_1"), "veb": (TEAL, "e_2"), "vr": (GREEN, "r"),
    "vs": (GREEN, "s"), "vsa": (GREEN, "s_1"), "vsb": (GREEN, "s_2"), "vG": (PURPLE, "G"),
    "vR": (WHITE_R, "R"), "vX": (FG, "X"), "vua": (YELLOW, "u_1"), "vub": (YELLOW, "u_2"),
}
TPL = TexTemplate()
TPL.add_to_preamble(r"\usepackage{xcolor}" + "".join(
    rf"\newcommand{{\{name}}}{{\textcolor[HTML]{{{_hx(col)}}}{{{body}}}}}" for name, (col, body) in _MACROS.items()))


def eq(tex, size=48, **kw):
    """MathTex using colour macros (\\vd, \\vQ, \\vk, \\vkinv, \\ve, \\vr, \\vs, \\vG, \\vR, ...)."""
    return MathTex(tex, font_size=size, color=FG, tex_template=TPL, **kw)


def glyphs(m, color):
    """Glyphs of MathTex `m` drawn in `color` (the coloured variables)."""
    target = ManimColor(color).to_hex().upper()
    return VGroup(*[g for g in m.family_members_with_points()
                    if g.get_fill_color().to_hex().upper() == target])


# ---------------------------------------------------------------- toy curve (y^2 = x^3 - 3x + 3 mod 79)
TP, TA, TB = 79, -3, 3


def toy_points():
    sq = {}
    for y in range(TP):
        sq.setdefault(y * y % TP, []).append(y)
    return [(x, y) for x in range(TP) for y in sq.get((x ** 3 + TA * x + TB) % TP, [])]


def toy_add(P, Q):
    if P is None:
        return Q
    if Q is None:
        return P
    if P[0] == Q[0] and (P[1] + Q[1]) % TP == 0:
        return None
    if P == Q:
        lam = (3 * P[0] * P[0] + TA) * pow(2 * P[1], -1, TP) % TP
    else:
        lam = (Q[1] - P[1]) * pow(Q[0] - P[0], -1, TP) % TP
    x = (lam * lam - P[0] - Q[0]) % TP
    return (x, (lam * (P[0] - x) - P[1]) % TP)


def toy_mul(k, P):
    R = None
    while k:
        if k & 1:
            R = toy_add(R, P)
        P = toy_add(P, P)
        k >>= 1
    return R


def toy_cloud(size=1.9, dot=0.035, color=MUTED):
    """Square inset with every point of the toy curve; returns (group, to_scene)."""
    frame = RoundedRectangle(width=size + 0.3, height=size + 0.3, corner_radius=0.12, fill_color=PANEL,
                             fill_opacity=1, stroke_color=DIM, stroke_width=1.2)

    def to_scene(pt):
        return frame.get_center() + np.array([(pt[0] / (TP - 1) - 0.5) * size, (pt[1] / (TP - 1) - 0.5) * size, 0])

    dots = VGroup(*[Dot(to_scene(pt), radius=dot, color=color) for pt in toy_points()])
    g = VGroup(frame, dots)
    g.to_scene = to_scene
    return g


# ---------------------------------------------------------------- small pictures
def dice(color=ORANGE, s=0.85):
    sq = RoundedRectangle(width=1, height=1, corner_radius=0.2, fill_color=color, fill_opacity=0.16,
                          stroke_color=color, stroke_width=4)
    pips = VGroup(*[Dot(np.array([x, y, 0]) * 0.27, radius=0.075, color=color)
                    for x, y in ((-1, 1), (1, 1), (0, 0), (-1, -1), (1, -1))])
    return VGroup(sq, pips).scale_to_fit_width(s)


def lattice_icon(color=PURPLE, w=2.6):
    v1, v2 = np.array([0.5, 0.0, 0]), np.array([0.18, 0.42, 0])
    dots = VGroup(*[Dot(i * v1 + j * v2, radius=0.065, color=color) for i in range(5) for j in range(4)])
    o = v1 + v2
    cell = Polygon(o, o + v1, o + v1 + v2, o + v2, fill_color=YELLOW, fill_opacity=0.15, stroke_width=0)
    a1 = Arrow(o, o + v1, buff=0, color=YELLOW, stroke_width=6, tip_length=0.14, max_tip_length_to_length_ratio=0.5)
    a2 = Arrow(o, o + v2, buff=0, color=YELLOW, stroke_width=6, tip_length=0.14, max_tip_length_to_length_ratio=0.5)
    g = VGroup(cell, dots, a1, a2)
    return g.scale(w / g.width)


def message_card(size=32):
    t = Mono(MSG, size, FG)
    box = RoundedRectangle(width=t.width + 0.6, height=t.height + 0.5, corner_radius=0.14, fill_color=FAINT,
                           fill_opacity=1, stroke_color=FG, stroke_width=1.5)
    t.move_to(box)
    return VGroup(box, t)


def hex_short(h, n=8):
    return h[:n] + "…"


class ECDSA(VOScene):
    def construct(self):
        self.chapter(4, "ECDSA: signing with a curve")

        # ------------------------------------------------------------ layout of the signing rows
        alice = icon_person(ALICE, 1.1, name="Alice")
        msg = message_card(30)
        sha = boxed(B("SHA-256", 32, TEAL), TEAL, buff=0.24)
        e_lab = eq(r"\ve =", 54)
        e_val = Mono(hex_short(E_HEX), 34, TEAL)
        e_row = VGroup(e_lab, e_val).arrange(RIGHT, buff=0.2)
        row_a = VGroup(alice, msg, sha, e_row).arrange(RIGHT, buff=0.72).move_to(UP * 2.75)
        a1 = arrow(msg.get_right(), sha.get_left(), buff=0.1)
        a2 = arrow(sha.get_right(), e_row.get_left(), buff=0.1)
        bits = label("256-bit fingerprint", 26, MUTED).next_to(e_val, DOWN, buff=0.15)

        dk = dice(ORANGE, 0.95)
        k_eq = eq(r"\vk", 66)
        k_txt = label("random", 28, ORANGE)
        k_grp = VGroup(dk, VGroup(k_eq, k_txt).arrange(DOWN, buff=0.05)).arrange(RIGHT, buff=0.3)
        R_eq = eq(r"\vR = \vk \cdot \vG", 54)
        cloud = toy_cloud(1.75, 0.03)
        r_eq = eq(r"\vr = x\text{-coord of } \vR", 46)
        r_val = Mono(hex_short(R_HEX), 32, GREEN)
        r_grp = VGroup(r_eq, r_val).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        row_b = VGroup(k_grp, R_eq, cloud, r_grp).arrange(RIGHT, buff=0.55).move_to(UP * 0.75)
        a3 = arrow(k_grp.get_right(), R_eq.get_left(), buff=0.12)
        a4 = arrow(cloud.get_right(), r_grp.get_left(), buff=0.12)

        # ------------------------------------------------------------ d1: hash the message
        with self.vo("d1") as v:
            self.play(FadeIn(alice, shift=0.2 * RIGHT), run_time=0.6)
            v.wait_until("msg", offset=-0.2)
            self.play(FadeIn(msg, shift=0.15 * RIGHT), run_time=0.6)
            v.wait_until("hash", offset=-0.2)
            self.play(GrowArrow(a1), FadeIn(sha, scale=0.8), run_time=0.6)
            self.play(Indicate(sha[1], color=TEAL, scale_factor=1.1), run_time=0.5)
            self.play(GrowArrow(a2), AddTextLetterByLetter(e_val, time_per_char=0.06), run_time=0.9)
            self.play(FadeIn(bits, shift=0.1 * UP), run_time=0.5)
            v.wait_until("e", offset=-0.2)
            self.play(FadeIn(e_lab, shift=0.1 * RIGHT), Indicate(e_val, color=TEAL, scale_factor=1.08), run_time=0.7)

        # ------------------------------------------------------------ d2: nonce, R, r
        with self.vo("d2") as v:
            v.wait_until("k", offset=-0.2)
            self.play(FadeIn(dk, scale=0.6), run_time=0.4)
            self.play(Rotate(dk, PI / 2), FadeIn(k_eq[0] if len(k_eq) == 1 else k_eq), FadeIn(k_txt), run_time=0.6)
            once = pill("used only once", ORANGE, size=26).next_to(k_grp, DOWN, buff=0.3)
            self.play(FadeIn(once, shift=0.1 * UP), run_time=0.5)
            nonce = pill("the nonce", ORANGE, size=28).move_to(once)
            v.wait_until("nonce", offset=-0.2)
            self.play(ReplacementTransform(once, nonce), Indicate(k_eq, color=ORANGE), run_time=0.6)

            pts = toy_points()
            G_pt = pts[3]
            R_pt = toy_mul(13, G_pt)
            g_dot = Dot(cloud.to_scene(G_pt), radius=0.08, color=PURPLE)
            r_dot = Dot(cloud.to_scene(R_pt), radius=0.08, color=FG)
            g_lab = eq(r"\vG", 36).next_to(g_dot, RIGHT, buff=0.08)
            r_lab = eq(r"\vR", 36).next_to(r_dot, UP, buff=0.06)
            hop = CurvedArrow(g_dot.get_center(), r_dot.get_center(), angle=-1.0, color=ORANGE,
                              stroke_width=3, tip_length=0.15)
            v.wait_until("R", offset=-0.2)
            self.play(GrowArrow(a3), Write(R_eq), FadeIn(cloud), run_time=0.9)
            self.play(FadeIn(g_dot, scale=2), FadeIn(g_lab), run_time=0.3)
            self.play(Create(hop), run_time=0.45)
            self.play(FadeIn(r_dot, scale=2), FadeIn(r_lab), run_time=0.3)

            proj = DashedLine(r_dot.get_center(), [r_dot.get_x(), cloud.get_bottom()[1] + 0.12, 0],
                              color=GREEN, stroke_width=3, dash_length=0.06)
            v.wait_until("r", offset=-0.2)
            self.play(Create(proj), GrowArrow(a4), FadeIn(r_eq, shift=0.1 * RIGHT), run_time=0.7)
            self.play(FadeIn(r_val), run_time=0.4)

        # ------------------------------------------------------------ d3: s
        with self.vo("d3") as v:
            s_eq = eq(r"\vs = \vkinv\,(\ve + \vr \cdot \vd) \bmod n", 64).move_to(DOWN * 1.3)
            v.wait_until("s", offset=-0.2)
            self.play(Write(s_eq), run_time=1.3)
            n_note = label("n = number of points on the curve", 28, MUTED).next_to(s_eq, DOWN, buff=0.3)
            self.play(FadeIn(n_note, shift=0.1 * UP), run_time=0.5)

            d_part = glyphs(s_eq, GOLD)
            d_box = SurroundingRectangle(d_part, color=GOLD, buff=0.08, corner_radius=0.06, stroke_width=3)
            d_tag = VGroup(icon_key(GOLD, 0.6), label("private key", 28, GOLD)).arrange(RIGHT, buff=0.12)
            d_tag.next_to(d_box, UP, buff=0.14)
            k_part = glyphs(s_eq, ORANGE)
            k_box = SurroundingRectangle(k_part, color=ORANGE, buff=0.08, corner_radius=0.06, stroke_width=3)
            k_tag = label("masked by the random k", 28, ORANGE).next_to(k_box, DOWN, buff=0.25).align_to(s_eq, LEFT)
            v.wait_until("mask", offset=-0.2)
            self.play(FadeOut(n_note), run_time=0.25)
            self.play(Create(d_box), FadeIn(d_tag, shift=0.1 * UP), run_time=0.6)
            self.play(Create(k_box), FadeIn(k_tag, shift=0.1 * UP), run_time=0.7)

            sig_lab = B("signature", 32, GREEN)
            sig_val = MT(f'( {span("r", GREEN, True)} , {span("s", GREEN, True)} )  =  '
                         f'( {span(hex_short(R_HEX), GREEN)} , {span(hex_short(S_HEX), GREEN)} )', 32, FG, font=MONO)
            sig = boxed(VGroup(sig_lab, sig_val).arrange(RIGHT, buff=0.45), GREEN, buff=0.25).move_to(DOWN * 3.05)
            v.wait_until("sig", offset=-0.2)
            self.play(FadeOut(VGroup(d_tag, k_tag)), FadeIn(sig, shift=0.2 * UP), run_time=0.7)

        # ------------------------------------------------------------ d4: Bob verifies
        with self.vo("d4") as v:
            others = VGroup(alice, a1, sha, a2, e_row, bits, k_grp, nonce, a3, R_eq, cloud, g_dot, r_dot,
                            g_lab, r_lab, hop, proj, a4, r_grp, s_eq, d_box, k_box)
            self.play(FadeOut(others), run_time=0.6)
            head = label("public information", 30, MUTED)
            q_chip = boxed(VGroup(icon_key(BLUE, 0.85),
                                  MT(f'{span("Q", BLUE, True)} = {span(hex_short(QX_HEX), BLUE)}', 30, FG, font=MONO)
                                  ).arrange(RIGHT, buff=0.25), BLUE, buff=0.2)
            sig_small = boxed(MT(f'( {span("r", GREEN, True)} , {span("s", GREEN, True)} )', 36, FG, font=MONO),
                              GREEN, buff=0.2)
            msg_new = message_card(30)
            col = VGroup(VGroup(label("message", 28, FG), msg_new),
                         VGroup(label("signature", 28, GREEN), sig_small),
                         VGroup(label("Alice's public key", 28, BLUE), q_chip))
            for g in col:
                g.arrange(DOWN, buff=0.12, aligned_edge=LEFT)
            col.arrange(DOWN, buff=0.42, aligned_edge=LEFT)
            left = VGroup(head, col).arrange(DOWN, buff=0.4, aligned_edge=LEFT).move_to(LEFT * 4.15 + DOWN * 0.1)
            sep = DashedLine(UP * 3.3, DOWN * 3.3, color=DIM, dash_length=0.1).move_to(LEFT * 1.25)
            bob = icon_person(BOB, 1.1, name="Bob").move_to(RIGHT * 5.75 + UP * 2.55)
            v.wait_until("pubinfo", offset=-0.2)
            self.play(FadeIn(head), ReplacementTransform(msg, msg_new), FadeIn(col[0][0]),
                      ReplacementTransform(sig, sig_small), FadeIn(col[1][0]), Create(sep), run_time=0.9)
            self.play(FadeIn(col[2], shift=0.15 * UP), FadeIn(bob, shift=0.2 * LEFT), run_time=0.7)

            u1 = eq(r"\vua = \ve \cdot \vs^{-1} \bmod n", 54)
            u2 = eq(r"\vub = \vr \cdot \vs^{-1} \bmod n", 54)
            X = eq(r"\vX = \vua \cdot \vG + \vub \cdot \vQ", 54)
            chk = eq(r"x\text{-coord of } \vX \overset{?}{=} \vr", 54)
            steps = VGroup(u1, u2, X, chk).arrange(DOWN, buff=0.5, aligned_edge=LEFT).move_to(RIGHT * 2.35 + DOWN * 0.45)
            for mark, mob in (("u1", u1), ("u2", u2), ("X", X)):
                v.wait_until(mark, offset=-0.2)
                self.play(Write(mob), run_time=0.8)
            v.wait_until("check", offset=-0.2)
            self.play(Write(chk), run_time=0.8)
            ok = VGroup(check_mark(GREEN, 0.55, 9), B("valid", 36, GREEN)).arrange(RIGHT, buff=0.15)
            ok.next_to(chk, DOWN, buff=0.35).align_to(chk, LEFT)
            self.play(FadeIn(ok, scale=0.6), Circumscribe(chk, color=GREEN, buff=0.12), run_time=0.8)

        # ------------------------------------------------------------ d5: why it works
        with self.vo("d5") as v:
            l1 = eq(r"\vX = \vua\,\vG + \vub\,\vQ", 60)
            l2 = eq(r"= \frac{\ve}{\vs}\,\vG + \frac{\vr}{\vs}\,\vd\,\vG", 60)
            l3 = eq(r"= \frac{\ve + \vr\,\vd}{\vs}\,\vG", 60)
            l4 = eq(r"= \vk\,\vG = \vR", 60)
            l1.move_to(UP * 2.75 + LEFT * 1.7)
            l2.next_to(l1, DOWN, buff=0.45).align_to(l1, LEFT).shift(RIGHT * 0.74)
            l3.next_to(l2, DOWN, buff=0.4).align_to(l2, LEFT)
            l4.next_to(l3, DOWN, buff=0.4).align_to(l2, LEFT)
            self.play(FadeOut(VGroup(left, sep, bob, u1, u2, chk, ok)), Transform(X, l1), run_time=0.8)
            sub = eq(r"\vQ = \vd \cdot \vG", 46)
            sub_box = boxed(sub, BLUE, buff=0.2).move_to(RIGHT * 4.6 + UP * 2.75)
            v.wait_until("sub", offset=-0.2)
            self.play(FadeIn(sub_box, shift=0.1 * LEFT), Indicate(glyphs(X, BLUE), color=BLUE), run_time=0.6)
            self.play(Write(l2), run_time=0.9)
            v.wait_until("collapse", offset=-0.2)
            self.play(Write(l3), run_time=0.9)
            since = eq(r"\vs = \frac{\ve + \vr\,\vd}{\vk}", 46)
            since_box = boxed(VGroup(label("by how s was built", 28, MUTED), since).arrange(DOWN, buff=0.18),
                              GREEN, buff=0.22).move_to(RIGHT * 4.6 + UP * 0.2)
            self.play(FadeIn(since_box, shift=0.1 * LEFT), run_time=0.7)
            v.wait_until("kG", offset=-0.2)
            self.play(Write(l4), run_time=0.8)
            r_hl = SurroundingRectangle(glyphs(l4, WHITE_R), color=GREEN, buff=0.1, corner_radius=0.06)
            tick = check_mark(GREEN, 0.55, 9).next_to(r_hl, RIGHT, buff=0.3)
            self.play(Create(r_hl), FadeIn(tick, scale=0.6), run_time=0.6)
            d_hl = SurroundingRectangle(glyphs(l3, GOLD), color=GOLD, buff=0.07, corner_radius=0.05, stroke_width=3)
            only = VGroup(icon_key(GOLD, 0.75), label("only the holder of d can produce this s", 30, GOLD)
                          ).arrange(RIGHT, buff=0.2).move_to(DOWN * 3.0)
            v.wait_until("only", offset=-0.2)
            self.play(Create(d_hl), FadeIn(only, shift=0.1 * UP), run_time=0.8)

        # ------------------------------------------------------------ d6: nonce reuse
        with self.vo("d6") as v:
            self.play(FadeOut(VGroup(X, l2, l3, l4, sub_box, since_box, r_hl, tick, d_hl, only)), run_time=0.5)
            big_k = eq(r"\vk", 150).move_to(DOWN * 0.1)
            v.wait_until("assume", offset=-0.2)
            self.play(FadeIn(big_k, scale=0.7), run_time=0.6)
            span_t = v.at("reuse") - v.at("assume")
            tags = [pill(w, ORANGE, size=36) for w in ("secret", "unpredictable", "never reused")]
            tags[0].next_to(big_k, LEFT, buff=1.0)
            tags[1].next_to(big_k, UP, buff=0.6)
            tags[2].next_to(big_k, RIGHT, buff=1.0)
            for frac, tg in zip((0.42, 0.58, 0.78), tags):
                dt = v.at("assume") + frac * span_t - 0.15 - self.time
                if dt > 0.02:
                    self.wait(dt)
                self.play(FadeIn(tg, scale=0.8), run_time=0.4)

            e1 = eq(r"\vsa = \vkinv\,(\vea + \vr\,\vd)", 58)
            e2 = eq(r"\vsb = \vkinv\,(\veb + \vr\,\vd)", 58)
            pair = VGroup(e1, e2).arrange(DOWN, buff=0.35, aligned_edge=LEFT).move_to(UP * 2.35 + LEFT * 1.3)
            v.wait_until("reuse", offset=-0.2)
            self.play(FadeOut(VGroup(big_k, *tags)), Write(e1), run_time=0.8)
            self.play(Write(e2), run_time=0.7)
            same = SurroundingRectangle(VGroup(glyphs(e1, ORANGE), glyphs(e2, ORANGE)), color=ORANGE, buff=0.08,
                                        corner_radius=0.06, stroke_width=3)
            same_lab = B("same k!", 34, ORANGE).next_to(pair, RIGHT, buff=0.6)
            self.play(Create(same), FadeIn(same_lab, shift=0.1 * LEFT), run_time=0.6)

            sub_l = eq(r"\vsa - \vsb = \vkinv\,(\vea - \veb)", 58)
            solve_k = eq(r"\Rightarrow\; \vk = \frac{\vea - \veb}{\vsa - \vsb}", 58)
            solve_d = eq(r"\Rightarrow\; \vd = \frac{\vsa\,\vk - \vea}{\vr}", 58)
            sub_l.next_to(pair, DOWN, buff=0.55).align_to(pair, LEFT)
            VGroup(solve_k, solve_d).arrange(RIGHT, buff=1.1).next_to(sub_l, DOWN, buff=0.5).align_to(pair, LEFT)
            v.wait_until("subtract", offset=-0.2)
            self.play(Write(sub_l), run_time=0.8)
            v.wait_until("solvek", offset=-0.2)
            self.play(Write(solve_k), run_time=0.8)
            v.wait_until("solved", offset=-0.2)
            self.play(Write(solve_d), run_time=0.8)
            d_hl2 = SurroundingRectangle(solve_d, color=RED, buff=0.15, corner_radius=0.1, stroke_width=3)
            leak = VGroup(icon_key(GOLD, 0.85), B("private key recovered", 34, RED)).arrange(RIGHT, buff=0.25)
            leak.next_to(d_hl2, DOWN, buff=0.3)
            self.play(Create(d_hl2), FadeIn(leak, shift=0.1 * UP), run_time=0.7)

        # ------------------------------------------------------------ d7: PlayStation 3
        with self.vo("d7") as v:
            self.play(FadeOut(VGroup(e1, e2, same, same_lab, sub_l, solve_k, solve_d, d_hl2, leak)), run_time=0.5)
            year = B("2010", 100, ORANGE).move_to(UP * 2.55)
            self.play(FadeIn(year, shift=0.2 * DOWN), run_time=0.6)
            who = T("Sony PlayStation 3: the software-signing key", 40, FG, weight=BOLD).next_to(year, DOWN, buff=0.3)
            v.wait_until("ps3", offset=-0.2)
            self.play(FadeIn(who, shift=0.1 * UP), run_time=0.6)
            rows = VGroup()
            for i in (1, 2, 3):
                rows.add(MT(f'signature {i}:   ( {span("r", ORANGE, True)} , '
                            f'{span(f"s<sub>{i}</sub>", GREEN, True)} )', 38, FG, font=MONO))
            rows.arrange(DOWN, buff=0.28, aligned_edge=LEFT).next_to(who, DOWN, buff=0.5)
            self.play(LaggedStart(*[FadeIn(r, shift=0.1 * UP) for r in rows], lag_ratio=0.3), run_time=1.2)
            r_col = VGroup(*[r[len("signature1:("):len("signature1:(r")] for r in rows])
            col_box = SurroundingRectangle(r_col, color=ORANGE, buff=0.1, corner_radius=0.06)
            note = label("the same r every time  →  the same k", 32, ORANGE).next_to(rows, DOWN, buff=0.4)
            v.wait_until("same", offset=-0.2)
            self.play(Create(col_box), FadeIn(note, shift=0.1 * UP), run_time=0.7)
            res = VGroup(icon_padlock(RED, 0.6), B("private signing key recovered", 36, RED)).arrange(RIGHT, buff=0.25)
            res.next_to(note, DOWN, buff=0.35)
            self.play(FadeIn(res, shift=0.1 * UP), run_time=0.6)

        # ------------------------------------------------------------ d8: biased nonces
        with self.vo("d8") as v:
            self.play(FadeOut(VGroup(year, who, rows, col_box, note, res)), run_time=0.5)
            rng = np.random.default_rng(5)
            krows = VGroup()
            for i in range(4):
                bits_s = "000" + "".join(rng.choice(["0", "1"], 23))
                cells = bit_cells(bits_s, cell=0.36, gap=0.045)
                for c in cells[:3]:
                    c[0].set_fill(ORANGE, 0.35).set_stroke(ORANGE, 1.5)
                    c[1].set_color(ORANGE)
                lab = eq(rf"\vk_{{{i + 1}}}", 44)
                krows.add(VGroup(lab, cells).arrange(RIGHT, buff=0.3))
            krows.arrange(DOWN, buff=0.22, aligned_edge=LEFT).move_to(UP * 0.95)
            brace = Brace(VGroup(*[r[1][:3] for r in krows]), UP, color=ORANGE, buff=0.12)
            b_lab = label("predictable bits", 30, ORANGE).next_to(brace, UP, buff=0.1)
            v.wait_until("bias", offset=-0.1)
            self.play(LaggedStart(*[FadeIn(r, shift=0.1 * RIGHT) for r in krows], lag_ratio=0.2), run_time=1.0)
            self.play(GrowFromCenter(brace), FadeIn(b_lab), run_time=0.6)

            lat = lattice_icon(PURPLE, 2.4)
            lt = B("lattice reduction", 56, PURPLE)
            key = icon_key(GOLD, 1.0)
            a_k = arrow(ORIGIN, RIGHT * 0.9, color=RED)
            lat_full = VGroup(lat, lt, a_k, key).arrange(RIGHT, buff=0.4).move_to(DOWN * 1.75)
            v.wait_until("lattice", offset=-0.2)
            self.play(FadeIn(lat, scale=0.8), Write(lt), run_time=1.0)
            self.play(GrowArrow(a_k), FadeIn(key, shift=0.1 * LEFT), run_time=0.6)
            remember = pill("remember this word", YELLOW, size=30).next_to(lat_full, DOWN, buff=0.45)
            self.play(FadeIn(remember, shift=0.1 * UP), Indicate(lt, color=PURPLE, scale_factor=1.06), run_time=0.8)

        # ------------------------------------------------------------ d9: three pillars
        with self.vo("d9") as v:
            self.play(FadeOut(VGroup(krows, brace, b_lab, lat_full, remember)), run_time=0.5)
            roof = Polygon(LEFT * 5.9, RIGHT * 5.9, UP * 1.1, fill_color=FAINT, fill_opacity=1,
                           stroke_color=FG, stroke_width=2.5).move_to(UP * 2.6)
            roof_t = B("ECDSA security", 34, FG).move_to(roof.get_center() + DOWN * 0.12)
            base = RoundedRectangle(width=12.0, height=0.32, corner_radius=0.06, fill_color=FAINT, fill_opacity=1,
                                    stroke_color=FG, stroke_width=2.5).move_to(DOWN * 1.25)
            cols, labs = VGroup(), VGroup()
            texts = [("Hard\nmath", BLUE), ("Good\nrandomness", ORANGE), ("The curve\nitself", YELLOW)]
            top_y, bot_y = roof.get_bottom()[1], base.get_top()[1]
            for i, (t1, c) in enumerate(texts):
                x = (i - 1) * 4.0
                shaft = Rectangle(width=0.8, height=top_y - bot_y - 0.36, fill_color=c, fill_opacity=0.18,
                                  stroke_color=c, stroke_width=3).move_to([x, (top_y + bot_y) / 2, 0])
                cap_t = Rectangle(width=1.2, height=0.18, fill_color=c, fill_opacity=0.5, stroke_color=c,
                                  stroke_width=2).next_to(shaft, UP, buff=0)
                cap_b = cap_t.copy().next_to(shaft, DOWN, buff=0)
                col = VGroup(shaft, cap_t, cap_b)
                cols.add(col)
                lb = T(t1, 34, c, weight=BOLD, line_spacing=0.9).next_to(base, DOWN, buff=0.35)
                lb.set_x(x)
                labs.add(lb)
            v.wait_until("pillars", offset=-0.2)
            self.play(FadeIn(roof, shift=0.2 * DOWN), FadeIn(roof_t), FadeIn(base, shift=0.2 * UP), run_time=0.7)
            for mark, i in (("p1", 0), ("p2", 1)):
                v.wait_until(mark, offset=-0.2)
                self.play(GrowFromEdge(cols[i], DOWN), FadeIn(labs[i], shift=0.1 * UP), run_time=0.6)
            v.wait_until("p3", offset=-0.25)
            self.play(GrowFromEdge(cols[2], DOWN), FadeIn(labs[2], shift=0.1 * UP), run_time=0.6)
            q = B("?", 80, YELLOW).move_to(cols[2].get_center())
            self.play(cols[2][0].animate.set_fill(YELLOW, 0.45), FadeIn(q, scale=0.5),
                      Flash(cols[2].get_top(), color=YELLOW, line_length=0.3), run_time=0.8)

        self.clear_all()

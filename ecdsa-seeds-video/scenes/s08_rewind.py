import re
from datetime import datetime, timezone

from common import *

A_LCG, C_LCG, MOD = 0x5DEECE66D, 0xB, 2 ** 48
A_INV = pow(A_LCG, -1, MOD)  # 0xDFE05BCB1365
T_P256 = 871696354  # 1997-08-16 01:52:34 UTC
STEPS_BACK = 20 * 1841 + 1  # state that produced the first byte of candidate 1842


def p256_states():
    x = (T_P256 << 16) | 0x330E
    out = [x]
    for _ in range(20 * 1842):
        x = (A_LCG * x + C_LCG) % MOD
        out.append(x)
    return out


STATES = p256_states()


def candidate(n):
    return "".join("%02X" % (STATES[20 * (n - 1) + 1 + j] >> 40) for j in range(20))


C_KEYWORDS = r"\b(for|if|break)\b"


def c_markup(line: str) -> str:
    """Tiny C highlighter for MarkupText."""
    indent = len(line) - len(line.lstrip(" "))
    line = "\u00a0" * indent + line[indent:]
    code, _, comment = line.partition("//")
    code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    code = re.sub(C_KEYWORDS, lambda m: span(m.group(0), PURPLE), code)
    code = re.sub(r"\b(srand48|lrand48|time|good_curve)\b", lambda m: span(m.group(0), BLUE), code)
    code = re.sub(r"(?<![\w#])(\d+)\b", lambda m: span(m.group(0), ORANGE), code)
    out = code
    if comment:
        out += span("//" + comment.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), MUTED)
    out = re.sub(r"  +", lambda m: "\u00a0" * len(m.group(0)), out)
    return out


def register(top_hex="????????", low_hex="????", size=60, top_color=FG, low_color=FG):
    top = Mono(top_hex, size, top_color, weight=BOLD)
    low = Mono(low_hex, size, low_color, weight=BOLD)
    tb = RoundedRectangle(width=top.width + 0.6, height=top.height + 0.55, corner_radius=0.14,
                          fill_color=PANEL, fill_opacity=1, stroke_color=DIM, stroke_width=2)
    lb = RoundedRectangle(width=low.width + 0.6, height=low.height + 0.55, corner_radius=0.14,
                          fill_color=PANEL, fill_opacity=1, stroke_color=DIM, stroke_width=2)
    boxes = VGroup(tb, lb).arrange(RIGHT, buff=0.12)
    top.move_to(tb)
    low.move_to(lb)
    g = VGroup(tb, lb, top, low)
    g.tb, g.lb, g.top, g.low = tb, lb, top, low
    return g


class Rewind(VOScene):
    def construct(self):
        self.chapter(8, "Rewinding the clock")

        # ---------------------------------------------------------- w1: runs backwards
        with self.vo("w1") as v:
            nodes = VGroup(*[boxed(M(f"x_{{{i}}}", size=60), DIM, buff=0.26) for i in range(5)])
            nodes.arrange(RIGHT, buff=1.45).move_to(UP * 1.5)
            fwd = VGroup(*[Arrow(nodes[i].get_right(), nodes[i + 1].get_left(), buff=0.08, color=BLUE,
                                 stroke_width=5, max_tip_length_to_length_ratio=0.3)
                           for i in range(4)]).shift(UP * 0.2)
            fwd_lab = M(r"\times a + 11", size=36, color=BLUE).next_to(nodes, UP, buff=0.35)
            self.play(LaggedStart(*[FadeIn(n, shift=0.1 * RIGHT) for n in nodes], lag_ratio=0.12),
                      LaggedStart(*[GrowArrow(a) for a in fwd], lag_ratio=0.12), FadeIn(fwd_lab), run_time=1.0)
            bwd = VGroup(*[Arrow(nodes[i + 1].get_left(), nodes[i].get_right(), buff=0.08, color=CLAUDE,
                                 stroke_width=5, max_tip_length_to_length_ratio=0.3)
                           for i in range(4)]).shift(DOWN * 0.2)
            v.wait_until("back", offset=-0.2)
            self.play(LaggedStart(*[GrowArrow(a) for a in reversed(bwd)], lag_ratio=0.15), run_time=1.0)
            bwd_lab = M(r"-11,\ \times a^{-1}", size=36, color=CLAUDE).next_to(nodes, DOWN, buff=0.35)
            f1 = M(r"x_{n+1} = a\,x_n + 11 \bmod 2^{48}", size=42)
            f2 = M(r"x_n = a^{-1}\,(x_{n+1} - 11) \bmod 2^{48}", size=42, color=CLAUDE)
            ainv = MT(f'a = {span("0x5DEECE66D", BLUE)}   ·   a⁻¹ = {span("0xDFE05BCB1365", CLAUDE)}', 28,
                      MUTED, font=MONO)
            forms = VGroup(f1, f2, ainv).arrange(DOWN, buff=0.32).move_to(DOWN * 1.95)
            v.wait_until("inv", offset=-0.2)
            self.play(FadeIn(bwd_lab), FadeIn(f1, shift=0.1 * UP), run_time=0.6)
            self.play(FadeIn(f2, shift=0.1 * UP), run_time=0.6)
            self.play(FadeIn(ainv), run_time=0.5)
            v.wait_until("rewind", offset=-0.2)
            rew = B("◀◀  rewind", 34, CLAUDE).next_to(nodes, UP, buff=0.55).align_to(nodes, RIGHT)
            self.play(FadeIn(rew, shift=0.2 * LEFT), FadeOut(forms), FadeOut(bwd_lab), run_time=0.5)
            self.play(LaggedStart(*[Indicate(a, color=YELLOW, scale_factor=1.15) for a in reversed(bwd)],
                                  lag_ratio=0.3), run_time=1.4)
            born = boxed(Mono("srand48( ? )", 34, YELLOW, weight=BOLD), YELLOW, buff=0.22)
            born.move_to(DOWN * 1.2 + LEFT * 3.6)
            born_lab = label("the moment it was born", 28, YELLOW).next_to(born, RIGHT, buff=0.4)
            v.wait_until("born", offset=-0.2)
            link = Arrow(born.get_top(), nodes[0].get_bottom(), buff=0.12, color=YELLOW, stroke_width=4)
            self.play(FadeIn(born, shift=0.1 * UP), GrowArrow(link), FadeIn(born_lab), run_time=0.8)

        # ---------------------------------------------------------- w2: srand48 sets 0x330E
        with self.vo("w2") as v:
            self.play(FadeOut(VGroup(nodes, fwd, bwd, fwd_lab, rew, link, born_lab)),
                      born.animate.move_to(UP * 2.6), run_time=0.7)
            code = Mono("srand48(seedval);", 40, FG, weight=BOLD)
            code_box = boxed(code, BLUE, buff=0.25).move_to(UP * 2.6)
            v.wait_until("srand", offset=-0.2)
            self.play(FadeTransform(born, code_box), run_time=0.6)
            reg = register("seedval ", "330E", 64).move_to(UP * 0.2)
            reg.top.set_color(MUTED)
            reg.low.set_color(YELLOW)
            state_lab = label("the 48-bit state", 28).next_to(reg, UP, buff=0.3)
            arr = Arrow(code_box.get_bottom(), state_lab.get_top(), buff=0.1, color=MUTED, stroke_width=3)
            self.play(GrowArrow(arr), FadeIn(state_lab), FadeIn(reg.tb), FadeIn(reg.lb), run_time=0.6)
            low_lab = label("low 16 bits: always 0x330E", 28, YELLOW).next_to(reg.lb, DOWN, buff=0.35)
            v.wait_until("c330e", offset=-0.2)
            self.play(Write(reg.low), reg.lb.animate.set_stroke(YELLOW, 3), run_time=0.8)
            self.play(FadeIn(low_lab, shift=0.1 * UP), run_time=0.5)
            top_lab = label("top 32 bits: the number passed in", 28, BLUE).next_to(reg.tb, DOWN, buff=0.35)
            top_lab.align_to(reg.tb, RIGHT).shift(LEFT * 0.2)
            if top_lab.get_left()[0] < -6.5:
                top_lab.shift(RIGHT * (-6.5 - top_lab.get_left()[0]))
            low_lab.next_to(reg.lb, DOWN, buff=1.05).align_to(reg.lb, LEFT)
            v.wait_until("top32", offset=-0.2)
            self.play(Write(reg.top), reg.tb.animate.set_stroke(BLUE, 3), FadeIn(top_lab, shift=0.1 * UP),
                      low_lab.animate.next_to(reg.lb, DOWN, buff=1.05).align_to(reg.lb, RIGHT), run_time=0.8)

        # ---------------------------------------------------------- w3: rewind P-256
        with self.vo("w3") as v:
            head = MT(f'{span("P-256", BLUE, True)} seed  ·  first byte {span("C4", YELLOW, True)}', 32, FG)
            head.move_to(UP * 3.0)
            n = ValueTracker(STEPS_BACK)
            reg2 = register("C401E993", "9EA5", 66).move_to(UP * 0.9)

            def live_state():
                i = int(round(n.get_value()))
                h = f"{STATES[i]:012X}"
                t = Mono(h[:8], 66, FG, weight=BOLD).move_to(reg2.tb)
                l = Mono(h[8:], 66, FG, weight=BOLD).move_to(reg2.lb)
                return VGroup(t, l)

            def live_count():
                i = int(round(n.get_value()))
                return MT(f'steps back: {span(f"{STEPS_BACK - i:,}", CLAUDE, True)}', 34, MUTED,
                          font=MONO).move_to(DOWN * 0.75)

            state_live = always_redraw(live_state)
            count_live = always_redraw(live_count)
            self.play(FadeOut(VGroup(code_box, arr, state_lab, top_lab, low_lab, reg)), FadeIn(head, shift=0.1 * DOWN),
                      FadeIn(reg2.tb), FadeIn(reg2.lb), FadeIn(state_live), FadeIn(count_live), run_time=0.5)
            rt = max(2.0, v.until("hit") - 0.1)
            self.sfx("rewind", duration=rt)
            self.play(n.animate.set_value(0), run_time=rt, rate_func=rate_functions.ease_in_out_sine)
            state_live.clear_updaters()
            count_live.clear_updaters()
            final = register("33F507E2", "330E", 66).move_to(reg2)
            final.top.set_color(FG)
            final.low.set_color(YELLOW)
            self.remove(state_live)
            self.add(final.top, final.low)
            self.play(reg2.lb.animate.set_stroke(YELLOW, 4), Indicate(final.low, color=YELLOW, scale_factor=1.2),
                      run_time=0.7)
            tick = check_mark(GREEN, 0.55).next_to(reg2.lb, RIGHT, buff=0.3)
            self.play(Create(tick), run_time=0.4)

            dec = MT(f'0x33F507E2 = {span("871,696,354", YELLOW, True)}', 40, FG, font=MONO)
            dec.move_to(DOWN * 1.25)
            v.wait_until("num", offset=-0.2)
            self.play(reg2.tb.animate.set_stroke(BLUE, 4), FadeOut(count_live), run_time=0.4)
            self.play(TransformFromCopy(final.top, dec), run_time=0.9)
            unix_lab = label("seconds since 1970-01-01 00:00:00 UTC", 28, MUTED).next_to(dec, DOWN, buff=0.3)
            v.wait_until("unix", offset=-0.2)
            self.play(FadeIn(unix_lab, shift=0.1 * UP), run_time=0.6)
            date = Mono("1997-08-16  01:52:34 UTC", 56, YELLOW, weight=BOLD)
            date_box = boxed(date, YELLOW, buff=0.3, stroke_width=3).move_to(DOWN * 2.85)
            v.wait_until("date", offset=-0.3)
            self.play(FadeIn(date_box, scale=0.9), run_time=0.7)
            self.play(Circumscribe(date_box, color=YELLOW, buff=0.05), run_time=1.0)

        # ---------------------------------------------------------- w4: a Friday night
        with self.vo("w4") as v:
            keep = date_box
            clk = icon_clock(FG, 1.55, hour=1, minute=52, numbers=True).move_to(LEFT * 3.2 + DOWN * 0.3)
            utc = label("01:52 UTC  ·  Saturday", 30, FG).next_to(clk, DOWN, buff=0.3)
            self.play(FadeOut(VGroup(head, reg2, final.top, final.low, tick, dec, unix_lab)),
                      keep.animate.scale(0.7).move_to(UP * 3.0), FadeIn(clk, scale=0.9), FadeIn(utc), run_time=0.8)
            east = VGroup(label("US East Coast", 30, BLUE), label("UTC − 4 hours (daylight time)", 26, MUTED))
            east.arrange(DOWN, buff=0.15).move_to(RIGHT * 3.0 + UP * 0.9)
            v.wait_until("east", offset=-0.2)
            self.play(FadeIn(east, shift=0.1 * LEFT), run_time=0.6)
            center = clk.face.get_center()
            self.play(Rotate(clk.hand_h, angle=4 * TAU / 12, about_point=center),
                      Rotate(clk.hand_m, angle=4 * TAU, about_point=center),
                      Transform(utc, label("21:52 local  ·  Friday", 30, YELLOW).move_to(utc)), run_time=1.6)
            moon = Difference(Circle(0.5), Circle(0.45).shift(RIGHT * 0.25 + UP * 0.12),
                              fill_color=YELLOW, fill_opacity=1, stroke_width=0)
            fri = B("Friday night, 9:52 PM", 44, YELLOW)
            fri_g = VGroup(moon, fri).arrange(RIGHT, buff=0.3).move_to(RIGHT * 3.0 + DOWN * 0.8)
            if fri_g.get_right()[0] > 6.5:
                fri_g.shift(LEFT * (fri_g.get_right()[0] - 6.5))
            v.wait_until("friday", offset=-0.2)
            self.play(FadeIn(fri_g, shift=0.1 * UP), run_time=0.6)
            sub = label("August 15, 1997", 28, MUTED).next_to(fri_g, DOWN, buff=0.25)
            self.play(FadeIn(sub), run_time=0.4)

        # ---------------------------------------------------------- w5: ten seeds, one year
        with self.vo("w5") as v:
            luck = VGroup(B("one date?", 44, FG), label("states ending in 330E appear by chance every 65,536 steps", 28))
            luck.arrange(DOWN, buff=0.25).move_to(UP * 2.4)
            self.play(FadeOut(VGroup(clk, utc, east, fri_g, sub, keep)), FadeIn(luck[0], shift=0.1 * UP), run_time=0.6)
            self.play(FadeIn(luck[1]), run_time=0.5)

            t0 = datetime(1997, 4, 20, tzinfo=timezone.utc).timestamp()
            t1 = datetime(1998, 5, 10, tzinfo=timezone.utc).timestamp()
            x_of = lambda ts: -6.0 + 12.0 * (ts - t0) / (t1 - t0)
            AY = -1.1
            axis = Line([-6.3, AY, 0], [6.3, AY, 0], stroke_color=DIM, stroke_width=3)
            ticks = VGroup()
            for y, mth in [(1997, m) for m in range(5, 13)] + [(1998, m) for m in range(1, 6)]:
                ts = datetime(y, mth, 1, tzinfo=timezone.utc).timestamp()
                xx = x_of(ts)
                ticks.add(Line([xx, AY - 0.08, 0], [xx, AY + 0.08, 0], stroke_color=DIM, stroke_width=2))
                ticks.add(T(datetime(y, mth, 1).strftime("%b"), 20, MUTED).move_to([xx, AY - 0.35, 0]))
            years = VGroup(T("1997", 24, MUTED, weight=BOLD).move_to([x_of(datetime(1997, 5, 1, tzinfo=timezone.utc).timestamp()) + 0.15, AY - 0.75, 0]),
                           T("1998", 24, MUTED, weight=BOLD).move_to([x_of(datetime(1998, 1, 1, tzinfo=timezone.utc).timestamp()) + 0.15, AY - 0.75, 0]))
            v.wait_until("timeline", offset=-0.3)
            self.play(Create(axis), FadeIn(ticks), FadeIn(years), luck.animate.scale(0.75).move_to(UP * 3.15),
                      run_time=0.8)

            def ts_of(w):
                return datetime.fromisoformat(w).replace(tzinfo=timezone.utc).timestamp()

            # (timestamp, dot names, label text, label height, label x-offset)
            groups = [
                ("1997-05-15 15:49:03", ["prime239v1", "prime239v2", "prime239v3"], "May 15 · prime239v1, v2, v3", 2.75, 0.3),
                ("1997-05-18 14:45:34", ["P-192", "prime192v2", "prime192v3"], "May 18 · P-192, prime192v2, v3", 2.15, 0.3),
                ("1997-08-08 01:12:04", ["P-521"], "Aug 8 · P-521", 0.35, 0.05),
                ("1997-08-16 01:52:34", ["P-256"], "Aug 16 · P-256", 0.9, 0.05),
                ("1997-08-30 14:50:08", ["P-384"], "Aug 30 · P-384", 1.45, 0.05),
                ("1998-04-03 12:52:07", ["P-224"], "Apr 3, 1998 · P-224", 0.6, -0.6),
            ]
            marks = VGroup()
            for when, names, text, hgt, dx in groups:
                xx = x_of(ts_of(when))
                dots = VGroup(*[Dot([xx, AY, 0], radius=0.11, color=BLUE if nm.startswith("P-") else TEAL)
                                for nm in names])
                for j, d in enumerate(dots):
                    d.shift(UP * 0.0 + RIGHT * 0.0)
                lead = Line([xx, AY + 0.12, 0], [xx, AY + hgt - 0.05, 0], stroke_color=DIM, stroke_width=2)
                col = YELLOW if "P-256" in names else (BLUE if any(nm.startswith("P-") for nm in names) else TEAL)
                txt = T(text, 24, col, weight=BOLD)
                txt.next_to([xx, AY + hgt, 0], UP, buff=0.04)
                txt.shift(RIGHT * (txt.width / 2 - 0.15 + dx))
                if txt.get_right()[0] > 6.5:
                    txt.shift(LEFT * (txt.get_right()[0] - 6.5))
                marks.add(VGroup(lead, dots, txt))
            self.play(LaggedStart(*[FadeIn(g, shift=0.15 * DOWN) for g in marks], lag_ratio=0.3),
                      run_time=max(1.8, v.until("made") - 0.2))
            span_ = BraceBetweenPoints([x_of(ts_of("1997-05-15")), AY - 1.05, 0], [x_of(ts_of("1998-04-03")), AY - 1.05, 0],
                                       direction=DOWN, color=YELLOW)
            span_lab = label("when the curves were being made", 30, YELLOW).next_to(span_, DOWN, buff=0.15)
            v.wait_until("made", offset=-0.2)
            self.play(GrowFromCenter(span_), FadeIn(span_lab, shift=0.1 * UP), FadeOut(luck), run_time=0.7)

        # ---------------------------------------------------------- w6: the reconstructed program
        with self.vo("w6") as v:
            lines = [
                "srand48(time(NULL));             // seed with the clock",
                "for (n = 1; ; n++) {",
                "    for (i = 0; i < 20; i++)",
                "        seed[i] = lrand48() >> 23; // keep the top 8 bits",
                "    if (good_curve(seed)) break;   // SHA-1 → b → checks",
                "}                                 // otherwise: draw again",
            ]
            texts = VGroup(*[MT(c_markup(l.lstrip(" ")) if l.strip() else " ", 25, FG, font=MONO) for l in lines])
            texts.arrange(DOWN, aligned_edge=LEFT, buff=0.2)
            cw = Mono("0" * 20, 25).width / 20
            for t_, l in zip(texts, lines):
                t_.shift(RIGHT * cw * (len(l) - len(l.lstrip(" "))))
            frame = RoundedRectangle(width=texts.width + 0.9, height=texts.height + 1.05, corner_radius=0.18,
                                     fill_color=PANEL, fill_opacity=1, stroke_color=DIM, stroke_width=1.5)
            dots = VGroup(*[Dot(radius=0.055, color=c) for c in (RED, YELLOW, GREEN)]).arrange(RIGHT, buff=0.1)
            dots.move_to(frame.get_corner(UL) + RIGHT * 0.35 + DOWN * 0.26)
            title = Mono("reconstructed  (illustrative)", 20, MUTED).move_to(frame.get_top() + DOWN * 0.26)
            texts.move_to(frame.get_center() + DOWN * 0.18)
            win = VGroup(frame, dots, title, texts).move_to(UP * 1.0)
            self.play(FadeOut(VGroup(axis, ticks, years, marks, span_, span_lab)), FadeIn(frame), FadeIn(dots),
                      FadeIn(title), run_time=0.6)
            self.play(LaggedStart(*[FadeIn(t, shift=0.1 * RIGHT) for t in texts], lag_ratio=0.12), run_time=1.0)
            hl = SurroundingRectangle(texts[0], buff=0.08, corner_radius=0.06, stroke_width=0,
                                      fill_color=YELLOW, fill_opacity=0.14)
            for mark, idx in (("l_seed", [0]), ("l_draw", [2, 3]), ("l_check", [4]), ("l_again", [1, 5])):
                target = SurroundingRectangle(VGroup(*[texts[i] for i in idx]), buff=0.08, corner_radius=0.06,
                                              stroke_width=0, fill_color=YELLOW, fill_opacity=0.14)
                v.wait_until(mark, offset=-0.2)
                if mark == "l_seed":
                    self.add(hl)
                    self.bring_to_back(hl)
                    self.bring_to_back(frame)
                    self.play(FadeIn(hl), run_time=0.3)
                else:
                    self.play(Transform(hl, target), run_time=0.4)

            nt = ValueTracker(1)
            n_live = always_redraw(lambda: MT(
                f'candidate {span(f"#{int(nt.get_value()):,}", CLAUDE, True)}', 34, FG, font=MONO)
                .move_to(DOWN * 2.0))
            c_live = always_redraw(lambda: Mono(hexgroups(candidate(int(nt.get_value()))), 30, MUTED)
                                   .move_to(DOWN * 2.75))
            v.wait_until("l_1842", offset=-0.5)
            self.play(FadeIn(n_live), FadeIn(c_live), FadeOut(hl), run_time=0.3)
            self.play(nt.animate.set_value(1842), run_time=2.2, rate_func=rate_functions.ease_in_quad)
            n_live.clear_updaters()
            c_live.clear_updaters()
            final_seed = Mono(hexgroups(candidate(1842)), 30, YELLOW, weight=BOLD).move_to(c_live)
            p256 = pill("P-256", BLUE, size=26).next_to(final_seed, RIGHT, buff=0.3)
            self.play(Transform(c_live, final_seed), FadeIn(p256, shift=0.1 * LEFT), run_time=0.5)

        # ---------------------------------------------------------- w7: binary curves halved the clock
        with self.vo("w7") as v:
            hdr = MT(f'{span("binary curves", PURPLE, True)}: B-233 · B-283 · B-409 · B-571', 34, FG).move_to(UP * 3.0)
            self.play(FadeOut(VGroup(win, n_live, c_live, p256)), FadeIn(hdr, shift=0.1 * DOWN), run_time=0.6)
            raw = VGroup(Mono("srand48 value  446,413,329", 34, FG),
                         MT(f'→ 1984-02-23 19:42 UTC  {span("?!", RED, True)}', 34, MUTED, font=MONO))
            raw.arrange(DOWN, buff=0.25, aligned_edge=LEFT).move_to(UP * 1.4)
            self.play(FadeIn(raw[0]), run_time=0.4)
            self.play(FadeIn(raw[1], shift=0.1 * RIGHT), run_time=0.5)
            dbl = VGroup(Mono("× 2 = 892,826,658", 34, PURPLE, weight=BOLD),
                         Mono("→ 1998-04-17 15:24:18 UTC", 34, YELLOW, weight=BOLD))
            dbl.arrange(DOWN, buff=0.25, aligned_edge=LEFT).move_to(DOWN * 0.45)
            v.wait_until("halved", offset=-0.2)
            self.play(FadeIn(dbl[0], shift=0.1 * DOWN), run_time=0.5)
            self.play(FadeIn(dbl[1], shift=0.1 * RIGHT), run_time=0.5)
            t0 = datetime(1998, 3, 25, tzinfo=timezone.utc).timestamp()
            t1 = datetime(1998, 4, 25, tzinfo=timezone.utc).timestamp()
            xo = lambda ts: -5.5 + 11 * (ts - t0) / (t1 - t0)
            ax = Line([-5.8, -2.4, 0], [5.8, -2.4, 0], stroke_color=DIM, stroke_width=3)
            tp224 = datetime(1998, 4, 3, 12, 52, tzinfo=timezone.utc).timestamp()
            tbin = datetime(1998, 4, 17, 15, 24, tzinfo=timezone.utc).timestamp()
            d224 = Dot([xo(tp224), -2.4, 0], radius=0.12, color=BLUE)
            l224 = T("P-224 · Apr 3", 26, BLUE, weight=BOLD).next_to(d224, DOWN, buff=0.2)
            dbin = VGroup(*[Dot([xo(tbin) + 0.06 * i, -2.4, 0], radius=0.1, color=PURPLE) for i in range(4)])
            lbin = T("B-233…B-571 · Apr 17", 26, PURPLE, weight=BOLD).next_to(dbin, DOWN, buff=0.2)
            gap = BraceBetweenPoints(d224.get_center() + UP * 0.2, dbin.get_center() + UP * 0.2, direction=UP, color=YELLOW)
            gap_l = label("two weeks", 26, YELLOW).next_to(gap, UP, buff=0.1)
            v.wait_until("apr", offset=-0.2)
            self.play(Create(ax), FadeIn(d224, scale=0.5), FadeIn(l224), run_time=0.6)
            self.play(FadeIn(dbin, scale=0.5), FadeIn(lbin), run_time=0.5)
            self.play(GrowFromCenter(gap), FadeIn(gap_l), run_time=0.5)

        # ---------------------------------------------------------- w8: "It's real."
        with self.vo("w8") as v:
            box = RoundedRectangle(width=12.2, height=3.3, corner_radius=0.22, fill_color=PANEL, fill_opacity=1,
                                   stroke_color=CLAUDE, stroke_width=2.5).move_to(UP * 1.0)
            tag = MT(f'{span("Claude", CLAUDE, True)}  ·  reasoning (excerpt)', 28, MUTED)
            tag.next_to(box, UP, buff=0.18).align_to(box, LEFT).shift(RIGHT * 0.2)
            self.play(FadeOut(VGroup(hdr, raw, dbl, ax, d224, l224, dbin, lbin, gap, gap_l)), FadeIn(box), FadeIn(tag),
                      run_time=0.6)
            l1 = T("“This is astonishing: it solves the 25-year-old mystery.", 32, FG)
            l2 = T("Hmm wait. Let me be skeptical: am I in some sort of", 32, FG)
            l3 = T("simulated/test environment?”", 32, FG)
            qlines = VGroup(l1, l2, l3).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
            qlines.move_to(box.get_center())
            if qlines.width > 11.4:
                qlines.scale_to_fit_width(11.4)
            v.wait_until("quote", offset=-0.1)
            self.play(AddTextLetterByLetter(l1, time_per_char=0.03), run_time=min(1.8, v.until("sim", 0.5)))
            v.wait_until("sim", offset=-0.1)
            self.play(AddTextLetterByLetter(l2, time_per_char=0.03), run_time=1.4)
            self.play(AddTextLetterByLetter(l3, time_per_char=0.03), run_time=0.8)
            facts = VGroup(
                MT(f'32-bit timestamp + small index  →  {span("all 160 seed bits match", GREEN, True)}', 30, FG),
                MT(f'chance of a fluke  ≈  {span("2⁻¹¹⁵", YELLOW, True)}   ·   ×10 seeds', 30, MUTED),
            ).arrange(DOWN, buff=0.25).move_to(DOWN * 1.65)
            v.wait_until("verify", offset=-0.2)
            self.play(FadeIn(facts[0], shift=0.1 * UP), run_time=0.6)
            self.play(FadeIn(facts[1], shift=0.1 * UP), run_time=0.6)
            real = B("“It's real.”", 64, CLAUDE).move_to(DOWN * 3.0)
            v.wait_until("real", offset=-0.2)
            self.sfx("chime", note=79)
            self.play(FadeIn(real, scale=1.2), run_time=0.6)

        # ---------------------------------------------------------- w9: the base points, and Lenstra
        with self.vo("w9") as v:
            self.play(FadeOut(VGroup(box, tag, qlines, facts, real)), run_time=0.6)
            bonus = pill("BONUS", YELLOW, size=28).move_to(UP * 3.1)
            v.wait_until("bonus", offset=-0.2)
            self.play(FadeIn(bonus, scale=0.8), run_time=0.4)
            curve = mini_curve(BLUE, 2.4, stroke=5).move_to(LEFT * 4.3 + UP * 0.6)
            gdot = Dot(curve.point_from_proportion(0.78), radius=0.13, color=PURPLE)
            glab = MT(f'base point {span("G", PURPLE, True)}', 30, FG).next_to(curve, DOWN, buff=0.3)
            v.wait_until("bp", offset=-0.2)
            self.play(Create(curve), run_time=0.7)
            self.play(FadeIn(gdot, scale=2), FadeIn(glab), run_time=0.5)
            rows = [("P-192", "20000"), ("prime239v1", "20420"), ("prime239v2", "20507"),
                    ("prime239v3", "20509"), ("prime192v2", "20512"), ("prime192v3", "20517")]
            tbl = VGroup(*[MT(f'{span(nm, BLUE if nm.startswith("P-") else TEAL, True)}   seed {span(sd, YELLOW)}  ✓',
                              28, FG, font=MONO) for nm, sd in rows]).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
            hdr2 = B("FreeLIP's random number generator", 32, FG)
            card = VGroup(hdr2, tbl).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
            card = boxed(card, DIM, buff=0.35).move_to(RIGHT * 2.4 + UP * 0.5)
            v.wait_until("freelip", offset=-0.2)
            self.play(FadeIn(card[0]), FadeIn(hdr2), run_time=0.5)
            self.play(LaggedStart(*[FadeIn(r, shift=0.1 * RIGHT) for r in tbl], lag_ratio=0.12), run_time=1.0)
            arjen = MT(f'FreeLIP: written by {span("Arjen K. Lenstra", CLAUDE, True)}', 32, FG).move_to(DOWN * 2.15)
            v.wait_until("arjen", offset=-0.2)
            self.play(FadeIn(arjen, shift=0.1 * UP), run_time=0.6)
            lll = MT(f'{span("L", CLAUDE, True)}LL = {span("Lenstra", CLAUDE, True)} · Lenstra · Lovász', 40, FG)
            lll.move_to(DOWN * 3.0)
            v.wait_until("same", offset=-0.2)
            self.play(FadeIn(lll, shift=0.1 * UP), run_time=0.6)
            self.play(Indicate(lll, color=CLAUDE, scale_factor=1.06), run_time=0.8)

        self.clear_all()

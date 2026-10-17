from common import *

# ------------------------------------------------------------------ real data
LCG_A, LCG_C, MASK48 = 0x5DEECE66D, 0xB, (1 << 48) - 1
LCG_A_INV = pow(LCG_A, -1, 1 << 48)

SEEDS = [  # FIPS 186-2 seeds as five 32-bit words (checked against OpenSSL)
    ("P-192", "3045AE6F C8422F64 ED579528 D38120EA E12196D5"),
    ("P-224", "BD713447 99D5C7FC DC45B59F A3B9AB8F 6A948BC5"),
    ("P-256", "C49D3608 86E70493 6A6678E1 139D26B7 819F7E90"),
    ("P-384", "A335926A A319A27A 1D00896A 6773A482 7ACDAC73"),
    ("P-521", "D09E8800 291CB853 96CC6717 393284AA A0DA64BA"),
    ("B-163", "85E25BFE 5C86226C DB12016F 7553F9D0 E693A268"),
    ("B-233", "74D59FF0 7F6B413D 0EA14B34 4B20A2DB 049B50C3"),
    ("B-283", "77E2B073 70EB0F83 2A6DD5B6 2DFC88CD 06BB84BE"),
    ("B-409", "4099B5A4 57F9D69F 79213D09 4C4BCD4D 4262210B"),
    ("B-571", "2AA058F7 3A0E33AB 486B0F61 0410C53A 7F132310"),
]
BINARY_HITS = ["B-233", "B-283", "B-409", "B-571"]
SEED_OF = dict(SEEDS)


def lcg_step(x: int) -> int:
    return (LCG_A * x + LCG_C) & MASK48


def recover_hidden(words: list[int]) -> int | None:
    """Brute-force the 17 bits lrand48 hides, as Claude did for the binary seeds."""
    for h in range(1 << 17):
        x = (words[0] << 17) | h
        for w in words[1:]:
            x = lcg_step(x)
            if x >> 17 != w:
                break
        else:
            return h
    return None


B233 = [int(w, 16) for w in SEED_OF["B-233"].split()]
B233_HIDDEN = recover_hidden(B233)                    # 0x9923
B233_STATE = (B233[0] << 17) | B233_HIDDEN            # state that printed word 1
B233_PREV = (LCG_A_INV * (B233_STATE - LCG_C)) & MASK48
assert lcg_step(B233_PREV) == B233_STATE
HIDDEN = {name: recover_hidden([int(w, 16) for w in SEED_OF[name].split()]) for name in BINARY_HITS}


def bits48(x: int) -> str:
    return format(x, "048b")


def icon_fingerprint(color=CLAUDE, h=1.6) -> VGroup:
    arcs = VGroup()
    for i, rad in enumerate(np.linspace(0.18, 1.0, 7)):
        start = PI * (0.62 + 0.09 * ((i * 5) % 7))
        a = Arc(radius=rad, start_angle=start, angle=TAU * (0.74 + 0.03 * (i % 3)),
                stroke_color=color, stroke_width=5)
        arcs.add(a)
    arcs.stretch(1.32, 1)
    return arcs.scale_to_fit_height(h)


def claude_tag(size=34) -> VGroup:
    t = B("Claude", size, CLAUDE)
    r = RoundedRectangle(width=t.width + 0.5, height=t.height + 0.32, corner_radius=0.16,
                         fill_color=CLAUDE, fill_opacity=0.12, stroke_color=CLAUDE, stroke_width=2)
    t.move_to(r)
    return VGroup(r, t)


def register(x: int, cell=0.245, gap=0.012, size=17) -> VGroup:
    return bit_cells(bits48(x), cell=cell, gap=gap, on=FG, off=MUTED, digit_size=size)


def set_cell(cells: VGroup, i: int, ch: str, color, size=17):
    sq = cells[i][0]
    new = Mono(ch, size, color).move_to(sq)
    if len(cells[i]) > 1:
        cells[i].remove(cells[i][1])
    cells[i].add(new)


class Investigation(VOScene):
    def construct(self):
        self.chapter(6, "The investigation")

        # ---------------------------------------------------------- i1: the question
        with self.vo("i1") as v:
            date = Mono("October 2026", 40, MUTED).move_to(UP * 3.05)
            self.play(FadeIn(date, shift=0.1 * DOWN), run_time=0.6)

            theory = label("the passphrase theory", 30, MUTED)
            tries = ["Give Bob and Jerry a raise", "Bob and Jerry rule", "Give Jerry a raise!",
                     "give bob and jerry a raise 2"]
            rows = VGroup()
            for t in tries:
                code = Mono(f'SHA-1("{t}")', 30, FG)
                neq = M(r"\neq", size=44, color=MUTED)
                seed_t = Mono("seed", 30, MUTED)
                x = cross_mark(RED, 0.34, 6)
                rows.add(VGroup(code, neq, seed_t, x).arrange(RIGHT, buff=0.3))
            rows.arrange(DOWN, buff=0.34, aligned_edge=LEFT)
            block = VGroup(theory, rows).arrange(DOWN, buff=0.45, aligned_edge=LEFT).move_to(DOWN * 0.2)
            v.wait_until("nope", offset=-0.2)
            self.play(FadeIn(theory, shift=0.1 * UP), run_time=0.4)
            self.play(LaggedStart(*[FadeIn(r, shift=0.15 * RIGHT) for r in rows], lag_ratio=0.45), run_time=2.6)

            person = icon_person(BLUE, 1.3)
            p_lab = label("Anthropic employee", 26, BLUE).next_to(person, DOWN, buff=0.2)
            g_person = VGroup(person, p_lab).move_to(LEFT * 4.6 + DOWN * 0.75)
            model = claude_tag(44)
            m_lab = label("internal research model", 26, CLAUDE).next_to(model, DOWN, buff=0.25)
            g_model = VGroup(model, m_lab).move_to(RIGHT * 4.3 + DOWN * 0.75)
            q = T("Can you figure out how these\nseeds were generated?", 34, FG, line_spacing=1.0)
            bubble = icon_bubble(q, FG, tail="left").move_to(LEFT * 0.45 + UP * 1.45)
            v.wait_until("ask", offset=-0.3)
            self.play(FadeOut(block, shift=0.3 * LEFT), run_time=0.4)
            self.play(FadeIn(g_person, shift=0.2 * RIGHT), FadeIn(g_model, shift=0.2 * LEFT), run_time=0.6)
            self.play(FadeIn(VGroup(*bubble[:3]), scale=0.9), run_time=0.5)
            self.wait(0.4)
            self.play(AddTextLetterByLetter(q, time_per_char=0.05), run_time=2.4)

            hint = Mono('hint: "Give Bob and Jerry a raise"', 28, MUTED).move_to(DOWN * 2.55)
            strike = Line(hint.get_left() + LEFT * 0.1, hint.get_right() + RIGHT * 0.1, stroke_color=RED, stroke_width=5)
            no_hint = B("no hint", 30, RED).next_to(hint, DOWN, buff=0.22)
            v.wait_until("nohint", offset=-0.35)
            self.play(FadeIn(hint, shift=0.1 * UP), run_time=0.4)
            self.play(Create(strike), FadeIn(no_hint, shift=0.1 * UP), run_time=0.5)

        # ---------------------------------------------------------- i2: a different angle
        with self.vo("i2") as v:
            self.play(FadeOut(VGroup(date, g_person, bubble, hint, strike, no_hint, m_lab)),
                      model.animate.scale(0.85).move_to(LEFT * 5.0 + UP * 3.1), run_time=0.7)
            heading = T("took a different angle", 38, FG).next_to(model, RIGHT, buff=0.35)
            self.play(FadeIn(heading, shift=0.1 * LEFT), run_time=0.5)
            old = pill("guess the passphrase", MUTED, size=30)
            new = pill("reconstruct the software", CLAUDE, size=30)
            arr0 = Arrow(LEFT, RIGHT, color=CLAUDE, stroke_width=5, buff=0).scale(0.6)
            reframe = VGroup(old, arr0, new).arrange(RIGHT, buff=0.35).move_to(UP * 1.9)
            old_strike = Line(old.get_left(), old.get_right(), stroke_color=RED, stroke_width=4)
            self.play(FadeIn(old), run_time=0.4)
            self.play(Create(old_strike), GrowArrow(arr0), FadeIn(new, shift=0.15 * LEFT), run_time=0.8)

            question = T("What software would have made these, in 1997?", 38, FG, slant=ITALIC).move_to(UP * 0.8)
            v.wait_until("y1997", offset=-0.2)
            self.play(Write(question), run_time=1.2)

            code = code_window(["#include <stdlib.h>", "for (i = 0; i < 20; i++)", "seed[i] = ???;"],
                               size=28, title="seedgen.c  ·  1997")
            code.move_to(LEFT * 3.35 + DOWN * 1.75)
            adv = Mono("0000000000", 28).width / 10
            base_line = code.lines[2]
            code.lines.remove(base_line)  # rebuilt below: JetBrains Mono fuses "???" into one ligature glyph

            def code_val(val):
                m = MT(f'seed[i] = {span(val, CLAUDE)};', 28, FG, font=MONO)
                return m.move_to(base_line, aligned_edge=LEFT).shift(RIGHT * 4 * adv)

            cur = code_val("???").set_color(FG)
            cur_target = code_val("???")
            v.wait_until("cprog", offset=-0.2)
            self.play(FadeIn(code, shift=0.2 * UP), FadeIn(cur, shift=0.2 * UP), run_time=0.7)

            libc = VGroup(B("C library", 32, FG), T("random number generator", 30, MUTED)).arrange(DOWN, buff=0.12)
            libc_box = boxed(libc, CLAUDE, buff=0.3).move_to(RIGHT * 3.55 + DOWN * 0.95)
            v.wait_until("prng", offset=-0.2)
            self.play(Transform(cur, cur_target), FadeIn(libc_box, shift=0.2 * LEFT), run_time=0.6)
            target = cur.get_left() + RIGHT * (len("seed[i] = ") + 1.5) * adv + UP * 0.22
            link = Arrow(libc_box.get_left(), target, color=CLAUDE, stroke_width=4,
                         buff=0.12, max_tip_length_to_length_ratio=0.12)
            self.play(GrowArrow(link), run_time=0.5)
            # the generator ticks out a few bytes in place of the question marks
            for o in ["0x3F", "0xA2", "0x17", "0xC9", "0x5E", "0x80", "0x2B"]:
                nv = code_val(o)
                self.play(FadeOut(cur), FadeIn(nv), run_time=0.18)
                cur = nv
                self.wait(0.16)
            val = cur

            fp = icon_fingerprint(CLAUDE, 1.15)
            fp_lab = T("weak enough to\nleave fingerprints", 30, FG, line_spacing=0.95)
            fp_g = VGroup(fp, fp_lab).arrange(RIGHT, buff=0.3).next_to(libc_box, DOWN, buff=0.4)
            v.wait_until("fp", offset=-0.3)
            self.play(FadeIn(fp, scale=0.7), FadeIn(fp_lab, shift=0.1 * LEFT), run_time=0.7)

        # ---------------------------------------------------------- i3: the scanner
        with self.vo("i3") as v:
            self.play(FadeOut(VGroup(heading, reframe, old_strike, question, code, val, libc_box, link, fp_g)),
                      run_time=0.6)
            title = T("a scanner for 1990s generators", 38, FG).next_to(model, RIGHT, buff=0.35)
            self.play(FadeIn(title, shift=0.1 * LEFT), run_time=0.5)

            name = Mono("P-256 seed", 26, MUTED)
            hexrow = Mono(SEED_OF["P-256"], 30, FG)
            head = VGroup(name, hexrow).arrange(RIGHT, buff=0.4).move_to(UP * 1.95)
            bits = format(int(SEED_OF["P-256"].replace(" ", ""), 16), "0160b")
            cell, gap = 0.15, 0.006
            rows = VGroup()
            for r in range(2):
                row = VGroup()
                for b in bits[r * 80:(r + 1) * 80]:
                    row.add(Square(cell, stroke_width=0, fill_color=BLUE if b == "1" else FAINT,
                                   fill_opacity=0.9 if b == "1" else 1))
                row.arrange(RIGHT, buff=gap)
                rows.add(row)
            rows.arrange(DOWN, buff=0.12).move_to(UP * 0.85)
            row_lab = label("160 bits", 26).next_to(rows, LEFT, buff=0.2)
            self.play(FadeIn(head), run_time=0.4)
            self.play(LaggedStart(*[FadeIn(c) for c in rows[0]] + [FadeIn(c) for c in rows[1]], lag_ratio=0.01),
                      run_time=1.0)

            # Two neighbouring 16-bit chunks slide along the first row, one bit per step.
            off = ValueTracker(0)
            chunk_w = 16
            step = cell + gap

            def window():
                o = int(off.get_value())
                left = rows[0][o].get_left()
                a = Rectangle(width=chunk_w * step - gap, height=cell + 0.12, stroke_color=YELLOW, stroke_width=3)
                b = a.copy().set_stroke(CLAUDE)
                a.move_to(left + RIGHT * (chunk_w * step - gap) / 2)
                b.next_to(a, RIGHT, buff=gap)
                return VGroup(a, b)

            win = always_redraw(window)
            ab = VGroup(Mono("chunk A", 24, YELLOW), Mono("→ next output? →", 24, MUTED),
                        Mono("chunk B", 24, CLAUDE)).arrange(RIGHT, buff=0.2)
            ab.next_to(rows, DOWN, buff=0.35)
            offset_t = always_redraw(lambda: Mono(f"offset {int(off.get_value()):3d}", 26, MUTED)
                                     .next_to(ab, RIGHT, buff=0.6))

            combo_cells = VGroup(*[RoundedRectangle(width=0.3, height=0.3, corner_radius=0.06, stroke_color=DIM,
                                                    stroke_width=1.5, fill_color=FAINT, fill_opacity=1)
                                   for _ in range(34)])
            combo_cells.arrange_in_grid(rows=2, cols=17, buff=0.1).move_to(DOWN * 2.05)
            combo_lab = label("generator × output format", 28, MUTED).next_to(combo_cells, DOWN, buff=0.2)
            v.wait_until("slide", offset=-0.2)
            self.play(FadeIn(win), FadeIn(ab), FadeIn(offset_t), FadeIn(combo_cells), FadeIn(combo_lab), run_time=0.5)
            slide_time = max(1.5, v.at("combos") - self.time - 0.3)
            self.play(off.animate(rate_func=linear).set_value(80 - 2 * chunk_w),
                      LaggedStart(*[c.animate.set_fill(BLUE, 0.55).set_stroke(BLUE) for c in combo_cells],
                                  lag_ratio=0.6),
                      run_time=slide_time)
            count = B("34", 44, YELLOW)
            count_lab = T("combinations tested", 30, FG)
            cg = VGroup(count, count_lab).arrange(RIGHT, buff=0.25).next_to(combo_cells, RIGHT, buff=0.4)
            if cg.get_right()[0] > 6.6:
                VGroup(combo_cells, cg).arrange(RIGHT, buff=0.4).move_to(DOWN * 2.05)
                combo_lab.next_to(combo_cells, DOWN, buff=0.2)
            v.wait_until("combos", offset=-0.2)
            self.play(FadeIn(cg, shift=0.1 * LEFT), Indicate(combo_cells, color=YELLOW, scale_factor=1.05), run_time=0.8)

        # ---------------------------------------------------------- i4: the pattern
        with self.vo("i4") as v:
            win.clear_updaters()
            offset_t.clear_updaters()
            self.play(FadeOut(VGroup(head, rows, win, ab, offset_t, combo_cells, combo_lab, cg)), run_time=0.5)
            notice = T("noticed something", 38, FG).next_to(model, RIGHT, buff=0.35)
            self.play(ReplacementTransform(title, notice), run_time=0.5)

            table = VGroup()
            for nm, words in SEEDS:
                n = Mono(nm, 26, BLUE if nm.startswith("P") else PURPLE, weight=BOLD)
                ws = VGroup(*[Mono(w, 26, FG) for w in words.split()]).arrange(RIGHT, buff=0.3)
                table.add(VGroup(n, ws))
            for r in table:
                r[1].next_to(r[0], RIGHT, buff=0.5)
            table.arrange(DOWN, buff=0.17, aligned_edge=LEFT).move_to(UP * 0.35 + RIGHT * 0.45)
            for r in table:  # align word columns
                r[1].align_to(table[0][1], LEFT)
            v.wait_until("words", offset=-0.2)
            self.play(LaggedStart(*[FadeIn(r, shift=0.1 * RIGHT) for r in table], lag_ratio=0.12), run_time=1.6)

            hit_rows = VGroup(*[r for r in table if r[0].text in BINARY_HITS])
            rest = VGroup(*[r for r in table if r[0].text not in BINARY_HITS])
            bands = VGroup(*[RoundedRectangle(width=r.width + 0.36, height=r.height + 0.15, corner_radius=0.1,
                                              stroke_color=PURPLE, stroke_width=2, fill_color=PURPLE,
                                              fill_opacity=0.12).move_to(r) for r in hit_rows])
            brace = Brace(bands, LEFT, buff=0.12, color=PURPLE)
            binary_lab = label("binary curves", 26, PURPLE).rotate(PI / 2).next_to(brace, LEFT, buff=0.12)
            v.wait_until("four", offset=-0.2)
            self.play(rest.animate.set_opacity(0.28), FadeIn(bands), run_time=0.8)
            self.wait(1.0)
            self.play(GrowFromCenter(brace), FadeIn(binary_lab), run_time=0.6)

            firsts = VGroup(*[w[0] for r in hit_rows for w in r[1]])
            v.wait_until("zeros", offset=-0.2)
            self.play(LaggedStart(*[f.animate.set_color(GREEN) for f in firsts], lag_ratio=0.06), run_time=1.2)
            legend = MT(f'first hex digit {span("0–7", GREEN, True)}  ⇔  top bit {span("0", GREEN, True)}'
                        f'   ·   {span("20 / 20 words", GREEN, True)}', 30, FG)
            legend.next_to(table, DOWN, buff=0.32)
            self.play(FadeIn(legend, shift=0.1 * UP), run_time=0.6)

            odds = pill("by chance: ≈ 1 in 5,800", YELLOW, size=32)
            odds.next_to(legend, DOWN, buff=0.25)
            v.wait_until("odds", offset=-0.2)
            self.play(FadeIn(odds, scale=0.8), run_time=0.6)

        # ---------------------------------------------------------- i5: the name
        with self.vo("i5") as v:
            self.play(FadeOut(VGroup(table, bands, brace, binary_lab, legend, odds, notice)),
                      FadeOut(model), run_time=0.6)
            fp = icon_fingerprint(CLAUDE, 1.4).move_to(UP * 1.3)
            self.play(Create(fp), run_time=1.2)
            name = Mono("lrand48()", 110, CLAUDE, weight=BOLD).move_to(DOWN * 0.6)
            glow = name.copy().set_fill(opacity=0).set_stroke(CLAUDE, 14, opacity=0.18)
            v.wait_until("name", offset=-0.25)
            self.play(FadeIn(name, scale=1.15), FadeIn(glow), fp.animate.scale(0.6).move_to(UP * 2.0), run_time=0.7)

        # ---------------------------------------------------------- i6: how lrand48 works
        with self.vo("i6") as v:
            self.remove(glow)
            title = Mono("lrand48()", 44, CLAUDE, weight=BOLD)
            sub = label("a classic Unix random number generator", 30, FG)
            VGroup(title, sub).arrange(RIGHT, buff=0.4).move_to(UP * 3.15)
            self.play(ReplacementTransform(name, title), FadeOut(fp), run_time=0.7)
            self.play(FadeIn(sub, shift=0.1 * LEFT), run_time=0.5)

            reg = register(B233_PREV).move_to(UP * 1.55 + RIGHT * 0.2)
            reg_lab = MT(f'state x  ·  {span("48 bits", FG, True)}', 28, MUTED).next_to(reg, UP, buff=0.3).align_to(reg, LEFT)
            reg_hex = Mono(f"0x{B233_PREV:012X}", 28, MUTED).next_to(reg, UP, buff=0.3).align_to(reg, RIGHT)
            v.wait_until("state", offset=-0.2)
            self.play(FadeIn(reg_lab), LaggedStart(*[FadeIn(c) for c in reg], lag_ratio=0.02), FadeIn(reg_hex),
                      run_time=1.2)

            rule = M(r"x \;\leftarrow\;", r"(\texttt{0x5DEECE66D}\cdot x", r"\,+\,11)", r"\bmod 2^{48}", size=48)
            rule.move_to(DOWN * 0.1)
            v.wait_until("step", offset=-0.2)
            self.play(Write(rule), run_time=1.0)
            mul_l = label("multiply", 26, CLAUDE).next_to(rule[1], DOWN, buff=0.2)
            add_l = label("add", 26, CLAUDE).next_to(rule[2], DOWN, buff=0.2)
            mod_l = label("wrap", 26, CLAUDE).next_to(rule[3], DOWN, buff=0.2)
            self.play(rule[1].animate.set_color(CLAUDE), FadeIn(mul_l), run_time=0.5)
            self.wait(0.6)
            self.play(rule[1].animate.set_color(FG), rule[2].animate.set_color(CLAUDE), FadeIn(add_l), run_time=0.5)
            self.wait(0.5)
            self.play(rule[2].animate.set_color(FG), rule[3].animate.set_color(CLAUDE), FadeIn(mod_l), run_time=0.5)
            new_reg = register(B233_STATE).move_to(reg)
            new_hex = Mono(f"0x{B233_STATE:012X}", 28, MUTED).move_to(reg_hex, aligned_edge=RIGHT)
            self.play(Transform(reg, new_reg), Transform(reg_hex, new_hex), run_time=1.2)

            clock = icon_clock(MUTED, 0.42, hour=10, minute=10)
            clock_lab = label("wraps around: clock arithmetic again", 28, MUTED)
            cg = VGroup(clock, clock_lab).arrange(RIGHT, buff=0.25).next_to(rule, DOWN, buff=0.75)
            v.wait_until("clock", offset=-0.2)
            self.play(FadeIn(cg, shift=0.1 * UP), Rotate(clock.hand_m, -TAU, about_point=clock.face.get_center()),
                      run_time=1.0)

            top31 = VGroup(*reg[:31])
            low17 = VGroup(*reg[31:])
            br = Brace(top31, DOWN, buff=0.08, color=CLAUDE)
            br_lab = label("output: the top 31 bits", 28, CLAUDE).next_to(br, DOWN, buff=0.08)
            v.wait_until("out", offset=-0.2)
            self.play(FadeOut(VGroup(cg, mul_l, add_l, mod_l)), rule.animate.set_color(FG).scale(0.75).move_to(DOWN * 3.1),
                      run_time=0.5)
            self.play(GrowFromCenter(br), FadeIn(br_lab), low17.animate.set_opacity(0.35), run_time=0.7)

            word = bit_cells("0" + bits48(B233_STATE)[:31], cell=0.245, gap=0.012, on=FG, off=MUTED, digit_size=17)
            word.next_to(br_lab, DOWN, buff=0.4)
            word.shift(RIGHT * (reg[0].get_center()[0] - word[1].get_center()[0]))
            word_lab = MT(f'= {span("0x74D59FF0", FG, True)}  ·  32-bit word', 28, MUTED).next_to(word, DOWN, buff=0.25)
            word_lab.align_to(word, RIGHT)
            v.wait_until("topbit", offset=-0.2)
            self.play(TransformFromCopy(top31, VGroup(*word[1:])), FadeIn(word[0]), run_time=0.9)
            word[0][0].set_fill(GREEN, 0.35).set_stroke(GREEN, 2)
            zero_lab = label("always 0", 28, GREEN).next_to(word[0], DOWN, buff=0.18)
            self.play(Indicate(word[0], color=GREEN, scale_factor=1.6), FadeIn(zero_lab), FadeIn(word_lab), run_time=0.8)

        # ---------------------------------------------------------- i7: brute force 17 bits
        with self.vo("i7") as v:
            self.play(FadeOut(VGroup(word, word_lab, zero_lab, br, br_lab, rule)), low17.animate.set_opacity(1),
                      run_time=0.5)
            for i in range(31, 48):
                set_cell(reg, i, "?", YELLOW)
                reg[i][0].set_fill(YELLOW, 0.12).set_stroke(YELLOW, 1)
            br2 = Brace(VGroup(*reg[31:]), DOWN, buff=0.08, color=YELLOW)
            br2_lab = label("17 hidden bits", 28, YELLOW).next_to(br2, DOWN, buff=0.08)
            known = Brace(VGroup(*reg[:31]), DOWN, buff=0.08, color=FG)
            known_lab = MT(f'known: seed word {span("74D59FF0", FG, True)}', 28, MUTED).next_to(known, DOWN, buff=0.08)
            self.play(LaggedStart(*[FadeIn(c, scale=1.3) for c in reg[31:]], lag_ratio=0.08), FadeOut(reg_hex),
                      run_time=1.2)
            self.play(GrowFromCenter(br2), FadeIn(br2_lab), run_time=0.5)
            self.play(GrowFromCenter(known), FadeIn(known_lab), run_time=0.5)

            tracker = ValueTracker(0)
            of = Mono("/ 131,072 guesses (2¹⁷)", 30, MUTED)
            counter_proto = Mono("131,072", 46, YELLOW, weight=BOLD)
            row = VGroup(counter_proto, of).arrange(RIGHT, buff=0.3).move_to(DOWN * 0.55)
            right_edge = counter_proto.get_right()
            counter = always_redraw(lambda: Mono(f"{int(tracker.get_value()):,}", 46, YELLOW, weight=BOLD)
                                    .move_to(right_edge, aligned_edge=RIGHT))
            v.wait_until("brute", offset=-0.2)
            self.play(FadeIn(counter), FadeIn(of), run_time=0.4)
            self.play(tracker.animate.set_value(131072), run_time=max(1.5, v.at("next") - self.time - 0.7),
                      rate_func=rate_functions.ease_in_out_sine)
            counter.clear_updaters()

            hidden = format(B233_HIDDEN, "017b")
            for j, ch in enumerate(hidden):
                set_cell(reg, 31 + j, ch, GREEN)
                reg[31 + j][0].set_fill(GREEN, 0.15).set_stroke(GREEN, 1)
            found = Mono(f"found: 0x{B233_HIDDEN:05X}", 30, GREEN).next_to(br2_lab, DOWN, buff=0.12).align_to(br2_lab, RIGHT)

            ws = VGroup(*[Mono(f"{w:08X}", 28, FG) for w in B233]).arrange(RIGHT, buff=0.8).move_to(DOWN * 1.85)
            arrows = VGroup(*[Arrow(ws[i].get_right(), ws[i + 1].get_left(), buff=0.1, color=MUTED, stroke_width=3,
                                    max_tip_length_to_length_ratio=0.35) for i in range(4)])
            ticks = VGroup(*[check_mark(GREEN, 0.36, 6).next_to(ws[i], DOWN, buff=0.15) for i in range(1, 5)])
            ws_lab = label("B-233 seed: the generator predicts the next four words", 26, PURPLE)
            ws_lab.next_to(ws, UP, buff=0.2).align_to(ws, LEFT)
            v.wait_until("next", offset=-0.3)
            self.play(FadeIn(found), FadeOut(counter), FadeOut(of), FadeIn(ws[0]), FadeIn(ws_lab), run_time=0.5)
            for i in range(4):
                self.play(GrowArrow(arrows[i]), FadeIn(ws[i + 1], shift=0.1 * RIGHT), run_time=0.35)
                self.play(FadeIn(ticks[i], scale=0.6), run_time=0.2)

            summary = VGroup()
            for nm in BINARY_HITS:
                summary.add(VGroup(Mono(nm, 28, PURPLE, weight=BOLD), check_mark(GREEN, 0.34, 6)).arrange(RIGHT, buff=0.18))
            summary.arrange(RIGHT, buff=0.6)
            tally = B("4 / 4 seeds", 34, GREEN)
            sg = VGroup(summary, tally).arrange(RIGHT, buff=0.8).move_to(DOWN * 3.1)
            v.wait_until("match", offset=-0.2)
            self.play(LaggedStart(*[FadeIn(x, shift=0.1 * UP) for x in summary], lag_ratio=0.25), run_time=1.0)
            self.play(FadeIn(tally, scale=0.8), run_time=0.4)

        self.clear_all()

from common import *

# A real ECDSA P-256 / SHA-256 signature (DER) over the message "Pay Bob $100".
SIG_HEX = ("304502202617752E853F16FB0FFE5FF555D7E15688F6B8E90798E789274863732B1DE972"
           "022100ED2B5BA2FDEFC68DA29AB842672CD087A38CD9CB93F06ECE2E896D87933E2015")
INK = "#8fb8ff"


def squiggle(width=2.0, color=INK, stroke=5) -> VMobject:
    """A hand-written looking signature scrawl."""
    pts = [(-1.0, -0.05), (-0.86, 0.42), (-0.74, -0.22), (-0.6, 0.12), (-0.47, 0.34), (-0.4, -0.16),
           (-0.24, 0.26), (-0.12, -0.1), (0.02, 0.22), (0.12, -0.06), (0.24, 0.18), (0.36, -0.12),
           (0.52, 0.2), (0.66, -0.04), (0.86, 0.12), (1.0, -0.02), (0.7, -0.3), (0.1, -0.34), (-0.85, -0.3)]
    m = VMobject(stroke_color=color, stroke_width=stroke)
    m.set_points_smoothly([np.array([x, y, 0.0]) for x, y in pts])
    return m.scale_to_fit_width(width)


def paper(w=2.4, h=1.9, color=FG, fill=FAINT) -> VGroup:
    f = 0.32
    page = Polygon([-w / 2, h / 2, 0], [w / 2 - f, h / 2, 0], [w / 2, h / 2 - f, 0], [w / 2, -h / 2, 0],
                   [-w / 2, -h / 2, 0], fill_color=fill, fill_opacity=1, stroke_color=color, stroke_width=2.5)
    fold = Polygon([w / 2 - f, h / 2, 0], [w / 2 - f, h / 2 - f, 0], [w / 2, h / 2 - f, 0],
                   fill_color=color, fill_opacity=0.3, stroke_color=color, stroke_width=2)
    return VGroup(page, fold)


def message_card(amount="$100", w=2.4, h=1.9) -> VGroup:
    """A small document reading 'Pay Bob $100'. g.amount is the amount text."""
    p = paper(w, h)
    l1 = Mono("Pay Bob", 30, FG)
    l2 = Mono(amount, 30, FG)
    txt = VGroup(l1, l2).arrange(DOWN, buff=0.18, aligned_edge=LEFT).move_to(p[0]).shift(LEFT * 0.12)
    g = VGroup(p, txt)
    g.amount = l2
    return g


def machine(name, color, w=2.0, h=1.1) -> VGroup:
    box = RoundedRectangle(width=w, height=h, corner_radius=0.16, fill_color=PANEL, fill_opacity=1,
                           stroke_color=color, stroke_width=3)
    t = B(name, 32, color).move_to(box)
    return VGroup(box, t)


def sig_card() -> VGroup:
    lab = label("signature", 26, GREEN)
    lines = VGroup(Mono(f"{SIG_HEX[0:8]} {SIG_HEX[8:16]}", 28, GREEN),
                   Mono(f"{SIG_HEX[16:24]} {SIG_HEX[24:32]}…", 28, GREEN)).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
    return boxed(VGroup(lab, lines).arrange(DOWN, buff=0.18, aligned_edge=LEFT), GREEN, buff=0.22)


def sig_badge() -> VGroup:
    t = Mono(SIG_HEX[:8] + "…", 26, GREEN)
    r = RoundedRectangle(width=t.width + 0.3, height=t.height + 0.26, corner_radius=0.1, fill_color=PANEL,
                         fill_opacity=1, stroke_color=GREEN, stroke_width=2)
    t.move_to(r)
    return VGroup(r, t)


def masked_person(color=RED, h=1.5) -> VGroup:
    p = icon_person(color, h)
    head = p[0]
    mask = RoundedRectangle(width=head.width * 1.22, height=head.height * 0.34, corner_radius=head.height * 0.12,
                            fill_color=BG, fill_opacity=1, stroke_width=0).move_to(head.get_center() + UP * head.height * 0.04)
    eyes = VGroup(*[Dot(radius=head.width * 0.07, color=color).move_to(mask.get_center() + RIGHT * dx * head.width)
                    for dx in (-0.2, 0.2)])
    return VGroup(p, mask, eyes)


def one_way_street(width=11.0) -> VGroup:
    """Road with a ONE WAY sign: easy forward (green), blocked backward (red)."""
    road = RoundedRectangle(width=width, height=1.5, corner_radius=0.2, fill_color="#1b2230", fill_opacity=1,
                            stroke_color=DIM, stroke_width=2)
    mid = DashedLine(road.get_left() + RIGHT * 0.4, road.get_right() + LEFT * 0.4, dash_length=0.35,
                     dashed_ratio=0.55, stroke_color=YELLOW, stroke_width=3, stroke_opacity=0.7)
    post = Rectangle(width=0.12, height=1.2, fill_color=MUTED, fill_opacity=1, stroke_width=0)
    plate = RoundedRectangle(width=3.3, height=1.0, corner_radius=0.08, fill_color="#0d0f13", fill_opacity=1,
                             stroke_color=FG, stroke_width=3)
    shaft_w, shaft_h, head_w, head_h = 2.25, 0.46, 0.55, 0.78
    x0 = -(shaft_w + head_w) / 2
    sign_arrow = Polygon([x0, shaft_h / 2, 0], [x0 + shaft_w, shaft_h / 2, 0], [x0 + shaft_w, head_h / 2, 0],
                         [x0 + shaft_w + head_w, 0, 0], [x0 + shaft_w, -head_h / 2, 0], [x0 + shaft_w, -shaft_h / 2, 0],
                         [x0, -shaft_h / 2, 0], fill_color=FG, fill_opacity=1, stroke_width=0)
    sign_txt = B("ONE WAY", 26, "#0d0f13")
    post.next_to(road, UP, buff=0).shift(LEFT * (width / 2 - 1.9))
    plate.next_to(post, UP, buff=0)
    sign_arrow.move_to(plate)
    sign_txt.move_to(sign_arrow).shift(LEFT * 0.27)
    sign = VGroup(post, plate, sign_arrow, sign_txt)
    fwd = Arrow(road.get_left() + RIGHT * 0.8, road.get_right() + LEFT * 0.8, buff=0, color=GREEN, stroke_width=8,
                max_tip_length_to_length_ratio=0.05, tip_length=0.35).shift(UP * 0.38)
    bwd = Arrow(road.get_right() + LEFT * 0.8, road.get_center() + RIGHT * 0.9, buff=0, color=RED, stroke_width=8,
                max_tip_length_to_length_ratio=0.12, tip_length=0.35).shift(DOWN * 0.38)
    barrier = VGroup(*[Rectangle(width=0.18, height=0.22, fill_color=RED if i % 2 == 0 else FG, fill_opacity=1,
                                 stroke_width=0) for i in range(5)]).arrange(DOWN, buff=0)
    barrier.move_to(road.get_center() + RIGHT * 0.55 + DOWN * 0.38)
    g = VGroup(road, mid, sign, fwd, bwd, barrier)
    g.road, g.mid, g.sign, g.fwd, g.bwd, g.barrier = road, mid, sign, fwd, bwd, barrier
    return g


class Signatures(VOScene):
    def construct(self):
        self.chapter(1, "A signature you can't copy")

        # ---------------------------------------------------------- s1: who am I talking to?
        with self.vo("s1") as v:
            browser = icon_browser("https://bank.example", w=3.6, h=2.4).move_to(LEFT * 4.5 + DOWN * 0.3)
            you = label("your browser", 30, FG).next_to(browser, DOWN, buff=0.3)
            self.play(FadeIn(browser, shift=0.2 * RIGHT), FadeIn(you), run_time=0.8)
            question = B("Who am I really talking to?", 46).move_to(UP * 2.75)
            self.play(FadeIn(question, shift=0.15 * DOWN), run_time=0.8)
            line = DashedLine(browser.get_right() + RIGHT * 0.15, RIGHT * 3.1 + DOWN * 0.3, dash_length=0.18,
                              stroke_color=MUTED, stroke_width=3)
            qmark = B("?", 90, MUTED).move_to(RIGHT * 4.5 + DOWN * 0.3)
            self.play(Create(line), FadeIn(qmark, scale=0.6), run_time=0.9)
            track = Line(line.get_start(), line.get_end())
            packets = VGroup(*[Dot(radius=0.07, color=BLUE) for _ in range(3)])
            self.play(LaggedStart(*[MoveAlongPath(p, track, rate_func=linear) for p in packets], lag_ratio=0.3),
                      run_time=1.6)
            self.remove(*packets)

            bank = icon_bank(FG, 2.0).move_to(RIGHT * 4.5 + DOWN * 0.1)
            bank_lab = label("my bank", 30, FG).next_to(bank, DOWN, buff=0.35)
            v.wait_until("bank", offset=-0.2)
            self.play(ReplacementTransform(qmark, bank), FadeIn(bank_lab, shift=0.1 * UP), run_time=0.5)

            eve = masked_person(RED, 1.5).move_to(DOWN * 0.15)
            eve_lab = label("an impostor?", 30, RED).next_to(eve, DOWN, buff=0.3)
            v.wait_until("eve", offset=-0.2)
            self.play(line.animate.set_stroke(RED, opacity=0.8), FadeIn(eve, shift=0.3 * UP),
                      FadeIn(eve_lab), run_time=0.6)
            grab = Dot(radius=0.08, color=BLUE).move_to(line.get_start())
            self.play(grab.animate.move_to(eve.get_left() + LEFT * 0.1).set_color(RED), run_time=0.7,
                      rate_func=linear)
            self.play(FadeOut(grab, scale=0.3), Wiggle(eve, scale_value=1.06), run_time=0.6)

        # ---------------------------------------------------------- s2: paper signatures are copyable
        with self.vo("s2") as v:
            self.play(FadeOut(VGroup(browser, you, question, line, bank, bank_lab, eve, eve_lab)), run_time=0.5)
            doc = paper(3.0, 3.6).move_to(LEFT * 4.3 + DOWN * 0.1)
            heading = Mono("I.O.U.", 30, FG).move_to(doc[0].get_top() + DOWN * 0.55)
            lines = VGroup(*[Line(LEFT, RIGHT, stroke_color=FG, stroke_width=2, stroke_opacity=0.45).set_width(w)
                             for w in (2.2, 2.0, 2.2, 1.5)]).arrange(DOWN, buff=0.28, aligned_edge=LEFT)
            lines.next_to(heading, DOWN, buff=0.4)
            sig = squiggle(2.1).move_to(doc[0].get_bottom() + UP * 0.6)
            v.wait_until("sig", offset=-0.2)
            self.play(FadeIn(VGroup(doc, heading, lines), shift=0.15 * UP), run_time=0.6)
            self.play(Create(sig), run_time=1.3, rate_func=linear)

            v.wait_until("copyable", offset=-0.2)
            ghost = sig.copy().set_stroke(opacity=0.9)
            copy_tag = pill("copy", MUTED, size=26, mono=True).next_to(doc, UP, buff=0.25)
            self.play(ghost.animate.shift(UP * 0.35 + RIGHT * 0.35), FadeIn(copy_tag, shift=0.1 * DOWN), run_time=0.7)

            others = VGroup()
            for title in ("I quit.", "Sell my car", "IOU $1M"):
                d = paper(2.6, 2.5)
                t = Mono(title, 26, FG).move_to(d[0].get_top() + DOWN * 0.55)
                ls = VGroup(*[Line(LEFT, RIGHT, stroke_color=FG, stroke_width=2, stroke_opacity=0.4).set_width(w)
                              for w in (1.8, 1.4)]).arrange(DOWN, buff=0.25, aligned_edge=LEFT).next_to(t, DOWN, buff=0.3)
                others.add(VGroup(d, t, ls))
            others.arrange(RIGHT, buff=0.35).move_to(RIGHT * 2.45 + DOWN * 0.1)
            self.play(LaggedStart(*[FadeIn(o, shift=0.2 * LEFT) for o in others], lag_ratio=0.25), run_time=1.2)

            v.wait_until("copy", offset=-0.2)
            copies = [ghost.copy().scale(0.82).move_to(o[0].get_bottom() + UP * 0.48) for o in others]
            self.play(*[TransformFromCopy(ghost, c) for c in copies], FadeOut(copy_tag), run_time=0.9)
            forged = VGroup(*[stamp("FORGED", RED, 22, angle=-14 * DEGREES).move_to(o[0].get_center() + UP * 0.05)
                              for o in others])
            self.play(LaggedStart(*[FadeIn(f, scale=1.5) for f in forged], lag_ratio=0.2), run_time=0.8)

        # ---------------------------------------------------------- s3: two keys
        with self.vo("s3") as v:
            self.play(FadeOut(VGroup(doc, heading, lines, sig, ghost, others, *copies, forged)), run_time=0.5)
            gold = icon_key(GOLD, 1.9).move_to(LEFT * 2.0 + UP * 0.4)
            blue = icon_key(BLUE, 1.9).move_to(RIGHT * 2.0 + UP * 0.4)
            gl = B("private key", 34, GOLD).next_to(gold, DOWN, buff=0.4)
            bl = B("public key", 34, BLUE).next_to(blue, DOWN, buff=0.4)
            v.wait_until("keys", offset=-0.2)
            self.play(FadeIn(gold, shift=0.2 * RIGHT), FadeIn(blue, shift=0.2 * LEFT), FadeIn(gl), FadeIn(bl),
                      run_time=0.6)
            only = VGroup(icon_padlock(GOLD, 0.36), label("only you hold it", 28, GOLD)).arrange(RIGHT, buff=0.15)
            only.next_to(gl, DOWN, buff=0.22)
            v.wait_until("priv", offset=-0.2)
            self.play(Indicate(gold, color=YELLOW, scale_factor=1.15), FadeIn(only, shift=0.1 * UP), run_time=0.7)

            # Rows: signing on top, verifying below.
            y1, y2 = 1.45, -1.85
            msg_a = message_card().move_to(LEFT * 5.25 + UP * y1)
            plus_a = B("+", 40, MUTED).move_to(LEFT * 3.75 + UP * y1)
            key_a_pos = LEFT * 2.75 + UP * y1
            sign_box = machine("sign", GOLD).move_to(RIGHT * 0.15 + UP * y1)
            arr_a1 = arrow(key_a_pos + RIGHT * 0.8, sign_box.get_left(), color=MUTED, buff=0.08)
            card = sig_card().move_to(RIGHT * 4.25 + UP * y1)
            arr_a2 = arrow(sign_box.get_right(), card.get_left(), color=MUTED, buff=0.12)
            priv_tag = label("private", 26, GOLD).move_to(key_a_pos + UP * 0.62)
            pub_tag = label("public", 26, BLUE).move_to(LEFT * 2.75 + UP * (y2 + 0.62))
            self.play(FadeOut(only), FadeOut(gl), FadeOut(bl),
                      gold.animate.scale_to_fit_width(1.35).move_to(key_a_pos),
                      blue.animate.scale_to_fit_width(1.35).move_to(LEFT * 2.75 + UP * y2).set_opacity(0.3),
                      FadeIn(priv_tag), run_time=0.8)

            v.wait_until("sign", offset=-0.2)
            self.play(FadeIn(msg_a, shift=0.2 * RIGHT), FadeIn(plus_a), run_time=0.5)
            self.play(GrowArrow(arr_a1), FadeIn(sign_box, scale=0.9), run_time=0.6)
            self.play(GrowArrow(arr_a2), FadeIn(card[0]), FadeIn(card[1][0]), run_time=0.5)
            self.play(AddTextLetterByLetter(card[1][1][0], time_per_char=0.03),
                      AddTextLetterByLetter(card[1][1][1], time_per_char=0.03), run_time=0.7)
            link = DashedLine(msg_a.amount.get_bottom() + DOWN * 0.08, card[0].get_bottom() + DOWN * 0.08,
                              path_arc=0.5, dash_length=0.12, stroke_color=GREEN, stroke_width=2.5, stroke_opacity=0.8)
            dep = label("depends on every bit of the message", 28, GREEN).next_to(link, DOWN, buff=0.08)
            self.play(Create(link), FadeIn(dep), run_time=0.8)

            v.wait_until("pub", offset=-0.2)
            self.play(FadeOut(link), FadeOut(dep), blue.animate.set_opacity(1), FadeIn(pub_tag), run_time=0.5)
            crowd = VGroup(*[icon_person(c, 0.85) for c in (BLUE, TEAL, PURPLE, PINK)]).arrange(RIGHT, buff=0.55)
            crowd.move_to(RIGHT * 2.9 + UP * (y2 - 0.1))
            anyone = label("anyone can have it", 28, BLUE).next_to(crowd, DOWN, buff=0.25)
            self.play(LaggedStart(*[FadeIn(c, shift=0.1 * UP) for c in crowd], lag_ratio=0.15), FadeIn(anyone),
                      run_time=0.6)
            minis = VGroup(*[icon_key(BLUE, 0.55).move_to(blue) for _ in crowd])
            self.play(LaggedStart(*[m.animate.next_to(c, UP, buff=0.12) for m, c in zip(minis, crowd)],
                                  lag_ratio=0.15), run_time=0.8)

            msg_b = message_card().move_to(LEFT * 5.25 + UP * y2)
            badge = sig_badge().move_to(msg_b[0][0].get_corner(DR) + UP * 0.05 + LEFT * 0.35)
            plus_b = B("+", 40, MUTED).move_to(LEFT * 3.75 + UP * y2)
            verify_box = machine("verify", BLUE).move_to(RIGHT * 0.15 + UP * y2)
            arr_b1 = arrow(LEFT * 2.75 + UP * y2 + RIGHT * 0.8, verify_box.get_left(), color=MUTED, buff=0.08)
            ok = VGroup(Circle(radius=0.55, stroke_color=GREEN, stroke_width=5, fill_color=GREEN, fill_opacity=0.12),
                        check_mark(GREEN, 0.75, 9)).move_to(RIGHT * 3.4 + UP * y2)
            ok[1].move_to(ok[0])
            ok_lab = B("valid", 34, GREEN).next_to(ok, RIGHT, buff=0.3)
            arr_b2 = arrow(verify_box.get_right(), ok.get_left(), color=MUTED, buff=0.12)
            v.wait_until("verify", offset=-0.2)
            self.play(FadeOut(VGroup(crowd, minis, anyone)), TransformFromCopy(msg_a, msg_b),
                      FadeIn(plus_b), run_time=0.6)
            self.play(TransformFromCopy(card, badge), run_time=0.6)
            self.play(GrowArrow(arr_b1), FadeIn(verify_box, scale=0.9), run_time=0.5)
            self.play(GrowArrow(arr_b2), FadeIn(ok, scale=0.7), FadeIn(ok_lab, shift=0.1 * LEFT), run_time=0.5)

            v.wait_until("cant", offset=-0.2)
            ghost_key = blue.copy().set_opacity(0.85)
            self.play(ghost_key.animate.move_to(sign_box.get_bottom() + DOWN * 0.55), run_time=0.5)
            no = cross_mark(RED, 0.55, 9).move_to(ghost_key)
            cant = label("can't sign", 28, RED).next_to(ghost_key, RIGHT, buff=0.3)
            self.play(FadeIn(no, scale=1.4), FadeIn(cant), run_time=0.35)

        # ---------------------------------------------------------- s4: tamper
        with self.vo("s4") as v:
            self.play(FadeOut(VGroup(ghost_key, no, cant)), run_time=0.3)
            nine = Mono("$900", 30, FG).move_to(msg_b.amount, aligned_edge=LEFT)
            nine[1].set_color(RED)
            v.wait_until("edit", offset=0.0)
            self.play(Transform(msg_b.amount, nine), run_time=0.5)
            self.play(Circumscribe(msg_b.amount[1], color=RED, buff=0.06, time_width=0.6), run_time=0.7)
            bad = VGroup(Circle(radius=0.55, stroke_color=RED, stroke_width=5, fill_color=RED, fill_opacity=0.12),
                         cross_mark(RED, 0.55, 9)).move_to(ok)
            bad[1].move_to(bad[0])
            bad_lab = B("invalid", 34, RED).next_to(bad, RIGHT, buff=0.3)
            v.wait_until("fail", offset=-0.25)
            self.play(Indicate(verify_box[1], color=RED, scale_factor=1.15),
                      verify_box[0].animate.set_stroke(RED, 4), run_time=0.5)
            self.play(ReplacementTransform(ok, bad), ReplacementTransform(ok_lab, bad_lab), run_time=0.5)

        # ---------------------------------------------------------- s5: one-way street
        with self.vo("s5") as v:
            self.play(FadeOut(VGroup(msg_a, plus_a, gold, priv_tag, arr_a1, sign_box, arr_a2, card,
                                     msg_b, badge, plus_b, blue, pub_tag, arr_b1, verify_box, arr_b2, bad, bad_lab)),
                      run_time=0.5)
            street = one_way_street(11.4).move_to(DOWN * 0.15)
            street_title = B("a one-way street", 46).move_to(UP * 2.95)
            easy = B("easy to do", 34, GREEN).next_to(street.road, UP, buff=0.25).shift(RIGHT * 2.6)
            hard = B("practically impossible to undo", 34, RED).next_to(street.road, DOWN, buff=0.3).shift(RIGHT * 0.9)
            v.wait_until("oneway", offset=-0.2)
            self.play(FadeIn(street.road), Create(street.mid), FadeIn(street.sign, shift=0.2 * DOWN),
                      FadeIn(street_title, shift=0.1 * DOWN), run_time=0.7)
            car = RoundedRectangle(width=0.7, height=0.36, corner_radius=0.1, fill_color=GREEN, fill_opacity=1,
                                   stroke_width=0).move_to(street.fwd.get_start() + RIGHT * 0.3)
            self.play(GrowArrow(street.fwd), FadeIn(easy, shift=0.1 * DOWN), FadeIn(car), run_time=0.5)
            self.play(car.animate.move_to(street.fwd.get_end() + LEFT * 0.6), run_time=0.9, rate_func=smooth)
            car2 = car.copy().set_fill(RED).move_to(street.bwd.get_start() + LEFT * 0.4)
            self.play(GrowArrow(street.bwd), FadeIn(street.barrier, scale=1.3), FadeIn(car2), FadeIn(hard, shift=0.1 * UP),
                      run_time=0.6)
            self.play(car2.animate.move_to(street.barrier.get_right() + RIGHT * 0.45), run_time=0.6, rate_func=rush_into)
            self.play(Wiggle(car2, scale_value=1.1, rotation_angle=0.03 * TAU), run_time=0.5)

            road_grp = VGroup(street, car, car2, easy, hard)
            acr = VGroup(*[B(ch, 110, FG) for ch in "ECDSA"]).arrange(RIGHT, buff=0.12).move_to(UP * 0.6)
            v.wait_until("ecdsa", offset=-0.2)
            self.play(FadeOut(road_grp, shift=0.3 * DOWN), FadeOut(street_title), run_time=0.5)
            self.play(LaggedStart(*[FadeIn(c, shift=0.2 * UP) for c in acr], lag_ratio=0.12), run_time=0.7)
            words = ["Elliptic", "Curve", "Digital", "Signature", "Algorithm"]
            colors = [BLUE, BLUE, GREEN, GREEN, FG]
            full = VGroup(*[MarkupText(f'<b><span foreground="{c}">{w[0]}</span>{w[1:]}</b>', font=SANS,
                                       font_size=50, color=FG) for w, c in zip(words, colors)])
            full.arrange(RIGHT, buff=0.32)
            if full.width > 12.8:
                full.scale_to_fit_width(12.8)
            full.move_to(UP * 0.2)
            self.play(acr.animate.scale(0.5).move_to(UP * 2.45), run_time=0.6)
            self.play(LaggedStart(*[AnimationGroup(TransformFromCopy(acr[i], full[i][0]), FadeIn(full[i][1:], shift=0.1 * RIGHT))
                                    for i in range(5)], lag_ratio=0.3), run_time=2.0)

            ingr = label("two ingredients", 30, MUTED).move_to(DOWN * 1.15)
            card1 = VGroup(icon_clock(FG, 0.62, hour=2, minute=0), B("Clock arithmetic", 36, FG)).arrange(RIGHT, buff=0.35)
            card2 = VGroup(mini_curve(BLUE, 0.95), B("Elliptic curves", 36, BLUE)).arrange(RIGHT, buff=0.35)
            c1 = boxed(card1, DIM, buff=0.3)
            c2 = boxed(card2, BLUE, buff=0.3)
            plus = B("+", 48, MUTED)
            cards = VGroup(c1, plus, c2).arrange(RIGHT, buff=0.45).move_to(DOWN * 2.35)
            self.play(FadeIn(ingr), run_time=0.4)
            v.wait_until("clockword", offset=-0.2)
            self.play(FadeIn(c1, shift=0.2 * UP), run_time=0.5)
            v.wait_until("curveword", offset=-0.2)
            self.play(FadeIn(plus), FadeIn(c2, shift=0.2 * UP), run_time=0.5)

        self.clear_all()

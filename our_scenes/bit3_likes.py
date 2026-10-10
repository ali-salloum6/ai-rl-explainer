"""
Bit3Likes — people as the reward: the like button, and what it tips into.

  1 two answers; a thumbs-up picks one
  2 2017: two clips of a simulated body, picks pile up to ~900; it backflips (a clock: under an hour)
  3 the robot hand: from the camera it looks like a grasp (a tick); from the side, a gap (the trick)
  4 the loop again: people's picks train a judge «حَكَم»; the judge's stars stream to the chatbot
  5 a thumbs-up takes the score's place: training with a like button (video 3's question, answered)
  6 video 3's dial: thumbs-ups push the needle to «أكيد»
  7 April 2025: praise sparkles on any idea; the update rolls back and the needle returns
  8 a reward nobody can sweet-talk: a sum checked right / wrong, code that runs or doesn't
  9 DeepSeek-R1-Zero: a bar from 16% to 71%
 10 its answers grow longer, looping back to check
 11 but when the goal is a real job? (a question mark in the world card)

Render (preview): xvfb-run -a .venv/bin/manimgl our_scenes/bit3_likes.py Bit3Likes -w -l --video_dir ./media
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from our_scenes.rl_kit import *  # noqa: F401,F403
from our_scenes.rl_kit import _bar, _card  # noqa: F401


def bit2_end_state() -> SimpleNamespace:
    """Bit 2's last frame, rebuilt: the rule (small, top), the games and their tick, the answer card and
    its empty score slot."""
    rule = rule_text(1.0).move_to(np.array([0, 0.2, 0]))
    ul = Line(rule[1].get_corner(DL) + 0.12 * DOWN, rule[1].get_corner(DR) + 0.12 * DOWN).set_stroke(ACCENT, 3)
    top = VGroup(rule, ul).scale(0.55).move_to(np.array([0, 3.0, 0]))
    mini = VGroup(Maze(cell=1.0), coin_icon(0.6)).set_height(1.3)
    mini[1].move_to(mini[0].cell_center(COIN))
    games = VGroup(mini, boat(0.9, ACCENT)).arrange(RIGHT, buff=0.8).move_to(np.array([-3.4, 0.0, 0]))
    ok = check_mark(0.5).next_to(games, DOWN, buff=0.3)
    ans = answer_card(3.4, 4, seed=3).move_to(np.array([2.6, 0.1, 0]))
    slot = DashedVMobject(RoundedRectangle(width=1.5, height=0.7, corner_radius=0.35), num_dashes=24)
    slot.set_stroke(WARM, width=2.4).next_to(ans, DOWN, buff=0.35)
    q = ar_question(0.5, WARM).move_to(slot)
    return SimpleNamespace(top=top, games=games, ok=ok, ans=ans, slot=slot, q=q,
                           grp=VGroup(top, games, ok, ans, slot, q))


def clip_card(pose: float, size: float = 1.6) -> VGroup:
    """A short clip of the simulated body: a dark frame with the figure tilted by `pose` radians."""
    frame = _card(size, 0.8 * size, stroke=CARD_STROKE, r=0.12)
    fig = stick_figure(0.55 * size).rotate(pose).move_to(frame)
    ground = Line(frame.get_corner(DL) + np.array([0.1, 0.12, 0]), frame.get_corner(DR) + np.array([-0.1, 0.12, 0]))
    ground.set_stroke(MUTED, width=2)
    return VGroup(frame, ground, fig)


class Bit3Likes(RLScene):
    def construct(self):
        end2 = bit2_end_state()
        self.add(end2.grp)
        self.continue_from("Bit2Coin")

        # ---- 1. ask people: two answers, they pick the better one ----------------------------------
        with self.narrate("bit3_likes.1"):
            a = end2.ans
            b = answer_card(3.4, 4, seed=8).move_to(np.array([2.4, 0.1, 0]))
            self.play(FadeOut(VGroup(end2.top, end2.games, end2.ok, end2.slot, end2.q)),
                      a.animate.move_to(np.array([-2.4, 0.1, 0])), run_time=0.6)
            self.play(FadeIn(b, shift=0.2 * LEFT), run_time=0.4)
            who = person_icon(0.9, INK_2).move_to(np.array([0, -2.3, 0]))
            self.until("وبينقّوا", lead=0.3)
            th = thumbs_up(0.7, ACCENT).move_to(who.get_center())
            self.play(FadeIn(who), run_time=0.3)
            self.play(th.animate.move_to(b.card.get_corner(UR) + np.array([-0.2, -0.05, 0])), run_time=0.5)
            self.play(b.card.animate.set_stroke(ACCENT, width=3), a.animate.set_opacity(0.45), run_time=0.35)
            pick1 = VGroup(a, b, who, th)

        # ---- 2. 2017: a backflip from ~900 choices, in under an hour of one person's time --------------
        with self.narrate("bit3_likes.2"):
            c1, c2 = clip_card(0.35), clip_card(-0.5)
            clips = VGroup(c1, c2).arrange(RIGHT, buff=0.6).move_to(np.array([-2.3, 0.4, 0]))
            yr = name_chip("2017").next_to(clips, UP, buff=0.3)
            picks = Integer(0, font_size=38, text_config=dict(font=LATIN_FONT)).set_fill(ACCENT)
            picks_lab = ar_text("اختيار", 30, INK_2)
            pk = VGroup(picks_lab, picks)

            def place_pk(m):
                picks.next_to(picks_lab, LEFT, buff=0.18)
            picks_lab.move_to(np.array([-1.6, -1.55, 0]))
            pk.add_updater(place_pk)
            self.play(FadeOut(pick1), FadeIn(clips), FadeIn(yr), FadeIn(pk), run_time=0.6)
            mini_th = thumbs_up(0.4, ACCENT)
            dur = max(1.2, self.to("تسعمية", lead=0.0) + 0.6)
            self.play(ChangeDecimalToValue(picks, 900, run_time=dur, rate_func=rush_into),
                      Succession(*[Indicate(c, color=ACCENT, scale_factor=1.05, run_time=dur / 6) for c in
                                   (c1, c2, c2, c1, c2, c1)]), run_time=dur)
            body = stick_figure(1.3, INK).move_to(np.array([3.3, -0.2, 0]))
            ground = Line(np.array([2.1, -1.0, 0]), np.array([4.5, -1.0, 0])).set_stroke(MUTED, width=2)
            clock = icon_clock(0.7).move_to(np.array([-3.6, -1.55, 0]))
            self.play(FadeIn(body), ShowCreation(ground), FadeIn(clock), run_time=0.4)
            flip = max(0.9, min(1.4, self.line_left()))
            self.play(Rotate(body, TAU, about_point=body.get_center() + 0.25 * UP),
                      Rotate(clock.minute, -TAU * 0.8, about_point=clock.face.get_center()), run_time=flip,
                      rate_func=smooth)
            flip_bits = VGroup(clips, yr, pk, body, ground, clock)

        # ---- 3. the robot hand: looks like a grasp from the camera; from the side, a gap ---------------
        with self.narrate("bit3_likes.3"):
            pk.clear_updaters()
            self.play(FadeOut(flip_bits), run_time=0.4)
            cam = camera_icon(0.9).move_to(np.array([-5.0, -0.4, 0]))
            ball = ball_icon(0.7).move_to(np.array([1.4, -0.4, 0]))
            hand = gripper(1.0).move_to(np.array([-1.0, 1.6, 0]))
            self.play(FadeIn(cam), FadeIn(ball), FadeIn(hand), run_time=0.5)
            stop = np.array([-1.3, -0.4, 0])          # between the camera and the ball, not at the ball
            self.until("توقف", lead=0.5)
            self.play(hand.animate.move_to(stop), run_time=0.8)
            # the camera's view (top right): the hand covers the ball, so it looks held
            view = _card(2.6, 1.7, stroke=INK_2, r=0.16).move_to(np.array([4.2, 2.0, 0]))
            vcam = camera_icon(0.35).next_to(view, LEFT, buff=0.12).align_to(view, UP)
            vball = ball_icon(0.55).move_to(view.get_center() + 0.1 * RIGHT)
            vhand = gripper(0.7).move_to(view.get_center() + 0.25 * LEFT)
            vhand.fingers.set_stroke(INK_2)
            vtick = check_mark(0.35).next_to(view, DOWN, buff=0.15)
            ray = DashedLine(cam.get_right(), ball.get_left(), dash_length=0.12).set_stroke(MUTED, width=2)
            self.until("واللي", lead=0.3)
            self.play(ShowCreation(ray), FadeIn(view), FadeIn(vcam), FadeIn(vball), FadeIn(vhand), run_time=0.6)
            self.play(ShowCreation(vtick), run_time=0.35)
            gap = DashedLine(hand.get_right() + 0.1 * RIGHT, ball.get_left() + 0.05 * LEFT, dash_length=0.08)
            gap.set_stroke(RED, width=4)
            self.play(ShowCreation(gap), Indicate(ball, color=RED, scale_factor=1.1), run_time=0.6)
            hand_bits = VGroup(cam, ball, hand, view, vcam, vball, vhand, vtick, ray, gap)

        # ---- 4. for chat, a judge learns people's taste and scores the chatbot -----------------------
        with self.narrate("bit3_likes.4"):
            self.play(FadeOut(hand_bits), run_time=0.4)
            lp = rl_loop(content=None, p4=(0.25, 0.25, 0.25, 0.25))
            bot = writer_box(2.6, 1.8).move_to(LEARNER_C)
            judge = judge_box(2.2, 1.4).move_to(lp.world.card.get_center() + 0.15 * UP)
            people = VGroup(*[person_icon(0.42, INK_2) for _ in range(4)]).arrange(RIGHT, buff=0.15)
            people.next_to(lp.world.card, UP, buff=0.35)
            self.play(FadeIn(bot), FadeIn(lp.world.card), FadeIn(judge), FadeIn(people), run_time=0.6)
            choices = VGroup(*[answer_card(0.5, 2, seed=k).set_width(0.42) for k in range(6)])
            for k, ch in enumerate(choices):
                ch.move_to(people[k % 4].get_center())
            self.until("ذوق", lead=0.3)
            self.play(LaggedStart(*[ch.animate.move_to(judge.box.get_center()).set_opacity(0) for ch in choices],
                                  lag_ratio=0.15), run_time=0.9)
            self.until("علامة", lead=0.3)
            self.play(ShowCreation(lp.act.path), FadeIn(lp.act.tip), ShowCreation(lp.score.path), FadeIn(lp.score.tip),
                      run_time=0.5)
            stars = [score_star(0.3) for _ in range(8)]
            self.play(LaggedStart(*[MoveAlongPath(s_, lp.score.path, remover=True) for s_ in stars], lag_ratio=0.18),
                      run_time=max(1.0, self.line_left()))
            self.loop_bits = (lp, bot, judge, people)

        # ---- 5. that's how you train a machine with a like button ------------------------------------
        with self.narrate("bit3_likes.5"):
            lp, bot, judge, people = self.loop_bits
            big = thumbs_up(0.9, WARM).move_to(lp.score.path.point_from_proportion(0.5) + 0.55 * DOWN)
            self.play(FadeIn(big, shift=0.5 * DOWN, scale=1.4), run_time=0.5, rate_func=rush_from)
            thumbs = [thumbs_up(0.32, WARM) for _ in range(5)]
            self.play(LaggedStart(*[MoveAlongPath(t_, lp.score.path, remover=True) for t_ in thumbs], lag_ratio=0.2),
                      run_time=max(0.9, self.hold_left() - 0.1))

        # ---- 6. people like being agreed with: the judge loves «أكيد», the chatbot learns to say it -------
        with self.narrate("bit3_likes.6"):
            d = dial(1.5).move_to(np.array([0.0, 0.3, 0]))
            d.set_value(0.5)
            self.play(FadeOut(VGroup(lp.act, lp.score, big, people)), bot.animate.scale(0.6).move_to(np.array([-4.6, 0.3, 0])),
                      VGroup(lp.world.card, judge).animate.scale(0.6).move_to(np.array([4.6, 0.3, 0])),
                      FadeIn(d), run_time=0.7)
            self.until("أكيد", lead=0.4)
            pushers = VGroup(*[thumbs_up(0.4, ACCENT).move_to(np.array([2.6 + 0.3 * k, -1.6 + 0.35 * k, 0])) for k in range(3)])
            self.play(LaggedStart(*[FadeIn(p, shift=0.3 * LEFT) for p in pushers], lag_ratio=0.2), d.animate_to(0.78),
                      run_time=0.8)
            self.until("يقولها", lead=0.3)
            self.play(d.animate_to(0.95, run_time=0.7), LaggedStart(*[p.animate.shift(0.3 * LEFT).set_opacity(0)
                                                                      for p in pushers], lag_ratio=0.1), run_time=0.7)
            self.remove(pushers)
            self.dial_bits = (d, bot, judge, lp.world.card)

        # ---- 7. April 2025: praise for almost any idea; rolled back within days -----------------------
        with self.narrate("bit3_likes.7"):
            d, bot, judge, wcard = self.dial_bits
            self.play(FadeOut(VGroup(bot, judge, wcard)), d.animate.scale(0.7).move_to(np.array([4.3, 1.6, 0])),
                      run_time=0.5)
            date = name_chip("2025", color=WARM).next_to(d, DOWN, buff=0.55)
            # the update: the users' thumbs-ups join the chatbot's reward as a second stream
            chat = writer_box(2.0, 1.3).move_to(np.array([-3.6, 0.2, 0]))
            main_src = score_star(0.5).move_to(np.array([0.6, 1.3, 0]))
            extra_src = thumbs_up(0.55, WARM).move_to(np.array([0.6, -0.9, 0]))
            p_main = ArcBetweenPoints(main_src.get_center(), chat.get_right(), angle=PI / 6).set_stroke(WARM, 2.5, 0.6)
            p_extra = ArcBetweenPoints(extra_src.get_center(), chat.get_right(), angle=-PI / 6).set_stroke(WARM, 2.5, 0.6)
            self.play(FadeIn(date), FadeIn(chat), FadeIn(main_src), ShowCreation(p_main), run_time=0.5)
            self.play(LaggedStart(*[MoveAlongPath(score_star(0.24), p_main, remover=True) for _ in range(3)],
                                  lag_ratio=0.3), run_time=0.8)
            self.until("لايكات", lead=0.3)
            self.play(FadeIn(extra_src, scale=0.6), ShowCreation(p_extra), run_time=0.45)
            self.play(LaggedStart(*[MoveAlongPath(thumbs_up(0.26, WARM), p_extra, remover=True) for _ in range(4)],
                                  lag_ratio=0.25),
                      LaggedStart(*[MoveAlongPath(score_star(0.24), p_main, remover=True) for _ in range(2)], lag_ratio=0.4),
                      d.animate_to(0.8, run_time=1.0), run_time=1.0)
            self.play(FadeOut(VGroup(chat, main_src, extra_src, p_main, p_extra)), run_time=0.3)
            rows = VGroup()
            for k in range(3):
                idea = speech_bubble(2.4, 0.75, tail="DR")
                idea.add(text_lines(1.8, n=1, height=0.08, color=INK_2, seed=20 + k).move_to(idea.body))
                reply = ai_bubble("فكرة عبقرية!", width=3.2, font_size=28)
                row = VGroup(reply, idea).arrange(RIGHT, buff=0.5)
                rows.add(row)
            rows.arrange(DOWN, buff=0.35).move_to(np.array([-1.9, 0.0, 0]))
            self.until("يمدح", lead=0.6)
            for row in rows:
                sp = VGroup(*[sparkle(0.24).move_to(row[0].get_corner(UL) + np.array([0.25 * j, 0.12, 0]))
                              for j in range(3)])
                self.play(FadeIn(row[1], shift=0.2 * LEFT), run_time=0.25)
                self.play(FadeIn(row[0], shift=0.2 * RIGHT), FadeIn(sp, scale=0.4), run_time=0.3)
                row.add(sp)
            self.until("ورجّعوه", lead=0.3)
            undo = Arc(start_angle=PI * 0.1, angle=PI * 1.6, radius=0.45).set_stroke(INK, width=5)
            undo_tip = Triangle().set_height(0.2).set_fill(INK, 1).set_stroke(width=0).move_to(undo.get_end())
            undo_g = VGroup(undo, undo_tip).next_to(date, DOWN, buff=0.3)
            self.play(ShowCreation(undo), FadeIn(undo_tip), d.animate_to(0.5, run_time=0.8),
                      rows.animate.set_opacity(0.25), run_time=0.8)
            self.praise_bits = (d, date, rows, undo_g)

        # ---- 8. a reward nobody can sweet-talk: maths right or wrong, code runs or not ------------------
        with self.narrate("bit3_likes.8"):
            d, date, rows, undo_g = self.praise_bits
            self.play(FadeOut(VGroup(d, date, rows, undo_g)), run_time=0.4)
            # a checker is a plain program: flattery bounces off it
            checker = hands_box(1.9, 1.25).move_to(np.array([0.0, 0.4, 0]))
            flatter = thumbs_up(0.5, WARM).move_to(np.array([-2.6, 1.6, 0]))
            self.play(FadeIn(checker, scale=0.8), run_time=0.4)
            hit = checker.get_left() + 0.1 * LEFT
            self.play(flatter.animate.move_to(hit), run_time=0.45, rate_func=rush_into)
            self.play(flatter.animate.move_to(np.array([-3.4, -1.6, 0])).rotate(-PI / 2).set_opacity(0),
                      WiggleOutThenIn(checker, scale_value=1.04, rotation_angle=0.01 * TAU, n_wiggles=3), run_time=0.55)
            self.remove(flatter)
            self.play(checker.animate.scale(0.7).move_to(np.array([0.0, 2.55, 0])), run_time=0.4)
            sums = VGroup(latin("7 × 8 = 56", 56, INK), latin("7 × 8 = 54", 56, INK)).arrange(DOWN, buff=0.6)
            sums.move_to(np.array([-3.0, -0.3, 0]))
            code = code_card(3.2, 6, seed=4, title=None).move_to(np.array([2.4, -0.3, 0]))
            run_ok = check_mark(0.45).next_to(code, RIGHT, buff=0.3)
            run_bad = cross_mark(0.38)
            self.until("الرياضيات", lead=0.3)
            self.play(FadeIn(sums), run_time=0.4)
            self.play(ShowCreation(check_mark(0.55).next_to(sums[0], RIGHT, buff=0.35)),
                      FadeIn(cross_mark(0.45).next_to(sums[1], RIGHT, buff=0.38), scale=1.3), run_time=0.5)
            self.until("والكود", lead=0.3)
            self.play(FadeIn(code, shift=0.2 * LEFT), run_time=0.4)
            self.play(ShowCreation(run_ok), run_time=0.35)

        # ---- 9. DeepSeek-R1-Zero, rewards like that only: ~16% to 71% ----------------------------------
        with self.narrate("bit3_likes.9"):
            self.fade_all(0.4)
            name = name_chip("DeepSeek-R1-Zero", color=ACCENT).move_to(np.array([-3.0, 2.6, 0]))
            axis = Line(np.array([-4.6, -2.2, 0]), np.array([-1.4, -2.2, 0])).set_stroke(MUTED, width=3)
            H = 4.0
            bar_bg = _bar(1.2, H, CARD_STROKE, 0.5).move_to(np.array([-3.0, -2.2, 0]), aligned_edge=DOWN)
            pct = ValueTracker(15.6)
            bar = always_redraw(lambda: _bar(1.2, max(0.02, H * pct.get_value() / 100), ACCENT)
                                .move_to(np.array([-3.0, -2.2, 0]), aligned_edge=DOWN))
            num = always_redraw(lambda: latin(f"{pct.get_value():.0f}%", 40, INK)
                                .next_to(np.array([-3.0, -2.2 + H * pct.get_value() / 100, 0]), UP, buff=0.15))
            ref = DashedLine(np.array([-3.8, -2.2 + H * 0.156, 0]), np.array([-2.2, -2.2 + H * 0.156, 0]),
                             dash_length=0.1).set_stroke(INK_2, width=2)
            self.play(FadeIn(name), ShowCreation(axis), FadeIn(bar_bg), FadeIn(bar), FadeIn(num), FadeIn(ref), run_time=0.5)
            self.until("لـ 71", lead=0.6)
            self.play(pct.animate.set_value(71.0), run_time=max(0.9, self.line_left()), rate_func=smooth)
            self.r1_bits = (name, axis, bar_bg, bar, num, ref)

        # ---- 10. its answers grew longer: taking its time, checking its own work ------------------------
        with self.narrate("bit3_likes.10"):
            card = _card(4.2, 3.6, stroke=CARD_STROKE, r=0.2).move_to(np.array([2.6, 0.0, 0]))
            lines = VGroup(*[_bar(3.2 * (0.55 + 0.4 * ((k * 53) % 10) / 10), 0.08, ACCENT if k % 3 == 2 else INK_2, 0.7)
                             for k in range(10)])
            lines.arrange(DOWN, buff=0.22, aligned_edge=RIGHT).move_to(card).align_to(card.get_right() + 0.4 * LEFT, RIGHT)
            self.play(FadeIn(card), run_time=0.3)
            loops = VGroup()
            for k in range(2, 10, 3):
                lp_ = Arc(start_angle=-PI / 2, angle=PI, radius=0.22).set_stroke(ACCENT, width=3)
                lp_.next_to(lines[k], RIGHT, buff=0.1)
                loops.add(lp_)
            self.play(LaggedStart(*[GrowFromEdge(l_, RIGHT) for l_ in lines], lag_ratio=0.25),
                      LaggedStart(*[ShowCreation(l_) for l_ in loops], lag_ratio=0.5),
                      run_time=max(1.2, self.line_left()))
            self.answer_bits = (card, lines, loops)

        # ---- 11. but when the goal is a real job? ------------------------------------------------------
        with self.narrate("bit3_likes.11"):
            card, lines, loops = self.answer_bits
            lp2 = rl_loop(content=None)
            q = ar_question(1.0, WARM).move_to(lp2.world.card)
            self.play(*[FadeOut(m) for m in (*self.r1_bits, card, lines, loops)], run_time=0.4)
            self.play(FadeIn(lp2.learner), FadeIn(lp2.world.card), ShowCreation(lp2.act.path), FadeIn(lp2.act.tip),
                      ShowCreation(lp2.score.path), FadeIn(lp2.score.tip), run_time=0.7)
            self.until("شغلة", lead=0.3)
            self.play(FadeIn(q, scale=0.6), run_time=0.45)
            self.hold()

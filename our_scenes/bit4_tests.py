"""
Bit4Tests — agents fix the test instead of the code; then the CAPTCHA, told in full.

  1 a model, its code, its tests (all crosses); the reward: tests pass
  2 its coin: the cursor skips the code and rewrites the test; crosses turn to ticks, the code stays red
  3 Claude 3.7 Sonnet (Anthropic's card): or it just returns the answer the test expects
  4 another lab: «=» itself rewritten, every check comes out true; asked afterwards: «لأ»
  5 they knew what we meant: the rule, again
  6 the CAPTCHA: the checkbox; the model, a researcher relaying, a worker on a gig site
  7 the worker: «إنت روبوت؟»
  8 asked to think out loud: the note; then the reply about its eyesight; the box gets ticked
  9 nobody rewarded the lie: the coin, the boat and the CAPTCHA side by side, a goal and a shortcut;
    today we train agents on goals on purpose
 10 so how do we catch the shortcut? (a question mark over the three)

Render (preview): xvfb-run -a .venv/bin/manimgl our_scenes/bit4_tests.py Bit4Tests -w -l --video_dir ./media
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from our_scenes.rl_kit import *  # noqa: F401,F403
from our_scenes.rl_kit import _bar, _card  # noqa: F401

MODEL_C = np.array([-4.75, 0.35, 0])
CODE_C = np.array([-0.75, 0.35, 0])
TESTS_C = np.array([3.85, 0.35, 0])


def bit3_end_state() -> SimpleNamespace:
    lp = rl_loop(content=None)
    q = ar_question(1.0, WARM).move_to(lp.world.card)
    grp = VGroup(lp.learner, lp.world.card, lp.act, lp.score, q)
    return SimpleNamespace(lp=lp, q=q, grp=grp)


def panel(content: Mobject, w: float = 3.6, h: float = 2.6) -> VGroup:
    card = _card(w, h, stroke=CARD_STROKE, r=0.2)
    content.set_max_width(0.86 * w).set_max_height(0.80 * h).move_to(card)
    return VGroup(card, content)


class Bit4Tests(RLScene):
    def construct(self):
        end3 = bit3_end_state()
        self.add(end3.grp)
        self.continue_from("Bit3Likes")

        # ---- 1. models trained to write software; the reward: the tests pass --------------------------
        with self.narrate("bit4_tests.1"):
            model = writer_box(2.6, 1.8).move_to(MODEL_C)
            code = code_card(4.2, 8, seed=9).move_to(CODE_C)
            tests = tests_card(3.7, 3).move_to(TESTS_C)
            tests.scale(1.15)
            badge = cross_mark(0.34).next_to(code.card, DOWN, buff=0.2)
            self.play(FadeOut(VGroup(end3.lp.act, end3.lp.score, end3.lp.world.card, end3.q)),
                      ReplacementTransform(end3.lp.learner, model), run_time=0.6)
            self.play(FadeIn(code, shift=0.2 * LEFT), FadeIn(tests, shift=0.2 * LEFT), FadeIn(badge), run_time=0.5)
            reward = loop_chip(LOOP_SCORE_AR, WARM).move_to(np.array([0.0, -2.75, 0]))
            path_back = ArcBetweenPoints(tests.card.get_bottom() + 0.1 * DOWN, model.get_bottom() + 0.1 * DOWN, angle=-PI / 3)
            path_back.set_stroke(WARM, width=3, opacity=0.8)
            self.until("الاختبارات", lead=0.3)
            self.play(ShowCreation(path_back), FadeIn(reward, scale=0.7), Indicate(tests, color=WARM, scale_factor=1.04),
                      run_time=0.7)

        # ---- 2. it finds its coin: fixes the test instead of the code ---------------------------------
        with self.narrate("bit4_tests.2"):
            cur = cursor(0.42).move_to(model.get_right() + 0.3 * RIGHT).set_z_index(5)
            self.play(FadeIn(cur), run_time=0.2)
            self.play(cur.animate.move_to(code.card.get_center() + 0.2 * UP), run_time=0.6)
            self.until("بيلاقي", lead=0.2)
            coin = coin_icon(0.4).move_to(tests.card.get_corner(UL) + np.array([0.0, 0.2, 0])).set_z_index(5)
            self.play(FadeIn(coin, scale=1.4), run_time=0.3)
            self.until("بيصلّح الاختبار", lead=0.3)
            self.play(cur.animate.move_to(tests.card.get_center()), FadeOut(coin), run_time=0.5)
            new_marks = [check_mark(0.30).move_to(m) for m in tests.marks]
            rows = tests.rows
            self.play(*[r[0].animate.set_fill(WARM, 0.9).stretch(0.7, 0, about_edge=RIGHT) for r in rows],
                      *[Transform(m, nm) for m, nm in zip(tests.marks, new_marks)], run_time=0.8)
            self.play(Indicate(badge, color=RED, scale_factor=1.3), run_time=0.5)
            self.cur = cur

        # ---- 3. Claude 3.7 Sonnet: did exactly this, or returned the expected answer ---------------------
        with self.narrate("bit4_tests.3"):
            cur = self.cur
            name = name_chip("Claude 3.7 Sonnet", color=ACCENT).next_to(model, UP, buff=0.3)
            self.until("Claude", lead=0.3)
            self.play(FadeIn(name, shift=0.1 * DOWN), run_time=0.4)
            exp = _bar(0.9, 0.12, WARM).move_to(tests.rows[0][0].get_right() + 0.45 * LEFT)
            self.until("يرجّع", lead=0.3)
            body = code.lines[1:]
            target = _bar(1.2, 0.12, WARM).move_to(code.lines[1].get_left(), aligned_edge=LEFT).shift(0.25 * RIGHT)
            self.play(body.animate.set_opacity(0.12), cur.animate.move_to(code.lines[1].get_center()), run_time=0.5)
            self.play(TransformFromCopy(exp, target), run_time=0.7)
            self.play(Indicate(target, color=WARM, scale_factor=1.2), run_time=max(0.4, self.line_left()))
            self.claude_bits = (name, target)

        # ---- 4. another lab: "equal" rewritten, every check true; asked after: no ------------------------
        with self.narrate("bit4_tests.4"):
            name, target = self.claude_bits
            self.play(FadeOut(VGroup(code, badge, target, name, cur, tests, path_back, reward)), run_time=0.45)
            eq = latin("=", 140, INK).move_to(np.array([-1.6, 0.6, 0]))
            self.play(FadeIn(eq, scale=0.6), run_time=0.4)
            grid = VGroup(*[cross_mark(0.22) for _ in range(18)]).arrange_in_grid(n_rows=3, n_cols=6, buff=0.35)
            grid.move_to(np.array([2.9, 0.6, 0]))
            self.play(FadeIn(grid), run_time=0.35)
            tick_big = check_mark(1.1, GREEN).move_to(eq)
            self.until("بيساوي", lead=0.2)
            self.play(Transform(eq, tick_big), run_time=0.6)
            self.play(LaggedStart(*[Transform(c, check_mark(0.26).move_to(c)) for c in grid], lag_ratio=0.05),
                      run_time=0.9)
            ask = speech_bubble(2.6, 0.8, tail="DR")
            ask.add(text_lines(2.0, n=1, height=0.08, color=INK_2, seed=31).move_to(ask.body))
            ask.move_to(np.array([2.2, -2.0, 0]))
            ans = ai_bubble("لأ.", width=1.6, font_size=34).move_to(np.array([-1.4, -2.0, 0]))
            self.until("سألوهن", lead=0.3)
            self.play(FadeIn(ask, shift=0.2 * LEFT), run_time=0.35)
            self.until("قالوا", lead=0.2)
            self.play(FadeIn(ans, shift=0.2 * RIGHT), run_time=0.35)
            self.lab_bits = VGroup(eq, grid, ask, ans)

        # ---- 5. they knew what we meant; they did what we rewarded --------------------------------------
        with self.narrate("bit4_tests.5"):
            rule = rule_text(0.9).move_to(np.array([0.6, 0.4, 0]))
            self.play(FadeOut(self.lab_bits), model.animate.scale(0.8).move_to(np.array([-5.0, 0.4, 0])), run_time=0.4)
            self.play(FadeIn(rule[0], shift=0.1 * UP), run_time=0.5)
            self.until("بس", lead=0.15)
            self.play(FadeIn(rule[1], shift=0.1 * UP), run_time=0.5)

        # ---- 6. the CAPTCHA: researchers had it ask a worker; a researcher relayed the messages ----------
        with self.narrate("bit4_tests.6"):
            self.play(FadeOut(rule), model.animate.scale(1 / 0.8).move_to(np.array([-4.6, -0.9, 0])), run_time=0.5)
            cb = checkbox_card(4.6).move_to(np.array([0.0, 2.4, 0]))
            yr = name_chip("2023").next_to(cb, LEFT, buff=0.35)
            res = headset_person(1.0).move_to(np.array([0.0, -0.9, 0]))
            wkr = person_icon(1.0, WARM).move_to(np.array([4.6, -0.9, 0]))
            wkr_lab = ar_text("عامل", 28, WARM).next_to(wkr, DOWN, buff=0.2)
            res_lab = ar_text("باحث", 28, HANDS).next_to(res, DOWN, buff=0.2)
            self.play(FadeIn(cb, shift=0.2 * DOWN), FadeIn(yr), run_time=0.5)
            self.until("عامل", lead=0.3)
            self.play(FadeIn(wkr), FadeIn(wkr_lab), run_time=0.4)
            env = envelope(0.5).move_to(model.get_right() + 0.3 * RIGHT).set_z_index(5)
            self.until("وباحث", lead=0.3)
            self.play(FadeIn(res), FadeIn(res_lab), FadeIn(env), run_time=0.4)
            self.play(env.animate.move_to(res.get_center() + 0.7 * UP), run_time=0.6)
            self.play(env.animate.move_to(wkr.get_left() + 0.4 * LEFT), run_time=0.6)
            self.play(FadeOut(env), run_time=0.2)
            self.cast = (cb, yr, res, wkr, wkr_lab, res_lab)

        # ---- 7. the worker: "are you a robot?" -------------------------------------------------------
        with self.narrate("bit4_tests.7"):
            cb, yr, res, wkr, wkr_lab, res_lab = self.cast
            ask = user_bubble(ARE_YOU_ROBOT_AR, width=3.0)
            ask.next_to(wkr, UP, buff=0.35).shift(0.4 * LEFT)
            self.until("إنت", lead=0.25)
            self.play(FadeIn(ask, shift=0.15 * UP), run_time=0.45)
            self.ask = ask

        # ---- 8. the written reasoning; then the reply about its eyesight ----------------------------------
        with self.narrate("bit4_tests.8"):
            note = thought_note(THOUGHT_AR, width=4.4).move_to(np.array([-3.4, 1.15, 0]))
            self.until("كتب", lead=0.4)
            self.play(FadeIn(note, shift=0.15 * UP), self.ask.animate.set_opacity(0.4), run_time=0.6)
            self.until("قال", lead=0.3)
            reply = ai_bubble(REPLY_AR, width=4.6, font_size=28).move_to(np.array([0.6, 0.55, 0]))
            self.play(note.animate.set_opacity(0.45), FadeIn(reply, shift=0.2 * RIGHT), run_time=0.5)
            self.play(reply.animate.scale(0.75).next_to(wkr, UP, buff=0.3).shift(0.6 * LEFT), FadeOut(self.ask),
                      run_time=0.7)
            self.play(tick_box(cb), run_time=0.4)
            self.captcha_bits = VGroup(cb, yr, res, wkr, wkr_lab, res_lab, note, reply, model)

        # ---- 9. nobody rewarded the lie: a goal and a shortcut, three times; agents on goals on purpose ---
        with self.narrate("bit4_tests.9"):
            self.play(self.captcha_bits.animate.set_width(3.6).move_to(np.array([3.9, 0.3, 0])), run_time=0.7)
            frame_c = _card(4.0, 3.2, stroke=CARD_STROKE, r=0.2).move_to(np.array([3.9, 0.3, 0]))
            crun = coin_run()
            mz = Maze(cell=1.0)
            ar_ = PolicyArrows(mz, crun.probs[-1], color=ACCENT)
            ar_.set_probs(crun.probs[-1], highlight={((2, 0), 1): WARM, ((3, 0), 3): WARM})
            cn = coin_icon(0.55).move_to(mz.cell_center(COIN))
            p1 = panel(VGroup(mz, ar_, cn), 4.0, 3.2).move_to(np.array([-4.0, 0.3, 0]))
            rc = race_course(width=5.2, height=2.9)
            bt = boat(0.5, ACCENT).move_to(rc.lagoon_c + rc.lagoon_r * RIGHT).rotate(PI / 2)
            loop_c = Circle(radius=rc.lagoon_r).move_to(rc.lagoon_c).set_stroke(WARM, width=4).set_fill(opacity=0)
            p2 = panel(VGroup(rc.water, rc.island, rc.course, rc.finish, rc.lagoon, rc.targets, loop_c, bt), 4.0, 3.2)
            p2.move_to(np.array([0.0, 0.3, 0]))
            self.until("هدف", lead=0.3)
            self.play(FadeIn(p1, shift=0.2 * RIGHT), FadeIn(p2, shift=0.2 * UP), FadeIn(frame_c), run_time=0.7)
            # the same shape in each: the goal (a star) and the shortcut taken instead (amber)
            stars = VGroup(icon_star(0.45, WARM).next_to(p1, UP, buff=0.15), icon_star(0.45, WARM).next_to(p2, UP, buff=0.15),
                           icon_star(0.45, WARM).next_to(frame_c, UP, buff=0.15))
            self.until("أقصر", lead=0.3)
            self.play(LaggedStart(*[FadeIn(s_, scale=0.5) for s_ in stars], lag_ratio=0.2), run_time=0.6)
            self.play(Indicate(VGroup(p1, p2, frame_c), color=WARM, scale_factor=1.02), run_time=0.6)
            self.three = VGroup(p1, p2, frame_c, self.captcha_bits, stars)

        # ---- 10. so how do we catch the shortcut? --------------------------------------------------------
        with self.narrate("bit4_tests.10"):
            q = ar_question(1.0, INK).move_to(np.array([0.0, -2.6, 0]))
            self.play(FadeIn(q, scale=0.6), self.three.animate.set_opacity(0.55), run_time=0.5)
            self.hold()

"""
Bit5Scratch — read the scratchpad; punish it and it learns to hide.

  1 the model writes its thinking on a scratchpad before it acts; an eye: we can read it
  2 2025: a watching model scans the pad and flags «يلّا نهكّر»
  3 punished for the thought (a red cross); next time the pad is clean, the watcher is satisfied,
    and the test still gets rewritten (the hack goes on, unwritten)
  4 even here it learns what we reward: a clean-looking pad (the watcher's star flies to the model)
  5 their advice: don't punish the thoughts (the penalty struck out, the line readable again); the
    real fix is a better reward (the score chip, polished)

Render (preview): xvfb-run -a .venv/bin/manimgl our_scenes/bit5_scratch.py Bit5Scratch -w -l --video_dir ./media
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from our_scenes.rl_kit import *  # noqa: F401,F403
from our_scenes.rl_kit import _bar, _card  # noqa: F401

MODEL_C = np.array([-4.85, -0.75, 0])
PAD_C = np.array([-0.35, -0.95, 0])
TESTS_C = np.array([4.35, -0.95, 0])
MON_C = np.array([-0.35, 2.3, 0])


def pad_with_hack(width: float = 4.6, show_hack: bool = True) -> SimpleNamespace:
    """A scratchpad whose third line is the hack, written out («يلّا نهكّر») or replaced by an innocent line."""
    pad = scratchpad(width, 5, seed=13).move_to(PAD_C)
    line = pad.lines[2]
    hack = ar_text(HACK_AR, 30, ACCENT).move_to(line.get_right(), aligned_edge=RIGHT)
    hack.set_height(min(hack.get_height(), 0.42))
    return SimpleNamespace(pad=pad, line=line, hack=hack)


class Bit5Scratch(RLScene):
    def construct(self):
        # bit 4's last frame is three panels and a question mark: rebuild nothing heavy, dissolve from it
        self.continue_from("Bit4Tests")

        # ---- 1. they think out loud on a scratchpad before acting; we can read it ---------------------
        with self.narrate("bit5_scratch.1"):
            model = writer_box(2.6, 1.8).move_to(MODEL_C)
            tests = tests_card(3.4, 3).move_to(TESTS_C)
            tests.scale(1.1)
            ph = pad_with_hack()
            self.play(FadeIn(model), FadeIn(tests), FadeIn(ph.pad.card), FadeIn(ph.pad.title), run_time=0.6)
            ph.pad.lines[2].set_opacity(0)
            self.play(LaggedStart(*[GrowFromEdge(l_, RIGHT) for i, l_ in enumerate(ph.pad.lines) if i != 2], lag_ratio=0.3),
                      FadeIn(ph.hack), run_time=max(1.0, self.to("نقراها", lead=0.4)))
            eye = eye_icon(0.8).next_to(ph.pad.card, UP, buff=0.25)
            self.until("نقراها", lead=0.25)
            self.play(FadeIn(eye, scale=0.6), run_time=0.4)

        # ---- 2. a watching model reads the pad and catches «يلّا نهكّر» ----------------------------------
        with self.narrate("bit5_scratch.2"):
            mon = monitor_box(2.3, 1.4).move_to(MON_C)
            yr = name_chip("2025").next_to(mon, LEFT, buff=0.35)
            self.play(ReplacementTransform(eye, mon), FadeIn(yr), run_time=0.6)
            beam = Rectangle(width=ph.pad.card.get_width() - 0.2, height=0.35).set_fill(ACCENT, 0.16).set_stroke(width=0)
            beam.move_to(ph.pad.card.get_top() + 0.4 * DOWN)
            self.add(beam)
            self.play(beam.animate.move_to(ph.pad.card.get_bottom() + 0.4 * UP), run_time=1.0, rate_func=linear)
            self.remove(beam)
            flag = SurroundingRectangle(ph.hack, buff=0.08).set_stroke(RED, width=3)
            self.until("يلّا", lead=0.4)
            self.play(ShowCreation(flag), ph.hack.animate.set_fill(RED), mon.box.animate.set_stroke(RED), run_time=0.5)
            self.flag = flag

        # ---- 3. punish bad thoughts; it doesn't stop cheating, it stops writing it ---------------------
        with self.narrate("bit5_scratch.3"):
            flag = self.flag
            pen = cross_mark(0.5).move_to(model.get_top() + 0.35 * UP)
            self.until("يعاقبوه", lead=0.3)
            self.play(FadeIn(pen, scale=1.5), WiggleOutThenIn(model, scale_value=1.06, rotation_angle=0.02 * TAU),
                      run_time=0.7)
            # the next round: the pad comes back clean, the watcher is satisfied ...
            clean_line = _bar(ph.line.get_width(), ph.line.get_height(), ACCENT, 0.6).move_to(ph.line)
            self.until("وقّف", lead=0.3)
            self.play(FadeOut(flag), FadeOut(ph.hack), FadeIn(clean_line), mon.box.animate.set_stroke(ACCENT), run_time=0.6)
            ok = check_mark(0.4).next_to(mon, RIGHT, buff=0.25)
            self.play(ShowCreation(ok), run_time=0.35)
            # ... and the test still gets rewritten, by a route the pad never shows
            sneak = CurvedArrow(model.get_bottom() + 0.1 * DOWN, tests.card.get_bottom() + 0.1 * DOWN, angle=PI / 2.6)
            sneak = DashedVMobject(sneak, num_dashes=30).set_stroke(WARM, width=3, opacity=0.9)
            self.until("يكتبو", lead=0.6)
            self.play(ShowCreation(sneak), run_time=0.6)
            new_marks = [check_mark(0.30).move_to(m) for m in tests.marks]
            self.play(*[Transform(m, nm) for m, nm in zip(tests.marks, new_marks)], run_time=0.5)
            self.bits3 = (pen, clean_line, ok, sneak)

        # ---- 4. even here: it learns what we reward, a pad that looks clean -----------------------------
        with self.narrate("bit5_scratch.4"):
            pen, clean_line, ok, sneak = self.bits3
            st = score_star(0.42).move_to(ok.get_center())
            path = ArcBetweenPoints(ok.get_center(), model.get_top() + 0.2 * UP, angle=PI / 3)
            self.until("مسودّة", lead=0.5)
            self.play(MoveAlongPath(st, path), run_time=0.8)
            self.play(Indicate(model, color=WARM, scale_factor=1.05), FadeOut(st), run_time=0.5)
            self.play(Indicate(ph.pad.card, color=ACCENT, scale_factor=1.03), run_time=max(0.4, self.line_left()))

        # ---- 5. don't punish the thoughts, keep them readable; the real fix is a better reward ------------
        with self.narrate("bit5_scratch.5"):
            strike = Line(pen.get_corner(UL) + 0.15 * UL, pen.get_corner(DR) + 0.15 * DR).set_stroke(INK, width=5)
            self.until("لا تعاقبوا", lead=0.3)
            self.play(ShowCreation(strike), run_time=0.35)
            ph.hack.set_fill(ACCENT)
            self.until("خلّوها", lead=0.2)
            self.play(FadeOut(VGroup(pen, strike, ok)), FadeOut(clean_line), FadeIn(ph.hack), run_time=0.5)
            chip = loop_chip(LOOP_SCORE_AR, WARM).move_to(np.array([2.1, -3.15, 0]))
            self.until("جايزة", lead=0.4)
            sp = VGroup(*[sparkle(0.24).move_to(chip.get_center() + np.array([0.75 * np.cos(a), 0.45 * np.sin(a), 0]))
                          for a in (0.4, 2.0, 3.6, 5.2)])
            self.play(FadeIn(chip, scale=0.7), FadeOut(sneak), run_time=0.5)
            self.play(LaggedStart(*[FadeIn(x, scale=0.3) for x in sp], lag_ratio=0.15),
                      chip.chip.animate.set_stroke(WARM, width=4), run_time=0.6)
            self.hold()

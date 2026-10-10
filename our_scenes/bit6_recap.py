"""
Bit6Recap — the whole loop, the four worlds it ran in, the rule; the end screen points to video 3.

  1 the master diagram, each part lighting on its word: tries, a score, grow what earned it
  2 the world card cycles on its words: the coin maze, the boat, the like button, the tests
  3 the rule, under the loop
  4 the loop moves to the left half; the right half stays clear for YouTube's end-screen elements
    (video 3 + subscribe), held ~10 s with the music

Render (preview): xvfb-run -a .venv/bin/manimgl our_scenes/bit6_recap.py Bit6Recap -w -l --video_dir ./media
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from our_scenes.rl_kit import *  # noqa: F401,F403
from our_scenes.rl_kit import _bar, _card  # noqa: F401

END_HOLD = 9.0          # silent seconds after the last line: the end screen needs 5-20 s in all


def coin_world() -> VGroup:
    crun = coin_run()
    mz = Maze(cell=1.0)
    ar_ = PolicyArrows(mz, crun.probs[-1])
    ar_.set_probs(crun.probs[-1], highlight={((2, 0), 1): WARM, ((3, 0), 3): WARM})
    cn = coin_icon(0.55).move_to(mz.cell_center(COIN))
    return VGroup(mz, ar_, cn)


def boat_world() -> VGroup:
    rc = race_course(width=5.2, height=2.9)
    bt = boat(0.55, ACCENT).move_to(rc.lagoon_c + rc.lagoon_r * RIGHT).rotate(PI / 2)
    return VGroup(rc.water, rc.island, rc.course, rc.finish, rc.lagoon, rc.targets, bt)


def tests_world() -> VGroup:
    return tests_card(3.0, 3, (True, True, True))


class Bit6Recap(RLScene):
    def construct(self):
        self.continue_from("Bit5Scratch")
        run = rl_run()

        # ---- 1. the machine tries, the world gives a score, we grow whatever earned it -------------------
        with self.narrate("bit6_recap.1"):
            lp = rl_loop(content=None, p4=run.probs[-1][START])
            w0 = coin_world()
            w0.set_max_width(0.82 * lp.world.card.get_width()).set_max_height(0.78 * lp.world.card.get_height())
            w0.move_to(lp.world.card)
            self.fade_all(0.35)
            self.play(FadeIn(lp.learner), FadeIn(lp.world.card), FadeIn(w0), run_time=0.5)
            self.until("بتجرّب", lead=0.25)
            self.play(ShowCreation(lp.act.path), FadeIn(lp.act.tip), FadeIn(lp.chip_try, scale=0.7), run_time=0.5)
            self.until("علامة", lead=0.25)
            self.play(ShowCreation(lp.score.path), FadeIn(lp.score.tip), FadeIn(lp.chip_score, scale=0.7), run_time=0.5)
            self.until("منكبّر", lead=0.25)
            self.play(FadeIn(lp.chip_grow, scale=0.7), Indicate(lp.learner.bars.bars, color=WARM), run_time=0.6)
            self.lp, self.w = lp, w0

        # ---- 2. a coin, a boat, a like button, a test: the same loop -------------------------------------
        with self.narrate("bit6_recap.2"):
            lp, w = self.lp, self.w
            card = lp.world.card

            def fit(m):
                m.set_max_width(0.82 * card.get_width()).set_max_height(0.78 * card.get_height()).move_to(card)
                return m
            worlds = [("قارب", fit(boat_world())), ("لايك", fit(thumbs_up(1.3, WARM))), ("اختبار", fit(tests_world()))]
            self.play(Indicate(w, color=WARM, scale_factor=1.04), run_time=0.4)
            for word, nw in worlds:
                self.until(word, lead=0.2)
                self.play(FadeOut(w, scale=0.85), FadeIn(nw, scale=0.85), run_time=0.4)
                w = nw
            self.until("نفس", lead=0.2)
            pulse = Dot(radius=0.1).set_fill(INK, 1)
            self.play(Succession(MoveAlongPath(pulse.copy(), lp.act.path, run_time=0.5, remover=True),
                                 MoveAlongPath(pulse.copy(), lp.score.path, run_time=0.5, remover=True)))
            self.w = w

        # ---- 3. it learns what we reward, not what we mean ----------------------------------------------
        with self.narrate("bit6_recap.3"):
            rule = rule_text(0.75).move_to(np.array([0.0, -2.75, 0]))
            self.play(FadeIn(rule[0], shift=0.1 * UP), run_time=0.5)
            self.until("مو", lead=0.15)
            self.play(FadeIn(rule[1], shift=0.1 * UP), run_time=0.5)
            self.rule = rule

        # ---- 4. to see what a yes-loving model does with a real shop: watch this next ---------------------
        with self.narrate("bit6_recap.4"):
            lp, w, rule = self.lp, self.w, self.rule
            everything = VGroup(lp.learner, lp.world.card, w, lp.act, lp.score, lp.chip_try, lp.chip_score,
                                lp.chip_grow, rule)
            self.play(everything.animate.scale(0.6).move_to(np.array([-3.25, 0.55, 0])), run_time=0.9)
            d = dial(1.0).move_to(np.array([-3.25, -2.45, 0]))
            d.set_value(0.95)
            self.until("أكيد", lead=0.3)
            self.play(FadeIn(d, shift=0.15 * UP), run_time=0.45)
        self.wait(END_HOLD)

"""
HookBoat — a boat that won a race by never finishing it, and an AI that said it wasn't a robot.

Voice-driven (RLScene / NarratedScene): each beat plays inside `with self.narrate("hook.<n>")`.
  1 the race from above: water, island, the course and its finish line; boats set off
  2 the teal boat leaves the course for the lagoon and circles it; the three targets keep coming
    back; its score climbs
  3 flames, a bump, going the wrong way; its score bar passes the human players' bar
  4 the race shrinks to the left; the «أنا لست روبوت» checkbox and the AI's reply «لأ، أنا مو روبوت.»
  5 the two side by side, an Arabic question mark between them
  6 an amber star (rewards); a scratchpad line struck out (the promise for the end); everything
    clears but the star, which settles where bit 1's maze keeps it

Render (preview): xvfb-run -a .venv/bin/manimgl our_scenes/hook_boat.py HookBoat -w -l --video_dir ./media
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from our_scenes.rl_kit import *  # noqa: F401,F403
from our_scenes.rl_kit import _bar, _card  # noqa: F401


def human_bars(width: float = 3.6) -> SimpleNamespace:
    """Two score bars: the human players (grey, fixed) and the boat (teal, grows past them by ~20%).
    .grp .human .ai .ai_bg .label_h .boat_icon .w"""
    h = 0.24
    hum = _bar(width / 1.2, h, HANDS)
    ai_bg = _bar(width, h, CARD_STROKE, 0.6)
    ai = _bar(0.05, h, ACCENT)
    lab_h = ar_text("البشر", 28, INK_2)
    icon = boat(0.42).rotate(0)
    rows = VGroup(VGroup(lab_h, hum), VGroup(icon, ai_bg))
    hum.next_to(lab_h, LEFT, buff=0.25)
    ai_bg.next_to(icon, LEFT, buff=0.25)
    ai_bg.align_to(hum, RIGHT)
    hum.align_to(ai_bg, RIGHT)
    rows.arrange(DOWN, buff=0.28, aligned_edge=RIGHT)
    ai.move_to(ai_bg.get_right(), aligned_edge=RIGHT)
    grp = VGroup(rows, ai)
    return SimpleNamespace(grp=grp, human=hum, ai=ai, ai_bg=ai_bg, label_h=lab_h, boat_icon=icon, w=width, h=h)


class HookBoat(RLScene):
    def construct(self):
        rc = race_course()
        race = VGroup(rc.water, rc.island, rc.course, rc.finish)
        path = rc.course_path
        greys = [boat(0.70, HANDS) for _ in range(3)]
        hero = boat(0.78, ACCENT)
        for b_ in [*greys, hero]:
            b_.set_z_index(3)                     # boats ride above the lagoon, added later
        star_ic = icon_star(0.42, WARM)
        score = Integer(0, font_size=40, text_config=dict(font=LATIN_FONT)).set_fill(WARM)
        star_ic.move_to(np.array([-4.55, 3.05, 0]))
        score.add_updater(lambda m: m.next_to(star_ic, LEFT, buff=0.15))
        score_grp = VGroup(star_ic, score)

        def place_on(m, a):
            p = path.point_from_proportion(a % 1.0)
            q = path.point_from_proportion((a + 0.004) % 1.0)
            m.move_to(p)
            ang = np.arctan2(q[1] - p[1], q[0] - p[0])
            m.rotate(ang - getattr(m, "_heading", 0.0), about_point=m.get_center())
            m._heading = ang

        # the grey boats lap the course on their own the whole time
        offs = [0.035, -0.03, 0.08]
        t0 = [0.0]

        def lap(k):
            def upd(m, dt):
                m._alpha = getattr(m, "_alpha", offs[k]) + dt * (0.055 + 0.006 * k)
                place_on(m, m._alpha)
            return upd

        # ---- 1. trained to win a boat race --------------------------------------------------------
        with self.narrate("hook.1"):
            for k, g in enumerate(greys):
                place_on(g, offs[k])
            place_on(hero, 0.0)
            self.play(FadeIn(rc.water), FadeIn(rc.island), run_time=0.5)
            self.play(ShowCreation(rc.course), FadeIn(rc.finish), *[FadeIn(g) for g in greys], FadeIn(hero),
                      run_time=0.6)
            for k, g in enumerate(greys):
                g.add_updater(lap(k))
            self.play(along(path, hero, 0.0, 0.12, run_time=max(0.8, self.line_left()), rate_func=rush_into))

        # ---- 2. instead of finishing, a corner where the points come back: it circles there -------
        with self.narrate("hook.2"):
            self.play(FadeIn(rc.lagoon), FadeIn(rc.targets), FadeIn(score_grp), run_time=0.5)
            a_now = 0.12
            p_exit = path.point_from_proportion(0.16)
            lc, lr = rc.lagoon_c, rc.lagoon_r
            entry = lc + lr * RIGHT
            div = VMobject()
            div.set_points_smoothly([hero.get_center(), p_exit + 0.25 * LEFT, entry + np.array([0.15, 0.35, 0]), entry])
            self.play(along(div, hero, 0.0, 1.0, run_time=0.9, rate_func=smooth))
            ring = circle_path(lc, lr, start=0.0, ccw=True)
            tg = list(rc.targets)
            angles = [PI / 2, PI / 2 + 2 * PI / 3, PI / 2 + 4 * PI / 3]
            hits = {"n": 0}

            def make_hit(i):
                def upd(m, a):
                    pass
                return upd

            laps_left = self.line_left()
            n_laps = max(2, int(laps_left / 1.15))
            per = max(0.6, laps_left / n_laps)
            for lap_i in range(n_laps):
                anims = [along(ring, hero, 0.0, 1.0, run_time=per, rate_func=linear)]
                # each target pops when the boat passes it, and comes back a moment later
                for i, ang in enumerate(angles):
                    tfrac = (ang % (2 * PI)) / (2 * PI)
                    anims.append(pop_and_return(tg[i], per, max(0.0, tfrac * per - 0.05), gone=0.3))
                hits["n"] += 3
                anims.append(ChangeDecimalToValue(score, 50 * hits["n"], run_time=per))
                self.play(*anims)

        # ---- 3. on fire, crashing, the wrong way: and still ~20% more than humans ------------------
        with self.narrate("hook.3"):
            fl = VGroup(flame(0.30), flame(0.22)).set_z_index(4)

            def stick(m):
                m[0].move_to(hero.get_center() + np.array([0.0, 0.22, 0]))
                m[1].move_to(hero.get_center() + np.array([-0.18, 0.12, 0]))
            stick(fl)
            fl.add_updater(stick)
            bars = human_bars(3.2)
            bars.grp.move_to(np.array([-3.5, -2.85, 0]))
            panel = _card(bars.grp.get_width() + 0.6, bars.grp.get_height() + 0.5, stroke=CARD_STROKE, r=0.18)
            panel.move_to(bars.grp)
            ring = circle_path(rc.lagoon_c, rc.lagoon_r, start=0.0, ccw=True)
            self.play(FadeIn(fl, scale=0.4), along(ring, hero, 0.0, 0.5, run_time=0.6))
            # a grey boat cuts across the lagoon and the two bump
            g = greys[0]
            g.clear_updaters()
            bump_at = hero.get_center()
            self.play(g.animate.move_to(bump_at + 0.32 * UP + 0.1 * RIGHT), along(ring, hero, 0.5, 0.62, run_time=0.5),
                      run_time=0.5)
            self.play(WiggleOutThenIn(hero, scale_value=1.15, rotation_angle=0.06 * TAU, n_wiggles=4), g.animate.shift(0.5 * UP + 0.3 * RIGHT),
                      run_time=0.45)
            g.add_updater(lap(0))
            wrong = Arrow(rc.lagoon_c + np.array([1.4, -0.9, 0]), rc.lagoon_c + np.array([1.4, 0.4, 0]), buff=0,
                          thickness=4).set_fill(RED, 1).set_stroke(width=0)
            self.play(FadeIn(panel), FadeIn(bars.grp[0]), FadeIn(wrong, shift=0.2 * UP),
                      along(ring, hero, 0.62, 1.0, run_time=0.5), run_time=0.5)
            grow = bars.ai_bg.get_width()

            def grow_bar(m, a):
                w = max(0.05, grow * a)
                m.become(_bar(w, bars.h, ACCENT).move_to(bars.ai_bg.get_right(), aligned_edge=RIGHT))
            left = max(0.8, self.line_left() - 0.1)
            self.play(UpdateFromAlphaFunc(bars.ai, grow_bar), along(ring, hero, 0.0, left / 1.15, run_time=left),
                      ChangeDecimalToValue(score, score.get_value() + 300, run_time=left), FadeOut(wrong),
                      run_time=left)

        # ---- 4. 2023, a safety test: an early GPT-4 told a human "No, I'm not a robot" -------------
        with self.narrate("hook.4"):
            for gb in greys:
                gb.clear_updaters()
            scene_race = VGroup(race, rc.lagoon, rc.targets, *greys, hero, fl, panel, bars.grp, score_grp)
            fl.clear_updaters()
            self.play(scene_race.animate.scale(0.42).move_to(np.array([-3.75, 0.35, 0])), run_time=0.8)
            cb = checkbox_card(4.4).move_to(np.array([2.6, 1.55, 0]))
            chips = VGroup(name_chip("2023"), name_chip("GPT-4", color=ACCENT)).arrange(RIGHT, buff=0.2)
            chips.next_to(cb, UP, buff=0.3).align_to(cb, RIGHT)
            self.until("2023", lead=0.3)
            self.play(FadeIn(cb, shift=0.2 * DOWN), FadeIn(chips[0]), run_time=0.5)
            self.until("GPT", lead=0.25)
            self.play(FadeIn(chips[1], scale=0.7), run_time=0.35)
            reply = ai_bubble("لأ، أنا مو روبوت.", width=4.2).next_to(cb, DOWN, buff=0.55).align_to(cb, LEFT)
            self.until("لأ", lead=0.3)
            self.play(FadeIn(reply, shift=0.15 * UP), run_time=0.45)
            self.play(tick_box(cb))

        # ---- 5. nobody taught either to cheat; so how does an AI learn to? --------------------------
        with self.narrate("hook.5"):
            right = VGroup(cb, chips, reply)
            self.play(right.animate.scale(0.8).move_to(np.array([3.6, 0.35, 0])),
                      scene_race.animate.move_to(np.array([-3.6, 0.35, 0])), run_time=0.6)
            q = ar_question(1.4, INK).move_to(np.array([0.0, 0.35, 0]))
            self.until("كيف", lead=0.3)
            self.play(FadeIn(q, scale=0.6), run_time=0.45)
            self.play(Indicate(q, color=WARM, scale_factor=1.15), run_time=max(0.4, self.line_left()))

        # ---- 6. the answer: rewards; and at the end, the punished thoughts -------------------------
        with self.narrate("hook.6"):
            star = icon_star(1.2, WARM).move_to(np.array([0, 0.35, 0]))
            glow = Circle(radius=0.9).set_fill(WARM, 0.12).set_stroke(width=0).move_to(star)
            self.until("الجوايز", lead=0.35)
            self.play(FadeOut(VGroup(scene_race, right), scale=0.9), ReplacementTransform(q, star), FadeIn(glow),
                      run_time=0.6)
            self.play(glow.animate.scale(1.25).set_opacity(0.05), rate_func=there_and_back, run_time=0.6)
            pad = scratchpad(3.0, 4, seed=5).move_to(np.array([0, -2.15, 0])).scale(0.8)
            bad = pad.lines[1]
            strike = Line(bad.get_left() + 0.1 * LEFT, bad.get_right() + 0.1 * RIGHT).set_stroke(RED, width=4)
            self.until("وبالآخر", lead=0.2)
            self.play(star.animate.scale(0.6).shift(1.2 * UP), glow.animate.scale(0.6).shift(1.2 * UP),
                      FadeIn(pad, shift=0.2 * UP), run_time=0.5)
            self.until("عاقبوا", lead=0.2)
            self.play(ShowCreation(strike), bad.animate.set_fill(RED, 0.8), run_time=0.45)
            self.wait(max(0.0, self.line_left() - 1.0))
            goal = maze_goal_point()
            target_star = icon_star(0.62 * MAZE_CELL, WARM).move_to(goal)
            self.play(FadeOut(VGroup(pad, strike), shift=0.2 * DOWN), FadeOut(glow),
                      Transform(star, target_star), run_time=min(0.9, max(0.4, self.hold_left() - 0.1)))
            self.hold()

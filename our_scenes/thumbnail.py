"""
Thumbnail candidates for video 4, drawn in the video's own pieces (nothing that isn't in the video).

  A (default)  the ticked «أنا لست روبوت» checkbox, the channel's teal cursor beside the tick, an amber
               reward star: the AI passed the robot test, and the star says how (rewards).
  B            the maze's coin loop: two arrows pointing at each other over the coin, the dot bouncing,
               the star ignored in the corner (the mechanism itself, no text)
  C            the boat circling its lagoon on fire, the score climbing past the human bar

Rules (docs/packaging_rules.md): one subject, large; 0–3 words; dark ground; the bottom-right corner empty
(the duration badge); readable at 160 px.

Render: xvfb-run -a .venv/bin/manimgl our_scenes/thumbnail.py ThumbA -w -s --hd --video_dir ./media
then scripts/make_thumbnails.py crops/exports 1280x720 and 1920x1080 and the feed sheet.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from our_scenes.rl_kit import *  # noqa: F401,F403
from our_scenes.rl_kit import _bar, _card  # noqa: F401


def soft_glow(center, radius: float, color, opacity: float = 0.10, rings: int = 40) -> VGroup:
    """A smooth radial glow: many faint discs, densest in the middle."""
    g = VGroup()
    for k in range(rings):
        r = radius * (1 - k / rings) ** 0.8
        g.add(Circle(radius=max(r, 0.01)).move_to(center).set_fill(color, opacity / rings * 2.2).set_stroke(width=0))
    return g


class ThumbA(RLScene):
    def construct(self):
        glow = soft_glow(np.array([-0.4, 0.3, 0]), 6.5, ACCENT, 0.22)
        cb = checkbox_card(10.4, checked=True).move_to(np.array([-0.55, 0.35, 0]))
        cb.tick.set_stroke(width=18)
        big = ar_text(CAPTCHA_AR, 120, "#1d1d1b")
        big.set_height(0.40 * cb.card.get_height())
        big.next_to(cb.box, LEFT, buff=0.55)
        cb.label.become(big)
        cur = cursor(1.7).next_to(cb.box, RIGHT, buff=0.3).shift(0.18 * DOWN)
        star = icon_star(1.9, WARM).move_to(cb.card.get_corner(UR) + np.array([0.15, 0.75, 0]))
        sglow = soft_glow(star.get_center(), 1.8, WARM, 0.45)
        rays = VGroup(*[Line(ORIGIN, 0.5 * RIGHT).set_stroke(WARM, width=7).shift(1.3 * RIGHT)
                        .rotate(a, about_point=ORIGIN).shift(star.get_center()) for a in np.linspace(0, TAU, 9)[:-1]])
        self.add(glow, cb, sglow, rays, star, cur)
        self.wait(0.1)


class ThumbB(RLScene):
    def construct(self):
        crun = coin_run()
        mz = Maze(cell=1.3, center=np.array([-0.5, 0.25, 0]))
        ar_ = PolicyArrows(mz, crun.probs[-1])
        ar_.set_opacity(0.25)
        coin = coin_icon(1.0).move_to(mz.cell_center(COIN))
        a, b = mz.cell_center((2, 0)), mz.cell_center((3, 0))
        mid = (a + b) / 2
        top = ArcBetweenPoints(a + 0.15 * UP, b + 0.15 * UP, angle=-PI * 0.85).set_stroke(WARM, width=16)
        bot = ArcBetweenPoints(b + 0.15 * DOWN, a + 0.15 * DOWN, angle=-PI * 0.85).set_stroke(WARM, width=16)
        tips = VGroup()
        for arc in (top, bot):
            d = arc.get_points()[-1] - arc.get_points()[-4]
            tip = Triangle().set_height(0.5).set_fill(WARM, 1).set_stroke(width=0)
            tip.rotate(np.arctan2(d[1], d[0]) - PI / 2).move_to(arc.get_end())
            tips.add(tip)
        dot = learner_dot(mz.cell).move_to(b)
        mz.star.set_opacity(0.3)
        cglow = soft_glow(mid, 2.2, WARM, 0.35)
        self.add(cglow, mz, ar_, coin, top, bot, tips, dot)
        self.wait(0.1)


class ThumbC(RLScene):
    def construct(self):
        rc = race_course(width=12.4, height=6.6, center=np.array([0.0, 0.2, 0]))
        lag = rc.lagoon_c
        hero = boat(1.2, ACCENT).move_to(lag + rc.lagoon_r * RIGHT).rotate(PI / 2)
        fl = VGroup(flame(0.75).move_to(hero.get_center() + np.array([0.0, 0.5, 0])),
                    flame(0.5).move_to(hero.get_center() + np.array([-0.35, 0.25, 0])))
        trail = Arc(start_angle=-PI / 2, angle=1.6 * PI, radius=rc.lagoon_r).move_to(lag)
        trail.set_stroke(INK, width=6, opacity=0.5)
        star = icon_star(1.2, WARM).move_to(np.array([-4.6, 2.4, 0]))
        num = latin("999", 120, WARM, weight="BOLD").next_to(star, RIGHT, buff=0.3)
        self.add(rc.water, rc.island, rc.course, rc.finish, rc.lagoon, rc.targets, trail, hero, fl, star, num)
        self.wait(0.1)

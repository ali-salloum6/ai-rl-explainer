"""
Test bench for our_scenes/rl_kit.py (not a video beat): stills of the maze, the chance arrows and
bars, and the RL loop, so the kit can be checked by eye before a scene uses it.

  xvfb-run -a .venv/bin/manimgl our_scenes/rl_kit_demo.py MazeStill -s -l    # PNG of the last frame
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from our_scenes.rl_kit import *  # noqa: F401,F403


class MazeStill(RLScene):
    def construct(self):
        run = rl_run()
        maze = Maze(cell=0.82, center=np.array([-2.2, -0.1, 0]))
        arrows = PolicyArrows(maze, run.probs[0])
        dot = learner_dot(maze.cell).move_to(maze.cell_center(START))
        bars = ChanceBars(run.probs[0][START]).move_to(np.array([4.0, -0.1, 0]))
        cnt = VGroup(ar_text(TRY_AR, 30, INK_2), latin("1", 30, INK_2)).arrange(LEFT, buff=0.15)
        cnt.next_to(maze, UP, buff=0.25).align_to(maze, RIGHT)
        self.add(maze, arrows, dot, bars, cnt)
        self.wait(0.1)


class MazeLearned(RLScene):
    def construct(self):
        run = rl_run()
        maze = Maze(cell=0.82, center=np.array([-2.2, -0.1, 0]))
        arrows = PolicyArrows(maze, run.probs[-1])
        path = greedy_path(run.probs[-1])
        tr = trail_line(maze, path, WARM, 0.55, 6)
        dot = learner_dot(maze.cell).move_to(maze.cell_center(START))
        bars = ChanceBars(run.probs[-1][START]).move_to(np.array([4.0, -0.1, 0]))
        self.add(maze, tr, arrows, dot, bars)
        self.wait(0.1)


class LoopStill(RLScene):
    def construct(self):
        run = rl_run()
        lp = rl_loop(content=mini_maze(), p4=run.probs[-1][START])
        self.add(lp.learner, lp.world, lp.act, lp.score, lp.chip_try, lp.chip_score, lp.chip_grow)
        self.wait(0.1)


class PartsSheet(RLScene):
    """Every new part on one frame, to check the drawing."""

    def construct(self):
        rc = race_course(width=4.6, height=2.6, center=np.array([-4.3, 2.1, 0]))
        b = boat(0.5).move_to(rc.lagoon_c + np.array([0.62, 0, 0])).rotate(PI / 2)
        f = flame(0.3).next_to(b, UP, buff=0.0)
        self.add(rc.water, rc.island, rc.course, rc.finish, rc.lagoon, rc.targets, b, f)
        cb = checkbox_card(3.6, checked=True).move_to(np.array([1.2, 2.9, 0]))
        bub = ai_bubble(REPLY_AR, width=4.2).move_to(np.array([1.2, 1.7, 0]))
        self.add(cb, bub)
        note = thought_note(THOUGHT_AR, width=3.4).move_to(np.array([5.0, 2.4, 0]))
        self.add(note)
        people = VGroup(person_icon(0.8, WARM), headset_person(0.8), person_icon(0.8, INK_2)).arrange(RIGHT, buff=0.4)
        people.move_to(np.array([5.0, 0.9, 0]))
        self.add(people)
        tb = tetris_board(0.13).move_to(np.array([-5.6, -1.6, 0]))
        pz = pause_icon(0.5).move_to(tb)
        self.add(tb, pz)
        hs = VGroup(agent_token(ACCENT), agent_token(SEEKER), crate(), ramp_icon()).arrange(RIGHT, buff=0.25)
        hs.move_to(np.array([-3.2, -0.4, 0]))
        self.add(hs)
        fig = stick_figure(0.9).move_to(np.array([-3.4, -2.1, 0]))
        gr = gripper(0.8).move_to(np.array([-1.6, -2.1, 0]))
        bl = ball_icon(0.45).next_to(gr, RIGHT, buff=0.1)
        cam = camera_icon(0.7).next_to(gr, LEFT, buff=0.3)
        self.add(fig, gr, bl, cam)
        jb = judge_box(1.8, 1.1).move_to(np.array([1.0, -0.3, 0]))
        ac = answer_card(2.0, 3).move_to(np.array([1.0, -2.3, 0]))
        sp = VGroup(*[sparkle(0.3) for _ in range(3)]).arrange(RIGHT, buff=0.15).next_to(ac, UP, buff=0.1)
        self.add(jb, ac, sp)
        cc = code_card(2.4, 5).move_to(np.array([3.4, -1.0, 0]))
        tc = tests_card(2.2, 3, (True, False, True)).move_to(np.array([5.6, -1.0, 0]))
        self.add(cc, tc)
        pad = scratchpad(2.4, 4).move_to(np.array([3.6, -2.95, 0]))
        mon = monitor_box(1.3, 0.8).move_to(np.array([5.7, -2.95, 0]))
        self.add(pad, mon)
        pg = pixel_game(1.4).move_to(np.array([-0.8, 0.9, 0]))
        gb = go_board(1.2).move_to(np.array([-1.0, -0.9, 0]))
        coin = coin_icon(0.5).move_to(np.array([-0.2, 2.9, 0]))
        tc2 = try_counter(37).move_to(np.array([-1.6, 2.9, 0]))
        self.add(pg, gb, coin, tc2)
        self.wait(0.1)


class RuleStill(RLScene):
    def construct(self):
        self.add(rule_text())
        self.add(name_chip("GPT-4").move_to(np.array([0, -2, 0])), name_chip("2023").move_to(np.array([2, -2, 0])),
                 name_chip(JUDGE_AR, arabic=True).move_to(np.array([-2, -2, 0])))
        self.wait(0.1)

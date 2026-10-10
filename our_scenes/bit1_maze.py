"""
Bit1Maze — teach a machine from scratch: a dot, a maze, a reward. The centrepiece.

Everything on the maze is a real REINFORCE run (rl_kit.rl_run, seeded): the tries, the trails and
every arrow length are what the learner actually did and had.
  1 the maze draws in around the star the hook left; the dot
  2 the way is never shown (a dashed guess, struck out); the star = the reward
  3 four equal chances: the bars card (one bar per move, named on its word), then the arrows in
    every cell
  4 try 1: wandering, bumping into walls; no reward, nothing changes
  5 try 6: by chance, the star
  6 every move on that trail gets a little likelier (the arrows on the trail grow; the bars of the
    cell next to the star, where the push is strongest)
  7-8 hundreds of tries fast; the arrows settle into a path; the dot runs it straight
  9 the path glows: the reward drew it
 10 the master diagram: the maze becomes the world, the bars the learner; try -> score -> grow
 11 scaled up: a pixel game (2013), a Go board (2016)
 12 the score chip wobbles: what if the reward isn't what we want?

Render (preview): xvfb-run -a .venv/bin/manimgl our_scenes/bit1_maze.py Bit1Maze -w -l --video_dir ./media
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from our_scenes.rl_kit import *  # noqa: F401,F403
from our_scenes.rl_kit import _bar, _card  # noqa: F401


def cell_ring(maze: Maze, c, color=ACCENT) -> VMobject:
    r = RoundedRectangle(width=0.98 * maze.cell, height=0.98 * maze.cell, corner_radius=0.14 * maze.cell)
    return r.move_to(maze.cell_center(c)).set_fill(opacity=0).set_stroke(color, width=3)


class Bit1Maze(RLScene):
    def construct(self):
        run = rl_run()
        k1 = run.first_success                     # the first try that reaches the star (index)
        maze = Maze(cell=MAZE_CELL, center=MAZE_C)
        star = maze.star
        self.add(star)                             # the hook left the star exactly here
        self.continue_from("HookBoat")
        dot = learner_dot(maze.cell).move_to(maze.cell_center(START))
        dot.set_z_index(4)
        arrows = PolicyArrows(maze, run.probs[0])
        arrows.set_z_index(2)

        # ---- 1. a dot in a maze, and a star -------------------------------------------------------
        with self.narrate("bit1_maze.1"):
            floor = maze.floor
            self.play(LaggedStart(*[FadeIn(t, scale=0.8) for t in floor], lag_ratio=0.02), FadeIn(maze.walls),
                      FadeIn(maze.frame), run_time=min(1.4, max(0.8, self.to("نقطة", lead=0.2))))
            self.until("نقطة", lead=0.15)
            self.play(GrowFromCenter(dot), run_time=0.4)
            self.until("ونجمة", lead=0.15)
            self.play(Indicate(star, color=WARM, scale_factor=1.3), run_time=0.6)

        # ---- 2. we never show it the way; it gets a reward when it arrives --------------------------
        with self.narrate("bit1_maze.2"):
            guess = trail_line(maze, greedy_path(run.probs[-1]), INK_2, 0.5, 3)
            guess = DashedVMobject(guess, num_dashes=40, positive_space_ratio=0.5).set_stroke(INK_2, width=3, opacity=0.5)
            self.until("الطريق", lead=0.3)
            self.play(ShowCreation(guess), run_time=0.7)
            no = cross_mark(0.5).move_to(maze.cell_center((4, 2)))
            self.until("أبداً", lead=0.2)
            self.play(FadeIn(no, scale=1.4), guess.animate.set_stroke(opacity=0.15), run_time=0.35)
            self.play(FadeOut(VGroup(guess, no)), run_time=0.35)
            glow = Circle(radius=0.55 * maze.cell).set_fill(WARM, 0.22).set_stroke(width=0).move_to(star)
            self.until("جايزة", lead=0.2)
            self.play(FadeIn(glow, scale=0.5), Indicate(star, color=WARM, scale_factor=1.35), run_time=0.6)
            self.play(FadeOut(glow), run_time=0.3)

        # ---- 3. a chance for every move; at first all equal ------------------------------------------
        with self.narrate("bit1_maze.3"):
            bars = ChanceBars(run.probs[0][START], width=2.7, height=2.5).move_to(BARS_C)
            ring = cell_ring(maze, START)
            link = Line(ring.get_right(), bars.card.get_left()).set_stroke(ACCENT, width=2, opacity=0.5)
            self.play(ShowCreation(ring), FadeIn(bars, shift=0.2 * LEFT), ShowCreation(link), run_time=0.7)
            for word, k in (("فوق", 1), ("تحت", 2), ("يمين", 3), ("شمال", 0)):
                self.until(word, lead=0.1)
                self.play(Indicate(bars.bars[k], color=WARM, scale_factor=1.25), Indicate(bars.marks[k], color=WARM),
                          run_time=0.35)
            self.until("متل بعض", lead=0.35)
            self.play(LaggedStart(*[FadeIn(a) for a in arrows], lag_ratio=0.004), run_time=0.8)

        # ---- 4. try 1: at random, bumping into walls, and nothing ------------------------------------
        with self.narrate("bit1_maze.4"):
            cnt = try_counter(1)
            cnt.move_to(np.array([maze.frame.get_right()[0] - 0.9, COUNTER_Y, 0]))
            self.play(FadeIn(cnt), FadeOut(VGroup(ring, link)), run_time=0.3)
            tr = empty_trail(INK_2, 0.35, 3)
            self.add(tr)
            moves0 = run.moves[0]
            step = max(0.035, (self.line_left() - 1.2) / len(moves0))
            self.play(walk_anim(dot, maze, run.paths[0], moves0, step, tr))
            nothing = ar_text("ولا شي", 30, MUTED).next_to(cnt, DOWN, buff=0.2)
            self.play(FadeOut(tr), FadeIn(nothing), run_time=0.4)

        # ---- 5. until, by chance, the star (try k1+1) ----------------------------------------------
        with self.narrate("bit1_maze.5"):
            self.play(FadeOut(nothing), dot.animate.move_to(maze.cell_center(START)), run_time=0.3)
            self.play(count_anim(cnt, 1, k1 + 1, run_time=0.4))
            tr = empty_trail(ACCENT, 0.5, 4)
            self.add(tr)
            path, moves = run.paths[k1], run.moves[k1]
            step = max(0.04, min(0.11, (self.line_left() - 0.6) / len(moves)))
            self.play(walk_anim(dot, maze, path, moves, step, tr))
            self.play(Flash(star.get_center(), color=WARM, line_length=0.35, flash_radius=0.45),
                      Indicate(star, color=WARM, scale_factor=1.4), run_time=0.6)

        # ---- 6. every move on the way gets a little likelier --------------------------------------
        with self.narrate("bit1_maze.6"):
            used = {(path[t], a) for t, a in enumerate(moves) if path[t] != GOAL}
            hl = {k: WARM for k in used}
            near = path[-2]                          # the cell the star was reached from: the biggest push
            ring2 = cell_ring(maze, near, WARM)
            bars_near = ChanceBars(run.probs[k1][near], width=2.7, height=2.5).move_to(BARS_C)
            link2 = Line(ring2.get_right(), bars_near.card.get_left()).set_stroke(WARM, width=2, opacity=0.6)
            self.play(tr.animate.set_stroke(WARM, opacity=0.75), FadeTransform(bars, bars_near), ShowCreation(ring2),
                      ShowCreation(link2), run_time=0.6)
            self.until("منكبّرلها", lead=0.3)
            self.play(arrows.morph(run.probs[k1 + 1], run_time=1.4, highlight=hl),
                      bars_near.morph(run.probs[k1 + 1][near], run_time=1.4), run_time=1.4)
            self.play(FadeOut(tr), run_time=0.3)

        # ---- 7. again, and again: hundreds of tries ------------------------------------------------
        with self.narrate("bit1_maze.7"):
            bars = bars_near
            self.play(FadeOut(VGroup(ring2, link2)), run_time=0.25)
            ring3 = cell_ring(maze, START)
            link3 = Line(ring3.get_right(), bars.card.get_left()).set_stroke(ACCENT, width=2, opacity=0.5)
            bars_start = ChanceBars(run.probs[k1 + 1][START], width=2.7, height=2.5).move_to(BARS_C)
            self.play(FadeTransform(bars, bars_start), ShowCreation(ring3), ShowCreation(link3),
                      dot.animate.move_to(maze.cell_center(START)), run_time=0.4)
            bars = bars_start
            keys = [k1 + 1, 12, 20, 35, 60, 100, 160]
            dur = max(1.2, self.hold_left() - 0.1)
            # glimpses of tries while the chances change
            demo = [k for k in (14, 40, 110) if run.reached[k]] or [14]
            self.play(arrows.morph_through([run.probs[k] for k in keys], run_time=dur),
                      bars.morph_through([run.probs[k][START] for k in keys], run_time=dur),
                      count_anim(cnt, k1 + 1, keys[-1], run_time=dur),
                      Succession(*[walk_anim(dot, maze, run.paths[k], run.moves[k],
                                             dur / len(demo) / max(1, len(run.moves[k]))) for k in demo]))

        # ---- 8. the moves that lead to the star grow; a path appears ---------------------------------
        with self.narrate("bit1_maze.8"):
            keys = [160, 220, 300, SIM_EPISODES]
            dur = max(1.0, self.line_left() * 0.55)
            self.play(arrows.morph_through([run.probs[k] for k in keys], run_time=dur),
                      bars.morph_through([run.probs[k][START] for k in keys], run_time=dur),
                      count_anim(cnt, 160, SIM_EPISODES, run_time=dur), dot.animate.move_to(maze.cell_center(START)),
                      run_time=dur)
            gp = greedy_path(run.probs[-1])
            gm = [next(a for a in range(4) if maze_step(gp[i], a) == gp[i + 1]) for i in range(len(gp) - 1)]
            self.play(walk_anim(dot, maze, gp, gm, max(0.12, min(0.2, (self.line_left() - 0.1) / len(gm)))))

        # ---- 9. nobody drew this path; the reward did -----------------------------------------------
        with self.narrate("bit1_maze.9"):
            glow_path = trail_line(maze, gp, WARM, 0.85, 7)
            glow_path.set_z_index(1)
            self.play(ShowCreation(glow_path), Indicate(star, color=WARM, scale_factor=1.25), run_time=0.9)
            self.until("الجايزة", lead=0.2)
            self.play(glow_path.animate.set_stroke(width=11, opacity=1.0), rate_func=there_and_back, run_time=0.7)

        # ---- 10. reinforcement learning: try, get a score, grow what worked --------------------------
        with self.narrate("bit1_maze.10"):
            title = ar_text("التعلّم المعزّز", 44, INK).move_to(np.array([0, 3.05, 0]))
            board = VGroup(maze, arrows, glow_path, dot)
            lp = rl_loop(content=None, p4=run.probs[-1][START])
            world = lp.world
            self.play(FadeIn(title, shift=0.2 * DOWN), FadeOut(VGroup(ring3, link3, cnt)), run_time=0.5)
            target_w = 0.82 * world.card.get_width()
            self.play(board.animate.set_width(target_w).move_to(world.card.get_center()), FadeIn(world.card),
                      ReplacementTransform(bars, lp.learner), run_time=1.0)
            world.add(board)
            world.content = board
            self.until("جرّب", lead=0.25)
            self.play(ShowCreation(lp.act.path), FadeIn(lp.act.tip), FadeIn(lp.chip_try, scale=0.7), run_time=0.5)
            self.until("علامة", lead=0.25)
            sc = score_star(0.38).move_to(lp.score.path.get_start())
            self.play(ShowCreation(lp.score.path), FadeIn(lp.score.tip), FadeIn(lp.chip_score, scale=0.7), run_time=0.5)
            self.play(MoveAlongPath(sc, lp.score.path), run_time=0.6)
            self.remove(sc)
            self.until("وكبّر", lead=0.25)
            self.play(FadeIn(lp.chip_grow, scale=0.7), Indicate(lp.learner.bars.bars, color=WARM), run_time=0.6)

        # ---- 11. scaled up: Atari from pixels, a world-class Go player ------------------------------
        with self.narrate("bit1_maze.11"):
            pulse = Dot(radius=0.09).set_fill(INK, 1)

            def lap_pulse(rt):
                return Succession(MoveAlongPath(pulse.copy(), lp.act.path, run_time=rt / 2, remover=True),
                                  MoveAlongPath(pulse.copy(), lp.score.path, run_time=rt / 2, remover=True))
            game = pixel_game(1.9).move_to(world.card)
            y13 = name_chip("2013").next_to(world.card, UP, buff=0.15)
            self.until("أتاري", lead=0.35)
            self.play(FadeOut(board, scale=0.8), FadeIn(game, scale=0.8), FadeIn(y13), lap_pulse(0.8), run_time=0.8)
            go = go_board(1.8).move_to(world.card)
            y16 = name_chip("2016").next_to(world.card, UP, buff=0.15)
            self.until("وغلبت", lead=0.3)
            self.play(FadeOut(game, scale=0.8), FadeIn(go, scale=0.8), FadeTransform(y13, y16), lap_pulse(0.8),
                      run_time=0.8)
            world.remove(board)
            world.add(go)
            self.chip_year = y16

        # ---- 12. but what if the reward isn't exactly what we want? ----------------------------------
        with self.narrate("bit1_maze.12"):
            q = ar_question(0.8, WARM).next_to(lp.chip_score, RIGHT, buff=0.3)
            self.until("الجايزة", lead=0.3)
            self.play(WiggleOutThenIn(lp.chip_score, scale_value=1.15, rotation_angle=0.03 * TAU, n_wiggles=4),
                      FadeIn(q, scale=0.6), FadeOut(title), run_time=0.9)
            self.hold()

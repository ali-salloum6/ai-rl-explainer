"""
Bit2Coin — it learns what we reward, not what we mean.

The coin is a real run on the same maze (rl_kit.coin_run, seeded): a coin worth a point every time
it is stepped on, the star worth more but ending the try. From scratch the dot learns to farm it.
  1 bit 1's loop gives way to a fresh maze (equal arrows); a coin drops on the bottom row
  2 one step on the coin = a point; then training runs fast and the arrows turn toward the coin
  3 the trained dot bounces on the coin, forever; the star dims; the two arrows point at each other
  4 the boat: the race's score was targets, not finishing (the coin and the lagoon side by side)
  5 hide-and-seek from above: after ~380 million games a seeker rides a box over the fort's wall
  6 Tetris, about to lose: pause, and it stays paused
  7 the rule, written
  8 so write the reward better? For a game, maybe. A sentence: an answer card, an empty score slot

Render (preview): xvfb-run -a .venv/bin/manimgl our_scenes/bit2_coin.py Bit2Coin -w -l --video_dir ./media
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from our_scenes.rl_kit import *  # noqa: F401,F403
from our_scenes.rl_kit import _bar, _card  # noqa: F401


def bit1_end_state() -> SimpleNamespace:
    """Bit 1's last frame, rebuilt: the loop with the Go board, the 2016 chip and the question mark."""
    run = rl_run()
    lp = rl_loop(content=None, p4=run.probs[-1][START])
    go = go_board(1.8).move_to(lp.world.card)
    y16 = name_chip("2016").next_to(lp.world.card, UP, buff=0.15)
    q = ar_question(0.8, WARM).next_to(lp.chip_score, RIGHT, buff=0.3)
    grp = VGroup(lp.learner, lp.world, go, lp.act, lp.score, lp.chip_try, lp.chip_score, lp.chip_grow, y16, q)
    return SimpleNamespace(lp=lp, grp=grp)


def coin_greedy(p: np.ndarray, steps: int = 18) -> tuple[list, list]:
    """Follow the likeliest move from the start for `steps` moves (the trained coin farmer)."""
    s, path, moves = START, [START], []
    for _ in range(steps):
        a = int(np.argmax(p[s]))
        s = maze_step(s, a)
        path.append(s)
        moves.append(a)
        if s == GOAL:
            break
    return path, moves


def arena() -> SimpleNamespace:
    """Hide-and-seek from above: the room, the hiders' fort (right), seekers (left), a box and a ramp.
    .room .fort .hiders .seekers .crate .ramp .fort_wall_x"""
    W, H = 9.0, 5.0
    room = RoundedRectangle(width=W, height=H, corner_radius=0.2).set_fill("#0e1320", 1).set_stroke(WALL_FILL, width=8)
    fx0, fx1, fy0, fy1 = 1.6, 4.1, -1.3, 1.3
    fort = VGroup(wall_seg((fx0, fy0), (fx0, fy1)), wall_seg((fx0, fy1), (fx1, fy1)),
                  wall_seg((fx0, fy0), (fx1, fy0)), wall_seg((fx1, fy0), (fx1, fy1)))
    hiders = VGroup(agent_token(ACCENT, 0.42).move_to(np.array([2.5, 0.4, 0])),
                    agent_token(ACCENT, 0.42).move_to(np.array([3.2, -0.45, 0])).rotate(PI))
    seekers = VGroup(agent_token(SEEKER, 0.42).move_to(np.array([-3.4, 0.9, 0])),
                     agent_token(SEEKER, 0.42).move_to(np.array([-3.2, -1.2, 0])))
    crate_ = crate(0.55).move_to(np.array([-0.4, 0.2, 0]))
    ramp_ = ramp_icon(0.7).move_to(np.array([-1.5, 0.2, 0]))
    return SimpleNamespace(room=room, fort=fort, hiders=hiders, seekers=seekers, crate=crate_, ramp=ramp_,
                           fort_wall_x=fx0, grp=VGroup(room, fort, hiders, seekers, crate_, ramp_))


class Bit2Coin(RLScene):
    def construct(self):
        end1 = bit1_end_state()
        self.add(end1.grp)
        self.continue_from("Bit1Maze")
        crun = coin_run()

        # ---- 1. help a new dot learn faster: a coin on the way --------------------------------------
        with self.narrate("bit2_coin.1"):
            maze = Maze(cell=MAZE_CELL, center=MAZE_C)
            arrows = PolicyArrows(maze, crun.probs[0])
            arrows.set_z_index(2)
            dot = learner_dot(maze.cell).move_to(maze.cell_center(START)).set_z_index(4)
            self.play(FadeOut(end1.grp, scale=0.9), run_time=0.5)
            self.play(FadeIn(maze, scale=0.95), FadeIn(arrows), GrowFromCenter(dot), run_time=0.7)
            coin = coin_icon(0.55 * maze.cell).move_to(maze.cell_center(COIN)).set_z_index(3)
            self.until("ليرة", lead=0.25)
            self.play(FadeIn(coin, shift=0.6 * DOWN, scale=1.3), run_time=0.45, rate_func=rush_from)
            self.until("جايزة", lead=0.2)
            sp = VGroup(*[sparkle(0.22).move_to(coin.get_center() + 0.42 * np.array([np.cos(a), np.sin(a), 0]))
                          for a in (0.6, 2.2, 4.0)])
            self.play(LaggedStart(*[FadeIn(x, scale=0.3) for x in sp], lag_ratio=0.2), run_time=0.5)
            self.play(FadeOut(sp), run_time=0.3)

        # ---- 2. a point per step on the coin; watch what it learns ---------------------------------
        with self.narrate("bit2_coin.2"):
            ctr_icon = coin_icon(0.42)
            coins = Counter(ctr_icon, 0, font_size=34, color=WARM)
            coins.move_to(np.array([maze.frame.get_left()[0] + 0.6, COUNTER_Y, 0]))
            tries = try_counter(1).move_to(np.array([maze.frame.get_right()[0] - 0.9, COUNTER_Y, 0]))
            self.play(FadeIn(coins), FadeIn(tries), run_time=0.4)
            demo_path = [START, (1, 0), COIN]
            self.play(walk_anim(dot, maze, demo_path, [1, 1], 0.28), run_time=0.56)
            self.play(Indicate(coin, color=WARM, scale_factor=1.3), count_anim(coins, 0, 1, run_time=0.3), run_time=0.4)
            self.until("شوفوا", lead=0.2)
            keys = [0, 15, 40, 80, 150, 260, COIN_EPISODES]
            dur = max(1.4, self.hold_left() - 0.1)
            self.play(arrows.morph_through([crun.probs[k] for k in keys], run_time=dur),
                      count_anim(tries, 1, COIN_EPISODES, run_time=dur),
                      dot.animate.move_to(maze.cell_center(START)), FadeOut(coins), run_time=dur)

        # ---- 3. it never goes to the star: back and forth on the coin, forever ----------------------
        with self.narrate("bit2_coin.3"):
            coins.set_value(0)
            self.play(FadeIn(coins), run_time=0.2)
            gpath, gmoves = coin_greedy(crun.probs[-1], 22)
            n_hits = sum(1 for i in range(1, len(gpath)) if gpath[i] == COIN and gpath[i - 1] != COIN)
            self.until("النجمة", lead=0.2)
            self.play(maze.star.animate.set_opacity(0.25), run_time=0.4)
            step = max(0.12, (self.line_left() - 0.4) / len(gmoves))
            self.play(walk_anim(dot, maze, gpath, gmoves, step),
                      count_anim(coins, 0, n_hits, run_time=step * len(gmoves)))
            pair = {((2, 0), 1): WARM, ((3, 0), 3): WARM}
            self.until("كافأناها", lead=0.3)
            self.play(arrows.morph(crun.probs[-1], run_time=0.6, highlight=pair), Indicate(coin, color=WARM),
                      run_time=0.6)
            arrows.set_probs(crun.probs[-1], highlight=pair)

        # ---- 4. the boat, exactly: its score was targets, not finishing -----------------------------
        with self.narrate("bit2_coin.4"):
            left = VGroup(maze, arrows, dot, coin, coins, tries)
            self.play(left.animate.scale(0.58).move_to(np.array([-3.45, -0.15, 0])), run_time=0.7)
            rc = race_course(width=5.6, height=3.1, center=np.array([3.25, -0.15, 0]))
            hero = boat(0.46, ACCENT).set_z_index(3)
            race = VGroup(rc.water, rc.island, rc.course, rc.finish, rc.lagoon, rc.targets)
            ring = circle_path(rc.lagoon_c, rc.lagoon_r, start=0.0, ccw=True)
            hero.move_to(ring.point_from_proportion(0))
            eq = ar_text("=", 70, INK_2).move_to(np.array([-0.05, -0.15, 0]))
            self.play(FadeIn(race, shift=0.2 * LEFT), FadeIn(hero), FadeIn(eq), run_time=0.6)
            self.until("الأهداف", lead=0.3)
            per = 1.0
            tg = list(rc.targets)
            angles = [PI / 2, PI / 2 + 2 * PI / 3, PI / 2 + 4 * PI / 3]
            fin_x = cross_mark(0.34).move_to(rc.finish.get_center())
            for lap in range(max(1, int(self.line_left() / per))):
                anims = [along(ring, hero, 0.0, 1.0, run_time=per)]
                anims += [pop_and_return(tg[i], per, max(0.0, (a % TAU) / TAU * per - 0.05), 0.25)
                          for i, a in enumerate(angles)]
                if lap == 1:
                    anims.append(FadeIn(fin_x, scale=1.5))
                # the maze dot keeps bouncing too
                anims.append(walk_anim(dot, maze, [COIN, (3, 0), COIN], [1, 3], per / 2))
                self.play(*anims)
            self.boat_bits = (race, hero, eq, fin_x)

        # ---- 5. hide-and-seek: a seeker rides a box over the wall ------------------------------------
        with self.narrate("bit2_coin.5"):
            race, hero, eq, fin_x = self.boat_bits
            self.play(FadeOut(VGroup(left, race, hero, eq, fin_x)), run_time=0.5)
            ar = arena()
            ar.grp.scale(0.95).move_to(np.array([0, -0.25, 0]))
            games = Integer(0, font_size=34, text_config=dict(font=LATIN_FONT), group_with_commas=True).set_fill(INK_2)
            games_lab = ar_text("جولة", 30, INK_2)
            gctr = VGroup(games_lab, games)

            def place_ctr(m):
                games.next_to(games_lab, LEFT, buff=0.2)
            games_lab.move_to(np.array([4.6, 2.95, 0]))
            gctr.add_updater(place_ctr)
            self.play(FadeIn(ar.grp, scale=0.96), FadeIn(gctr), run_time=0.6)
            self.until("مئات", lead=0.3)
            self.play(ChangeDecimalToValue(games, 380_000_000, run_time=1.3, rate_func=rush_into))
            sk = ar.seekers[0]
            # the seeker drags the ramp to the box, climbs it, rides the box to the wall, drops over it
            self.until("يركبوا", lead=0.6)
            self.play(sk.animate.move_to(ar.ramp.get_left() + 0.3 * LEFT), run_time=0.5)
            self.play(ar.ramp.animate.next_to(ar.crate, LEFT, buff=0.0), sk.animate.move_to(ar.crate.get_left() +
                      0.75 * LEFT), run_time=0.5)
            self.play(sk.animate.move_to(ar.crate.get_center()).scale(1.25), run_time=0.45)
            rider = VGroup(ar.crate, sk)
            wall_x = ar.fort[0].get_center()[0]
            self.until("فوق", lead=0.4)
            self.play(rider.animate.move_to(np.array([wall_x - 0.45, ar.crate.get_y(), 0])), run_time=0.7)
            hop = ArcBetweenPoints(sk.get_center(), np.array([wall_x + 0.55, sk.get_y() - 0.1, 0]), angle=-PI / 2)
            self.play(MoveAlongPath(sk, hop), sk.animate.scale(0.8), run_time=0.55)
            self.play(LaggedStart(*[Indicate(h, color=SEEKER, scale_factor=1.3) for h in ar.hiders], lag_ratio=0.2),
                      Flash(np.array([wall_x, sk.get_y(), 0]), color=WARM, flash_radius=0.4), run_time=0.6)
            self.hide_bits = (ar, gctr)

        # ---- 6. Tetris, about to lose: pause, and leave it paused ------------------------------------
        with self.narrate("bit2_coin.6"):
            ar, gctr = self.hide_bits
            gctr.clear_updaters()
            self.play(FadeOut(VGroup(ar.grp, gctr)), run_time=0.45)
            tb = tetris_board(0.27).move_to(np.array([0, -0.2, 0]))
            piece = VGroup(*[Square(0.27 * 0.92).set_fill("#8e7cf0", 0.95).set_stroke(BG, width=1) for _ in range(4)])
            piece.arrange(RIGHT, buff=0.27 * 0.08)
            piece.move_to(tb.frame.get_top() + 0.4 * DOWN)
            self.play(FadeIn(tb), FadeIn(piece), run_time=0.5)
            self.play(piece.animate.shift(0.27 * 2 * DOWN), run_time=max(0.4, self.to("وقّف", lead=0.25)),
                      rate_func=linear)
            pz = pause_icon(1.1).move_to(tb.frame.get_center()).set_z_index(5)
            self.until("وقّف", lead=0.15)
            self.play(FadeIn(pz, scale=0.6), tb.blocks.animate.set_opacity(0.45), piece.animate.set_opacity(0.6),
                      run_time=0.45)
            self.play(Indicate(pz, color=WARM, scale_factor=1.08), run_time=max(0.5, self.hold_left() - 0.55))
            self.tetris_bits = (tb, piece, pz)

        # ---- 7. the rule ---------------------------------------------------------------------------
        with self.narrate("bit2_coin.7"):
            tb, piece, pz = self.tetris_bits
            rule = rule_text(1.0).move_to(np.array([0, 0.2, 0]))
            self.play(FadeOut(VGroup(tb, piece, pz), scale=0.9), run_time=0.4)
            self.until("بيتعلّم", lead=0.2)
            self.play(FadeIn(rule[0], shift=0.15 * UP), run_time=0.6)
            self.until("مو", lead=0.15)
            self.play(FadeIn(rule[1], shift=0.15 * UP), run_time=0.6)
            ul = Line(rule[1].get_corner(DL) + 0.12 * DOWN, rule[1].get_corner(DR) + 0.12 * DOWN).set_stroke(ACCENT, 3)
            self.play(GrowFromCenter(ul), run_time=0.4)

        # ---- 8. write the reward better? for a game, maybe; but a sentence? ---------------------------
        with self.narrate("bit2_coin.8"):
            self.play(VGroup(rule, ul).animate.scale(0.55).move_to(np.array([0, 3.0, 0])), run_time=0.6)
            mini = VGroup(Maze(cell=1.0), coin_icon(0.6)).set_height(1.3)
            mini[1].move_to(mini[0].cell_center(COIN))
            boat_ic = boat(0.9, ACCENT)
            games = VGroup(mini, boat_ic).arrange(RIGHT, buff=0.8).move_to(np.array([-3.4, 0.0, 0]))
            ok = check_mark(0.5).next_to(games, DOWN, buff=0.3)
            self.until("للعبة", lead=0.25)
            self.play(FadeIn(games, shift=0.2 * UP), run_time=0.5)
            self.play(ShowCreation(ok), run_time=0.35)
            ans = answer_card(3.4, 4, seed=3).move_to(np.array([2.6, 0.1, 0]))
            slot = DashedVMobject(RoundedRectangle(width=1.5, height=0.7, corner_radius=0.35), num_dashes=24)
            slot.set_stroke(WARM, width=2.4).next_to(ans, DOWN, buff=0.35)
            q = ar_question(0.5, WARM).move_to(slot)
            self.until("جملة", lead=0.5)
            self.play(FadeIn(ans, shift=0.2 * LEFT), run_time=0.5)
            self.play(ShowCreation(slot), FadeIn(q, scale=0.6), run_time=0.5)
            self.hold()

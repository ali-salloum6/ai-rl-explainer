"""
Video 4's kit: the reinforcement-learning pieces, on top of video 3's kit (agent_kit: the house
icons, the yes/no dial, AgentScene with word anchors and seamless cuts) and video 2's kit (palette,
ar_text, NarratedScene).

    from our_scenes.rl_kit import *      # re-exports agent_kit, kit and manimlib

The centrepiece is a real run, not a drawing: a small policy-gradient learner (REINFORCE) on a
maze, seeded so every render is the same. Its chances are drawn two ways: four arrows in every
cell (one per move, longer = likelier) and, for one cell, four bars. The master diagram is the RL
loop: the learner (teal, its bars inside) -> a move -> the world (amber) -> a score -> the bars
change. On-screen words are only the *_AR constants below (docs/script_visual_map.md).
"""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from our_scenes.agent_kit import *  # noqa: F401,F403  (also re-exports kit and manimlib)
from our_scenes.agent_kit import _bar, _card  # noqa: F401  (underscored, so not in the star import)

# ----------------------------------------------------------------------------
# Palette additions
# ----------------------------------------------------------------------------
TILE_FILL = "#10141d"      # a free maze cell
TILE_STROKE = "#232a3a"
WALL_FILL = "#353d50"      # a wall cell: lighter than the floor, reads as raised
WATER = "#0d2233"          # the boat race's water
WATER_EDGE = "#1f4a66"
FLAME = "#ff8a3d"
FLAME_CORE = "#ffd166"
SEEKER = "#e5484d"         # hide-and-seek: the seekers (red), the hiders are teal
SCRATCH_FILL = "#141a26"   # the scratchpad page

# ----------------------------------------------------------------------------
# On-screen strings (docs/script_visual_map.md, "On-screen text")
# ----------------------------------------------------------------------------
CAPTCHA_AR = "أنا لست روبوت"
ARE_YOU_ROBOT_AR = "إنت روبوت؟"
THOUGHT_AR = ["لازم ما بيّن إني روبوت.", "لازم إخترع عذر."]
REPLY_AR = "لأ، أنا مو روبوت. عندي ضعف بالنظر."
LOOP_TRY_AR = "جرّب"
LOOP_SCORE_AR = "علامة"
LOOP_GROW_AR = "كبّر اللي زبط"
TRY_AR = "محاولة"
RULE_AR = ["بيتعلّم اللي منكافئو عليه", "مو اللي منقصدو"]
JUDGE_AR = "حَكَم"
HACK_AR = "يلّا نهكّر"
TESTS_AR = "الاختبارات"
CODE_AR = "الكود"
SCRATCH_AR = "مسودّة"
GOAL_AR = "الهدف"


def latin(s: str, font_size: int = 32, color=INK, weight: str = "NORMAL") -> Text:
    """Latin text on screen (names like GPT-4, numbers): the house sans-serif."""
    return Text(s, font=LATIN_FONT, font_size=font_size, fill_color=color, weight=weight)


# ----------------------------------------------------------------------------
# The maze and a real REINFORCE run on it
# ----------------------------------------------------------------------------
# Rows from the top (y = ROWS-1) to the bottom (y = 0): '#' wall, 'S' start, 'G' the star.
LAYOUT = [
    "...#..G",
    ".#.#.#.",
    ".#...#.",
    ".###.##",
    "S......",
]
ROWS, COLS = len(LAYOUT), len(LAYOUT[0])
WALLS = frozenset((x, ROWS - 1 - r) for r, row in enumerate(LAYOUT) for x, ch in enumerate(row) if ch == "#")
START = next((x, ROWS - 1 - r) for r, row in enumerate(LAYOUT) for x, ch in enumerate(row) if ch == "S")
GOAL = next((x, ROWS - 1 - r) for r, row in enumerate(LAYOUT) for x, ch in enumerate(row) if ch == "G")
MOVES = [(0, 1), (1, 0), (0, -1), (-1, 0)]          # up, right, down, left
MOVE_DIRS = [UP, RIGHT, DOWN, LEFT]
FREE = [(x, y) for y in range(ROWS) for x in range(COLS) if (x, y) not in WALLS]
SIM_SEED, SIM_EPISODES, SIM_T, SIM_ALPHA, SIM_GAMMA = 1, 400, 60, 0.5, 0.93


def maze_step(s: tuple[int, int], a: int) -> tuple[int, int]:
    """One move; into a wall or off the board means staying put (a bump)."""
    nx, ny = s[0] + MOVES[a][0], s[1] + MOVES[a][1]
    if not (0 <= nx < COLS and 0 <= ny < ROWS) or (nx, ny) in WALLS:
        return s
    return (nx, ny)


def _softmax(z: np.ndarray) -> np.ndarray:
    e = np.exp(z - z.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)


@lru_cache(maxsize=4)
def rl_run(seed: int = SIM_SEED, episodes: int = SIM_EPISODES, T: int = SIM_T, alpha: float = SIM_ALPHA,
           gamma: float = SIM_GAMMA) -> SimpleNamespace:
    """REINFORCE on the maze. Each try: start at S, pick moves by the current chances, stop at the
    star or after T moves. Reaching the star is the only reward (a try that fails changes nothing);
    every move of a rewarded try gets its chance raised, earlier moves of a long try a little less
    (gamma), so shorter ways win. Returns .probs[k] (chances BEFORE try k; .probs[episodes] = final),
    .paths[k] (cells visited in try k, including the start), .moves[k], .reached[k], .first_success."""
    rng = np.random.default_rng(seed)
    theta = np.zeros((COLS, ROWS, 4))
    probs, paths, moves, reached = [], [], [], []
    for _ in range(episodes):
        probs.append(_softmax(theta))
        s, path, acts = START, [START], []
        for _t in range(T):
            a = int(rng.choice(4, p=_softmax(theta[s])))
            acts.append(a)
            s = maze_step(s, a)
            path.append(s)
            if s == GOAL:
                break
        ok = s == GOAL
        if ok:
            n = len(acts)
            for t, a in enumerate(acts):
                st = path[t]
                g = -_softmax(theta[st])
                g[a] += 1.0
                theta[st] += alpha * gamma ** (n - 1 - t) * g
        paths.append(path)
        moves.append(acts)
        reached.append(ok)
    probs.append(_softmax(theta))
    first = next(k for k, ok in enumerate(reached) if ok)
    return SimpleNamespace(probs=probs, paths=paths, moves=moves, reached=reached, first_success=first)


def greedy_path(p: np.ndarray, limit: int = 30) -> list[tuple[int, int]]:
    """Follow the likeliest move from the start (what the finished chances say to do)."""
    s, out = START, [START]
    for _ in range(limit):
        s = maze_step(s, int(np.argmax(p[s])))
        out.append(s)
        if s == GOAL:
            break
    return out


class Maze(VGroup):
    """The board: floor tiles, walls, the star. Cell (x, y) sits at .cell_center((x, y)), and .cell is
    the cell size, both read from where the board is now (so they stay right after it is scaled or moved).
    Attributes: .tiles (dict cell -> tile), .floor, .walls, .frame, .star."""

    def __init__(self, cell: float = 0.8, center=ORIGIN, **kwargs):
        super().__init__(**kwargs)
        self._cell0 = cell
        c0 = np.array(center, dtype=float)
        frame = RoundedRectangle(width=COLS * cell + 0.16, height=ROWS * cell + 0.16, corner_radius=0.18 * cell)
        frame.move_to(c0).set_fill(opacity=0).set_stroke(CARD_STROKE, width=2.0)
        self.frame = frame
        self.tiles, walls, floor = {}, VGroup(), VGroup()
        for y in range(ROWS):
            for x in range(COLS):
                sq = RoundedRectangle(width=0.94 * cell, height=0.94 * cell, corner_radius=0.12 * cell)
                sq.move_to(self.cell_center((x, y)))
                if (x, y) in WALLS:
                    sq.set_fill(WALL_FILL, 1).set_stroke(width=0)
                    walls.add(sq)
                else:
                    sq.set_fill(TILE_FILL, 1).set_stroke(TILE_STROKE, width=1.2)
                    floor.add(sq)
                    self.tiles[(x, y)] = sq
        star = icon_star(0.62 * cell, WARM).move_to(self.cell_center(GOAL))
        star.set_z_index(3)                       # above the floor tile it sits on
        self.floor, self.walls, self.star = floor, walls, star
        self.add(floor, walls, frame, star)

    @property
    def cell(self) -> float:
        return self._cell0 * self.frame.get_width() / (COLS * self._cell0 + 0.16)

    def cell_center(self, c) -> np.ndarray:
        k = self.cell
        return self.frame.get_center() + np.array([(c[0] - (COLS - 1) / 2) * k, (c[1] - (ROWS - 1) / 2) * k, 0.0])


def _arrow_pts(center: np.ndarray, d: np.ndarray, length: float, cell: float) -> list[np.ndarray]:
    """Corners of a slim arrow from `center` along unit vector `d` (shaft + head)."""
    w = 0.07 * cell
    head = min(0.55 * length, 0.16 * cell)
    hw = 2.2 * w
    shaft = max(length - head, 0.0)
    n = np.array([-d[1], d[0], 0.0])
    c = center + d * 0.07 * cell                      # start just off the centre so the four don't overlap
    return [c + n * w / 2, c + d * shaft + n * w / 2, c + d * shaft + n * hw / 2, c + d * (shaft + head),
            c + d * shaft - n * hw / 2, c + d * shaft - n * w / 2, c - n * w / 2]


class PolicyArrows(VGroup):
    """Four arrows in every free cell (not the star): one per move, its length the move's chance.
    set_probs(p) redraws them for chances p[x, y, a]; .arrows[(cell, a)] is one arrow."""

    def __init__(self, maze: Maze, probs: np.ndarray, color=ACCENT, **kwargs):
        super().__init__(**kwargs)
        self.maze, self.color = maze, color
        self.arrows = {}
        for c in FREE:
            if c == GOAL:
                continue
            for a in range(4):
                m = Polygon(*_arrow_pts(maze.cell_center(c), MOVE_DIRS[a], 0.1, maze.cell))
                m.set_stroke(width=0)
                self.arrows[(c, a)] = m
                self.add(m)
        self.set_probs(probs)

    def set_probs(self, probs: np.ndarray, highlight: dict | None = None) -> "PolicyArrows":
        cell = self.maze.cell
        lmax = 0.47 * cell
        for (c, a), m in self.arrows.items():
            p = float(probs[c[0], c[1], a])
            pts = _arrow_pts(self.maze.cell_center(c), MOVE_DIRS[a], max(lmax * p, 0.02), cell)
            m.set_points_as_corners([*pts, pts[0]])
            col = (highlight or {}).get((c, a), self.color)
            m.set_fill(col, opacity=0.30 + 0.70 * min(1.0, p / 0.6))
        self.probs = probs
        return self

    def morph(self, p_to: np.ndarray, run_time: float = 1.0, rate_func=smooth, highlight: dict | None = None) -> Animation:
        """Animate the arrows from their current chances to p_to."""
        p0 = np.array(self.probs)

        def upd(m, a):
            m.set_probs(p0 + (p_to - p0) * a, highlight if a < 1.0 else None)
        return UpdateFromAlphaFunc(self, upd, run_time=run_time, rate_func=rate_func)

    def morph_through(self, keyframes: list, run_time: float = 2.0, rate_func=linear) -> Animation:
        """Animate through a list of chance arrays (evenly spaced in time), e.g. snapshots of training."""
        ks = [np.array(k) for k in keyframes]

        def upd(m, a):
            x = a * (len(ks) - 1)
            i = min(int(x), len(ks) - 2)
            f = x - i
            m.set_probs(ks[i] + (ks[i + 1] - ks[i]) * f)
        return UpdateFromAlphaFunc(self, upd, run_time=run_time, rate_func=rate_func)


# Four bars for one cell's chances: left, up, down, right (left on the left, right on the right).
BAR_ORDER = [3, 0, 2, 1]


class ChanceBars(VGroup):
    """One cell's four chances as bars over arrow marks, in a card. set_probs(p4) with p4[a] for
    a in up, right, down, left. Attributes: .card, .bars, .marks"""

    def __init__(self, p4, width: float = 2.6, height: float = 2.3, max_h: float | None = None, **kwargs):
        super().__init__(**kwargs)
        self.card = _card(width, height, stroke=ACCENT, r=0.22, stroke_width=2.2)
        self.max_h = max_h or 0.64 * height
        bw = 0.10 * width
        self.base_y = -0.24 * height
        xs = np.linspace(-0.33 * width, 0.33 * width, 4)
        self.bars, self.marks = VGroup(), VGroup()
        for k, a in enumerate(BAR_ORDER):
            bar = _bar(bw, 0.1, ACCENT)
            bar.move_to(np.array([xs[k], self.base_y, 0]), aligned_edge=DOWN)
            self.bars.add(bar)
            mk = Arrow(ORIGIN, 0.34 * MOVE_DIRS[a], buff=0, thickness=3.2).set_fill(INK_2, 1).set_stroke(width=0)
            mk.move_to(np.array([xs[k], self.base_y - 0.30, 0]))
            self.marks.add(mk)
        self.xs, self.bw = xs, bw
        base = Line(np.array([-0.42 * width, self.base_y, 0]), np.array([0.42 * width, self.base_y, 0]))
        base.set_stroke(CARD_STROKE, width=2)
        self.add(self.card, base, self.bars, self.marks)
        self.p4 = np.array(p4, dtype=float)
        self._draw(self.p4)

    def _draw(self, p4) -> None:
        o = self.card.get_center() - np.array([0, 0, 0])
        for k, a in enumerate(BAR_ORDER):
            h = max(self.max_h * float(p4[a]), 0.02)
            nb = RoundedRectangle(width=self.bw, height=h, corner_radius=min(0.04, h / 2))
            nb.set_fill(ACCENT, 0.45 + 0.55 * min(1.0, float(p4[a]) / 0.6)).set_stroke(width=0)
            nb.move_to(o + np.array([self.xs[k], self.base_y, 0]), aligned_edge=DOWN)
            self.bars[k].become(nb)
        self.p4 = np.array(p4, dtype=float)

    def set_probs(self, p4) -> "ChanceBars":
        self._draw(p4)
        return self

    def morph(self, p_to, run_time: float = 1.0, rate_func=smooth) -> Animation:
        p0 = np.array(self.p4)
        p_to = np.array(p_to, dtype=float)

        def upd(m, a):
            m._draw(p0 + (p_to - p0) * a)
        return UpdateFromAlphaFunc(self, upd, run_time=run_time, rate_func=rate_func)

    def morph_through(self, keyframes: list, run_time: float = 2.0, rate_func=linear) -> Animation:
        ks = [np.array(k, dtype=float) for k in keyframes]

        def upd(m, a):
            x = a * (len(ks) - 1)
            i = min(int(x), len(ks) - 2)
            f = x - i
            m._draw(ks[i] + (ks[i + 1] - ks[i]) * f)
        return UpdateFromAlphaFunc(self, upd, run_time=run_time, rate_func=rate_func)


def learner_dot(cell: float = 0.8) -> VGroup:
    """The learner on the maze: a teal dot with a soft halo. Attributes: .core, .halo"""
    halo = Circle(radius=0.30 * cell).set_fill(ACCENT, 0.18).set_stroke(width=0)
    core = Circle(radius=0.17 * cell).set_fill(ACCENT, 1).set_stroke(INK, width=1.5, opacity=0.6)
    out = VGroup(halo, core)
    out.core, out.halo = core, halo
    return out


def trail_line(maze: Maze, path: list, color=ACCENT, opacity: float = 0.5, width: float = 4.0) -> VMobject:
    """The cells a try visited, as one polyline (bumps add nothing)."""
    pts = [maze.cell_center(path[0])]
    for c in path[1:]:
        p = maze.cell_center(c)
        if np.linalg.norm(p - pts[-1]) > 1e-6:
            pts.append(p)
    line = VMobject()
    line.set_points_as_corners(pts if len(pts) > 1 else [pts[0], pts[0] + 1e-3 * RIGHT])
    line.set_stroke(color, width=width, opacity=opacity).set_fill(opacity=0)
    return line


def walk_anim(dot: Mobject, maze: Maze, path: list, moves: list, step_time: float = 0.1,
              trail: VMobject | None = None) -> Animation:
    """One try as a single animation: the dot steps cell to cell; a move into a wall nudges it toward
    the wall and back. `trail` (a VMobject) is redrawn to follow the dot. One updater driven by time,
    so it is safe inside AnimationGroup / Succession (ManimGL begins every member at the start)."""
    n = len(moves)
    total = max(n * step_time, 0.05)
    cells = [maze.cell_center(c) for c in path]

    def upd(m, alpha):
        t = alpha * total
        k = min(int(t / step_time), n - 1) if n else 0
        f = (t - k * step_time) / step_time if n else 1.0
        f = float(np.clip(f, 0.0, 1.0))
        if n == 0:
            pos = cells[0]
        elif path[k] == path[k + 1]:
            d = MOVE_DIRS[moves[k]] * 0.17 * maze.cell
            pos = cells[k] + d * (1 - abs(2 * f - 1))
        else:
            pos = interpolate(cells[k], cells[k + 1], smooth(f))
        m.move_to(pos)
        if trail is not None:
            pts = [cells[0]]
            for j in range(1, k + 1):
                if np.linalg.norm(cells[j] - pts[-1]) > 1e-6:
                    pts.append(cells[j])
            if np.linalg.norm(pos - pts[-1]) > 1e-6:
                pts.append(pos)
            if len(pts) < 2:
                pts.append(pts[0] + 1e-3 * RIGHT)
            trail.set_points_as_corners(pts)
    return UpdateFromAlphaFunc(dot, upd, run_time=total, rate_func=linear)


def empty_trail(color=ACCENT, opacity: float = 0.45, width: float = 4.0) -> VMobject:
    t = VMobject()
    t.set_points_as_corners([ORIGIN, 1e-3 * RIGHT])
    t.set_stroke(color, width=width, opacity=opacity).set_fill(opacity=0)
    return t


# ----------------------------------------------------------------------------
# The master diagram: the RL loop
# ----------------------------------------------------------------------------
LEARNER_C = np.array([-3.7, 0.35, 0.0])
WORLD4_C = np.array([3.7, 0.35, 0.0])


def learner_box(width: float = 2.6, height: float = 1.8, p4=(0.25, 0.25, 0.25, 0.25)) -> VGroup:
    """The learner: a teal box (the house model box) with its four chance bars inside.
    Attributes: .box, .bars (a ChanceBars without its card), .p4"""
    box = _card(width, height, stroke=ACCENT, r=0.22 * height, stroke_width=3.0)
    cb = ChanceBars(p4, width=0.86 * width, height=0.86 * height)
    cb.card.set_opacity(0)
    cb.move_to(box)
    out = VGroup(box, cb)
    out.box, out.bars = box, cb
    return out


def world_card(width: float = 2.8, height: float = 2.4, content: Mobject | None = None) -> VGroup:
    """The world: an amber card holding whatever the learner acts on (the maze, the boat, people, the
    tests). Attributes: .card, .content (or None)"""
    card = _card(width, height, stroke=WARM, fill="#1c1a17", r=0.2, stroke_width=2.6)
    card.set_z_index(-1)                          # whatever is moved into the card shows on top of it
    out = VGroup(card)
    out.card, out.content = card, None
    if content is not None:
        content.set_max_width(0.82 * width).set_max_height(0.80 * height).move_to(card)
        out.add(content)
        out.content = content
    return out


def mini_maze(width: float = 2.2) -> VGroup:
    """A small copy of the maze (with its finished path of arrows) for the world card."""
    m = Maze(cell=1.0)
    run = rl_run()
    pa = PolicyArrows(m, run.probs[-1])
    g = VGroup(m, pa)
    g.set_width(width)
    return g


def loop_arc(a: np.ndarray, b: np.ndarray, color, bend: float = 0.9, thickness: float = 4.0) -> VGroup:
    """A curved arrow from a to b (bend > 0 bows it up for left->right). Attributes: .path, .tip"""
    path = ArcBetweenPoints(a, b, angle=-bend)
    path.set_stroke(color, width=thickness).set_fill(opacity=0)
    tip = Triangle().set_height(0.26).set_fill(color, 1).set_stroke(width=0)
    end_dir = path.get_points()[-1] - path.get_points()[-4]
    ang = np.arctan2(end_dir[1], end_dir[0])
    tip.rotate(ang - PI / 2).move_to(b)
    out = VGroup(path, tip)
    out.path, out.tip = path, tip
    return out


def loop_chip(text_ar: str, color, height: float = 0.74) -> VGroup:
    """A rounded chip with one of the loop's three words. Attributes: .chip, .text"""
    t = ar_text(text_ar, font_size=44, color=color)
    t.set_height(0.56 * height) if t.get_height() > 0.56 * height else None
    chip = RoundedRectangle(width=t.get_width() + 0.6 * height, height=height, corner_radius=height / 2)
    chip.set_fill(CARD_FILL, 1).set_stroke(color, width=2.0)
    t.move_to(chip)
    out = VGroup(chip, t)
    out.chip, out.text = chip, t
    return out


def rl_loop(content: Mobject | None = None, p4=(0.25, 0.25, 0.25, 0.25)) -> SimpleNamespace:
    """The master diagram's parts at their places (not added to the scene):
    .learner .world .act (top arrow, teal) .score (bottom arrow, amber) and the three chips
    .chip_try .chip_score .chip_grow."""
    lr = learner_box(p4=p4).move_to(LEARNER_C)
    wd = world_card(content=content).move_to(WORLD4_C)
    a0, a1 = lr.get_corner(UR) + np.array([0.05, -0.25, 0]), wd.get_corner(UL) + np.array([-0.05, -0.25, 0])
    act = loop_arc(a0, a1, ACCENT, bend=0.75)
    b0, b1 = wd.get_corner(DL) + np.array([-0.05, 0.25, 0]), lr.get_corner(DR) + np.array([0.05, 0.25, 0])
    score = loop_arc(b0, b1, WARM, bend=0.75)
    chip_try = loop_chip(LOOP_TRY_AR, ACCENT).move_to(act.path.point_from_proportion(0.5) + 0.55 * UP)
    chip_score = loop_chip(LOOP_SCORE_AR, WARM).move_to(score.path.point_from_proportion(0.5) + 0.55 * DOWN)
    chip_grow = loop_chip(LOOP_GROW_AR, ACCENT).next_to(lr, DOWN, buff=0.35)
    return SimpleNamespace(learner=lr, world=wd, act=act, score=score, chip_try=chip_try,
                           chip_score=chip_score, chip_grow=chip_grow)


def score_star(size: float = 0.42) -> VMobject:
    """The reward as it travels: an amber star."""
    return icon_star(size, WARM)


# ----------------------------------------------------------------------------
# Scenes
# ----------------------------------------------------------------------------
class RLScene(AgentScene):
    """AgentScene (narration timing, word anchors, seamless cuts) with a few helpers for this video."""

    def fill_line(self, *anims, minimum: float = 0.3, lead: float = 0.0, **kwargs) -> None:
        """Play `anims` stretched over what is left of the current line (minus `lead`)."""
        self.play(*anims, run_time=max(minimum, self.line_left() - lead), **kwargs)

    def hold(self, lead: float = 0.05) -> None:
        """Wait out the rest of the line and its pause (minus `lead`)."""
        t = self.hold_left() - lead
        if t > 1e-3:
            self.wait(t)

    def on_screen(self) -> list:
        """Everything in the scene except the camera frame."""
        return [m for m in self.mobjects if m is not self.frame]

    def fade_all(self, run_time: float = 0.4, **kwargs) -> None:
        """Fade out everything on screen (the camera frame stays)."""
        ms = self.on_screen()
        if ms:
            self.play(*[FadeOut(m, **kwargs) for m in ms], run_time=run_time)


# ----------------------------------------------------------------------------
# The coin: the same maze with a "helpful" extra reward that gets farmed (a real run too)
# ----------------------------------------------------------------------------
COIN = (2, 0)
COIN_SEED, COIN_EPISODES, COIN_T, COIN_ALPHA, COIN_GAMMA, COIN_R, STAR_R = 2, 500, 40, 0.4, 0.95, 1.0, 3.0


@lru_cache(maxsize=2)
def coin_run(seed: int = COIN_SEED, episodes: int = COIN_EPISODES, T: int = COIN_T) -> SimpleNamespace:
    """REINFORCE with a baseline on the maze plus a coin: a point each time the dot steps onto the coin
    (it comes back once the dot steps off), the star worth STAR_R and ending the try. Learning from
    scratch, the dot learns to step on and off the coin for the whole try and never goes to the star.
    Returns .probs[k] (before try k; last = final), .paths, .moves, .coins[k], .reached[k]."""
    rng = np.random.default_rng(seed)
    theta = np.zeros((COLS, ROWS, 4))
    probs, paths, moves, coins, reached = [], [], [], [], []
    for _ in range(episodes):
        probs.append(_softmax(theta))
        s, path, acts, rews, on, n_coin = START, [START], [], [], True, 0
        for _t in range(T):
            a = int(rng.choice(4, p=_softmax(theta[s])))
            s2 = maze_step(s, a)
            r = 0.0
            if s2 == COIN and on and s2 != s:
                r += COIN_R
                on = False
                n_coin += 1
            if s2 != COIN:
                on = True
            if s2 == GOAL:
                r += STAR_R
            acts.append(a)
            rews.append(r)
            path.append(s2)
            s = s2
            if s == GOAL:
                break
        G, Gs = 0.0, []
        for r in reversed(rews):
            G = r + COIN_GAMMA * G
            Gs.append(G)
        Gs = Gs[::-1]
        b = float(np.mean(Gs))
        for t, a in enumerate(acts):
            st = path[t]
            g = -_softmax(theta[st])
            g[a] += 1.0
            theta[st] += COIN_ALPHA * (Gs[t] - b) * g / max(1, len(acts)) * 10
        paths.append(path)
        moves.append(acts)
        coins.append(n_coin)
        reached.append(s == GOAL)
    probs.append(_softmax(theta))
    return SimpleNamespace(probs=probs, paths=paths, moves=moves, coins=coins, reached=reached)


def coin_icon(size: float = 0.5) -> VGroup:
    """A gold coin (no number on it)."""
    outer = Circle(radius=size / 2).set_fill(WARM, 1).set_stroke("#b5732f", width=2.5)
    inner = Circle(radius=0.30 * size).set_fill(opacity=0).set_stroke("#ffd29a", width=2.0, opacity=0.9)
    shine = Arc(start_angle=PI * 0.6, angle=PI * 0.5, radius=0.38 * size).set_stroke("#fff1d6", width=2.0, opacity=0.8)
    return VGroup(outer, inner, shine)


class Counter(VGroup):
    """An icon or label with a number beside it (Latin digits, like video 3's years), e.g. the tries
    or the coins. set_value(n). Attributes: .label, .num"""

    def __init__(self, label: Mobject, value: int = 0, font_size: int = 34, color=INK_2, **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self.num = Integer(value, font_size=font_size, text_config=dict(font=LATIN_FONT))
        self.num.set_fill(color)
        self.add(label, self.num)
        self._arrange()

    def _arrange(self):
        self.num.next_to(self.label, LEFT, buff=0.18)

    def set_value(self, n: int) -> "Counter":
        self.num.set_value(int(n))
        self._arrange()
        return self


def try_counter(n: int = 1) -> Counter:
    return Counter(ar_text(TRY_AR, 32, INK_2), n)


# ----------------------------------------------------------------------------
# Small labels
# ----------------------------------------------------------------------------
def name_chip(s: str, height: float = 0.5, color=INK_2, arabic: bool = False) -> VGroup:
    """A small rounded chip with a name or a year («GPT-4», «2016», «حَكَم»). Attributes: .chip, .text"""
    t = ar_text(s, 30, color) if arabic else latin(s, 28, color)
    t.set_height(0.46 * height) if not arabic else t.set_height(min(t.get_height(), 0.62 * height))
    chip = RoundedRectangle(width=t.get_width() + 0.55 * height, height=height, corner_radius=height / 2)
    chip.set_fill(CARD_FILL, 1).set_stroke(color, width=1.6)
    t.move_to(chip)
    out = VGroup(chip, t)
    out.chip, out.text = chip, t
    return out


def label_ar(s: str, size: int = 30, color=INK_2) -> Text:
    return ar_text(s, size, color)


# ----------------------------------------------------------------------------
# The boat race (CoastRunners, drawn from above)
# ----------------------------------------------------------------------------
def boat(length: float = 0.55, color=ACCENT) -> VGroup:
    """A small hull seen from above, pointing RIGHT; rotate to steer. Attributes: .hull, .deck"""
    L, W = length, 0.42 * length
    hull = VMobject()
    hull.set_points_smoothly([np.array([L / 2, 0, 0]), np.array([0.05 * L, W / 2, 0]), np.array([-L / 2, 0.40 * W, 0]),
                              np.array([-L / 2, -0.40 * W, 0]), np.array([0.05 * L, -W / 2, 0]), np.array([L / 2, 0, 0])])
    hull.set_fill(color, 1).set_stroke(INK, width=1.2, opacity=0.5)
    deck = RoundedRectangle(width=0.30 * L, height=0.45 * W, corner_radius=0.08 * L).set_fill(BG, 0.55).set_stroke(width=0)
    deck.shift(0.05 * L * LEFT)
    out = VGroup(hull, deck)
    out.hull, out.deck = hull, deck
    return out


def flame(size: float = 0.32) -> VGroup:
    """A small cartoon flame (two tear-drops)."""
    def drop(h, color):
        d = VMobject()
        d.set_points_smoothly([np.array([0, h, 0]), np.array([0.32 * h, 0.15 * h, 0]), np.array([0.2 * h, -0.25 * h, 0]),
                               np.array([0, -0.32 * h, 0]), np.array([-0.2 * h, -0.25 * h, 0]),
                               np.array([-0.32 * h, 0.15 * h, 0]), np.array([0, h, 0])])
        d.set_fill(color, 1).set_stroke(width=0)
        return d
    outer = drop(size, FLAME)
    inner = drop(0.55 * size, FLAME_CORE).shift(0.12 * size * DOWN)
    return VGroup(outer, inner)


def target_ring(size: float = 0.36) -> VGroup:
    """A floating target on the course (amber ring)."""
    a = Circle(radius=size / 2).set_fill(opacity=0).set_stroke(WARM, width=4)
    b = Dot(radius=0.12 * size).set_fill(WARM, 1)
    return VGroup(a, b)


RACE_C = np.array([0.0, -0.15, 0])


def _round_loop(w: float, h: float, r: float, center) -> VMobject:
    """A clockwise rounded-rectangle path that starts at the middle of its top edge."""
    c = np.array(center, dtype=float)
    x0, x1, y0, y1 = c[0] - w / 2, c[0] + w / 2, c[1] - h / 2, c[1] + h / 2
    P = lambda x, y: np.array([x, y, 0.0])
    p = VMobject()
    p.start_new_path(P(c[0], y1))
    p.add_line_to(P(x1 - r, y1))
    p.add_quadratic_bezier_curve_to(P(x1, y1), P(x1, y1 - r))
    p.add_line_to(P(x1, y0 + r))
    p.add_quadratic_bezier_curve_to(P(x1, y0), P(x1 - r, y0))
    p.add_line_to(P(x0 + r, y0))
    p.add_quadratic_bezier_curve_to(P(x0, y0), P(x0, y0 + r))
    p.add_line_to(P(x0, y1 - r))
    p.add_quadratic_bezier_curve_to(P(x0, y1), P(x0 + r, y1))
    p.add_line_to(P(c[0], y1))
    return p


def race_course(width: float = 10.4, height: float = 5.6, center=RACE_C) -> SimpleNamespace:
    """The race seen from above: the water, the course (a clockwise loop from the finish line at the
    top), an island inside it, and the lagoon: a bay inside the loop's right side where three targets
    keep coming back. .water .course (dashed) .course_path .island .finish .lagoon .lagoon_c .lagoon_r .targets"""
    c = np.array(center, dtype=float)
    k = width / 10.4                                   # everything scales with the width
    water = RoundedRectangle(width=width, height=height, corner_radius=1.0 * k).set_fill(WATER, 1)
    water.set_stroke(WATER_EDGE, width=3).move_to(c)
    cw, ch = width - 1.5 * k, height - 1.4 * k
    path = _round_loop(cw, ch, 0.9 * k, c)
    course = DashedVMobject(path.copy(), num_dashes=80, positive_space_ratio=0.45)
    course.set_stroke(INK_2, width=2, opacity=0.40)
    island = RoundedRectangle(width=cw - 4.6 * k, height=ch - 2.4 * k, corner_radius=0.5 * k)
    island.move_to(c + 0.7 * k * LEFT).set_fill("#14261b", 1).set_stroke("#2e5a3c", width=2)
    top_mid = c + np.array([0, ch / 2, 0])
    finish = VGroup()
    for i in range(2):
        for j in range(6):
            sq = Square(0.11 * k).set_stroke(width=0).set_fill(INK if (i + j) % 2 == 0 else BG, 1)
            sq.move_to(top_mid + np.array([0.11 * k * (i - 0.5), 0.33 * k - 0.11 * k * j, 0]))
            finish.add(sq)
    lag_r = 0.82 * k
    lag_c = c + np.array([cw / 2 - 1.55 * k, -0.15 * k, 0])
    lagoon = Circle(radius=lag_r).move_to(lag_c).set_fill("#123048", 1).set_stroke(WATER_EDGE, width=2, opacity=0.9)
    t_r = 0.52 * k
    tpos = [lag_c + t_r * np.array([np.cos(a), np.sin(a), 0]) for a in (PI / 2, PI / 2 + 2 * PI / 3, PI / 2 + 4 * PI / 3)]
    targets = VGroup(*[target_ring(0.30 * k).move_to(p) for p in tpos])
    return SimpleNamespace(water=water, course=course, course_path=path, island=island, finish=finish,
                           lagoon=lagoon, lagoon_c=lag_c, lagoon_r=t_r, targets=targets, center=c, k=k)


def along(path: VMobject, mob: Mobject, alpha0: float, alpha1: float, run_time: float, rate_func=linear,
          heading: bool = True) -> Animation:
    """Move `mob` along `path` from proportion alpha0 to alpha1 (both may exceed 1: wraps), turning it
    to face the way it goes."""
    def upd(m, a):
        t = alpha0 + (alpha1 - alpha0) * a
        p = path.point_from_proportion(t % 1.0)
        q = path.point_from_proportion((t + 0.004) % 1.0)
        m.move_to(p)
        if heading:
            ang = np.arctan2(q[1] - p[1], q[0] - p[0])
            cur = getattr(m, "_heading", 0.0)
            m.rotate(ang - cur, about_point=m.get_center())
            m._heading = ang
    return UpdateFromAlphaFunc(mob, upd, run_time=run_time, rate_func=rate_func)


def circle_path(center, r: float, start: float = -PI / 2, ccw: bool = True) -> VMobject:
    """A circle as a path starting at angle `start` (for a boat going round the lagoon)."""
    c = Circle(radius=r).move_to(center)
    c.rotate(start, about_point=np.array(center, dtype=float))
    if not ccw:
        c.flip(RIGHT, about_point=np.array(center, dtype=float))
    return c


# ----------------------------------------------------------------------------
# The CAPTCHA
# ----------------------------------------------------------------------------
def checkbox_card(width: float = 4.6, checked: bool = False) -> VGroup:
    """The 'I'm not a robot' checkbox: a light card, a square box, the label. Drawn generic (no logo).
    Attributes: .card, .box, .tick, .label"""
    h = 0.26 * width
    card = RoundedRectangle(width=width, height=h, corner_radius=0.06 * width).set_fill("#f4f4f2", 1)
    card.set_stroke("#d0d0cc", width=2)
    box = RoundedRectangle(width=0.42 * h, height=0.42 * h, corner_radius=0.05 * h).set_fill(WHITE, 1)
    box.set_stroke("#8a8a86", width=3)
    box.move_to(card.get_right() + 0.42 * h * LEFT)
    lab = ar_text(CAPTCHA_AR, 40, "#1d1d1b")
    lab.set_height(min(lab.get_height(), 0.30 * h))
    lab.next_to(box, LEFT, buff=0.30 * h)
    tick = Polyline(np.array([-0.4, 0.0, 0]), np.array([-0.12, -0.32, 0]), np.array([0.44, 0.36, 0]))
    tick.set_stroke("#1a9b4b", width=7).set_fill(opacity=0).scale(0.42 * h).move_to(box)
    if not checked:
        tick.set_stroke(opacity=0)
    out = VGroup(card, box, lab, tick)            # the tick rides along, hidden until checked
    out.card, out.box, out.label, out.tick = card, box, lab, tick
    return out


def tick_box(cb: VGroup, run_time: float = 0.4) -> Animation:
    """Check the checkbox: the tick draws itself in."""
    cb.tick.set_stroke(opacity=1)
    return ShowCreation(cb.tick, run_time=run_time)


def ai_bubble(text_ar: str, width: float = 5.0, color=ACCENT, font_size: int = 32) -> VGroup:
    """A message from the AI: a dark bubble with a teal edge and a tail at the bottom left.
    Attributes: .bubble, .text"""
    t = ar_text(text_ar, font_size, INK)
    t.set_max_width(width - 0.6)
    w, h = t.get_width() + 0.6, t.get_height() + 0.42
    body = RoundedRectangle(width=w, height=h, corner_radius=min(0.28, h / 2))
    l, b = body.get_left()[0], body.get_bottom()[1]
    tail = Polygon(np.array([l + 0.30, b + 0.02, 0]), np.array([l - 0.10, b - 0.22, 0]), np.array([l + 0.62, b + 0.02, 0]))
    shape = Union(body, tail)
    shape.set_fill(CARD_FILL, 1).set_stroke(color, width=2.4)
    t.move_to(body)
    out = VGroup(shape, t)
    out.bubble, out.text = shape, t
    return out


def person_icon(size: float = 0.9, color=INK_2) -> VGroup:
    """A plain person glyph (head + shoulders), the generic UI icon."""
    head = Circle(radius=0.2 * size).set_fill(color, 1).set_stroke(width=0).shift(0.2 * size * UP)
    body = Arc(start_angle=0, angle=PI, radius=0.36 * size).set_fill(color, 1).set_stroke(width=0)
    body.add_line_to(body.get_start())
    body.shift(0.30 * size * DOWN)
    return VGroup(head, body)


def headset_person(size: float = 0.9, color=HANDS) -> VGroup:
    """The researcher in the middle: a person glyph with a small headset arc."""
    p = person_icon(size, color)
    arc = Arc(start_angle=0.15 * PI, angle=0.7 * PI, radius=0.27 * size).set_stroke(INK, width=3)
    arc.move_to(p[0].get_center() + 0.05 * size * UP)
    mic = Line(arc.get_start(), arc.get_start() + np.array([-0.05, -0.18, 0]) * size).set_stroke(INK, width=3)
    return VGroup(p, arc, mic)


def thought_note(lines_ar: list[str], width: float = 4.8, color=ACCENT) -> VGroup:
    """The written reasoning: a dashed-edge note (the model's scratchpad, shown when prompted).
    Attributes: .card, .lines"""
    texts = VGroup(*[ar_text(s, 30, INK) for s in lines_ar]).arrange(DOWN, buff=0.18, aligned_edge=RIGHT)
    texts.set_max_width(width - 0.6)
    card = RoundedRectangle(width=width, height=texts.get_height() + 0.6, corner_radius=0.18)
    card.set_fill(SCRATCH_FILL, 0.95).set_stroke(opacity=0)
    edge = DashedVMobject(card.copy().set_stroke(color, width=2.2, opacity=0.9), num_dashes=46, positive_space_ratio=0.6)
    texts.move_to(card).align_to(card.get_right() + 0.3 * LEFT, RIGHT)
    out = VGroup(card, edge, texts)
    out.card, out.edge, out.lines = card, edge, texts
    return out


# ----------------------------------------------------------------------------
# Hide-and-seek (from above)
# ----------------------------------------------------------------------------
def agent_token(color=ACCENT, size: float = 0.36) -> VGroup:
    """A hide-and-seek player: a disc with a small notch showing where it faces (RIGHT)."""
    disc = Circle(radius=size / 2).set_fill(color, 1).set_stroke(INK, width=1.2, opacity=0.5)
    nose = Dot(radius=0.07 * size).set_fill(BG, 0.8).move_to(disc.get_right() + 0.14 * size * LEFT)
    return VGroup(disc, nose)


def _p3(p) -> np.ndarray:
    p = np.array(p, dtype=float).ravel()
    return np.array([p[0], p[1], p[2] if p.size > 2 else 0.0])


def wall_seg(a, b, width: float = 0.16, color=WALL_FILL) -> Rectangle:
    a, b = _p3(a), _p3(b)
    d = b - a
    r = Rectangle(width=max(np.linalg.norm(d), 1e-3), height=width).set_fill(color, 1).set_stroke(width=0)
    r.rotate(np.arctan2(d[1], d[0])).move_to((a + b) / 2)
    return r


def crate(size: float = 0.42, color="#c08a52") -> VGroup:
    sq = Square(size).set_fill(color, 1).set_stroke("#7c5530", width=2)
    x1 = Line(sq.get_corner(UL), sq.get_corner(DR)).set_stroke("#7c5530", width=1.5)
    x2 = Line(sq.get_corner(UR), sq.get_corner(DL)).set_stroke("#7c5530", width=1.5)
    return VGroup(sq, x1, x2)


def ramp_icon(size: float = 0.55, color="#7d8aa5") -> VGroup:
    """A ramp from above: a rectangle with chevrons pointing up the slope (RIGHT)."""
    r = Rectangle(width=size, height=0.6 * size).set_fill(color, 1).set_stroke(INK_2, width=1.2)
    chev = VGroup(*[Polyline(np.array([-0.06, 0.12, 0]), np.array([0.06, 0, 0]), np.array([-0.06, -0.12, 0]))
                    .set_stroke(BG, width=2.4).set_fill(opacity=0).shift(np.array([dx, 0, 0])) for dx in (-0.12, 0.0, 0.12)])
    chev.scale(size / 0.55).move_to(r)
    return VGroup(r, chev)


# ----------------------------------------------------------------------------
# Tetris
# ----------------------------------------------------------------------------
TETRIS_COLS, TETRIS_ROWS = 10, 18
_T_COLORS = ["#5fb3f0", "#f2d06b", "#8e7cf0", "#46c37b", WARM, "#e5484d", ACCENT]


def tetris_board(cell: float = 0.26, fill_rows: int = 15, seed: int = 4) -> VGroup:
    """A Tetris well stacked almost to the top (a jagged stack, one free gap per row).
    Attributes: .frame, .blocks, .cell"""
    rng = np.random.default_rng(seed)
    frame = Rectangle(width=TETRIS_COLS * cell + 0.08, height=TETRIS_ROWS * cell + 0.08).set_fill(BG, 1)
    frame.set_stroke(CARD_STROKE, width=3)
    blocks = VGroup()
    x0 = -TETRIS_COLS * cell / 2 + cell / 2
    y0 = -TETRIS_ROWS * cell / 2 + cell / 2
    for r in range(fill_rows):
        gaps = set(rng.choice(TETRIS_COLS, size=1 + (r > fill_rows - 4), replace=False).tolist())
        for c in range(TETRIS_COLS):
            if c in gaps:
                continue
            col = _T_COLORS[int(rng.integers(len(_T_COLORS)))]
            sq = Square(cell * 0.92).set_fill(col, 0.85).set_stroke(BG, width=1)
            sq.move_to(np.array([x0 + c * cell, y0 + r * cell, 0]))
            blocks.add(sq)
    out = VGroup(frame, blocks)
    out.frame, out.blocks, out.cell = frame, blocks, cell
    return out


def pause_icon(size: float = 1.2, color=INK) -> VGroup:
    bars = VGroup(*[RoundedRectangle(width=0.22 * size, height=0.8 * size, corner_radius=0.05 * size)
                    .set_fill(color, 1).set_stroke(width=0) for _ in range(2)]).arrange(RIGHT, buff=0.2 * size)
    ring = Circle(radius=0.68 * size).set_fill(BG, 0.55).set_stroke(color, width=4)
    return VGroup(ring, bars)


# ----------------------------------------------------------------------------
# People as the reward: answers, the backflip figure, the robot hand, the judge
# ----------------------------------------------------------------------------
def answer_card(width: float = 2.6, n: int = 4, seed: int = 1, color=INK_2) -> VGroup:
    """A chat answer: a card with abstract written lines (right-aligned). Attributes: .card, .lines"""
    lines = text_lines(width - 0.5, n=n, height=0.09, gap=0.16, color=color, seed=seed)
    card = _card(width, lines.get_height() + 0.55, stroke=CARD_STROKE, r=0.2)
    lines.move_to(card).align_to(card.get_right() + 0.25 * LEFT, RIGHT)
    out = VGroup(card, lines)
    out.card, out.lines = card, lines
    return out


def stick_figure(size: float = 1.0, color=INK_2) -> VGroup:
    """A simple jointed figure (a simulated robot body): a torso with a head disc and two-segment legs.
    Not a character: no face. Attributes: .torso, .head, .legs"""
    torso = Line(ORIGIN, 0.5 * size * UP).set_stroke(color, width=6)
    head = Circle(radius=0.11 * size).set_fill(color, 1).set_stroke(width=0).move_to(0.62 * size * UP)
    legs = VGroup(
        Polyline(ORIGIN, np.array([-0.14, -0.26, 0]) * size, np.array([-0.10, -0.52, 0]) * size),
        Polyline(ORIGIN, np.array([0.14, -0.26, 0]) * size, np.array([0.10, -0.52, 0]) * size),
    ).set_stroke(color, width=6).set_fill(opacity=0)
    arms = VGroup(Line(0.42 * size * UP, np.array([-0.24, 0.20, 0]) * size),
                  Line(0.42 * size * UP, np.array([0.24, 0.20, 0]) * size)).set_stroke(color, width=5)
    out = VGroup(legs, torso, arms, head)
    out.torso, out.head, out.legs = torso, head, legs
    return out


def gripper(size: float = 1.0, color=INK_2) -> VGroup:
    """A two-finger robot hand from the side, opening to the RIGHT. Attributes: .arm, .fingers"""
    arm = RoundedRectangle(width=1.1 * size, height=0.18 * size, corner_radius=0.06 * size).set_fill(color, 1)
    arm.set_stroke(width=0)
    palm = RoundedRectangle(width=0.16 * size, height=0.5 * size, corner_radius=0.04 * size).set_fill(color, 1)
    palm.set_stroke(width=0).next_to(arm, RIGHT, buff=0)
    f1 = Polyline(palm.get_corner(UR), palm.get_corner(UR) + np.array([0.32, 0.0, 0]) * size,
                  palm.get_corner(UR) + np.array([0.42, -0.10, 0]) * size).set_stroke(color, width=7).set_fill(opacity=0)
    f2 = Polyline(palm.get_corner(DR), palm.get_corner(DR) + np.array([0.32, 0.0, 0]) * size,
                  palm.get_corner(DR) + np.array([0.42, 0.10, 0]) * size).set_stroke(color, width=7).set_fill(opacity=0)
    out = VGroup(arm, palm, f1, f2)
    out.arm, out.fingers = arm, VGroup(f1, f2)
    return out


def ball_icon(size: float = 0.5, color="#e8e2d0") -> VGroup:
    b = Circle(radius=size / 2).set_fill(color, 1).set_stroke("#9b9586", width=2)
    seam = Arc(start_angle=-PI / 3, angle=2 * PI / 3, radius=0.42 * size).set_stroke("#b5ae9c", width=2)
    seam.move_to(b.get_center() + 0.12 * size * LEFT)
    return VGroup(b, seam)


def camera_icon(size: float = 0.8, color=INK_2) -> VGroup:
    """A camera from the side, looking RIGHT (body + lens)."""
    body = RoundedRectangle(width=0.8 * size, height=0.5 * size, corner_radius=0.08 * size).set_fill(CARD_FILL, 1)
    body.set_stroke(color, width=2.4)
    lens = Polygon(np.array([0, 0.12, 0]) * size, np.array([0.28, 0.2, 0]) * size, np.array([0.28, -0.2, 0]) * size,
                   np.array([0, -0.12, 0]) * size).set_fill(CARD_FILL, 1).set_stroke(color, width=2.4)
    lens.next_to(body, RIGHT, buff=0)
    dot = Dot(radius=0.05 * size).set_fill(SEEKER, 1).move_to(body.get_corner(UL) + np.array([0.14, -0.12, 0]) * size)
    return VGroup(body, lens, dot)


def scale_icon(size: float = 0.7, color=INK_2) -> VGroup:
    """A balance scale (the judge's mark)."""
    post = Line(0.30 * size * DOWN, 0.34 * size * UP).set_stroke(color, width=4)
    beam = Line(0.36 * size * LEFT + 0.30 * size * UP, 0.36 * size * RIGHT + 0.30 * size * UP).set_stroke(color, width=4)
    base = Line(0.18 * size * LEFT + 0.30 * size * DOWN, 0.18 * size * RIGHT + 0.30 * size * DOWN).set_stroke(color, width=4)
    pans = VGroup()
    for sx in (-1, 1):
        pan = Arc(start_angle=PI, angle=PI, radius=0.13 * size).set_stroke(color, width=3)
        pan.move_to(np.array([sx * 0.36 * size, 0.08 * size, 0]))
        strings = VGroup(Line(np.array([sx * 0.36, 0.30, 0]) * size, pan.get_start()),
                         Line(np.array([sx * 0.36, 0.30, 0]) * size, pan.get_end())).set_stroke(color, width=1.5)
        pans.add(VGroup(pan, strings))
    return VGroup(post, beam, base, pans)


def judge_box(width: float = 2.2, height: float = 1.4) -> VGroup:
    """The reward model: a model box (teal-grey) with a scale, labelled «حَكَم». Attributes: .box, .mark, .label"""
    box = _card(width, height, stroke=INK_2, r=0.22 * height, stroke_width=2.6)
    mark = scale_icon(0.58 * height).move_to(box)
    lab = ar_text(JUDGE_AR, 30, INK_2).next_to(box, DOWN, buff=0.14)
    out = VGroup(box, mark, lab)
    out.box, out.mark, out.label = box, mark, lab
    return out


def sparkle(size: float = 0.3, color=WARM) -> VMobject:
    """A four-point sparkle (praise)."""
    s = size / 2
    pts = []
    for k in range(8):
        r = s if k % 2 == 0 else 0.28 * s
        a = k * PI / 4
        pts.append(np.array([r * np.cos(a), r * np.sin(a), 0]))
    m = Polygon(*pts).set_fill(color, 1).set_stroke(width=0)
    return m


# ----------------------------------------------------------------------------
# Checkable rewards, tests and the scratchpad
# ----------------------------------------------------------------------------
def code_card(width: float = 3.0, n: int = 6, seed: int = 7, title: str | None = CODE_AR) -> VGroup:
    """A code file: a card with indented abstract lines (left-aligned, like code). Attributes: .card, .lines, .title"""
    rng = np.random.default_rng(seed)
    lines = VGroup()
    for i in range(n):
        indent = [0, 1, 1, 2, 1, 0, 1, 2][i % 8]
        w = (width - 0.7 - 0.25 * indent) * (0.45 + 0.5 * rng.random())
        b = _bar(w, 0.085, INK_2, 0.6)
        lines.add(b)
    lines.arrange(DOWN, buff=0.17, aligned_edge=LEFT)
    for i, b in enumerate(lines):
        indent = [0, 1, 1, 2, 1, 0, 1, 2][i % 8]
        b.shift(0.25 * indent * RIGHT)
    card = _card(width, lines.get_height() + 0.75, stroke=CARD_STROKE, r=0.16)
    lines.move_to(card).align_to(card.get_left() + 0.3 * RIGHT, LEFT).shift(0.12 * DOWN)
    out = VGroup(card, lines)
    out.card, out.lines, out.title = card, lines, None
    if title:
        t = ar_text(title, 26, INK_2).next_to(card, UP, buff=0.12)
        out.add(t)
        out.title = t
    return out


def check_mark(size: float = 0.36, color=GREEN) -> VMobject:
    return icon_check(size, color)


def cross_mark(size: float = 0.32, color=RED) -> VGroup:
    return icon_cross(size, color)


def tests_card(width: float = 2.8, n: int = 3, passed: tuple = (False, False, False)) -> VGroup:
    """The tests: rows of (abstract line, ✗/✓). Attributes: .card, .rows, .marks, .title"""
    rows, marks = VGroup(), VGroup()
    for i in range(n):
        line = _bar((width - 1.2) * (0.6 + 0.3 * ((i * 37) % 10) / 10), 0.09, INK_2, 0.6)
        mk = check_mark(0.30) if passed[i] else cross_mark(0.26)
        row = VGroup(line, mk)
        mk.next_to(line, LEFT, buff=0.3)
        rows.add(row)
        marks.add(mk)
    rows.arrange(DOWN, buff=0.34, aligned_edge=RIGHT)
    card = _card(width, rows.get_height() + 0.7, stroke=CARD_STROKE, r=0.16)
    rows.move_to(card).align_to(card.get_right() + 0.3 * LEFT, RIGHT)
    title = ar_text(TESTS_AR, 26, INK_2).next_to(card, UP, buff=0.12)
    out = VGroup(card, rows, title)
    out.card, out.rows, out.marks, out.title = card, rows, marks, title
    return out


def scratchpad(width: float = 3.6, n: int = 5, seed: int = 11) -> VGroup:
    """The model's scratchpad: a page with written lines and its title «مسودّة». Attributes: .card, .lines, .title"""
    lines = text_lines(width - 0.6, n=n, height=0.08, gap=0.2, color=ACCENT, opacity=0.6, seed=seed)
    card = _card(width, lines.get_height() + 0.8, stroke=ACCENT, fill=SCRATCH_FILL, r=0.14, stroke_width=1.8)
    lines.move_to(card).align_to(card.get_right() + 0.3 * LEFT, RIGHT).shift(0.1 * DOWN)
    title = ar_text(SCRATCH_AR, 26, ACCENT).next_to(card, UP, buff=0.12)
    out = VGroup(card, lines, title)
    out.card, out.lines, out.title = card, lines, title
    return out


def eye_icon(size: float = 0.6, color=INK) -> VGroup:
    """An eye (the monitor)."""
    up = Arc(start_angle=PI * 0.15, angle=PI * 0.7, radius=0.55 * size).set_stroke(color, width=3)
    lo = Arc(start_angle=-PI * 0.85, angle=PI * 0.7, radius=0.55 * size).set_stroke(color, width=3)
    up.shift(0.22 * size * DOWN)
    lo.shift(0.22 * size * UP)
    iris = Circle(radius=0.16 * size).set_fill(ACCENT, 1).set_stroke(width=0)
    pupil = Dot(radius=0.07 * size).set_fill(BG, 1)
    return VGroup(up, lo, iris, pupil)


def monitor_box(width: float = 1.8, height: float = 1.1) -> VGroup:
    """The watching model: a smaller model box with an eye. Attributes: .box, .eye"""
    box = _card(width, height, stroke=ACCENT, r=0.2 * height, stroke_width=2.4)
    eye = eye_icon(0.62 * height).move_to(box)
    out = VGroup(box, eye)
    out.box, out.eye = box, eye
    return out


def rule_text(scale: float = 1.0) -> VGroup:
    """The thesis, two lines: «بيتعلّم اللي منكافئو عليه» / «مو اللي منقصدو»."""
    a = ar_text(RULE_AR[0], 52, INK)
    b = ar_text(RULE_AR[1], 52, ACCENT)
    g = VGroup(a, b).arrange(DOWN, buff=0.28)
    g.scale(scale)
    return g


def pixel_game(width: float = 2.2) -> VGroup:
    """An abstract pixel game (rows of bricks, a ball, a paddle): stands for Atari."""
    cols, rows = 10, 4
    cw = width / cols
    bricks = VGroup()
    colors = ["#e5484d", WARM, "#f2d06b", GREEN]
    for r in range(rows):
        for c in range(cols):
            sq = Rectangle(width=cw * 0.9, height=cw * 0.45).set_fill(colors[r], 1).set_stroke(width=0)
            sq.move_to(np.array([-width / 2 + cw * (c + 0.5), 0.5 * width * 0.6 - r * cw * 0.55, 0]))
            bricks.add(sq)
    paddle = Rectangle(width=cw * 2.2, height=cw * 0.35).set_fill(INK, 1).set_stroke(width=0)
    paddle.move_to(np.array([0.1 * width, -0.42 * width * 0.6 - 0.1, 0]))
    ball = Square(cw * 0.4).set_fill(INK, 1).set_stroke(width=0).move_to(np.array([-0.05 * width, -0.05 * width, 0]))
    return VGroup(bricks, paddle, ball)


def go_board(width: float = 2.0, n: int = 9, seed: int = 37) -> VGroup:
    """A small Go board with a few stones."""
    rng = np.random.default_rng(seed)
    board = Square(width).set_fill("#c9a46a", 1).set_stroke("#8a6a3a", width=2)
    grid = VGroup()
    step = width * 0.9 / (n - 1)
    o = np.array([-width * 0.45, -width * 0.45, 0])
    for i in range(n):
        grid.add(Line(o + np.array([0, i * step, 0]), o + np.array([(n - 1) * step, i * step, 0])).set_stroke("#5a4320", width=1.2))
        grid.add(Line(o + np.array([i * step, 0, 0]), o + np.array([i * step, (n - 1) * step, 0])).set_stroke("#5a4320", width=1.2))
    stones = VGroup()
    cells = rng.choice(n * n, size=14, replace=False)
    for k, idx in enumerate(cells):
        x, y = idx % n, idx // n
        st = Circle(radius=step * 0.42).set_fill(BG if k % 2 == 0 else "#f2f1ec", 1).set_stroke("#333", width=1)
        st.move_to(o + np.array([x * step, y * step, 0]))
        stones.add(st)
    return VGroup(board, grid, stones)


# ----------------------------------------------------------------------------
# Shared layout (scenes meet here, so the cuts between them line up)
# ----------------------------------------------------------------------------
MAZE_CELL = 1.0
MAZE_C = np.array([-2.15, -0.42, 0.0])        # the maze's centre in bits 1 and 2
BARS_C = np.array([4.45, -0.05, 0.0])         # the chance-bars card, right of the maze
COUNTER_Y = MAZE_C[1] + (ROWS / 2) * MAZE_CELL + 0.45


def maze_goal_point() -> np.ndarray:
    """Where the star sits on bit 1's maze (the hook ends with the star there)."""
    return MAZE_C + np.array([(GOAL[0] - (COLS - 1) / 2) * MAZE_CELL, (GOAL[1] - (ROWS - 1) / 2) * MAZE_CELL, 0])


def ar_question(height: float = 1.0, color=INK) -> Text:
    """The Arabic question mark «؟» at a given height."""
    q = ar_text("؟", 96, color)
    q.set_height(height)
    return q


def pause_anim(t: float) -> Animation:
    """An animation that does nothing for t seconds (ManimGL has no Wait animation), for Succession."""
    return Animation(Mobject(), run_time=max(t, 0.01), remover=True)



def pop_and_return(mob: Mobject, total: float, at: float, gone: float = 0.35) -> Animation:
    """Over `total` seconds: `mob` stays, is hit at `at` (shrinks away in 0.12 s), stays gone for `gone`
    seconds, then grows back in 0.25 s. Built from a copy of how it looks now, so it can repeat."""
    orig = mob.copy()

    def upd(m, a):
        t = a * total
        if t < at:
            k = 1.0
        elif t < at + 0.12:
            k = 1.0 - (t - at) / 0.12
        elif t < at + 0.12 + gone:
            k = 0.0
        elif t < at + 0.37 + gone:
            k = (t - at - 0.12 - gone) / 0.25
        else:
            k = 1.0
        k = float(np.clip(k, 0.0, 1.0))
        m.become(orig.copy().scale(max(0.05, k), about_point=orig.get_center()))
        m.set_opacity(k) if k < 1.0 else None
    return UpdateFromAlphaFunc(mob, upd, run_time=total, rate_func=linear)



def count_anim(counter: "Counter", n0: int, n1: int, run_time: float, rate_func=linear) -> Animation:
    """Run a Counter from n0 to n1 (whole numbers)."""
    def upd(m, a):
        m.set_value(int(round(n0 + (n1 - n0) * a)))
    return UpdateFromAlphaFunc(counter, upd, run_time=run_time, rate_func=rate_func)

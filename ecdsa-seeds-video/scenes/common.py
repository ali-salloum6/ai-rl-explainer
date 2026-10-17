"""Shared style, building blocks and voiceover timing for every scene."""
from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
from manim import *  # noqa: F401,F403
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from narration import load_segments  # noqa: E402

SEGMENTS = load_segments()
BUILD = ROOT / "build"
TIMELINE_DIR = BUILD / "timeline"
GAP = 0.3  # breath between narration segments, seconds

# ---------------------------------------------------------------- palette
BG = "#0a0d14"
BG_CENTER = "#141b29"
FG = "#e8ebf2"
MUTED = "#8a93a8"
DIM = "#4a5368"
FAINT = "#1c2331"
PANEL = "#121826"
BLUE = "#5cc8ff"
TEAL = "#2dd4bf"
YELLOW = "#ffd166"
GOLD = "#f5b942"
ORANGE = "#ff9f43"
CLAUDE = "#d97757"
RED = "#ff5c7a"
GREEN = "#3ddc97"
PURPLE = "#b392f0"
PINK = "#f78fb3"

SANS = "Inter"
MONO = "JetBrains Mono"

# Variable colours used consistently in every equation.
VAR_COLORS = {
    "d": GOLD,   # private key
    "Q": BLUE,   # public key
    "k": ORANGE, # nonce
    "e": TEAL,   # message hash
    "r": GREEN,  # signature part
    "s": GREEN,  # signature part
    "G": PURPLE, # base point
}


# ---------------------------------------------------------------- text
def T(text, size=36, color=FG, weight=NORMAL, font=SANS, **kw) -> Text:
    return Text(text, font=font, font_size=size, color=color, weight=weight, **kw)


def B(text, size=36, color=FG, **kw) -> Text:
    return T(text, size=size, color=color, weight=BOLD, **kw)


def Mono(text, size=32, color=FG, weight=NORMAL, **kw) -> Text:
    return Text(text, font=MONO, font_size=size, color=color, weight=weight, **kw)


def MT(markup, size=36, color=FG, font=SANS, **kw) -> MarkupText:
    return MarkupText(markup, font=font, font_size=size, color=color, **kw)


def M(*tex, size=48, color=FG, colors: dict | None = None, **kw) -> MathTex:
    """MathTex; parts written as {{x}} whose TeX equals a key of `colors` get that colour."""
    m = MathTex(*tex, font_size=size, color=color, **kw)
    if colors:
        for part in m.submobjects:
            key = getattr(part, "tex_string", "").strip()
            if key in colors:
                part.set_color(colors[key])
    return m


def span(text, color, bold=False) -> str:
    w = ' weight="bold"' if bold else ""
    return f'<span foreground="{color}"{w}>{text}</span>'


def label(text, size=24, color=MUTED, **kw) -> Text:
    return T(text, size=size, color=color, **kw)


def hexgroups(h: str, n: int = 8) -> str:
    h = h.replace(" ", "")
    return " ".join(h[i:i + n] for i in range(0, len(h), n))


# ---------------------------------------------------------------- shapes
def panel(width, height, color=PANEL, stroke=DIM, radius=0.18, opacity=1.0) -> RoundedRectangle:
    return RoundedRectangle(width=width, height=height, corner_radius=radius,
                            fill_color=color, fill_opacity=opacity,
                            stroke_color=stroke, stroke_width=1.5)


def boxed(mob, color=DIM, buff=0.25, fill=PANEL, radius=0.15, stroke_width=1.5) -> VGroup:
    rect = SurroundingRectangle(mob, buff=buff, corner_radius=radius, color=color,
                                stroke_width=stroke_width)
    rect.set_fill(fill, 1)
    return VGroup(rect, mob)


def pill(text, color=FG, fill=FAINT, size=24, mono=False, buff=0.16) -> VGroup:
    t = Mono(text, size, color) if mono else T(text, size, color)
    r = RoundedRectangle(width=t.width + 2 * buff + 0.1, height=t.height + 2 * buff,
                         corner_radius=(t.height + 2 * buff) / 2, fill_color=fill,
                         fill_opacity=1, stroke_color=color, stroke_width=1.2)
    t.move_to(r)
    return VGroup(r, t)


def check_mark(color=GREEN, size=0.5, width=8) -> VMobject:
    m = VMobject(stroke_color=color, stroke_width=width)
    m.set_points_as_corners([LEFT * 0.5 + UP * 0.05, DOWN * 0.4 + LEFT * 0.1, RIGHT * 0.55 + UP * 0.5])
    m.set_cap_style = None
    return m.scale(size)


def cross_mark(color=RED, size=0.45, width=8) -> VGroup:
    a = Line(UL, DR, stroke_color=color, stroke_width=width)
    b = Line(UR, DL, stroke_color=color, stroke_width=width)
    return VGroup(a, b).scale(size / 2)


def stamp(text, color=RED, size=40, angle=-12 * DEGREES) -> VGroup:
    t = B(text, size, color)
    r = RoundedRectangle(width=t.width + 0.5, height=t.height + 0.35, corner_radius=0.08,
                         stroke_color=color, stroke_width=5, fill_opacity=0)
    g = VGroup(r, t)
    t.move_to(r)
    return g.rotate(angle)


def arrow(start, end, color=MUTED, buff=0.1, width=4, tip=0.2) -> Arrow:
    return Arrow(start, end, buff=buff, color=color, stroke_width=width,
                 max_tip_length_to_length_ratio=0.25, tip_length=tip)


# ---------------------------------------------------------------- icons
def icon_padlock(color=GOLD, h=1.0) -> VGroup:
    body = RoundedRectangle(width=1.0, height=0.78, corner_radius=0.12,
                            fill_color=color, fill_opacity=1, stroke_width=0)
    arc = AnnularSector(inner_radius=0.22, outer_radius=0.34, angle=PI, start_angle=0,
                        fill_color=color, fill_opacity=1, stroke_width=0)
    arc.move_to(body.get_top() + UP * 0.45, aligned_edge=UP)
    legs = VGroup(*[Rectangle(width=0.12, height=0.3, fill_color=color, fill_opacity=1,
                              stroke_width=0).move_to(body.get_top() + UP * 0.12 + RIGHT * dx)
                    for dx in (-0.28, 0.28)])
    hole = VGroup(Circle(0.085, fill_color=BG, fill_opacity=1, stroke_width=0),
                  Polygon(LEFT * 0.05, RIGHT * 0.05, RIGHT * 0.03 + DOWN * 0.2, LEFT * 0.03 + DOWN * 0.2,
                          fill_color=BG, fill_opacity=1, stroke_width=0))
    hole.move_to(body.get_center() + DOWN * 0.03)
    g = VGroup(legs, arc, body, hole)
    return g.scale_to_fit_height(h)


def icon_key(color=GOLD, w=1.4) -> VGroup:
    bow = Annulus(inner_radius=0.13, outer_radius=0.3, fill_color=color, fill_opacity=1, stroke_width=0)
    shaft = Rectangle(width=0.95, height=0.13, fill_color=color, fill_opacity=1, stroke_width=0)
    shaft.next_to(bow, RIGHT, buff=-0.04)
    t1 = Rectangle(width=0.1, height=0.2, fill_color=color, fill_opacity=1, stroke_width=0)
    t2 = t1.copy().stretch(0.7, 1)
    t1.next_to(shaft.get_right(), DOWN, buff=0).shift(LEFT * 0.08)
    t2.next_to(shaft.get_right(), DOWN, buff=0).shift(LEFT * 0.3)
    t1.align_to(shaft, UP).shift(DOWN * 0.12)
    t2.align_to(shaft, UP).shift(DOWN * 0.12)
    g = VGroup(bow, shaft, t1, t2)
    return g.scale_to_fit_width(w)


def icon_chip(color=TEAL, s=1.0) -> VGroup:
    body = RoundedRectangle(width=1.0, height=1.0, corner_radius=0.1, fill_color=color,
                            fill_opacity=0.18, stroke_color=color, stroke_width=3)
    core = RoundedRectangle(width=0.5, height=0.5, corner_radius=0.06, fill_color=color,
                            fill_opacity=0.9, stroke_width=0)
    pins = VGroup()
    for i in range(4):
        off = -0.33 + i * 0.22
        for d in (UP, DOWN, LEFT, RIGHT):
            pin = Rectangle(width=0.07 if d[0] == 0 else 0.16, height=0.16 if d[0] == 0 else 0.07,
                            fill_color=color, fill_opacity=1, stroke_width=0)
            perp = RIGHT if d[0] == 0 else UP
            pin.move_to(d * 0.58 + perp * off)
            pins.add(pin)
    return VGroup(pins, body, core).scale_to_fit_width(s)


def icon_doc(color=FG, h=1.4, lines=4, fill=FAINT) -> VGroup:
    w = h * 0.78
    f = 0.24 * h
    page = Polygon(
        [-w / 2, h / 2, 0], [w / 2 - f, h / 2, 0], [w / 2, h / 2 - f, 0], [w / 2, -h / 2, 0], [-w / 2, -h / 2, 0],
        fill_color=fill, fill_opacity=1, stroke_color=color, stroke_width=2.5)
    fold = Polygon([w / 2 - f, h / 2, 0], [w / 2 - f, h / 2 - f, 0], [w / 2, h / 2 - f, 0],
                   fill_color=color, fill_opacity=0.35, stroke_color=color, stroke_width=2)
    ls = VGroup(*[Line([-w / 2 + 0.15 * h, h / 2 - 0.42 * h - i * 0.16 * h, 0],
                       [w / 2 - 0.15 * h - (0.12 * h if i == lines - 1 else 0), h / 2 - 0.42 * h - i * 0.16 * h, 0],
                       stroke_color=color, stroke_width=2, stroke_opacity=0.55) for i in range(lines)])
    return VGroup(page, fold, ls)


def icon_person(color=BLUE, h=1.2, name: str | None = None, name_color=None) -> VGroup:
    head = Circle(radius=0.22, fill_color=color, fill_opacity=1, stroke_width=0)
    body = Sector(radius=0.42, angle=PI, start_angle=0, fill_color=color, fill_opacity=1, stroke_width=0)
    body.next_to(head, DOWN, buff=0.06)
    fig = VGroup(head, body).scale_to_fit_height(h)
    if name:
        lab = T(name, 26, name_color or color, weight=BOLD).next_to(fig, DOWN, buff=0.15)
        return VGroup(fig, lab)
    return fig


def icon_browser(url="https://bank.example", w=3.4, h=2.2, color=BLUE) -> VGroup:
    frame = RoundedRectangle(width=w, height=h, corner_radius=0.15, fill_color=PANEL, fill_opacity=1,
                             stroke_color=DIM, stroke_width=2)
    bar = Line(frame.get_left() + UP * (h / 2 - 0.42), frame.get_right() + UP * (h / 2 - 0.42),
               stroke_color=DIM, stroke_width=2)
    dots = VGroup(*[Dot(radius=0.05, color=c) for c in (RED, YELLOW, GREEN)]).arrange(RIGHT, buff=0.09)
    dots.move_to(frame.get_corner(UL) + RIGHT * 0.32 + DOWN * 0.21)
    addr = RoundedRectangle(width=w - 1.0, height=0.24, corner_radius=0.12, fill_color=FAINT, fill_opacity=1,
                            stroke_width=0).move_to(frame.get_top() + DOWN * 0.21 + RIGHT * 0.3)
    lock = icon_padlock(GREEN, 0.15).move_to(addr.get_left() + RIGHT * 0.18)
    url_t = Mono(url, 14, MUTED).next_to(lock, RIGHT, buff=0.08)
    content = VGroup(*[RoundedRectangle(width=w * f, height=0.13, corner_radius=0.06, fill_color=DIM,
                                        fill_opacity=0.6, stroke_width=0) for f in (0.7, 0.55, 0.62)])
    content.arrange(DOWN, buff=0.18, aligned_edge=LEFT).move_to(frame.get_center() + DOWN * 0.25)
    return VGroup(frame, bar, dots, addr, lock, url_t, content)


def icon_bank(color=FG, w=1.6) -> VGroup:
    roof = Polygon(LEFT * 0.9, RIGHT * 0.9, UP * 0.5, fill_color=color, fill_opacity=1, stroke_width=0)
    beam = Rectangle(width=1.7, height=0.12, fill_color=color, fill_opacity=1, stroke_width=0)
    beam.next_to(roof, DOWN, buff=0.05)
    cols = VGroup(*[Rectangle(width=0.16, height=0.75, fill_color=color, fill_opacity=1, stroke_width=0)
                    for _ in range(4)]).arrange(RIGHT, buff=0.26).next_to(beam, DOWN, buff=0.05)
    base = Rectangle(width=1.8, height=0.14, fill_color=color, fill_opacity=1, stroke_width=0)
    base.next_to(cols, DOWN, buff=0.05)
    return VGroup(roof, beam, cols, base).scale_to_fit_width(w)


def icon_door(color=RED, h=1.6) -> VGroup:
    frame = Rectangle(width=0.9, height=1.6, stroke_color=color, stroke_width=4, fill_opacity=0)
    door = Polygon(frame.get_corner(DL), frame.get_corner(UL), frame.get_corner(UL) + RIGHT * 0.55 + DOWN * 0.18,
                   frame.get_corner(DL) + RIGHT * 0.55 + UP * 0.12,
                   fill_color=color, fill_opacity=0.35, stroke_color=color, stroke_width=3)
    knob = Dot(door.get_center() + RIGHT * 0.15, radius=0.05, color=color)
    glow = Polygon(frame.get_corner(UR), frame.get_corner(DR), door.get_vertices()[3], door.get_vertices()[2],
                   fill_color=YELLOW, fill_opacity=0.25, stroke_width=0)
    return VGroup(glow, frame, door, knob).scale_to_fit_height(h)


def icon_clock(color=FG, r=1.0, hour=9.0, minute=0.0, numbers=False, tick_color=None) -> VGroup:
    face = Circle(radius=r, stroke_color=color, stroke_width=4, fill_color=PANEL, fill_opacity=1)
    ticks = VGroup()
    for i in range(12):
        ang = PI / 2 - i * TAU / 12
        d = np.array([np.cos(ang), np.sin(ang), 0])
        ticks.add(Line(d * r * 0.86, d * r * 0.96, stroke_color=tick_color or color,
                       stroke_width=4 if i % 3 == 0 else 2))
    nums = VGroup()
    if numbers:
        for i in range(12):
            ang = PI / 2 - i * TAU / 12
            d = np.array([np.cos(ang), np.sin(ang), 0])
            nums.add(T(str(12 if i == 0 else i), size=int(19 * r), color=color).move_to(d * r * 0.68))
    h_ang = PI / 2 - (hour % 12 + minute / 60) * TAU / 12
    m_ang = PI / 2 - minute * TAU / 60
    hand_h = Line(ORIGIN, r * 0.5 * np.array([np.cos(h_ang), np.sin(h_ang), 0]), stroke_color=color, stroke_width=7)
    hand_m = Line(ORIGIN, r * 0.75 * np.array([np.cos(m_ang), np.sin(m_ang), 0]), stroke_color=color, stroke_width=4)
    hub = Dot(ORIGIN, radius=0.06 * r + 0.02, color=color)
    g = VGroup(face, ticks, nums, hand_h, hand_m, hub)
    g.hand_h, g.hand_m, g.face = hand_h, hand_m, face
    return g


def icon_stopwatch(color=CLAUDE, r=0.6) -> VGroup:
    face = Circle(radius=r, stroke_color=color, stroke_width=5, fill_color=PANEL, fill_opacity=1)
    crown = RoundedRectangle(width=0.28 * r / 0.6, height=0.16 * r / 0.6, corner_radius=0.04,
                             fill_color=color, fill_opacity=1, stroke_width=0).next_to(face, UP, buff=0.04)
    stem = Rectangle(width=0.08 * r / 0.6, height=0.08, fill_color=color, fill_opacity=1, stroke_width=0)
    stem.next_to(face, UP, buff=-0.02)
    sector = Sector(radius=r * 0.82, angle=-TAU * 0.5, start_angle=PI / 2, fill_color=color,
                    fill_opacity=0.35, stroke_width=0)
    hand = Line(ORIGIN, UP * r * 0.8, stroke_color=color, stroke_width=4).rotate(-PI, about_point=ORIGIN)
    return VGroup(face, sector, stem, crown, hand, Dot(radius=0.05, color=color))


def icon_shield(color=GREEN, h=1.6, check=True) -> VGroup:
    pts = [UP * 0.8 + LEFT * 0.65, UP * 0.95, UP * 0.8 + RIGHT * 0.65, RIGHT * 0.62 + DOWN * 0.1,
           DOWN * 0.95, LEFT * 0.62 + DOWN * 0.1]
    sh = VMobject(fill_color=color, fill_opacity=0.22, stroke_color=color, stroke_width=5)
    sh.set_points_smoothly([*pts, pts[0]])
    g = VGroup(sh)
    if check:
        g.add(check_mark(color, 0.8, 10).move_to(sh.get_center() + UP * 0.05))
    return g.scale_to_fit_height(h)


def icon_bubble(text_mob, color=FG, fill=PANEL, tail="left", buff=0.3) -> VGroup:
    box = RoundedRectangle(width=text_mob.width + 2 * buff, height=text_mob.height + 2 * buff,
                           corner_radius=0.2, fill_color=fill, fill_opacity=1, stroke_color=color, stroke_width=2)
    box.move_to(text_mob)
    c = box.get_corner(DL if tail == "left" else DR)
    sgn = 1 if tail == "left" else -1
    a, b2, tipp = c + RIGHT * sgn * 0.35, c + RIGHT * sgn * 0.8, c + RIGHT * sgn * 0.15 + DOWN * 0.32
    tail_fill = Polygon(a + UP * 0.03, b2 + UP * 0.03, tipp, fill_color=fill, fill_opacity=1, stroke_width=0)
    edges = VGroup(Line(a, tipp, stroke_color=color, stroke_width=2), Line(b2, tipp, stroke_color=color, stroke_width=2))
    return VGroup(box, tail_fill, edges, text_mob)


def code_window(lines: list[str], size=26, w=None, title=None, colors: dict | None = None) -> VGroup:
    """A dark editor window with monospaced lines. `colors` maps line index to colour."""
    texts = VGroup(*[Mono(l.lstrip(" ") if l.strip() else " ", size, (colors or {}).get(i, FG))
                     for i, l in enumerate(lines)])
    texts.arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    cw = Mono("0" * 20, size).width / 20  # leading spaces have no glyphs, so indent by hand
    for t, l in zip(texts, lines):
        t.shift(RIGHT * cw * (len(l) - len(l.lstrip(" "))))
    width = w or texts.width + 0.9
    height = texts.height + 1.0
    frame = RoundedRectangle(width=width, height=height, corner_radius=0.18, fill_color=PANEL, fill_opacity=1,
                             stroke_color=DIM, stroke_width=1.5)
    dots = VGroup(*[Dot(radius=0.055, color=c) for c in (RED, YELLOW, GREEN)]).arrange(RIGHT, buff=0.1)
    dots.move_to(frame.get_corner(UL) + RIGHT * 0.35 + DOWN * 0.25)
    texts.next_to(frame.get_corner(UL), DR, buff=0).shift(RIGHT * 0.45 + DOWN * 0.55)
    g = VGroup(frame, dots)
    if title:
        g.add(Mono(title, 18, MUTED).move_to(frame.get_top() + DOWN * 0.25))
    g.add(texts)
    g.lines = texts
    return g


def bit_cells(bits: str, cell=0.24, gap=0.03, on=FG, off=DIM, show_digits=True, digit_size=None,
              fill_on=None, fill_off=None) -> VGroup:
    cells = VGroup()
    for b in bits:
        sq = Square(cell, stroke_color=DIM, stroke_width=1,
                    fill_color=(fill_on if b == "1" else fill_off) or FAINT, fill_opacity=1)
        g = VGroup(sq)
        if show_digits:
            g.add(Mono(b, digit_size or int(cell * 70), on if b == "1" else off).move_to(sq))
        cells.add(g)
    cells.arrange(RIGHT, buff=gap)
    return cells


# ---------------------------------------------------------------- background
def _background_path(w: int, h: int) -> Path:
    path = BUILD / f"bg_{w}x{h}.png"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        cx, cy = w / 2, h * 0.45
        r = np.sqrt(((xx - cx) / w) ** 2 + ((yy - cy) / h) ** 2 * 0.9)
        t = np.clip(r / 0.75, 0, 1) ** 1.6
        c0 = np.array(ManimColor(BG_CENTER).to_rgb()) * 255
        c1 = np.array(ManimColor(BG).to_rgb()) * 255
        img = c0[None, None, :] * (1 - t[..., None]) + c1[None, None, :] * t[..., None]
        rng = np.random.default_rng(7)
        img += rng.normal(0, 1.1, img.shape)  # a little grain against banding
        img = np.clip(img, 0, 255).astype(np.uint8)
        Image.fromarray(np.dstack([img, np.full((h, w), 255, np.uint8)]), "RGBA").save(path)
    return path


# ---------------------------------------------------------------- voiceover timing
class VO:
    """Handle for one narration segment while its visuals play."""

    def __init__(self, scene: "VOScene", sid: str, start: float):
        self.scene = scene
        self.seg = SEGMENTS[sid]
        self.id = sid
        self.start = start

    @property
    def duration(self) -> float:
        return self.seg.duration

    @property
    def end(self) -> float:
        return self.start + self.seg.duration

    def at(self, mark: str) -> float:
        return self.start + self.seg.mark_time(mark)

    def until(self, mark: str, minimum: float = 0.3) -> float:
        """Run time that makes an animation started now finish on `mark`."""
        return max(minimum, self.at(mark) - self.scene.time)

    def left(self, minimum: float = 0.3) -> float:
        return max(minimum, self.end - self.scene.time)

    def wait_until(self, mark: str, offset: float = 0.0):
        target = self.at(mark) + offset
        dt = target - self.scene.time
        if dt > 1 / 60:
            self.scene.wait(dt)
        elif dt < -0.6:
            self.scene.late.append((self.id, mark, round(-dt, 2)))

    def wait_end(self, offset: float = 0.0):
        dt = self.end + offset - self.scene.time
        if dt > 1 / 60:
            self.scene.wait(dt)


class VOScene(Scene):
    """Scene whose pacing follows the narration segments of script.md."""

    def setup(self):
        self.camera.background_image = str(_background_path(config.pixel_width, config.pixel_height))
        self.camera.init_background()
        self.timeline: list[dict] = []
        self.events: list[dict] = []
        self.late: list[tuple] = []

    @contextmanager
    def vo(self, sid: str, gap: float = GAP):
        v = VO(self, sid, self.time)
        self.timeline.append({"id": sid, "start": round(self.time, 4), "duration": round(v.duration, 4)})
        yield v
        remaining = v.end + gap - self.time
        if remaining > 1 / 60:
            self.wait(remaining)

    def sfx(self, name: str, **params):
        """Cue a sound effect at the current time; tools/assemble.py renders it."""
        self.events.append({"sfx": name, "t": round(self.time, 4), **params})

    def chapter(self, num: int, title: str, hold: float = 1.1):
        n = Mono(f"{num:02d}", 34, CLAUDE, weight=BOLD)
        t = B(title, 60)
        if t.width > 12:
            t.scale_to_fit_width(12)
        line = Line(LEFT, RIGHT, stroke_color=CLAUDE, stroke_width=3).set_width(1.2)
        grp = VGroup(n, t, line).arrange(DOWN, buff=0.32)
        self.sfx("whoosh")
        self.play(FadeIn(n, shift=0.15 * UP), FadeIn(t, shift=0.15 * UP), GrowFromCenter(line), run_time=0.9)
        self.wait(hold)
        self.play(FadeOut(grp, shift=0.15 * UP), run_time=0.5)

    def clear_all(self, run_time=0.6, shift=ORIGIN):
        mobs = [m for m in self.mobjects]
        if mobs:
            self.play(*[FadeOut(m, shift=shift) for m in mobs], run_time=run_time)

    def tear_down(self):
        TIMELINE_DIR.mkdir(parents=True, exist_ok=True)
        out = {"scene": type(self).__name__, "segments": self.timeline, "events": self.events,
               "duration": round(self.time, 4), "late": self.late}
        out["fps"] = config.frame_rate
        out["height"] = config.pixel_height
        text = json.dumps(out, indent=1)
        (TIMELINE_DIR / f"{type(self).__name__}.json").write_text(text)
        if config.write_to_movie and not config.dry_run and not config.save_last_frame:
            # Only real renders define the timing the assembler must follow.
            (TIMELINE_DIR / f"{type(self).__name__}_{config.pixel_height}p{int(config.frame_rate)}.json").write_text(text)
        if self.late:
            print(f"[timing] {type(self).__name__}: visuals late at {self.late}")


def icon_magnifier(color=FG, r=0.45) -> VGroup:
    ring = Annulus(inner_radius=r * 0.78, outer_radius=r, fill_color=color, fill_opacity=1, stroke_width=0)
    glass = Circle(radius=r * 0.78, fill_color=color, fill_opacity=0.12, stroke_width=0)
    handle = RoundedRectangle(width=r * 0.32, height=r * 1.1, corner_radius=r * 0.12, fill_color=color,
                              fill_opacity=1, stroke_width=0)
    handle.rotate(PI / 4).move_to(ring.get_center() + (DR / np.linalg.norm(DR)) * r * 1.35)
    return VGroup(glass, ring, handle)


def mini_curve(color=BLUE, w=1.6, a=-3.0, b=3.0, stroke=4) -> VMobject:
    """Small drawing of y^2 = x^3 + ax + b, used as an icon."""
    roots = np.roots([1, 0, a, b])
    x0 = float(min(r.real for r in roots if abs(r.imag) < 1e-9))
    xmax = 2.25
    tmax = np.sqrt(xmax - x0)
    f = lambda x: x ** 3 + a * x + b
    c = ParametricFunction(lambda t: np.array([x0 + t * t, np.sign(t) * np.sqrt(max(f(x0 + t * t), 0)), 0]),
                           t_range=[-tmax, tmax, 0.01], stroke_color=color, stroke_width=stroke)
    return c.scale_to_fit_width(w)

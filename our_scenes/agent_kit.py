"""
Video 3's kit (copied from ../ai-agents-explainer for video 4): the pieces of the agent diagram and
the shop, on top of video 2's kit (palette, ar_text, word_chip, user_bubble, model_box, cursor,
NarratedScene, ...). Video 4 uses it for the house icons, the yes/no dial (the callback to video 3's
ending), AgentScene's word anchors and seamless cuts; its own pieces live in our_scenes/rl_kit.py.

    from our_scenes.agent_kit import *      # re-exports our_scenes.kit and manimlib

Every scene builds the master diagram with `master()`, so the writer, the hands, the world,
the tools guide and the desk sit in the same place from bit to bit (docs/agents_plan.md §4).
On-screen words are only the ones docs/script_visual_map.md lists (the *_AR / *_EN constants).
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from our_scenes.kit import *  # noqa: F401,F403  (also re-exports manimlib)


def _first_font(*names: str) -> str:
    """The first of `names` installed here (macOS has Helvetica Neue and Menlo; a Linux render box
    has Inter and DejaVu Sans Mono), so Latin text looks the same wherever the video is rendered."""
    try:
        import manimpango
        have = set(manimpango.list_fonts())
    except Exception:
        return names[0]
    return next((n for n in names if n in have), names[-1])


LATIN_FONT = _first_font("Helvetica Neue", "Inter", "DejaVu Sans")
MONO_FONT = _first_font("Menlo", "DejaVu Sans Mono", "Liberation Mono")

# ----------------------------------------------------------------------------
# Palette additions
# ----------------------------------------------------------------------------
HANDS = "#9aa1ad"          # the program ("the hands"): plain grey, clearly not smart
RED = "#e5484d"            # a loss, a wrong pick (sparingly)
GREEN = "#46c37b"          # a tick
BLAZER = "#3b6fd1"         # the blue blazer
TIE = "#d64545"            # the red tie
FRIDGE_BODY = "#252c3b"
FRIDGE_EDGE = "#8a93a6"
GLASS = "#101623"
CARDBOARD = "#b98552"
METAL = "#aeb6c3"
DESK_FILL = "#1a2030"
DESK_EDGE = "#4a5468"
NIGHT = "#05070d"

# ----------------------------------------------------------------------------
# On-screen strings (docs/script_visual_map.md, "On-screen text set by the Arabic picks")
# ----------------------------------------------------------------------------
REQUEST_SLIP_AR = "ابعت إيميل للمورّد: أربعين علبة كولا."
GUIDE_TITLE_AR = "دليل الأدوات"
MENU_TITLE_AR = "منيو المحل"
TOOL_NAMES_AR = ["إيميل", "محادثة الزباين", "بحث", "ملاحظات", "المخزون"]
ITEM_NAMES_AR = ["كولا", "شيبس", "مكعب معدن"]
DIAL_NO_AR, DIAL_YES_AR = "لأ", "أكيد"
ASK_DISCOUNT_AR = "خصم؟"
LOOP_WORDS_AR = ["فكّر", "نفّذ", "اقرا"]
CHECKLIST_AR = ["شوف التكلفة", "شوف الربح", "جاوب"]
ROUND_TWO_AR = "المحاولة التانية"
BOSS_AR = "المدير"
WRONG_NOTE_AR = "سارة من المورّد قالت…"
SUPPLIER_AR = "المورّد"
AGENT_EN = "AI Agent"
CONTEXT_EN = "context window"
TRANSCEND_EN = "ETERNAL TRANSCENDENCE"


def en_text(s: str, font_size: int = 32, color=INK, weight: str = "NORMAL") -> Text:
    """Latin text (the few English terms the map allows on screen)."""
    return Text(s, font=LATIN_FONT, font_size=font_size, fill_color=color, weight=weight)


def chip_en(s: str, height: float = 0.52, color=ACCENT) -> VGroup:
    """A rounded chip with an English term in it («AI Agent», «context window»). Attributes: .chip, .text"""
    text = en_text(s, font_size=30, color=color)
    text.set_height(0.40 * height)
    chip = RoundedRectangle(width=text.get_width() + 0.75 * height, height=height, corner_radius=height / 2)
    chip.set_fill(CARD_FILL, opacity=1.0)
    chip.set_stroke(color, width=2.0)
    text.move_to(chip)
    out = VGroup(chip, text)
    out.chip, out.text = chip, text
    return out


def _card(width: float, height: float, stroke=CARD_STROKE, fill=CARD_FILL, r: float = 0.14,
          stroke_width: float = 2.0, fill_opacity: float = 1.0) -> RoundedRectangle:
    c = RoundedRectangle(width=width, height=height, corner_radius=min(r, height / 2, width / 2))
    c.set_fill(fill, opacity=fill_opacity)
    c.set_stroke(stroke, width=stroke_width)
    return c


def _bar(width: float, height: float, color, opacity: float = 1.0) -> RoundedRectangle:
    b = RoundedRectangle(width=max(width, 1e-3), height=height, corner_radius=min(height / 2, width / 2))
    b.set_fill(color, opacity=opacity)
    b.set_stroke(width=0)
    return b


def text_lines(width: float, n: int = 2, height: float = 0.07, gap: float = 0.10, color=INK_2,
               opacity: float = 0.55, seed: int = 1, rtl: bool = True) -> VGroup:
    """Abstract written lines (for slips and rows whose words don't matter): right-aligned, ragged."""
    rng = np.random.default_rng(seed)
    lines = VGroup()
    for i in range(n):
        w = width * (1.0 if i < n - 1 else 0.45 + 0.35 * rng.random()) * (0.86 + 0.14 * rng.random())
        lines.add(_bar(w, height, color, opacity))
    lines.arrange(DOWN, buff=gap, aligned_edge=RIGHT if rtl else LEFT)
    return lines


# ----------------------------------------------------------------------------
# The writer, the hands, slips, envelopes
# ----------------------------------------------------------------------------
def writer_box(width: float = 2.5, height: float = 1.6) -> VGroup:
    """The model: video 2's writer (teal box). Attributes: .box, .motif"""
    return model_box(width, height)


def hands_box(width: float = 1.75, height: float = 1.15) -> VGroup:
    """The small program that does exactly what a request says: a plain grey box with a code mark.
    Attributes: .box, .mark"""
    box = _card(width, height, stroke=HANDS, r=0.18 * height, stroke_width=2.6)
    mark = Text("{ }", font=MONO_FONT, font_size=40, fill_color=HANDS)
    mark.set_height(0.36 * height)
    mark.move_to(box)
    out = VGroup(box, mark)
    out.box, out.mark = box, mark
    return out


def slip(text_ar: str | None = None, kind: str = "request", width: float | None = None, n_lines: int = 2,
         font_size: int = 26, seed: int = 3, height: float | None = None) -> VGroup:
    """A small card with one written line: a request (teal edge) or a result (amber edge).
    Without text it carries abstract lines. Attributes: .card, .content, .edge, .kind"""
    color = ACCENT if kind == "request" else WARM if kind == "result" else INK_2
    pad_x, pad_y = 0.22, 0.14
    if text_ar is not None:
        content = ar_text(text_ar, font_size=font_size, color=INK)
        if width is not None:
            content.set_max_width(width - 2 * pad_x - 0.08)
        w = width if width is not None else content.get_width() + 2 * pad_x + 0.08
        h = height if height is not None else content.get_height() + 2 * pad_y
    else:
        w = width if width is not None else 1.3
        content = text_lines(w - 2 * pad_x - 0.08, n=n_lines, seed=seed)
        h = height if height is not None else content.get_height() + 2 * pad_y
    card = _card(w, h, stroke=color, r=0.08, stroke_width=2.0)
    edge = _bar(0.07, h - 0.10, color, 0.95)
    edge.move_to(card.get_right() + 0.075 * LEFT)
    content.move_to(card.get_center() + 0.04 * LEFT)
    out = VGroup(card, edge, content)
    out.card, out.content, out.edge, out.kind = card, content, edge, kind
    return out


def envelope(width: float = 0.62, color=INK_2, fill=CARD_FILL) -> VGroup:
    h = 0.66 * width
    body = Rectangle(width=width, height=h)
    body.set_fill(fill, opacity=1.0)
    body.set_stroke(color, width=2.0)
    ul, ur = body.get_corner(UL), body.get_corner(UR)
    flap = Polyline(ul, body.get_center() + 0.10 * h * DOWN, ur)
    flap.set_stroke(color, width=2.0)
    flap.set_fill(opacity=0)
    return VGroup(body, flap)


# ----------------------------------------------------------------------------
# Small icons (flat, house style, no logos)
# ----------------------------------------------------------------------------
def icon_box(size: float = 0.6) -> VGroup:
    """A cardboard carton."""
    front = Rectangle(width=size, height=0.72 * size)
    front.set_fill(CARDBOARD, opacity=1.0).set_stroke("#7c5530", width=1.5)
    top = Polygon(front.get_corner(UL), front.get_corner(UR), front.get_corner(UR) + np.array([0.18, 0.16, 0]) * size,
                  front.get_corner(UL) + np.array([0.18, 0.16, 0]) * size)
    top.set_fill("#d39d66", opacity=1.0).set_stroke("#7c5530", width=1.5)
    tape = Rectangle(width=0.16 * size, height=0.72 * size).move_to(front)
    tape.set_fill("#e8c08f", opacity=0.9).set_stroke(width=0)
    return VGroup(top, front, tape)


def icon_tag(size: float = 0.5, color=WARM) -> VGroup:
    """A price tag (no number on it)."""
    w, h = size, 0.56 * size
    tag = Polygon(np.array([-w / 2, 0, 0]), np.array([-w / 2 + 0.28 * w, h / 2, 0]), np.array([w / 2, h / 2, 0]),
                  np.array([w / 2, -h / 2, 0]), np.array([-w / 2 + 0.28 * w, -h / 2, 0]))
    tag.set_fill(color, opacity=1.0).set_stroke(width=0)
    hole = Circle(radius=0.07 * size).move_to(np.array([-w / 2 + 0.24 * w, 0, 0]))
    hole.set_fill(BG, opacity=1.0).set_stroke(width=0)
    return VGroup(tag, hole)


def rounded_polygon(points, radii) -> VMobject:
    """ONE closed outline through `points` (x, y; in order), each corner rounded by its own radius: a per-corner
    version of Polygon.round_corners. Use it for a stroked shape that has a part stuck on (a bubble's tail):
    ManimGL's Union() leaves each part's own outline in place, so a stroked union shows a seam across the join."""
    verts = [np.array([x, y, 0.0]) for x, y in points]
    n = len(verts)
    arcs = []
    for k in range(n):
        v1, v2, v3 = verts[k - 1], verts[k], verts[(k + 1) % n]
        e1, e2 = normalize(v2 - v1), normalize(v3 - v2)
        angle = angle_between_vectors(e1, e2)
        cut = radii[k] * np.tan(angle / 2)
        arcs.append(ArcBetweenPoints(v2 - e1 * cut, v2 + e2 * cut, angle=np.sign(cross2d(e1, e2)) * angle, n_components=2))
    out = VMobject()
    for k in range(n):
        out.add_subpath(arcs[k].get_points())
        out.add_line_to(arcs[(k + 1) % n].get_start())
    return out


def bubble_outline(width: float, height: float, corner: float, tail: str = "DR", base_w: float = 0.2,
                   tip_in: float = 0.1, depth: float = 0.2, gap: float = 0.03) -> VMobject:
    """A rounded speech bubble and its tail as ONE closed outline, centred on the body. The tail hangs from the
    bottom edge by the right ("DR") or left ("DL") corner: its base starts `gap` past the corner's curve and is
    `base_w` wide; its tip is `depth` below the body and `tip_in` in from the side."""
    hw, hh = width / 2, height / 2
    near = hw - corner - gap                      # base end nearest the corner
    pts = [(-hw, hh), (-hw, -hh), (near - base_w, -hh), (hw - tip_in, -hh - depth), (near, -hh), (hw, -hh), (hw, hh)]
    soft, tip = 0.15 * depth, 0.07 * depth
    out = rounded_polygon(pts, [corner, corner, soft, tip, soft, corner, corner])
    return out.flip(UP) if tail == "DL" else out


def icon_bubble(size: float = 0.5, color=INK_2, fill=BUBBLE_FILL) -> VGroup:
    """A small chat bubble (three dots) with a tail at its bottom right, body and tail one outline (no seam)."""
    shape = bubble_outline(size, 0.66 * size, 0.2 * size, "DR", base_w=0.2 * size, tip_in=0.10 * size,
                           depth=0.20 * size, gap=0.03 * size)
    shape.set_fill(fill, opacity=1.0).set_stroke(color, width=1.6)
    dots = VGroup(*[Dot(radius=0.045 * size).set_fill(color, 1.0) for _ in range(3)]).arrange(RIGHT, buff=0.1 * size)
    dots.move_to(ORIGIN)
    return VGroup(shape, dots)


def speech_bubble(width: float = 2.0, height: float = 1.4, tail: str = "DR", fill=BUBBLE_FILL) -> VGroup:
    """A rounded speech bubble with a tail at one bottom corner ("DR" / "DL"). Attributes: .body, .shape"""
    body = RoundedRectangle(width=width, height=height, corner_radius=min(0.3, height / 2))
    s = 1 if tail == "DR" else -1
    bx = body.get_right()[0] - 0.45 if s > 0 else body.get_left()[0] + 0.45
    b = body.get_bottom()[1]
    tl = Polygon(np.array([bx - 0.22 * s, b + 0.05, 0]), np.array([bx + 0.12 * s, b + 0.05, 0]), np.array([bx + 0.32 * s, b - 0.32, 0]))
    shape = Union(body, tl)
    shape.set_fill(fill, opacity=1.0).set_stroke(width=0)
    body.set_fill(opacity=0).set_stroke(width=0)        # invisible: moves with the bubble, marks its middle
    out = VGroup(shape, body)
    out.body, out.shape = body, shape
    return out


def icon_search(size: float = 0.5, color=INK_2) -> VGroup:
    ring = Circle(radius=0.28 * size).set_stroke(color, width=2.4).set_fill(opacity=0)
    ring.shift(0.08 * size * (UP + LEFT))
    handle = Line(ring.get_center() + 0.2 * size * (DOWN + RIGHT), ring.get_center() + 0.42 * size * (DOWN + RIGHT))
    handle.set_stroke(color, width=4)
    return VGroup(ring, handle)


def icon_note(size: float = 0.5, color=INK_2) -> VGroup:
    page = _card(0.72 * size, 0.9 * size, stroke=color, r=0.05 * size, stroke_width=1.6)
    lines = VGroup(*[_bar(0.42 * size, 0.04 * size, color, 0.8) for _ in range(3)]).arrange(DOWN, buff=0.12 * size)
    lines.move_to(page)
    return VGroup(page, lines)


def icon_shelves(size: float = 0.5, color=INK_2) -> VGroup:
    frame = Rectangle(width=0.9 * size, height=0.8 * size).set_stroke(color, width=1.6).set_fill(opacity=0)
    shelf = Line(frame.get_left(), frame.get_right()).set_stroke(color, width=1.6)
    items = VGroup(*[Rectangle(width=0.14 * size, height=0.22 * size).set_fill(c, 1).set_stroke(width=0)
                     for c in (TIE, ACCENT, WARM)]).arrange(RIGHT, buff=0.08 * size)
    items.next_to(shelf, UP, buff=0.0)
    items2 = items.copy().next_to(shelf, DOWN, buff=0.0).align_to(frame, DOWN).shift(0.02 * UP)
    return VGroup(frame, shelf, items, items2)


def icon_can(size: float = 0.5, color=TIE) -> VGroup:
    body = RoundedRectangle(width=0.5 * size, height=0.86 * size, corner_radius=0.08 * size)
    body.set_fill(color, opacity=1.0).set_stroke(width=0)
    rim = _bar(0.5 * size, 0.06 * size, METAL).move_to(body.get_top() + 0.03 * size * DOWN)
    band = _bar(0.5 * size, 0.12 * size, INK, 0.85).move_to(body)
    return VGroup(body, band, rim)


def icon_chips(size: float = 0.5, color=WARM) -> VGroup:
    bag = Polygon(np.array([-0.26, -0.42, 0]) * size, np.array([0.26, -0.42, 0]) * size, np.array([0.3, 0.36, 0]) * size,
                  np.array([0.22, 0.44, 0]) * size, np.array([-0.22, 0.44, 0]) * size, np.array([-0.3, 0.36, 0]) * size)
    bag.set_fill(color, opacity=1.0).set_stroke(width=0)
    crimp = _bar(0.5 * size, 0.06 * size, "#ffd8a8", 0.9).move_to(np.array([0, 0.34, 0]) * size)
    chip = Ellipse(width=0.26 * size, height=0.18 * size).set_fill("#ffe2a0", 1).set_stroke(width=0).move_to(ORIGIN)
    return VGroup(bag, crimp, chip)


def icon_cube(size: float = 0.5) -> VGroup:
    """A metal cube (isometric)."""
    s = 0.42 * size
    c = np.array([0.0, 0.0, 0.0])
    top = Polygon(c + np.array([0, s, 0]), c + np.array([0.87 * s, 0.5 * s, 0]), c, c + np.array([-0.87 * s, 0.5 * s, 0]))
    left = Polygon(c + np.array([-0.87 * s, 0.5 * s, 0]), c, c + np.array([0, -s, 0]), c + np.array([-0.87 * s, -0.5 * s, 0]))
    right = Polygon(c + np.array([0.87 * s, 0.5 * s, 0]), c, c + np.array([0, -s, 0]), c + np.array([0.87 * s, -0.5 * s, 0]))
    for p, col in ((top, "#dfe4ec"), (left, METAL), (right, "#7f8896")):
        p.set_fill(col, opacity=1.0).set_stroke("#5d6573", width=1.0)
    return VGroup(top, left, right)


def icon_percent(size: float = 0.5, color=WARM) -> VGroup:
    """A discount chip: a % on a round chip."""
    disc = Circle(radius=0.5 * size).set_fill(color, opacity=1.0).set_stroke(width=0)
    pct = Text("%", font=LATIN_FONT, font_size=40, fill_color=BG, weight="BOLD")
    pct.set_height(0.52 * size).move_to(disc)
    return VGroup(disc, pct)


def icon_gift(size: float = 0.5, color=ACCENT) -> VGroup:
    box = Rectangle(width=0.8 * size, height=0.6 * size).set_fill(color, 1).set_stroke(width=0).shift(0.1 * size * DOWN)
    lid = Rectangle(width=0.9 * size, height=0.18 * size).set_fill(color, 1).set_stroke(BG, width=1.5)
    lid.next_to(box, UP, buff=0)
    rib = Rectangle(width=0.1 * size, height=0.78 * size).set_fill(INK, 1).set_stroke(width=0).move_to(VGroup(box, lid))
    bow = VGroup(*[Ellipse(width=0.26 * size, height=0.16 * size).set_fill(INK, 1).set_stroke(width=0)
                   .rotate(a).next_to(lid, UP, buff=-0.02).shift(0.11 * size * d) for a, d in ((0.5, LEFT), (-0.5, RIGHT))])
    return VGroup(box, lid, rib, bow)


def icon_star(size: float = 0.5, color=WARM) -> VMobject:
    pts = []
    for k in range(10):
        r = 0.5 * size if k % 2 == 0 else 0.21 * size
        a = PI / 2 + k * PI / 5
        pts.append(np.array([r * np.cos(a), r * np.sin(a), 0.0]))
    star = Polygon(*pts)
    star.set_fill(color, opacity=1.0).set_stroke(width=0)
    return star


def icon_clock(size: float = 0.8, color=INK_2) -> VGroup:
    """A clock face without numbers. Attributes: .face, .hour, .minute"""
    face = Circle(radius=0.5 * size).set_fill(CARD_FILL, 1).set_stroke(color, width=2.4)
    ticks = VGroup(*[Line(UP * 0.40 * size, UP * 0.46 * size).set_stroke(color, width=2).rotate(k * TAU / 12, about_point=ORIGIN)
                     for k in range(12)])
    hour = Line(ORIGIN, UP * 0.24 * size).set_stroke(INK, width=4)
    minute = Line(ORIGIN, UP * 0.38 * size).set_stroke(ACCENT, width=3)
    pin = Dot(radius=0.04 * size).set_fill(INK, 1)
    out = VGroup(face, ticks, hour, minute, pin)
    out.face, out.hour, out.minute = face, hour, minute
    return out


def icon_calendar(size: float = 1.0, color=INK_2) -> VGroup:
    """A month page: a header band and a grid of day squares (no numbers). Attributes: .days"""
    page = _card(size, 0.92 * size, stroke=color, r=0.06 * size, stroke_width=2.0)
    head = Rectangle(width=size, height=0.18 * size).set_fill(TIE, 0.9).set_stroke(width=0)
    head.align_to(page, UP)
    rings = VGroup(*[_bar(0.05 * size, 0.14 * size, INK) for _ in range(2)]).arrange(RIGHT, buff=0.4 * size)
    rings.move_to(head.get_top())
    days = VGroup(*[Square(side_length=0.1 * size).set_fill(INK_2, 0.35).set_stroke(width=0) for _ in range(35)])
    days.arrange_in_grid(5, 7, buff=0.03 * size)
    days.next_to(head, DOWN, buff=0.07 * size)
    out = VGroup(page, head, days, rings)
    out.days = days
    return out


def icon_phone(height: float = 3.0) -> VGroup:
    """A phone silhouette (no logo). Attributes: .body, .screen"""
    w = 0.5 * height
    body = RoundedRectangle(width=w, height=height, corner_radius=0.12 * height)
    body.set_fill("#1b2130", 1).set_stroke(INK_2, width=2.4)
    screen = RoundedRectangle(width=w - 0.14 * w, height=height - 0.1 * height, corner_radius=0.08 * height)
    screen.set_fill(BG, 1).set_stroke(width=0).move_to(body)
    notch = _bar(0.3 * w, 0.05 * height, "#1b2130").move_to(screen.get_top() + 0.04 * height * DOWN)
    out = VGroup(body, screen, notch)
    out.body, out.screen = body, screen
    return out


def icon_blazer(size: float = 1.0) -> VGroup:
    """A blue blazer with a red tie (the shopkeeper's 'I'll deliver it in person' moment)."""
    s = size
    left = Polygon(np.array([-0.06, 0.40, 0]) * s, np.array([-0.30, 0.34, 0]) * s, np.array([-0.46, 0.20, 0]) * s,
                   np.array([-0.46, -0.46, 0]) * s, np.array([-0.04, -0.46, 0]) * s, np.array([-0.04, -0.06, 0]) * s)
    right = left.copy().flip(UP, about_point=ORIGIN)
    for p in (left, right):
        p.set_fill(BLAZER, 1).set_stroke("#22417f", width=1.5)
    shirt = Polygon(np.array([-0.06, 0.40, 0]) * s, np.array([0.06, 0.40, 0]) * s, np.array([0.04, -0.06, 0]) * s,
                    np.array([-0.04, -0.06, 0]) * s)
    shirt.set_fill(INK, 1).set_stroke(width=0)
    tie = Polygon(np.array([0, 0.36, 0]) * s, np.array([0.05, 0.30, 0]) * s, np.array([0.035, -0.02, 0]) * s,
                  np.array([0, -0.10, 0]) * s, np.array([-0.035, -0.02, 0]) * s, np.array([-0.05, 0.30, 0]) * s)
    tie.set_fill(TIE, 1).set_stroke(width=0)
    lapels = VGroup(
        Polygon(np.array([-0.06, 0.40, 0]) * s, np.array([-0.18, 0.18, 0]) * s, np.array([-0.04, -0.04, 0]) * s),
        Polygon(np.array([0.06, 0.40, 0]) * s, np.array([0.18, 0.18, 0]) * s, np.array([0.04, -0.04, 0]) * s))
    lapels.set_fill("#2c55a6", 1).set_stroke("#22417f", width=1.0)
    buttons = VGroup(*[Dot(radius=0.02 * s).set_fill(INK_2, 1).move_to(np.array([0.13, y, 0]) * s) for y in (-0.18, -0.30)])
    return VGroup(left, right, shirt, lapels, tie, buttons)


def icon_button(size: float = 0.5) -> VGroup:
    base = Circle(radius=0.5 * size).set_fill("#2a3140", 1).set_stroke(INK_2, width=2)
    cap = Circle(radius=0.32 * size).set_fill(GREEN, 1).set_stroke(width=0)
    return VGroup(base, cap)


def icon_supplier(size: float = 0.6, color=INK_2) -> VGroup:
    """A small warehouse: the supplier."""
    body = Rectangle(width=0.9 * size, height=0.5 * size).set_fill(CARD_FILL, 1).set_stroke(color, width=1.8)
    roof = Polygon(body.get_corner(UL), body.get_corner(UR), body.get_top() + 0.3 * size * UP)
    roof.set_fill(CARD_FILL, 1).set_stroke(color, width=1.8)
    door = Rectangle(width=0.3 * size, height=0.32 * size).set_fill("#2a3140", 1).set_stroke(color, width=1.2)
    door.align_to(body, DOWN)
    return VGroup(body, roof, door)


def icon_check(size: float = 0.4, color=GREEN) -> VMobject:
    tick = Polyline(np.array([-0.4, 0.0, 0]) * size, np.array([-0.12, -0.3, 0]) * size, np.array([0.42, 0.34, 0]) * size)
    tick.set_stroke(color, width=5).set_fill(opacity=0)
    return tick


def icon_cross(size: float = 0.4, color=RED) -> VGroup:
    a = Line(np.array([-0.4, -0.4, 0]) * size, np.array([0.4, 0.4, 0]) * size).set_stroke(color, width=6)
    b = Line(np.array([-0.4, 0.4, 0]) * size, np.array([0.4, -0.4, 0]) * size).set_stroke(color, width=6)
    return VGroup(a, b)


def question_mark(height: float = 0.8, color=INK) -> Text:
    q = Text("?", font=LATIN_FONT, font_size=72, fill_color=color, weight="BOLD")
    q.set_height(height)
    return q


def thumbs_up(height: float = 0.6, color=ACCENT) -> SVGMobject:
    t = SVGMobject(str(REPO_ROOT / "assets" / "icons" / "thumbs_up.svg"))
    t.set_height(height)
    t.set_fill(color, opacity=1.0).set_stroke(width=0)
    return t


# ----------------------------------------------------------------------------
# The shop: fridge (+ baskets), iPad
# ----------------------------------------------------------------------------
def fridge(height: float = 3.2) -> VGroup:
    """The office fridge: glass door with shelves of drinks and snacks, two baskets on top.
    Attributes: .body, .door, .items, .baskets"""
    w = 0.56 * height
    body = RoundedRectangle(width=w, height=height, corner_radius=0.06 * height)
    body.set_fill(FRIDGE_BODY, 1).set_stroke(FRIDGE_EDGE, width=2.4)
    door = RoundedRectangle(width=w - 0.14 * w, height=height - 0.2 * height, corner_radius=0.03 * height)
    door.set_fill(GLASS, 1).set_stroke(FRIDGE_EDGE, width=1.6)
    door.move_to(body).shift(0.04 * height * UP)
    handle = _bar(0.035 * height, 0.3 * height, FRIDGE_EDGE).next_to(door, LEFT, buff=-0.08 * w).shift(0.1 * height * UP)
    vent = VGroup(*[_bar(0.6 * w, 0.012 * height, FRIDGE_EDGE, 0.6) for _ in range(3)]).arrange(DOWN, buff=0.02 * height)
    vent.next_to(door, DOWN, buff=0.03 * height)
    shelves, items = VGroup(), VGroup()
    rows = 4
    colors = [[TIE, TIE, ACCENT, ACCENT], [WARM, WARM, INK_2, TIE], [ACCENT, "#f2d06b", "#f2d06b", WARM], [INK_2, TIE, ACCENT, WARM]]
    for r in range(rows):
        y = door.get_top()[1] - (r + 1) * door.get_height() / rows + 0.02 * height
        sh = Line(np.array([door.get_left()[0] + 0.04, y, 0]), np.array([door.get_right()[0] - 0.04, y, 0]))
        sh.set_stroke(FRIDGE_EDGE, width=1.4, opacity=0.8)
        shelves.add(sh)
        row = VGroup(*[RoundedRectangle(width=0.09 * height, height=0.15 * height, corner_radius=0.02 * height)
                       .set_fill(c, 0.9).set_stroke(width=0) for c in colors[r]]).arrange(RIGHT, buff=0.04 * height)
        row.move_to(np.array([door.get_center()[0], y + 0.085 * height, 0]))
        items.add(row)
    baskets = VGroup()
    for k in (-1, 1):
        bw = 0.42 * w
        bk = Polygon(np.array([-bw / 2, 0.16 * height * 0.5, 0]), np.array([bw / 2, 0.16 * height * 0.5, 0]),
                     np.array([0.42 * bw, -0.08 * height * 0.5, 0]), np.array([-0.42 * bw, -0.08 * height * 0.5, 0]))
        bk.set_fill("#3b4559", 1).set_stroke(FRIDGE_EDGE, width=1.4)
        snacks = VGroup(*[RoundedRectangle(width=0.07 * height, height=0.08 * height, corner_radius=0.015 * height)
                          .set_fill(c, 1).set_stroke(width=0) for c in ((WARM, "#f2d06b", TIE) if k < 0 else (ACCENT, WARM, INK_2))])
        snacks.arrange(RIGHT, buff=0.015 * height).next_to(bk, UP, buff=-0.04 * height)
        basket = VGroup(snacks, bk)
        basket.next_to(body, UP, buff=0.0).shift(k * 0.24 * w * RIGHT)
        baskets.add(basket)
    out = VGroup(body, door, shelves, items, handle, vent, baskets)
    out.body, out.door, out.items, out.baskets = body, door, items, baskets
    return out


def ipad(width: float = 1.2) -> VGroup:
    """The self-checkout iPad on a small stand; its screen holds a tiny teal cursor (the AI is in there).
    Attributes: .frame, .screen, .cursor"""
    h = 0.74 * width
    frame = RoundedRectangle(width=width, height=h, corner_radius=0.08 * width)
    frame.set_fill("#1b2130", 1).set_stroke(INK_2, width=2.0)
    screen = RoundedRectangle(width=width - 0.12 * width, height=h - 0.12 * width, corner_radius=0.05 * width)
    screen.set_fill("#0c1a1f", 1).set_stroke(width=0).move_to(frame)
    cur = cursor(height=0.24 * h).move_to(screen)
    stand = Polygon(frame.get_bottom() + 0.08 * width * LEFT, frame.get_bottom() + 0.08 * width * RIGHT,
                    frame.get_bottom() + np.array([0.16 * width, -0.42 * h, 0]), frame.get_bottom() + np.array([-0.16 * width, -0.42 * h, 0]))
    stand.set_fill("#3b4559", 1).set_stroke(FRIDGE_EDGE, width=1.2)
    out = VGroup(stand, frame, screen, cur)
    out.frame, out.screen, out.cursor = frame, screen, cur
    return out


# ----------------------------------------------------------------------------
# The tools guide (دليل الأدوات) and the shop's price menu (منيو المحل)
# ----------------------------------------------------------------------------
_TOOL_ICONS = [lambda s: envelope(0.82 * s), lambda s: icon_bubble(0.82 * s), icon_search, icon_note, icon_shelves]
_TOOL_BLANKS = [2, 2, 1, 1, 1]


def tool_row(i: int, width: float = 4.4, height: float = 0.46, name_size: int = 26, seed: int = 0) -> VGroup:
    """One tool: icon · name · one line about it · blanks to fill (right to left, the way Arabic reads).
    Attributes: .icon, .name, .desc, .blanks, .bg"""
    bg = _card(width, height, stroke=CARD_STROKE, fill="#1a2030", r=0.08, stroke_width=1.2)
    icon = _TOOL_ICONS[i](0.62 * height)
    icon.move_to(bg.get_right() + 0.34 * height * LEFT * 1.25)
    name = ar_text(TOOL_NAMES_AR[i], font_size=name_size, color=INK)
    name.set_height(min(name.get_height(), 0.5 * height))
    name.next_to(icon, LEFT, buff=0.16)
    blanks = VGroup(*[RoundedRectangle(width=0.46 * height * 1.45, height=0.5 * height, corner_radius=0.06)
                      .set_fill(BG, 1).set_stroke(INK_2, width=1.4) for _ in range(_TOOL_BLANKS[i])])
    blanks.arrange(RIGHT, buff=0.08).move_to(bg.get_left() + (blanks.get_width() / 2 + 0.14) * RIGHT)
    room = name.get_left()[0] - blanks.get_right()[0] - 0.3
    desc = text_lines(max(room, 0.3), n=1, height=0.055, color=INK_2, opacity=0.5, seed=10 + i + seed)
    desc.move_to(np.array([(name.get_left()[0] + blanks.get_right()[0]) / 2, bg.get_y(), 0]))
    out = VGroup(bg, icon, name, desc, blanks)
    out.bg, out.icon, out.name, out.desc, out.blanks = bg, icon, name, desc, blanks
    return out


def tools_guide(width: float = 4.4, row_h: float = 0.46, rows: tuple = (0, 1, 2, 3, 4), title: bool = True) -> VGroup:
    """The written list of tools the writer is handed. Attributes: .card, .title, .rows"""
    rws = VGroup(*[tool_row(i, width - 0.3, row_h) for i in rows]).arrange(DOWN, buff=0.08)
    parts = [rws]
    ttl = None
    if title:
        ttl = ar_text(GUIDE_TITLE_AR, font_size=30, color=ACCENT)
        ttl.set_height(0.36)
        parts.insert(0, ttl)
    inner = VGroup(*parts).arrange(DOWN, buff=0.14)
    if ttl is not None:
        ttl.align_to(rws, RIGHT)
    card = _card(width, inner.get_height() + 0.36, stroke=ACCENT, r=0.16, stroke_width=2.2)
    card.move_to(inner)
    out = VGroup(card, *parts)
    out.card, out.title, out.rows = card, ttl, rws
    return out


def filled_row_slip(values_ar: list[str], height: float = 0.5, name_size: int = 26) -> VGroup:
    """A request written as the email row with its blanks filled: name · value · value (a teal slip).
    Attributes: .card, .name, .values"""
    name = ar_text(TOOL_NAMES_AR[0], font_size=name_size, color=INK)
    name.set_height(min(name.get_height(), 0.5 * height))
    vals = VGroup()
    for v in values_ar:
        t = ar_text(v, font_size=name_size - 2, color=INK)
        t.set_height(min(t.get_height(), 0.46 * height))
        box = RoundedRectangle(width=t.get_width() + 0.3, height=0.72 * height, corner_radius=0.06)
        box.set_fill(BG, 1).set_stroke(ACCENT, width=1.4)
        t.move_to(box)
        vals.add(VGroup(box, t))
    vals.arrange(LEFT, buff=0.1)
    inner = VGroup(name, vals).arrange(LEFT, buff=0.2)
    card = _card(inner.get_width() + 0.5, height, stroke=ACCENT, r=0.08, stroke_width=2.0)
    card.move_to(inner)
    edge = _bar(0.07, height - 0.10, ACCENT, 0.95).move_to(card.get_right() + 0.075 * LEFT)
    inner.shift(0.04 * LEFT)
    out = VGroup(card, edge, name, vals)
    out.card, out.name, out.values = card, name, vals
    return out


_ITEM_ICONS = [lambda s: icon_can(s, TIE), lambda s: icon_chips(s, WARM), icon_cube]
ITEM_PRICE = [0.62, 0.50, 0.40]      # bar lengths (relative), no numbers on screen
ITEM_COST = [0.40, 0.30, 0.74]       # the cube costs more than it sells for


def dashed_box(width: float, height: float, color=INK_2, opacity: float = 0.9) -> VMobject:
    box = DashedVMobject(Rectangle(width=width, height=height), num_dashes=max(8, int(2 * (width + height) / 0.12)),
                         positive_space_ratio=0.55)
    box.set_stroke(color, width=1.8, opacity=opacity)
    return box


def price_menu(width: float = 4.6, row_h: float = 0.62, show_cost: bool = False, title: bool = True) -> VGroup:
    """The shop's price menu. Per item, two bars right-aligned so they compare at a glance: what it
    sells for (amber, a tag before it) and, under it, what it paid (a box before it): an empty dashed
    slot until round two, then a bar (red where it is longer than the price). No numbers on screen.
    Attributes: .card, .title, .rows (each: .icon, .name, .price, .cost_slot, .cost, .q)"""
    unit = 1.6
    rows = VGroup()
    heads = []
    for i in range(3):
        bg = _card(width - 0.3, row_h, stroke=CARD_STROKE, fill="#1a2030", r=0.08, stroke_width=1.2)
        icon = _ITEM_ICONS[i](0.6 * row_h)
        icon.move_to(bg.get_right() + 0.4 * row_h * LEFT)
        name = ar_text(ITEM_NAMES_AR[i], font_size=24, color=INK)
        name.set_height(min(name.get_height(), 0.4 * row_h))
        name.next_to(icon, LEFT, buff=0.14)
        heads.append((bg, icon, name))
    x_r = min(n.get_left()[0] for _, _, n in heads) - 0.5      # bars end here; the small tag / box sit after it
    for i, (bg, icon, name) in enumerate(heads):
        y_p, y_c = bg.get_y() + 0.15 * row_h, bg.get_y() - 0.17 * row_h
        bh = 0.17 * row_h
        price = _bar(ITEM_PRICE[i] * unit, bh, WARM).move_to(np.array([x_r, y_p, 0]), aligned_edge=RIGHT)
        tag = icon_tag(0.2, WARM).move_to(np.array([x_r + 0.22, y_p, 0]))
        slot = dashed_box(0.92 * unit, bh + 0.06).move_to(np.array([x_r, y_c, 0]), aligned_edge=RIGHT)
        box = icon_box(0.17).move_to(np.array([x_r + 0.22, y_c, 0]))
        lossy = ITEM_COST[i] > ITEM_PRICE[i]
        cost = _bar(ITEM_COST[i] * unit, bh, RED if lossy else HANDS).move_to(np.array([x_r, y_c, 0]), aligned_edge=RIGHT)
        q = question_mark(0.26, INK_2).move_to(slot)
        row = VGroup(bg, icon, name, tag, price, box, slot)
        row.bg, row.icon, row.name, row.price, row.cost_slot, row.cost, row.q = bg, icon, name, price, slot, cost, q
        row.tag, row.box = tag, box
        if show_cost:
            row.add(cost)
        rows.add(row)
    rows.arrange(DOWN, buff=0.08)
    parts = [rows]
    ttl = None
    if title:
        ttl = ar_text(MENU_TITLE_AR, font_size=30, color=WARM)
        ttl.set_height(0.36)
        ttl.next_to(rows, UP, buff=0.16).align_to(rows, RIGHT)
        parts.insert(0, ttl)
    inner = VGroup(*parts)
    card = _card(width, inner.get_height() + 0.36, stroke=WARM, r=0.16, stroke_width=2.2)
    card.move_to(inner)
    out = VGroup(card, *parts)
    out.card, out.title, out.rows = card, ttl, rows
    return out


# ----------------------------------------------------------------------------
# The desk (what the writer can see this lap), the notebook, the to-do, the summary
# ----------------------------------------------------------------------------
def desk(width: float = 7.4, depth: float = 0.32) -> VGroup:
    """A tray of fixed width the slips lie on. Attributes: .top, .front"""
    top = Polygon(np.array([-width / 2, 0, 0]), np.array([width / 2, 0, 0]), np.array([width / 2 - 0.25, depth, 0]),
                  np.array([-width / 2 + 0.25, depth, 0]))
    top.set_fill(DESK_FILL, 1).set_stroke(DESK_EDGE, width=1.8)
    front = Rectangle(width=width, height=0.16).set_fill("#141927", 1).set_stroke(DESK_EDGE, width=1.8)
    front.next_to(top, DOWN, buff=0)
    out = VGroup(top, front)
    out.top, out.front = top, front
    return out


def notebook(width: float = 1.0, height: float = 1.2) -> VGroup:
    """A small notebook pinned to the desk: survives what falls off. Attributes: .page, .lines, .pin"""
    page = _card(width, height, stroke=INK_2, fill="#1f2636", r=0.06, stroke_width=2.0)
    rings = VGroup(*[Circle(radius=0.035).set_stroke(INK_2, width=1.6).set_fill(BG, 1) for _ in range(5)])
    rings.arrange(RIGHT, buff=0.1).move_to(page.get_top() + 0.06 * DOWN)
    lines = VGroup(*[Line(LEFT * width * 0.36, RIGHT * width * 0.36).set_stroke(INK_2, width=1.0, opacity=0.45)
                     for _ in range(5)]).arrange(DOWN, buff=height * 0.13)
    lines.move_to(page).shift(0.06 * DOWN)
    pin = Dot(radius=0.07).set_fill(TIE, 1).move_to(page.get_corner(UR) + np.array([-0.12, -0.12, 0]))
    out = VGroup(page, lines, rings, pin)
    out.page, out.lines, out.pin = page, lines, pin
    return out


def todo_card(width: float = 1.0, height: float = 1.1) -> VGroup:
    """The to-do list put back in front every lap: three boxes and short lines (one ticked). Attributes: .boxes"""
    page = _card(width, height, stroke=ACCENT, fill="#14202a", r=0.06, stroke_width=2.0)
    rows, boxes = VGroup(), VGroup()
    for k in range(3):
        b = Square(side_length=0.14).set_stroke(ACCENT, width=1.6).set_fill(opacity=0)
        ln = _bar(0.45 * width, 0.05, INK_2, 0.6)
        row = VGroup(ln, b).arrange(RIGHT, buff=0.1)
        rows.add(row)
        boxes.add(b)
    rows.arrange(DOWN, buff=0.16, aligned_edge=RIGHT).move_to(page)
    tick = icon_check(0.22, ACCENT).move_to(boxes[0])
    out = VGroup(page, rows, tick)
    out.page, out.boxes = page, boxes
    return out


def job_card(width: float = 1.0, height: float = 1.1) -> VGroup:
    """The job (what the shop is for): a card with a target mark."""
    page = _card(width, height, stroke=INK_2, fill="#1f2636", r=0.06, stroke_width=2.0)
    target = VGroup(*[Circle(radius=r).set_stroke(c, width=2.2).set_fill(opacity=0)
                      for r, c in ((0.26, INK_2), (0.16, TIE), (0.06, TIE))])
    target[-1].set_fill(TIE, 1)
    target.move_to(page).shift(0.1 * UP)
    line = _bar(0.5 * width, 0.05, INK_2, 0.6).next_to(target, DOWN, buff=0.14)
    return VGroup(page, target, line)


def checklist_card(width: float = 2.3) -> VGroup:
    """Round two's checklist (CHECKLIST_AR), pinned to the desk. Attributes: .page, .items, .boxes, .ticks"""
    items, boxes, ticks = VGroup(), VGroup(), VGroup()
    for s in CHECKLIST_AR:
        t = ar_text(s, font_size=24, color=INK)
        t.set_height(min(t.get_height(), 0.3))
        b = Square(side_length=0.2).set_stroke(GREEN, width=1.8).set_fill(opacity=0)
        row = VGroup(t, b).arrange(RIGHT, buff=0.14)
        items.add(row)
        boxes.add(b)
        ticks.add(icon_check(0.26, GREEN).move_to(b).shift(0.03 * UP))
    items.arrange(DOWN, buff=0.14, aligned_edge=RIGHT)
    page = _card(max(width, items.get_width() + 0.4), items.get_height() + 0.4, stroke=GREEN, fill="#14211b", r=0.08)
    page.move_to(items)
    pin = Dot(radius=0.07).set_fill(TIE, 1).move_to(page.get_corner(UR) + np.array([-0.12, -0.12, 0]))
    out = VGroup(page, items, pin)
    out.page, out.items, out.boxes, out.ticks = page, items, boxes, ticks
    return out


# ----------------------------------------------------------------------------
# The dial (yes / no odds), plugs and the shared socket
# ----------------------------------------------------------------------------
class Dial(VGroup):
    """A semicircle gauge from «لأ» to «أكيد» with a needle, and the two odds as bars underneath.
    set_value(v): 0 = no, 1 = yes (the needle and the bars follow)."""

    def __init__(self, radius: float = 1.6, **kwargs):
        super().__init__(**kwargs)
        self.radius = radius
        track = Arc(start_angle=0, angle=PI, radius=radius).set_stroke(CARD_STROKE, width=14)
        n = 24
        grad = VGroup()
        for k in range(n):
            a0 = PI - k * PI / n
            seg = Arc(start_angle=a0 - PI / n, angle=PI / n * 0.92, radius=radius)
            mix = k / (n - 1)
            seg.set_stroke(interpolate_color(MUTED, ACCENT, mix), width=10)
            grad.add(seg)
        ticks = VGroup(*[Line(UP * (radius - 0.24), UP * (radius - 0.08)).rotate(-PI / 2 + k * PI / 8, about_point=ORIGIN)
                         .set_stroke(INK_2, width=2) for k in range(9)])
        no = ar_text(DIAL_NO_AR, font_size=34, color=INK_2).next_to(np.array([-radius, 0, 0]), DOWN, buff=0.2)
        yes = ar_text(DIAL_YES_AR, font_size=34, color=ACCENT).next_to(np.array([radius, 0, 0]), DOWN, buff=0.2)
        hub = Circle(radius=0.12).set_fill(INK, 1).set_stroke(width=0)
        needle = Polygon(np.array([-0.06, 0, 0]), np.array([0.06, 0, 0]), np.array([0, radius - 0.18, 0]))
        needle.set_fill(INK, 1).set_stroke(width=0)
        self.track, self.grad, self.ticks, self.no, self.yes, self.hub = track, grad, ticks, no, yes, hub
        self.needle = needle
        self.value = 0.5
        bw = 1.15 * radius
        self.bar_no_bg = _bar(bw, 0.16, CARD_STROKE).move_to(np.array([-0.62 * radius, -0.95, 0]))
        self.bar_yes_bg = _bar(bw, 0.16, CARD_STROKE).move_to(np.array([0.62 * radius, -0.95, 0]))
        self.bar_no = _bar(bw * 0.5, 0.16, MUTED)
        self.bar_yes = _bar(bw * 0.5, 0.16, ACCENT)
        self.bar_w = bw
        self.add(track, grad, ticks, no, yes, self.bar_no_bg, self.bar_yes_bg, self.bar_no, self.bar_yes, needle, hub)
        self._place(0.5)

    def _place(self, v: float) -> None:
        v = float(np.clip(v, 0.0, 1.0))
        c = self.hub.get_center()
        ang = (0.5 - v) * PI
        self.needle.become(Polygon(np.array([-0.06, 0, 0]), np.array([0.06, 0, 0]), np.array([0, self.radius - 0.18, 0]))
                           .set_fill(INK, 1).set_stroke(width=0).rotate(ang, about_point=ORIGIN).shift(c))
        bw = self.bar_w
        no_w, yes_w = max(bw * (1 - v), 0.02), max(bw * v, 0.02)
        self.bar_no.become(_bar(no_w, 0.16, MUTED).move_to(self.bar_no_bg.get_right(), aligned_edge=RIGHT))
        self.bar_yes.become(_bar(yes_w, 0.16, ACCENT).move_to(self.bar_yes_bg.get_left(), aligned_edge=LEFT))
        self.value = v

    def set_value(self, v: float) -> "Dial":
        self._place(v)
        return self

    def animate_to(self, v: float, run_time: float = 0.8, rate_func=smooth) -> Animation:
        v0 = self.value

        def upd(m, a):
            m._place(v0 + (v - v0) * a)
        return UpdateFromAlphaFunc(self, upd, run_time=run_time, rate_func=rate_func)


def dial(radius: float = 1.6) -> Dial:
    return Dial(radius=radius)


_PLUG_COLORS = [TIE, WARM, "#f2d06b", "#8e7cf0", "#5fb3f0"]


def plug(kind: int, size: float = 0.7, color=None) -> VGroup:
    """An app's plug: a body with a differently shaped tip per kind (0..4); kind -1 = the shared shape.
    Attributes: .body, .tip"""
    color = color or (_PLUG_COLORS[kind % 5] if kind >= 0 else ACCENT)
    body = RoundedRectangle(width=0.62 * size, height=0.5 * size, corner_radius=0.08 * size)
    body.set_fill(color, 1).set_stroke(width=0)
    cord = Line(body.get_bottom(), body.get_bottom() + 0.5 * size * DOWN).set_stroke(color, width=4)
    tip_c = body.get_top() + 0.16 * size * UP
    s = 0.13 * size
    if kind == 0:
        tip = VGroup(*[Circle(radius=s * 0.6).move_to(tip_c + d * 0.13 * size) for d in (LEFT, RIGHT)])
    elif kind == 1:
        tip = Square(side_length=2 * s).move_to(tip_c)
    elif kind == 2:
        tip = Triangle().set_height(2.2 * s).move_to(tip_c)
    elif kind == 3:
        tip = VGroup(*[Rectangle(width=0.5 * s, height=2.2 * s).move_to(tip_c + d * 0.12 * size) for d in (LEFT, ORIGIN, RIGHT)])
    elif kind == 4:
        tip = icon_star(3 * s).move_to(tip_c)
    else:
        tip = VGroup(*[RoundedRectangle(width=0.55 * s, height=2.0 * s, corner_radius=0.2 * s).move_to(tip_c + d * 0.11 * size)
                       for d in (LEFT, RIGHT)])
    tip.set_fill(INK_2, 1).set_stroke(width=0)
    out = VGroup(cord, body, tip)
    out.body, out.tip = body, tip
    return out


def socket(size: float = 1.0) -> VGroup:
    """The one shared socket (MCP, 2024): a plate whose slots fit the shared plug shape."""
    plate = RoundedRectangle(width=1.2 * size, height=0.9 * size, corner_radius=0.16 * size)
    plate.set_fill(CARD_FILL, 1).set_stroke(ACCENT, width=2.6)
    s = 0.13 * size * 0.7
    slots = VGroup(*[RoundedRectangle(width=0.55 * s * 1.1, height=2.0 * s * 1.1, corner_radius=0.2 * s)
                     .set_fill(BG, 1).set_stroke(ACCENT, width=1.4).move_to(plate.get_center() + d * 0.11 * size * 0.7)
                     for d in (LEFT, RIGHT)])
    return VGroup(plate, slots)


# ----------------------------------------------------------------------------
# The world node and the master diagram
# ----------------------------------------------------------------------------
def world_node(size: float = 2.2) -> VGroup:
    """Everything outside: the fridge, the supplier, the customers (amber). Attributes: .card, .fridge, .supplier, .customers"""
    card = _card(size, 1.12 * size, stroke=WARM, fill="#1c1a17", r=0.2, stroke_width=2.4)
    fr = fridge(0.62 * size)
    fr.move_to(card.get_center() + np.array([0.22 * size, 0.06 * size, 0]))
    sup = icon_supplier(0.34 * size).move_to(card.get_center() + np.array([-0.26 * size, 0.22 * size, 0]))
    cust = icon_bubble(0.3 * size, WARM).move_to(card.get_center() + np.array([-0.26 * size, -0.2 * size, 0]))
    out = VGroup(card, fr, sup, cust)
    out.card, out.fridge, out.supplier, out.customers = card, fr, sup, cust
    return out


# Master layout (docs/agents_plan.md §4): the same places in every bit.
WRITER_C = np.array([-2.65, 0.60, 0.0])
HANDS_C = np.array([1.30, 0.60, 0.0])
WORLD_C = np.array([4.60, 0.60, 0.0])
GUIDE_C = np.array([-2.65, 2.55, 0.0])
DESK_Y = -2.50
DESK_X0, DESK_X1 = -5.90, 1.70          # the desk spans this; slips lie on it, oldest at the left
SLIP_Y = DESK_Y + 0.55                  # where slips sit on the desk
SLIP_W = 1.1                            # a slip's width on the desk
RETURN_Y = -3.25                        # the result slips' way back runs under the desk


def arrow(a, b, color=INK_2, thickness: float = 3.0, buff: float = 0.08) -> Arrow:
    ar = Arrow(a, b, buff=buff, thickness=thickness)
    ar.set_fill(color, opacity=1.0).set_stroke(width=0)
    return ar


def return_path() -> VMobject:
    """From under the world, down and left under the desk, up into the desk's right end."""
    p = VMobject()
    a = WORLD_C + np.array([0.0, -1.15, 0])
    p.start_new_path(a)
    p.add_line_to(np.array([WORLD_C[0], RETURN_Y + 0.25, 0]))
    p.add_quadratic_bezier_curve_to(np.array([WORLD_C[0], RETURN_Y, 0]), np.array([WORLD_C[0] - 0.25, RETURN_Y, 0]))
    p.add_line_to(np.array([DESK_X1 + 0.6, RETURN_Y, 0]))
    p.add_quadratic_bezier_curve_to(np.array([DESK_X1 + 0.35, RETURN_Y, 0]), np.array([DESK_X1 + 0.35, RETURN_Y + 0.25, 0]))
    p.add_line_to(np.array([DESK_X1 + 0.35, SLIP_Y, 0]))
    p.set_stroke(WARM, width=2.2, opacity=0.55)
    p.set_fill(opacity=0)
    return p


def master(guide: bool = False, desk_on: bool = False, menu: bool = False) -> SimpleNamespace:
    """The master diagram's parts, each at its place (not added to the scene).
    .writer .hands .world .to_hands .to_world .back (+ .guide, .desk, .view when asked)"""
    w = writer_box().move_to(WRITER_C)
    h = hands_box().move_to(HANDS_C)
    wd = world_node().move_to(WORLD_C)
    to_hands = arrow(w.get_right(), h.get_left(), ACCENT, buff=0.12)
    to_world = arrow(h.get_right(), wd.get_left(), HANDS, buff=0.12)
    back = return_path()
    ns = SimpleNamespace(writer=w, hands=h, world=wd, to_hands=to_hands, to_world=to_world, back=back)
    if guide:
        g = tools_guide(width=4.0, row_h=0.36)
        g.set_height(1.75).move_to(GUIDE_C)
        ns.guide = g
    if desk_on:
        d = desk(width=DESK_X1 - DESK_X0).move_to(np.array([(DESK_X0 + DESK_X1) / 2, DESK_Y, 0]), aligned_edge=UP)
        d.shift((DESK_Y - d.top.get_bottom()[1]) * UP)
        ns.desk = d
        ns.view = view_cone(w, d)
    return ns


N_ROW = 6                                           # slips the row / desk shows before the oldest slide off
CUR_POS = WRITER_C + np.array([1.52, 0.45, 0])      # where the writer's cursor waits (right of its box)
REQ_POS = np.array([0.45, 2.40, 0])                 # a written request, above the lane, clear of the tools guide
LANE_Y = SLIP_Y + 0.66                              # the loop's bottom lane runs just above the row / desk


def loop_lane() -> VGroup:
    """The loop as a closed lane: writer -> hands, down, back along the row, up into the writer."""
    x0, x1, y0, y1, r = WRITER_C[0], HANDS_C[0], LANE_Y, WRITER_C[1], 0.35
    path = VMobject()
    path.start_new_path(np.array([x0 + r, y1, 0]))
    path.add_line_to(np.array([x1 - r, y1, 0]))
    path.add_quadratic_bezier_curve_to(np.array([x1, y1, 0]), np.array([x1, y1 - r, 0]))
    path.add_line_to(np.array([x1, y0 + r, 0]))
    path.add_quadratic_bezier_curve_to(np.array([x1, y0, 0]), np.array([x1 - r, y0, 0]))
    path.add_line_to(np.array([x0 + r, y0, 0]))
    path.add_quadratic_bezier_curve_to(np.array([x0, y0, 0]), np.array([x0, y0 + r, 0]))
    path.add_line_to(np.array([x0, y1 - r, 0]))
    path.add_quadratic_bezier_curve_to(np.array([x0, y1, 0]), np.array([x0 + r, y1, 0]))
    path.set_stroke(ACCENT, width=3, opacity=0.6).set_fill(opacity=0)
    dashed = DashedVMobject(path, num_dashes=60, positive_space_ratio=0.6)
    dashed.set_stroke(ACCENT, width=3, opacity=0.6)
    heads = VGroup()
    for pos, ang in ((np.array([x1, (y0 + y1) / 2, 0]), -PI / 2), (np.array([(x0 + x1) / 2, y0, 0]), PI),
                     (np.array([x0, (y0 + y1) / 2 - 0.3, 0]), PI / 2)):
        tip = Triangle().set_height(0.22).set_fill(ACCENT, 0.85).set_stroke(width=0)
        tip.rotate(ang - PI / 2).move_to(pos)
        heads.add(tip)
    out = VGroup(dashed, heads)
    out.path = path
    return out


def view_cone(writer: Mobject, d: Mobject, opacity: float = 0.10) -> VMobject:
    """The writer's soft highlight: from its bottom edge down over the desk, and never past it."""
    top_l, top_r = writer.get_corner(DL) + 0.2 * RIGHT, writer.get_corner(DR) + 0.2 * LEFT
    bot_l = np.array([d.get_left()[0], d.get_top()[1], 0])
    bot_r = np.array([d.get_right()[0], d.get_top()[1], 0])
    cone = Polygon(top_l, top_r, bot_r, bot_l)
    cone.set_fill(ACCENT, opacity=opacity).set_stroke(width=0)
    return cone


def desk_slot(i: int, n: int, width: float = SLIP_W) -> np.ndarray:
    """Center of the i-th of n slips laid on the desk from the left (oldest) to the right (newest)."""
    span = DESK_X1 - DESK_X0 - 0.4
    step = min(width + 0.12, span / max(n, 1))
    return np.array([DESK_X0 + 0.2 + step * (i + 0.5), SLIP_Y, 0])


def row_of_slips(n: int = N_ROW, seed: int = 0, kinds: list[str] | None = None) -> VGroup:
    """n slips lying on the row / desk (oldest at the left), at desk_slot(i, N_ROW); mostly results."""
    kinds = kinds or ["request" if (i + seed) % 3 == 0 else "result" for i in range(n)]
    return VGroup(*[slip(kind=kinds[i], width=SLIP_W, seed=seed + i).move_to(desk_slot(i, N_ROW)) for i in range(n)])


def loop_ring(center=None, radius: float = 3.2, color=ACCENT, opacity: float = 0.55) -> VGroup:
    """The loop drawn as a dashed ring with two arrowheads (clockwise)."""
    center = WRITER_C * 0 + np.array([0.6, 0.2, 0]) if center is None else center
    ring = DashedVMobject(Circle(radius=radius), num_dashes=48, positive_space_ratio=0.55)
    ring.set_stroke(color, width=3, opacity=opacity)
    ring.move_to(center)
    heads = VGroup()
    for ang in (PI / 2 + 0.2, -PI / 2 + 0.2):
        tip = Triangle().set_height(0.22).set_fill(color, opacity).set_stroke(width=0)
        pos = center + radius * np.array([np.cos(ang), np.sin(ang), 0])
        tip.rotate(ang - PI).move_to(pos)
        heads.add(tip)
    return VGroup(ring, heads)


Z_BACK, Z_FLY = -1, 2


def behind(mob: Mobject) -> Mobject:
    """Draw under the boxes. ManimGL batches neighbouring mobjects of one type and paints all their fills
    before any of their strokes, so a stroke-only path would show through a box's fill; a lower z_index
    puts it in its own batch, painted first."""
    return mob.set_z_index(Z_BACK)


def flying(mob: Mobject) -> Mobject:
    """Draw over everything else (a slip or envelope on its way), for the same batching reason."""
    return mob.set_z_index(Z_FLY)


def write_rtl(text_mob: Mobject, **kwargs) -> Animation:
    """Write Arabic text from right to left (its glyphs come in visual, left-to-right order)."""
    text_mob.set_submobjects(list(reversed(text_mob.submobjects)))
    return Write(text_mob, **kwargs)


def dim(mob: Mobject, opacity: float = 0.25) -> Mobject:
    """Fade a part back (keeps it on screen)."""
    return mob.set_opacity(opacity)


# ----------------------------------------------------------------------------
# Scenes
# ----------------------------------------------------------------------------
class AgentScene(NarratedScene):
    """NarratedScene on the house background, with word anchors: inside `with self.narrate(key)`,
    self.until("word") waits until just before that word of the line is spoken (line_word_at),
    and self.to("word") is the time left until then (to size an animation that should land on it)."""

    def setup(self):
        super().setup()
        self.camera.background_rgba = list(color_to_rgba(BG))

    def _word_t(self, needle: str, lead: float) -> float:
        ln = self._line
        if ln is None:
            raise RuntimeError("until()/to() only inside a narrate() block")
        return ln["start"] + line_word_at(ln["key"], needle) - lead

    def until(self, needle: str, lead: float = 0.12) -> None:
        t = self._word_t(needle, lead)
        if t > self.time + 1e-3:
            self.wait(t - self.time)

    def to(self, needle: str, lead: float = 0.12, minimum: float = 0.25) -> float:
        return max(minimum, self._word_t(needle, lead) - self.time)

    def blink_for(self, mob: Mobject, seconds: float, period: float = 0.5) -> None:
        """Blink a cursor for about `seconds` (whole blinks; at least one)."""
        n = max(1, int(round(seconds / period)))
        self.play(blink(mob, n=n, period=seconds / n))

    def continue_from(self, prev_scene: str, fade: float = 0.45) -> None:
        """Open on the previous segment's exact last frame (media/frames/<prev_scene>_last.png, saved by
        scripts/render_segments.py after each render) and dissolve it into this scene's own first frame over
        `fade` seconds, on its own clock: the cut between segments is seamless and no timing changes. A no-op
        when the frame isn't there (render the previous segment first)."""
        path = MEDIA_DIR / "frames" / f"{prev_scene}_last.png"
        if not path.is_file():
            return
        img = ImageMobject(str(path))
        img.set_height(FRAME_HEIGHT).move_to(ORIGIN)
        img.set_z_index(50)
        t0 = self.time

        def upd(m, dt):
            a = min(1.0, (self.time - t0) / fade)
            m.set_opacity(1.0 - smooth(a))
            if a >= 1.0:
                m.clear_updaters()
        img.add_updater(upd)
        self.add(img)

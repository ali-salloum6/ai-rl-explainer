"""
Shared visual kit, copied from video 2 (ai-image-explainer) for video 4.

Generic and meant to be reused here: the palette (BG, INK, ACCENT, WARM, CARD_*), ar_text,
word_chip, user_bubble, reply_card, model_box, cursor, ribbon, safe_rect and the narration
timing (NarratedScene, line_duration, line_word_at). Video 2 only, kept as reference until
this video's scenes exist: the hero face raster, tiles/glyphs, the printer and the *_AR strings.
Prune those once nothing here imports them.

Every scene file does:

    import sys
    from pathlib import Path
    _REPO_ROOT = Path(__file__).resolve().parent.parent
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from our_scenes.kit import *          # re-exports manimlib too

Design rules baked in (see docs/image_plan.md §0 and the beat-spine memo):
  * a tile is a CODE from a learned alphabet — glyphs are abstract two-tone
    geometric marks, never digits / letters / QR-ish patterns;
  * no numbers on screen (the glyph tray ends in an ellipsis);
  * the only on-screen strings are the *_AR constants below;
  * the printer is a visibly smaller WARM box; the writer is an ACCENT box;
  * everything is deterministic (seeded noise, fixed tile→glyph clustering).

Engine: ManimGL 1.7.2 (3b1b manimlib). Frame 16:9, FRAME_WIDTH≈14.2, height 8.
"""
from __future__ import annotations

import hashlib
import os
import tempfile
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from manimlib import *
from manimlib.mobject.boolean_ops import Union
from manimlib.mobject.svg.text_mobject import register_font
from manimlib.utils.color import rgb_to_hex

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
AMIRI_PATH: str = str(REPO_ROOT / "assets" / "fonts" / "Amiri-Regular.ttf")
MEDIA_DIR = REPO_ROOT / "media"

# ----------------------------------------------------------------------------
# Palette (video 1 house style: black background, TEAL accent, dark fills)
# ----------------------------------------------------------------------------
BG = "#000000"            # scene background (matches video 1)
INK = "#f2f1ec"           # primary text / light marks
INK_2 = "#c9ccd1"         # secondary text, brackets, thin lines
MUTED = "#6b7280"         # tile outlines, ellipsis dots, safe-area rect
ACCENT = "#3dd6c6"        # the WRITER (autoregressive) side — cool teal (video 1 TEAL)
WARM = "#f0a35e"          # the PRINTER (diffusion decoder) side — warm amber
CARD_FILL = "#151a28"     # dark fill of cards, chips, bubbles, boxes (video 1)
CARD_STROKE = "#3a4256"   # subtle stroke on cards / chips / bubbles
SKY = "#8ec9f0"           # the sky band behind the hero's head

# Glyph tones (every glyph uses exactly these two, so they read as one alphabet)
TONE_A = "#ece9e1"        # light tone
TONE_B = ACCENT           # teal tone

# ----------------------------------------------------------------------------
# On-screen strings (PLACEHOLDERS — Ali edits these in one place)
# ----------------------------------------------------------------------------
REQUEST_AR = "ارسم شخص مبتسم"
SIGN_WORD_AR = "مرحبا"
SIGN_REQUEST_AR = 'اكتب "مرحبا" عاللافتة'
EDIT_SKY_AR = "خلي السما أغمق"
HAT_REQUEST_AR = "حطّلا طاقية"
PRINTER_AR = "الطابعة"
UPLOAD_LABEL_AR = "صورتك"
FAMILY_LABEL_AR = "نفس العائلة، محادثة وحدة"

# ----------------------------------------------------------------------------
# Sizes / conventions
# ----------------------------------------------------------------------------
N_PIX = 48            # hero raster size (48×48 = 2304 pixel squares)
N_TILES = 8           # tiles per side (8×8 = 64 tiles, 6×6 pixels each)
NUM_GLYPHS = 12       # size of the drawn alphabet (the tray ends in "…")
HERO_IMAGE_RES = 384  # resolution of the smooth "developed photo" PNG
SCENE_HERO_WIDTH = 4.0
RIBBON_Y = -2.9       # y of "the line" when it runs along the bottom

HERO_VARIANTS = ("base", "dark_sky", "hat", "sign", "alt_portrait", "alt_hat")

# Which glyph every sky tile maps to (light sky vs. darkened sky).
SKY_GLYPH_LIGHT = 0
SKY_GLYPH_DARK = 1
_SKY_TILE_FRACTION = 0.5

# ----------------------------------------------------------------------------
# Text
# ----------------------------------------------------------------------------
def ar_text(s: str, font_size: int = 40, color=INK) -> Text:
    """Arabic text in Amiri (Pango shapes RTL + ligatures). Only *_AR strings belong on screen."""
    with register_font(AMIRI_PATH):
        t = Text(
            s,
            font="Amiri",
            font_size=font_size,
            disable_ligatures=False,
            fill_color=color,
        )
    return t


# ----------------------------------------------------------------------------
# Hero: procedural raster portrait (numpy), supersampled for soft edges
# ----------------------------------------------------------------------------
def _c(*rgb) -> np.ndarray:
    return np.array(rgb, dtype=float)


def _ellipse(U, V, cx, cy, rx, ry):
    return ((U - cx) / rx) ** 2 + ((V - cy) / ry) ** 2 <= 1.0


def _paint(rgb, mask, color):
    rgb[mask] = color


def _blend(rgb, alpha, color):
    """Per-pixel alpha blend of a flat color (alpha: 2-D array in [0,1])."""
    a = alpha[..., None]
    rgb *= (1.0 - a)
    rgb += a * np.asarray(color, dtype=float)


def _text_mask(S: int, text: str, cx: float, cy: float, px_size: float) -> np.ndarray:
    """Rasterise shaped Arabic text (PIL + raqm) into an S×S float mask, centred at (cx, cy) in pixels."""
    img = Image.new("L", (S, S), 0)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(AMIRI_PATH, max(int(round(px_size)), 4))
    try:
        draw.text((cx, cy), text, font=font, fill=255, anchor="mm", direction="rtl", language="ar")
    except (ValueError, OSError):  # PIL built without raqm: still draw something
        draw.text((cx, cy), text, font=font, fill=255, anchor="mm")
    return np.asarray(img, dtype=float) / 255.0


# ----------------------------------------------------------------------------
# Face styles: how the eyes and the smile are drawn (both people). Head-local coords X, Y
# (X right, Y up; the eyes sit near Y 0.05, the mouth near Y -0.30). FACE_STYLE is the one in use.
# ----------------------------------------------------------------------------
def _brows(rgb, X, Y, alt, pal, lift=0.0):
    """Soft short arcs, inner ends a touch higher (warm, not surprised)."""
    for sgn in (-1, 1):
        ex, ey = sgn * 0.18, 0.045
        bu = (X - ex) / 0.075
        brow_c = ey + 0.098 + lift + 0.018 * (1 - bu ** 2) + 0.008 * (-sgn * bu)
        thick = (0.011 if alt else 0.016) * (1 - 0.45 * bu ** 2)
        _paint(rgb, (np.abs(bu) <= 1.0) & (np.abs(Y - brow_c) <= thick), pal["hair"])


def _stroke(X, Y, ex, sgn, x0, y0, length, slope, th):
    """A short slanted stroke starting at (ex + sgn*x0, y0), running outward (for lashes)."""
    w = (X - (ex + sgn * x0)) * sgn
    return (w >= 0) & (w <= length) & (np.abs(Y - (y0 + slope * w)) <= th)


_INK = _c(0.13, 0.09, 0.08)


def _eyes_dots(rgb, X, Y, alt, pal):
    for sgn in (-1, 1):
        ex, ey = sgn * 0.18, 0.045
        eye = _ellipse(X, Y, ex, ey, 0.029, 0.041)
        _paint(rgb, eye, _INK)
        _paint(rgb, _ellipse(X, Y, ex - 0.009, ey + 0.014, 0.010, 0.010) & eye, _c(1, 1, 1))
        if alt:
            _paint(rgb, _stroke(X, Y, ex, sgn, 0.018, ey + 0.030, 0.030, 0.55, 0.0055), _INK)
            _paint(rgb, _stroke(X, Y, ex, sgn, 0.008, ey + 0.040, 0.026, 0.90, 0.0050), _INK)
    _brows(rgb, X, Y, alt, pal)


def _eyes_happy(rgb, X, Y, alt, pal):
    for sgn in (-1, 1):
        ex, ey = sgn * 0.18, 0.040
        u = (X - ex) / 0.055
        arc = (np.abs(u) <= 1.0) & (np.abs(Y - (ey + 0.024 * (1 - u ** 2))) <= 0.0105)
        _paint(rgb, arc, _INK)
        if alt:
            _paint(rgb, _stroke(X, Y, ex, sgn, 0.050, ey + 0.004, 0.024, 0.75, 0.0050), _INK)
    _brows(rgb, X, Y, alt, pal, lift=0.012)


def _eyes_round(rgb, X, Y, alt, pal):
    for sgn in (-1, 1):
        ex, ey = sgn * 0.18, 0.045
        whites = _ellipse(X, Y, ex, ey, 0.050, 0.047)
        _paint(rgb, whites, _c(0.98, 0.98, 0.97))
        _paint(rgb, _ellipse(X, Y, ex + sgn * 0.004, ey - 0.004, 0.034, 0.036) & whites, pal["iris"])
        _paint(rgb, _ellipse(X, Y, ex + sgn * 0.004, ey - 0.004, 0.017, 0.018) & whites, _c(0.07, 0.07, 0.09))
        _paint(rgb, _ellipse(X, Y, ex - 0.010, ey + 0.012, 0.010, 0.010) & whites, _c(1, 1, 1))
        rim = _ellipse(X, Y, ex, ey + 0.002, 0.057, 0.054) & ~whites & (Y > ey + 0.010)
        _paint(rgb, rim, _INK if alt else _c(0.25, 0.16, 0.12))
        if alt:
            _paint(rgb, _stroke(X, Y, ex, sgn, 0.045, ey + 0.030, 0.026, 0.80, 0.0055), _INK)
    _brows(rgb, X, Y, alt, pal)


def _eyes_gentle(rgb, X, Y, alt, pal):
    for sgn in (-1, 1):
        ex, ey = sgn * 0.18, 0.050
        eye = _ellipse(X, Y, ex, ey, 0.026, 0.034)
        _paint(rgb, eye, _INK)
        _paint(rgb, _ellipse(X, Y, ex - 0.008, ey + 0.012, 0.009, 0.009) & eye, _c(1, 1, 1))
        u = (X - ex) / 0.050                  # the lower lid lifted by the smile
        crease = (np.abs(u) <= 1.0) & (np.abs(Y - (ey - 0.050 + 0.016 * u ** 2)) <= 0.0055)
        _paint(rgb, crease, pal["skin"] * 0.78)
        if alt:
            _paint(rgb, _stroke(X, Y, ex, sgn, 0.018, ey + 0.024, 0.028, 0.60, 0.0055), _INK)
    _brows(rgb, X, Y, alt, pal)


def _mouth_line(rgb, X, Y, alt, pal):
    m = X / (0.100 if alt else 0.110)
    yc = -0.305 + 0.042 * m ** 2
    th = (0.010 if alt else 0.0085) * (1 - 0.45 * m ** 2) + 0.003
    _paint(rgb, (np.abs(m) <= 1.0) & (np.abs(Y - yc) <= th), pal["lip"] * 0.72 if alt else _c(0.50, 0.22, 0.21))


def _mouth_open(rgb, X, Y, alt, pal):
    mw = 0.105 if alt else 0.115
    depth = 0.056 if alt else 0.062
    m = X / mw
    top = -0.288 + 0.014 * m ** 2
    bot = top - depth * np.clip(1 - m ** 2, 0, 1) ** 0.9
    mouth = (np.abs(m) <= 1.0) & (Y <= top) & (Y >= bot)
    if alt:   # lips around the opening
        mo = X / (mw + 0.012)
        topo = -0.288 + 0.012 + 0.014 * mo ** 2
        boto = topo - 0.085 * np.clip(1 - mo ** 2, 0, 1) ** 0.9
        _paint(rgb, (np.abs(mo) <= 1.0) & (Y <= topo) & (Y >= boto), pal["lip"])
    _paint(rgb, mouth, _c(0.40, 0.11, 0.14))
    _paint(rgb, mouth & _ellipse(X, Y, 0.0, -0.288 - 0.85 * depth, 0.055, 0.026), _c(0.86, 0.44, 0.46))   # tongue


def _mouth_teeth(rgb, X, Y, alt, pal):
    mw, depth, rim = (0.105, 0.070, 0.011) if alt else (0.115, 0.078, 0.007)
    def shape(half_w, top_y, d):
        mm = X / half_w
        top = top_y + 0.030 * mm ** 2
        bot = top - d * np.clip(1 - mm ** 2, 0, 1) ** 0.8
        return (np.abs(mm) <= 1.0) & (Y <= top) & (Y >= bot), top, bot
    lips, _, _ = shape(mw + rim, -0.292 + rim * 0.6, depth + 2.2 * rim)
    _paint(rgb, lips, pal["lip"])
    mouth, top, bot = shape(mw, -0.292, depth)
    _paint(rgb, mouth, _c(0.40, 0.11, 0.14))
    _paint(rgb, mouth & (Y >= top - 0.34 * (top - bot) - 0.002), _c(0.98, 0.97, 0.94))       # top teeth
    _paint(rgb, mouth & _ellipse(X, Y, 0.0, -0.292 - 0.86 * depth, 0.055, 0.026), _c(0.86, 0.44, 0.46))  # tongue


def _mouth_lips(rgb, X, Y, alt, pal):
    m = X / (0.105 if alt else 0.115)
    inside = np.abs(m) <= 1.0
    yl = -0.312 + 0.034 * m ** 2
    k = np.clip(1 - m ** 2, 0, 1)
    upper = inside & (Y >= yl) & (Y <= yl + (0.014 if alt else 0.008) * k ** 0.7)
    lower = inside & (Y <= yl) & (Y >= yl - (0.026 if alt else 0.016) * k ** 0.8)
    _paint(rgb, upper, pal["lip"] * 0.92)
    _paint(rgb, lower, pal["lip"])
    _paint(rgb, inside & (np.abs(Y - yl) <= 0.0042), _c(0.45, 0.17, 0.19))


def _eyes_almond(rgb, X, Y, alt, pal):
    """The previous style (kept for reference)."""
    hair, iris = pal["hair"], pal["iris"]
    ey = 0.06
    for sgn in (-1, 1):
        ex = sgn * 0.185
        erx = 0.088
        u = (X - ex) / erx
        inside = np.abs(u) <= 1.0
        arch = np.clip(1 - u ** 2, 0, 1)
        y_up = ey + 0.040 * arch                        # upper lid: a gentle arc
        y_lo = ey - 0.026 * arch + 0.004                # lower edge: flatter, like a smiling eye
        whites = inside & (Y < y_up) & (Y > y_lo)
        _paint(rgb, whites, _c(0.97, 0.97, 0.96))
        ir = _ellipse(X, Y, ex + sgn * 0.004, ey + 0.005, 0.039, 0.039) & whites
        _paint(rgb, ir, iris)
        pupil = _ellipse(X, Y, ex + sgn * 0.004, ey + 0.002, 0.016, 0.016) & whites
        _paint(rgb, pupil, _c(0.07, 0.07, 0.09))
        glint = _ellipse(X, Y, ex - 0.012, ey + 0.014, 0.009, 0.009) & whites
        _paint(rgb, glint, _c(1.0, 1.0, 1.0))
        lid_t = (0.017 if alt else 0.010) * (0.35 + 0.65 * arch) + 0.004
        wide = np.abs(u) <= 1.08
        lid = wide & (Y >= y_up - 0.002) & (Y <= y_up + lid_t)
        if alt:  # her lash line flicks up a little at the outer corner
            wu = (X - (ex + sgn * 0.075)) * sgn
            lid |= (wu > 0) & (wu < 0.030) & (Y > ey + 0.004 + 0.20 * wu) & (Y < ey + 0.020 + 0.40 * wu)
        _paint(rgb, lid, _c(0.07, 0.05, 0.05) if alt else _c(0.22, 0.13, 0.10))
        # brows: lower, softer, inner ends lifted a touch — warm rather than surprised
        bu = (X - sgn * 0.19) / 0.12
        brow_c = ey + 0.108 + 0.022 * (1 - bu ** 2) + 0.012 * (-sgn * bu)
        thick = (0.016 if alt else 0.022) * (1 - 0.5 * bu ** 2)
        brow = (np.abs(bu) <= 1.0) & (np.abs(Y - brow_c) <= thick)
        _paint(rgb, brow, hair)



def _mouth_d(rgb, X, Y, alt, pal):
    """The previous style (kept for reference)."""
    lip = pal["lip"]
    mw = 0.13 if alt else 0.145                 # half-width
    depth_c = 0.058 if alt else 0.064           # depth of the opening at its centre
    rim = 0.012 if alt else 0.008
    def _smile(half_w, top_y, depth):
        m = X / half_w
        top = top_y + 0.032 * m ** 2
        bot = top - depth * np.clip(1 - m ** 2, 0, 1) ** 0.8
        return (np.abs(m) <= 1.0) & (Y <= top) & (Y >= bot), top, bot
    lips, _, _ = _smile(mw + rim, -0.300 + rim * 0.6, depth_c + 2.2 * rim)
    _paint(rgb, lips, lip)
    mouth, top, bot = _smile(mw, -0.300, depth_c)
    _paint(rgb, mouth, _c(0.42, 0.12, 0.15))
    teeth = mouth & (Y >= top - 0.42 * (top - bot) - 0.003)
    _paint(rgb, teeth, _c(0.98, 0.97, 0.94))
    tongue = mouth & (Y <= bot + 0.30 * (top - bot)) & (np.abs(X) < 0.55 * mw)
    _paint(rgb, tongue, _c(0.78, 0.36, 0.38))



FACE_STYLES = {
    "1_minimal":   {"eyes": _eyes_dots,   "mouth": _mouth_line},
    "2_cheerful":  {"eyes": _eyes_dots,   "mouth": _mouth_open},
    "3_laughing":  {"eyes": _eyes_happy,  "mouth": _mouth_open},
    "4_storybook": {"eyes": _eyes_round,  "mouth": _mouth_lips},
    "5_warm":      {"eyes": _eyes_gentle, "mouth": _mouth_teeth},
    "6_bright":    {"eyes": _eyes_round,  "mouth": _mouth_teeth},
    "previous":    {"eyes": _eyes_almond, "mouth": _mouth_d},
}
FACE_STYLE = "1_minimal"                  # Ali picked this one (27 Sep 2026) from the style sheet



def _render_hero(variant: str, n: int, ss: int = 4, face: str | None = None):
    """
    Returns (rgb[n,n,3] in [0,1], sky_fraction[n,n] in [0,1]).
    u: -1 (left) .. +1 (right); v: +1 (top) .. -1 (bottom). Painter's order.
    Face features live in head-local coords (hx, hy, hs) so the head can be scaled as one thing.
    """
    if variant not in HERO_VARIANTS:
        raise ValueError(f"unknown hero variant {variant!r}; use one of {HERO_VARIANTS}")
    alt = variant.startswith("alt")
    S = n * ss
    px = (np.arange(S) + 0.5) / S * 2.0 - 1.0
    U, V = np.meshgrid(px, -px)  # V[0] is the top row
    rgb = np.zeros((S, S, 3), dtype=float)
    covered = np.zeros((S, S), dtype=bool)

    # --- sky (gradient) -----------------------------------------------------
    t = (V + 1.0) / 2.0  # 0 bottom .. 1 top
    if variant == "dark_sky":
        top, bottom = _c(0.08, 0.11, 0.30), _c(0.20, 0.25, 0.48)
    else:
        top, bottom = _c(0.47, 0.74, 0.94), _c(0.76, 0.88, 0.97)
    rgb[:] = bottom[None, None, :] * (1 - t)[..., None] + top[None, None, :] * t[..., None]

    # --- palette per person -------------------------------------------------
    if alt:  # the woman in the upload beat: fair skin, long dark hair, lashes, earrings, scoop neck
        skin = _c(0.97, 0.84, 0.76)
        hair = _c(0.16, 0.10, 0.08)
        shirt = _c(0.62, 0.22, 0.38)
        iris = _c(0.30, 0.20, 0.13)
        lip = _c(0.84, 0.44, 0.48)
        head_rx, head_ry = 0.45, 0.55
    else:
        skin = _c(0.95, 0.77, 0.63)
        hair = _c(0.27, 0.16, 0.11)
        shirt = _c(0.72, 0.29, 0.25)
        iris = _c(0.28, 0.44, 0.60)
        lip = _c(0.80, 0.46, 0.44)
        head_rx, head_ry = 0.50, 0.56
    hx, hy, hs = 0.0, 0.06, 1.15          # head centre and scale in frame coords
    X = (U - hx) / hs                     # head-local coords
    Y = (V - hy) / hs
    chin_v = hy - head_ry * hs

    # --- long hair behind the head and shoulders (drawn first, the torso covers its foot)
    if alt:
        fall_w = 0.53 + 0.15 * np.clip((0.25 - Y) / 0.9, 0, 1)   # hair widens gently toward the shoulders
        back = ((np.abs(X) < fall_w) & (Y < 0.30)) | _ellipse(X, Y, 0.0, 0.24, 0.58, 0.44)
        back_hi = np.exp(-(((X + 0.30) ** 2 + (Y - 0.35) ** 2) / 0.10))
        rgb[back] = hair[None, :] * (0.85 + 0.25 * back_hi[back])[:, None]
        covered |= back

    # --- torso / shirt ------------------------------------------------------
    torso = V < (-0.68 - 0.22 * U ** 2)
    shade = 0.82 + 0.18 * (1.0 - np.clip(np.abs(U), 0, 1) ** 2)
    rgb[torso] = (shirt[None, :] * shade[torso][:, None])
    covered |= torso
    if alt:  # scoop neckline, then two locks of hair lying over the shoulders
        scoop = torso & (np.abs(U) < 0.30) & (V > -0.92 + 3.2 * U ** 2)
        _paint(rgb, scoop, skin * 0.84)
        for sgn in (-1, 1):
            lu = (U - sgn * 0.43) / 0.16
            lock = torso & (np.abs(lu) <= 1.0 - 0.25 * np.clip(-(V + 0.80) / 0.2, 0, 1)) & (V > -1.0)
            lock_hi = 0.9 + 0.2 * np.clip(1 - np.abs(lu + sgn * 0.4), 0, 1)
            rgb[lock] = hair[None, :] * lock_hi[lock][:, None]
    else:
        collar = torso & (np.abs(U) < 0.24 - 0.40 * (V + 0.68)) & (V > -0.86)
        _paint(rgb, collar, shirt * 1.18)

    # --- neck ---------------------------------------------------------------
    neck = (np.abs(U) < 0.19) & (V > -0.80) & (V < chin_v + 0.12)
    _paint(rgb, neck, skin * 0.80)
    covered |= neck

    # --- ears ---------------------------------------------------------------
    for sgn in ((-1, 1) if not alt else ()):
        ear = _ellipse(X, Y, sgn * (head_rx + 0.04), -0.06, 0.075, 0.105)
        _paint(rgb, ear, skin * 0.90)
        covered |= ear

    # --- head with soft shading -----------------------------------------
    dv = Y / head_ry
    rx_v = head_rx * (1.0 - (0.30 if alt else 0.20) * np.clip(-dv, 0, 1) ** 2)  # narrower chin
    head = X ** 2 / rx_v ** 2 + dv ** 2 <= 1.0
    d = np.sqrt(X ** 2 / rx_v ** 2 + dv ** 2)
    light = 0.90 + 0.12 * (1.0 - d) - 0.05 * X - 0.10 * np.clip(-dv, 0, 1) ** 2
    rgb[head] = skin[None, :] * light[head][:, None]
    covered |= head
    for sgn in (-1, 1):  # cheek blush
        dd = np.sqrt((X - sgn * 0.30) ** 2 + (Y + 0.16) ** 2) / 0.12
        _blend(rgb, np.where(head, 0.30 * np.clip(1 - dd ** 2, 0, 1), 0.0), _c(0.95, 0.55, 0.55))
    nose_shadow = _ellipse(X, Y, 0.035, -0.15, 0.055, 0.032) & head
    _blend(rgb, np.where(nose_shadow, 0.55, 0.0), skin * 0.82)
    nose_light = _ellipse(X, Y, -0.01, -0.10, 0.02, 0.045) & head
    _blend(rgb, np.where(nose_light, 0.35, 0.0), skin * 1.10)

    # --- eyes and mouth: drawn in the chosen face style (FACE_STYLES) -------------------
    pal = {"hair": hair, "iris": iris, "lip": lip, "skin": skin}
    style = FACE_STYLES[face or FACE_STYLE]
    style["eyes"](rgb, X, Y, alt, pal)
    style["mouth"](rgb, X, Y, alt, pal)

    # --- hair ---------------------------------------------------------------
    if alt:
        cap = _ellipse(X, Y, 0.0, 0.22, 0.58, 0.48) & (Y > 0.30 - 0.10 * X ** 2 + 0.12 * X)
        frame_in = 0.34 + 0.06 * np.clip(-Y, 0, 1)          # curtains widen a little toward the jaw
        fall_w = 0.53 + 0.15 * np.clip((0.25 - Y) / 0.9, 0, 1)
        sides = (np.abs(X) > frame_in) & (np.abs(X) < fall_w) & (Y > -0.62) & (Y < 0.30)
        hair_mask = cap | sides
        hi = np.exp(-(((X + 0.25) ** 2 + (Y - 0.50) ** 2) / 0.05))
    else:
        cap = _ellipse(X, Y, 0.0, 0.24, 0.53, 0.40)
        hairline = 0.27 - 0.12 * X ** 2 - 0.06 * np.clip(X, 0, 1)
        cap &= Y > hairline
        sides = _ellipse(X, Y, 0.0, 0.20, 0.545, 0.46) & (np.abs(X) > 0.37) & (Y > -0.10)
        hair_mask = cap | sides
        hi = np.exp(-(((X + 0.18) ** 2 + (Y - 0.52) ** 2) / 0.04))
    rgb[hair_mask] = hair[None, :] * (1.0 + 0.35 * hi[hair_mask])[:, None]
    covered |= hair_mask
    if alt:  # small gold earrings peeking out under the hair at the jaw
        for sgn in (-1, 1):
            ring = _ellipse(X, Y, sgn * (head_rx - 0.02), -0.30, 0.045, 0.045)
            _paint(rgb, ring, _c(0.93, 0.74, 0.30))

    # --- hat (beanie with a band and a pom-pom) -------------------------
    if variant in ("hat", "alt_hat"):
        mustard = _c(0.92, 0.70, 0.26)
        dome = _ellipse(X, Y, 0.0, 0.30, 0.57, 0.40) & (Y > 0.18)
        dome_shade = 0.86 + 0.14 * (1.0 - np.clip(np.abs(X) / 0.57, 0, 1) ** 2) - 0.04 * X
        rgb[dome] = mustard[None, :] * dome_shade[dome][:, None]
        band = dome & (Y < 0.29)
        _paint(rgb, band, mustard * 0.78)
        pom = _ellipse(X, Y, 0.0, 0.68, 0.08, 0.08)
        _paint(rgb, pom, _c(0.97, 0.94, 0.86))
        covered |= dome | pom

    # --- sign / plaque carrying SIGN_WORD_AR ------------------------------
    if variant == "sign":
        pcx, pcy, phw, phh = 0.62, -0.74, 0.34, 0.15
        plaque = (np.abs(U - pcx) <= phw) & (np.abs(V - pcy) <= phh)
        inner = (np.abs(U - pcx) <= phw - 0.022) & (np.abs(V - pcy) <= phh - 0.022)
        _paint(rgb, plaque, _c(0.26, 0.22, 0.20))
        _paint(rgb, inner, _c(0.97, 0.94, 0.86))
        covered |= plaque
        cx_px = (pcx + 1.0) / 2.0 * S
        cy_px = (1.0 - pcy) / 2.0 * S
        mask = _text_mask(S, SIGN_WORD_AR, cx_px, cy_px, px_size=phh * S * 0.66)
        _blend(rgb, mask * inner, _c(0.14, 0.11, 0.11))

    # --- downsample (box filter) ----------------------------------------
    rgb = np.clip(rgb, 0.0, 1.0)
    rgb = rgb.reshape(n, ss, n, ss, 3).mean(axis=(1, 3))
    sky = (~covered).astype(float).reshape(n, ss, n, ss).mean(axis=(1, 3))
    return rgb, sky


@lru_cache(maxsize=None)
def _hero_cached(variant: str, n: int):
    rgb, sky = _render_hero(variant, n)
    rgb.setflags(write=False)
    sky.setflags(write=False)
    return rgb, sky


def hero_array(variant: str = "base", n: int = N_PIX) -> np.ndarray:
    """(n, n, 3) floats in [0,1], row 0 = top. Variants: base, dark_sky, hat, sign, alt_portrait, alt_hat."""
    return _hero_cached(variant, n)[0].copy()


def hero_sky_fraction(variant: str = "base", n: int = N_PIX) -> np.ndarray:
    """(n, n) floats in [0,1]: how much of each pixel is uncovered sky."""
    return _hero_cached(variant, n)[1].copy()


# ----------------------------------------------------------------------------
# Pixel-square rasters
# ----------------------------------------------------------------------------
def _pixel_template(side: float) -> Square:
    sq = Square(side_length=side)
    sq.set_fill(WHITE, opacity=1.0)
    sq.set_stroke(width=0)
    return sq


def _array_to_pixels(arr: np.ndarray, width: float) -> VGroup:
    """Raster-order squares (row-major, top-left first), centred at ORIGIN."""
    n = arr.shape[0]
    side = width / n
    tmpl = _pixel_template(side)
    left = -width / 2 + side / 2
    top = width / 2 - side / 2
    pixels = VGroup()
    for i in range(n):
        y = top - i * side
        for j in range(n):
            sq = tmpl.copy()
            sq.move_to(np.array([left + j * side, y, 0.0]))
            sq.set_fill(rgb_to_hex(arr[i, j]), opacity=1.0)
            pixels.add(sq)
    return pixels


def hero_pixels(variant: str = "base", width: float = SCENE_HERO_WIDTH) -> VGroup:
    """N_PIX*N_PIX Square pixels (fill 1, stroke 0), raster order, centred at ORIGIN."""
    return _array_to_pixels(hero_array(variant), width)


def _atomic_png(path: Path, arr: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB")
    fd, tmp = tempfile.mkstemp(suffix=".png", dir=str(path.parent))
    os.close(fd)
    img.save(tmp, format="PNG")
    os.replace(tmp, path)  # atomic: six authors may render in parallel


def hero_image_path(variant: str = "base", res: int = HERO_IMAGE_RES) -> str:
    """Write media/kit_hero_<variant>_<res>_<hash>.png (content-hashed, so never stale) and return its absolute path."""
    arr = hero_array(variant, n=res)
    digest = hashlib.md5(arr.astype(np.float32).tobytes()).hexdigest()[:10]
    path = MEDIA_DIR / f"kit_hero_{variant}_{res}_{digest}.png"
    if not path.is_file():
        _atomic_png(path, arr)
    return str(path)


def hero_image(variant: str = "base", width: float = SCENE_HERO_WIDTH) -> ImageMobject:
    """Smooth 'developed photo' version of the hero (an ImageMobject; NOT a VMobject, so not for VGroup)."""
    img = ImageMobject(hero_image_path(variant))
    img.set_width(width)
    img.move_to(ORIGIN)
    return img


# ----------------------------------------------------------------------------
# Tiles and patches
# ----------------------------------------------------------------------------
def tile_index(i: int, j: int, n: int = N_TILES) -> int:
    """Row i, column j (0 = top-left) -> raster index."""
    return i * n + j


def tile_center(idx: int, width: float = SCENE_HERO_WIDTH, n: int = N_TILES) -> np.ndarray:
    """Centre of tile idx for a grid of this width centred at ORIGIN."""
    cell = width / n
    i, j = divmod(idx, n)
    return np.array([-width / 2 + (j + 0.5) * cell, width / 2 - (i + 0.5) * cell, 0.0])


def tile_cells(width: float = SCENE_HERO_WIDTH, n: int = N_TILES) -> VGroup:
    """n*n Square outlines (MUTED), raster order, centred at ORIGIN. Attribute: .cell_size"""
    cell = width / n
    cells = VGroup()
    for idx in range(n * n):
        sq = Square(side_length=cell)
        sq.set_fill(opacity=0)
        sq.set_stroke(MUTED, width=2.0)
        sq.move_to(tile_center(idx, width, n))
        cells.add(sq)
    cells.cell_size = cell
    return cells


def tile_patches(variant: str = "base", width: float = SCENE_HERO_WIDTH, n: int = N_TILES) -> VGroup:
    """n*n VGroups of pixel squares (one per tile, raster order), each scaled to 0.94 of its cell."""
    arr = hero_array(variant)
    pix = arr.shape[0]
    if pix % n:
        raise ValueError("N_PIX must be a multiple of n")
    b = pix // n
    side = width / pix
    tmpl = _pixel_template(side)
    left = -width / 2 + side / 2
    top = width / 2 - side / 2
    patches = VGroup()
    for idx in range(n * n):
        ti, tj = divmod(idx, n)
        patch = VGroup()
        for di in range(b):
            i = ti * b + di
            for dj in range(b):
                j = tj * b + dj
                sq = tmpl.copy()
                sq.move_to(np.array([left + j * side, top - i * side, 0.0]))
                sq.set_fill(rgb_to_hex(arr[i, j]), opacity=1.0)
                patch.add(sq)
        patch.scale(0.94, about_point=tile_center(idx, width, n))
        patches.add(patch)
    return patches


def sky_tiles(variant: str = "base", n: int = N_TILES) -> list[int]:
    """Raster indices of tiles that are (mostly) sky."""
    sky = hero_sky_fraction(variant)
    b = sky.shape[0] // n
    out = []
    for idx in range(n * n):
        i, j = divmod(idx, n)
        if sky[i * b:(i + 1) * b, j * b:(j + 1) * b].mean() >= _SKY_TILE_FRACTION:
            out.append(idx)
    return out


# ----------------------------------------------------------------------------
# Tile -> glyph: a tiny deterministic codebook (k-means over patch statistics)
# ----------------------------------------------------------------------------
def _tile_features(variant: str, n: int = N_TILES) -> np.ndarray:
    """
    Per-tile statistics for the codebook. Sky pixels are ignored (replaced by the tile's
    non-sky mean) so a hair/sky edge tile keeps its glyph when only the sky changes;
    the sky fraction itself is one feature.
    """
    arr = hero_array(variant)
    sky = hero_sky_fraction(variant)
    b = arr.shape[0] // n
    lum_w = np.array([0.299, 0.587, 0.114])
    feats = []
    for idx in range(n * n):
        i, j = divmod(idx, n)
        block = arr[i * b:(i + 1) * b, j * b:(j + 1) * b]
        w = 1.0 - sky[i * b:(i + 1) * b, j * b:(j + 1) * b]
        wsum = float(w.sum())
        if wsum > 1e-6:
            mean = (block * w[..., None]).sum(axis=(0, 1)) / wsum
        else:
            mean = block.reshape(-1, 3).mean(axis=0)
        filled = block * w[..., None] + mean[None, None, :] * (1.0 - w)[..., None]
        lum = filled @ lum_w
        gy = np.abs(np.diff(lum, axis=0)).mean()
        gx = np.abs(np.diff(lum, axis=1)).mean()
        feats.append([*mean, 1.5 * lum.std(), 1.5 * gx, 1.5 * gy, 0.8 * (1.0 - wsum / w.size)])
    return np.array(feats)


def _kmeans_deterministic(X: np.ndarray, k: int, iters: int = 40) -> tuple[np.ndarray, np.ndarray]:
    """Farthest-first seeding + Lloyd iterations. No randomness."""
    centers = [X[np.argmin(np.linalg.norm(X - X.mean(axis=0), axis=1))]]
    for _ in range(1, k):
        dists = np.min([np.linalg.norm(X - c, axis=1) for c in centers], axis=0)
        centers.append(X[np.argmax(dists)])
    C = np.array(centers)
    labels = np.zeros(len(X), dtype=int)
    for _ in range(iters):
        D = np.linalg.norm(X[:, None, :] - C[None, :, :], axis=2)
        new_labels = D.argmin(axis=1)
        if np.array_equal(new_labels, labels) and _ > 0:
            break
        labels = new_labels
        for c in range(k):
            if np.any(labels == c):
                C[c] = X[labels == c].mean(axis=0)
    return C, labels


@lru_cache(maxsize=None)
def _codebook():
    """Cluster the non-sky tiles of the first person's pictures into NUM_GLYPHS-2 glyphs (0 and 1
    are reserved for sky); the second person's tiles (alt_*) take the nearest of those glyphs, so
    redrawing her never reshuffles the alphabet the other scenes show."""
    rows, alt_rows = [], []
    for v in HERO_VARIANTS:
        sky = set(sky_tiles(v))
        F = _tile_features(v)
        for idx in range(F.shape[0]):
            if idx not in sky:
                (alt_rows if v.startswith("alt") else rows).append((v, idx, F[idx]))
    X = np.array([r[2] for r in rows])
    k = NUM_GLYPHS - 2
    C, labels = _kmeans_deterministic(X, k)
    # stable glyph ids: order clusters by mean luminance of their centre
    order = np.argsort(C[:, :3] @ np.array([0.299, 0.587, 0.114]))
    remap = {int(c): 2 + rank for rank, c in enumerate(order)}
    table = {}
    for (v, idx, _), lab in zip(rows, labels):
        table[(v, idx)] = remap[int(lab)]
    for v, idx, f in alt_rows:
        table[(v, idx)] = remap[int(np.argmin(((C - f) ** 2).sum(axis=1)))]
    return table


def glyph_for_tile(variant: str, idx: int) -> int:
    """Deterministic tile -> glyph id. All sky tiles of a variant share one glyph; similar patches share glyphs."""
    if idx in sky_tiles(variant):
        return SKY_GLYPH_DARK if variant == "dark_sky" else SKY_GLYPH_LIGHT
    return _codebook()[(variant, idx)]


def glyphs_for_variant(variant: str) -> list[int]:
    """All N_TILES*N_TILES glyph ids in raster order."""
    return [glyph_for_tile(variant, idx) for idx in range(N_TILES * N_TILES)]


# ----------------------------------------------------------------------------
# Glyph alphabet: two-tone geometric marks (never digits / letters / QR)
# ----------------------------------------------------------------------------
def _flat(mob: VMobject, color) -> VMobject:
    mob.set_fill(color, opacity=1.0)
    mob.set_stroke(width=0)
    return mob


def _pill(w: float, h: float, color) -> VMobject:
    return _flat(RoundedRectangle(width=w, height=h, corner_radius=min(w, h) / 2 * 0.999), color)


def _poly(color, *pts) -> VMobject:
    return _flat(Polygon(*[np.array([x, y, 0.0]) for x, y in pts]), color)


def _glyph_unit(k: int) -> VGroup:
    """Glyph k drawn inside a unit box (about 1×1), tones A (light) and B (teal)."""
    A, B = TONE_A, TONE_B
    k = int(k) % NUM_GLYPHS
    if k == 0:    # half disc
        return VGroup(_flat(Circle(radius=0.5), A), _flat(Sector(angle=PI, start_angle=PI, radius=0.5), B))
    if k == 1:    # ring + core
        return VGroup(_flat(Annulus(inner_radius=0.29, outer_radius=0.5), A), _flat(Circle(radius=0.16), B))
    if k == 2:    # diamond + dot
        return VGroup(_flat(Square(side_length=0.72).rotate(PI / 4), A), _flat(Circle(radius=0.13), B))
    if k == 3:    # square split on the diagonal
        return VGroup(_flat(Square(side_length=0.82), A), _poly(B, (0.41, 0.41), (0.41, -0.41), (-0.41, -0.41)))
    if k == 4:    # triangle over a bar
        tri = _poly(A, (-0.42, -0.05), (0.42, -0.05), (0.0, 0.55))
        return VGroup(tri, _pill(0.84, 0.17, B).move_to(0.34 * DOWN))
    if k == 5:    # disc with a small square at its corner
        return VGroup(_flat(Circle(radius=0.40), A).shift(0.06 * UL), _flat(Square(side_length=0.30), B).move_to(0.30 * DR))
    if k == 6:    # hexagon + small triangle
        hexa = _flat(RegularPolygon(n=6, radius=0.5, start_angle=PI / 6), A)
        return VGroup(hexa, _poly(B, (-0.2, -0.14), (0.2, -0.14), (0.0, 0.22)))
    if k == 7:    # nested squares, offset
        return VGroup(_flat(Square(side_length=0.72), A), _flat(Square(side_length=0.34), B).move_to(0.15 * UR))
    if k == 8:    # arch over a block
        arch = _flat(AnnularSector(angle=PI, start_angle=0, inner_radius=0.24, outer_radius=0.5), A).shift(0.08 * DOWN)
        return VGroup(arch, _flat(Rectangle(width=0.34, height=0.30), B).move_to(0.30 * DOWN))
    if k == 9:    # chevron + dot
        chev = _poly(A, (-0.5, 0.05), (0.0, 0.5), (0.5, 0.05), (0.5, -0.22), (0.0, 0.23), (-0.5, -0.22))
        return VGroup(chev, _flat(Circle(radius=0.13), B).move_to(0.40 * DOWN))
    if k == 10:   # bowtie (two facing triangles)
        return VGroup(_poly(A, (-0.5, 0.36), (-0.5, -0.36), (0.0, 0.0)), _poly(B, (0.5, 0.36), (0.5, -0.36), (0.0, 0.0)))
    # k == 11: ring with one coloured quarter
    ring = _flat(Annulus(inner_radius=0.26, outer_radius=0.5), A)
    wedge = _flat(AnnularSector(angle=PI / 2, start_angle=PI / 2, inner_radius=0.26, outer_radius=0.5), B)
    return VGroup(ring, wedge)


def glyph(k: int, size: float = 0.5) -> VMobject:
    """Two-tone geometric mark k in [0, NUM_GLYPHS), fitted in a size×size box, centred at ORIGIN."""
    g = _glyph_unit(k)
    g.set_width(size) if g.get_width() >= g.get_height() else g.set_height(size)
    g.move_to(ORIGIN)
    g.k = int(k) % NUM_GLYPHS
    return g


def _card_frame(size: float) -> RoundedRectangle:
    card = RoundedRectangle(width=size, height=size, corner_radius=0.16 * size)
    card.set_fill(CARD_FILL, opacity=1.0)
    card.set_stroke(CARD_STROKE, width=1.2)
    return card


def glyph_card(k: int, size: float = 0.5) -> VGroup:
    """Rounded card with glyph k on it (the card's FRONT). Attributes: .card, .mark, .k"""
    card = _card_frame(size)
    mark = glyph(k, 0.60 * size)
    mark.move_to(card)
    out = VGroup(card, mark)
    out.card, out.mark, out.k = card, mark, int(k) % NUM_GLYPHS
    return out


def patch_card(variant: str, idx: int, size: float = 0.5) -> VGroup:
    """Same card size, showing tile idx's patch of pixels (the card's BACK). Attributes: .card, .patch, .idx"""
    card = _card_frame(size)
    arr = hero_array(variant)
    b = arr.shape[0] // N_TILES
    i0, j0 = divmod(idx, N_TILES)
    patch = _array_to_pixels(arr[i0 * b:(i0 + 1) * b, j0 * b:(j0 + 1) * b], 0.78 * size)
    patch.move_to(card)
    out = VGroup(card, patch)
    out.card, out.patch, out.idx = card, patch, idx
    return out


def ellipsis_mark(size: float = 0.4, color=MUTED) -> VGroup:
    """Three dots '…' (a mark, not text)."""
    r = 0.07 * size
    dots = VGroup(*[Dot(radius=r, fill_color=color) for _ in range(3)])
    dots.arrange(RIGHT, buff=0.16 * size)
    dots.no_rescale = True  # ribbon() leaves it at its own size
    return dots


def glyph_tray(size: float = 0.4, cols: int | None = None, gap: float | None = None) -> VGroup:
    """NUM_GLYPHS cards in a row (or a grid with `cols` columns) ending with an ellipsis. Attributes: .cards, .ellipsis"""
    gap = 0.18 * size if gap is None else gap
    cards = VGroup(*[glyph_card(k, size) for k in range(NUM_GLYPHS)])
    dots = ellipsis_mark(size)
    if cols is None or cols >= NUM_GLYPHS:
        cards.arrange(RIGHT, buff=gap)
        dots.next_to(cards, RIGHT, buff=1.6 * gap)
    else:
        rows = int(np.ceil(NUM_GLYPHS / cols))
        cards.arrange_in_grid(n_rows=rows, n_cols=cols, buff=gap)
        dots.next_to(cards[-1], RIGHT, buff=1.6 * gap)
    tray = VGroup(cards, dots)
    tray.cards, tray.ellipsis = cards, dots
    tray.move_to(ORIGIN)
    return tray


class FlipCard(Animation):
    """A card turning over: the front squashes to a sliver, the back grows from it."""

    def __init__(self, front: Mobject, back: Mobject, run_time: float = 0.5, rate_func=smooth, **kwargs):
        self.front, self.back = front, back
        back.move_to(front)
        self.front0, self.back0 = front.copy(), back.copy()
        group = VGroup(front, back) if all(isinstance(m, VMobject) for m in (front, back)) else Group(front, back)
        super().__init__(group, run_time=run_time, rate_func=rate_func, **kwargs)

    def interpolate_mobject(self, alpha: float) -> None:
        a = self.rate_func(self.time_spanned_alpha(alpha))
        if a < 0.5:
            self.front.become(self.front0.copy().stretch(max(np.cos(PI * a), 1e-3), 0))
            self.back.become(self.back0.copy().stretch(1e-3, 0).set_opacity(0))
        else:
            self.back.become(self.back0.copy().stretch(max(-np.cos(PI * a), 1e-3), 0))
            self.front.become(self.front0.copy().stretch(1e-3, 0).set_opacity(0))

    def clean_up_from_scene(self, scene) -> None:
        super().clean_up_from_scene(scene)
        scene.remove(self.front)


def flip_card(card_front: VGroup, card_back: VGroup, run_time: float = 0.5) -> Animation:
    """front -> back flip. The back is moved onto the front; after the flip only the back stays in the scene."""
    return FlipCard(card_front, card_back, run_time=run_time)


# ----------------------------------------------------------------------------
# Writer devices
# ----------------------------------------------------------------------------
def cursor(height: float = 0.5) -> VMobject:
    """Text cursor in ACCENT: an I-beam, a stem with a short horizontal bar at the top and at the bottom."""
    h = height
    stem, bar, wide = 0.10 * h, 0.10 * h, 0.40 * h          # stem width, bar thickness, bar width
    pts = [(-wide / 2, h / 2), (wide / 2, h / 2), (wide / 2, h / 2 - bar), (stem / 2, h / 2 - bar),
           (stem / 2, bar - h / 2), (wide / 2, bar - h / 2), (wide / 2, -h / 2), (-wide / 2, -h / 2),
           (-wide / 2, bar - h / 2), (-stem / 2, bar - h / 2), (-stem / 2, h / 2 - bar), (-wide / 2, h / 2 - bar)]
    beam = Polygon(*[np.array([x, y, 0.0]) for x, y in pts])
    beam.round_corners(0.03 * h)
    beam.set_fill(ACCENT, opacity=1.0)
    beam.set_stroke(width=0)
    return beam


def blink(cursor_mob: Mobject, n: int = 2, period: float = 0.5) -> Animation:
    """Blink n times (on/off each `period`); ends visible."""
    def _f(m, a):
        m.set_opacity(1.0 if (a * n) % 1.0 < 0.5 or a >= 1.0 else 0.0)
    return UpdateFromAlphaFunc(cursor_mob, _f, run_time=n * period, rate_func=linear)


def candidate_fan(ks: list[int], weights: list[float], size: float = 0.45) -> VGroup:
    """Glyph cards (top to bottom) with UNLABELED bars proportional to weights. Attributes: .cards, .bars"""
    wmax = max(max(weights), 1e-9)
    cards, bars, rows = VGroup(), VGroup(), VGroup()
    for k, w in zip(ks, weights):
        card = glyph_card(k, size)
        bar = RoundedRectangle(width=max(2.6 * size * w / wmax, 0.05), height=0.40 * size, corner_radius=0.12 * size)
        bar.set_fill(ACCENT, opacity=0.35 + 0.65 * w / wmax)
        bar.set_stroke(width=0)
        bar.next_to(card, RIGHT, buff=0.25 * size)
        cards.add(card)
        bars.add(bar)
        rows.add(VGroup(card, bar))
    rows.arrange(DOWN, buff=0.22 * size, aligned_edge=LEFT)
    fan = VGroup(rows)
    fan.cards, fan.bars, fan.rows = cards, bars, rows
    return fan


def ribbon(items: list[Mobject], height: float = 0.5, gap: float = 0.12) -> VGroup:
    """Arrange chips / cards / strips in one line, left to right; each item is scaled to `height` (a strip by its band)."""
    for it in items:
        if getattr(it, "no_rescale", False):
            continue
        ref = getattr(it, "band", it)
        h = ref.get_height()
        if h > 1e-6 and abs(h - height) > 1e-3:
            it.scale(height / h)
    line = VGroup(*items)
    line.arrange(RIGHT, buff=gap, aligned_edge=UP)
    for it in items:  # small marks (the ellipsis) sit on the centre line, not the top edge
        if getattr(it, "no_rescale", False):
            it.set_y(line[0].get_y())
    return line


_BASELINE_REF = "H"   # a Latin capital: sits on the baseline, never part of an Arabic word
CHIP_TEXT_SCALE = 1.24  # text scale per unit of chip height — the same for every word


def _baseline_text(s: str, font_size: int = 36, arabic: bool = True) -> Text:
    """Text plus .baseline_dy (baseline minus the text's own centre y). The word is shaped
    next to an invisible reference letter that is then dropped, so words of any shape share
    one baseline and one font size (sizing by bounding box made short words big)."""
    kw = dict(font="Amiri", disable_ligatures=False) if arabic else {}
    with register_font(AMIRI_PATH):
        t = Text(_BASELINE_REF + " " + s, font_size=font_size, fill_color=INK, **kw)
    ref = t.select_parts(_BASELINE_REF)
    base = ref.get_bottom()[1]
    for m in ref.family_members_with_points():
        for holder in t.get_family():
            if m in holder.submobjects:
                holder.remove(m)
    t.baseline_dy = base - t.get_center()[1]
    return t


def word_chip(s: str, height: float = 0.5, arabic: bool = True) -> VGroup:
    """A chip holding one word. Every word gets the same font size and baseline, so chips
    differ in width only. Attributes: .chip, .text"""
    text = _baseline_text(s, 36, arabic)
    k = CHIP_TEXT_SCALE * height
    text.scale(k)
    chip = RoundedRectangle(width=text.get_width() + 0.55 * height, height=height, corner_radius=0.26 * height)
    chip.set_fill(CARD_FILL, opacity=1.0)
    chip.set_stroke(CARD_STROKE, width=1.2)
    text.move_to(chip)
    text.shift((chip.get_center()[1] - 0.22 * height - (text.get_center()[1] + k * text.baseline_dy)) * UP)
    out = VGroup(chip, text)
    out.chip, out.text = chip, text
    return out


# ----------------------------------------------------------------------------
# Chat (plain bubbles and cards, no product chrome)
# ----------------------------------------------------------------------------
BUBBLE_FILL = "#2b3448"   # the user's chat bubble: lighter than cards, no outline


class _ChatBubble(VGroup):
    @property
    def body(self) -> RoundedRectangle:
        """The rounded part without the tail, where the bubble is NOW (a fresh shape built from
        the text's current place and scale — for measuring and anchoring, not for animating)."""
        k = self.text.get_width() / self._text_w0
        b = RoundedRectangle(width=self._body_w * k, height=self._body_h * k, corner_radius=self._body_r * k)
        return b.move_to(self.text.get_center())


def user_bubble(text_ar: str, width: float = 4.5) -> VGroup:
    """The user's chat message: a filled bubble that hugs its text (`width` is only a
    maximum), with a tail curling out of its bottom-right corner. The group's bounding box
    includes the tail; .body is the rounded part without it, and follows the bubble wherever it
    moves. Attributes: .bubble, .body, .text"""
    pad_x, pad_y = 0.34, 0.22
    text = ar_text(text_ar, font_size=34)
    text.set_max_width(width - 2 * pad_x)
    w, h = text.get_width() + 2 * pad_x, text.get_height() + 2 * pad_y + 0.06
    body = RoundedRectangle(width=w, height=h, corner_radius=min(0.30, h / 2))
    r, b = body.get_right()[0], body.get_bottom()[1]
    tail = VMobject()
    tail.start_new_path(np.array([r - 0.46, b + 0.20, 0.0]))
    tail.add_line_to(np.array([r - 0.46, b, 0.0]))
    tail.add_quadratic_bezier_curve_to(np.array([r - 0.06, b, 0.0]), np.array([r + 0.14, b - 0.13, 0.0]))
    tail.add_quadratic_bezier_curve_to(np.array([r - 0.02, b - 0.02, 0.0]), np.array([r, b + 0.30, 0.0]))
    tail.add_line_to(np.array([r - 0.46, b + 0.20, 0.0]))
    bubble = Union(body, tail)
    bubble.set_fill(BUBBLE_FILL, opacity=1.0)
    bubble.set_stroke(BUBBLE_FILL, width=0)
    text.move_to(body)
    out = _ChatBubble(bubble, text)
    out.bubble, out.text = bubble, text
    out._text_w0, out._body_w, out._body_h = text.get_width(), w, h
    out._body_r = min(0.30, h / 2)
    return out


def reply_card(width: float = 4.5, height: float = 3.2) -> VGroup:
    """Plain reply card the picture sits in. Attribute: .box"""
    box = RoundedRectangle(width=width, height=height, corner_radius=0.30)
    box.set_fill(CARD_FILL, opacity=0.65)
    box.set_stroke(CARD_STROKE, width=1.5)
    out = VGroup(box)
    out.box = box
    return out


# ----------------------------------------------------------------------------
# Boxes
# ----------------------------------------------------------------------------
def _box_motif(width: float, height: float, color) -> VGroup:
    """Identical inner motif for every model box: three stacked layers, offset diagonally."""
    w, h = 0.34 * width, 0.36 * height
    layers = VGroup()
    for k in range(3):
        r = RoundedRectangle(width=w, height=h, corner_radius=0.18 * h)
        r.set_fill(CARD_FILL, opacity=1.0)
        r.set_stroke(color, width=2.0, opacity=0.40 + 0.25 * k)
        r.shift((k - 1) * np.array([0.11 * width, -0.12 * height, 0.0]))
        layers.add(r)
    return layers


def model_box(width: float = 2.2, height: float = 1.4, label_ar: str | None = None) -> VGroup:
    """Rounded silhouette in ACCENT stroke (all model boxes look identical). Attributes: .box, .motif, .label (or None)"""
    box = RoundedRectangle(width=width, height=height, corner_radius=0.22 * height)
    box.set_fill(CARD_FILL, opacity=1.0)
    box.set_stroke(ACCENT, width=3.0)
    motif = _box_motif(width, height, ACCENT)
    motif.move_to(box)
    out = VGroup(box, motif)
    out.box, out.motif, out.label = box, motif, None
    if label_ar:
        label = ar_text(label_ar, font_size=30, color=INK_2)
        label.set_max_width(1.2 * width)
        label.next_to(box, DOWN, buff=0.15)
        out.add(label)
        out.label = label
    return out


def printer_box(width: float = 1.6, height: float = 1.0) -> VGroup:
    """Visibly smaller box in WARM stroke, labelled PRINTER_AR inside. Attributes: .box, .label"""
    box = RoundedRectangle(width=width, height=height, corner_radius=0.22 * height)
    box.set_fill(CARD_FILL, opacity=1.0)
    box.set_stroke(WARM, width=3.0)
    label = ar_text(PRINTER_AR, font_size=34, color=WARM)
    label.set_max_width(0.78 * width)
    if label.get_height() > 0.46 * height:
        label.set_height(0.46 * height)
    label.move_to(box)
    out = VGroup(box, label)
    out.box, out.label = box, label
    return out


# ----------------------------------------------------------------------------
# Printer / snow
# ----------------------------------------------------------------------------
def _box_blur(arr: np.ndarray, k: int) -> np.ndarray:
    """Separable box blur with an odd kernel k (edge-padded)."""
    if k <= 1:
        return arr
    r = k // 2
    p = np.pad(arr, ((r, r), (0, 0), (0, 0)), mode="edge")
    acc = np.zeros_like(arr)
    for dy in range(k):
        acc += p[dy:dy + arr.shape[0]]
    acc /= k
    p = np.pad(acc, ((0, 0), (r, r), (0, 0)), mode="edge")
    acc2 = np.zeros_like(arr)
    for dx in range(k):
        acc2 += p[:, dx:dx + arr.shape[1]]
    return acc2 / k


def snow_array(variant: str = "base", level: float = 1.0, seed: int = 7) -> np.ndarray:
    """Hero blended with deterministic TV snow. level 1 = pure snow, 0 = clean; in between the hero is also blurred."""
    level = float(np.clip(level, 0.0, 1.0))
    hero = hero_array(variant)
    n = hero.shape[0]
    rng = np.random.default_rng(seed)
    grain = rng.random((n, n))
    noise = np.repeat((0.12 + 0.80 * grain)[..., None], 3, axis=2)
    if level >= 1.0:
        return noise
    k = 1 + 2 * int(round(4 * level))
    base = _box_blur(hero, k)
    return np.clip((1.0 - level) * base + level * noise, 0.0, 1.0)


def snow_pixels(variant: str = "base", width: float = 2.4, level: float = 1.0, seed: int = 7) -> VGroup:
    """Pixel squares of snow_array (same geometry as hero_pixels at that width)."""
    return _array_to_pixels(snow_array(variant, level, seed), width)


def recolor_to(pixels: VGroup, arr: np.ndarray) -> Animation:
    """Animate an existing pixel VGroup's fills to a new (n, n, 3) array (raster order must match)."""
    target = pixels.copy()
    flat = arr.reshape(-1, 3)
    for sq, rgb in zip(target, flat):
        sq.set_fill(rgb_to_hex(np.clip(rgb, 0, 1)), opacity=1.0)
    return Transform(pixels, target)


# ----------------------------------------------------------------------------
# Uploaded photo: one soft continuous strip (clearly not cards)
# ----------------------------------------------------------------------------
def soft_strip(variant: str = "alt_portrait", width: float = 3.0, height: float = 0.5, label: bool = True) -> VGroup:
    """Continuous blurred colour band read off the hero (three scanlines, blurred). Attributes: .band, .label (or None)"""
    arr = hero_array(variant)
    n = arr.shape[0]
    rows = [int(n * 0.22), int(n * 0.50), int(n * 0.80)]
    seq = np.concatenate([arr[r].reshape(n // 2, 2, 3).mean(axis=1) for r in rows], axis=0)  # 72 colours
    k = 7
    p = np.pad(seq, ((k // 2, k // 2), (0, 0)), mode="edge")
    seq = np.array([p[i:i + k].mean(axis=0) for i in range(len(seq))])
    m = len(seq)
    slice_w = width / m
    band = VGroup()
    for i, rgb in enumerate(seq):
        s = Rectangle(width=slice_w * 1.02, height=height)
        s.set_stroke(width=0)
        edge = min(i, m - 1 - i)
        s.set_fill(rgb_to_hex(rgb), opacity=min(1.0, 0.35 + 0.22 * edge))
        s.move_to(np.array([-width / 2 + (i + 0.5) * slice_w, 0.0, 0.0]))
        band.add(s)
    out = VGroup(band)
    out.band, out.label = band, None
    if label:
        lab = ar_text(UPLOAD_LABEL_AR, font_size=28, color=INK_2)
        lab.set_height(min(lab.get_height(), 0.55 * height))
        lab.next_to(band, DOWN, buff=0.10)
        out.add(lab)
        out.label = lab
    return out


# ----------------------------------------------------------------------------
# Layout helpers
# ----------------------------------------------------------------------------
def safe_rect() -> Rectangle:
    """The safe area (8% margins) — add it while composing, remove before rendering."""
    r = Rectangle(width=0.84 * FRAME_WIDTH, height=0.84 * FRAME_HEIGHT)
    r.set_fill(opacity=0)
    r.set_stroke(MUTED, width=1.0, opacity=0.7)
    return r


# ----------------------------------------------------------------------------
# Narration — the voice drives the picture
# ----------------------------------------------------------------------------
# config/narration.json holds the spoken lines; scripts/narrate.py voices them into
# media/audio/lines/ and records each line's length in index.json. A scene plays the
# picture for line <key> inside `with self.narrate(key):` — the line starts when the
# block starts, and on exit the scene holds until the line has been spoken (plus a
# breath). The scene logs when every line started to media/timing/<Scene>.json, and
# `narrate.py track` lays the voice down from that log, so sound and picture agree by
# construction whatever the voice, language or reading speed.
import json as _json
import re as _re
import warnings as _warnings
from contextlib import contextmanager as _contextmanager

NARRATION_PATH = REPO_ROOT / "config" / "narration.json"      # keys, pauses, English text
NARRATION_AR_PATH = REPO_ROOT / "config" / "narration_ar.json"  # Ali's Arabic text per key
# Which narration the scenes are timed to: "ar" = Ali's recorded Arabic (cleaned by
# scripts/process_takes.py), "ar_tts" = the offline Arabic placeholder voice (scripts/voice_ar_tts.py),
# "en" = the AI English placeholder. Set VO_LANG=ar_tts or VO_LANG=en to render with those.
VO_LANG = os.environ.get("VO_LANG", "ar")
LINES_DIR = MEDIA_DIR / "audio" / {"en": "lines", "ar_tts": "lines_ar/tts"}.get(VO_LANG, "lines_ar/clean")
LINES_INDEX = LINES_DIR / "index.json"
TIMING_DIR = MEDIA_DIR / "timing"
LINE_PAUSE = 0.4       # default breath after a line (a line's own `pause` in narration.json wins)
_EST_WORDS_PER_S = 2.6  # placeholder pace for lines that have not been voiced yet


@lru_cache(maxsize=1)
def _narration() -> dict[str, str]:
    if VO_LANG in ("ar", "ar_tts"):
        doc = _json.loads(NARRATION_AR_PATH.read_text(encoding="utf-8"))
        return {ln["key"]: ln["ar"] for seg in doc["segments"] for ln in seg["lines"] if ln.get("status") == "ready"}
    doc = _json.loads(NARRATION_PATH.read_text(encoding="utf-8"))
    return {ln["key"]: ln["text"] for seg in doc["segments"] for ln in seg["lines"]}


@lru_cache(maxsize=1)
def _pauses() -> dict[str, float]:
    doc = _json.loads(NARRATION_PATH.read_text(encoding="utf-8"))
    return {ln["key"]: float(ln.get("pause", LINE_PAUSE)) for seg in doc["segments"] for ln in seg["lines"]}


@lru_cache(maxsize=1)
def _voiced() -> dict:
    if not LINES_INDEX.is_file():
        return {}
    return _json.loads(LINES_INDEX.read_text(encoding="utf-8")).get("lines", {})


def line_text(key: str) -> str:
    try:
        return _narration()[key]
    except KeyError:
        raise KeyError(f"no narration line {key!r} in {NARRATION_PATH.name}") from None


def by_lang(en: float, ar: float) -> float:
    """A value that depends on the narration language, e.g. where a word falls in a line:
    self.beat_to(ln, by_lang(en=0.30, ar=0.41))."""
    return en if VO_LANG == "en" else ar


def line_phrases(key: str) -> list[tuple[float, float]]:
    """Voiced stretches inside the recorded line (seconds from its start), split at pauses —
    for placing an animation on a word. Empty when the recording has none (English TTS)."""
    entry = _voiced().get(key) or {}
    if entry.get("text") != line_text(key):      # a recording of older wording says nothing here
        return []
    return [tuple(p) for p in entry.get("phrases", [])]


_PIN_TOL = 0.12   # a pause is pinned to a punctuation mark only this close (in shares of the line); Ali also
                  # breathes where there is no comma, and pinning that to a far mark put words seconds early


def line_word_at(key: str, needle: str) -> float:
    """Seconds into line `key` where `needle` (a word or phrase of its text) is spoken: its share
    of the line's letters, laid over the voiced stretches (line_phrases) so pauses are skipped.
    An estimate (about ±0.15 s); without phrases it is spread over the whole line."""
    text = line_text(key)
    i = text.find(needle)
    if i < 0:
        raise ValueError(f"{needle!r} is not in line {key}: {text!r}")
    letters = lambda s: len(_re.sub(r"[\W_]", "", s))
    total = max(1, letters(text))
    frac = letters(text[:i]) / total
    phrases = line_phrases(key)
    if not phrases:
        return frac * line_duration(key)
    # The pauses between phrases fall at punctuation: pin each pause to the punctuation mark whose
    # share of the letters is closest, then spread letters evenly between those pins.
    spans = [b - a for a, b in phrases]
    voiced = sum(spans)
    marks = [letters(text[:m.end()]) / total for m in _re.finditer(r"[،,.؟?:!…](?=\s)", text)]
    knots_x, knots_t, used = [0.0], [0.0], -1
    for n in range(len(phrases) - 1):
        cum_t = sum(spans[: n + 1])
        options = [(abs(x - cum_t / voiced), k) for k, x in enumerate(marks) if k > used]
        if not options:
            break
        d, k = min(options)
        if d > _PIN_TOL or marks[k] <= knots_x[-1]:   # a breath with no punctuation near it stays unpinned
            continue
        knots_x.append(marks[k]); knots_t.append(cum_t); used = k
    knots_x.append(1.0); knots_t.append(voiced)
    t = float(np.interp(frac, knots_x, knots_t))
    for a, b in phrases:                               # voiced time -> time in the line
        if t < b - a - 1e-9:
            return a + t
        t -= b - a
    return phrases[-1][1]


def line_pause(key: str) -> float:
    """Silence after line `key` before the next line starts (or its segment ends): the viewer's
    time to take the line in. Set per line in narration.json; LINE_PAUSE when absent."""
    line_text(key)
    return _pauses()[key]


def line_duration(key: str) -> float:
    """Spoken length of line `key` in seconds. Falls back to a word-count estimate (with a
    warning) until the line has been voiced, so scenes render before the voice exists."""
    text = line_text(key)
    entry = _voiced().get(key)
    if entry and entry.get("text") == text:
        return float(entry["duration"])
    reason = "not voiced yet" if not entry else "text changed since it was voiced"
    _warnings.warn(f"narration {key}: {reason}; using an estimate — run scripts/narrate.py synth")
    return max(1.0, len(text.split()) / _EST_WORDS_PER_S)


class NarratedScene(Scene):
    """Scene whose timing follows its narration. See the section comment above."""

    def setup(self):
        super().setup()
        self._narration_log: list[dict] = []
        self._line: dict | None = None

    @_contextmanager
    def narrate(self, key: str, pause: float | None = None):
        """Play the block's animations while line `key` is spoken; on exit, hold until the
        line is finished plus `pause` (default: the line's own pause, line_pause(key)). If the
        block runs longer than that, the next line simply starts later — the picture is never
        cut short to fit the voice. Animations meant to run on through the pause (the process
        the line describes, left to play in silence) take their length from hold_left()."""
        if self._line is not None:
            raise RuntimeError(f"narrate({key!r}) nested inside narrate({self._line['key']!r})")
        dur = line_duration(key)
        if pause is None:
            pause = line_pause(key)
        self._line = {"key": key, "start": round(self.time, 4), "duration": round(dur, 4),
                      "pause": round(pause, 4)}
        try:
            yield self._line
        finally:
            line, self._line = self._line, None
            line["picture_end"] = round(self.time, 4)
            self._narration_log.append(line)
        left = line["start"] + dur + pause - self.time
        if left > 1e-3:
            self.wait(left)

    def line_left(self) -> float:
        """Seconds of the current line still to be spoken — size an animation to fill a line
        with run_time=self.line_left(). Zero outside a narrate block."""
        if self._line is None:
            return 0.0
        return max(0.0, self._line["start"] + self._line["duration"] - self.time)

    def hold_left(self) -> float:
        """Seconds until the current block's pause is over: line_left() plus the pause still to
        come. Zero outside a narrate block."""
        if self._line is None:
            return 0.0
        ln = self._line
        return max(0.0, ln["start"] + ln["duration"] + ln["pause"] - self.time)

    def tear_down(self):
        try:
            TIMING_DIR.mkdir(parents=True, exist_ok=True)
            out = TIMING_DIR / f"{type(self).__name__}.json"
            tmp = out.with_suffix(".tmp")
            tmp.write_text(_json.dumps({"scene": type(self).__name__, "duration": round(self.time, 4),
                                        "lines": self._narration_log}, indent=2) + "\n")
            tmp.replace(out)
        finally:
            super().tear_down()

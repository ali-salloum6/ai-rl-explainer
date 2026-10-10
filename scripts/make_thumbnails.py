#!/usr/bin/env python3
"""
Video 4's thumbnails: export the upload files and build the packaging test sheet.

  python3 scripts/make_thumbnails.py        # after rendering our_scenes/thumbnail.py (see its docstring)

in:   media/thumbnails/Thumb*.png                  1920x1080 Manim stills (our_scenes/thumbnail.py)
out:  docs/youtube/thumbnails/<stem>_1920x1080.png the full-size still
      docs/youtube/thumbnails/<stem>_1280x720.png  the upload file (>= 1280x720 for every variant, or YouTube drops a
                                                   whole A/B test to 480p; well under 2 MB for mobile upload)
      docs/youtube/thumbnails/packaging_test.png   each candidate as a viewer meets it: a phone feed card (390 px),
                                                   the suggested sidebar (168 px) and the 160 px stamp, next to the
                                                   channel's videos 2 and 3 (docs/img/src/)

The sheet is laid out in headless Chrome/Chromium (CHROME_BIN, or found automatically), so the Arabic titles are
shaped by a real browser.
"""
from __future__ import annotations

import glob
import html
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "media" / "thumbnails"
OUT = ROOT / "docs" / "youtube" / "thumbnails"
IMG = ROOT / "docs" / "img" / "src"

TITLE = "كيف الذكاء الاصطناعي بيتعلّم يغشّ؟"
# Manim still -> (file stem, title shown with it, note)
PAIRS = [
    ("ThumbA", "thumb_a_checkbox", TITLE, "A (default)"),
    ("ThumbB", "thumb_b_coin", TITLE, "B (challenger)"),
    ("ThumbC", "thumb_c_boat", TITLE, "C (spare)"),
]
NEIGHBOURS = [
    (IMG / "v2_written.png", "كيف الذكاء الاصطناعي بيرسم الصور؟", "3:48"),
    (IMG / "v3_c_shopkeeper.png", "كيف ايجنت ذكاء اصطناعي يدير محل؟", "5:54"),
]
CHANNEL = "Ali Salloum - علي سلوم"
DURATION = "7:05"  # the placeholder cut; set it to the final cut's length
EXTRA = 160  # headless Chrome's viewport is shorter than --window-size: ask for more, then crop


def chrome() -> str:
    c = [os.environ.get("CHROME_BIN")] + sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")) + [
        shutil.which(n) for n in ("google-chrome", "chromium", "chromium-browser", "chrome")]
    for x in c:
        if x and os.path.exists(x):
            return x
    sys.exit("No Chrome/Chromium found: set CHROME_BIN=/path/to/chrome")


def export() -> list[tuple[Path, str, str]]:
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for name, stem, title, note in PAIRS:
        src = SRC / f"{name}.png"
        if not src.is_file():
            print(f"skip {name}: render our_scenes/thumbnail.py {name} first")
            continue
        big, small = OUT / f"{stem}_1920x1080.png", OUT / f"{stem}_1280x720.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", "scale=1920:1080:flags=lanczos", str(big)], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", "scale=1280:720:flags=lanczos", str(small)], check=True)
        made.append((small, title, note))
        print(f"wrote {small.relative_to(ROOT)} ({small.stat().st_size // 1024} KB) and {big.name}")
    return made


def card(img: Path, title: str, w: int, dur: str, note: str = "") -> str:
    h = round(w * 9 / 16)
    t = html.escape(title)
    n = f'<div class="note">{html.escape(note)}</div>' if note else ""
    return (f'<div class="card" style="width:{w}px">{n}<div class="thumb" style="width:{w}px;height:{h}px">'
            f'<img src="file://{img}" style="width:{w}px;height:{h}px"><span class="dur">{dur}</span></div>'
            f'<div class="title" style="width:{w}px">{t}</div><div class="meta">{html.escape(CHANNEL)}</div></div>')


def sheet(made: list[tuple[Path, str, str]]) -> None:
    items = [(p, t, DURATION, n) for p, t, n in made] + [(p, t, d, "") for p, t, d in NEIGHBOURS if p.is_file()]
    feed = "".join(card(p, t, 390, d, n) for p, t, d, n in items)
    side = "".join(f'<div class="side"><div class="thumb" style="width:168px;height:94px"><img src="file://{p}" '
                   f'style="width:168px;height:94px"><span class="dur small">{d}</span></div><div class="stitle">'
                   f'{html.escape(t)}<div class="meta">{html.escape(CHANNEL)}</div></div></div>' for p, t, d, n in items)
    stamps = "".join(f'<div class="stamp"><img src="file://{p}" style="width:160px;height:90px">'
                     f'<div class="meta">{html.escape(n or "neighbour")}</div></div>' for p, t, d, n in items)
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><style>
    body {{ background:#0f0f0f; color:#f1f1f1; font-family:'DejaVu Sans', sans-serif; margin:24px; width:2150px; }}
    h2 {{ font-size:18px; color:#aaa; font-weight:normal; margin:18px 0 10px; }}
    .row {{ display:flex; gap:22px; flex-wrap:nowrap; align-items:flex-start; }}
    .thumb {{ position:relative; border-radius:10px; overflow:hidden; background:#222; }}
    .dur {{ position:absolute; right:6px; bottom:6px; background:rgba(0,0,0,.8); color:#fff; font-size:13px; padding:1px 5px; border-radius:4px; }}
    .dur.small {{ font-size:11px; right:4px; bottom:4px; }}
    .title {{ direction:rtl; text-align:right; font-size:16px; line-height:1.45; margin-top:8px; max-height:47px; overflow:hidden; }}
    .meta {{ direction:rtl; text-align:right; color:#aaa; font-size:12px; margin-top:3px; }}
    .note {{ color:#3dd6c6; font-size:13px; margin-bottom:6px; }}
    .side {{ display:flex; gap:10px; width:400px; flex-direction:row-reverse; }}
    .stitle {{ direction:rtl; text-align:right; font-size:14px; line-height:1.4; width:220px; }}
    .stamp {{ text-align:center; }}
    </style></head><body>
    <h2>Phone feed (390 px)</h2><div class="row">{feed}</div>
    <h2>Suggested sidebar (168 px)</h2><div class="row">{side}</div>
    <h2>Stamp (160 px): which is which at a glance?</h2><div class="row">{stamps}</div>
    </body></html>"""
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "sheet.html"
        f.write_text(doc, encoding="utf-8")
        raw = Path(td) / "raw.png"
        w, h = 2200, 900
        subprocess.run([chrome(), "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=1", f"--window-size={w},{h + EXTRA}", "--virtual-time-budget=4000",
                        "--allow-file-access-from-files", f"--screenshot={raw}", f"file://{f}"],
                       check=True, capture_output=True, timeout=90)
        out = OUT / "packaging_test.png"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-vf", f"crop={w}:{h}:0:0", str(out)], check=True)
        print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    sheet(export())

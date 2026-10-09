#!/usr/bin/env python3
"""
One sheet with every thumbnail the channel has tried and what it got, rendered with headless Chrome/Chromium.

  python3 scripts/packaging_history.py        # docs/img/src/*.png -> docs/img/packaging_history.png

Edit CARDS (and docs/img/src/) to add a new video; the numbers are the ones in docs/channel_data.md.
Needs Chrome or Chromium (CHROME_BIN, or found automatically) and ffmpeg for the crop (Pillow is used if present).
"""
import glob, os, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "docs/img/src", ROOT / "docs/img/packaging_history.png"
FONT = ROOT / "assets/fonts/Amiri-Regular.ttf"

# (image, label, title, when, result)
CARDS = [
    ("v1_c2_launch.png", "Video 1, launch", "كيف الموبايل بيعرف وجهك؟ الشبكات العصبية", "~25 Aug 2026",
     "Day 1: 663 impressions, 0.5% CTR, 3 views from impressions (2 s each). Froze after ~7 h; mostly Suggested."),
    ("v1_c1_swap.png", "Video 1, after the swap", "كيف تعمل الشبكات العصبية؟", "from 26 Aug",
     "+18 impressions in 24 h, 0.4% CTR, no new clicks. Lifetime to 13 Sep: 1,051 impressions, 1.33% CTR."),
    ("v2_written.png", "Video 2", "كيف الذكاء الاصطناعي بيرسم الصور؟", "27 Sep",
     "347 impressions in 3 days. Browse wave 30 Sep to 2 Oct: 560 Browse impressions, 5.36% CTR; stopped abruptly 3 Oct."),
    ("v3_a_loop.png", "Video 3, launch", "كيف AI Agent بيدير محل؟", "5 Oct 12:46 UTC",
     "6 impressions in 13.5 h (5 search, 1 suggested, 0 Browse). Swapped after ~14 h."),
    ("v3_c_shopkeeper.png", "Video 3, now", "كيف ايجنت ذكاء اصطناعي يدير محل؟", "thumbnail 6 Oct, title ~9 Oct",
     "24 impressions and 4 views in 3 days (1 click: CTR 4.17%). No Browse test seen."),
]
EXTRA = 160  # headless Chrome's viewport is shorter than --window-size: ask for more, then crop


def chrome() -> str:
    c = [os.environ.get("CHROME_BIN")] + sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")) + [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Chromium.app/Contents/MacOS/Chromium"
    ] + [shutil.which(n) for n in ("google-chrome", "chromium", "chromium-browser", "chrome")]
    for x in c:
        if x and Path(x).exists():
            return x
    sys.exit("No Chrome/Chromium found: set CHROME_BIN=/path/to/chrome")


def main() -> None:
    w, h = 1780, 470
    cards = "".join(
        f'<div class="c"><img src="file://{SRC / img}"><div class="l">{lab}</div><div class="t">{t}</div>'
        f'<div class="m">{when}</div><div class="r">{res}</div></div>' for img, lab, t, when, res in CARDS)
    html = f"""<!doctype html><meta charset="utf-8"><style>
@font-face{{font-family:Amiri;src:url("file://{FONT}")}}
html,body{{margin:0}}body{{background:#0f0f0f;color:#eee;font:15px/1.35 Arial,sans-serif;width:{w}px;height:{h}px;overflow:hidden}}
.g{{display:flex;gap:20px;padding:26px 24px}}.c{{width:332px}}img{{width:332px;height:187px;border-radius:10px;display:block;background:#000}}
.l{{color:#3dd6c6;font-weight:700;margin-top:10px}}.t{{direction:rtl;text-align:right;font:22px Amiri,serif;margin-top:6px;height:66px}}
.m{{color:#999;font-size:13px;margin-top:2px}}.r{{margin-top:10px;font-size:14px}}</style>
<div class="g">{cards}</div>"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        f, raw = Path(td, "s.html"), Path(td, "raw.png")
        f.write_text(html, encoding="utf-8")
        subprocess.run([chrome(), "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                        f"--window-size={w},{h + EXTRA}", "--virtual-time-budget=4000", "--allow-file-access-from-files",
                        f"--screenshot={raw}", f"file://{f}"], check=True, capture_output=True, timeout=90)
        try:
            from PIL import Image
            Image.open(raw).crop((0, 0, w, h)).save(OUT)
        except ImportError:
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-vf", f"crop={w}:{h}:0:0", str(OUT)], check=True)
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()

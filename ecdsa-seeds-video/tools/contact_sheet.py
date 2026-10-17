"""Tile frames of a video into labelled contact sheets for quick review.

usage: contact_sheet.py VIDEO OUT_PREFIX [--every SEC] [--times t1,t2,...] [--cols 4] [--width 480]
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def duration(video):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out")
    ap.add_argument("--every", type=float, default=2.0)
    ap.add_argument("--times", default="")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--rows", type=int, default=4)
    ap.add_argument("--width", type=int, default=480)
    a = ap.parse_args()
    total = duration(a.video)
    if a.times:
        times = [float(t) for t in a.times.split(",")]
    else:
        end = min(a.end or total, total - 0.05)
        times, t = [], a.start
        while t <= end:
            times.append(round(t, 2))
            t += a.every
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    frames = []
    with tempfile.TemporaryDirectory() as td:
        for i, t in enumerate(times):
            p = Path(td) / f"f{i:04d}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", a.video, "-frames:v", "1",
                            "-vf", f"scale={a.width}:-1", str(p)], check=True)
            if p.exists():
                im = Image.open(p).convert("RGB")
                canvas = Image.new("RGB", (im.width, im.height + 22), (0, 0, 0))
                canvas.paste(im, (0, 0))
                d = ImageDraw.Draw(canvas)
                d.text((4, im.height + 2), f"{t:6.1f}s", fill=(255, 220, 0), font=font)
                frames.append(canvas)
    per = a.cols * a.rows
    for s in range(0, len(frames), per):
        chunk = frames[s:s + per]
        w, h = chunk[0].size
        rows = (len(chunk) + a.cols - 1) // a.cols
        sheet = Image.new("RGB", (a.cols * w + (a.cols - 1) * 4, rows * h + (rows - 1) * 4), (60, 60, 60))
        for j, im in enumerate(chunk):
            sheet.paste(im, ((j % a.cols) * (w + 4), (j // a.cols) * (h + 4)))
        out = f"{a.out}_{s // per:02d}.png"
        sheet.save(out)
        print(out)


if __name__ == "__main__":
    main()

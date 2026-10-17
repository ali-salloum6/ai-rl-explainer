"""Flag moments where rendered content touches the frame edge (text or shapes running off-screen).

    python tools/qa_edges.py [-q h]          # scans build/media/videos/*/<res>/*.mp4 at 2 fps
"""
import argparse
import glob
import subprocess

import numpy as np

RES = {"l": "480p15", "m": "720p30", "h": "1080p60", "p": "1440p60", "k": "2160p60"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-q", "--quality", default="h", choices=RES)
    ap.add_argument("--threshold", type=int, default=80, help="grey level that counts as content")
    a = ap.parse_args()
    w, h, border = 480, 270, 3
    clean = True
    for f in sorted(glob.glob(f"build/media/videos/*/{RES[a.quality]}/*.mp4")):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-vf", f"fps=2,scale={w}:{h}", "-f", "rawvideo",
                              "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
        frames = np.frombuffer(raw, np.uint8).reshape(-1, h, w)
        hits = []
        for i, fr in enumerate(frames):
            edges = {"left": fr[:, :border], "right": fr[:, -border:], "top": fr[:border, :], "bottom": fr[-border:, :]}
            sides = [k for k, e in edges.items() if (e > a.threshold).sum() > 2]
            if sides:
                hits.append(f"{i / 2:.1f}s {'/'.join(sides)}")
        clean &= not hits
        print(f"{f.split('/')[-1]:22} {'ok' if not hits else 'EDGE: ' + ', '.join(hits[:8])}")
    raise SystemExit(0 if clean else 1)


if __name__ == "__main__":
    main()

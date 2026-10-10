#!/usr/bin/env python3
"""
YouTube chapters for the description, from the rendered segments' lengths (the cut is their plain concat).

  python3 scripts/chapters.py            # print the chapters, the total and the card time
  python3 scripts/chapters.py --write    # also put them in place of {CHAPTERS} in docs/youtube/description.txt

Run it after the build you upload (Ali's voice), so the times match that cut. YouTube needs the first
chapter at 0:00, at least three chapters and each at least 10 s long; this checks all three.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIO = REPO_ROOT / "config" / "audio_manifest.json"
SCENES = REPO_ROOT / "config" / "scenes_manifest.json"
TIMING_DIR = REPO_ROOT / "media" / "timing"
DESCRIPTION = REPO_ROOT / "docs" / "youtube" / "description.txt"

TITLES = {
    "hook": "قارب ربح السباق بدون ما يخلّصو",
    "bit1_maze": "متاهة ونقطة: كيف الجايزة بترسم الطريق",
    "bit2_coin": "ليرة عالطريق: بيتعلّم اللي منكافئو عليه",
    "bit3_likes": "زر اللايك: الناس كجايزة",
    "bit4_tests": "الإيجنتات بتصلّح الاختبار، وقصة الكابتشا",
    "bit5_scratch": "المسودّة: شو صار لما عاقبوه",
    "bit6_recap": "باختصار",
}
CARD_LINE = ("bit3_likes", "bit3_likes.6")   # the dial returns at «أكيد»: the card to video 3 goes here


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                          "default=nw=1:nk=1", str(path)], capture_output=True, text=True, check=True).stdout
    return float(out)


def stamp(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true", help="fill {CHAPTERS} in docs/youtube/description.txt")
    args = ap.parse_args()
    segs = json.loads(AUDIO.read_text(encoding="utf-8"))["segments"]
    scene_cls = {s["id"]: s["scene"].split(":", 1)[1]
                 for s in json.loads(SCENES.read_text(encoding="utf-8"))["segments"]}
    t, rows, starts, problems = 0.0, [], {}, []
    for s in segs:
        d = duration(REPO_ROOT / s["video"])
        starts[s["id"]] = t
        rows.append(f"{stamp(t)} {TITLES[s['id']]}")
        if d < 10:
            problems.append(f"{s['id']} is {d:.1f}s; YouTube wants every chapter at least 10 s")
        t += d
    if len(rows) < 3:
        problems.append("YouTube wants at least three chapters")
    block = "\n".join(rows)
    print(block)
    print(f"\ntotal {stamp(t)} ({t:.1f}s)")
    seg, key = CARD_LINE
    log = TIMING_DIR / f"{scene_cls[seg]}.json"
    if log.is_file():
        line = next((ln for ln in json.loads(log.read_text())["lines"] if ln["key"] == key), None)
        if line:
            print(f"card to video 3 at {stamp(starts[seg] + line['start'])} ({key}, the dial at «أكيد»)")
    if problems:
        print("\nProblems:\n  " + "\n  ".join(problems))
        sys.exit(1)
    if args.write:
        txt = DESCRIPTION.read_text(encoding="utf-8")
        if "{CHAPTERS}" not in txt:
            sys.exit(f"no {{CHAPTERS}} left in {DESCRIPTION.relative_to(REPO_ROOT)}; edit the old ones by hand")
        DESCRIPTION.write_text(txt.replace("{CHAPTERS}", block), encoding="utf-8")
        print(f"wrote the chapters into {DESCRIPTION.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()

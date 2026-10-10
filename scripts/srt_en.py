#!/usr/bin/env python3
"""
English subtitles for the Arabic cut, from the same timing as the Arabic ones.

Every line's English text (config/narration.json) is shown while its Arabic line is spoken: where the
scene started the line (media/timing/<Scene>.json, written by NarratedScene) for as long as the voiced
Arabic lasts (the recorded index, or the placeholder voice's), offset by the real length of every
segment before it. Long lines split in two at a clause, like the Arabic cues.

  python3 scripts/srt_en.py                       # Ali's recorded voice (media/audio/lines_ar/clean)
  python3 scripts/srt_en.py --voice ar_tts        # the placeholder voice (media/audio/lines_ar/tts)
  python3 scripts/srt_en.py --out docs/youtube/subtitles_en.srt

YouTube: Subtitles -> Add language -> English -> upload. (Also add an English title and description:
docs/youtube/publish_pack.md.)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCENES = ROOT / "config" / "scenes_manifest.json"
AUDIO = ROOT / "config" / "audio_manifest.json"
NARR = ROOT / "config" / "narration.json"
TIMING = ROOT / "media" / "timing"
INDEX = {"ar": ROOT / "media/audio/lines_ar/clean/index.json", "ar_tts": ROOT / "media/audio/lines_ar/tts/index.json"}
MAX_CHARS, HOLD = 84, 0.6


def duration(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                        "default=noprint_wrappers=1:nokey=1", str(p)], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def split(text: str) -> list[str]:
    if len(text) <= MAX_CHARS:
        return [text]
    cuts = [m.end() for m in re.finditer(r"[.?!:;](?=\s)|,(?=\s)|\s—(?=\s)", text)]
    if not cuts:
        return [text]
    cut = min(cuts, key=lambda c: abs(c - len(text) / 2))
    return [text[:cut].strip(), text[cut:].strip()]


def stamp(t: float) -> str:
    t = max(0.0, t)
    ms = int(round((t - int(t)) * 1000))
    s = int(t) + (ms == 1000)
    ms = 0 if ms == 1000 else ms
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d},{ms:03d}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--voice", choices=["ar", "ar_tts"], default="ar")
    ap.add_argument("--out", type=Path, default=ROOT / "media" / "output" / "full_cut_ar.en.srt")
    args = ap.parse_args()
    en = {l["key"]: l["text"] for s in json.loads(NARR.read_text(encoding="utf-8"))["segments"] for l in s["lines"]}
    index = json.loads(INDEX[args.voice].read_text(encoding="utf-8"))["lines"]
    scenes = json.loads(SCENES.read_text(encoding="utf-8"))["segments"]
    videos = {s["id"]: ROOT / s["video"] for s in json.loads(AUDIO.read_text(encoding="utf-8"))["segments"]}
    cues, offset = [], 0.0
    for seg in scenes:
        cls = seg["scene"].split(":", 1)[1]
        log = json.loads((TIMING / f"{cls}.json").read_text(encoding="utf-8"))
        seg_dur = duration(videos[seg["id"]])
        for ln in log["lines"]:
            dur = float(index.get(ln["key"], {}).get("duration", ln["duration"]))
            parts = split(en[ln["key"]])
            total = sum(len(p) for p in parts)
            t, done = offset + ln["start"], 0
            for p in parts:
                share = dur * len(p) / total
                cues.append([t + 0.0, t + share, p])
                t += share
        offset += seg_dur
    for k, c in enumerate(cues):
        nxt = cues[k + 1][0] if k + 1 < len(cues) else c[1] + HOLD
        c[1] = min(c[1] + HOLD, nxt - 0.04)
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(f"{i}\n{stamp(a)} --> {stamp(b)}\n{t}\n\n" for i, (a, b, t) in enumerate(cues, 1)),
                   encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}: {len(cues)} cues over {offset:.1f}s")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Export ~8–12 review keyframes for a segment into keyframes/<id>/.

Examples:
  python3 scripts/export_keyframes.py --segment bit14
  python3 scripts/export_keyframes.py --segment bit14 --count 10
  python3 scripts/export_keyframes.py --segment bit14 --times 0.5,3,6,8,9,12
  python3 scripts/export_keyframes.py --segment bit14 --video media/Bit14LossFunction.mp4
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = REPO_ROOT / "config" / "audio_manifest.json"
DEFAULT_COUNT = 10


def load_manifest(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def ffprobe_duration(path: Path) -> float:
    r = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(r.stdout.strip())


def even_times(duration: float, count: int) -> list[float]:
    if count < 1:
        raise ValueError("count must be >= 1")
    if duration <= 0:
        return [0.0]
    # Stay slightly inside the clip so the last frame is not EOF-empty.
    end = max(duration - 0.05, 0.0)
    if count == 1:
        return [end * 0.5]
    return [end * i / (count - 1) for i in range(count)]


def parse_times(raw: str) -> list[float]:
    out: list[float] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        out.append(float(part))
    if not out:
        raise ValueError("no times parsed from --times")
    return out


def export_frame(video: Path, t: float, out_png: Path) -> None:
    out_png.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{t:.3f}",
            "-i", str(video),
            "-frames:v", "1",
            "-q:v", "2",
            str(out_png),
        ],
        check=True,
    )


def resolve_video(repo: Path, seg: dict, override: Path | None) -> Path:
    if override is not None:
        path = override if override.is_absolute() else repo / override
        if not path.is_file():
            sys.exit(f"Missing --video file: {path}")
        return path

    # Prefer muxed (has VO timing) when present; else silent render.
    out_dir = repo / "media" / "output"
    mux_name = seg.get("output") or f"{seg['id']}_with_audio.mp4"
    muxed = out_dir / mux_name
    if muxed.is_file():
        return muxed

    silent = repo / seg["video"]
    if silent.is_file():
        return silent

    sys.exit(
        f"No video for segment {seg['id']!r}: tried {muxed} and {silent}"
    )


def main() -> None:
    p = argparse.ArgumentParser(description="Export review keyframes into keyframes/<id>/")
    p.add_argument("--segment", required=True, metavar="ID", help="Segment id (e.g. bit14)")
    p.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="audio_manifest.json",
    )
    p.add_argument("--video", type=Path, default=None, help="Override input MP4")
    p.add_argument(
        "--count",
        type=int,
        default=DEFAULT_COUNT,
        help=f"Evenly spaced frames (default {DEFAULT_COUNT}); ignored if --times set",
    )
    p.add_argument(
        "--times",
        type=str,
        default=None,
        help="Comma-separated cue times in seconds (e.g. 0.5,3,6,9)",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Override output dir (default keyframes/<id>/)",
    )
    args = p.parse_args()

    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        sys.exit("ffmpeg and ffprobe must be on PATH")

    manifest_path = args.manifest if args.manifest.is_absolute() else REPO_ROOT / args.manifest
    data = load_manifest(manifest_path)
    seg = next((s for s in data["segments"] if s.get("id") == args.segment), None)
    if seg is None:
        sys.exit(f"Unknown segment id: {args.segment!r}")

    video = resolve_video(REPO_ROOT, seg, args.video)
    duration = ffprobe_duration(video)
    times = parse_times(args.times) if args.times else even_times(duration, args.count)

    out_dir = args.out_dir
    if out_dir is None:
        out_dir = REPO_ROOT / "keyframes" / args.segment
    elif not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir

    if out_dir.exists():
        for old in out_dir.glob("*.png"):
            old.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for i, t in enumerate(times):
        t_clamped = min(max(t, 0.0), max(duration - 0.01, 0.0))
        path = out_dir / f"{i:02d}_t{t_clamped:.2f}s.png"
        export_frame(video, t_clamped, path)
        written.append(path)
        print(f"wrote {path.relative_to(REPO_ROOT)}  (t={t_clamped:.2f}s)")

    print(f"Done: {len(written)} frames → {out_dir.relative_to(REPO_ROOT)}  (source {video.relative_to(REPO_ROOT)})")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Render Manim segments listed in config/scenes_manifest.json.

Incremental by default (skip up-to-date silent MP4s):
  ./scripts/render_segments.py --segment bit13             # preview, only if changed
  MANIM_HD=1 ./scripts/render_segments.py                 # HD, skip up-to-date segments
  ./scripts/render_segments.py --force --segment bit13    # force re-render

Pair with:
  python3 scripts/mux_audio.py --segment bit13
  python3 scripts/assemble_final.py
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCENES = REPO_ROOT / "config/scenes_manifest.json"
DEFAULT_AUDIO = REPO_ROOT / "config/audio_manifest.json"
PREVIEW_WIDTH = 854
HD_WIDTH = 1920


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def video_width(path: Path) -> int | None:
    if not path.is_file():
        return None
    try:
        r = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return int(r.stdout.strip())
    except (subprocess.CalledProcessError, ValueError, OSError):
        return None


def source_paths(scene_entry: dict) -> list[Path]:
    paths: list[Path] = []
    scene_file = scene_entry["scene"].split(":", 1)[0]
    paths.append(REPO_ROOT / scene_file)
    for dep in scene_entry.get("deps") or []:
        paths.append(REPO_ROOT / dep)
    return paths


def needs_render(
    scene_entry: dict,
    video_path: Path,
    *,
    hd: bool,
) -> tuple[bool, str]:
    expected_w = HD_WIDTH if hd else PREVIEW_WIDTH
    if not video_path.is_file():
        return True, "missing silent MP4"

    width = video_width(video_path)
    if width != expected_w:
        return True, f"resolution {width or '?'} ≠ expected {expected_w}"

    v_mtime = video_path.stat().st_mtime
    for src in source_paths(scene_entry):
        if not src.is_file():
            return True, f"source missing: {src.relative_to(REPO_ROOT)}"
        if src.stat().st_mtime > v_mtime:
            return True, f"newer source: {src.relative_to(REPO_ROOT)}"

    return False, "up to date"


def parse_scene(spec: str) -> tuple[str, str]:
    if ":" not in spec:
        sys.exit(f"Invalid scene spec {spec!r} (expected path:ClassName)")
    file_part, class_part = spec.split(":", 1)
    return file_part, class_part


def main() -> None:
    p = argparse.ArgumentParser(
        description="Render Manim segments (skips up-to-date silent MP4s by default)."
    )
    p.add_argument(
        "--scenes-manifest",
        type=Path,
        default=DEFAULT_SCENES,
        help="config/scenes_manifest.json",
    )
    p.add_argument(
        "--audio-manifest",
        type=Path,
        default=DEFAULT_AUDIO,
        help="config/audio_manifest.json (for silent video paths)",
    )
    p.add_argument(
        "--segment",
        action="append",
        dest="segments",
        metavar="ID",
        help="Only these segment id(s); repeatable",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Re-render even when the silent MP4 is up to date",
    )
    p.add_argument(
        "--stale",
        action="store_true",
        help=argparse.SUPPRESS,  # deprecated no-op; skip-up-to-date is now default
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would render, do not invoke manimgl",
    )
    p.add_argument(
        "manim_args",
        nargs="*",
        help="Extra flags forwarded to manimgl (e.g. -n 3)",
    )
    args = p.parse_args()

    scenes_data = load_json(args.scenes_manifest)
    audio_data = load_json(args.audio_manifest)
    video_by_id = {s["id"]: REPO_ROOT / s["video"] for s in audio_data["segments"]}

    entries = scenes_data["segments"]
    if args.segments:
        wanted = set(args.segments)
        entries = [e for e in entries if e["id"] in wanted]
        missing = wanted - {e["id"] for e in entries}
        if missing:
            sys.exit(f"Unknown segment id(s): {', '.join(sorted(missing))}")

    hd = os.environ.get("MANIM_HD", "0") == "1"
    manim = os.environ.get("MANIM", str(REPO_ROOT / ".venv/bin/manimgl"))
    manim_path = Path(manim)
    if not args.dry_run and not manim_path.is_file():
        sys.exit(f"Missing manimgl at {manim_path}")

    flags = ["-w", "--hd" if hd else "-l", "--video_dir", "./media"]
    rendered = skipped = 0

    for entry in entries:
        seg_id = entry["id"]
        video_path = video_by_id.get(seg_id)
        if video_path is None:
            sys.exit(f"No video path in audio manifest for segment {seg_id!r}")

        needs, reason = needs_render(entry, video_path, hd=hd)
        if not args.force and not needs:
            print(f"skip {seg_id}: {reason}")
            skipped += 1
            continue

        scene_file, scene_class = parse_scene(entry["scene"])
        cmd = [str(manim_path), scene_file, scene_class, *flags, *args.manim_args]
        label = "dry-run" if args.dry_run else ("render" if needs else "force")
        print(f"{label} {seg_id}: {reason if needs else 'forced'}")
        print("  ", " ".join(cmd))
        if not args.dry_run:
            subprocess.run(cmd, cwd=REPO_ROOT, check=True)
        rendered += 1

    qual = "HD" if hd else "preview"
    print(f"Done ({qual}): rendered {rendered}, skipped {skipped}")


if __name__ == "__main__":
    main()

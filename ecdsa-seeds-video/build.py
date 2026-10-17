#!/usr/bin/env python3
"""Build "It's Just Timestamps".

    python build.py preview                 # fast 480p silent preview with burned-in captions
    python build.py voice                   # TTS for every segment (ElevenLabs or OpenAI, by which key is set)
    python build.py render -q h             # render all scenes at 1080p60 (parallel)
    python build.py assemble -q h           # concat + voice + score + subtitles -> output/
    python build.py all                     # voice (if a key is set) + render + assemble, 1080p60

Scene timing follows audio/timings.json when it exists, so after `voice` the scenes must be
re-rendered for picture and narration to line up.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable
MANIM = str(Path(PY).parent / "manim")
QUALITY = {"l": (854, 480, 15), "m": (1280, 720, 30), "h": (1920, 1080, 60), "p": (2560, 1440, 60),
           "k": (3840, 2160, 60)}

sys.path.insert(0, str(ROOT / "tools"))
from narration import load_segments, scenes_in_order  # noqa: E402


def scene_files() -> dict[str, str]:
    files = {}
    for f in sorted((ROOT / "scenes").glob("s*.py")):
        for m in re.finditer(r"^class (\w+)\(VOScene\)", f.read_text(), re.M):
            files[m.group(1)] = f.name
    return files


def render(quality: str, jobs: int, only: list[str] | None = None, timeout: float | None = None):
    w, h, _ = QUALITY[quality]
    timeout = timeout or {"l": 900, "m": 1800}.get(quality, 7200)
    # Pre-build the background image once so parallel renders don't race to write it.
    subprocess.run([PY, "-c", f"import sys; sys.path.insert(0, 'scenes'); import common; common._background_path({w}, {h})"],
                   cwd=ROOT, check=True, capture_output=True)
    files = scene_files()
    order = [s for s in scenes_in_order(load_segments()) if not only or s in only]
    logs = ROOT / "build" / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    def one(name: str):
        t0 = time.time()
        log = logs / f"{name}_{quality}.log"
        cmd = [MANIM, f"-q{quality}", "--disable_caching", "--media_dir", "../build/media", files[name], name]
        with open(log, "w") as fh:
            try:  # a Manim exception can leave the process hung on its ffmpeg pipe
                rc = subprocess.run(cmd, cwd=ROOT / "scenes", stdout=fh, stderr=subprocess.STDOUT,
                                    timeout=timeout).returncode
            except subprocess.TimeoutExpired:
                rc = 124
        return name, rc, time.time() - t0, log

    print(f"rendering {len(order)} scenes at -q{quality} with {jobs} jobs")
    failed = []
    with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
        for name, rc, dt, log in ex.map(one, order):
            status = "ok" if rc == 0 else f"FAILED (see {log})"
            print(f"  {name:16} {dt / 60:5.1f} min  {status}", flush=True)
            if rc:
                failed.append(name)
            else:
                late = re.findall(r"\[timing\].*", log.read_text())
                for line in late:
                    print("   ", line)
    if failed:
        sys.exit(f"render failed: {failed}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["preview", "voice", "render", "assemble", "all"])
    ap.add_argument("-q", "--quality", default="h", choices=QUALITY)
    ap.add_argument("-j", "--jobs", type=int, default=max(1, (os.cpu_count() or 2)))
    ap.add_argument("--scenes", default="", help="comma-separated scene names to render")
    ap.add_argument("--burn-subs", action="store_true")
    ap.add_argument("--voice", default=None, help="voice name/id (ElevenLabs default George, OpenAI default cedar)")
    ap.add_argument("--engine", choices=["elevenlabs", "openai"], default=None,
                    help="TTS engine; default: whichever API key is set (ElevenLabs first)")
    a, extra = ap.parse_known_args()  # anything unrecognised is passed on to tools/tts_openai.py
    only = [s for s in a.scenes.split(",") if s] or None

    eleven_vars = ("ELEVENLABS_API_KEY", "XI_API_KEY", "ELEVEN_API_KEY")
    engine = a.engine or ("elevenlabs" if any(os.environ.get(v) for v in eleven_vars)
                          else "openai" if os.environ.get("OPENAI_API_KEY") else None)

    def voice():
        if engine is None:
            sys.exit("no TTS key found: set ELEVENLABS_API_KEY or OPENAI_API_KEY, or pass --engine elevenlabs "
                     "when the key is injected as a network secret")
        tool = "tools/tts_elevenlabs.py" if engine == "elevenlabs" else "tools/tts_openai.py"
        cmd = [PY, tool] + (["--voice", a.voice] if a.voice else []) + extra
        subprocess.run(cmd, cwd=ROOT, check=True)

    def assemble(q, burn, allow_missing):
        cmd = [PY, "tools/assemble.py", "--quality", q] + (["--burn-subs"] if burn else [])
        cmd += ["--allow-missing-voice"] if allow_missing else []
        subprocess.run(cmd, cwd=ROOT, check=True)

    if a.step == "preview":
        render("l", a.jobs, only)
        assemble("l", True, True)
    elif a.step == "voice":
        voice()
    elif a.step == "render":
        render(a.quality, a.jobs, only)
    elif a.step == "assemble":
        assemble(a.quality, a.burn_subs, not (ROOT / "audio" / "timings.json").exists())
    elif a.step == "all":
        if engine:
            voice()
        else:
            print("no TTS key set: building with estimated timings and no voice")
        render(a.quality, a.jobs, only)
        assemble(a.quality, a.burn_subs, not (ROOT / "audio" / "timings.json").exists())


if __name__ == "__main__":
    main()

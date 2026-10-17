"""Assemble the final film from the rendered scenes.

1. Concatenates the scene renders in script order.
2. Lays every voice clip (audio/<id>.flac) at the exact time its scene started that segment.
3. Adds the procedural score (ducked under the voice) and sound-effect cues.
4. Writes subtitles (SRT, soft track) and loudness-normalises the mix to -16 LUFS.

    python tools/assemble.py --quality h            # final, 1080p60
    python tools/assemble.py --quality l --burn-subs  # quick preview with captions burned in
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import textwrap
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import music  # noqa: E402
from narration import AUDIO_DIR, ROOT, load_segments, scenes_in_order  # noqa: E402

SR = music.SR
QUALITY = {"l": (480, 15), "m": (720, 30), "h": (1080, 60), "p": (1440, 60), "k": (2160, 60)}
BUILD = ROOT / "build"
OUT = ROOT / "output"

VOICE_PEAK = 0.0  # set from data
MUSIC_REL_DB = -19.0       # score level relative to the voice, between lines
MUSIC_DUCK_DB = -7.0       # extra attenuation while someone is speaking
SFX_REL_DB = {"whoosh": -21.0, "chime": -19.0, "rewind": -23.0, "ticks": -21.0, "tick": -22.0}


def sh(cmd: list[str]) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def probe_duration(path: Path) -> float:
    return float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]))


def scene_files() -> dict[str, str]:
    files = {}
    for f in sorted((ROOT / "scenes").glob("s*.py")):
        for m in re.finditer(r"^class (\w+)\(VOScene\)", f.read_text(), re.M):
            files[m.group(1)] = f.stem
    return files


def read_audio(path: Path) -> np.ndarray:
    """Mono float samples at SR from any file ffmpeg can read (the voice clips are FLAC)."""
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768


def write_wav(path: Path, x: np.ndarray):
    x = np.clip(x, -1, 1)
    pcm = (x * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(pcm.shape[1] if pcm.ndim > 1 else 1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def db(x: float) -> float:
    return 10 ** (x / 20)


def smooth(x: np.ndarray, seconds: float) -> np.ndarray:
    """Hann-window moving average, computed on a 100 Hz envelope for speed."""
    hop = SR // 100
    m = len(x) // hop + 1
    env = np.pad(x, (0, m * hop - len(x))).reshape(m, hop).mean(axis=1)
    k = np.hanning(2 * max(1, int(seconds * 100)) + 1)
    env = np.convolve(env, k / k.sum(), mode="same")
    return np.interp(np.arange(len(x)) / hop, np.arange(m), env).astype(np.float32)


# ---------------------------------------------------------------- subtitles
def fmt_ts(t: float) -> str:
    t = max(0.0, t)
    h, rem = divmod(int(round(t * 1000)), 3600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


MAX_CUE = 88


def _split(units: list, lo: int, hi: int) -> list[tuple[int, int]]:
    """Split units[lo:hi] into cues of at most MAX_CUE characters, at sentence ends first,
    then the clause break nearest the middle, then the word boundary nearest the middle."""
    def text(a, b):
        out = ""
        for d, _, glue in units[a:b]:
            out += ("" if glue or not out else " ") + d
        return out

    if len(text(lo, hi)) <= MAX_CUE or hi - lo <= 1:
        return [(lo, hi)]
    cuts = [i for i in range(lo + 1, hi) if not units[i][2]]
    for pattern in (r"[.?!][”\"]?$", r"[,:;—][”\"]?$", r""):
        cand = [i for i in cuts if re.search(pattern, units[i - 1][0])] if pattern else cuts
        if pattern == r"[.?!][”\"]?$" and cand:
            parts, a = [], lo
            for c in cand:
                parts.append((a, c))
                a = c
            parts.append((a, hi))
            return [p for a_, b_ in parts for p in _split(units, a_, b_)]
        if cand:
            total = len(text(lo, hi))
            best = min(cand, key=lambda c: abs(len(text(lo, c)) - total / 2))
            return _split(units, lo, best) + _split(units, best, hi)
    return [(lo, hi)]


def cues_for(seg, start: float) -> list[tuple[float, float, str]]:
    units = seg.units()
    out = []
    for i, j in _split(units, 0, len(units)):
        text = ""
        for d, _, glue in units[i:j]:
            text += ("" if glue or not text else " ") + d
        w0 = seg.word_index_at_unit(units, i)
        w1 = max(w0, seg.word_index_at_unit(units, j) - 1)
        t0 = start + seg.time_of_word(w0, "start")
        t1 = start + seg.time_of_word(w1, "end") + 0.15
        out.append((t0, t1, text))
    # make cues contiguous within the segment (no flicker between them)
    for k in range(len(out) - 1):
        out[k] = (out[k][0], out[k + 1][0] - 0.02, out[k][2])
    return out


def write_srt(cues, path: Path):
    lines = []
    for n, (t0, t1, text) in enumerate(cues, 1):
        wrapped = "\n".join(textwrap.wrap(text, 46))
        lines.append(f"{n}\n{fmt_ts(t0)} --> {fmt_ts(t1)}\n{wrapped}\n")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_chapters(order, files, offsets, path: Path):
    """YouTube-style chapter list, using each scene's chapter card title."""
    lines = []
    for name, off in zip(order, offsets):
        src = (ROOT / "scenes" / f"{files[name]}.py").read_text()
        m = re.search(r'self\.chapter\(\s*\d+\s*,\s*"([^"]+)"', src)
        title = m.group(1) if m else "Intro: the 25-year-old mystery"
        mm, ss = divmod(int(off), 60)
        lines.append(f"{mm:02d}:{ss:02d} {title}")
    path.write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quality", default="h", choices=QUALITY)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--no-music", action="store_true")
    ap.add_argument("--no-sfx", action="store_true")
    ap.add_argument("--burn-subs", action="store_true", help="burn captions into the picture (previews)")
    ap.add_argument("--scenes", default="", help="comma-separated subset of scenes (chapter previews)")
    ap.add_argument("--allow-missing-voice", action="store_true",
                    help="assemble even if some voice clips are missing (silent preview)")
    args = ap.parse_args()

    height, fps = QUALITY[args.quality]
    qdir = f"{height}p{fps}"
    segs = load_segments()
    order = scenes_in_order(segs)
    if args.scenes:
        keep = set(args.scenes.split(","))
        order = [s for s in order if s in keep]
        segs = {k: v for k, v in segs.items() if v.scene in keep}
    files = scene_files()
    work = BUILD / "assembly" / qdir
    work.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(exist_ok=True)

    videos, timelines, offsets = [], [], []
    t = 0.0
    for name in order:
        if name not in files:
            sys.exit(f"no scene file defines {name}")
        mp4 = BUILD / "media" / "videos" / files[name] / qdir / f"{name}.mp4"
        tl = BUILD / "timeline" / f"{name}_{qdir}.json"
        if not mp4.exists() or not tl.exists():
            sys.exit(f"missing render for {name} at {qdir}: {mp4} / {tl}")
        timeline = json.loads(tl.read_text())
        dur = probe_duration(mp4)
        if abs(dur - timeline["duration"]) > 2 / fps:
            print(f"warning: {name}: video {dur:.3f}s vs timeline {timeline['duration']:.3f}s")
        videos.append(mp4)
        timelines.append(timeline)
        offsets.append(t)
        t += dur
    total = t
    print(f"{len(videos)} scenes, {total / 60:.2f} min")

    # 1. video: stream-copy concat
    concat_list = work / "concat.txt"
    concat_list.write_text("".join(f"file '{v}'\n" for v in videos))
    video = work / "video.mp4"
    sh(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(video)])

    # 2. voice track and subtitles
    n = int(total * SR) + SR
    voice = np.zeros(n, dtype=np.float32)
    cues = []
    missing = []
    for off, tl in zip(offsets, timelines):
        for entry in tl["segments"]:
            seg = segs[entry["id"]]
            start = off + entry["start"]
            cues.extend(cues_for(seg, start))
            path = seg.audio_path
            if path is None:
                missing.append(seg.id)
                continue
            clip = read_audio(path)
            i0 = int(round(start * SR))
            voice[i0:i0 + len(clip)] += clip[: max(0, n - i0)]
    if missing and not args.allow_missing_voice:
        sys.exit(f"{len(missing)} voice clips missing (e.g. {missing[:5]}); run tools/tts_openai.py "
                 f"or pass --allow-missing-voice for a silent preview")
    has_voice = len(missing) < len(segs)
    srt = OUT / ("its_just_timestamps.srt" if not args.scenes else "partial.srt")
    write_srt(cues, srt)
    if not args.scenes:
        write_chapters(order, files, offsets, OUT / "chapters.txt")

    # 3. score + effects, levelled against the voice
    voice_rms = float(np.sqrt(np.mean(voice[np.abs(voice) > 0.01] ** 2))) if has_voice else db(-20)
    mix = np.stack([voice, voice], axis=1)
    speaking = smooth((np.abs(voice) > 0.01).astype(np.float32), 0.35) if has_voice else np.zeros(n)
    speaking = np.clip(speaking * 3, 0, 1)
    if not args.no_music:
        score = music.ambient(total + 1.0)[:n]
        score = np.pad(score, ((0, n - len(score)), (0, 0)))
        s_rms = float(np.sqrt(np.mean(score ** 2))) + 1e-9
        gain = voice_rms * db(MUSIC_REL_DB) / s_rms
        duck = db(MUSIC_DUCK_DB * speaking)[:, None]
        mix += score * gain * duck
    if not args.no_sfx:
        for off, tl in zip(offsets, timelines):
            for ev in tl.get("events", []):
                name = ev["sfx"]
                if name == "whoosh":
                    clip = music.whoosh()
                elif name == "chime":
                    clip = music.chime(ev.get("note", 81))
                elif name == "rewind":
                    clip = music.rewind(ev.get("duration", 2.5))
                elif name == "ticks":
                    clip = music.ticks(ev.get("duration", 4.0))
                else:
                    continue
                c_rms = float(np.sqrt(np.mean(clip[np.abs(clip).max(axis=1) > 1e-4] ** 2))) + 1e-9
                clip = clip * voice_rms * db(SFX_REL_DB.get(name, -22)) / c_rms
                i0 = int(round((off + ev["t"]) * SR))
                j = min(n, i0 + len(clip))
                if i0 < n:
                    mix[i0:j] += clip[: j - i0]
    mix = mix[: int(total * SR)]
    peak = np.abs(mix).max()
    if peak > 0.98:
        mix *= 0.98 / peak
    raw_audio = work / "mix.wav"
    write_wav(raw_audio, mix)

    # 4. loudness-normalise and mux
    stem = "its_just_timestamps" if has_voice else f"its_just_timestamps_preview_{qdir}"
    if args.scenes:
        stem += "_" + "_".join(order)
    out = args.out or OUT / f"{stem}.mp4"
    vf = []
    if args.burn_subs:
        style = ("FontName=Inter,FontSize=15,PrimaryColour=&H00F2EBE8,BackColour=&H99000000,"
                 "BorderStyle=4,Outline=0,Shadow=0,MarginV=18")
        vf = ["-vf", f"subtitles={srt}:force_style='{style}'"]
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(raw_audio)]
    if not args.burn_subs:
        cmd += ["-i", str(srt)]
    cmd += ["-map", "0:v", "-map", "1:a"]
    if not args.burn_subs:
        cmd += ["-map", "2:s", "-c:s", "mov_text", "-metadata:s:s:0", "language=eng"]
    cmd += vf
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p"] if vf else ["-c:v", "copy"]
    target = -16 if has_voice else -24  # without a voice the score must stay a background bed
    cmd += ["-af", f"loudnorm=I={target}:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", str(out)]  # no -shortest: it would stop at the last subtitle cue
    sh(cmd)
    print(f"wrote {out} ({probe_duration(out) / 60:.2f} min) and {srt}")


if __name__ == "__main__":
    main()

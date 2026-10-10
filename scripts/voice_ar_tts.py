#!/usr/bin/env python3
"""
Voice the Arabic narration with an offline placeholder voice, until Ali records his own.

For every line marked ready in config/narration_ar.json, the line's spoken form (numbers and Latin
names spelled the way they are said, see SPOKEN) goes to a text-to-speech command; the take is then
cleaned exactly like a recorded one (scripts/process_takes.py: trimmed to the speech, long pauses
shortened, levelled to -20 LUFS, 48 kHz mono) and written to media/audio/lines_ar/tts/<key>.wav, with
media/audio/lines_ar/tts/index.json in the same shape as the recorded index (duration, text, phrases).

The scenes time themselves to it with VO_LANG=ar_tts, and `scripts/narrate.py track --lang ar_tts`
lays it under the renders (into the same media/audio/<id>-vo-ar.wav files Ali's takes will replace).
Ali's recordings never read or overwrite anything here.

  python3 scripts/voice_ar_tts.py --cmd "/path/to/tts/venv/bin/python /path/to/say.py"
  python3 scripts/voice_ar_tts.py --key hook.1 --force

The command is called as  <cmd> "<spoken text>" <out.wav>  and must write a mono WAV (any rate).
It can also come from the AR_TTS_CMD environment variable. Unchanged lines are skipped.

An engine that is slow to load (XTTS: ~2 min per call) is better run in one batch:
  python3 scripts/voice_ar_tts.py --export lines.json            # the spoken forms of the lines to voice
  <batch tool> lines.json raw/                                   # writes raw/<key>.wav
  python3 scripts/voice_ar_tts.py --from-dir raw/ --voice xtts   # clean them up and index them
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import process_takes as pt  # noqa: E402  (the same clean-up as Ali's takes)

LINES_AR = REPO_ROOT / "config" / "narration_ar.json"
OUT_DIR = REPO_ROOT / "media" / "audio" / "lines_ar" / "tts"
INDEX = OUT_DIR / "index.json"

# How the script's digits and Latin names are said (the subtitles keep the script's writing).
SPOKEN = [
    (r"DeepSeek-R1-Zero", "ديب سيك آر وان زيرو"),
    (r"Claude 3\.7 Sonnet", "كلود تري بوينت سِفن سونِت"),
    (r"ChatGPT", "تشات جي بي تي"),
    (r"GPT-4", "جي بي تي فور"),
    (r"OpenAI", "أوبن إيه آي"),
    (r"\bGo\b", "غو"),
    (r"الـ\s+غو", "الغو"),
    (r"\b2025\b", "ألفين وخمسة وعشرين"),
    (r"\b2023\b", "ألفين وتلاتة وعشرين"),
    (r"\b2019\b", "ألفين وتسعطعش"),
    (r"\b2017\b", "ألفين وسبعطعش"),
    (r"\b2016\b", "ألفين وستطعش"),
    (r"\b2013\b", "ألفين وتلتطعش"),
    (r"\b71\b", "واحد وسبعين"),
    (r"\b20\b", "عشرين"),
    (r"\b16\b", "ستّطعش"),
    (r"[«»\"“”]", ""),
    (r"…", "، "),
    (r"\s+", " "),
]


def spoken_form(text: str) -> str:
    s = text
    for pat, rep in SPOKEN:
        s = re.sub(pat, rep, s)
    return s.strip()


def read_any_wav(path: Path) -> tuple[np.ndarray, int]:
    """Mono float audio from a WAV (16-bit or float), resampled by ffmpeg to 48 kHz 16-bit first."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "a.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-ac", "1", "-ar", "48000",
                        "-c:a", "pcm_s16le", str(tmp)], check=True)
        return pt.read_wav(tmp)


def clean_take(raw: Path, out: Path) -> tuple[float, list]:
    """A raw TTS take, cleaned like a recorded one (process_takes.py); returns its length and phrases."""
    x, sr = read_any_wav(raw)
    lead = np.zeros(int(0.25 * sr), dtype=np.float32)          # room for the speech detector's edges
    x = np.concatenate([lead, x, lead])
    spans, info = pt.speech_phrases(x, sr)
    y, phrases, _ = pt.edit(x, sr, spans)
    dur = pt.finish(y, sr, info["floor_db"], out, denoise=False)
    return dur, phrases


def voice(cmd: list[str], text: str, out: Path) -> tuple[float, list]:
    with tempfile.TemporaryDirectory() as td:
        raw = Path(td) / "raw.wav"
        r = subprocess.run([*cmd, text, str(raw)], capture_output=True, text=True)
        if r.returncode or not raw.is_file():
            raise RuntimeError(f"TTS failed ({r.returncode}): {r.stderr[-400:]}")
        return clean_take(raw, out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--cmd", default=os.environ.get("AR_TTS_CMD", ""), help="TTS command: <cmd> <text> <out.wav>")
    ap.add_argument("--voice", default="", help="a name for the voice, kept in the index")
    ap.add_argument("--key", action="append", dest="keys", metavar="KEY", help="only these line keys")
    ap.add_argument("--force", action="store_true", help="re-voice even if unchanged")
    ap.add_argument("--export", type=Path, help="write the spoken forms of the lines to voice to this JSON and stop")
    ap.add_argument("--from-dir", type=Path, help="take raw/<key>.wav from this folder instead of running --cmd")
    args = ap.parse_args()
    if not (args.cmd or args.export or args.from_dir):
        sys.exit("No TTS command: pass --cmd, set AR_TTS_CMD, or use --export / --from-dir (see the docstring).")
    cmd = shlex.split(args.cmd) if args.cmd else ["batch"]
    lines = [ln for seg in json.loads(LINES_AR.read_text(encoding="utf-8"))["segments"]
             for ln in seg["lines"] if ln.get("status") == "ready"]
    if args.keys:
        lines = [ln for ln in lines if ln["key"] in args.keys]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    index = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.is_file() else {
        "notes": "Placeholder Arabic voice (scripts/voice_ar_tts.py), cleaned like a recorded take. 'phrases' are the "
                 "voiced stretches inside each line (s). Replaced by Ali's recordings (lines_ar/clean) once made.",
        "lines": {}}
    voice_id = args.voice or (Path(cmd[-1]).stem if args.cmd else "batch")
    todo = [ln for ln in lines if args.force or not (
        (e := index["lines"].get(ln["key"])) and e.get("text") == ln["ar"] and e.get("voice") == voice_id
        and (REPO_ROOT / e["file"]).is_file())]
    print(f"{len(lines)} lines, {len(lines) - len(todo)} up to date, {len(todo)} to voice with {voice_id}")
    if args.export:
        args.export.write_text(json.dumps([{"key": ln["key"], "text": spoken_form(ln["ar"])} for ln in todo],
                                          ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {args.export} ({len(todo)} lines)")
        return
    problems = []
    for n, ln in enumerate(todo, 1):
        out = OUT_DIR / f"{ln['key']}.wav"
        said = spoken_form(ln["ar"])
        try:
            if args.from_dir:
                raw = args.from_dir / f"{ln['key']}.wav"
                if not raw.is_file():
                    raise RuntimeError(f"no raw take {raw}")
                dur, phrases = clean_take(raw, out)
            else:
                dur, phrases = voice(cmd, said, out)
        except (RuntimeError, ValueError, subprocess.CalledProcessError) as e:
            problems.append(f"{ln['key']}: {e}")
            print(f"  [{n}/{len(todo)}] {ln['key']}: FAILED {e}")
            continue
        index["lines"][ln["key"]] = {"file": str(out.relative_to(REPO_ROOT)), "duration": round(dur, 3),
                                     "text": ln["ar"], "spoken": said, "voice": voice_id,
                                     "phrases": [[round(a, 2), round(b, 2)] for a, b in phrases]}
        tmp = INDEX.with_suffix(".tmp")
        tmp.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(INDEX)
        print(f"  [{n}/{len(todo)}] {ln['key']:16s} {dur:5.2f}s")
    total = sum(e["duration"] for e in index["lines"].values())
    print(f"\n{len(index['lines'])} lines, {total:.1f}s of speech -> {INDEX.relative_to(REPO_ROOT)}")
    if problems:
        print("\nProblems:\n  " + "\n  ".join(problems))
        sys.exit(1)


if __name__ == "__main__":
    main()

"""Generate the voiceover with the OpenAI TTS API, one clip per script segment.

Writes audio/<id>.wav (48 kHz mono, silence trimmed) and audio/timings.json with each
clip's duration and, unless --no-align, word timings from whisper-1 that the scenes use
to land visual beats on the right word.

    OPENAI_API_KEY=... python tools/tts_openai.py [--voice cedar] [--only c1,c2] [--force]

Clips whose text, voice, model and instructions are unchanged are reused.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from narration import AUDIO_DIR, TIMINGS, load_segments  # noqa: E402

DEFAULT_MODEL = "gpt-4o-mini-tts"
DEFAULT_VOICE = "cedar"
INSTRUCTIONS = """\
Voice: a warm, curious documentary narrator telling a true detective story about cryptography to smart,
tech-savvy listeners. Confident and clear, never salesy or theatrical.
Tone: intrigued; let a little wonder through on the reveals ("It's just timestamps.", "It's real.").
Pacing: measured and natural, about 150 words per minute. Slow down slightly for numbers, equations,
dates and hexadecimal. Brief, natural pauses at commas, colons and sentence ends.
Emphasis: lightly stress key terms the first time they appear (private key, public key, nonce, seed,
lattice, timestamp).
Pronunciation: read "mod" as "mod". Read spelled-out letters (E-C-D-S-A, L-L-L, D-R-B-G) letter by letter.
Read numbers in full exactly as written.
"""

WORD_RE = re.compile(r"[\w'’]+")


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def duration_of(path: Path) -> float:
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]))


def clip_hash(text: str, model: str, voice: str, instructions: str, speed: float) -> str:
    return hashlib.sha256(f"{model}|{voice}|{speed}|{instructions}|{text}".encode()).hexdigest()[:16]


def synthesize(client, text: str, out: Path, model: str, voice: str, instructions: str, speed: float):
    kwargs = dict(model=model, voice=voice, input=text, response_format="wav")
    if model.startswith("gpt-4o"):
        kwargs["instructions"] = instructions
    if speed != 1.0:
        kwargs["speed"] = speed
    with client.audio.speech.with_streaming_response.create(**kwargs) as resp:
        resp.stream_to_file(out)


def clean(raw: Path, out: Path):
    """48 kHz mono 16-bit, with leading/trailing silence trimmed to a short, even margin."""
    flt = ("silenceremove=start_periods=1:start_threshold=-48dB:start_silence=0.04,"
           "areverse,silenceremove=start_periods=1:start_threshold=-48dB:start_silence=0.08,areverse,"
           "adelay=40:all=1,apad=pad_dur=0.06")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", flt, "-ar", "48000", "-ac", "1",
         "-sample_fmt", "s16", str(out)])


def align(client, wav: Path, spoken: str) -> list[dict] | None:
    """Word start/end times for every word token of `spoken`, via whisper-1."""
    with open(wav, "rb") as f:
        tr = client.audio.transcriptions.create(model="whisper-1", file=f, response_format="verbose_json",
                                                timestamp_granularities=["word"], language="en")
    heard = [(w.word, float(w.start), float(w.end)) for w in (tr.words or [])]
    ours = WORD_RE.findall(spoken)
    if not heard or not ours:
        return None
    norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
    a = [norm(w) for w in ours]
    b = [norm(w) for w, _, _ in heard]
    times: list[tuple[float, float] | None] = [None] * len(ours)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            _, s, e = heard[blk.b + k]
            times[blk.a + k] = (s, e)
    # Interpolate words whisper spelled differently (numbers, hyphenated names, ...).
    known = [i for i, t in enumerate(times) if t]
    if not known:
        return None
    total = heard[-1][2]
    for i, t in enumerate(times):
        if t:
            continue
        prev = max([k for k in known if k < i], default=None)
        nxt = min([k for k in known if k > i], default=None)
        t0 = times[prev][1] if prev is not None else 0.0
        t1 = times[nxt][0] if nxt is not None else total
        lo = prev if prev is not None else -1
        hi = nxt if nxt is not None else len(ours)
        frac0 = (i - lo - 1 + 0.0) / max(1, hi - lo - 1)
        frac1 = (i - lo) / max(1, hi - lo - 1)
        times[i] = (t0 + (t1 - t0) * frac0, t0 + (t1 - t0) * frac1)
    return [{"w": w, "start": round(s, 3), "end": round(e, 3)} for w, (s, e) in zip(ours, times)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=os.environ.get("TTS_MODEL", DEFAULT_MODEL))
    ap.add_argument("--voice", default=os.environ.get("TTS_VOICE", DEFAULT_VOICE))
    ap.add_argument("--speed", type=float, default=float(os.environ.get("TTS_SPEED", "1.0")))
    ap.add_argument("--instructions-file", type=Path)
    ap.add_argument("--only", default="", help="comma-separated segment ids")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-align", action="store_true", help="skip whisper word alignment")
    ap.add_argument("--jobs", type=int, default=4)
    args = ap.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY is not set")
    from openai import OpenAI
    client = OpenAI(max_retries=5, timeout=180)

    instructions = args.instructions_file.read_text() if args.instructions_file else INSTRUCTIONS
    segs = load_segments()
    only = {s for s in args.only.split(",") if s}
    timings = json.loads(TIMINGS.read_text()) if TIMINGS.exists() else {}
    (AUDIO_DIR / "raw").mkdir(parents=True, exist_ok=True)

    def work(seg):
        h = clip_hash(seg.spoken, args.model, args.voice, instructions, args.speed)
        wav = AUDIO_DIR / f"{seg.id}.wav"
        old = timings.get(seg.id)
        if not args.force and old and old.get("hash") == h and wav.exists() and (old.get("words") or args.no_align):
            return seg.id, old, "cached"
        raw = AUDIO_DIR / "raw" / f"{seg.id}.wav"
        for attempt in range(4):
            try:
                synthesize(client, seg.spoken, raw, args.model, args.voice, instructions, args.speed)
                break
            except Exception as exc:  # network hiccups, rate limits
                if attempt == 3:
                    raise
                print(f"  {seg.id}: retry after {exc!r}", flush=True)
                time.sleep(2 ** (attempt + 1))
        clean(raw, wav)
        entry = {"file": wav.name, "duration": round(duration_of(wav), 3), "hash": h,
                 "voice": args.voice, "model": args.model}
        if not args.no_align:
            try:
                words = align(client, wav, seg.spoken)
                if words:
                    entry["words"] = words
            except Exception as exc:
                print(f"  {seg.id}: alignment failed ({exc!r}); using proportional timing", flush=True)
        return seg.id, entry, "new"

    todo = [s for s in segs.values() if not only or s.id in only]
    print(f"voice={args.voice} model={args.model}: {len(todo)} segments")
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        for sid, entry, status in ex.map(work, todo):
            timings[sid] = entry
            print(f"  {sid:4} {entry['duration']:6.2f}s  {status}", flush=True)
            TIMINGS.write_text(json.dumps(timings, indent=1))
    total = sum(timings[s.id]["duration"] for s in segs.values() if s.id in timings)
    print(f"done: {len(timings)} clips, {total / 60:.1f} min of narration -> {TIMINGS}")


if __name__ == "__main__":
    main()

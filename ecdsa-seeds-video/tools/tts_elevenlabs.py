"""Generate the voiceover with ElevenLabs, one clip per script segment.

Uses the text-to-speech "with-timestamps" endpoint, which returns character-level
alignment with the audio, so every word's timing is exact and no transcription pass is
needed. Writes audio/<id>.wav (48 kHz mono, trimmed to the speech) and audio/timings.json.

    ELEVENLABS_API_KEY=... python tools/tts_elevenlabs.py [--voice George] [--model eleven_multilingual_v2]

Clips whose text, voice, model and settings are unchanged are reused. If no key variable is
set, requests go out without one, which works when the environment injects the key for
api.elevenlabs.io as a network secret.
"""
from __future__ import annotations

import argparse
import base64
import concurrent.futures as cf
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from narration import AUDIO_DIR, TIMINGS, load_segments  # noqa: E402

API = "https://api.elevenlabs.io/v1"
KEY_VARS = ("ELEVENLABS_API_KEY", "XI_API_KEY", "ELEVEN_API_KEY")
DEFAULT_MODEL = "eleven_multilingual_v2"
PREFERRED_VOICES = ("George", "Brian", "Daniel", "Adam")  # warm, documentary-style narrators
SETTINGS = {"stability": 0.45, "similarity_boost": 0.8, "style": 0.15, "use_speaker_boost": True, "speed": 1.0}
HIGH_TIERS = {"pro", "growing_business", "scale", "business", "enterprise"}
WORD_RE = re.compile(r"[\w'’]+")


class APIError(Exception):
    def __init__(self, code: int, body: str):
        super().__init__(f"HTTP {code}: {body[:300]}")
        self.code, self.body = code, body


def api_key() -> str | None:
    return next((os.environ[v] for v in KEY_VARS if os.environ.get(v)), None)


def call(method: str, path: str, body: dict | None = None, query: str = "", timeout: float = 240):
    headers = {"Accept": "application/json", "User-Agent": "its-just-timestamps-video/1.0"}
    if api_key():
        headers["xi-api-key"] = api_key()
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    url = f"{API}{path}" + (f"?{query}" if query else "")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise APIError(e.code, e.read().decode(errors="replace")) from None


def call_retrying(*args, attempts: int = 7, **kw):
    for i in range(attempts):
        try:
            return call(*args, **kw)
        except APIError as e:
            busy = e.code == 429 or e.code >= 500
            if not busy or i == attempts - 1:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if i == attempts - 1:
                raise
            print(f"    network error {e!r}, retrying", flush=True)
        time.sleep(min(60, 2 ** (i + 1)))


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def duration_of(path: Path) -> float:
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]))


def pick_voice(wanted: str | None) -> tuple[str, str]:
    voices = call_retrying("GET", "/voices")["voices"]
    if wanted:
        for v in voices:
            if wanted in (v["voice_id"],) or v["name"].lower() == wanted.lower() \
                    or v["name"].lower().startswith(wanted.lower() + " "):
                return v["voice_id"], v["name"]
        if re.fullmatch(r"[A-Za-z0-9]{20}", wanted):  # a voice id not in the account's list (e.g. library)
            return wanted, wanted
        sys.exit(f"voice {wanted!r} not found; available: {', '.join(v['name'] for v in voices)}")
    for name in PREFERRED_VOICES:
        for v in voices:
            if v["name"].lower() == name.lower() or v["name"].lower().startswith(name.lower() + " "):
                return v["voice_id"], v["name"]
    return voices[0]["voice_id"], voices[0]["name"]


def char_times(text: str, alignment: dict) -> tuple[list[float], list[float]]:
    """Start/end time of every character of `text`, mapped from the API's alignment."""
    chars = alignment["characters"]
    cs, ce = alignment["character_start_times_seconds"], alignment["character_end_times_seconds"]
    got = "".join(chars)
    if got == text:
        return list(cs), list(ce)
    starts: list[float | None] = [None] * len(text)
    ends: list[float | None] = [None] * len(text)
    for blk in difflib.SequenceMatcher(None, text, got, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            starts[blk.a + k], ends[blk.a + k] = cs[blk.b + k], ce[blk.b + k]
    last = 0.0
    for i in range(len(text)):  # fill gaps from the nearest timed neighbour
        if starts[i] is None:
            nxt = next((starts[j] for j in range(i + 1, len(text)) if starts[j] is not None), last)
            starts[i], ends[i] = last, nxt
        last = ends[i]
    return starts, ends  # type: ignore[return-value]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--voice", default=os.environ.get("TTS_VOICE"), help="voice name or id (default: George)")
    ap.add_argument("--model", default=os.environ.get("TTS_MODEL", DEFAULT_MODEL))
    ap.add_argument("--speed", type=float, default=float(os.environ.get("TTS_SPEED", "1.0")))
    ap.add_argument("--only", default="", help="comma-separated segment ids")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--ignore-quota", action="store_true")
    args = ap.parse_args()

    if not api_key():
        print(f"no {KEY_VARS[0]} in the environment; relying on a network secret for api.elevenlabs.io")
    try:
        sub = call_retrying("GET", "/user/subscription")
    except APIError as e:
        sys.exit(f"ElevenLabs rejected the request ({e}). Check the API key and that api.elevenlabs.io is allowed.")
    except urllib.error.URLError as e:
        sys.exit(f"cannot reach api.elevenlabs.io ({e.reason}); add it to the environment's allowed domains")
    voice_id, voice_name = pick_voice(args.voice)
    settings = dict(SETTINGS, speed=args.speed)
    tier = str(sub.get("tier", "")).lower()
    formats = ["pcm_44100"] if tier in HIGH_TIERS else []
    formats += ["pcm_24000", "mp3_44100_128"]
    fmt_lock = threading.Lock()

    segs = load_segments()
    order = list(segs.values())
    only = {s for s in args.only.split(",") if s}
    timings = json.loads(TIMINGS.read_text()) if TIMINGS.exists() else {}
    (AUDIO_DIR / "raw").mkdir(parents=True, exist_ok=True)

    def h_of(seg) -> str:
        key = json.dumps(["elevenlabs", args.model, voice_id, settings, seg.spoken], sort_keys=True)
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    todo = [s for s in order if (not only or s.id in only)]
    fresh = [s for s in todo if args.force or timings.get(s.id, {}).get("hash") != h_of(s)
             or not (AUDIO_DIR / f"{s.id}.wav").exists()]
    fresh_ids = {s.id for s in fresh}
    need = sum(len(s.spoken) for s in fresh)
    left = int(sub.get("character_limit", 0)) - int(sub.get("character_count", 0))
    print(f"voice={voice_name} ({voice_id}) model={args.model} tier={tier or '?'}: "
          f"{len(fresh)}/{len(todo)} clips to synthesize, {need:,} characters, {left:,} left this period")
    if need > left and not args.ignore_quota:
        sys.exit("not enough ElevenLabs characters left for this run (use --only to do part of it, "
                 "or --ignore-quota to try anyway)")

    def work(seg):
        h = h_of(seg)
        wav = AUDIO_DIR / f"{seg.id}.wav"
        if seg.id not in fresh_ids:
            return seg.id, timings[seg.id], "cached"
        i = order.index(seg)
        body = {"text": seg.spoken, "model_id": args.model, "voice_settings": settings,
                "previous_text": order[i - 1].spoken if i > 0 else None,
                "next_text": order[i + 1].spoken if i + 1 < len(order) else None}
        while True:
            fmt = formats[0]
            try:
                resp = call_retrying("POST", f"/text-to-speech/{voice_id}/with-timestamps", body,
                                     query=f"output_format={fmt}")
                break
            except APIError as e:
                if e.code in (400, 401, 403, 422) and "output_format" in e.body and len(formats) > 1:
                    with fmt_lock:
                        if formats[0] == fmt:
                            formats.pop(0)
                            print(f"    {fmt} not available on this plan; using {formats[0]}", flush=True)
                    continue
                raise
        audio = base64.b64decode(resp["audio_base64"])
        raw = AUDIO_DIR / "raw" / f"{seg.id}.{'pcm' if fmt.startswith('pcm') else 'mp3'}"
        raw.write_bytes(audio)
        starts, ends = char_times(seg.spoken, resp.get("alignment") or resp["normalized_alignment"])
        spoken_idx = [k for k, ch in enumerate(seg.spoken) if not ch.isspace()]
        src = ["-f", "s16le", "-ar", fmt.split("_")[1], "-ac", "1", "-i", str(raw)] if fmt.startswith("pcm") \
            else ["-i", str(raw)]
        raw_dur = len(audio) / 2 / int(fmt.split("_")[1]) if fmt.startswith("pcm") else duration_of(raw)
        t0 = max(0.0, starts[spoken_idx[0]] - 0.06)
        t1 = min(raw_dur, ends[spoken_idx[-1]] + 0.18)
        run(["ffmpeg", "-v", "error", "-y", *src, "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}",
             "-af", "afade=t=in:d=0.012,areverse,afade=t=in:d=0.04,areverse",
             "-ar", "48000", "-ac", "1", "-sample_fmt", "s16", str(wav)])
        words = [{"w": m.group(0), "start": round(max(0.0, starts[m.start()] - t0), 3),
                  "end": round(max(0.0, ends[m.end() - 1] - t0), 3)} for m in WORD_RE.finditer(seg.spoken)]
        entry = {"file": wav.name, "duration": round(duration_of(wav), 3), "hash": h, "engine": "elevenlabs",
                 "voice": voice_name, "voice_id": voice_id, "model": args.model, "format": fmt, "words": words}
        return seg.id, entry, "new"

    with cf.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as ex:
        for sid, entry, status in ex.map(work, todo):
            timings[sid] = entry
            print(f"  {sid:4} {entry['duration']:6.2f}s  {status}", flush=True)
            TIMINGS.write_text(json.dumps(timings, indent=1))
    total = sum(timings[s.id]["duration"] for s in order if s.id in timings)
    print(f"done: {len(timings)} clips, {total / 60:.1f} min of narration -> {TIMINGS}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Narration: voice config/narration.json, then lay the voice under the rendered scenes.

  python3 scripts/narrate.py synth                   # voice every line (cached), OpenRouter
  python3 scripts/narrate.py synth --key bit2_printer.3 --force
  python3 scripts/narrate.py track                   # after rendering: VO WAVs + subtitle cues
  python3 scripts/narrate.py synth --backend coqui   # offline placeholder; run with ../youtube/venv/bin/python

synth — one audio file per line in media/audio/lines/<key>.wav, and media/audio/lines/
        index.json with each line's spoken length. Scenes read those lengths at render time
        (kit.NarratedScene), so render AFTER synth.
        OpenRouter backend: /audio/speech with google/gemini-3.1-flash-tts-preview, voice
        Iapetus (ZDR-eligible — the account enforces Zero Data Retention). Every take is
        transcribed back with Whisper and retried when the words differ from the script.
        Key: OPENROUTER_API_KEY from the environment or this repo's .env.

track — for every segment, read the render's timing log (media/timing/<Scene>.json, written
        by NarratedScene), place each line where the scene started it, and write
        media/audio/<id>-vo-ai.wav (44.1 kHz mono, -16 LUFS, exactly the render's length).
        Also writes config/cues_en_vo.json: subtitles cut from the voiced lines.

Then: python3 scripts/mux_audio.py && python3 scripts/build_srt_cut.py --cues config/cues_en_vo.json --burn
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
NARRATION = REPO_ROOT / "config" / "narration.json"
SCENES = REPO_ROOT / "config" / "scenes_manifest.json"
AUDIO_MANIFEST = REPO_ROOT / "config" / "audio_manifest.json"
CUES_VO = REPO_ROOT / "config" / "cues_en_vo.json"
NARRATION_AR = REPO_ROOT / "config" / "narration_ar.json"
AR_INDEX = REPO_ROOT / "media" / "audio" / "lines_ar" / "clean" / "index.json"
VO_LANG = os.environ.get("VO_LANG", "ar")   # which narration `track` lays down (see our_scenes/kit.py)
LINES_DIR = REPO_ROOT / "media" / "audio" / "lines"
INDEX = LINES_DIR / "index.json"
TIMING_DIR = REPO_ROOT / "media" / "timing"
AUDIO_DIR = REPO_ROOT / "media" / "audio"

OUT_RATE = 44100
SUB_MAX_CHARS = 84   # longer lines are split into two subtitles at a clause boundary
SUB_HOLD = 0.6       # a subtitle lingers this long after its words (never into the next one)
PAUSE_TOL = 0.3      # how far a line's actual silence may miss its planned pause

OPENROUTER = "https://openrouter.ai/api/v1"
# Chosen by ear from five ZDR-eligible voices (the account enforces Zero Data Retention).
DEFAULT_MODEL = "google/gemini-3.1-flash-tts-preview"
DEFAULT_VOICE = "Iapetus"
PCM_RATE = 24000                      # /audio/speech pcm = 16-bit mono at 24 kHz
STT_MODEL = "openai/whisper-large-v3"  # verifies every take (also ZDR-eligible)


# ----------------------------------------------------------------------------- utilities
def working_binary(name: str) -> str:
    """First ffmpeg/ffprobe that launches (a Homebrew upgrade can leave one of them broken)."""
    cands = [c for c in (shutil.which(name), f"/opt/homebrew/opt/ffmpeg-full/bin/{name}",
                         f"/opt/homebrew/bin/{name}", f"/usr/local/bin/{name}") if c]
    for c in cands:
        try:
            subprocess.run([c, "-version"], capture_output=True, check=True)
            return c
        except (OSError, subprocess.CalledProcessError):
            continue
    sys.exit(f"No working {name} found (tried {', '.join(cands)})")


FFMPEG = working_binary("ffmpeg")
FFPROBE = working_binary("ffprobe")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, doc: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def duration(path: Path) -> float:
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def words(text: str) -> list[str]:
    """Words as heard: apostrophes and quote marks are silent, so they are dropped
    ("ChatGPT's" and a transcribed "chat GPTs" compare equal)."""
    text = re.sub(r"['’‘\"“”-]", "", text.lower())
    text = re.sub(r"\bchat\s*g\.?\s*p\.?\s*t\.?", "chatgpt", text)
    text = re.sub(r"\bopen\s*a\.?\s*i\.?\b", "openai", text)
    return re.findall(r"[a-z0-9]+", text)


def word_diff(a: str, b: str) -> float:
    """Fraction of script words the take got wrong (edit distance over words)."""
    x, y = words(a), words(b)
    prev = list(range(len(y) + 1))
    for i in range(1, len(x) + 1):
        cur = [i] + [0] * len(y)
        for j in range(1, len(y) + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x[i - 1] != y[j - 1]))
        prev = cur
    return prev[-1] / max(1, len(x))


def trim_and_save(raw_wav: Path, out: Path) -> float:
    """Trim leading/trailing silence (keep 60 ms), save 44.1 kHz mono s16. Returns seconds."""
    af = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,"
          "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,areverse")
    tmp = out.with_suffix(".tmp.wav")
    subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw_wav),
                    "-af", af, "-ac", "1", "-ar", str(OUT_RATE), "-c:a", "pcm_s16le", str(tmp)],
                   check=True)
    tmp.replace(out)
    return duration(out)


def narration_lines() -> list[dict]:
    return [ln for seg in load(NARRATION)["segments"] for ln in seg["lines"]]


# ----------------------------------------------------------------------------- backends
def openrouter_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    env = REPO_ROOT / ".env"
    if not key and env.is_file():
        for raw in env.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*(?:export\s+)?OPENROUTER_API_KEY\s*=\s*(.*)$", raw)
            if m:
                key = m.group(1).strip().strip("'\"")
    if not key:
        sys.exit("No OPENROUTER_API_KEY: add a line OPENROUTER_API_KEY=... to "
                 f"{env} (gitignored) or export it.")
    return key


def _pcm16_to_wav(pcm: bytes, rate: int, path: Path) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)


def _post(path: str, body: dict, key: str, timeout: int = 180) -> bytes:
    req = urllib.request.Request(
        f"{OPENROUTER}/{path}", data=json.dumps(body).encode(), method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "HTTP-Referer": "https://github.com/ali-salloum6/ai-image-explainer",
                 "X-Title": "ai-image-explainer narration"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        raise RuntimeError(f"OpenRouter HTTP {e.code} on /{path}: {detail}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"OpenRouter unreachable on /{path}: {e.reason}") from None


def openrouter_take(text: str, model: str, voice: str, key: str, raw_out: Path) -> None:
    """One take of `text` from /audio/speech, written to raw_out as WAV."""
    pcm = _post("audio/speech", {"model": model, "input": text, "voice": voice,
                                 "response_format": "pcm"}, key)
    if len(pcm) < PCM_RATE // 5:
        raise RuntimeError(f"OpenRouter returned almost no audio ({len(pcm)} bytes)")
    _pcm16_to_wav(pcm, PCM_RATE, raw_out)


def openrouter_transcribe(wav: Path, key: str) -> str:
    """What was actually said in `wav`, via Whisper — used to check each take word for word."""
    out = _post("audio/transcriptions", {
        "model": STT_MODEL, "language": "en",
        "input_audio": {"data": base64.b64encode(wav.read_bytes()).decode(), "format": "wav"}}, key)
    return json.loads(out).get("text", "").strip()


def _import_coqui():
    """Coqui's TTS class, working around a broken pandas in the youtube venv (numpy 2.x next
    to a pandas built for numpy 1.x). Coqui needs pandas only for dataset tooling, never for
    inference, so a stub for this process is enough; the venv itself is not modified."""
    try:
        import pandas  # noqa: F401
    except Exception:
        import types

        for name in [m for m in sys.modules if m == "pandas" or m.startswith("pandas.")]:
            del sys.modules[name]

        class _Stub(types.ModuleType):
            def __getattr__(self, name):
                if name.startswith("__"):
                    raise AttributeError(name)
                return type(name, (), {})

        sys.modules["pandas"] = _Stub("pandas")
    from TTS.api import TTS
    return TTS


# Coqui's phonemizer mispronounces these; spoken form only (subtitles keep the script).
_COQUI_SAY = [
    (r"\bOpenAI\b", "Open A.I."), (r"\bChatGPT\b", "Chat G.P.T."), (r"\bFLUX\b", "Flux"),
    (r"\bMidjourney\b", "Mid-journey"), (r"DALL·E|DALL-E", "Dolly"), (r"\s*—\s*", ", "),
    (r"[\"”’']\s+(?=[a-z])", ", "), (r"[\"“”‘’]", ""), (r"(?<![A-Za-z.])'|'(?![A-Za-z])", ""),
]


class CoquiVoice:
    """Offline placeholder (Coqui VITS, LJSpeech). Run synth with ../youtube/venv/bin/python."""

    def __init__(self):
        self._tts = _import_coqui()("tts_models/en/ljspeech/vits", progress_bar=False)

    def take(self, text: str, raw_out: Path) -> str:
        said = text
        for pat, rep in _COQUI_SAY:
            said = re.sub(pat, rep, said)
        said = re.sub(r"\s+", " ", said).strip(" ,")
        self._tts.tts_to_file(text=said if said.endswith((".", "?", "!")) else said + ".",
                              file_path=str(raw_out))
        return text  # no transcript available offline


# ----------------------------------------------------------------------------- synth
def cmd_synth(args) -> None:
    lines = narration_lines()
    if args.keys:
        unknown = set(args.keys) - {ln["key"] for ln in lines}
        if unknown:
            sys.exit(f"Unknown key(s): {', '.join(sorted(unknown))}")
        lines = [ln for ln in lines if ln["key"] in args.keys]
    LINES_DIR.mkdir(parents=True, exist_ok=True)
    index = load(INDEX) if INDEX.is_file() else {"lines": {}}
    voice_id = f"coqui:vits" if args.backend == "coqui" else f"{args.model}:{args.voice}"

    todo = [ln for ln in lines if args.force or not (
        (e := index["lines"].get(ln["key"])) and e.get("text") == ln["text"]
        and e.get("voice") == voice_id and (REPO_ROOT / e["file"]).is_file())]
    print(f"{len(lines)} lines, {len(lines) - len(todo)} already voiced with {voice_id}, "
          f"{len(todo)} to voice")
    if not todo:
        return

    key = openrouter_key() if args.backend == "openrouter" else None
    coqui = CoquiVoice() if args.backend == "coqui" else None
    failures = []
    for n, ln in enumerate(todo, 1):
        out = LINES_DIR / f"{ln['key']}.wav"
        best = None
        for attempt in range(1, args.retries + 2):
            with tempfile.TemporaryDirectory() as td:
                raw = Path(td) / "raw.wav"
                cand = Path(td) / "cand.wav"
                try:
                    if coqui:
                        transcript = coqui.take(ln["text"], raw)
                        dur = trim_and_save(raw, cand)
                    else:
                        openrouter_take(ln["text"], args.model, args.voice, key, raw)
                        dur = trim_and_save(raw, cand)
                        transcript = openrouter_transcribe(cand, key)
                except RuntimeError as e:
                    print(f"  [{n}/{len(todo)}] {ln['key']} attempt {attempt}: {e}")
                    time.sleep(2 * attempt)
                    continue
                err = word_diff(ln["text"], transcript)
                if best is None or err < best[0]:
                    keep = LINES_DIR / f".{ln['key']}.cand.wav"
                    shutil.copyfile(cand, keep)
                    best = (err, transcript, dur, keep)
                if err <= args.max_word_error:
                    break
                print(f"  [{n}/{len(todo)}] {ln['key']} attempt {attempt}: words differ "
                      f"({err:.0%}) — heard: {transcript!r}")
        if best is None:
            failures.append(f"{ln['key']}: no audio")
            continue
        err, transcript, dur, cand = best
        cand.replace(out)
        index["lines"][ln["key"]] = {
            "file": str(out.relative_to(REPO_ROOT)), "duration": round(dur, 3),
            "text": ln["text"], "voice": voice_id, "transcript": transcript,
            "word_error": round(err, 3)}
        write_json(INDEX, index)
        flag = "" if err <= args.max_word_error else f"   ⚠ words differ {err:.0%}"
        print(f"  [{n}/{len(todo)}] {ln['key']:18s} {dur:5.2f}s{flag}")
        if err > args.max_word_error:
            failures.append(f"{ln['key']}: best take still {err:.0%} off — heard {transcript!r}")

    total = sum(e["duration"] for e in index["lines"].values())
    print(f"\nindex: {len(index['lines'])} lines, {total:.1f}s of speech → {INDEX.relative_to(REPO_ROOT)}")
    if failures:
        print("\nNeeds a listen:")
        for f in failures:
            print("  " + f)


# ----------------------------------------------------------------------------- track
def split_subtitle(text: str) -> list[str]:
    """Split a long line into two readable subtitles at the clause boundary nearest the middle."""
    if len(text) <= SUB_MAX_CHARS:
        return [text]
    cuts = [m.end() for m in re.finditer(r"[.?!:;؟](?=\s)|[,،](?=\s)|\s—(?=\s)", text)]
    if not cuts:
        return [text]
    mid = len(text) / 2
    cut = min(cuts, key=lambda c: abs(c - mid))
    a, b = text[:cut].strip(), text[cut:].strip().lstrip("— ").strip()
    return [a, b] if a and b else [text]


def cmd_track(args) -> None:
    order = [s["id"] for s in load(SCENES)["segments"]]
    scene_cls = {s["id"]: s["scene"].split(":", 1)[1] for s in load(SCENES)["segments"]}
    videos = {s["id"]: REPO_ROOT / s["video"] for s in load(AUDIO_MANIFEST)["segments"]}
    lang = args.lang
    idx_path = AR_INDEX if lang == "ar" else INDEX
    index = load(idx_path)["lines"] if idx_path.is_file() else {}
    if lang == "ar":
        text_of = {ln["key"]: ln["ar"] for seg in load(NARRATION_AR)["segments"] for ln in seg["lines"]
                   if ln.get("status") == "ready"}
    else:
        text_of = {ln["key"]: ln["text"] for ln in narration_lines()}
    suffix = "vo-ar" if lang == "ar" else "vo-ai"
    cues_out = REPO_ROOT / "config" / f"cues_{lang}_vo.json"
    pause_of = {ln["key"]: float(ln.get("pause", 0.4)) for ln in narration_lines()}
    pause_off = []
    cues_doc = {"notes": "Subtitles cut from the voiced narration (scripts/narrate.py track).",
                "segments": []}
    problems = []
    print(f"{'segment':14s} {'render':>7s} {'lines':>5s} {'speech':>7s}  status")
    for sid in order:
        if args.segments and sid not in args.segments:
            continue
        video, log_path = videos[sid], TIMING_DIR / f"{scene_cls[sid]}.json"
        if not video.is_file() or not log_path.is_file():
            problems.append(f"{sid}: missing render or timing log — render the scene first")
            continue
        log = load(log_path)
        seg_dur = duration(video)
        if abs(seg_dur - log["duration"]) > 0.25:
            problems.append(f"{sid}: timing log ({log['duration']:.2f}s) does not match the render "
                            f"({seg_dur:.2f}s) — re-render so they come from the same run")
        inputs, filters, cues, speech, status = [], [], [], 0.0, "ok"
        for i, ln in enumerate(log["lines"]):
            e = index.get(ln["key"])
            if not e or e.get("text") != text_of.get(ln["key"]):
                status = "UNVOICED/STALE"
                problems.append(f"{sid}: {ln['key']} not voiced for its current text — run synth, re-render")
                continue
            if abs(e["duration"] - ln["duration"]) > 0.05:
                status = "STALE RENDER"
                problems.append(f"{sid}: {ln['key']} was rendered for a {ln['duration']:.2f}s line but "
                                f"the voice is {e['duration']:.2f}s — re-render {scene_cls[sid]}")
            nxt_start = log["lines"][i + 1]["start"] if i + 1 < len(log["lines"]) else seg_dur
            gap = nxt_start - (ln["start"] + e["duration"])
            if abs(gap - pause_of[ln["key"]]) > PAUSE_TOL:
                pause_off.append(f"{ln['key']:18s} planned {pause_of[ln['key']]:.1f}s, got {gap:.1f}s")
            inputs += ["-i", str(REPO_ROOT / e["file"])]
            ms = max(0, int(round(ln["start"] * 1000)))
            filters.append(f"[{len(inputs) // 2 - 1}:a]adelay={ms}|{ms}[l{i}]")
            speech += e["duration"]
            parts = split_subtitle(text_of[ln["key"]])
            span = e["duration"]
            total_chars = sum(len(p) for p in parts)
            phrases = e.get("phrases") or []          # voiced stretches of a recorded take
            voiced = [b - a for a, b in phrases]

            def part_start(chars_before: int) -> float:
                """Seconds into the line where the part starts: by its share of the letters,
                snapped to the start of the take's nearest phrase when there are pauses."""
                frac = chars_before / total_chars
                if len(phrases) < 2:
                    return span * frac
                return min((abs(sum(voiced[:j]) / sum(voiced) - frac), phrases[j][0])
                           for j in range(1, len(phrases)))[1]

            starts, done = [], 0
            for p in parts:
                starts.append(0.0 if not starts else part_start(done))
                done += len(p)
            for j, p in enumerate(parts):
                end = starts[j + 1] if j + 1 < len(parts) else span
                cues.append({"start": round(ln["start"] + starts[j], 2), "end": round(ln["start"] + end, 2), "text": p})
        for k, c in enumerate(cues):
            nxt = cues[k + 1]["start"] if k + 1 < len(cues) else seg_dur
            c["end"] = round(min(c["end"] + SUB_HOLD, nxt - 0.04, seg_dur - 0.04), 2)
        cues_doc["segments"].append({"id": sid, "duration_s": round(seg_dur, 2), "cues": cues})

        out = AUDIO_DIR / f"{sid}-{suffix}.wav"
        n = len(filters)
        mix = (";".join(filters) + ";" + "".join(f"[l{i}]" for i in range(n))
               + f"amix=inputs={n}:normalize=0:dropout_transition=0,") if n else ""
        src = [] if n else ["-f", "lavfi", "-i", f"anullsrc=r={OUT_RATE}:cl=mono"]
        chain = (f"{mix}apad,atrim=0:{seg_dur:.6f},"
                 f"loudnorm=I=-16:TP=-1.5:LRA=11,aresample={OUT_RATE}[out]") if n else \
                f"[0:a]atrim=0:{seg_dur:.6f}[out]"
        tmp = out.with_suffix(".tmp.wav")
        subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *inputs, *src,
                        "-filter_complex", chain, "-map", "[out]",
                        "-ac", "1", "-ar", str(OUT_RATE), "-c:a", "pcm_s16le", str(tmp)], check=True)
        tmp.replace(out)
        print(f"{sid:14s} {seg_dur:6.1f}s {len(log['lines']):5d} {speech:6.1f}s  {status}")

    write_json(cues_out, cues_doc)
    print(f"\nWrote media/audio/<id>-{suffix}.wav and {cues_out.relative_to(REPO_ROOT)}")
    if pause_off:
        print(f"\nPauses off plan by more than {PAUSE_TOL}s (narration.json `pause`):")
        for x in pause_off:
            print("  " + x)
    if problems:
        print("\nProblems:")
        for p in problems:
            print("  " + p)
        sys.exit(1)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("synth", help="voice the narration lines")
    s.add_argument("--backend", choices=["openrouter", "coqui"], default="openrouter")
    s.add_argument("--model", default=DEFAULT_MODEL)
    s.add_argument("--voice", default=DEFAULT_VOICE)
    s.add_argument("--key", action="append", dest="keys", metavar="KEY", help="only these line keys")
    s.add_argument("--force", action="store_true", help="re-voice even if cached")
    s.add_argument("--retries", type=int, default=2, help="extra takes when the words differ")
    s.add_argument("--max-word-error", type=float, default=0.0,
                   help="accepted fraction of words the transcript disagrees on (default 0: "
                        "verbatim; a Whisper slip also counts, so a flagged line may be fine)")
    t = sub.add_parser("track", help="lay the voice under the rendered scenes")
    t.add_argument("--segment", action="append", dest="segments", metavar="ID")
    t.add_argument("--lang", choices=["ar", "en"], default=VO_LANG,
                   help="narration to lay down: ar = Ali's recorded Arabic (default), en = AI English")
    args = p.parse_args()
    {"synth": cmd_synth, "track": cmd_track}[args.cmd](args)


if __name__ == "__main__":
    main()

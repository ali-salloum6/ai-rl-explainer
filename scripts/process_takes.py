#!/usr/bin/env python3
"""
Clean the chosen Arabic takes (scripts/record_server.py) into the narration the scenes are timed to.

When scripts/enhance_takes.py has run a take through Adobe Enhance Speech, the enhanced audio is
what gets used; the cuts are still measured on the raw take (same length, sample-aligned), so a
line keeps its length whether or not it has been enhanced, and Adobe's clean-up replaces step 4's
noise reduction.

For every line in config/narration_ar.json with status "ready", takes the chosen take from
media/audio/lines_ar/manifest.json and:
  1. finds the speech: 10 ms frames louder than the take's own noise floor + 14 dB, grouped into
     phrases; a burst shorter than 120 ms standing alone is a key press, not speech, and is dropped
  2. trims to just before the first word and just after the last (soft onsets and trailing
     consonants kept), so the Space presses at both ends are gone
  3. shortens any pause inside the line longer than 0.75 s to 0.5 s (hesitations, not phrasing)
  4. rumble cut (70 Hz high-pass), gentle noise reduction, 48 kHz mono, short fades, gentle
     compression and a peak limiter, and
     one loudness for every line (-20 LUFS; each segment is brought to -16 LUFS when mixed)

Writes media/audio/lines_ar/clean/<key>.wav and media/audio/lines_ar/clean/index.json, the same
shape as the English index (media/audio/lines/index.json), plus the phrase timings inside each
cleaned line, so animations can be anchored to Arabic words.

Run:  .venv/bin/python scripts/process_takes.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
LINES_AR = REPO_ROOT / "config" / "narration_ar.json"
TAKES = REPO_ROOT / "media" / "audio" / "lines_ar"
MANIFEST = TAKES / "manifest.json"
ENHANCED = TAKES / "enhanced"
INNER_PAUSES = REPO_ROOT / "config" / "inner_pauses_ar.json"   # hand-set pauses inside a line
CLEAN = TAKES / "clean"
INDEX = CLEAN / "index.json"

FRAME = 0.01            # analysis frame, s
ABOVE_FLOOR = 14.0      # dB over the take's noise floor that counts as voice
SOFT_ABOVE = 6.0        # dB over the floor for soft onsets / decays kept at the edges
MIN_SPEECH = 0.12       # a burst shorter than this, standing alone, is a click
JOIN_GAP = 0.25         # gaps shorter than this are inside a phrase
LONG_PAUSE, KEEP_PAUSE = 0.75, 0.50
LEAD, TAIL = 0.05, 0.08  # padding kept before the first / after the last voiced frame
OUT_RATE = 48000
TARGET_LUFS, PEAK_DB = -20.0, -3.0


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path)) as w:
        sr, n, ch, sw = w.getframerate(), w.getnframes(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(n)
    assert sw == 2, f"{path.name}: expected 16-bit PCM"
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    return (x.reshape(-1, ch).mean(axis=1) if ch > 1 else x), sr


def runs(mask: np.ndarray) -> list[tuple[int, int]]:
    out, i = [], 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j < len(mask) and mask[j]:
                j += 1
            out.append((i, j))
            i = j
        else:
            i += 1
    return out


def speech_phrases(x: np.ndarray, sr: int) -> tuple[list[tuple[float, float]], dict]:
    f = int(FRAME * sr)
    n = len(x) // f
    db = 20 * np.log10(np.sqrt((x[: n * f].reshape(n, f) ** 2).mean(axis=1)) + 1e-9)
    floor = float(np.percentile(db, 10))
    loud = runs(db > floor + ABOVE_FLOOR)
    # group bursts into phrases; a phrase needs MIN_SPEECH of voiced frames to be speech
    groups: list[list[tuple[int, int]]] = []
    for r in loud:
        if groups and (r[0] - groups[-1][-1][1]) * FRAME < JOIN_GAP:
            groups[-1].append(r)
        else:
            groups.append([r])
    phrases, clicks = [], []
    for g in groups:
        voiced = sum(b - a for a, b in g) * FRAME
        (phrases if voiced >= MIN_SPEECH else clicks).append((g[0][0], g[-1][1]))
    if not phrases:
        raise ValueError("no speech found")
    # widen the outer edges over soft onsets / decays, never back into a click
    soft = db > floor + SOFT_ABOVE
    a, b = phrases[0][0], phrases[-1][1]
    stop_a = max([c[1] for c in clicks if c[1] <= a] + [0]) + 2
    while a - 1 >= stop_a and soft[a - 1] and (phrases[0][0] - a) * FRAME < 0.12:
        a -= 1
    stop_b = min([c[0] for c in clicks if c[0] >= b] + [n]) - 2
    while b < stop_b and soft[b] and (b - phrases[-1][1]) * FRAME < 0.30:
        b += 1
    phrases[0], phrases[-1] = (a, phrases[0][1]), (phrases[-1][0], b)
    if len(phrases) == 1:
        phrases = [(a, b)]
    info = {"floor_db": round(floor, 1), "clicks": [round(c[0] * FRAME, 2) for c in clicks]}
    first = max(0.0, phrases[0][0] * FRAME - LEAD)
    first = max(first, (max([c[1] for c in clicks if c[1] <= phrases[0][0]] + [0]) + 2) * FRAME)
    last = min(n * FRAME, phrases[-1][1] * FRAME + TAIL)
    spans = [(p[0] * FRAME, p[1] * FRAME) for p in phrases]
    spans[0] = (first, spans[0][1])
    spans[-1] = (spans[-1][0], last)
    return spans, info


def edit(x: np.ndarray, sr: int, spans: list[tuple[float, float]],
         gap_target: dict[int, float] | None = None) -> tuple[np.ndarray, list, list]:
    """Keep speech from the first to the last phrase. A pause between phrases longer than
    LONG_PAUSE becomes KEEP_PAUSE; a pause listed in `gap_target` (index i = the pause after
    phrase i) becomes exactly that long, lengthened with silence if needed.
    Returns the audio, the phrase spans in output time, and the pauses that were changed."""
    gap_target = gap_target or {}
    xf = int(0.015 * sr)
    pieces, out_spans, changed, t_out = [], [], [], 0.0
    cur_a = spans[0][0]
    for i, (a, b) in enumerate(spans):
        out_spans.append((t_out + (a - cur_a), t_out + (b - cur_a)))
        if i + 1 == len(spans):
            break
        nxt_a = spans[i + 1][0]
        gap = nxt_a - b
        target = gap_target.get(i, KEEP_PAUSE if gap > LONG_PAUSE else None)
        if target is None or abs(target - gap) < 1e-3:
            continue
        if target < gap:                      # cut the middle of the pause
            end = b + target / 2
            pieces.append(x[int(cur_a * sr): int(end * sr)])
            t_out += end - cur_a
            cur_a = nxt_a - target / 2
        else:                                 # open it up with silence in the middle
            mid = b + gap / 2
            pieces.append(x[int(cur_a * sr): int(mid * sr)])
            t_out += mid - cur_a
            pad = np.zeros(int(round((target - gap) * sr)), dtype=np.float32)
            pieces.append(pad)
            t_out += len(pad) / sr
            cur_a = mid
        changed.append((round(b, 2), round(gap, 2), round(target, 2)))
    pieces.append(x[int(cur_a * sr): int(spans[-1][1] * sr)])
    # join with short crossfades so an edited pause never clicks
    y = pieces[0]
    for p in pieces[1:]:
        k = min(xf, len(y), len(p))
        ramp = np.linspace(0.0, 1.0, k, dtype=np.float32)
        y = np.concatenate([y[:-k], y[-k:] * (1 - ramp) + p[:k] * ramp, p[k:]])
    return y, out_spans, changed


def gap_before(text: str, word: str, spans: list[tuple[float, float]]) -> int:
    """Index of the pause (between phrases i and i+1) that comes right before `word`: the phrase
    boundary whose share of the voiced time is closest to the word's share of the letters."""
    i = text.find(word)
    if i < 0:
        raise ValueError(f"{word!r} not in {text!r}")
    letters = lambda s: len(re.sub(r"[\W_]", "", s))
    frac = letters(text[:i]) / max(1, letters(text))
    voiced = np.array([b - a for a, b in spans])
    cum = np.cumsum(voiced)[:-1] / voiced.sum()
    return int(np.argmin(np.abs(cum - frac)))


def ffmpeg(args: list[str]) -> str:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-y", *args], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-800:])
    return r.stderr


def _measure(path: Path) -> tuple[float, float]:
    """Integrated loudness (LUFS) and true peak (dBFS)."""
    meas = ffmpeg(["-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"])
    return (float(re.findall(r"I:\s+(-?[\d.]+) LUFS", meas)[-1]),
            float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", meas)[-1]))


def finish(y: np.ndarray, sr: int, floor_db: float, out: Path, denoise: bool = True) -> float:
    """Filter, resample, level to TARGET_LUFS, write out; returns the final length in seconds."""
    with tempfile.TemporaryDirectory() as td:
        raw, mid = Path(td) / "raw.wav", Path(td) / "mid.wav"
        with wave.open(str(raw), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
            w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
        nf = float(np.clip(floor_db, -80, -20))
        dur = len(y) / sr
        chain = (f"highpass=f=70,{f'afftdn=nr=10:nf={nf:.0f}:tn=1,' if denoise else ''}aresample={OUT_RATE},"
                 f"afade=t=in:d=0.015,afade=t=out:st={max(0.0, dur - 0.04):.3f}:d=0.04")
        ffmpeg(["-i", str(raw), "-af", chain, "-ac", "1", "-c:a", "pcm_s24le", str(mid)])
        # A voice's peaks (plosives) sit far above its loudness, so levelling by loudness alone
        # stops at the peak ceiling and the mix comes out quiet. Bring the line to the target,
        # then a gentle compressor (3:1 over the loud syllables) and a limiter tame the peaks.
        lufs = _measure(mid)[0]
        dyn = Path(td) / "dyn.wav"
        ffmpeg(["-i", str(mid), "-af",
                f"volume={TARGET_LUFS - lufs:.2f}dB,"
                "acompressor=threshold=0.16:ratio=3:attack=4:release=70:knee=3,"
                f"alimiter=limit={10 ** (PEAK_DB / 20):.3f}:attack=2:release=40:level=disabled",
                "-ac", "1", "-c:a", "pcm_s24le", str(dyn)])
        lufs, peak = _measure(dyn)
        gain = min(TARGET_LUFS - lufs, PEAK_DB - peak)
        ffmpeg(["-i", str(dyn), "-af", f"volume={gain:.2f}dB", "-ac", "1", "-ar", str(OUT_RATE),
                "-c:a", "pcm_s16le", str(out)])
    with wave.open(str(out)) as w:
        return w.getnframes() / w.getframerate()


def main() -> None:
    lines = [ln for seg in json.loads(LINES_AR.read_text(encoding="utf-8"))["segments"]
             for ln in seg["lines"] if ln["status"] == "ready"]
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))["lines"]
    inner = json.loads(INNER_PAUSES.read_text(encoding="utf-8"))["lines"] if INNER_PAUSES.is_file() else {}
    CLEAN.mkdir(parents=True, exist_ok=True)
    index = {"notes": "Arabic narration: the chosen take of each line, cleaned by scripts/process_takes.py. "
                      "'phrases' are the voiced stretches inside the cleaned line (s), for anchoring animations.",
             "lines": {}}
    problems = []
    print(f"{'line':16s} {'take':24s} {'raw':>6s} {'clean':>6s}  trimmed / edits")
    for ln in lines:
        key = ln["key"]
        rec = manifest.get(key)
        if not rec or not rec.get("chosen"):
            problems.append(f"{key}: no take recorded")
            continue
        chosen = next(t for t in rec["takes"] if t["file"] == rec["chosen"])
        if chosen["text"] != ln["ar"]:
            problems.append(f"{key}: the chosen take ({rec['chosen']}) says older wording; record the line again")
            continue
        x, sr = read_wav(TAKES / "takes" / rec["chosen"])
        spans, info = speech_phrases(x, sr)          # cuts are measured on the raw take
        enh = ENHANCED / rec["chosen"]
        if enh.is_file():
            xe, sre = read_wav(enh)
            if abs(len(xe) / sre - len(x) / sr) > 0.01:
                problems.append(f"{key}: enhanced take is {len(xe) / sre:.2f}s, raw {len(x) / sr:.2f}s; used raw")
                enh = None
            else:
                x, sr = xe, sre
        else:
            enh = None
        gap_target = {}
        rule = inner.get(key)
        if rule and len(spans) > 1:
            try:
                gap_target[gap_before(ln["ar"], rule["before"], spans)] = float(rule["seconds"])
            except ValueError as e:
                problems.append(f"{key}: inner pause not applied ({e})")
        y, phrases, shortened = edit(x, sr, spans, gap_target)
        out = CLEAN / f"{key}.wav"
        dur = finish(y, sr, info["floor_db"], out, denoise=enh is None)
        index["lines"][key] = {
            "file": str(out.relative_to(REPO_ROOT)), "duration": round(dur, 3), "text": ln["ar"],
            "take": rec["chosen"], "source": "adobe enhanced" if enh else "raw",
            "phrases": [[round(a, 2), round(b, 2)] for a, b in phrases],
            "trimmed": {"start": round(spans[0][0], 2), "end": round(len(x) / sr - spans[-1][1], 2)},
            "clicks_removed": info["clicks"], "pauses_shortened": shortened, "noise_floor_db": info["floor_db"]}
        edits = f"cut {spans[0][0]:.2f}s before, {len(x) / sr - spans[-1][1]:.2f}s after"
        if info["clicks"]:
            edits += f"; key press at {', '.join(f'{c:.2f}' for c in info['clicks'])}s"
        if shortened:
            edits += "; pause " + ", ".join(f"{g:.2f}s→{to:.2f}s at {t:.1f}s" for t, g, to in shortened)
        print(f"{key:16s} {rec['chosen']:24s} {len(x) / sr:5.2f}s {dur:5.2f}s  {'enh' if enh else 'raw'}  {edits}")
    tmp = INDEX.with_suffix(".tmp")
    tmp.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(INDEX)
    total = sum(v["duration"] for v in index["lines"].values())
    print(f"\n{len(index['lines'])} lines, {total:.1f}s of speech → {INDEX.relative_to(REPO_ROOT)}")
    if problems:
        print("\nProblems:\n  " + "\n  ".join(problems))
        sys.exit(1)


if __name__ == "__main__":
    main()

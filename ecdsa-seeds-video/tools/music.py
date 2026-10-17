"""Procedural ambient score and sound effects, so the video ships with no licensed audio.

The score is a slow, low, minor-key pad (i - VI - iv - v in D minor) with a sub-bass,
sparse bell tones and a long synthetic reverb. It is meant to sit far under the voice.
"""
from __future__ import annotations

import numpy as np

SR = 48000


def _note(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def _lowpass(x: np.ndarray, cutoff: float) -> np.ndarray:
    """One-pole low-pass, applied twice for a gentle 12 dB/oct slope."""
    from scipy.signal import lfilter
    a = np.exp(-2 * np.pi * cutoff / SR)
    for _ in range(2):
        x = lfilter([1 - a], [1, -a], x, axis=0)
    return x


def _highpass(x: np.ndarray, cutoff: float) -> np.ndarray:
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, cutoff, btype="high", fs=SR, output="sos"), x, axis=0)


def _reverb(x: np.ndarray, seconds: float = 3.2, wet: float = 0.35, seed: int = 11) -> np.ndarray:
    from scipy.signal import oaconvolve
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = np.zeros((n, 2))
    for ch in range(2):
        noise = rng.standard_normal(n)
        ir[:, ch] = noise * np.exp(-6.9 * t / seconds)  # -60 dB at `seconds`
    ir[: int(0.012 * SR)] = 0  # pre-delay
    ir = _lowpass(ir, 3500)
    ir /= np.sqrt((ir ** 2).sum(axis=0, keepdims=True))
    out = np.stack([oaconvolve(x[:, ch], ir[:, ch])[: len(x)] for ch in range(2)], axis=1)
    return (1 - wet) * x + wet * out


def _pad_voice(freq: float, n: int, rng) -> np.ndarray:
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    partials = [(1, 1.0), (2, 0.32), (3, 0.12), (4, 0.06)]
    for ch, detune in enumerate((-4.0, 4.0)):  # cents, a slow chorus between left and right
        f = freq * 2 ** (detune / 1200)
        lfo = 1 + 0.0015 * np.sin(2 * np.pi * (0.11 + 0.03 * ch) * t + rng.uniform(0, 6.28))
        phase = 2 * np.pi * f * np.cumsum(lfo) / SR
        for k, amp in partials:
            out[:, ch] += amp * np.sin(k * phase + rng.uniform(0, 6.28))
    return out


def ambient(duration: float, seed: int = 5) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(duration * SR) + SR
    out = np.zeros((n, 2))
    chord_len = 9.0
    # D minor: Dm(add9) - Bbmaj7 - Gm7 - A7sus4  (MIDI notes, low register)
    chords = [[62, 69, 74, 76, 77], [58, 65, 69, 74, 77], [55, 62, 67, 70, 74], [57, 64, 69, 71, 74]]
    roots = [50, 46, 43, 45]
    k = 0
    start = 0.0
    while start < duration + chord_len:
        notes = chords[k % 4]
        seg = int((chord_len + 4.0) * SR)  # overlap for crossfades
        t = np.arange(seg) / SR
        env = np.minimum(1, t / 3.0) * np.minimum(1, np.maximum(0, (chord_len + 4.0 - t) / 4.0))
        env = env ** 1.5
        block = np.zeros((seg, 2))
        for m in notes:
            block += 0.16 * _pad_voice(_note(m), seg, rng)
        sub = np.sin(2 * np.pi * _note(roots[k % 4]) * t)[:, None] * np.array([[0.16, 0.16]])
        block += sub
        block *= env[:, None]
        i0 = int(start * SR)
        if i0 >= n:
            break
        i1 = min(n, i0 + seg)
        out[i0:i1] += block[: i1 - i0]
        # sparse bell tones from the chord, high and quiet
        for b in range(3):
            bt = start + 1.5 + b * 3.0 + rng.uniform(-0.4, 0.4)
            if bt >= duration:
                continue
            m = notes[rng.integers(1, len(notes))] + 12
            bl = int(3.5 * SR)
            tb = np.arange(bl) / SR
            bell = (np.sin(2 * np.pi * _note(m) * tb) + 0.25 * np.sin(2 * np.pi * _note(m) * 2.01 * tb))
            bell *= np.exp(-tb / 1.1) * np.minimum(1, tb / 0.01) * 0.05
            pan = rng.uniform(0.3, 0.7)
            j0 = int(bt * SR)
            if j0 >= n:
                continue
            j1 = min(n, j0 + bl)
            out[j0:j1, 0] += bell[: j1 - j0] * (1 - pan)
            out[j0:j1, 1] += bell[: j1 - j0] * pan
        start += chord_len
        k += 1
    out = _lowpass(out, 2600)
    out = _highpass(out, 110)
    out = _reverb(out, 3.4, 0.4)
    out = out[: int(duration * SR)]
    fade_in, fade_out = int(3 * SR), int(5 * SR)
    out[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
    out[-fade_out:] *= np.linspace(1, 0, fade_out)[:, None] ** 2
    return out / (np.abs(out).max() + 1e-9) * 0.5


# ---------------------------------------------------------------- sound effects
def tick(high: bool = True) -> np.ndarray:
    """A soft clock tick: a short, band-limited click."""
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    f = 2600 if high else 2000
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.006) + 0.4 * np.sin(2 * np.pi * f * 1.5 * t) * np.exp(-t / 0.004)
    return np.stack([x, x], axis=1) * 0.5


def whoosh(seconds: float = 1.1, seed: int = 2) -> np.ndarray:
    """Airy noise swell for chapter cards."""
    from scipy.signal import butter, sosfilt
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    noise = rng.standard_normal((n, 2))
    sos = butter(2, [300, 2500], btype="band", fs=SR, output="sos")
    x = sosfilt(sos, noise, axis=0)
    t = np.linspace(0, 1, n)
    env = np.sin(np.pi * t) ** 2 * (0.35 + 0.65 * t)
    return x * env[:, None] / (np.abs(x).max() + 1e-9) * 0.5


def chime(midi: float = 81, seconds: float = 2.5) -> np.ndarray:
    n = int(seconds * SR)
    t = np.arange(n) / SR
    f = _note(midi)
    x = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2.0 * t) + 0.15 * np.sin(2 * np.pi * f * 3.01 * t))
    x *= np.exp(-t / 0.8) * np.minimum(1, t / 0.005)
    return np.stack([x, x], axis=1) * 0.35


def rewind(seconds: float = 2.5) -> np.ndarray:
    """Ticks that accelerate then slow down, for the generator rewinding."""
    n = int(seconds * SR)
    out = np.zeros((n, 2))
    t, k = 0.0, 0
    while t < seconds - 0.06:
        u = t / seconds
        gap = 0.16 - 0.13 * np.sin(np.pi * u)  # fast in the middle, slow at both ends
        c = tick(k % 2 == 0) * (0.5 + 0.5 * np.sin(np.pi * u))
        i = int(t * SR)
        out[i:i + len(c)] += c[: max(0, min(len(c), n - i))]
        t += gap
        k += 1
    return out


def ticks(seconds: float = 4.0) -> np.ndarray:
    """A clock: one soft tick per second, alternating tick and tock."""
    n = int(seconds * SR)
    out = np.zeros((n, 2))
    for k in range(int(seconds)):
        c = tick(k % 2 == 0)
        i = k * SR
        out[i:i + len(c)] += c[: max(0, min(len(c), n - i))]
    return out

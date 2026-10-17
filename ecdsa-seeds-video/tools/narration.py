"""Parse script.md into narration segments and compute their timing.

A segment's timing comes from its rendered voice clip when audio/timings.json
has it, and from a speaking-rate estimate otherwise, so the video can be built
(and re-built) before and after the voiceover exists.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "script.md"
AUDIO_DIR = Path(os.environ.get("VO_AUDIO_DIR", ROOT / "audio"))
TIMINGS = AUDIO_DIR / "timings.json"

SCENE_RE = re.compile(r"^##\s*Scene:\s*(\w+)\s*$")
SEG_RE = re.compile(r"^\[([A-Za-z0-9_]+)\]\s*(.*)$")
TOKEN_RE = re.compile(r"\[\[([^|\]]+)\|([^\]]+)\]\]|\{([A-Za-z0-9_]+)\}")

# Estimated delivery speed of the narrator, used until real audio exists.
CHARS_PER_SEC = 17.5
PAUSE_WEIGHT = {",": 3.0, ";": 5.0, ":": 5.0, ".": 7.0, "?": 7.0, "!": 7.0, "—": 4.0}

_ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen "
         "fourteen fifteen sixteen seventeen eighteen nineteen").split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def _words(n: int) -> str:
    """Rough English reading of an integer; only used to estimate durations."""
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("" if n % 10 == 0 else "-" + _ONES[n % 10])
    if n < 1000:
        rest = n % 100
        return _ONES[n // 100] + " hundred" + ("" if rest == 0 else " " + _words(rest))
    for div, name in ((10**9, "billion"), (10**6, "million"), (1000, "thousand")):
        if n >= div:
            rest = n % div
            return _words(n // div) + " " + name + ("" if rest == 0 else " " + _words(rest))
    return str(n)


def _expand_numbers(text: str) -> str:
    def year_or_number(m: re.Match) -> str:
        raw = m.group(0)
        n = int(raw.replace(",", ""))
        if "," not in raw and 1900 <= n <= 2099:
            return _words(n // 100) + " " + _words(n % 100)
        return _words(n)
    return re.sub(r"\d[\d,]*\d|\d", year_or_number, text)


def speech_weight(text: str) -> float:
    """Approximate 'speaking length' of text, in characters, with pauses."""
    spoken = _expand_numbers(text)
    w = float(len(spoken))
    for ch, extra in PAUSE_WEIGHT.items():
        w += spoken.count(ch) * extra
    return w


@dataclass
class Segment:
    id: str
    scene: str
    raw: str
    spoken: str = ""
    display: str = ""
    marks: dict = field(default_factory=dict)  # mark -> char offset in `spoken`

    def parse(self) -> "Segment":
        spoken, display = [], []
        pos = 0
        for m in TOKEN_RE.finditer(self.raw):
            plain = self.raw[pos:m.start()]
            spoken.append(plain)
            display.append(plain)
            if m.group(3):
                self.marks[m.group(3)] = len("".join(spoken))
            else:
                display.append(m.group(1))
                spoken.append(m.group(2))
            pos = m.end()
        spoken.append(self.raw[pos:])
        display.append(self.raw[pos:])
        self.spoken = re.sub(r"\s+", " ", "".join(spoken)).strip()
        self.display = re.sub(r"\s+", " ", "".join(display)).strip()
        # Marks were recorded against the unstripped text; clamp to the stripped one.
        lead = len("".join(spoken)) - len("".join(spoken).lstrip())
        self.marks = {k: max(0, min(len(self.spoken), v - lead)) for k, v in self.marks.items()}
        return self

    def units(self) -> list[tuple[str, str, bool]]:
        """(display, spoken, glued_to_previous) for every word-like unit of the segment."""
        res: list[tuple[str, str, bool]] = []
        space = True

        def plain(text):
            nonlocal space
            for piece in re.split(r"(\s+)", text):
                if not piece:
                    continue
                if piece.isspace():
                    space = True
                    continue
                res.append((piece, piece, not space and bool(res)))
                space = False

        pos = 0
        for m in TOKEN_RE.finditer(self.raw):
            plain(self.raw[pos:m.start()])
            if not m.group(3):
                res.append((m.group(1), m.group(2), not space and bool(res)))
                space = False
            pos = m.end()
        plain(self.raw[pos:])
        return res

    def word_index_at_unit(self, units, i) -> int:
        prefix = ""
        for d, s, glue in units[:i]:
            prefix += ("" if glue or not prefix else " ") + s
        return len(re.findall(r"[\w'’]+", prefix))

    def time_of_word(self, idx: int, edge: str = "start") -> float:
        """Clip time of spoken word `idx` (its start or end)."""
        t = self.timing()
        words = (t or {}).get("words")
        tokens = re.findall(r"[\w'’]+", self.spoken)
        idx = max(0, min(idx, len(tokens) - 1))
        if words and len(words) == len(tokens):
            return float(words[idx][edge])
        # proportional estimate from the speech weight of the text before/through the word
        spans = [m.span() for m in re.finditer(r"[\w'’]+", self.spoken)]
        cut = spans[idx][0] if edge == "start" else spans[idx][1]
        total = speech_weight(self.spoken)
        return self.duration * (speech_weight(self.spoken[:cut]) / total if total else 0.0)

    # ---- timing -------------------------------------------------------
    def timing(self) -> dict | None:
        return load_timings().get(self.id)

    @property
    def audio_path(self) -> Path | None:
        t = self.timing()
        if t and (AUDIO_DIR / t["file"]).exists():
            return AUDIO_DIR / t["file"]
        return None

    @property
    def duration(self) -> float:
        t = self.timing()
        if t:
            return float(t["duration"])
        return speech_weight(self.spoken) / CHARS_PER_SEC + 0.25

    def mark_time(self, name: str) -> float:
        """Seconds from the start of the clip to the word following `{name}`."""
        if name not in self.marks:
            raise KeyError(f"segment {self.id} has no mark {{{name}}}")
        offset = self.marks[name]
        t = self.timing()
        words = (t or {}).get("words")
        if words:
            # Index of the first spoken word at or after the mark.
            idx = len(re.findall(r"[\w'’]+", self.spoken[:offset]))
            if idx >= len(words):
                return float(t["duration"])
            prev_end = words[idx - 1]["end"] if idx > 0 else 0.0
            # A mark placed after punctuation lands in the pause: split the gap.
            return 0.5 * (prev_end + words[idx]["start"]) if idx > 0 else float(words[0]["start"])
        total = speech_weight(self.spoken)
        before = speech_weight(self.spoken[:offset])
        return self.duration * (before / total if total else 0.0)


_TIMINGS_CACHE: dict | None = None


def load_timings() -> dict:
    global _TIMINGS_CACHE
    if _TIMINGS_CACHE is None:
        _TIMINGS_CACHE = json.loads(TIMINGS.read_text()) if TIMINGS.exists() else {}
    return _TIMINGS_CACHE


def load_segments(path: Path = SCRIPT) -> dict[str, Segment]:
    segs: dict[str, Segment] = {}
    scene = None
    current: Segment | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if m := SCENE_RE.match(s):
            scene, current = m.group(1), None
            continue
        if scene is None or s.startswith("%"):
            continue
        if m := SEG_RE.match(s):
            current = Segment(m.group(1), scene, m.group(2))
            if current.id in segs:
                raise ValueError(f"duplicate segment id {current.id}")
            segs[current.id] = current
        elif s and current is not None and not s.startswith("#"):
            current.raw += " " + s
        elif not s:
            current = None
    return {k: v.parse() for k, v in segs.items()}


def scenes_in_order(segs: dict[str, Segment]) -> list[str]:
    order: list[str] = []
    for seg in segs.values():
        if seg.scene not in order:
            order.append(seg.scene)
    return order


if __name__ == "__main__":
    segs = load_segments()
    total = 0.0
    words = 0
    for name in scenes_in_order(segs):
        part = [s for s in segs.values() if s.scene == name]
        d = sum(s.duration for s in part)
        w = sum(len(s.spoken.split()) for s in part)
        total += d
        words += w
        print(f"{name:18} {len(part):3} segs {w:5} words  ~{d/60:5.2f} min")
    print(f"{'TOTAL':18} {len(segs):3} segs {words:5} words  ~{total/60:5.2f} min")

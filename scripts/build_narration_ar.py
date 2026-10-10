"""Turn the decisions in docs/arabic_script.md into config/narration_ar.json, the file the recorder reads.

Run: python3 scripts/build_narration_ar.py   (then review the report: every line is ready / pending / removed)

Decisions are written after **Decision:** by hand, or in the recorder's Decide mode (scripts/record_server.py),
which writes the same thing into the file through set_decision() / set_option() below and rebuilds. Either
way the file is the record.

Decisions are read, not trusted blindly: a number picks that option (as it now reads in the file, so an
option with a few letters changed and then picked is recorded as the edited option plus its number), ★ picks
the starred option, Arabic text is the line itself, and anything that reads like an instruction (English
words other than the names and terms the line's options already use) has to be handled by hand in OVERRIDES
below. A decision of `remove` (or `cut`) drops the line.
"""
from __future__ import annotations

import json
import re
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "docs" / "arabic_script.md"
OUT = ROOT / "config" / "narration_ar.json"
NARR = ROOT / "config" / "narration.json"

TITLES = {
          "hook": "Hook: a boat that won by cheating, and an AI that said it wasn't a robot",
          "bit1_maze": "Bit 1: a dot, a maze, and a reward",
          "bit2_coin": "Bit 2: it learns what we reward, not what we mean",
          "bit3_likes": "Bit 3: people as the reward (the like button)",
          "bit4_tests": "Bit 4: agents fix the test; the CAPTCHA, told in full",
          "bit5_scratch": "Bit 5: read the scratchpad",
          "bit6_recap": "Bit 6: recap"}

# Decisions that carry an instruction, read by hand. key -> (status, option picked or None, what it means)
OVERRIDES = {}

# Latin words that can sit inside Arabic wording without making it read as an instruction
TERMS = {"ai", "agent", "agents", "github", "mcp", "claude", "anthropic", "chatgpt", "openai", "gpt", "deepseek",
         "r1", "zero", "sonnet", "go", "api", "captcha"}

AR_DIGITS = str.maketrans("١٢٣٤٥٦٧٨٩٠", "1234567890")
clean = lambda s: re.sub(r"^(?:★\s*)?\d\)\s*", "", s.replace("‏", "").replace("‎", "").strip()).lstrip("،, ")
OPTION_RE = r"(?m)^(★ )?\s*([1-9])\)\s*(.+?)\s*$"
_lock = threading.Lock()   # the recorder writes from several request threads


def blocks() -> list[dict]:
    """Every line in the file, in order: its key, when it plays (estimate), its options as they read now,
    the notes under them, and the decision as written."""
    out = []
    for b in re.split(r"(?m)^### ", MD.read_text(encoding="utf-8"))[1:]:
        head = b.split("\n", 1)[0]
        body = b.split("**Decision:**")[0]
        parts = [p.strip() for p in head.split("·")]
        d = re.search(r"(?m)^\*\*Decision:\*\*[ \t]*(.*)$", b)
        val = clean(d.group(1)) if d else ""
        if not val and d:                      # the pick was pasted on the lines under "Decision:"
            after = []
            for ln in b[d.end():].split("\n"):
                if ln.startswith("#"):
                    break
                if ln.strip():
                    after.append(clean(ln))
            val = " ".join(after)
        out.append({"key": re.search(r"`([^`]+)`", head).group(1),
                    "when": parts[0], "timing": parts[-1] if len(parts) > 2 else "",
                    "options": [{"n": int(m.group(2)), "star": bool(m.group(1)), "text": clean(m.group(3))}
                                for m in re.finditer(OPTION_RE, body)],
                    "notes": [ln.lstrip("> ").strip() for ln in body.split("\n") if ln.startswith(">")],
                    "decision": val})
    return out


def _pick(val: str) -> str:
    return re.sub(r"^★\s*(?=\d$)", "", val.translate(AR_DIGITS).strip("() ."))


def picked(blk: dict) -> int | None:
    """The option number a decision picks (★ = the starred one), or None."""
    if blk["key"] in OVERRIDES:
        return OVERRIDES[blk["key"]][1]
    pick, opts = _pick(blk["decision"]), blk["options"]
    if pick == "★" and opts:
        return next((o["n"] for o in opts if o["star"]), opts[0]["n"])
    if pick.isdigit() and any(o["n"] == int(pick) for o in opts):
        return int(pick)
    return None


def reads_like_instruction(val: str, options: list[dict]) -> bool:
    """English words in a decision, other than names and terms (TERMS, or ones the line's options use)."""
    known = TERMS | {w.lower() for o in options for w in re.findall(r"[A-Za-z]+", o["text"])}
    return any(w.lower() not in known for w in re.findall(r"[A-Za-z]+", val))


def resolve(blk: dict, en: dict) -> dict:
    """One line of config/narration_ar.json: the Arabic to record and its status."""
    key, val = blk["key"], blk["decision"]
    text = {o["n"]: o["text"] for o in blk["options"]}
    line = {"key": key, "en": en.get(key, "")}
    n = picked(blk)
    if key in OVERRIDES:
        status, _, note = OVERRIDES[key]
        line.update(ar=text[n] if n else None, status=status, note=note)
        if n:
            line["source"] = f"option {n}"
    elif not val:
        line.update(ar=None, status="pending")
    elif n:
        line.update(ar=text[n], status="ready", source=f"option {_pick(val)}")
    elif val.lower() in ("remove", "cut"):
        line.update(ar=None, status="removed", note="Ali: remove this line")
    elif reads_like_instruction(val, blk["options"]):
        line.update(ar=None, status="needs review", note=f"Decision reads like an instruction: {val!r}")
    else:
        line.update(ar=val, status="ready", source="Ali's wording")
    return line


def build(write: bool = True) -> tuple[dict, list[str], dict]:
    """Read every decision and (re)write config/narration_ar.json; returns it, a report line per key, and counts."""
    en = {l["key"]: l["text"] for s in json.loads(NARR.read_text(encoding="utf-8"))["segments"] for l in s["lines"]}
    segs, report, counts = {}, [], {}
    for blk in blocks():
        line = resolve(blk, en)
        segs.setdefault(blk["key"].split(".")[0], []).append(line)
        counts[line["status"]] = counts.get(line["status"], 0) + 1
        report.append(f"{line['key']:16s} {line['status']:12s} {line.get('source', ''):14s} "
                      f"{line['ar'] or line.get('note', '')}")
    doc = {"notes": "The Arabic narration as decided in docs/arabic_script.md, one entry per spoken line, grouped by "
                    "bit (segment id = scene). status: ready (text to record), pending (no decision yet), removed "
                    "(cut from the video). Read by scripts/record_server.py; regenerated after each round of decisions.",
           "segments": [{"id": s, "title": TITLES.get(s, s), "lines": ls} for s, ls in segs.items()]}
    new = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    if write and (not OUT.is_file() or OUT.read_text(encoding="utf-8") != new):
        tmp = OUT.with_name(OUT.name + ".tmp")
        tmp.write_text(new, encoding="utf-8")
        tmp.replace(OUT)
    return doc, report, counts


# ---------------------------------------------------------------- writing decisions (the recorder's Decide mode)
def _one_line(s: str) -> str:
    return " ".join(s.replace("‏", "").replace("‎", "").split())


def _rewrite_block(key: str, edit) -> None:
    """Rewrite one line's block with edit(block) -> block; the rest of the file stays byte for byte."""
    with _lock:
        parts = re.split(r"(?m)^(?=### )", MD.read_text(encoding="utf-8"))
        for i, b in enumerate(parts):
            m = re.match(r"### [^\n]*?`([^`]+)`", b)
            if m and m.group(1) == key:
                parts[i] = edit(b)
                break
        else:
            raise KeyError(f"no line {key} in {MD.name}")
        tmp = MD.with_name(MD.name + ".tmp")
        tmp.write_text("".join(parts), encoding="utf-8")
        tmp.replace(MD)


def set_decision(key: str, value: str) -> None:
    """Write `value` after the line's **Decision:**, as given ("" makes the line undecided again)."""
    value = _one_line(value)
    if "**Decision:**" in value:
        raise ValueError("a decision can't contain **Decision:**")

    def edit(b: str) -> str:
        lines = b.split("\n")
        i = next((j for j, ln in enumerate(lines) if ln.startswith("**Decision:**")), None)
        if i is None:
            raise KeyError(f"{key} has no **Decision:** line")
        j = i + 1
        while j < len(lines) and not lines[j].startswith("#"):
            j += 1
        blank = [ln for ln in lines[i + 1:j] if not ln.strip()]   # a pick pasted under the line is replaced too
        return "\n".join(lines[:i] + [f"**Decision:** {value}"] + blank + lines[j:])

    _rewrite_block(key, edit)


def set_option(key: str, n: int, text: str) -> None:
    """Replace option n's text (e.g. a few letters changed before picking it). Its number and ★ stay."""
    text = _one_line(text)
    if not text:
        raise ValueError("an option can't be empty")
    if "**Decision:**" in text:
        raise ValueError("an option can't contain **Decision:**")

    def edit(b: str) -> str:
        body, sep, rest = b.partition("**Decision:**")
        new, k = re.subn(rf"(?m)^((?:★ )?[ \t]*{int(n)}\)[ \t]*)(.+?)([ \t]*)$",
                         lambda m: m.group(1) + text + m.group(3), body, count=1)
        if not k:
            raise KeyError(f"{key} has no option {n}")
        return new + sep + rest

    _rewrite_block(key, edit)


def main() -> None:
    _, report, counts = build()
    print("\n".join(report))
    print(counts)


if __name__ == "__main__":
    main()

"""Turn the decisions in docs/arabic_script.md into config/narration_ar.json, the file the recorder reads.

Run: python3 scripts/build_narration_ar.py   (then review the report: every line is ready / pending / removed)

Decisions are read, not trusted blindly: a number picks that option (as it now reads in the file),
Arabic text is the line itself, and anything in English is an instruction that has to be handled
by hand in OVERRIDES below (e.g. a line to cut from the video).
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "docs" / "arabic_script.md"
OUT = ROOT / "config" / "narration_ar.json"
EDITS = ROOT / "config" / "narration_ar_edits.json"   # lines re-worded in the recorder: applied last
NARR = ROOT / "config" / "narration.json"

TITLES = {}   # segment id -> card title shown in the recorder, e.g. "hook": "Hook: ..."

# Decisions that carry an instruction, read by hand. key -> (status, option picked or None, what it means)
OVERRIDES = {}

AR_DIGITS = str.maketrans("١٢٣٤٥٦٧٨٩٠", "1234567890")
clean = lambda s: re.sub(r"^(?:★\s*)?\d\)\s*", "", s.replace("‏", "").replace("‎", "").strip()).lstrip("،, ")

def decisions():
    t = MD.read_text(encoding="utf-8")
    for b in re.split(r"(?m)^### ", t)[1:]:
        key = re.search(r"`([^`]+)`", b.split("\n", 1)[0]).group(1)
        opts = [clean(o) for o in re.findall(r"(?m)^(?:★ )?\s*[1-9]\)\s*(.+?)\s*$", b.split("**Decision:**")[0])]
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
        yield key, opts, val

en = {l["key"]: l["text"] for s in json.load(open(NARR, encoding="utf-8"))["segments"] for l in s["lines"]}
segs, report = {}, []
for key, opts, val in decisions():
    seg = key.split(".")[0]
    line = {"key": key, "en": en.get(key, "")}
    pick = val.translate(AR_DIGITS).strip("() .")
    if key in OVERRIDES:
        status, pick_n, note = OVERRIDES[key]
        line.update(ar=opts[pick_n - 1] if pick_n else None, status=status, note=note)
        if pick_n:
            line["source"] = f"option {pick_n}"
    elif not val:
        line.update(ar=None, status="pending")
    elif pick in ("★",) or (pick.isdigit() and 1 <= int(pick) <= len(opts)):
        line.update(ar=opts[0 if pick == "★" else int(pick) - 1], status="ready", source=f"option {pick}")
    elif re.search(r"[A-Za-z]", val):
        line.update(ar=None, status="needs review", note=f"Decision reads like an instruction: {val!r}")
    else:
        line.update(ar=val, status="ready", source="Ali's wording")
    edit = (json.loads(EDITS.read_text(encoding="utf-8"))["lines"].get(key) if EDITS.is_file() else None)
    if edit and line["status"] != "removed":
        line.update(ar=edit["ar"], status="ready", source="edited in recorder")
    segs.setdefault(seg, []).append(line)
    report.append(f"{key:16s} {line['status']:12s} {line.get('source', ''):14s} {line['ar'] or line.get('note', '')}")

doc = {"notes": "The Arabic narration as decided in docs/arabic_script.md, one entry per spoken line, grouped by "
                "bit (segment id = scene). status: ready (text to record), pending (no decision yet), removed "
                "(cut from the video). Read by scripts/record_server.py; regenerated after each round of decisions.",
       "segments": [{"id": s, "title": TITLES.get(s, s), "lines": ls} for s, ls in segs.items()]}
OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("\n".join(report))
counts = {}
for s in doc["segments"]:
    for l in s["lines"]:
        counts[l["status"]] = counts.get(l["status"], 0) + 1
print(counts)

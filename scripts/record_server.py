#!/usr/bin/env python3
"""
Local page for the Arabic narration: decide each line, then record it.

Decide mode shows every line of docs/arabic_script.md with its options: pick one, change a few letters of
an option first, write your own wording, or remove the line. Each choice is written into the file after the
line's **Decision:** (an edited option is rewritten in place and keeps its number), exactly as if typed there,
through scripts/build_narration_ar.py, which also rebuilds config/narration_ar.json. The file is re-read on
every request, so edits made in an editor show up on the next reload.

Record mode shows the decided Arabic one line at a time and records it from the browser's microphone. Lines
are grouped by bit; undecided lines show but can't be recorded yet, removed ones are skipped. Editing a
line's wording here (E) edits the option it uses, or your own wording, in the same file.

Every take is kept; nothing is ever overwritten or deleted:

  media/audio/lines_ar/takes/<key>__t01.wav, __t02.wav, ...   every take, in recording order
  media/audio/lines_ar/<key>.wav                                the take you chose (the newest, unless you pick another)
  media/audio/lines_ar/manifest.json                            per line: the Arabic you were shown for every take,
                                                                its length, when it was recorded, which take is chosen

If you said a line a little differently and then fixed its wording to match, "Mark as current" on the take
records that it says the new wording (a "says" field next to the wording you were shown; nothing else changes).

<key> is the line's key in config/narration.json (hook.1, bit3_chat.12, ...), so a file name says which
line it is, and manifest.json says exactly which words were read in it.

Run:  python3 scripts/record_server.py      then open http://localhost:8765 (Chrome or Safari)
      (RECORDER_SCRIPT / RECORDER_LINES / RECORDER_OUT / RECORDER_PORT point it elsewhere, e.g. to test on copies)
"""
from __future__ import annotations

import datetime as _dt
import io
import json
import os
import re
import shutil
import sys
import threading
import urllib.parse
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_narration_ar as nar  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
nar.MD = Path(os.environ.get("RECORDER_SCRIPT", nar.MD))
nar.OUT = Path(os.environ.get("RECORDER_LINES", nar.OUT))
EN_INDEX = REPO_ROOT / "media" / "audio" / "lines" / "index.json"
OUT_DIR = Path(os.environ.get("RECORDER_OUT", REPO_ROOT / "media" / "audio" / "lines_ar"))
TAKES_DIR = OUT_DIR / "takes"
MANIFEST = OUT_DIR / "manifest.json"
PAGE = Path(__file__).resolve().parent / "recorder" / "index.html"
FONT = REPO_ROOT / "assets" / "fonts" / "Amiri-Regular.ttf"
PORT = int(os.environ.get("RECORDER_PORT", 8765))

KEY_RE = re.compile(r"^[A-Za-z0-9_]+\.[0-9]+$")
TAKE_RE = re.compile(r"^([A-Za-z0-9_]+\.[0-9]+)__t(\d+)\.wav$")
_lock = threading.Lock()


def read_lines() -> list[dict]:
    """Every line in order, with its options and decision from docs/arabic_script.md. config/narration_ar.json
    is rebuilt from the file on every read, so the two never disagree. Removed lines are included (they can
    be brought back), and are never recordable."""
    doc, _, _ = nar.build()
    info = {b["key"]: b for b in nar.blocks()}
    out = []
    for seg in doc["segments"]:
        for ln in seg["lines"]:
            b = info[ln["key"]]
            out.append({"key": ln["key"], "segment": seg["id"], "segment_title": seg.get("title", seg["id"]),
                        "en": ln.get("en", ""), "text": ln.get("ar") or "", "status": ln.get("status", "pending"),
                        "note": ln.get("note", ""), "source": ln.get("source", ""), "picked": nar.picked(b),
                        "options": b["options"], "notes": b["notes"], "decision": b["decision"],
                        "when": b["when"], "timing": b["timing"]})
    return out


def load_manifest() -> dict:
    if MANIFEST.is_file():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"notes": "Arabic narration takes recorded with scripts/record_server.py. "
                     "Per line: every take (file in takes/, the Arabic shown while recording it, "
                     "seconds, time) and the chosen one, copied to <key>.wav.",
            "lines": {}}


def save_manifest(m: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST.with_suffix(".tmp")
    tmp.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(MANIFEST)


def en_seconds() -> dict[str, float]:
    if not EN_INDEX.is_file():
        return {}
    return {k: float(v["duration"]) for k, v in json.loads(EN_INDEX.read_text())["lines"].items()}


def lines_payload() -> list[dict]:
    man = load_manifest()["lines"]
    en_s = en_seconds()
    out = []
    for i, ln in enumerate(read_lines()):
        rec = man.get(ln["key"], {"takes": [], "chosen": None})
        out.append({**ln, "n": i + 1, "en_seconds": en_s.get(ln["key"]),
                    "takes": rec["takes"], "chosen": rec.get("chosen")})
    return out


def _next_take(key: str) -> int:
    nums = [int(m.group(2)) for p in TAKES_DIR.glob(f"{key}__t*.wav") if (m := TAKE_RE.match(p.name))]
    return max(nums, default=0) + 1


def save_take(key: str, body: bytes, shown_text: str) -> dict:
    with wave.open(io.BytesIO(body)) as w:            # refuse anything that isn't a readable WAV
        seconds = w.getnframes() / float(w.getframerate())
    with _lock:
        TAKES_DIR.mkdir(parents=True, exist_ok=True)
        name = f"{key}__t{_next_take(key):02d}.wav"
        (TAKES_DIR / name).write_bytes(body)
        shutil.copyfile(TAKES_DIR / name, OUT_DIR / f"{key}.wav")
        man = load_manifest()
        rec = man["lines"].setdefault(key, {"takes": [], "chosen": None})
        rec["takes"].append({"file": name, "text": shown_text, "seconds": round(seconds, 3),
                             "recorded": _dt.datetime.now().isoformat(timespec="seconds")})
        rec["chosen"] = name
        save_manifest(man)
    return rec


def mark_current(key: str, name: str, text: str) -> dict:
    """Take `name` says `text`, the line's current wording (it was re-worded after recording to match the take)."""
    with _lock:
        man = load_manifest()
        rec = man["lines"].get(key)
        take = next((t for t in rec["takes"] if t["file"] == name), None) if rec else None
        if take is None:
            raise KeyError(f"no take {name} for {key}")
        take["says"] = text
        take["confirmed"] = _dt.datetime.now().isoformat(timespec="seconds")
        save_manifest(man)
    return rec


def choose_take(key: str, name: str) -> dict:
    with _lock:
        man = load_manifest()
        rec = man["lines"].get(key)
        if not rec or name not in [t["file"] for t in rec["takes"]]:
            raise KeyError(f"no take {name} for {key}")
        shutil.copyfile(TAKES_DIR / name, OUT_DIR / f"{key}.wav")
        rec["chosen"] = name
        save_manifest(man)
    return rec


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # quieter console: one line per save
        pass

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200) -> None:
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path in ("/", "/index.html"):
            return self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        if url.path == "/font/Amiri-Regular.ttf":
            return self._send(200, FONT.read_bytes(), "font/ttf")
        if url.path == "/api/lines":
            try:
                return self._json({"lines": lines_payload(), "source": os.path.relpath(nar.MD, REPO_ROOT),
                                   "out_dir": str(OUT_DIR)})
            except Exception as e:
                return self._json({"error": f"could not read {nar.MD.name}: {e}"}, 500)
        if url.path.startswith("/audio/"):
            name = urllib.parse.unquote(url.path[len("/audio/"):])
            if TAKE_RE.match(name) and (TAKES_DIR / name).is_file():
                return self._send(200, (TAKES_DIR / name).read_bytes(), "audio/wav")
        self._send(404, b"not found", "text/plain")

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(url.query)
        key = (q.get("key") or [""])[0]
        if not KEY_RE.match(key):
            return self._json({"error": "bad key"}, 400)
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        try:
            if url.path == "/api/take":
                ready = {ln["key"] for ln in read_lines() if ln["status"] == "ready"}
                if key not in ready:
                    return self._json({"error": f"{key} is not ready to record (no decided text yet)"}, 409)
                shown = urllib.parse.unquote(self.headers.get("X-Text") or "")
                rec = save_take(key, body, shown)
                t = rec["takes"][-1]
                print(f"saved {t['file']}  {t['seconds']:.2f}s  {t['text']}", flush=True)
                return self._json(rec)
            if url.path == "/api/choose":
                return self._json(choose_take(key, json.loads(body)["file"]))
            if url.path == "/api/current":          # body {"file": "<key>__t03.wav"}: it says the current wording
                line = next((ln for ln in read_lines() if ln["key"] == key and ln["status"] == "ready"), None)
                if line is None:
                    return self._json({"error": f"{key} has no decided wording"}, 409)
                rec = mark_current(key, json.loads(body)["file"], line["text"])
                print(f"marked current: {json.loads(body)['file']} says {line['text']}", flush=True)
                return self._json(rec)
            if url.path == "/api/decide":           # body {"decision": "2" | "remove" | Arabic wording | ""}
                value = json.loads(body)["decision"]
                nar.set_decision(key, value)
                print(f"decided {key}: {value}", flush=True)
                return self._json({"ok": True})
            if url.path == "/api/option":           # body {"n": 2, "text": "...", "pick": true}
                req = json.loads(body)
                n = int(req["n"])
                nar.set_option(key, n, req["text"])
                if req.get("pick"):
                    nar.set_decision(key, str(n))
                print(f"option {n} of {key}{' (picked)' if req.get('pick') else ''}: {req['text']}", flush=True)
                return self._json({"ok": True})
        except ValueError as e:
            return self._json({"error": str(e)}, 400)
        except (wave.Error, EOFError) as e:
            return self._json({"error": f"not a WAV: {e}"}, 400)
        except KeyError as e:
            return self._json({"error": str(e)}, 404)
        self._json({"error": "unknown endpoint"}, 404)


def main() -> None:
    read_lines()  # fail early if docs/arabic_script.md can't be read
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Recorder on http://localhost:{PORT}  (decisions in {nar.MD}, takes to {OUT_DIR}/)", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

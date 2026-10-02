#!/usr/bin/env python3
"""
Local recorder for the Arabic narration.

Shows the Arabic narration one line at a time and records each line from the browser's microphone.
The lines come from config/narration_ar.json: the decisions in docs/arabic_script.md, read and turned
into plain text by Claude (a decision can also be an instruction, e.g. "remove this line", so the
recorder never reads the decisions itself). Lines are grouped by bit; "pending" lines show but can't
be recorded yet, "removed" ones are skipped. The file is re-read on every page load.

A line's text can be edited on its card. The new wording is written into config/narration_ar.json
and kept in config/narration_ar_edits.json (with the wording it replaced), which
scripts/build_narration_ar.py applies last, so an edit made here survives a rebuild from the script.

Every take is kept; nothing is ever overwritten or deleted:

  media/audio/lines_ar/takes/<key>__t01.wav, __t02.wav, ...   every take, in recording order
  media/audio/lines_ar/<key>.wav                                the take you chose (the newest, unless you pick another)
  media/audio/lines_ar/manifest.json                            per line: the Arabic you were shown for every take,
                                                                its length, when it was recorded, which take is chosen

<key> is the line's key in config/narration.json (hook.1, bit3_chat.12, ...), so a file name says which
line it is, and manifest.json says exactly which words were read in it.

Run:  python3 scripts/record_server.py      then open http://localhost:8765 (Chrome or Safari)
"""
from __future__ import annotations

import datetime as _dt
import io
import json
import os
import re
import shutil
import threading
import urllib.parse
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LINES_FILE = Path(os.environ.get("RECORDER_LINES", REPO_ROOT / "config" / "narration_ar.json"))
EDITS_FILE = LINES_FILE.with_name(LINES_FILE.stem + "_edits.json")
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
    """Recordable lines in order, from config/narration_ar.json (removed lines left out)."""
    doc = json.loads(LINES_FILE.read_text(encoding="utf-8"))
    out = []
    for seg in doc["segments"]:
        for ln in seg["lines"]:
            if ln.get("status") == "removed":
                continue
            out.append({"key": ln["key"], "segment": seg["id"], "segment_title": seg.get("title", seg["id"]),
                        "en": ln.get("en", ""), "text": ln.get("ar") or "",
                        "status": ln.get("status", "ready"), "note": ln.get("note", ""),
                        "edited": ln.get("source") == "edited in recorder"})
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


def _write_json(path: Path, doc: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def edit_line(key: str, text: str) -> dict:
    """New wording for line `key`: into narration_ar.json now, and into the edits file so a rebuild
    from docs/arabic_script.md keeps it."""
    text = " ".join(text.replace("\u200f", "").replace("\u200e", "").split())
    if not text:
        raise ValueError("empty line")
    with _lock:
        doc = json.loads(LINES_FILE.read_text(encoding="utf-8"))
        line = next((ln for seg in doc["segments"] for ln in seg["lines"] if ln["key"] == key), None)
        if line is None or line.get("status") == "removed":
            raise KeyError(f"no line {key}")
        was = line.get("ar")
        if text == was:
            return line
        line.update(ar=text, status="ready", source="edited in recorder")
        _write_json(LINES_FILE, doc)
        edits = (json.loads(EDITS_FILE.read_text(encoding="utf-8")) if EDITS_FILE.is_file() else
                 {"notes": "Lines re-worded in the recorder (scripts/record_server.py). "
                           "scripts/build_narration_ar.py applies these last.", "lines": {}})
        prev = edits["lines"].get(key, {})
        edits["lines"][key] = {"ar": text, "was": prev.get("was", was),
                               "edited": _dt.datetime.now().isoformat(timespec="seconds")}
        _write_json(EDITS_FILE, edits)
    print(f"edited {key}: {text}", flush=True)
    return line


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
                return self._json({"lines": lines_payload(), "source": os.path.relpath(LINES_FILE, REPO_ROOT),
                                   "out_dir": str(OUT_DIR)})
            except Exception as e:
                return self._json({"error": f"could not read {LINES_FILE.name}: {e}"}, 500)
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
            if url.path == "/api/edit":
                line = edit_line(key, json.loads(body)["text"])
                return self._json({"text": line["ar"], "edited": True})
        except ValueError as e:
            return self._json({"error": str(e)}, 400)
        except (wave.Error, EOFError) as e:
            return self._json({"error": f"not a WAV: {e}"}, 400)
        except KeyError as e:
            return self._json({"error": str(e)}, 404)
        self._json({"error": "unknown endpoint"}, 404)


def main() -> None:
    read_lines()  # fail early if the lines file can't be read
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Recorder on http://localhost:{PORT}  (lines from {os.path.relpath(LINES_FILE, REPO_ROOT)}, "
          f"takes to {OUT_DIR}/)", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

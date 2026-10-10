#!/usr/bin/env python3
"""
Adobe Podcast "Enhance Speech" on the chosen Arabic takes, one at a time (free plan: no bulk queue).

Uses scripts/adobe_enhance.py (copied from video 1) and its saved browser session:
config/adobe_enhance_auth.json here, or ../1-hour-challenge/config/adobe_enhance_auth.json. If the
session has expired, sign in again with:  .venv/bin/python scripts/adobe_enhance.py login

  in:   media/audio/lines_ar/takes/<key>__tNN.wav      the take chosen in manifest.json
  out:  media/audio/lines_ar/enhanced/<key>__tNN.wav   same name, so it stays tied to that take

Only lines marked ready in config/narration_ar.json are sent, and a take already enhanced is
skipped, so a re-recorded line costs one upload. scripts/process_takes.py then trims and levels
the enhanced audio (finding the speech in it: Adobe's silence is clean where the raw take's isn't).

Run:  .venv/bin/python scripts/enhance_takes.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adobe_enhance as ae  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
TAKES = REPO_ROOT / "media" / "audio" / "lines_ar"
OUT = TAKES / "enhanced"
LINES_AR = REPO_ROOT / "config" / "narration_ar.json"
AUTH = [REPO_ROOT / "config" / "adobe_enhance_auth.json",
        REPO_ROOT.parent / "ai-image-explainer" / "config" / "adobe_enhance_auth.json",
        REPO_ROOT.parent / "1-hour-challenge" / "config" / "adobe_enhance_auth.json"]


def chosen_takes() -> list[Path]:
    """The chosen take of every ready line, if it says the line's current wording."""
    ready = {ln["key"]: ln["ar"] for seg in json.loads(LINES_AR.read_text(encoding="utf-8"))["segments"]
             for ln in seg["lines"] if ln["status"] == "ready"}
    manifest = json.loads((TAKES / "manifest.json").read_text(encoding="utf-8"))["lines"]
    out, stale = [], []
    for key, text in ready.items():
        rec = manifest.get(key) or {}
        take = next((t for t in rec.get("takes", []) if t["file"] == rec.get("chosen")), None)
        if take and take.get("says", take["text"]) == text:   # "says": marked current in the recorder
            out.append(TAKES / "takes" / take["file"])
        else:
            stale.append(key)
    if stale:
        print(f"not recorded for the current wording (skipped): {', '.join(stale)}")
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true", help="enhance again even if done")
    args = p.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    pending = [(src, OUT / src.name) for src in chosen_takes()
               if args.force or not (OUT / src.name).is_file()]
    print(f"{len(pending)} take(s) to enhance")
    if args.dry_run or not pending:
        for src, _ in pending:
            print("  " + src.name)
        return
    auth = next((a for a in AUTH if a.is_file()), None)
    if not auth:
        raise SystemExit("No saved Adobe session. Run: .venv/bin/python scripts/adobe_enhance.py login")
    token, handle = ae.token_from_playwright(auth)
    failed = []
    try:
        client = ae.Phonos(token, refresh=handle["refresh"])
        if client.gateway("GET", "/api/v1/user").status_code == 401:
            raise SystemExit("Adobe session expired. Run: .venv/bin/python scripts/adobe_enhance.py login")
        for i, (src, dest) in enumerate(pending, 1):
            print(f"[{i}/{len(pending)}] {src.name}", flush=True)
            try:
                ae.enhance_one(client, src, dest, ae.MODEL_VERSION)
            except ae.DailyLimit as e:
                print(f"Adobe's daily limit reached ({e}). Run again tomorrow; finished takes are kept.")
                break
            except Exception as e:  # keep going; report at the end
                failed.append(f"{src.name}: {e}")
                print(f"  FAILED: {e}", flush=True)
            time.sleep(ae.BETWEEN_FILES_S)
    finally:
        handle["browser"].close()
        handle["pw"].stop()
    done = sum(1 for src in chosen_takes() if (OUT / src.name).is_file())
    print(f"\n{done} of {len(chosen_takes())} chosen takes enhanced → {OUT.relative_to(REPO_ROOT)}")
    if failed:
        print("Failed:\n  " + "\n  ".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
One-by-one Adobe Podcast Enhance Speech (free plan has no bulk queue).

Adobe has no public Enhance API. This talks to the same backend the website uses
(https://phonos-server-flex.adobe.io) with your IMS access token.

Auth (pick one):
  python3 scripts/adobe_enhance.py login
      Opens a browser. Sign in, wait until the enhance page loads, then the
      session is saved to config/adobe_enhance_auth.json (gitignored).

  Paste a Bearer token into config/adobe_enhance_token.txt or
  ADOBE_IMS_TOKEN. In Chrome DevTools on https://podcast.adobe.com/en/enhance
  while signed in: Network → any phonos-server-flex.adobe.io request →
  Request Headers → Authorization (the value after "Bearer ").

Cookies alone from podcast.adobe.com are usually not enough — IMS stores the
access token in localStorage. The login command captures both.

Then:
  python3 scripts/adobe_enhance.py run
  python3 scripts/adobe_enhance.py run --dry-run
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
import os
import shutil
import sqlite3
import sys
import tempfile
import time
import uuid
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = REPO_ROOT / "media" / "audio" / "take two"
DEFAULT_OUTPUT = DEFAULT_INPUT / "enhanced"
AUTH_PATH = REPO_ROOT / "config" / "adobe_enhance_auth.json"
TOKEN_PATH = REPO_ROOT / "config" / "adobe_enhance_token.txt"

PHONOS = "https://phonos-server-flex.adobe.io"
API_KEY = "phonos-server-prod"
ENHANCE_URL = "https://podcast.adobe.com/en/enhance"
FOLDER_PATH = "QuickActionJobs"
MODEL_VERSION = "v2"
POLL_S = 3.0
POLL_TIMEOUT_S = 15 * 60
BETWEEN_FILES_S = 2.0
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)


def md5_b64(data: bytes) -> str:
    return base64.b64encode(hashlib.md5(data).digest()).decode("ascii")


def pick(obj: dict, *keys):
    for k in keys:
        if k in obj and obj[k] not in (None, ""):
            return obj[k]
    return None


class Phonos:
    def __init__(self, token: str, refresh=None):
        self.token = token
        self.refresh = refresh
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def _auth_headers(self, extra: dict | None = None) -> dict:
        h = {
            "Authorization": f"Bearer {self.token}",
            "X-Api-Key": API_KEY,
            "Accept": "application/json",
        }
        if extra:
            h.update(extra)
        return h

    def gateway(self, method: str, path: str, **kwargs) -> requests.Response:
        url = path if path.startswith("http") else f"{PHONOS}{path}"
        if "://" not in path:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}time={int(time.time() * 1000)}"
        extra_headers = kwargs.pop("headers", None)
        headers = self._auth_headers(extra_headers)
        r = self.session.request(method, url, headers=headers, timeout=120, **kwargs)
        if r.status_code == 401 and self.refresh:
            new = self.refresh()
            if new:
                self.token = new
                headers = self._auth_headers(extra_headers)
                r = self.session.request(
                    method, url, headers=headers, timeout=120, **kwargs
                )
        return r

    def upload(self, path: Path) -> str:
        data = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "audio/mp4"
        blob_req = {
            "blob": {
                "filename": path.name,
                "content_type": content_type,
                "byte_size": len(data),
                "checksum": md5_b64(data),
            }
        }
        create = self.gateway(
            "POST",
            "/rails/active_storage/direct_uploads",
            json=blob_req,
            headers={
                "Content-Type": "application/json",
                "X-Folder-Path": FOLDER_PATH,
            },
        )
        if not create.ok:
            raise RuntimeError(
                f"direct_uploads failed {create.status_code}: {create.text[:500]}"
            )
        blob = create.json()
        signed_id = blob["signed_id"]
        du = blob["direct_upload"]
        put = self.session.put(
            du["url"],
            data=data,
            headers=du.get("headers") or {},
            timeout=300,
        )
        if not put.ok:
            raise RuntimeError(
                f"blob PUT failed {put.status_code}: {put.text[:300]}"
            )
        return signed_id

    def create_track(self, filename: str, signed_id: str, model_version: str) -> dict:
        track_id = str(uuid.uuid4())
        r = self.gateway(
            "POST",
            "/api/v1/enhance_speech_tracks",
            json={
                "id": track_id,
                "track_name": filename,
                "model_version": model_version,
                "signed_id": signed_id,
            },
            headers={"Content-Type": "application/json"},
        )
        if r.status_code == 429:
            retry = r.headers.get("Retry-After")
            wait = float(retry) if retry else 60.0
            raise RateLimited(wait)
        if r.status_code == 409:
            raise RateLimited(20.0, "concurrency limit")
        if r.status_code == 422:
            raise DailyLimit(r.text[:500])
        if not r.ok:
            raise RuntimeError(
                f"create track failed {r.status_code}: {r.text[:800]}"
            )
        return r.json()

    def get_track(self, track_id: str) -> dict:
        r = self.gateway("GET", f"/api/v1/enhance_speech_tracks/{track_id}")
        if not r.ok:
            raise RuntimeError(
                f"poll track failed {r.status_code}: {r.text[:500]}"
            )
        return r.json()

    def resolve_audio_url(self, url: str) -> str:
        if url.startswith("https://podcast.adobe.com"):
            return url
        if url.startswith("http://") or url.startswith("https://"):
            return url
        r = self.gateway("GET", url)
        if not r.ok:
            raise RuntimeError(
                f"presign failed {r.status_code}: {r.text[:400]}"
            )
        ctype = r.headers.get("Content-Type", "")
        if "json" in ctype:
            return r.json()["url"]
        # Some responses are already the file; caller handles bytes separately.
        return url

    def download(self, url: str, dest: Path) -> None:
        resolved = self.resolve_audio_url(url)
        if resolved == url and not url.startswith("http"):
            r = self.gateway("GET", url)
            dest.write_bytes(r.content)
            return
        r = self.session.get(resolved, timeout=300)
        if not r.ok:
            # Retry with auth in case it's still on Adobe.
            r = self.gateway("GET", resolved)
        if not r.ok:
            raise RuntimeError(f"download failed {r.status_code}: {r.text[:300]}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(r.content)


class RateLimited(Exception):
    def __init__(self, wait_s: float, msg: str = "rate limited"):
        super().__init__(msg)
        self.wait_s = wait_s


class DailyLimit(Exception):
    pass


def launch_chromium(pw, *, headless: bool):
    """Prefer the installed Google Chrome so we don't need Playwright's Chromium download."""
    try:
        return pw.chromium.launch(headless=headless, channel="chrome")
    except Exception as chrome_err:
        try:
            return pw.chromium.launch(headless=headless)
        except Exception as chromium_err:
            raise SystemExit(
                "Could not launch a browser.\n"
                f"  Chrome: {chrome_err}\n"
                f"  Playwright Chromium: {chromium_err}\n"
                "Install Chrome, or from the venv run:\n"
                "  .venv/bin/playwright install chromium\n"
                "(plain `playwright install` uses Homebrew's Playwright, which is the wrong version.)"
            ) from chromium_err


def read_token_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8").strip()
    if raw.lower().startswith("bearer "):
        raw = raw[7:].strip()
    return raw or None


def token_from_playwright(auth_path: Path) -> tuple[str, object]:
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = launch_chromium(pw, headless=True)
    context = browser.new_context(storage_state=str(auth_path))
    page = context.new_page()
    page.goto(ENHANCE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)

    def grab() -> str | None:
        return page.evaluate(
            """() => {
              const t = window.adobeIMS && window.adobeIMS.getAccessToken
                && window.adobeIMS.getAccessToken();
              return t && t.token || null;
            }"""
        )

    token = grab()
    if not token:
        page.evaluate(
            """async () => {
              if (window.adobeIMS && window.adobeIMS.refreshToken) {
                await window.adobeIMS.refreshToken();
              }
            }"""
        )
        page.wait_for_timeout(1500)
        token = grab()
    if not token:
        browser.close()
        pw.stop()
        raise RuntimeError(
            f"Signed-in session not found in {auth_path}. Run: "
            "python3 scripts/adobe_enhance.py login"
        )

    def refresh() -> str | None:
        page.evaluate(
            """async () => {
              if (window.adobeIMS && window.adobeIMS.refreshToken) {
                await window.adobeIMS.refreshToken();
              }
            }"""
        )
        return grab()

    # Keep playwright alive for refresh; caller must close.
    handle = {"browser": browser, "pw": pw, "page": page, "refresh": refresh}
    return token, handle


def _page_signed_in(page) -> bool:
    from playwright.sync_api import Error as PlaywrightError

    try:
        if page.is_closed():
            return False
        if "podcast.adobe.com" not in (page.url or ""):
            return False
        return bool(
            page.evaluate(
                """() => Boolean(window.adobeIMS && window.adobeIMS.isSignedInUser
                  && window.adobeIMS.isSignedInUser())"""
            )
        )
    except PlaywrightError:
        return False


def firefox_default_profile() -> Path:
    ini = Path.home() / "Library/Application Support/Firefox/profiles.ini"
    root = Path.home() / "Library/Application Support/Firefox"
    if not ini.is_file():
        raise SystemExit("No Firefox profiles.ini found.")
    text = ini.read_text(encoding="utf-8")
    # Prefer the profile locked to the current Firefox install.
    current = None
    default_rel = None
    section: dict[str, str] = {}
    sections: list[dict[str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            if section:
                sections.append(section)
            section = {"_name": line[1:-1]}
            continue
        if "=" in line and section is not None:
            k, v = line.split("=", 1)
            section[k] = v
    if section:
        sections.append(section)
    for s in sections:
        if s.get("_name", "").startswith("Install") and s.get("Default"):
            current = s["Default"]
        if s.get("Default") == "1" and s.get("Path"):
            default_rel = s["Path"]
        if s.get("Name") == "default-release" and s.get("Path"):
            default_rel = default_rel or s["Path"]
    rel = current or default_rel
    if not rel:
        raise SystemExit("Could not find a Firefox profile path.")
    path = root / rel if not Path(rel).is_absolute() else Path(rel)
    if not path.is_dir():
        raise SystemExit(f"Firefox profile missing: {path}")
    return path


def _firefox_samesite(value: int) -> str:
    return {0: "None", 1: "Lax", 2: "Strict"}.get(int(value), "Lax")


def firefox_adobe_cookies(profile: Path) -> list[dict]:
    src = profile / "cookies.sqlite"
    if not src.is_file():
        raise SystemExit(f"No cookies.sqlite in {profile}")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        shutil.copy2(src, tmp_path / "cookies.sqlite")
        for extra in ("cookies.sqlite-wal", "cookies.sqlite-shm"):
            p = profile / extra
            if p.is_file():
                shutil.copy2(p, tmp_path / extra)
        con = sqlite3.connect(str(tmp_path / "cookies.sqlite"))
        rows = con.execute(
            """
            SELECT host, name, value, path, expiry, isSecure, isHttpOnly, sameSite
            FROM moz_cookies
            WHERE host LIKE '%adobe%' OR host LIKE '%adobelogin%'
            """
        ).fetchall()
        con.close()
    cookies = []
    for host, name, value, path, expiry, secure, http_only, same_site in rows:
        expires = int(expiry or 0)
        if expires > 10**11:
            expires = expires // 1000
        cookie = {
            "name": name,
            "value": value,
            "domain": host,
            "path": path or "/",
            "secure": bool(secure),
            "httpOnly": bool(http_only),
            "sameSite": _firefox_samesite(same_site),
        }
        if expires > 0:
            cookie["expires"] = expires
        if cookie["sameSite"] == "None" and not cookie["secure"]:
            cookie["sameSite"] = "Lax"
        cookies.append(cookie)
    return cookies


def wait_until_signed_in(context, timeout_s: float = 600) -> None:
    from playwright.sync_api import Error as PlaywrightError

    deadline = time.time() + timeout_s
    last_url = ""
    while time.time() < deadline:
        pages = [p for p in context.pages if not p.is_closed()]
        urls = []
        for p in pages:
            try:
                urls.append(p.url)
            except PlaywrightError:
                continue
            if _page_signed_in(p):
                return
        here = urls[-1] if urls else ""
        if here != last_url:
            print(f"  … {here or '(navigating)'}")
            last_url = here
        time.sleep(1.0)
    raise SystemExit("Timed out waiting for Adobe sign-in.")


def cmd_login(auth_path: Path, *, from_firefox: bool) -> None:
    from playwright.sync_api import sync_playwright

    auth_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = launch_chromium(pw, headless=False)
        context = browser.new_context()
        if from_firefox:
            profile = firefox_default_profile()
            cookies = firefox_adobe_cookies(profile)
            print(
                f"Importing {len(cookies)} Adobe cookies from Firefox "
                f"({profile.name}) so Google login is not needed."
            )
            if not any(c["name"] == "ims_sid" for c in cookies):
                browser.close()
                raise SystemExit(
                    "No Adobe IMS session in Firefox. In your normal Firefox, open\n"
                    f"  {ENHANCE_URL}\n"
                    "sign in with Google there, then run this login command again."
                )
            context.add_cookies(cookies)
        else:
            print("Opening a fresh Chrome. Google may block this automated window.")
        page = context.new_page()
        print("Opening Adobe Enhance…")
        page.goto(ENHANCE_URL, wait_until="domcontentloaded")
        wait_until_signed_in(context)
        time.sleep(2)
        context.storage_state(path=str(auth_path))
        browser.close()
    print(f"Saved session → {auth_path}")


def list_inputs(input_dir: Path) -> list[Path]:
    files = sorted(
        p for p in input_dir.glob("*.m4a") if p.is_file()
    )
    return files


def enhance_one(client: Phonos, src: Path, dest: Path, model_version: str) -> None:
    print(f"  upload {src.name} ({src.stat().st_size} bytes)")
    signed_id = client.upload(src)
    print(f"  create track  signed_id={signed_id[:18]}…")
    while True:
        try:
            track = client.create_track(src.name, signed_id, model_version)
            break
        except RateLimited as e:
            print(f"  {e} — wait {e.wait_s:.0f}s")
            time.sleep(e.wait_s)
    track_id = pick(track, "id")
    if not track_id:
        raise RuntimeError(f"no track id in {track}")
    print(f"  polling {track_id}")
    t0 = time.time()
    while True:
        if time.time() - t0 > POLL_TIMEOUT_S:
            raise TimeoutError(f"still processing after {POLL_TIMEOUT_S}s")
        track = client.get_track(track_id)
        err = pick(track, "error_type", "errorType")
        if err:
            raise RuntimeError(f"Adobe error on {src.name}: {err} {track}")
        done = pick(track, "finished_processing_at", "finishedProcessingAt")
        if done:
            break
        time.sleep(POLL_S)
    audio_url = pick(
        track,
        "enhance_speech_audio_url",
        "enhanceSpeechAudioUrl",
    )
    if not audio_url:
        raise RuntimeError(f"no enhance url on finished track: {track.keys()}")
    print(f"  download → {dest.name}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    client.download(audio_url, tmp)
    tmp.replace(dest)


def cmd_run(args: argparse.Namespace) -> None:
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    if not input_dir.is_dir():
        raise SystemExit(f"missing input dir: {input_dir}")
    files = list_inputs(input_dir)
    if not files:
        raise SystemExit(f"no .m4a files in {input_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    pending: list[tuple[Path, Path]] = []
    skipped = 0
    for src in files:
        dest = output_dir / f"{src.stem}.wav"
        if dest.exists() and dest.stat().st_size > 0 and not args.force:
            skipped += 1
            continue
        pending.append((src, dest))

    print(f"{len(files)} source files, {skipped} already done, {len(pending)} to enhance")
    if args.dry_run:
        for src, dest in pending:
            print(f"  {src.name} → {dest.relative_to(REPO_ROOT)}")
        return
    if not pending:
        return

    token = os.environ.get("ADOBE_IMS_TOKEN") or read_token_file(TOKEN_PATH)
    handle = None
    refresh = None
    if not token:
        auth = Path(args.auth)
        if not auth.is_file():
            raise SystemExit(
                "No IMS token. Either:\n"
                "  1) python3 scripts/adobe_enhance.py login\n"
                "  2) put the Bearer token in config/adobe_enhance_token.txt\n"
                "     (DevTools → Network → phonos-server-flex.adobe.io → Authorization)"
            )
        token, handle = token_from_playwright(auth)
        refresh = handle["refresh"]
        print("Loaded IMS token from saved browser session")
    else:
        print("Using IMS token from env/file")

    client = Phonos(token, refresh=refresh)
    who = client.gateway("GET", "/api/v1/user")
    if who.status_code == 401:
        raise SystemExit("IMS token rejected (401). Re-run login or paste a fresh token.")
    if not who.ok:
        print(f"warning: /api/v1/user → {who.status_code} {who.text[:200]}")
    else:
        user = who.json()
        print(f"signed in as {pick(user, 'email', 'display_name', 'displayName', 'id')}")

    failed = 0
    try:
        for i, (src, dest) in enumerate(pending, 1):
            print(f"[{i}/{len(pending)}] {src.name}")
            try:
                enhance_one(client, src, dest, args.model)
            except DailyLimit as e:
                print(f"daily duration limit hit: {e}")
                print("Stop here. Re-run tomorrow; completed files will be skipped.")
                break
            except Exception as e:
                failed += 1
                print(f"  FAILED: {e}")
                if args.fail_fast:
                    raise
            if i < len(pending):
                time.sleep(BETWEEN_FILES_S)
    finally:
        if handle:
            handle["browser"].close()
            handle["pw"].stop()

    print(f"done. failed={failed} remaining skipped-on-rerun if output exists")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    login = sub.add_parser("login", help="Sign in once and save session")
    login.add_argument("--auth", type=Path, default=AUTH_PATH)
    login.add_argument(
        "--fresh",
        action="store_true",
        help="Do not import Firefox cookies (Google login in Playwright Chrome; often blocked)",
    )

    run = sub.add_parser("run", help="Enhance m4a files one by one")
    run.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    run.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    run.add_argument("--auth", type=Path, default=AUTH_PATH)
    run.add_argument("--model", default=MODEL_VERSION, help="v1 or v2 (site default is v2)")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--force", action="store_true", help="re-enhance even if wav exists")
    run.add_argument("--fail-fast", action="store_true")

    args = p.parse_args()
    if args.cmd == "login":
        cmd_login(args.auth, from_firefox=not args.fresh)
    else:
        cmd_run(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)

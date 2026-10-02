#!/usr/bin/env python3
"""
Build the review cut with English subtitles — for the stage BEFORE Arabic VO exists.

Inputs
  config/scenes_manifest.json   segment order
  config/audio_manifest.json    silent MP4 path per segment (media/<Scene>.mp4)
  config/cues_en.json           {"segments": [{"id": ..., "cues": [{"start", "end", "text"}, ...]}]}
                                cue times are seconds relative to that segment's start

Outputs (media/output/)
  full_cut.en.srt        cues offset by each segment's real duration (ffprobe), one timeline
  full_cut.mp4           the six silent renders concatenated (re-encoded, one timeline), silent
                         mono AAC track added, SRT embedded as a soft subtitle track (mov_text)
  full_cut_burned.mp4    with --burn: subtitles rendered into the picture (needs libass in ffmpeg)

Once VO exists, use the normal path instead: mux_audio.py -> assemble_final.py.

Usage
  python3 scripts/build_srt_cut.py
  python3 scripts/build_srt_cut.py --burn
  python3 scripts/build_srt_cut.py --cues path/to/other_cues.json --out media/output/review.mp4

The Arabic upload cut (narration, music bed, the bottom 20% left clear for YouTube's captions):
  .venv/bin/python scripts/build_srt_cut.py --cues config/cues_ar_vo.json --out media/output/full_cut_ar.mp4 \\
      --no-subs --lang ar --music "media/music/No.10 _A New Beginning - Esther Abrami.mp3" --music-lufs -38 \\
      --caption-band 0.20
"""
from __future__ import annotations

import argparse
import json
import shutil
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCENES = REPO_ROOT / "config" / "scenes_manifest.json"
AUDIO = REPO_ROOT / "config" / "audio_manifest.json"
CUES = REPO_ROOT / "config" / "cues_en.json"
OUT_DIR = REPO_ROOT / "media" / "output"


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def working_binary(name: str) -> str:
    """First ffmpeg/ffprobe on PATH that actually launches (a broken Homebrew ffmpeg-full may shadow the good one)."""
    candidates = []
    found = shutil.which(name)
    if found:
        candidates.append(found)
    candidates += [f"/opt/homebrew/bin/{name}", f"/usr/local/bin/{name}"]
    for c in candidates:
        try:
            subprocess.run([c, "-version"], capture_output=True, check=True)
            return c
        except (OSError, subprocess.CalledProcessError):
            continue
    sys.exit(f"No working {name} found (tried {', '.join(candidates)})")


FFMPEG = working_binary("ffmpeg")
FFPROBE = working_binary("ffprobe")


def probe(path: Path, entries: str, stream: str | None = None) -> str:
    cmd = [FFPROBE, "-v", "error"]
    if stream:
        cmd += ["-select_streams", stream]
    cmd += ["-show_entries", entries, "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()


def duration(path: Path) -> float:
    return float(probe(path, "format=duration"))


def size(path: Path) -> tuple[int, int]:
    w, h = probe(path, "stream=width,height", "v:0").split()
    return int(w), int(h)


SAFE = 0.84          # kit.safe_rect: the scenes keep everything inside the middle 84% of the frame
TOP_MARGIN = 0.03    # with a caption band, the safe box's top edge lands this far below the frame's top


def caption_band_filter(w: int, h: int, band: float) -> str:
    """ffmpeg filter that keeps the bottom `band` of the frame clear for the viewer's captions: the
    picture is scaled down and moved up so the scenes' safe box spans TOP_MARGIN .. 1 - band of the
    height, and the frame stays w x h. What goes off the top is the empty strip above the safe box."""
    s = (1.0 - band - TOP_MARGIN) / SAFE
    sw, sh = 2 * round(w * s / 2), 2 * round(h * s / 2)
    y0 = 2 * round((TOP_MARGIN * h - (1.0 - SAFE) / 2 * sh) / 2)   # the scaled frame's top row (even)
    f = f"scale={sw}:{sh}:flags=lanczos"
    if y0 < 0:
        f += f",crop={sw}:{sh + y0}:0:{-y0}"
        y0 = 0
    return f + f",pad={w}:{h}:{(w - sw) // 2}:{y0}:black"


def srt_time(t: float) -> str:
    t = max(0.0, t)
    ms = int(round((t - int(t)) * 1000))
    s = int(t)
    if ms == 1000:
        s, ms = s + 1, 0
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d},{ms:03d}"


def build_srt(order: list[str], videos: dict[str, Path], cues_by_id: dict[str, list[dict]]) -> tuple[str, list[tuple[str, float, float]]]:
    lines: list[str] = []
    timeline: list[tuple[str, float, float]] = []
    offset = 0.0
    n = 0
    for sid in order:
        dur = duration(videos[sid])
        timeline.append((sid, offset, dur))
        for cue in sorted(cues_by_id.get(sid, []), key=lambda c: c["start"]):
            start = offset + float(cue["start"])
            end = min(offset + float(cue["end"]), offset + dur)
            if end <= start:
                continue
            n += 1
            lines += [str(n), f"{srt_time(start)} --> {srt_time(end)}", str(cue["text"]).strip(), ""]
        offset += dur
    return "\n".join(lines) + "\n", timeline


def loudness(path: Path) -> float:
    """Integrated loudness (LUFS) of an audio file."""
    r = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True)
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1])


def music_body(path: Path) -> tuple[float, float, float]:
    """Where a music track starts sounding, where it reaches its full level, and where its ending
    starts to fade (from the EBU R128 short-term loudness), for looping it without a dip."""
    with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
        subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", str(path), "-af",
                        f"ebur128=metadata=1,ametadata=print:key=lavfi.r128.S:file={tmp.name}",
                        "-f", "null", "-"], capture_output=True)
        text = Path(tmp.name).read_text()
    t = [float(x) for x in re.findall(r"pts_time:([\d.]+)", text)]
    lv = [float(x) for x in re.findall(r"lavfi.r128.S=(-?[\d.]+|-inf)", text)]
    pairs = [(a, b) for a, b in zip(t, lv) if b > -70]
    med = sorted(b for _, b in pairs)[len(pairs) // 2]
    first = max(0.0, pairs[0][0] - 0.3)                    # first sound (S reacts within a frame or two)
    body = next(a for a, b in pairs if b > med - 4) - 3.0
    end = max(a for a, b in pairs if b > med - 6)
    return first, max(first, body), end


def main() -> None:
    p = argparse.ArgumentParser(description="Concatenate silent segment renders and attach an English SRT.")
    p.add_argument("--cues", type=Path, default=CUES)
    p.add_argument("--out", type=Path, default=OUT_DIR / "full_cut.mp4")
    p.add_argument("--burn", action="store_true", help="also write *_burned.mp4 with subtitles rendered in")
    p.add_argument("--no-subs", action="store_true",
                   help="no subtitle track in the video (the .srt is still written next to it)")
    p.add_argument("--lang", default="en", help="language code in the sidecar name: <out>.<lang>.srt")
    p.add_argument("--music", type=Path, action="append", default=[],
                   help="background music under the narration: one file, or two (the second takes over "
                        "at --music-switch with a 2 s crossfade); looped if short")
    p.add_argument("--music-switch", help="segment id where the second music file takes over")
    p.add_argument("--music-lufs", type=float, default=-40.0,
                   help="loudness of the music bed (the narration sits near -16 LUFS; default -40)")
    p.add_argument("--silent", action="store_true",
                   help="ignore narrated segments and concatenate the silent renders")
    p.add_argument("--caption-band", type=float, default=0.0,
                   help="keep this fraction of the height clear at the bottom for YouTube's captions "
                        "(the picture shrinks and moves up; 0.18 fits two caption lines)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    order = [s["id"] for s in load(SCENES)["segments"]]
    audio_doc = load(AUDIO)
    videos = {s["id"]: REPO_ROOT / s["video"] for s in audio_doc["segments"]}
    mux_dir = REPO_ROOT / audio_doc.get("output_dir", "media/output")
    muxed = {s["id"]: mux_dir / (s.get("output") or f"{s['id']}_with_audio.mp4")
             for s in audio_doc["segments"]}
    cues_path = args.cues if args.cues.is_absolute() else REPO_ROOT / args.cues
    cues_by_id = {s["id"]: s.get("cues", []) for s in load(cues_path)["segments"]}

    missing = [sid for sid in order if not videos.get(sid) or not videos[sid].is_file()]
    if missing:
        sys.exit(f"Missing silent renders for: {', '.join(missing)} (run ./scripts/render_segments.py)")
    sizes = {sid: size(videos[sid]) for sid in order}
    if len(set(sizes.values())) > 1:
        sys.exit("Segments differ in frame size: " + ", ".join(f"{k}={w}x{h}" for k, (w, h) in sizes.items()))

    srt_text, timeline = build_srt(order, videos, cues_by_id)
    out = args.out if args.out.is_absolute() else REPO_ROOT / args.out
    srt_path = out.with_suffix("").with_name(f"{out.stem}.{args.lang}.srt")

    total = sum(d for _, _, d in timeline)
    print("Timeline:")
    for sid, off, dur in timeline:
        print(f"  {sid:12s} {off:7.2f}s  +{dur:6.2f}s  cues={len(cues_by_id.get(sid, []))}")
    print(f"  total        {total:7.2f}s  ({int(total // 60)}:{int(total % 60):02d})")
    if args.dry_run:
        print(srt_text[:800])
        return

    out.parent.mkdir(parents=True, exist_ok=True)
    srt_path.write_text(srt_text, encoding="utf-8")
    print(f"Wrote {srt_path.relative_to(REPO_ROOT)}")

    # Narrated segments (mux_audio.py) when every one is present and newer than its
    # silent render; otherwise the silent renders with a silent track.
    use_vo = not args.silent and all(
        muxed[sid].is_file() and muxed[sid].stat().st_mtime >= videos[sid].stat().st_mtime
        for sid in order)
    print("Audio: " + ("narration from media/output/<id>_with_audio.mp4" if use_vo
                       else "silent (no fresh muxed segments; run scripts/mux_audio.py)"))

    n = len(order)
    if use_vo:
        inputs = [x for sid in order for x in ("-i", str(muxed[sid]))]
        concat = "".join(f"[{i}:v][{i}:a]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]"
        audio_in, audio_map, sub_idx, abitrate = [], ["-map", "[a]"], n, "192k"
    else:
        inputs = [x for sid in order for x in ("-i", str(videos[sid]))]
        concat = "".join(f"[{i}:v]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v]"
        audio_in = ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono"]
        audio_map, sub_idx, abitrate = ["-map", f"{n}:a:0"], n + 1, "96k"
    channels = "1"
    music = [m if m.is_absolute() else REPO_ROOT / m for m in args.music]
    if music and use_vo:
        # every bed levelled to the same loudness, faded in at the start and out with the ending
        offs = {sid: off for sid, off, _ in timeline}
        xf, k = 2.0, n
        gains = [args.music_lufs - loudness(m) for m in music]
        loop = "aloop=loop=-1:size=2147483647"
        if len(music) == 1:
            first, body, end = music_body(music[0])
            first = max(first, body - 4.0)     # skip the soft intro: the bed is there from the first seconds
            rep_xf = 4.0
            if end - first >= total:
                chain = f";[{k}:a]atrim={first:.3f},volume={gains[0]:.2f}dB[mus]"
            else:
                # play it through to just before its fade-out, then crossfade into a second play that
                # starts where the piece is at full level (skipping its silent/soft intro): no dip, no splice
                chain = (f";[{k}:a]volume={gains[0]:.2f}dB,asplit=2[r1][r2]"
                         f";[r1]atrim={first:.3f}:{end:.3f},asetpts=PTS-STARTPTS[p1]"
                         f";[r2]atrim={body:.3f},asetpts=PTS-STARTPTS,{loop}[p2]"
                         f";[p1][p2]acrossfade=d={rep_xf}:c1=tri:c2=tri[mus]")
                print(f"Music: plays {first:.1f}-{end:.1f}s of the track, then again from {body:.1f}s "
                      f"(crossfade at {end - first - rep_xf:.1f}s of the video)")
        else:
            sw = offs[args.music_switch]
            chain = (f";[{k}:a]{loop},atrim=0:{sw + xf / 2:.3f},volume={gains[0]:.2f}dB[m1]"
                     f";[{k + 1}:a]{loop},atrim=0:{total - sw + xf / 2:.3f},volume={gains[1]:.2f}dB[m2]"
                     f";[m1][m2]acrossfade=d={xf}:c1=tri:c2=tri[mus]")
        chain += (f";[mus]aresample=44100,aformat=channel_layouts=stereo,apad,atrim=0:{total:.3f},"
                  f"afade=t=in:d=1.0,afade=t=out:st={max(0.0, total - 3):.3f}:d=3[bed]"
                  f";[a]aresample=44100,aformat=channel_layouts=stereo[vo]"
                  f";[vo][bed]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.891:level=disabled[mix]")
        concat += chain
        audio_in = [x for m in music for x in ("-i", str(m))]
        audio_map, sub_idx, channels = ["-map", "[mix]"], n + len(music), "2"
        print("Music: " + " → ".join(f"{m.name} ({g:+.1f} dB)" for m, g in zip(music, gains))
              + (f", switching at {args.music_switch} ({offs[args.music_switch]:.1f}s)" if len(music) > 1 else ""))
    vmap = "[v]"
    if args.caption_band > 0:
        w, h = next(iter(sizes.values()))
        concat += f";[v]{caption_band_filter(w, h, args.caption_band)}[vb]"
        vmap = "[vb]"
        print(f"Caption band: bottom {args.caption_band:.0%} kept clear ({caption_band_filter(w, h, args.caption_band)})")
    lang3 = {"en": "eng", "ar": "ara"}.get(args.lang, args.lang)
    subs_in, subs_map, subs_codec = ([], [], []) if args.no_subs else (
        ["-i", str(srt_path)], ["-map", f"{sub_idx}:s:0"],
        ["-c:s", "mov_text", "-metadata:s:s:0", f"language={lang3}"])
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False, dir=out.parent) as tmp:
        tmp_path = Path(tmp.name)
    try:
        subprocess.run(
            [FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *inputs, *audio_in, *subs_in,
             "-filter_complex", concat,
             "-map", vmap, *audio_map, *subs_map,
             "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
             # -t, not -shortest: the subtitle stream ends at the last cue and would cut the tail
             "-c:a", "aac", "-b:a", abitrate, "-ar", "44100", "-ac", channels, "-t", f"{total:.3f}",
             *subs_codec,
             str(tmp_path)],
            check=True,
        )
        tmp_path.replace(out)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise
    print(f"Wrote {out.relative_to(REPO_ROOT)}")

    if args.burn:
        # Letterbox the review copy and burn the subtitles into the added band.
        # The film's recurring "line" (kit.RIBBON_Y) sits low in frame; subtitles
        # overlaid on the picture would cover it for most of the runtime.
        burned = out.with_name(out.stem + "_burned.mp4")
        w, h = size(out)
        band = max(56, round(h * 0.14))
        # Style units are libass PlayRes units (PlayResY defaults to 384), not pixels:
        # libass already scales them to the output height, so these must NOT be
        # multiplied by the resolution or the type doubles at HD.
        style = "FontName=Helvetica,FontSize=17,Outline=1,Shadow=0,MarginV=6,MarginL=20,MarginR=20"
        subprocess.run(
            [FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(out),
             "-vf", f"pad={w}:{h + band}:0:0:black,subtitles={srt_path}:force_style='{style}'",
             "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "copy", "-sn",
             str(burned)],
            check=True,
        )
        print(f"Wrote {burned.relative_to(REPO_ROOT)}  ({w}x{h + band}, {band}px subtitle band)")


if __name__ == "__main__":
    main()

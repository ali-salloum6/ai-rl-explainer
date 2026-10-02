#!/usr/bin/env python3
"""
Concatenate muxed segment MP4s (narration + VO), then mix in background music.

Reads config/final_assembly.json by default. Music is looped (optional) and
mixed under the concatenated narration track for the full program length.

Optional ``music_duck``: fade the bed down before a named segment (e.g. chapter
title), hold a quieter level (``hold_gain``, default ``0`` = silence) while that
segment plays, then fade back up—see ``final_assembly.json`` / ``music_duck``.

Optional **two bed tracks**: ``music.files`` may list two files; set
``music.switch_at_segment_id`` to the segment where the **second** track should
begin (first track loops until that time on the timeline, then the second loops
for the remainder). Optional ``music.crossfade_seconds`` (default ``2``): at the
switch, track 1 fades out over that many seconds, then track 2 fades in over the
same duration—**no overlap** (sequential, not simultaneous). Optional
``music.track2_gain`` (default ``1``) attenuates/boosts only the second file.

Segment joins use ffmpeg's **filter** concat (`concat=n=…:v=1:a=1`), not the
concat *demuxer* with `-c copy`. Per-segment muxes often have **longer video
than audio** (VO shorter than the silent render); stream-copy concat can glue
AAC and H.264 on misaligned timelines so later segments sound early. Decoding
and re-concatenating fixes that.

Requires ffmpeg on PATH.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "config" / "final_assembly.json"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_manifest(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def segment_output_map(manifest: dict, repo: Path) -> dict[str, Path]:
    out_dir = repo / manifest.get("output_dir", "media/output")
    m: dict[str, Path] = {}
    for seg in manifest["segments"]:
        sid = seg["id"]
        name = seg.get("output") or f"{sid}_with_audio.mp4"
        m[sid] = out_dir / name
    return m


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def ffprobe_audio_sample_rate(path: Path) -> int:
    r = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=sample_rate",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return int(float(r.stdout.strip()))


def ffprobe_format_duration(path: Path) -> float:
    """Container duration in seconds (muxed segment length)."""
    r = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(r.stdout.strip())


def ffprobe_video_size(path: Path) -> tuple[int, int]:
    """Return (width, height) of the first video stream."""
    r = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0:s=x",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    line = r.stdout.strip()
    if "x" not in line:
        sys.exit(f"ffprobe could not read video size from {path}")
    w_s, h_s = line.split("x", 1)
    return int(w_s), int(h_s)


def music_gain_expression(
    peak: float,
    t_fo_start: float,
    t_fo_end: float,
    t_chapter_end: float,
    t_fi_end: float,
    hold: float = 0.0,
) -> str:
    """
    Piecewise linear gain for background music:
      [0, t_fo_start): peak
      [t_fo_start, t_fo_end): fade out (peak -> hold)
      [t_fo_end, t_chapter_end): hold (0 = silence; e.g. 0.2 = dimmed bed)
      [t_chapter_end, t_fi_end): fade in (hold -> peak)
      [t_fi_end, inf): peak

    Commas inside ffmpeg expressions must be escaped as \\, for filter_complex.
    """
    V = peak
    H = max(0.0, min(float(hold), float(peak)))
    T1, T2, T3, T4 = t_fo_start, t_fo_end, t_chapter_end, t_fi_end
    # if(lt(t,T1), V, if(lt(t,T2), ramp1, if(lt(t,T3), H, if(lt(t,T4), ramp2, V))))
    den_fo = max(T2 - T1, 1e-6)
    den_fi = max(T4 - T3, 1e-6)
    # Linear: V at T1 → H at T2; H at T3 → V at T4
    ramp_out = f"{H}+({V}-{H})*({T2}-t)/{den_fo}"
    ramp_in = f"{H}+({V}-{H})*(t-{T3})/{den_fi}"

    return (
        f"if(lt(t\\,{T1})\\,{V}\\,"
        f"if(lt(t\\,{T2})\\,{ramp_out}\\,"
        f"if(lt(t\\,{T3})\\,{H}\\,"
        f"if(lt(t\\,{T4})\\,{ramp_in}\\,{V}))))"
    )


def dual_music_bed_filter(
    switch_start: float,
    seg2: float,
    *,
    crossfade_seconds: float,
    track2_gain: float,
) -> str:
    """
    Build ffmpeg filter: track 1 through switch_start (fade out), track 2 after
    (fade in), mixed on one timeline. Fades are sequential—no overlap.
    """
    s = switch_start
    seg2_d = max(0.01, seg2)
    cf = max(0.0, float(crossfade_seconds))
    delay_ms = int(round(s * 1000))

    if cf <= 0:
        return (
            f"[1:a]atrim=start=0:end={s:.6f},asetpts=PTS-STARTPTS[a1];"
            f"[2:a]atrim=start=0:end={seg2_d:.6f},asetpts=PTS-STARTPTS,"
            f"volume={track2_gain},adelay={delay_ms}|{delay_ms}[a2];"
            f"[a1][a2]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[music_cat]"
        )

    fade_out_st = max(0.0, s - cf)
    fade_out_d = min(cf, s)
    return (
        f"[1:a]atrim=start=0:end={s:.6f},asetpts=PTS-STARTPTS,"
        f"afade=t=out:st={fade_out_st:.6f}:d={fade_out_d:.6f}[a1];"
        f"[2:a]atrim=start=0:end={seg2_d:.6f},asetpts=PTS-STARTPTS,"
        f"volume={track2_gain},adelay={delay_ms}|{delay_ms},"
        f"afade=t=in:st=0:d={cf:.6f}[a2];"
        f"[a1][a2]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[music_cat]"
    )


def compute_music_switch_start(
    order: list[str],
    paths: list[Path],
    segment_id: str | None,
) -> float | None:
    """Timeline seconds where ``segment_id`` starts (sum of prior muxed durations)."""
    if not segment_id or segment_id not in order:
        return None
    i = order.index(segment_id)
    return sum(ffprobe_format_duration(paths[j]) for j in range(i))


def music_gain_expression_multi(
    peak: float,
    windows: list[tuple[float, float, float, float]],
    hold: float = 0.0,
) -> str:
    """Combine multiple title-card duck windows (product of 0–1 multipliers × peak)."""
    if not windows:
        return str(peak)
    # hold is a fraction of full bed (1.0); applied per-window then scaled by peak.
    multipliers = [music_gain_expression(1.0, *w, hold=hold) for w in windows]
    product = multipliers[0]
    for m in multipliers[1:]:
        product = f"({product})*({m})"
    return f"({product})*{peak}"


def duck_hold_label(hold: float) -> str:
    """Human-readable hold phase for logs (silence vs dimmed)."""
    if hold <= 0:
        return "silent"
    return f"dimmed×{hold:g}"


def duck_segment_ids(duck_cfg: dict) -> list[str]:
    ids = duck_cfg.get("segment_ids")
    if ids:
        return [s for s in ids if s]
    sid = duck_cfg.get("segment_id")
    return [sid] if sid else []


def compute_music_duck_times_for_segment(
    order: list[str],
    paths: list[Path],
    sid: str,
    duck_cfg: dict,
) -> tuple[float, float, float, float] | None:
    """Duck window for one segment id on the final timeline."""
    if sid not in order:
        return None
    fo = max(float(duck_cfg.get("fade_out_seconds", 1.0)), 0.05)
    fi = max(float(duck_cfg.get("fade_in_seconds", 1.0)), 0.05)
    lead = max(float(duck_cfg.get("lead_seconds", 0.0)), 0.0)

    durs = [ffprobe_format_duration(p) for p in paths]
    i = order.index(sid)
    t_chapter_start = sum(durs[:i])
    d_chapter = durs[i]
    t_chapter_end = t_chapter_start + d_chapter

    t_fo_end = t_chapter_start - lead
    t_fo_start = t_chapter_start - fo - lead
    t_fo_start = max(0.0, t_fo_start)
    if t_fo_end <= t_fo_start:
        t_fo_end = t_fo_start + fo
    t_fi_end = t_chapter_end + fi
    return (t_fo_start, t_fo_end, t_chapter_end, t_fi_end)


def compute_music_duck_windows(
    order: list[str],
    paths: list[Path],
    duck_cfg: dict,
) -> list[tuple[float, float, float, float]]:
    windows: list[tuple[float, float, float, float]] = []
    for sid in duck_segment_ids(duck_cfg):
        w = compute_music_duck_times_for_segment(order, paths, sid, duck_cfg)
        if w is not None:
            windows.append(w)
    return windows


def compute_music_duck_times(
    order: list[str],
    paths: list[Path],
    duck_cfg: dict,
) -> tuple[float, float, float, float] | None:
    """Legacy single-segment duck window (first id in config)."""
    windows = compute_music_duck_windows(order, paths, duck_cfg)
    return windows[0] if windows else None


def concat_filter_complex(num_segments: int) -> str:
    """Single-timeline concat of aligned video+audio (fixes AAC drift vs `concat -c copy`)."""
    parts = "".join(f"[{i}:v][{i}:a]" for i in range(num_segments))
    return f"{parts}concat=n={num_segments}:v=1:a=1[v][a]"


def main() -> None:
    p = argparse.ArgumentParser(
        description="Concat muxed segments and mix background music (final_assembly.json)"
    )
    p.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Path to final_assembly.json",
    )
    p.add_argument("--dry-run", action="store_true")
    p.add_argument(
        "--keep-intermediate",
        action="store_true",
        help="Keep narration-only concat next to output as *_narration_only.mp4",
    )
    args = p.parse_args()

    cfg_path = args.config if args.config.is_absolute() else REPO_ROOT / args.config
    cfg = load_json(cfg_path)

    man_rel = Path(cfg["narration_manifest"])
    man_path = man_rel if man_rel.is_absolute() else REPO_ROOT / man_rel
    manifest = load_manifest(man_path)
    out_map = segment_output_map(manifest, REPO_ROOT)

    order: list[str] = cfg["segment_order"]
    segment_paths: list[Path] = []
    for sid in order:
        if sid not in out_map:
            sys.exit(f"Unknown segment id {sid!r} (not in {man_path})")
        sp = out_map[sid]
        if not sp.is_file():
            sys.exit(f"Missing muxed segment (run mux_audio first): {sp}")
        segment_paths.append(sp)

    rates = [ffprobe_audio_sample_rate(p) for p in segment_paths]
    if len(set(rates)) > 1:
        detail = ", ".join(f"{p.name}={r}Hz" for p, r in zip(segment_paths, rates))
        sys.exit(
            "Refusing concat: muxed segments use different audio sample rates "
            f"({detail}). ffmpeg -c copy would glue mismatched AAC timelines and "
            "later segments sound pitch-shifted in the final mix. Re-run: "
            "`python3 scripts/mux_audio.py` after setting ffmpeg.audio_sample_rate "
            "in config/audio_manifest.json (44100 recommended to match typical music beds)."
        )

    sizes = [ffprobe_video_size(p) for p in segment_paths]
    if len(set(sizes)) > 1:
        detail = ", ".join(f"{p.name}={w}x{h}" for p, (w, h) in zip(segment_paths, sizes))
        sys.exit(
            "Refusing concat: muxed segments use different video frame sizes "
            f"({detail}). ffmpeg concat with -c copy cannot splice mismatched H.264 "
            "dimensions; players often freeze the last good frame while audio continues. "
            "Re-render every silent segment at the same resolution (e.g. ./scripts/render_all.sh "
            "or manimgl … -w --hd for 1920×1080) then re-run mux_audio.py on all segments."
        )

    out_rel = Path(cfg["output"])
    final_out = out_rel if out_rel.is_absolute() else REPO_ROOT / out_rel
    final_out.parent.mkdir(parents=True, exist_ok=True)

    music_cfg = cfg.get("music", {})
    files = music_cfg.get("files") or []
    if not files:
        sys.exit("final_assembly.json: music.files must list at least one audio file")
    music_path_a = REPO_ROOT / Path(files[0])
    if not music_path_a.is_file():
        sys.exit(f"Missing music file: {music_path_a}")
    music_path_b: Path | None = None
    if len(files) > 1:
        music_path_b = REPO_ROOT / Path(files[1])
        if not music_path_b.is_file():
            sys.exit(f"Missing second music file: {music_path_b}")

    switch_at = music_cfg.get("switch_at_segment_id")
    switch_start: float | None = None
    use_dual_music = music_path_b is not None and switch_at
    if len(files) > 1 and not switch_at:
        sys.exit(
            "final_assembly.json: music.files lists multiple tracks; add "
            'music.switch_at_segment_id (e.g. "bit7") so assembly knows when '
            "to switch to the second file."
        )
    if use_dual_music:
        switch_start = compute_music_switch_start(order, segment_paths, switch_at)
        if switch_start is None:
            sys.exit(
                f"music.switch_at_segment_id={switch_at!r} is not in segment_order."
            )

    volume = float(music_cfg.get("volume", 0.12))
    track2_gain = float(music_cfg.get("track2_gain", 1.0))
    crossfade_seconds = float(music_cfg.get("crossfade_seconds", 2.0))
    loop_music = bool(music_cfg.get("loop", True))
    ff = cfg.get("ffmpeg", {})
    acodec = ff.get("audio_codec", "aac")
    abitrate = ff.get("audio_bitrate", "192k")
    # Match silent/mux pipeline so the narration pass does not re-invent quality.
    man_ff = manifest.get("ffmpeg", {})
    vcodec = man_ff.get("video_codec", "libx264")
    vpreset = man_ff.get("video_preset", "fast")
    vcrf = str(man_ff.get("video_crf", 18))

    out_dir = final_out.parent
    narration_only = out_dir / "._narration_concat.mp4"

    duck_cfg = cfg.get("music_duck") or {}
    duck_windows: list[tuple[float, float, float, float]] = []
    # Fraction of full bed during chapter titles (0 = silence; 0.2 = dimmed).
    duck_hold = max(0.0, min(float(duck_cfg.get("hold_gain", 0.0)), 1.0))
    if duck_cfg.get("enabled", True) and duck_segment_ids(duck_cfg):
        duck_windows = compute_music_duck_windows(order, segment_paths, duck_cfg)

    if args.dry_run:
        print("[dry-run] segments:", *[str(x) for x in segment_paths], sep="\n  ")
        print("[dry-run] music:", music_path_a)
        if music_path_b:
            print("[dry-run] music (track 2):", music_path_b)
            print("[dry-run] music switch at segment:", switch_at, "→", switch_start)
        print("[dry-run] music volume:", volume)
        if use_dual_music:
            print("[dry-run] track2_gain (second bed multiplier):", track2_gain)
            print("[dry-run] crossfade_seconds (no overlap):", crossfade_seconds)
        if duck_windows:
            hold_lbl = duck_hold_label(duck_hold)
            for i, (t1, t2, t3, t4) in enumerate(duck_windows):
                print(
                    f"[dry-run] music_duck[{i}]: fade out "
                    f"[{t1:.2f}s–{t2:.2f}s], {hold_lbl} [{t2:.2f}s–{t3:.2f}s], "
                    f"fade in [{t3:.2f}s–{t4:.2f}s]"
                )
        print("[dry-run] ->", final_out)
        return

    n_seg = len(segment_paths)
    narr_cmd: list[str] = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        *[x for p in segment_paths for x in ("-i", str(p))],
        "-filter_complex",
        concat_filter_complex(n_seg),
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-c:v",
        vcodec,
        "-preset",
        vpreset,
        "-crf",
        vcrf,
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        acodec,
        "-b:a",
        abitrate,
        "-ar",
        str(rates[0]),
        "-ac",
        "1",
        str(narration_only),
    ]
    try:
        run(narr_cmd)
    except subprocess.CalledProcessError:
        narration_only.unlink(missing_ok=True)
        sys.exit(
            "ffmpeg filter concat failed (see stderr). Re-mux segments with matching "
            "codecs/rates, or re-run `python3 scripts/mux_audio.py` for all ids."
        )

    total_prog = ffprobe_format_duration(narration_only)

    # Mix narration + background bed(s); output length = video length
    loop_args_a: list[str] = ["-stream_loop", "-1"] if loop_music else []
    loop_args_b: list[str] = ["-stream_loop", "-1"] if loop_music else []

    if use_dual_music:
        assert switch_start is not None and music_path_b is not None
        seg2 = max(0.01, total_prog - switch_start)
        if switch_start <= 0:
            sys.exit("music switch time must be > 0 when using two tracks.")
        fc_concat = dual_music_bed_filter(
            switch_start,
            seg2,
            crossfade_seconds=crossfade_seconds,
            track2_gain=track2_gain,
        )
        if duck_windows:
            expr = music_gain_expression_multi(volume, duck_windows, hold=duck_hold)
            fc = (
                fc_concat + ";"
                f"[music_cat]volume=volume='{expr}':eval=frame[bg];"
                f"[0:a][bg]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]"
            )
            hold_lbl = duck_hold_label(duck_hold)
            for i, (t1, t2, t3, t4) in enumerate(duck_windows):
                print(
                    f"Music duck[{i}]: fade out "
                    f"[{t1:.2f}s–{t2:.2f}s], {hold_lbl} [{t2:.2f}s–{t3:.2f}s], "
                    f"fade in [{t3:.2f}s–{t4:.2f}s]",
                    flush=True,
                )
        else:
            fc = (
                fc_concat + ";"
                f"[music_cat]volume={volume}[bg];"
                f"[0:a][bg]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]"
            )

        cf = max(0.0, crossfade_seconds)
        print(
            f"Music tracks: track1 → {switch_start:.2f}s, "
            f"track2 → {seg2:.2f}s (from segment {switch_at}), "
            f"track2_gain={track2_gain}, "
            f"crossfade={cf:.2f}s (sequential, no overlap)",
            flush=True,
        )

        ffmpeg_inputs: list[str | Path] = [
            "-i",
            str(narration_only),
            *loop_args_a,
            "-i",
            str(music_path_a),
            *loop_args_b,
            "-i",
            str(music_path_b),
        ]
    else:
        if duck_windows:
            expr = music_gain_expression_multi(volume, duck_windows, hold=duck_hold)
            fc = (
                f"[1:a]volume=volume='{expr}':eval=frame[bg];"
                f"[0:a][bg]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]"
            )
            hold_lbl = duck_hold_label(duck_hold)
            for i, (t1, t2, t3, t4) in enumerate(duck_windows):
                print(
                    f"Music duck[{i}]: fade out "
                    f"[{t1:.2f}s–{t2:.2f}s], {hold_lbl} [{t2:.2f}s–{t3:.2f}s], "
                    f"fade in [{t3:.2f}s–{t4:.2f}s]",
                    flush=True,
                )
        else:
            fc = (
                f"[1:a]volume={volume}[bg];"
                f"[0:a][bg]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]"
            )
        ffmpeg_inputs = ["-i", str(narration_only), *loop_args_a, "-i", str(music_path_a)]

    with tempfile.NamedTemporaryFile(
        suffix=".mp4", delete=False, dir=out_dir
    ) as tmp:
        tmp_path = Path(tmp.name)
    try:
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                *ffmpeg_inputs,
                "-filter_complex",
                fc,
                "-map",
                "0:v:0",
                "-map",
                "[aout]",
                "-c:v",
                "copy",
                "-c:a",
                acodec,
                "-b:a",
                abitrate,
                str(tmp_path),
            ]
        )
        tmp_path.replace(final_out)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise
    finally:
        if args.keep_intermediate:
            kept = final_out.with_name(final_out.stem + "_narration_only.mp4")
            narration_only.replace(kept)
            print(f"Kept narration-only concat: {kept}")
        else:
            narration_only.unlink(missing_ok=True)

    print(f"Wrote {final_out}")


if __name__ == "__main__":
    main()

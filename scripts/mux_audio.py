#!/usr/bin/env python3
"""
Mux narration onto rendered scene videos using config/audio_manifest.json.

Strategies:
  longest   — omit ffmpeg -shortest; mux runs to the longer stream (default). Shorter
              audio leaves silent tail or shorter video may freeze/EOF depending on ffmpeg.
  shortest  — pass ffmpeg -shortest; output length = min(audio, video); trims the longer.

Optional segment field ``audio_concat``: list of repo-relative WAV (or FFmpeg-readable)
paths. Those files are concatenated in order via ffmpeg ``concat`` filter (normalized
mono at ``ffmpeg.audio_sample_rate``). Use this for one video that spans multiple takes
without merging files by hand—omit ``audio`` when ``audio_concat`` is set.

Set ``no_vo``: true (and omit ``audio``) for segments with no narration: mux adds a
silent mono AAC track matching the video length (e.g. chapter title cards).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = REPO_ROOT / "config" / "audio_manifest.json"


def load_manifest(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def outp_dir_for_temp(repo: Path) -> Path:
    d = repo / "media" / "output"
    d.mkdir(parents=True, exist_ok=True)
    return d


def ffmpeg_concat_audios(paths: list[Path], outp: Path, *, sample_rate: int) -> None:
    outp.parent.mkdir(parents=True, exist_ok=True)
    if not paths:
        raise ValueError("ffmpeg_concat_audios needs at least one path")

    if len(paths) == 1:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(paths[0]),
                "-ac",
                "1",
                "-ar",
                str(int(sample_rate)),
                str(outp),
            ],
            check=True,
        )
        return

    n = len(paths)
    inp_args: list[str] = []
    for p in paths:
        inp_args.extend(["-i", str(p)])
    graphs = ";".join(
        f"[{k}:a]aresample={int(sample_rate)},aformat=sample_fmts=fltp[a{k}]"
        for k in range(n)
    )
    concat_in = "".join(f"[a{k}]" for k in range(n))
    filt = f"{graphs};{concat_in}concat=n={n}:v=0:a=1[out]"

    cmd = (
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
        + inp_args
        + [
            "-filter_complex",
            filt,
            "-map",
            "[out]",
            "-ac",
            "1",
            "-ar",
            str(int(sample_rate)),
            str(outp),
        ]
    )
    subprocess.run(cmd, check=True)


def resolve_concat_audio(
    repo: Path, seg: dict, *, sample_rate: int
) -> tuple[Optional[Path], Path]:
    """
    Build optional temp WAV concat; return ``(unlink_me, ffmpeg_audio_input)``
    ``unlink_me`` is the temp path iff ``audio_concat`` was used.
    """
    rels = seg.get("audio_concat")
    if rels is not None:
        if seg.get("audio"):
            raise ValueError(
                f"segment {seg.get('id')!r}: set only one of audio, audio_concat"
            )
        paths = [(repo / r).resolve() for r in rels]
        for p in paths:
            if not p.is_file():
                raise FileNotFoundError(f"missing concat audio source: {p}")
        outp_f = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav",
            prefix=f"mux_concat_{seg.get('id', 'segment')}_",
            dir=str(outp_dir_for_temp(repo)),
        )
        outp = Path(outp_f.name)
        outp_f.close()
        ffmpeg_concat_audios(paths, outp, sample_rate=sample_rate)
        return outp, outp

    if seg.get("no_vo"):
        if seg.get("audio") or seg.get("audio_concat"):
            raise ValueError(
                f"segment {seg.get('id')!r}: no_vo cannot be combined with audio"
            )
        return None, Path()

    if not seg.get("audio"):
        raise ValueError(
            f"segment {seg.get('id')!r}: missing audio "
            "(or use audio_concat, or no_vo: true)"
        )
    return None, repo / seg["audio"]


def mux_input_paths(repo: Path, seg: dict) -> list[Path]:
    """Video + narration sources that should trigger a remux when newer than output."""
    paths = [repo / seg["video"]]
    if seg.get("no_vo"):
        return paths
    if seg.get("audio_concat"):
        paths.extend(repo / p for p in seg["audio_concat"])
    elif seg.get("audio"):
        paths.append(repo / seg["audio"])
    return paths


def mux_needs_update(repo: Path, seg: dict, out_path: Path) -> tuple[bool, str]:
    if not out_path.is_file():
        return True, "missing muxed output"
    out_mtime = out_path.stat().st_mtime
    for path in mux_input_paths(repo, seg):
        if not path.is_file():
            return True, f"missing input: {path.relative_to(repo)}"
        if path.stat().st_mtime > out_mtime:
            return True, f"newer input: {path.relative_to(repo)}"
    return False, "up to date"


def mux_silent(
    repo: Path,
    seg: dict,
    out_dir: Path,
    ff: dict,
    *,
    dry_run: bool,
) -> Path:
    """Attach silent mono AAC to a video-only segment (no narration)."""
    vid = repo / seg["video"]
    out_name = seg.get("output") or f"{seg['id']}_with_audio.mp4"
    out_path = out_dir / out_name
    sample_rate = int(ff.get("audio_sample_rate", 44100))
    channels = int(ff.get("audio_channels", 1))
    ch_layout = "mono" if channels == 1 else "stereo"

    if not vid.is_file():
        raise FileNotFoundError(f"Missing video: {vid}")

    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(vid),
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r={sample_rate}:cl={ch_layout}",
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        ff.get("video_codec", "libx264"),
        "-preset",
        ff.get("video_preset", "fast"),
        "-crf",
        str(ff.get("video_crf", 18)),
        "-c:a",
        ff.get("audio_codec", "aac"),
        "-b:a",
        ff.get("audio_bitrate", "192k"),
        "-ar",
        str(sample_rate),
        "-ac",
        str(channels),
        "-shortest",
    ]

    if dry_run:
        print("[dry-run]", " ".join(cmd), str(out_path))
        return out_path

    with tempfile.NamedTemporaryFile(
        suffix=".mp4", delete=False, dir=out_dir
    ) as tmp:
        tmp_path = Path(tmp.name)
    try:
        subprocess.run(cmd + [str(tmp_path)], check=True)
        tmp_path.replace(out_path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise
    return out_path


def mux_one(
    repo: Path,
    seg: dict,
    out_dir: Path,
    ff: dict,
    *,
    dry_run: bool,
) -> Path:
    if seg.get("no_vo"):
        return mux_silent(repo, seg, out_dir, ff, dry_run=dry_run)

    vid = repo / seg["video"]
    sample_rate_default = ff.get("audio_sample_rate", 44100)
    unlink_audio_tmp, aud = resolve_concat_audio(
        repo, seg, sample_rate=int(sample_rate_default)
    )

    out_name = seg.get("output") or f"{seg['id']}_with_audio.mp4"
    out_path = out_dir / out_name
    strategy = seg.get("strategy", "longest")

    if not vid.is_file():
        raise FileNotFoundError(f"Missing video: {vid}")
    if not aud.is_file():
        raise FileNotFoundError(f"Missing audio: {aud}")

    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(aud),
        "-i",
        str(vid),
        "-map",
        "1:v:0",
        "-map",
        "0:a:0",
        "-c:v",
        ff.get("video_codec", "libx264"),
        "-preset",
        ff.get("video_preset", "fast"),
        "-crf",
        str(ff.get("video_crf", 18)),
        "-c:a",
        ff.get("audio_codec", "aac"),
        "-b:a",
        ff.get("audio_bitrate", "192k"),
    ]
    # Unify sample rate + channel layout across segments so ffmpeg concat -c copy
    # does not glue 44.1k + 48k AAC into one timeline (bit2 would sound pitch-shifted
    # / "anonymized" in the final mix). Match music bed (44100) for assemble_final.
    ar = ff.get("audio_sample_rate")
    if ar is not None:
        cmd.extend(["-ar", str(int(ar))])
    ac = ff.get("audio_channels")
    if ac is not None:
        cmd.extend(["-ac", str(int(ac))])
    if strategy == "shortest":
        cmd.append("-shortest")
    elif strategy == "longest":
        pass  # default mux: do not pass -shortest
    else:
        raise ValueError(f"Unknown strategy {strategy!r} (supported: longest, shortest)")

    if dry_run:
        print("[dry-run]", " ".join(cmd), str(out_path))
        if unlink_audio_tmp is not None and unlink_audio_tmp.exists():
            unlink_audio_tmp.unlink(missing_ok=True)
        return out_path

    with tempfile.NamedTemporaryFile(
        suffix=".mp4", delete=False, dir=out_dir
    ) as tmp:
        tmp_path = Path(tmp.name)
    try:
        subprocess.run(cmd + [str(tmp_path)], check=True)
        tmp_path.replace(out_path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise
    finally:
        if unlink_audio_tmp is not None and unlink_audio_tmp.exists():
            unlink_audio_tmp.unlink(missing_ok=True)
    return out_path


def main() -> None:
    p = argparse.ArgumentParser(
        description="Mux narration audio onto silent MP4 per audio_manifest.json "
        "(WAV/M4A/…). Set ffmpeg.audio_sample_rate so all segments match for final concat."
    )
    p.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Path to manifest (default: config/audio_manifest.json)",
    )
    p.add_argument(
        "--segment",
        action="append",
        dest="segments",
        metavar="ID",
        help="Only process segment id(s); repeatable",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Remux even when the muxed output is newer than video and audio",
    )
    p.add_argument(
        "--stale",
        action="store_true",
        help=argparse.SUPPRESS,  # deprecated no-op; skip-up-to-date is now default
    )
    p.add_argument("--dry-run", action="store_true", help="Print ffmpeg commands only")
    args = p.parse_args()

    manifest_path = args.manifest if args.manifest.is_absolute() else REPO_ROOT / args.manifest
    data = load_manifest(manifest_path)
    out_dir = REPO_ROOT / data.get("output_dir", "media/output")
    ff = data.get("ffmpeg", {})
    segments = data["segments"]
    if args.segments:
        wanted = set(args.segments)
        segments = [s for s in segments if s.get("id") in wanted]
        if not segments:
            sys.exit(f"No matching segment id in {manifest_path}")

    muxed = skipped = 0
    for seg in segments:
        out_name = seg.get("output") or f"{seg['id']}_with_audio.mp4"
        out_path = out_dir / out_name
        needs, reason = mux_needs_update(REPO_ROOT, seg, out_path)
        if not args.force and not needs:
            print(f"skip {seg['id']}: {reason}")
            skipped += 1
            continue
        print(f"mux {seg['id']}: {reason if needs else 'forced'}")
        out = mux_one(REPO_ROOT, seg, out_dir, ff, dry_run=args.dry_run)
        if not args.dry_run:
            print(f"Wrote {out}")
        muxed += 1

    print(f"Done: muxed {muxed}, skipped {skipped}")


if __name__ == "__main__":
    main()

# Video production instructions

**Agents: treat this file as your system prompt for work in this repo.** Read it at the start of a session when building scenes, changing the script map, rendering, or muxing. Overview: [`README.md`](../README.md). Checklist: [`ADDING_SEGMENTS.md`](ADDING_SEGMENTS.md).

## Lineage

Process copied from video 2 ([`../../ai-image-explainer/docs/instructions.md`](../../ai-image-explainer/docs/instructions.md)), which copied it from video 1 ([`../../1-hour-challenge/docs/instructions.md`](../../1-hour-challenge/docs/instructions.md)).

Keep this file aligned with those siblings when changing hard rules. Topic-specific plan: [`rl_plan.md`](rl_plan.md). Launch lessons to respect: [`../../1-hour-challenge/docs/launch_analytics_notes.md`](../../1-hour-challenge/docs/launch_analytics_notes.md).

## Docs for agent work


| File | Role |
| ---- | ---- |
| **`docs/instructions.md`** (this file) | Agent system prompt: roles, bit workflow, render/mux |
| **`docs/script_visual_map.md`** | **Contract** — Arabic lines ↔ on-screen beats |
| **`docs/context.md`** | Goals, sibling cite, no Pi creatures |
| **`docs/ADDING_SEGMENTS.md`** | Short “next bit” checklist |
| **`docs/rl_plan.md`** | Structure, story facts, accuracy guardrails, packaging (not locked) |
| **`docs/arabic_script.md`** | Arabic line candidates + Ali's decisions → `config/narration_ar.json` |
| **`docs/to_do.md`** | Human scratchpad |
| **`README.md`** | Layout + setup |


Do not invent parallel process docs. Lasting process → here; beat-level content → visual map.

## Roles

- **Ali** writes the **Arabic script** (and records VO). Owns wording, pacing intent, and **approval** of the animation plan.
- **The agent** owns **Manim code**, manifests, render/mux tooling, and proposes the **visual / animation description** in the map.

`docs/script_visual_map.md` is the contract. Do not invent labels or numbers outside it (or an explicit Ali decision written into the map).

## Bit workflow (mandatory)

1. **Ali writes the Arabic paragraph** into `script_visual_map.md` (**before recording VO**).
2. **Agent proposes the animation** in the same map row (and/or chat). **No Manim yet.**
3. **Ali marks the visual plan approved** (“approved”, “LGTM”, “go build”).
4. **Only then** write/update `our_scenes/…`, manifests, and renders.
5. After a useful preview render, export **~8–12 keyframes** to `keyframes/<segment_id>/`.
6. **Then** Ali records VO when the picture is stable; mux; assemble when needed.

**Do not** jump from a new Arabic paragraph straight into Manim. **Do not** code a new bit before approval.

When Ali pastes Arabic without a visual plan, the agent’s first response is the proposed beats — not scene code.

## Keyframes

- Destination: `keyframes/<segment_id>/`
- ~**8–12** frames across the beat
- Helper: `python3 scripts/export_keyframes.py --segment <id>`

Keyframes are gitignored local review artifacts.

## Script vs on-screen text

Spoken script is **reference** for pacing and what to illustrate. Do **not** paste long narration as on-screen paragraphs by default.

## Words on screen

- Prefer motion and diagrams.
- Short labels OK for technical terms or diagram parts. Keep minimal.

## Rendering (ManimGL)

Venv + `pip install -e ./manim` and `pip install -r manim/requirements.txt` (see README).

### Default quality

**Unless Ali asks for HD / production, use preview:**

- Single: `manimgl our_scenes/<file>.py <SceneName> -w -l --video_dir ./media`
- Batch: `./scripts/render_all.sh`

**Always mux** when VO exists for that segment — silent MP4 alone is not the review deliverable.

**HD only when Ali asks:** `--hd` / `MANIM_HD=1` / `./scripts/render_and_build.sh`.

### Incremental (skip up-to-date)

Default: skip fresh outputs. `--force` rebuilds.

```bash
./scripts/render_segments.py --segment bit1
python3 scripts/mux_audio.py --segment bit1
./scripts/render_and_build.sh          # HD path when asked
./scripts/render_and_build.sh --force
```

Register segments in `config/scenes_manifest.json` and `config/audio_manifest.json`. Same frame size for all segments in one assemble run.

**Render segments in order.** Each segment opens on the previous one's exact last frame and dissolves into its own (`continue_from`), so the cuts are seamless; `render_segments.py` saves every render's last frame to `media/frames/` for the next one. After changing a segment, re-render it and the one after it.

### Visual verification

Render preview → keyframes → **look at PNGs** → fix → repeat. Mux when VO exists.

## Arabic text (Amiri)

```python
from pathlib import Path
from manimlib.mobject.svg.text_mobject import register_font

with register_font(str(Path(__file__).resolve().parent.parent / "assets/fonts/Amiri-Regular.ttf")):
    label = Text("رسم", font="Amiri", font_size=48, disable_ligatures=False)
```

## Audio + picture

`config/audio_manifest.json`: each segment ties silent MP4 + WAV/M4A → `media/output/<id>_with_audio.mp4`.

- Default strategy `longest`; optional `shortest`.
- Keep `ffmpeg.audio_sample_rate` (e.g. 44100) and channels consistent across segments.
- `python3 scripts/mux_audio.py` / `--segment <id>` / `--dry-run`

## Full program

`config/final_assembly.json`: `segment_order` + `music` → `media/output/final_with_music.mp4`.

- `./scripts/build_final.sh` — mux stale + assemble  
- `python3 scripts/assemble_final.py` — assemble only  
- `--dry-run` / `--keep-intermediate` as in video 1

## Voice pipeline (as used for video 2)

1. `config/narration.json`: one entry per spoken line (`key`, English text, `pause`). Scenes are `NarratedScene`s and play each line inside `with self.narrate(key):`, so timing follows the voice.
2. Placeholder voice: `python3 scripts/narrate.py synth` (English AI voice, `VO_LANG=en`), render, then `python3 scripts/narrate.py track` and `python3 scripts/build_srt_cut.py --cues config/cues_en_vo.json --burn` for the review cut.
3. Arabic: candidates and decisions in `docs/arabic_script.md` → `python3 scripts/build_narration_ar.py` → `config/narration_ar.json`. Ali decides in the recorder's Decide mode (step 4) or by hand after **Decision:**; both write the same file. A decision that reads like an instruction shows as "needs a look" and goes in the builder's `OVERRIDES` by hand.
4. Decide and record: `python3 scripts/record_server.py`, open http://localhost:8765 (also in `.claude/launch.json`). Decide mode: pick an option, change a few of its letters first, write your own wording, or remove the line. Record mode: one line at a time; every take is kept.
5. `scripts/enhance_takes.py` (Adobe Enhance Speech, one by one) → `scripts/process_takes.py` (trim, pauses, loudness) → re-render with `VO_LANG=ar` (default) → `narrate.py track` → mux.
6. Upload cut with the music bed and the bottom band clear for YouTube captions: `build_srt_cut.py --cues config/cues_ar_vo.json --caption-band 0.20` (see its docstring).

**Placeholder Arabic voice (video 4, before Ali records).** `scripts/voice_ar_tts.py` voices every ready line with an offline TTS into `media/audio/lines_ar/tts/` (cleaned like a recorded take, its own index), render with `VO_LANG=ar_tts`, then `narrate.py track --lang ar_tts` writes the same `<id>-vo-ar.wav` files and `cues_ar_vo.json` that Ali's takes will replace. Nothing in his recording path reads or writes the placeholder. It is for timing and review only: never publish with it (the upload checklist declares the voice as Ali's own).

**Headless (cloud) rendering.** ManimGL needs an OpenGL display; `render_segments.py` runs it inside `xvfb-run` when there is no `$DISPLAY`. A one-off render: `xvfb-run -a .venv/bin/manimgl our_scenes/<file>.py <Scene> -w -l --video_dir ./media`. A still: add `-s` *with* `-w` (`-s` alone opens a window and waits).

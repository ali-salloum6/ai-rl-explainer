# Adding the next scene + VO (checklist)

Short workflow. Full agent rules: [`instructions.md`](instructions.md).  
Same checklist pattern as [`../../1-hour-challenge/docs/ADDING_SEGMENTS.md`](../../1-hour-challenge/docs/ADDING_SEGMENTS.md).

## Naming

| Segment `id` | Typical VO | Muxed output |
| ------------ | ---------- | ------------ |
| `hook` | `media/audio/hook-vo.wav` | `hook_with_audio.mp4` |
| `bit1`, `bit2`, … | `media/audio/bit1-vo.wav`, … | `bit1_with_audio.mp4`, … |

Keep `id`, VO stem, and output aligned.

## 1. Script (Arabic) — before recording

Add the paragraph to [`script_visual_map.md`](script_visual_map.md). Do **not** record VO yet.

## 2. Animation plan — propose, Ali approves

Agent writes the visual beat. **Stop until approved.** Then Manim.

## 3. Manim scene

- Code under `our_scenes/`
- Preview: `manimgl our_scenes/<file>.py <Scene> -w -l --video_dir ./media` (HD only when asked)
- Or: `./scripts/render_segments.py --segment <id>`
- Keyframes: `python3 scripts/export_keyframes.py --segment <id>`

## 4. Voice

Export WAV to the manifest path once the picture is stable enough.

## 5. Manifests + mux

1. Append row in `config/audio_manifest.json`
2. Append `id` to `segment_order` in `config/final_assembly.json`
3. Append row in `config/scenes_manifest.json` (`scene`: `path:ClassName`)
4. `python3 scripts/mux_audio.py --segment <id>`

## 6. Full program

`./scripts/build_final.sh` or `./scripts/render_and_build.sh` (HD when asked).

## 7. Review

Silent `media/<Scene>.mp4` · keyframes · `media/output/<id>_with_audio.mp4` · `final_with_music.mp4`

# Start here (video 4, ai-rl-explainer): state on 10 Oct 2026

One page for a fresh session. **On 10 Oct Ali asked for the whole video end to end** ("do your research for what would maximize watch hours … write the script and the code, and get the final video with the lines"), so it was built: research, script, scenes, a placeholder Arabic voice and the cut. **What's left is Ali's:** review, re-decide any line, record his voice, publish.

## Where things stand

- **Topic:** how AI is trained with rewards (reinforcement learning), and why that makes it cheat: «كيف الذكاء الاصطناعي بيتعلّم يغشّ؟». It answers video 3's closing question («كيف بتدرّب آلة بزر اللايك؟») word for word in bit 3.
- **Research (10 Oct):** what maximizes watch hours, with sources and the decisions it drove: [`watch_time_research.md`](watch_time_research.md). Headline: average view duration has stayed ~70 s whatever the length, so the first minute decides; the video opens on motion, keeps one open loop, chains the bits by "but / therefore", ends on content.
- **Facts (re-checked 10 Oct):** [`rl_research.md`](rl_research.md). Corrected: DeepSeek **R1-Zero** (not R1), the CAPTCHA model was pre-release and the researchers suggested the gig site, 3.7 Sonnet's card documents editing tests, the robot hand is back.
- **Script:** 56 lines in Syrian Arabic, each with two options, ★ decided by Claude: [`arabic_script.md`](arabic_script.md); the English and the pauses: `config/narration.json`; line ↔ picture: [`script_visual_map.md`](script_visual_map.md).
- **Scenes:** seven, in `our_scenes/` (`hook_boat.py` … `bit6_recap.py`) on `rl_kit.py`. The maze and the coin are real REINFORCE runs, seeded.
- **The cut:** rendered with a **placeholder** Arabic voice (offline XTTS, a Damascene voice from the Arabic Speech Corpus) so the timing and the review are real: **7:05**, 1080p, in `media/output/` (`full_cut_ar.mp4`, the upload shape; `full_cut_ar_subtitled.mp4`, the same with the lines burned in, was sent in the chat because `media/` isn't committed). **Never publish with it**: re-record (below) and rebuild.
- **Packaging:** title, thumbnails A/B/C, description, tags, pinned comment, schedule and upload checklist: [`youtube/publish_pack.md`](youtube/publish_pack.md).

## What Ali does next

1. **Watch the review cut** (sent in the chat; rebuilt by the commands below) and mark changes per row in `script_visual_map.md`, or just say them.
2. **Re-decide lines** in the recorder's Decide mode (`python3 scripts/record_server.py`, http://localhost:8765); every line is ★ now.
3. **Record** in Record mode, then `scripts/enhance_takes.py` → `scripts/process_takes.py`.
4. **Rebuild with his voice** (the scenes re-time themselves):

   ```bash
   VO_LANG=ar MANIM_HD=1 .venv/bin/python scripts/render_segments.py --force
   .venv/bin/python scripts/narrate.py track --lang ar
   .venv/bin/python scripts/mux_audio.py --force
   .venv/bin/python scripts/build_srt_cut.py --cues config/cues_ar_vo.json --out media/output/full_cut_ar.mp4 \
       --no-subs --lang ar --music "media/music/No.10 _A New Beginning - Esther Abrami.mp3" --music-lufs -38 --caption-band 0.20
   .venv/bin/python scripts/srt_en.py --voice ar
   .venv/bin/python scripts/chapters.py --write   # chapters into description.txt; prints the length and the card time
   ```

5. **Open the primary sources** in `rl_research.md` §6 (15 minutes; the sandbox couldn't reach them).
6. **Publish** with `youtube/publish_pack.md` (checklist, schedule, first-hour share list).

## Length

The research set **~6:00** (`watch_time_research.md` §2, decision 6); the placeholder cut runs **7:05**. Speech is 379 s of it at about 11 characters a second (XTTS sped up 1.1×), plus 37 s of planned pauses and the 9 s end-screen hold. The maze arrives at 0:44, later than the ~0:30 of decision 3, and not only because of the pace: the hook's six lines (472 characters as written, more with the numbers said in words) take ~40 s with their pauses even at a brisk 13 characters a second. To bring the maze earlier, shorten `hook.3` first («وبيخبط بالقوارب، وماشي بالعكس»), not the title question or the open loop. Ali's pace decides the rest: `scripts/chapters.py` prints the length after his rebuild. If it still runs past ~6:30, the side examples are the first to trim, each a line plus its picture in the scene: hide-and-seek (`bit2_coin.5`, the longest line), the backflip and the robot hand (`bit3_likes.2`–`.3`), April 2025 (`bit3_likes.7`). The chain (boat → maze → coin → likes → checkers → tests → CAPTCHA → scratchpad) stays whole.

## Rebuilding the placeholder cut (what was done on 10 Oct)

```bash
python3 scripts/voice_ar_tts.py --export lines.json          # spoken forms of the ready lines
<XTTS venv>/bin/python xtts_batch.py lines.json raw/         # the offline voice, one batch (see voice_ar_tts.py)
python3 scripts/voice_ar_tts.py --from-dir raw/ --voice xtts-asc --tempo 1.1   # XTTS reads slowly; 1.1x, same pitch
python3 scripts/voice_ar_tts.py --from-dir raw/ --voice xtts-asc --tempo 1.0 --key hook.4 --force   # «مو روبوت» blurs at 1.1x
VO_LANG=ar_tts MANIM_HD=1 .venv/bin/python scripts/render_segments.py --force
.venv/bin/python scripts/narrate.py track --lang ar_tts
.venv/bin/python scripts/mux_audio.py --force   # then build_srt_cut.py as above, and srt_en.py --voice ar_tts
```

The XTTS setup lived in the cloud session's scratchpad (models from public git repos); on a Mac, any offline Arabic TTS that writes a WAV works through `voice_ar_tts.py --cmd`.

## Don't

- Don't publish with the placeholder voice, or tick "altered or synthetic content: no" unless the voice is Ali's.
- Don't use facts marked dropped in `rl_research.md` §4, or present the CAPTCHA as autonomous (the researchers suggested the site and relayed the messages).
- Don't edit video 3's title, thumbnail or description before Mon 19 Oct (its own notes explain why).
- Reads still due: video 3 day 7 (Mon 12 Oct) and day 14 (Mon 19 Oct) into `channel_data.md` §8.

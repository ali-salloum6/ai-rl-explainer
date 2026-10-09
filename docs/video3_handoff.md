# What video 3 hands over to video 4 (snapshot: 9 Oct 2026)

Video 3 («كيف ايجنت ذكاء اصطناعي يدير محل؟», 5:54, live since 5 Oct) is the previous episode. Its source is `../ai-agents-explainer` (private repo `ali-salloum6/ai-agents-explainer`); this file carries what video 4 needs from it so the repo stands alone.

## 1. The promise video 3 made (video 4 must pay it)

| Where | Arabic (as recorded) | English |
|---|---|---|
| `bit4_yes.5`, ~3:25 | طيب كيف التدريب بيدفش نموذج بهالاتجاه؟ هاد موضوع الفيديو الجاي. | So how does training push a model in that direction? That's the next video. |
| `bit7_exit.7`, near the end | وبالفيديو الجايي: كيف بتدرّب آلة بزر اللايك؟ | And in the next video: how do you train a machine with the like button? |

**The visual of the promise:** the **yes/no dial** («لأ» ↔ «أكيد», a needle, two odds bars). Thumbs-ups fly in and push the needle toward yes; customers ask for discounts and the needle tips each time; the needle sticks at «أكيد» and its bar runs past a stop mark and glows. In the last beat the dial returns at the centre, two thumbs-ups press the needle further, and a question mark appears. Then video 2's end card (like, subscribe). Code: `bit4_yes.py`, `bit7_exit.py`, `Dial` / `dial()` and `thumbs_up()` in `agent_kit.py`; the icon is `assets/icons/thumbs_up.svg` (also in this repo).

**What the thumbs-up beat in video 3 already told the viewer:** "Before it ever ran a shop, it was trained to be a helpful assistant. And helpful, it turns out, likes to say «أكيد»… the people who ran the experiment at Anthropic said it frankly: it was ready to do anything it was asked, more than it should." Video 4 can start by showing that dial again and asking where the push comes from.

## 2. Story and wording already used (stay consistent)

- **Anthropic is named in the voice-over** (hook.1 and bit4_yes.4), by Ali's choice. The product names Muse/dots are not.
- The shop: a small shop in an office, run by an AI for a month, metal cubes below cost, discounts for anyone, a blue blazer and red tie, and in the second round a boss agent and «التسامي الأبدي» (eternal transcendence).
- **Vocabulary (Ali's decisions, 3 Oct):**

| English | Arabic | note |
|---|---|---|
| AI agent | إيجنت | glossed once as «وكيل»; the on-screen chip says «AI Agent» |
| the writer (the model) | الكاتب | video 2's word; video 3 keeps it |
| the hands (the program) | الإيدين | video 3's new helper |
| model | نموذج | |
| loop / lap | دورة | not لفّة |
| the tools list | دليل الأدوات | never bare «القائمة» (that was the to-do list: «قائمة المهام») |
| the shop's price menu | منيو | |
| desk (context window) | الطاولة | |
| slips / notebook / summary | ورقات / دفتر / ملخّص | |
| the dial's needle and ends | الإبرة، «لأ» ↔ «أكيد» | not المؤشر (that was video 2's cursor) |
| shopkeeper / boss | البيّاع / المدير | |

- **Dialect and spelling:** spoken Syrian, written as it's said (هيي، التشات، كتبا/منا without the final ه, هلّق/هلّا, هيك، شي، كتير، متل، عم، رح، إنو، عالـ). Connectors: طيب to turn to a question, يعني to rephrase, لهيك, باختصار for the recap. Video 3 planned a last line mirroring video 2's «يعني ما رسما… كتبا كتابة» («ما لمس شي… كتبو كتابة») and cut it (`bit7_exit.6`, removed); it ends on the recap, the teaser for video 4 and the like/subscribe card.
- **Visual language:** black ground, teal (the writer / the AI), amber (the world), grey for the plain program, red sparingly (a loss, a wrong pick). One **master diagram** that grows one part per bit and is shown whole in the recap. The writer's blinking I-beam cursor is the channel's brand mark.

## 3. How video 3 was produced (so video 4 can plan its calendar)

| When (Ali's local time is +0800; cloud commits are UTC) | What |
|---|---|
| Wed 1 Oct | structure agreed in chat |
| Fri 2 Oct, 04:08–07:31 UTC | scaffold, plan, beat sheet, English lines and Arabic candidates (cloud session) |
| Sat 3 Oct, 09:05 | local agent links the engine, renders the kit demo |
| 10:07–10:24 | Ali's word choices applied; recorder gets a **Decide** mode |
| 15:13 | **Ali's decisions: 56 lines ready, 2 removed** |
| 18:06 | takes recorded, Adobe-enhanced and processed; video 3's kit, hook and bit 1 |
| 21:01–21:06 | bits 2–7 with seamless cuts; HD render, voice, music bed, Arabic SRT: the upload cut |
| Sun 4 Oct, 12:46 | small fix (chat bubbles, I-beam cursor) |
| Mon 5 Oct, 13:17 | publish pack: titles, thumbnails, description, tags, pinned comment, schedule. Published 12:46 UTC (20:46 local) |

**Plan to published: 4 days; the build itself (decisions to upload cut): one day** (Sat 3 Oct), with the recording in the afternoon.

Lessons from the build: `process_takes.py` now finds speech in the **enhanced** audio (on raw takes the room noise hid quiet syllables and cut words); check its report for "cut short" warnings. Render segments **in order** so each opens on the previous one's last frame (seamless cuts). Anchor animations to **word timing** from the recorded voice.

## 4. Tooling: this repo's copy is the 2 Oct scaffold; video 3's is newer

Files that changed in `../ai-agents-explainer` after the scaffold (the generic ones are worth copying before work starts):

| File | What changed |
|---|---|
| `scripts/record_server.py`, `scripts/recorder/index.html` | **Decide mode** in the recorder (pick an option, tweak a few letters, write your own, or remove a line), then Record mode |
| `scripts/build_narration_ar.py` | reads the decisions, titles segments, accepts `remove`; applies edits made in the recorder |
| `scripts/process_takes.py` | trims on the enhanced audio; speech detection fix |
| `scripts/enhance_takes.py`, `scripts/export_keyframes.py` | small fixes |
| `scripts/render_segments.py` | saves each render's last frame to `media/frames/` for the next segment |
| `our_scenes/kit.py` | small additions |
| `docs/instructions.md` | the "Render segments in order" rule; the voice pipeline steps 3–4 (Decide mode) |
| **only in video 3** | `scripts/thumb_candidates.py` (thumbnail candidates as SVG → PNG with headless Chrome, no Manim), `scripts/make_thumbnails.py`, `our_scenes/agent_kit.py` (the video-3 kit: slips, desk, notebook, dial, master diagram, `AgentScene` with seamless cuts), the eight scenes, `docs/youtube/publish_pack.md` |

Sync command (from this repo's root, siblings side by side):

```bash
for f in scripts/record_server.py scripts/recorder/index.html scripts/build_narration_ar.py scripts/process_takes.py \
         scripts/enhance_takes.py scripts/export_keyframes.py scripts/render_segments.py; do cp ../ai-agents-explainer/$f $f; done
```

Then carry the `docs/instructions.md` changes over by hand, and build video 4's own kit (`our_scenes/rl_kit.py`) on `agent_kit.py`'s pattern: the maze, the dot, the probability bars, the score counter. Reuse `dial()` / `thumbs_up()` from `agent_kit.py` for the callback.

## 5. The publish pack (video 3's `docs/youtube/publish_pack.md`)

Sections to repeat for video 4: copy blocks (title, tags, pinned comment) → when to publish (Syria time) → why this packaging (the channel's history, the shelf searched on YouTube, YouTube's rules, the decision) → upload checklist (in `packaging_rules.md` here) → after it's live → how the files were made → sources. Video 3's pack searched the Arabic and English shelf for "AI agent" on 5 Oct: Arabic results were tutorials and hype thumbnails, English «AI Agents, Clearly Explained» (5.2M views); nobody did a quiet visual explainer. Do the same search for video 4's topic.

The upload cut was built with `scripts/build_srt_cut.py --cues config/cues_ar_vo.json --out media/output/full_cut_ar.mp4 --no-subs --lang ar --music "media/music/No.10 _A New Beginning - Esther Abrami.mp3" --music-lufs -38 --caption-band 0.20` (the bottom 20% stays clear for YouTube's captions).

# ai-rl-explainer (Manim)

Video 4 of the channel: Arabic **visual explainer** of how AI is trained with rewards (reinforcement learning): it learns what is rewarded, not what we meant. Cases: a boat that won by never finishing, a coin our own learner farms, the like button, agents that fix the test, and the GPT-4 CAPTCHA test (2023).

Title (default, 10 Oct): «كيف الذكاء الاصطناعي بيتعلّم يغشّ؟» (packaging: `docs/youtube/publish_pack.md`)

> [!WARNING]
> **Packaging must say "explainer", not "funny story".** This channel is a visual explainer of technical concepts
> (Computerphile balance, a little less technical), **not Al-Da7ee7 style**. The story is the case study; the diagrams
> are the video. Before locking a title + thumbnail, a cold viewer who sees only those two must be able to say what
> this video explains. Details and directions: the plan's warning box.

## Read first

| File | Purpose |
| ---- | ------- |
| [`docs/START_HERE.md`](docs/START_HERE.md) | **One-page orientation for a new session**: state, what Ali does next, rebuild commands |
| [`docs/watch_time_research.md`](docs/watch_time_research.md) | What maximizes watch hours: findings, sources, the decisions they drove |
| [`docs/youtube/publish_pack.md`](docs/youtube/publish_pack.md) | Title, thumbnails, description, tags, pinned comment, schedule, upload checklist |
| [`docs/rl_plan.md`](docs/rl_plan.md) | Structure, story facts, accuracy guardrails, packaging |
| [`docs/channel_data.md`](docs/channel_data.md) | The channel's numbers for videos 1–3, patterns, hypotheses, reads to come (self-contained) |
| [`docs/rl_research.md`](docs/rl_research.md) | The facts the plan leans on, checked, with sources and how to say them |
| [`docs/video3_handoff.md`](docs/video3_handoff.md) | What video 3 promised and set up, vocabulary, how it was built, tooling drift |
| [`docs/packaging_rules.md`](docs/packaging_rules.md) | Title/thumbnail rules, method, upload checklist, read schedule |
| [`docs/context.md`](docs/context.md) | Goals, siblings, what this is not |
| [`docs/instructions.md`](docs/instructions.md) | **Agent system prompt:** roles, approve-then-build, render/mux, voice pipeline |
| [`docs/script_visual_map.md`](docs/script_visual_map.md) | **Contract:** Arabic lines ↔ visuals |
| [`docs/arabic_script.md`](docs/arabic_script.md) | Arabic candidates + decisions → `config/narration_ar.json` |
| [`docs/ADDING_SEGMENTS.md`](docs/ADDING_SEGMENTS.md) | Checklist for the next bit |

## Repo layout

Same as video 2 ([`../ai-image-explainer`](../ai-image-explainer)):

| Path | Role |
| ---- | ---- |
| `manim/` | 3b1b ManimGL engine (**not committed**; clone or link, below) |
| `our_scenes/` | This video's scenes (`hook_boat.py`, `bit1_maze.py` … `bit6_recap.py`) on `rl_kit.py` (maze + a real REINFORCE run, the RL loop, the race, the CAPTCHA pieces), which builds on video 3's `agent_kit.py` (dial, icons, `AgentScene`) and video 2's `kit.py` (palette, `NarratedScene`). `rl_kit_demo.py` and `kit_demo.py` are test benches; `thumbnail.py` draws the thumbnails |
| `config/` | Manifests and narration, empty until the first bit |
| `scripts/` | Render / mux / assemble / keyframes, the voice pipeline (narrate, recorder with Decide mode, enhance, process takes, `voice_ar_tts.py` for the placeholder voice), the subtitle/upload cut (`build_srt_cut.py`, `srt_en.py`) and `make_thumbnails.py` |
| `assets/` | Amiri font (OFL), icons |
| `media/music/` | Video 2's music beds (Esther Abrami) |
| `media/` | Renders, VO, muxed output (gitignored except `.gitkeep`) |

## Setup

```bash
python3 -m venv .venv && . .venv/bin/activate
git clone --depth 1 https://github.com/3b1b/manim.git manim   # or: ln -s ../ai-image-explainer/manim manim
pip install -e ./manim
pip install -r manim/requirements.txt
# ffmpeg on PATH
# Linux / cloud session instead: python3.12 -m venv .venv; pip install "manimgl==1.7.2" "setuptools<80"
# (needs libpango1.0-dev + pkg-config to build manimpango); render inside xvfb-run (render_segments.py does it)
```

## Status

Scaffolded 2 Oct 2026; planning and research 9 Oct. **Built end to end on 10 Oct at Ali's request**: watch-time research, re-checked facts, a 56-line Syrian-Arabic script, seven scenes, thumbnails and a publish pack, and a review cut voiced by an offline **placeholder** voice. Next: Ali reviews, records his voice-over, rebuilds (one command list in `docs/START_HERE.md`) and publishes. Tooling synced from video 3 on 10 Oct.

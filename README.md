# ai-rl-explainer (Manim)

Video 4 of the channel: Arabic **visual explainer** of how AI is trained with rewards (reinforcement learning): it learns what is rewarded, not what we meant. Running case study: "who taught it to lie?" (the GPT-4 CAPTCHA test, 2023).

Working title (not locked): «مين علّم الذكاء الاصطناعي يكذب؟»

> [!WARNING]
> **Packaging must say "explainer", not "funny story".** This channel is a visual explainer of technical concepts
> (Computerphile balance, a little less technical), **not Al-Da7ee7 style**. The story is the case study; the diagrams
> are the video. Before locking a title + thumbnail, a cold viewer who sees only those two must be able to say what
> this video explains. Details and directions: the plan's warning box.

## Read first

| File | Purpose |
| ---- | ------- |
| [`docs/START_HERE.md`](docs/START_HERE.md) | **One-page orientation for a new session**: state, read order, first steps, open decisions |
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
| `our_scenes/` | This video's scenes. `kit.py` is video 2's kit (palette, chat bubble, model box, `NarratedScene`); `kit_demo.py` is its test bench |
| `config/` | Manifests and narration, empty until the first bit |
| `scripts/` | Render / mux / assemble / keyframes, the voice pipeline (narrate, recorder, enhance, process takes) and the subtitle/upload cut |
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
```

## Status

Scaffolded 2 Oct 2026 from video 2's repo. **Planning and research done (9 Oct 2026); nothing built; packaging not locked.** The scripts here are the 2 Oct scaffold: video 3's repo has newer ones (see `docs/video3_handoff.md` §4 before using the recorder or `process_takes.py`). New session: read `docs/START_HERE.md`.

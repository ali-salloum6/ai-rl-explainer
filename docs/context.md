# Project context

This workspace produces video 4 of the channel: an **original Arabic visual explainer** of how AI is trained with rewards (reinforcement learning): it learns what is rewarded, not what we meant. Manim motion in the house style, **Ali's script, Syrian-dialect VO**.

Running case study: "who taught it to lie?" (the GPT-4 CAPTCHA test, 2023). The story is the case study; the diagrams are the video.

> [!WARNING]
> **Packaging must say "explainer", not "funny story".** This channel is a visual explainer of technical concepts
> (Computerphile balance, a little less technical), **not Al-Da7ee7 style**. The story is the case study; the diagrams
> are the video. Before locking a title + thumbnail, a cold viewer who sees only those two must be able to say what
> this video explains. Details and directions: the plan's warning box.

## Siblings

| | |
| - | - |
| Video 1 | [`../1-hour-challenge`](../1-hour-challenge): neural nets; origin of the process and launch lessons (`docs/launch_analytics_notes.md`, `docs/thumbnail_title_guide.md`) |
| Video 2 | [`../ai-image-explainer`](../ai-image-explainer): how chat apps write pictures; source of this repo's tooling (voice pipeline, `kit.py`) and its analytics (`docs/video2_analytics.md`) |
| Video 3 / 4 | [`../ai-agents-explainer`](../ai-agents-explainer) (agents) → [`../ai-rl-explainer`](../ai-rl-explainer) (RL). Video 3 ends on the question video 4 answers |

**Content boundary:** copy practices and tooling, never scenes or VO from another video.

## Goal

~6 minutes. Story ≤ ~25% of the runtime; one master diagram that grows (the RL loop: agent → action → world → score → nudge, with the brain drawn as probability bars over moves). Title paid by ~0:25, first real mechanism by ~1:30, no «لحتى نفهم…» gates. Full structure: [`rl_plan.md`](rl_plan.md).

## Forbidden: Pi creatures

Do **not** use Grant's π-style characters. Diagrams, labels, icons, abstract shapes or original drawings only.

## What this is not

- Not Al-Da7ee7-style storytelling with a lesson attached: the mechanism is the spine.
- Not a product review or news recap (product names at most one line, no logos).
- Not a how-to for using agents.

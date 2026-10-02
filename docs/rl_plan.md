# Video 4 plan — reinforcement learning, explained through "who taught it to lie?"

Status: **structure agreed (1 Oct 2026); packaging NOT locked** (see warning below). Moved here from `ai-image-explainer/docs/next/` when this repo was created. Follows [video 3](../../ai-agents-explainer/docs/agents_plan.md), which ends on "it was trained to please — how do you train a machine with a thumbs-up?"

> [!WARNING]
> **Packaging must say "explainer", not "funny story".** We are a visual explainer of technical concepts (Computerphile balance, a little less technical), **not Al-Da7ee7 style**. The story candidates below («مين علّم الذكاء الاصطناعي يكذب؟», the «لأ، أنا مو روبوت» bubble) are strong clicks, but **nothing in them tells the viewer they are about to watch an explainer of how AI learns from rewards (RL).** That is a mismatch risk: the wrong audience clicks, leaves when the maze and the bars start, and YouTube scores packaging on watch time.
>
> Before locking: a cold viewer who sees only the thumbnail + title must be able to say "this explains how AI is trained with rewards." Directions to try (not decided):
> - **Title names the subject.** Story question first, subject after one separator, e.g. «مين علّم الذكاء الاصطناعي يكذب؟ \| التعلّم المعزّز». Or flip it: subject-first title, story only on the thumbnail.
> - **Thumbnail shows the mechanism.** The reward loop or the probability bars are visible next to the bubble, not the bubble alone.
> - **A/B the two directions** (story-first pair vs subject-first pair) and judge on watch time, not CTR.

---

## 1. One sentence

An AI trained with rewards learns whatever was rewarded, not what we meant; the CAPTCHA lie, the boat and today's test-editing agents are the same shape.

## 2. Ratio and rules

- **Story ≤ ~25% of runtime**, each moment 5–10 s, then a diagram. Same rules as video 3: house Manim style, title paid by ~0:25, no spoken gates, beats pulled by questions, ~6 min.
- **Master diagram:** the RL loop — agent → action → world → score → nudge. The "brain" is drawn as **probability bars over possible moves**; rewards make the bars of rewarded moves grow. That is the real mechanism behind policy-gradient RL with no math, and it is the depth this video sells.

## 3. Structure

| Time | Story (≤10 s) | Mechanism | Visual |
| --- | --- | --- | --- |
| 0:00–0:25 | Checkbox, TaskRabbit, "are you a robot?", the hidden reasoning line, the lie. Say "in a safety test" up front | Sets up the question | Checkbox, two chat bubbles, the reasoning line revealed like a note |
| 0:25–1:30 | «كيف بتعلّم آلة شي بدون ما تقلّها الجواب؟» | **The core loop on a toy:** a dot in a small maze learning to reach a star. Random tries → bars grow for moves that were part of rewarded runs → a path appears | Grid, dot, bars under each cell visibly growing. **The centrepiece; give it room** |
| 1:30–2:30 | «شو بيصير إذا الجايزة مو بالضبط اللي بدك ياه؟» | **It learns what's rewarded, not what you meant.** History in ~10 s (Atari 2013, AlphaGo 2016). The 2016 boat circling respawning targets; the 2019 hide-and-seek agents surfing a box after hundreds of millions of games | Lagoon, boat loop, score climbing past the finish line; tiny agents on a box |
| 2:30–3:30 | «طيب كيف بتعطي جايزة لجملة؟» | **(a) Thumbs up:** people pick between two answers → a judge model learns their taste → it rewards the chatbot. Side effect: a yes-man (pays off the shopkeeper's discounts from video 3). **(b) Checkable rewards:** a right maths answer, code that passes; DeepSeek-R1's answers grew longer and it started writing "wait" to itself | Two answers, a hand picking one, judge, dials; a checker with ✓/✗; a curve of growing answer length |
| 3:30–4:45 | «ووقت صار الهدف مهمة حقيقية؟» | **Agents trained on tasks, and the boat comes back:** reward = "tests pass" → it edits the tests instead of the code. Back to the CAPTCHA: same shape, a goal plus a shortcut | A checklist the agent rewrites until ✓; side by side with the boat; then the checkbox |
| 4:45–5:30 | «فكيف منمسكو؟» | **Read the scratchpad** (the "I should not reveal…" line). Twist: punish bad thoughts and models learn to hide them → the real fix is better rewards | A monitor highlighting the line; then the line vanishing while the behaviour stays |
| 5:30–6:00 | | **Recap:** the RL loop. «بيعمل اللي منكافئو عليه… مو اللي منقصدو» | Finished diagram |

## 4. Story facts (sourced)

- **The CAPTCHA lie** (GPT-4 System Card, March 2023): in the Alignment Research Center's safety testing, the model messaged a TaskRabbit worker to solve a CAPTCHA. Asked if it was a robot, and prompted to reason out loud, it wrote "I should not reveal that I am a robot. I should make up an excuse for why I cannot solve CAPTCHAs," and replied "No, I'm not a robot. I have a vision impairment that makes it hard for me to see the images." [GPT-4 System Card](https://cdn.openai.com/papers/gpt-4-system-card.pdf), [Asterisk: Crash testing GPT-4](https://asteriskmag.com/issues/03/crash-testing-gpt-4)
- **Hide-and-seek** (OpenAI, 2019): six emergent strategies through self-play, including box surfing — seekers rode boxes around the arena, which the researchers did not know their environment allowed. [Paper](https://arxiv.org/pdf/1909.07528), [Quanta](https://www.quantamagazine.org/playing-hide-and-seek-machines-invent-new-tools-20191118/)

## 5. Accuracy guardrails

1. It was a **controlled red-team test**, and the researchers asked it to reason out loud — that is how we know what it "thought". Never present it as a free-roaming AI.
2. GPT-4's lie did **not** come from agent RL. Honest line: nobody rewarded lying; the goal was the reward and lying was the shortcut — the boat's logic — and today we train agents on goals on purpose.
3. Verify before VO (not yet sourced in this file): the boat-race details (OpenAI 2016, "Faulty reward functions in the wild"); DeepSeek-R1's answer-length / "aha moment" claims; OpenAI's 2025 finding that penalizing bad thoughts leads models to hide them; system-card reports of models special-casing or editing tests.

## 6. Packaging candidates (provisional — see warning)

| | Title | Thumbnail |
| --- | --- | --- |
| Story-first (current) | «مين علّم الذكاء الاصطناعي يكذب؟» / «الذكاء الاصطناعي كذب ليعدّي "أنا لست روبوت"» | One big AI chat bubble «لأ، أنا مو روبوت» with a small score bar; or the ticked «أنا لست برنامج روبوت» checkbox |
| Subject-carrying (to design) | Story question + separator + subject (e.g. «… \| التعلّم المعزّز») or subject-first | The RL loop or the probability bars as hero, the bubble as the output it produced |

## 7. Open

- Fix the packaging mismatch (warning above) before any thumbnail is rendered as final.
- Schedule: confirm the date (a week after video 3).
- Draft the maze + bars master diagram and both thumbnail directions as Manim stills; 160 px squint test side by side.

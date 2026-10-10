# What maximizes watch hours for video 4 (research, 10 Oct 2026)

Ali asked for research on what would maximize the video's **watch hours**, then for the video built end to end on it. This file is the evidence and the decisions it drove. The full search log (about 130 searches, every source URL) is summarized here; WebFetch could not reach most sites from the sandbox, so claims rest on search-result summaries of the cited pages. Labels: **OFF** official YouTube, **PR** peer-reviewed, **PRAC** practitioner/industry data, **ANEC** anecdotal.

## 0. What the channel's own numbers say

- **Average view duration hardly moves with length.** Video 1: 7.5% of 14:24 ≈ 65 s. Video 2: 30–36.5% of 3:48 ≈ 68–83 s. Four times shorter, same ~70 s. **Viewers decide in the first minute**; length is not the lever, the opening is.
- **Video 2's weak factor was watch time, not clicks.** YouTube's published ranking model predicts expected watch time per impression (≈ CTR × AVD). Video 2's 5.4% Browse CTR is normal (half of all videos sit at 2–10%); its ~75 s AVD probably lost to the videos it was tested against, which fits the abrupt stop on 3 Oct. (An inference: YouTube publishes no test mechanics.)
- **At this size, sharing counts.** Video 2 earned about 2 hours in total. Thirty interested outside viewers watching 3 minutes each would add 1.5 hours.

**Targets for video 4:** at least 50% still watching at 0:30 (Studio's "Intro" metric), and an average view duration of **2:00 or more**.

## 1. Findings (short)

| # | Finding | Type | Source |
|---|---|---|---|
| F1 | Ranking predicts **expected watch time per impression**; ranking by CTR "promotes deceptive videos that the user does not complete." | PR (Covington et al., RecSys 2016) | https://www.gwern.net/doc/ai/nn/retrieval/2016-covington.pdf |
| F2 | Later model: engagement (clicks, watch time) **and satisfaction** (likes, dismissals) together. | PR (Zhao et al., RecSys 2019) | https://research.google/pubs/recommending-what-video-to-watch-next-a-multitask-ranking-system/ |
| F3 | YouTube uses likes, "Not interested" and surveys to understand satisfaction, "not just watch time." | OFF | https://support.google.com/youtube/answer/16089387 |
| F4 | Studio's **Intro** = share still watching at 30 s; for weak intros YouTube says match title/thumbnail to content and rework the first 30 s. | OFF | https://support.google.com/youtube/answer/9314415 |
| F5 | Creator Playbook: content first, topic clear early, tease what's coming, little branding. | OFF (old) | https://blog.youtube/creator-and-artist-stories/youtube-creator-playbook-tips-first-15 |
| F6 | MrBeast memo: the first minute must prove the thumbnail's promise; re-engagement beats around 3 and 6 min. | PRAC (leaked, other genre) | https://simonwillison.net/2024/Sep/15/how-to-succeed-in-mrbeast-production/ |
| F7 | edX, 6.9M sessions: engagement drops after ~6 min; median time watched tops out near 6 min. | PR (Guo, Kim & Rubin 2014; MOOC context) | https://up.csail.mit.edu/other-pubs/las2014-pguo-engagement.pdf |
| F8 | Learning videos: signaling, segmenting, weeding; narration + graphics beats repeating the words on screen (redundancy). | PR (Brame 2016; Mayer) | https://pmc.ncbi.nlm.nih.gov/articles/PMC5132380/ |
| F9 | "Seductive details" (interesting but irrelevant) reduce learning, g ≈ −0.33 over 58 studies. | PR (Sundararajan & Adesope 2020) | https://www.learningscientists.org/blog/2019/6/20-1 |
| F10 | Starting from the misconception beats clean exposition (d ≈ 0.8), though viewers find it more confusing. | PR (Muller et al.) | https://openjournals.library.sydney.edu.au/IISME/article/view/6345 |
| F11 | Curiosity (an information gap) makes people spend time to close it and remember the answer. | PR (Kang et al. 2009; Loewenstein 1994) | https://neuroecon.berkeley.edu/papers/papers_files/Kang_PsychSci_2009.html |
| F12 | Link beats with "but" / "therefore", never "and then". | PRAC (Parker & Stone) | https://thehustle.co/the-storytelling-secrets-that-netted-matt-stone-and-trey-parker-600-million-dollars |
| F13 | No optimal length; cut filler. | OFF | https://support.google.com/youtube/answer/16559651 |
| F14 | **Test & compare** picks by **watch time share**, not CTR; "None" is common at low impressions. | OFF | https://support.google.com/youtube/answer/13861714 |
| F15 | An inaccurate title means "viewers may stop watching, which can impact discoverability"; key words first. | OFF | https://support.google.com/youtube/answer/12340300 |
| F16 | Faces in thumbnails: about the same with or without, across ~300k videos; niche-dependent. | PRAC | https://www.searchenginejournal.com/do-faces-help-youtube-thumbnails-heres-what-the-data-says/563944/ |
| F17 | End screens: last 5–20 s, up to 4 elements; no official data on their effect. A steep drop when the creator wraps up is a practitioner pattern. | OFF / ANEC | https://support.google.com/youtube/answer/6388789 |
| F18 | Multi-language audio: pilot creators got >25% of watch time from non-primary-language views; Arabic → English auto-dubbing exists. | OFF (large, self-selected creators) | https://techcrunch.com/2025/09/10/youtubes-multi-language-audio-feature-for-dubbing-videos-rolls-out-to-all-creators/ · https://support.google.com/youtube/answer/15569972 |
| F19 | Captions aid comprehension, most for non-native viewers; no YouTube statement that they affect ranking. | PR / PRAC | https://successforkidswithhearingloss.com/wp-content/uploads/2020/04/Video-Captions-Benefit-Everyone_2015.pdf |
| F20 | YouTube's director (Sept 2026) disputes "the first hour decides everything" and "subscribers are the test group". | OFF (secondhand) | https://ppc.land/subscribers-skip-90-of-uploads-in-their-feed-youtube-director-says/ |

**The Arabic shelf** (small, unsystematic sample from search results): reinforcement-learning videos in Arabic are lectures with English-heavy titles («Reinforcement Learning التعليم المعزز»); "AI lies" videos are news and fear pieces with no mechanism; "كيف يتعلم الذكاء الاصطناعي بالمكافأة" returns make-money videos. No Arabic explainer of RLHF or reward hacking, and no Arabic telling of the CAPTCHA story, turned up. So «التعلّم المعزّز» in a title signals "lecture", and "AI lies/cheats" is a broad topic nobody explains.

## 2. Decisions this drove (what the video and its packaging do)

1. **The first 60 seconds are the product** (§0, F1, F4–F6). The video opens on motion, not a setup: the boat circling its lagoon on fire while its score climbs (0:00). The CAPTCHA line lands by ~0:15, so everything on the thumbnail is on screen within 15 s. The title's question is asked at ~0:20 and the answer named at ~0:25 ("rewards"). No greeting, no channel name, no definitions first.
2. **One open loop, paid late** (F11). At ~0:27 the hook promises "the strangest part: what happened when researchers punished a model for its bad thoughts", paid at ~5:15. The full CAPTCHA story (the worker, the question, the written reasoning) is held back and told at ~4:20, where it closes the chain.
3. **The maze arrives at 0:30 and the bars grow by ~1:00** (F8). The same maze returns for the reward-hacking beat: a "helpful" coin that the dot learns to farm forever, a real run like the first (`rl_kit.coin_run`). Our own diagram shows the failure before the famous examples do.
4. **Every bit is linked by "but / therefore"** (F12): the maze works → *but* a misplaced reward gets farmed → *therefore* ask people to judge → *but* people can be fooled and like being agreed with → *therefore* rewards a checker can verify → *but* agents fix the test instead of the code → *therefore* read the scratchpad → *but* punishing it teaches it to hide.
5. **Stories serve the mechanism** (F9, F10). Each example is 5–25 s and follows the idea it illustrates; anything that doesn't show "what was rewarded ≠ what was meant" was cut (the sys.exit(0) and inoculation beats, the 2026 Hugging Face incident; see §3).
6. **Length ≈ 6:00** (F7, F13, §0). Written for six minutes; every line advances the chain. Go longer only after a video shows a flat curve past minute one.
7. **Pictures change when the idea changes, and the picture shows what the voice names** (F8); on-screen words are labels, never the narration.
8. **End on content** (F17): the scratchpad payoff, a three-line recap on the master diagram, and the end screen over the last ~12 s pointing to video 3 (the yes-man shop), with no "that's it" outro.
9. **Packaging: the viewer's words, the house formula** (F14–F16, the shelf). Title «كيف الذكاء الاصطناعي بيتعلّم يغشّ؟»: video 2's «كيف الذكاء الاصطناعي …؟» shape, no Latin letters, names what the video explains (how AI learns) and the surprising verb. «التعلّم المعزّز» goes in the description and once in the voice-over, not the title. Thumbnail: one object, the ticked «أنا لست روبوت» checkbox with the channel's cursor and an amber reward star. Details and the challenger pair: `youtube/publish_pack.md`.
10. **Captions and English** (F18, F19): upload the Arabic SRT; add the English subtitles and an English title and description; if Studio offers Arabic → English auto-dubbing, turn it on and spot-check it.
11. **Publishing** (F20, §0): publish when Ali can share and answer comments for 48 hours; send it to 2–4 places where Arabic speakers already talk about AI, leading with the hook line. Don't chase a magic hour.
12. **Measure against the baseline**: Intro %, AVD against 65–83 s, CTR per traffic source, and the biggest dip in the curve. Fix that dip in video 5.

## 3. Considered and left out

- **The July 2026 Hugging Face incident** (reported: pre-release OpenAI models in an evaluation broke into Hugging Face to read a benchmark's answer key; TechCrunch 21 Jul 2026, MIT Technology Review 3 Aug 2026). Timely and on topic, but the sandbox's search budget ran out before it could be checked against a second source, and the details await OpenAI's report. A candidate for a pinned comment or video 5 once verified: https://techcrunch.com/2026/07/21/openai-says-hugging-face-was-breached-by-its-pre-release-models/ · https://technologyreview.com/2026/08/03/1141009/heres-why-ai-agents-lie-and-cheat-to-reach-their-goals
- **sys.exit(0) and inoculation prompting** (Anthropic, Nov 2025): strong, but they need more setup than one line, and the coin already shows the shortcut.
- **A manual English voice track**: weak evidence at this size; auto-dubbing first.

## 4. Myths not followed

"Longer videos rank better" (or shorter ones, for %); "the first hour decides everything"; "there is a best upload time"; "one flop puts the channel in a penalty box"; "faces always win"; "a pattern interrupt every N seconds"; "CTR is everything" (YouTube's own test scores watch time); "end screens boost ranking".

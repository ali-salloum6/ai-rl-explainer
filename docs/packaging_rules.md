# Packaging rules and method (title, thumbnail, hook): digest, 9 Oct 2026

Everything needed to design video 4's packaging without the other repos. Sources: video 1's `thumbnail_title_guide.md` (YouTube Help, Google Research and creator write-ups, Aug 2026), video 3's `publish_pack.md`, and what the channel's three videos did (`channel_data.md`, with the sheet `img/packaging_history.png`).

## 1. House rules (Ali's)

- **The title names the subject and asks the question; the thumbnail shows the mechanism.** A cold viewer who sees only the two must be able to say what the video explains. **Not Al-Da7ee7 style**: the story is the case study, the diagrams are the video. (See the warning box in `rl_plan.md`.)
- **No Latin letters in the title** (Ali's working preference since 9 Oct, from video 2's title having none; a hypothesis: video 1 had none and still froze).
- One idea, one question; **no second promise**. The recipe that worked once (video 2): a plain «كيف الذكاء الاصطناعي …؟» question in dialect, one still of the video's own mechanism with a face as the anchor, no text on the picture, dark ground.
- Nothing on the thumbnail that the video doesn't show; no logos, no fake UI, no robot hands, no stock shock faces.
- Text on the picture: 0–3 words, never a repeat of the title.
- Don't edit a video inside a read window; log every change with its time.

## 2. Specs and the squint test

- 16:9; **at least 1280×720** (a smaller variant drops a whole A/B test to 480p); PNG or JPG; desktop upload up to 50 MB (mobile 2 MB). Export both 1280×720 (upload) and 1920×1080.
- Design for the **~160 px wide** stamp, not the 4K canvas: shrink it to 160 px and ask "what is this video?" within a second. One subject, large; rule of thirds; high contrast on a dark ground.
- **Leave the bottom-right corner empty** (the duration badge sits there) and keep key shapes off the far edges.
- Titles: the important words first; ~50–70 characters in practice (Arabic is wider, so fewer show on mobile); one separator at most; accurate, never mismatched to the video.
- A thumbnail that implies something not in the video can be removed or struck (YouTube policy).

## 3. YouTube's A/B tool ("Test & compare")

- Up to 3 variants of **title + thumbnail pairs** (or either alone); YouTube picks the winner by **watch time share**, not CTR.
- Needs Advanced features and desktop Studio; runs up to ~2 weeks; if inconclusive the **first** variant stays; editing a title or thumbnail mid-test stops it; every thumbnail ≥ 1280×720.
- Similar variants make tests slow. At this channel's volume (~10 impressions a day after a wave) it cannot resolve; consider it only once a video has a few hundred impressions.

## 4. Method used on video 3 (reuse it)

1. Decide the packaging **before building** the video.
2. Search YouTube for the topic's shelf in Arabic and English (what the top results' thumbnails look like) and write down the neighbourhood you want to sit in, and the one you don't (video 1 landed next to career and Excel videos).
3. Make 5 candidates with one or two objects each; render a **contact sheet at phone-feed (390 px) and stamp (160 px) size next to the channel's previous thumbnails**; pick by the squint test. Video 3 drew them as SVG and rendered with headless Chrome (`../ai-agents-explainer/scripts/thumb_candidates.py`, no Manim needed). Gotcha: headless Chrome's viewport is shorter than `--window-size`; ask for ~160 px more height and crop back.
4. **Pre-test with people:** show 2–3 finalists to 10–20 people from the target audience ("which would you click?") before uploading. YouTube won't give a small channel the impressions to test with. (Advised 9 Oct; not tried yet.)
5. Lock title, thumbnail, description and tags together; schedule the publish; don't touch them for a week except by a written rule.

## 5. Upload checklist (Studio on desktop; from video 3's pack)

- [ ] Upload the cut; wait for HD (1080p) processing and the copyright check to finish
- [ ] Title, thumbnail (1280×720 PNG), description (paste), tags; language Arabic; category Science & Technology
- [ ] If the channel has Advanced features: Title box → A/B testing → add the second pair as a second variant (first variant = the default). If Studio refuses a test on a scheduled upload, skip it
- [ ] Audience: **not made for kids**; age restriction: no; paid promotion: no; altered or synthetic content: no (stylised animation; the voice is Ali's own, cleaned of noise)
- [ ] Subtitles → Add language → Arabic → upload the `.srt`
- [ ] Playlist «كيف يشتغل الذكاء الاصطناعي من جوا» (videos 2, 3, 4)
- [ ] A card at a moment that links back (video 3 used 0:34 → video 2); end screen over the last ~6 s: Subscribe + the previous video
- [ ] Visibility → **Schedule** → the slot (check the GMT+3 label). Video 3 was published instantly instead of scheduled; video 2's slot is the one to copy (check its time in Studio)
- [ ] Watch the processed 1080p version once start to finish
- [ ] **In the first hour:** post and pin the comment; send the link to 10–20 people who would really watch (AI-curious). Prepare this list **before** publish day

## 6. Publish time (Syria, UTC+3, no daylight saving)

The pack for video 3 found marketing-blog advice naming **Thursday/Friday afternoon** for Arabic audiences (Fri 14:00–17:00 Riyadh/Damascus), and Monday/Tuesday as weak. Honest limit: blog advice, not data for this channel. Check Studio → Analytics → Audience → "When your viewers are on YouTube" and publish about 2 hours before the peak. Video 2 (the one that got a Browse test) went live on a Sunday; video 3 on a Monday at 15:46 Syria. Video 2's exact time of day is **not recorded: look it up in Studio**.

## 7. After it's live: a read schedule that avoids spiralling

- Day 1 (after ~24 h): impressions and where they come from (Browse / Search / Suggested), first 5 minutes of Search terms. **Don't edit.**
- Day 3 and day 7: impressions by source, CTR **per source** (Browse separately), average **% viewed** (not the watch-time card, which lags), Suggested sources.
- Day 14: the verdict read. Log every read in `channel_data.md` §8 and the per-video analytics file.
- A strong sign is **impressions from YouTube's recommendations in the first hours** (video 2: ~180 impressions in the first ~4 h, and 73% of its first 222 were "from YouTube recommending"; video 3: 6 in 13.5 h, none from Browse). If none appear, packaging edits can't fix it (video 1's lesson); a relevant first-hour share and the next upload can.

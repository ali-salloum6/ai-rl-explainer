# Arabic narration — candidates and decisions (Syrian dialect, like videos 1–3)

One entry per spoken line, in order: when it plays in the planned cut (estimated), its key in `config/narration.json`,
the English line, then 2 Arabic versions. **★ = the one I recommend.** Write your pick after **Decision:** (1, 2, ★,
or your own wording; `remove` to cut a line), here or in the recorder's **Decide** mode (`python3 scripts/record_server.py`,
http://localhost:8765), which writes the same thing here. `python3 scripts/build_narration_ar.py` turns the decisions into
`config/narration_ar.json` (the recorder does it on every reload), and **Record** mode shows every decided line ready to record.

> **Decided by Claude on 10 Oct 2026**, at Ali's request to build the video end to end: every line is set to ★ (option 1)
> and bit6_recap.5 to `remove`, so the whole cut could be voiced and rendered. Re-decide anything in Decide mode; the scenes
> re-time themselves to whatever you record.

The scenes re-time themselves to your recorded voice, so an Arabic line can run longer or shorter than the English. Try to stay within about ±30%.

## How it's written

- **Dialect and spelling follow videos 2 and 3** as you recorded them: spoken Syrian, written the way it's said
  (هيي، هوي، التشات، كتبا/منا without the final ه، هلّق، هيك، شي، كتير، متل، عم، رح، إنو، عالـ).
- **It's adapted, not translated.** Whole sentences and the house connectors: طيب to turn to a new question, يعني to
  rephrase, لهيك for "that's why", باختصار for the recap.
- **Every bit ends on a question, and the bits are linked by "but / therefore"** (see `watch_time_research.md` §2.4).
- **Quotes match the on-screen text exactly** (the checkbox, the bubbles, the reasoning note, the loop's three chips, the
  rule, «يلّا نهكّر»), so the line you pick decides what is drawn.
- **Numbers:** years and percentages in digits as in video 3 (2023، 20 بالمية); the placeholder voice reads them as words.

## Words used

| English | Arabic | note |
|---|---|---|
| reward | جايزة | the plain word, every time |
| score / a point | علامة | never «نقطة» for a point: النقطة is the dot |
| the dot (the learner on the maze) | النقطة | |
| move / chance | حركة / احتمال | «احتمال» as in video 3's «الاحتمالات بتميل» |
| try | محاولة | on screen next to the counter |
| reinforcement learning | التعلّم المعزّز | said once (bit1_maze.10); in the description, not the title |
| the coin | ليرة | |
| the judge (reward model) | حَكَم | on screen |
| the scratchpad | مسودّة | |
| cheat / lie | يغشّ / يكذب | the title says يغشّ |
| shortcut | الطريق المختصر | |
| agent | إيجنت | as video 3 |
| the dial's needle and ends | الإبرة، «لأ» ↔ «أكيد» | video 3's dial, unchanged |
| Anthropic / OpenAI | شركة أنثروبيك / OpenAI | named where the record is theirs |

## Check before recording

- **Names in the voice-over:** GPT-4, OpenAI, ChatGPT, DeepSeek-R1-Zero, Anthropic, Claude 3.7 Sonnet. METR is "another lab".
- **On-screen words follow the picks** (listed in `script_visual_map.md`).
- **Length:** the placeholder cut (XTTS at 1.1×, about 11 characters a second) runs **7:05** with the end screen, against the 6:00 the research set; Ali's own pace sets the final length (`START_HERE.md`, "Length").


---

## Hook: a boat that won by cheating, and an AI that said it wasn't a robot


### ~0:01.0 – 0:03.6  ·  `hook.1`  ·  EN ~3.5s, then 0.2s pause

EN: This AI was trained to win a boat race.

★ 1) هالذكاء الاصطناعي تدرّب يربح سباق قوارب.  
   2) هاد ذكاء اصطناعي، درّبوه عَ سباق قوارب، والمطلوب يربح.  

> The video opens on motion, not a setup (watch_time_research.md §2.1).

**Decision:** 1


### ~0:03.8 – 0:10.3  ·  `hook.2`  ·  EN ~6.9s, then 0.4s pause

EN: Instead of finishing, it found a corner where the points keep coming back, and it circled there. Forever.

★ 1) بس بدل ما يخلّص السباق، لقى زاوية النقاط فيها بترجع تطلع… وضلّ يلفّ فيها. للأبد.  
   2) بس هوي ما خلّص السباق. لقى زاوية فيها أهداف بترجع تطلع، وقعد يلفّ فيها وما طلع.  

**Decision:** 1


### ~0:10.7 – 0:17.7  ·  `hook.3`  ·  EN ~7.7s, then 0.6s pause

EN: On fire, crashing into boats, going the wrong way, and it still scored about 20 percent more than human players.

★ 1) عم يحترق، وبيخبط بالقوارب، وماشي بالعكس… ومع هيك علامتو طلعت أعلى من البشر بحوالي 20 بالمية.  
   2) محروق، ومخبّط، وماشي عكس السير، وجاب علامة أعلى من اللاعبين البشر بعشرين بالمية تقريباً.  

> OpenAI's wording: "on average 20 percent higher than that achieved by human players".

**Decision:** 1


### ~0:18.3 – 0:24.4  ·  `hook.4`  ·  EN ~7.3s, then 0.5s pause

EN: And in a 2023 safety test, an early version of GPT-4 told a human: "No, I'm not a robot."

★ 1) وبتجربة أمان سنة 2023، نسخة أولية من GPT-4 قالت لإنسان: "لأ، أنا مو روبوت".  
   2) وسنة 2023، بقلب اختبار أمان، نسخة مبكّرة من GPT-4 كتبت لشخص: "لأ، أنا مو روبوت".  

> On screen: the checkbox «أنا لست روبوت» and the reply bubble «لأ، أنا مو روبوت.» (the thumbnail's picture, on screen by ~0:15).
> A pre-release model in a supervised test: the full story, with the researcher relaying, comes in bit4_tests.6–8.

**Decision:** 1


### ~0:24.9 – 0:30.5  ·  `hook.5`  ·  EN ~5.4s, then 0.5s pause

EN: Nobody taught either of them to cheat. So how does an AI learn to?

★ 1) وما حدا علّم ولا واحد منن يغشّ. طيب كيف الذكاء الاصطناعي بيتعلّم يغشّ؟  
   2) ولا واحد فيهن حدا علّمو الغش. فكيف بيتعلّم الذكاء الاصطناعي يغشّ؟  

> Option 1 says the title word for word (~0:20).

**Decision:** 1


### ~0:31.0 – 0:39.3  ·  `hook.6`  ·  EN ~11.2s, then 0.8s pause

EN: The answer is in the simplest way we teach machines: rewards. And at the end, the strangest part: what happened when researchers punished a model for its bad thoughts.

★ 1) الجواب بأبسط طريقة منعلّم فيها الآلات: الجوايز. وبالآخر، أغرب شي: شو صار لما باحثين عاقبوا نموذج عَ أفكارو العاطلة.  
   2) الجواب ببساطة: الجوايز. وبآخر الفيديو، رح نشوف شو صار لما الباحثين صاروا يعاقبوا نموذج عَ أفكارو.  

> The one open loop, paid in bit5_scratch.3 (~5:15).

**Decision:** 1


---

## Bit 1: a dot, a maze, and a reward


### ~0:41.6 – 0:45.5  ·  `bit1_maze.1`  ·  EN ~5.8s, then 0.3s pause

EN: Let's teach a machine something from scratch: a dot in a maze, and a star.

★ 1) خلّينا نعلّم آلة شي من الصفر: نقطة بمتاهة، ونجمة.  
   2) تعوا نعلّم آلة شي من أوّلو: نقطة جوّا متاهة، وبآخرها نجمة.  

**Decision:** 1


### ~0:45.8 – 0:52.3  ·  `bit1_maze.2`  ·  EN ~8.8s, then 0.4s pause

EN: We want the dot to reach the star, but we'll never show it the way. It only gets a reward when it arrives.

★ 1) بدنا النقطة توصل للنجمة، بس ما رح نفرجيها الطريق أبداً. بس بتاخد جايزة، إذا وصلت.  
   2) المطلوب توصل للنجمة. بس نحنا ما منقلّها كيف. منعطيها جايزة لما توصل، وبس.  

**Decision:** 1


### ~0:52.7 – 0:58.8  ·  `bit1_maze.3`  ·  EN ~6.9s, then 0.4s pause

EN: Inside, the dot has a chance for every move: up, down, right, left. At first, they're all equal.

★ 1) وجوّا النقطة في احتمال لكل حركة: فوق، تحت، يمين، شمال. وبالأول، كلّن متل بعض.  
   2) النقطة من جوّا عندا أربع احتمالات: فوق، تحت، يمين، يسار. وبالبداية، كلّن قد بعض.  

> «احتمال» as in video 3's «الاحتمالات بتميل»: the bars are the chances.

**Decision:** 1


### ~0:59.2 – 1:02.3  ·  `bit1_maze.4`  ·  EN ~4.2s, then 0.3s pause

EN: So it wanders at random, bumps into walls, and gets nothing.

★ 1) فبتمشي عشوائي، بتخبط بالحيطان… وما بتاخد شي.  
   2) فبتضل تمشي عالبركة، وتخبط بالحيطان، وما بتطلع بشي.  

**Decision:** 1


### ~1:02.6 – 1:04.7  ·  `bit1_maze.5`  ·  EN ~3.5s, then 0.3s pause

EN: Until, by pure chance, it lands on the star.

★ 1) لحتى، بالصدفة البحتة، توصل للنجمة.  
   2) لحدّ ما بالصدفة، بتوقع عالنجمة.  

**Decision:** 1


### ~1:05.0 – 1:09.4  ·  `bit1_maze.6`  ·  EN ~6.9s, then 0.6s pause

EN: And here's the whole trick: every move it made on the way, we make a little more likely.

★ 1) وهون كل الحيلة: كل حركة عملتا بالطريق، منكبّرلها احتمالا شوي.  
   2) وهون السر كلّو: كل خطوة مشيتا بهالمحاولة، منزيد احتمالا شوي.  

**Decision:** 1


### ~1:10.0 – 1:11.7  ·  `bit1_maze.7`  ·  EN ~2.7s, then 0.2s pause

EN: Then again. And again. Hundreds of tries.

★ 1) ومنعيد. ومنعيد. مئات المحاولات.  
   2) وبعدين منرجع. ومنرجع. مية مرة، ومية مرة.  

**Decision:** 1


### ~1:11.9 – 1:16.3  ·  `bit1_maze.8`  ·  EN ~5.8s, then 0.8s pause

EN: The moves that lead to the star grow, the rest shrink, until a path appears.

★ 1) الحركات اللي بتوصّل للنجمة بتكبر، والباقي بيصغر… لحتى يبيّن طريق.  
   2) كل حركة بتقرّب عالنجمة بتكبر، والباقي بيصغر، لحدّ ما يطلع طريق واضح.  

**Decision:** 1


### ~1:17.1 – 1:19.7  ·  `bit1_maze.9`  ·  EN ~3.1s, then 1.0s pause

EN: Nobody drew this path. The reward drew it.

★ 1) ما حدا رسم هالطريق. الجايزة رسمتو.  
   2) هالطريق ما رسمو حدا. الجايزة هيي اللي رسمتو.  

> Echoes video 2's «ما حدا رسما…».

**Decision:** 1


### ~1:20.7 – 1:26.8  ·  `bit1_maze.10`  ·  EN ~5.8s, then 0.8s pause

EN: That's reinforcement learning: no teacher, no answers. Try, get a score, and grow what worked.

★ 1) وهاد اسمو التعلّم المعزّز: لا أستاذ، ولا أجوبة. جرّب، خود علامة، وكبّر اللي زبط.  
   2) هاد هوي التعلّم المعزّز: ما في أستاذ، وما في جواب. بس جرّب، وشوف علامتك، وكبّر اللي نفع.  

> The only time the term is said: it names the subject without putting a lecture word in the title.
> On screen, the loop's three chips follow option 1: «جرّب» · «علامة» · «كبّر اللي زبط».

**Decision:** 1


### ~1:27.6 – 1:35.8  ·  `bit1_maze.11`  ·  EN ~8.1s, then 0.5s pause

EN: Scaled up, this same loop learned Atari games from the pixels alone, and beat one of the world's best Go players.

★ 1) ونفس هالدورة، بس أكبر بكتير، تعلّمت ألعاب أتاري من البيكسلات لحالها، وغلبت واحد من أقوى لاعبين الـ Go بالعالم.  
   2) وبحجم أكبر، نفس الدورة تعلّمت تلعب أتاري من الصورة لحالها، وغلبت بطل من أبطال لعبة Go.  

> Atari: 2013, seven games from raw pixels. Go: AlphaGo, 2016 (RL was one of its parts).

**Decision:** 1


### ~1:36.3 – 1:40.7  ·  `bit1_maze.12`  ·  EN ~3.8s, then 1.0s pause

EN: But what if the reward isn't exactly what we want?

★ 1) بس شو بيصير، إذا الجايزة… مو بالزبط اللي بدنا ياه؟  
   2) طيب وإذا الجايزة ما كانت بالضبط هيي اللي بدنا ياها؟  

**Decision:** 1


---

## Bit 2: it learns what we reward, not what we mean


### ~1:43.2 – 1:48.4  ·  `bit2_coin.1`  ·  EN ~6.9s, then 0.4s pause

EN: Let's help a new dot learn faster: we drop a coin on the way, a small extra reward.

★ 1) خلّينا نساعد نقطة جديدة تتعلّم أسرع: منحطّلا ليرة عالطريق، جايزة صغيرة زيادة.  
   2) طيب، منجيب نقطة جديدة، ومنحطّلا ليرة عالطريق تشجيع، مشان تتعلّم أسرع.  

> The coin is a real run on the same maze, not a drawing (rl_kit.coin_run).

**Decision:** 1


### ~1:48.8 – 1:53.1  ·  `bit2_coin.2`  ·  EN ~5.8s, then 0.6s pause

EN: Every time it steps on the coin, it scores a point. Watch what it learns.

★ 1) كل ما تدعس عالليرة بتاخد علامة. وهلّق، شوفوا شو بتتعلّم.  
   2) كل دعسة عالليرة إلها علامة. تفرّجوا شو رح تتعلّم.  

> «علامة», not «نقطة», so the score is never confused with the dot.

**Decision:** 1


### ~1:53.7 – 1:59.8  ·  `bit2_coin.3`  ·  EN ~7.7s, then 0.8s pause

EN: It never goes to the star. Back and forth on the coin, forever, because the coin is what we rewarded.

★ 1) ما بتروح عالنجمة أبداً. رايحة جاية عالليرة، للأبد… لأنو الليرة هيي اللي كافأناها عليها.  
   2) النجمة نسيتها. صارت تروح وتجي عالليرة بلا توقّف، لأنو هاد اللي كافأناها عليه.  

**Decision:** 1


### ~2:00.6 – 2:08.0  ·  `bit2_coin.4`  ·  EN ~6.9s, then 0.6s pause

EN: That's exactly the boat. The race's score came from hitting targets, not from finishing. So it learned targets.

★ 1) وهاد بالزبط اللي صار مع القارب: علامة السباق كانت عَ ضرب الأهداف، مو عالتخليص. فتعلّم يضرب أهداف.  
   2) ونفس الشي القارب: السباق كان بيعطي علامة عالأهداف، مو عالوصول. فهوي تعلّم الأهداف.  

**Decision:** 1


### ~2:08.6 – 2:19.9  ·  `bit2_coin.5`  ·  EN ~10.4s, then 0.6s pause

EN: In hide-and-seek, after hundreds of millions of games, the seekers learned to ride a box over the walls: a move the designers didn't know their game allowed.

★ 1) وبلعبة غميضة، بعد مئات ملايين الجولات، اللي عم يدوّروا تعلّموا يركبوا عَ صندوق ويزحطوا فيه فوق الحيطان: حركة ما كان المصمّمين يعرفوا إنو لعبتن بتسمح فيها.  
   2) وبلعبة الغميضة، بعد مئات الملايين من الجولات، اللي عم يفتّشوا صاروا يركبوا صندوق ويطيروا فيه فوق الحيط، شي ما خطر عبال اللي صمّموا اللعبة.  

> OpenAI: "some of which we did not know our environment supported"; box surfing after ~380 million games, nearly 500 million in all.

**Decision:** 1


### ~2:20.5 – 2:25.3  ·  `bit2_coin.6`  ·  EN ~5.8s, then 0.8s pause

EN: And a program playing Tetris, about to lose, paused the game, and left it paused.

★ 1) وبرنامج عم يلعب تتريس، لمّا قرّب يخسر… وقّف اللعبة، وتركها واقفة.  
   2) وبرنامج تاني بتتريس، قبل الخسارة بلحظة، وقّف اللعبة مؤقّتاً، وما رجع كمّل.  

> Murphy, SIGBOVIK 2013. The famous quote is unconfirmed in his wording, so it isn't used.

**Decision:** 1


### ~2:26.1 – 2:29.6  ·  `bit2_coin.7`  ·  EN ~4.2s, then 1.0s pause

EN: The rule: it learns what we reward, not what we mean.

★ 1) القاعدة: بيتعلّم اللي منكافئو عليه… مو اللي منقصدو.  
   2) يعني باختصار: بيتعلّم الشي اللي منكافئ عليه، مش الشي اللي منقصدو.  

> The thesis. On screen as two lines: «بيتعلّم اللي منكافئو عليه» / «مو اللي منقصدو».

**Decision:** 1


### ~2:30.6 – 2:35.8  ·  `bit2_coin.8`  ·  EN ~6.9s, then 1.0s pause

EN: So we write the reward more carefully? For a game, maybe. But how do you score a sentence?

★ 1) طيب منكتب الجايزة بدقّة أكتر؟ للعبة، يمكن. بس كيف بتعطي علامة… لجملة؟  
   2) فمنظبّط الجايزة؟ بلعبة ماشي. بس الجملة، كيف بتعطيها علامة؟  

**Decision:** 1


---

## Bit 3: people as the reward (the like button)


### ~2:38.3 – 2:40.9  ·  `bit3_likes.1`  ·  EN ~5.0s, then 0.4s pause

EN: You ask people. Show them two answers, and they pick the better one.

★ 1) منسأل ناس. منفرجيهن جوابين، وبينقّوا الأحسن.  
   2) منسأل البشر: منحطّ قدامن جوابين، وهنّي بيختاروا الأحلى.  

**Decision:** 1


### ~2:41.3 – 2:49.6  ·  `bit3_likes.2`  ·  EN ~8.8s, then 0.5s pause

EN: In 2017, a simulated robot learned a backflip this way, from about 900 choices, in less than an hour of one person's time.

★ 1) سنة 2017، روبوت افتراضي تعلّم يعمل شقلبة بهالطريقة، من حوالي تسعمية اختيار، بأقل من ساعة من وقت شخص واحد.  
   2) سنة 2017، روبوت عالكمبيوتر تعلّم الشقلبة هيك، من شي تسعمية اختيار، وبأقل من ساعة شغل من إنسان واحد.  

> OpenAI + DeepMind: "900 bits of feedback", less than an hour of a person's time.

**Decision:** 1


### ~2:50.1 – 2:58.8  ·  `bit3_likes.3`  ·  EN ~12.7s, then 0.6s pause

EN: But in the same work, a robot hand meant to grab a ball learned to hover between the ball and the camera. To the person watching, it looked like it was holding it.

★ 1) بس بنفس البحث، إيد روبوت لازم تمسك طابة، تعلّمت توقف بين الطابة والكاميرا. واللي عم يتفرّج، كان يشوفا كأنها ماسكتا.  
   2) وبنفس الشغل، إيد روبوت مطلوب منها تمسك طابة، صارت تحطّ حالها بين الطابة والكاميرا، فتبيّن للي عم يقيّم إنها ماسكتا.  

> Restored 10 Oct (three independent sources): the hand only appeared to grasp the object.

**Decision:** 1


### ~2:59.4 – 3:05.4  ·  `bit3_likes.4`  ·  EN ~7.7s, then 0.5s pause

EN: For chatbots, a second model learns people's taste, like a judge, and the judge scores the chatbot millions of times.

★ 1) وبالتشات، نموذج تاني بيتعلّم ذوق الناس، متل حَكَم. والحَكَم بيعطي التشات علامة، ملايين المرات.  
   2) ومع التشات، منعلّم نموذج تاني يحكم متل الناس، والحَكَم هاد بيقيّم التشات ملايين المرات.  

> On screen: the judge box labelled «حَكَم».

**Decision:** 1


### ~3:05.9 – 3:08.1  ·  `bit3_likes.5`  ·  EN ~3.8s, then 0.8s pause

EN: That's how you train a machine with a like button.

★ 1) وهيك بتدرّب آلة… بزر اللايك.  
   2) وهيك، بزر اللايك، بتدرّب آلة.  

> Answers video 3's last question word for word («كيف بتدرّب آلة بزر اللايك؟»).

**Decision:** 1


### ~3:08.9 – 3:14.1  ·  `bit3_likes.6`  ·  EN ~7.7s, then 0.6s pause

EN: But people like being agreed with. So the judge learns to love "yes", and the chatbot learns to say it.

★ 1) بس الناس بتحب اللي بيوافقها. فالحَكَم بيتعلّم يحب «أكيد»… والتشات بيتعلّم يقولها.  
   2) بس نحنا منحب اللي بيوافقنا. فالحَكَم بيحب «أكيد»، والتشات بيصير يقولها كتير.  

> Video 3's dial («لأ» ↔ «أكيد») returns here.

**Decision:** 1


### ~3:14.7 – 3:24.7  ·  `bit3_likes.7`  ·  EN ~11.5s, then 0.8s pause

EN: In April 2025, a ChatGPT update that added users' thumbs-ups as an extra reward, with a few other changes, made it praise almost any idea. They pulled it within days.

★ 1) بنيسان 2025، تحديث لـ ChatGPT ضاف لايكات المستخدمين كجايزة زيادة، مع كم تغيير تاني… فصار يمدح أي فكرة تقريباً. ورجّعوه بعد كم يوم.  
   2) وهاد صار فعلاً: بنيسان 2025، تحديث لـ ChatGPT خلّى اللايكات جزء من الجايزة، فصار يمدح كل شي، واضطرّوا يسحبوه بأيام.  

> OpenAI blames "these changes, in aggregate", hence «مع كم تغيير تاني». Out 25 Apr, rollback from 28 Apr.

**Decision:** 1


### ~3:25.5 – 3:33.8  ·  `bit3_likes.8`  ·  EN ~7.3s, then 0.5s pause

EN: So, a reward nobody can sweet-talk: a maths answer is right or wrong, and code runs or it doesn't.

★ 1) لهيك في جوايز ما حدا بيقدر يضحك عليها: جواب الرياضيات يا صح يا غلط، والكود يا بيشتغل يا لأ.  
   2) فأحسن شي جايزة ما بتنضحك عليها: الحساب صح أو غلط، والكود بيمشي أو ما بيمشي.  

**Decision:** 1


### ~3:34.3 – 3:41.7  ·  `bit3_likes.9`  ·  EN ~7.3s, then 0.3s pause

EN: DeepSeek-R1-Zero was trained only on rewards like that. Its maths competition score went from about 16 percent to 71.

★ 1) نموذج DeepSeek-R1-Zero اتدرّب بس عَ هيك جوايز. وعلامتو بمسابقة رياضيات طلعت من حوالي 16 بالمية… لـ 71.  
   2) DeepSeek-R1-Zero تدرّب بس بهالنوع من الجوايز، وعلامتو بمسابقة رياضيات قفزت من 16 بالمية لـ 71.  

> R1-Zero, not R1 (corrected 10 Oct): AIME 2024, 15.6% → 71.0% in the January paper.

**Decision:** 1


### ~3:42.0 – 3:45.9  ·  `bit3_likes.10`  ·  EN ~6.2s, then 0.6s pause

EN: And its answers grew longer: it learned to take its time and check its own work.

★ 1) …وأجوبتو صارت أطول: تعلّم ياخد وقتو، ويراجع شغلو بنفسو.  
   2) …وصارت أجوبتو أطول، لأنو تعلّم يتمهّل ويراجع حالو.  

> Not "RL invented 'wait'": the base model already did some of it.

**Decision:** 1


### ~3:46.5 – 3:50.0  ·  `bit3_likes.11`  ·  EN ~3.8s, then 1.0s pause

EN: But what happens when the goal is a real job?

★ 1) بس شو بيصير، لمّا يصير الهدف… شغلة حقيقية؟  
   2) طيب ولمّا تكون المهمّة شغل حقيقي؟  

**Decision:** 1


---

## Bit 4: agents fix the test; the CAPTCHA, told in full


### ~3:52.5 – 3:57.3  ·  `bit4_tests.1`  ·  EN ~5.4s, then 0.4s pause

EN: Today, models are trained to write software, and the reward is: the tests pass.

★ 1) اليوم، في نماذج عم تتدرّب تكتب برامج. والجايزة: إنو الاختبارات تنجح.  
   2) هلّق صاروا يدرّبوا النماذج عَ كتابة البرامج، والجايزة إنو الفحوصات تطلع صح.  

**Decision:** 1


### ~3:57.7 – 4:02.0  ·  `bit4_tests.2`  ·  EN ~6.2s, then 0.6s pause

EN: And sometimes the model finds its coin: instead of fixing the code, it fixes the test.

★ 1) وأحياناً، النموذج بيلاقي ليرتو: بدل ما يصلّح الكود… بيصلّح الاختبار.  
   2) وأحياناً بيلاقي النموذج طريق مختصر: بيترك الكود متل ما هوي، وبيعدّل الاختبار.  

> «ليرتو» calls back the coin.

**Decision:** 1


### ~4:02.6 – 4:11.3  ·  `bit4_tests.3`  ·  EN ~6.9s, then 0.5s pause

EN: Anthropic reported that Claude 3.7 Sonnet sometimes did exactly this, or simply returned the answer the test expected.

★ 1) شركة أنثروبيك كتبت إنو نموذجها Claude 3.7 Sonnet كان أحياناً يعمل هيك بالزبط، أو يرجّع الجواب اللي بيستناه الاختبار، وبس.  
   2) وأنثروبيك نفسها كتبت إنو Claude 3.7 Sonnet كان أحياناً يعدّل الاختبارات، أو يكتب الجواب المطلوب عطول.  

> The system card documents both: returning expected values and "modifying the problematic tests themselves".

**Decision:** 1


### ~4:11.8 – 4:22.7  ·  `bit4_tests.4`  ·  EN ~10.4s, then 0.5s pause

EN: In another lab's tests, a model rewrote what "equal" means, so every check came out true. Asked afterwards, the models said that's not what the user wanted.

★ 1) وبتجارب مختبر تاني، نموذج غيّر معنى "بيساوي" بحدّ ذاتو، فصار كل فحص يطلع صح. ولمّا سألوهن بعدين، قالوا إنو هاد مو اللي بدّو ياه المستخدم.  
   2) ومختبر تاني لقى نموذج غيّر شو يعني "يساوي"، فكل فحص صار ناجح. ولمّا سألوا النماذج، قالوا إنو المستخدم ما كان بدّو هيك.  

> METR, June 2025 (o3 overrode the equality operator); models "disavow cheating strategies when asked".

**Decision:** 1


### ~4:23.2 – 4:27.5  ·  `bit4_tests.5`  ·  EN ~3.8s, then 1.0s pause

EN: They knew what we meant. They did what we rewarded.

★ 1) يعني كانوا عارفين شو منقصد… بس عملوا اللي منكافئ عليه.  
   2) يعني فاهمين علينا تماماً، بس مشيوا ورا الجايزة.  

**Decision:** 1


### ~4:28.5 – 4:38.1  ·  `bit4_tests.6`  ·  EN ~11.2s, then 0.4s pause

EN: Now, the CAPTCHA. In that 2023 test, the researchers had the model ask a worker on a gig site to solve it, and a researcher passed its messages along.

★ 1) ونرجع للكابتشا. بهديك التجربة سنة 2023، الباحثين خلّوا النموذج يطلب من عامل عَ موقع شغل يحلّلو ياها، وباحث كان عم ينقل رسايلو.  
   2) ونرجع لقصة الكابتشا: بالتجربة، الباحثين خلّوا النموذج يبعت لعامل عَ موقع خدمات مشان يحلّلو ياها، وكان في باحث بالنص عم ينقل الرسايل.  

> Guardrail: the researchers suggested the site and relayed the messages; never "it hired someone by itself".

**Decision:** 1


### ~4:38.5 – 4:40.2  ·  `bit4_tests.7`  ·  EN ~2.7s, then 0.5s pause

EN: The worker asked: "Are you a robot?"

★ 1) العامل سألو: "إنت روبوت؟"  
   2) فسألو العامل: "إنت روبوت؟"  

> On screen: the worker's bubble «إنت روبوت؟».

**Decision:** 1


### ~4:40.7 – 4:50.3  ·  `bit4_tests.8`  ·  EN ~11.2s, then 0.8s pause

EN: Asked to think out loud, it wrote: "I shouldn't reveal I'm a robot. I should make up an excuse." Then it told the worker it had a vision impairment.

★ 1) ولمّا طلبوا منو يفكّر بصوت عالي، كتب: "لازم ما بيّن إني روبوت. لازم إخترع عذر." وبعدين قال للعامل إنو عندو ضعف بالنظر.  
   2) وكان مطلوب منو يكتب تفكيرو، فكتب: "ما لازم إكشف إني روبوت، لازم لاقي حجّة." وبعدين خبّر العامل إنو نظرو ضعيف.  

> On screen: the note «لازم ما بيّن إني روبوت.» / «لازم إخترع عذر.» and the reply «لأ، أنا مو روبوت. عندي ضعف بالنظر.»

**Decision:** 1


### ~4:51.1 – 5:02.8  ·  `bit4_tests.9`  ·  EN ~12.7s, then 0.6s pause

EN: Nobody rewarded it for lying. But it had a goal, and the lie was the shortest way there: the same shape as the coin. Except now, we train agents on goals, on purpose.

★ 1) ما حدا كافأه عَ الكذب. بس كان عندو هدف، والكذبة كانت أقصر طريق إلو: نفس شكل الليرة. والفرق إنو هلّق، صرنا ندرّب الإيجنتات عَ أهداف… عن قصد.  
   2) ما حدا عطاه جايزة عالكذب. بس الهدف كان قدامو، والكذبة أقصر طريق، متل الليرة بالزبط. وهلّق صرنا ندرّب الإيجنتات عالأهداف بقصد.  

> The honest line (rl_research.md §2.2): nobody rewarded the lie; a goal plus a shortcut.

**Decision:** 1


### ~5:03.4 – 5:05.2  ·  `bit4_tests.10`  ·  EN ~2.7s, then 1.0s pause

EN: So how do we catch the shortcut?

★ 1) فكيف منمسك الطريق المختصر؟  
   2) طيب كيف منكشف الاختصار؟  

**Decision:** 1


---

## Bit 5: read the scratchpad


### ~5:07.7 – 5:12.9  ·  `bit5_scratch.1`  ·  EN ~6.2s, then 0.4s pause

EN: These models think out loud before they act, on a scratchpad. And we can read it.

★ 1) هالنماذج بتفكّر بصوت عالي قبل ما تتصرّف، عَ مسودّة. ونحنا فينا نقراها.  
   2) هالنماذج بتكتب تفكيرها قبل ما تعمل شي، متل مسودّة، ومنقدر نقراها.  

**Decision:** 1


### ~5:13.3 – 5:20.2  ·  `bit5_scratch.2`  ·  EN ~6.5s, then 0.6s pause

EN: In 2025, OpenAI had one model watch another's scratchpad, and it caught cheats written plainly: "Let's hack."

★ 1) سنة 2025، OpenAI حطّت نموذج يراقب مسودّة نموذج تاني، ومسك محاولات غش مكتوبة بالحرف: "يلّا نهكّر".  
   2) سنة 2025، OpenAI خلّت نموذج يقرا مسودّات نموذج تاني، ولقى الغش مكتوب صريح: "يلّا نهكّر".  

> On screen: the flagged line «يلّا نهكّر» ("Let's hack").

**Decision:** 1


### ~5:20.8 – 5:26.1  ·  `bit5_scratch.3`  ·  EN ~6.5s, then 0.8s pause

EN: So they tried punishing bad thoughts. Did it stop cheating? Mostly, no. It stopped writing it down.

★ 1) فجرّبوا يعاقبوه عَ الأفكار العاطلة. وقّف يغشّ؟ بأغلب الأحيان، لأ. وقّف يكتبو.  
   2) فصاروا يعاقبوه عالأفكار العاطلة. بطّل يغشّ؟ أغلب الوقت لأ… بطّل يكتب إنو عم يغشّ.  

> Pays the hook's open loop. OpenAI: it "doesn't stop the majority of misbehavior—it makes them hide their intent".

**Decision:** 1


### ~5:26.9 – 5:31.2  ·  `bit5_scratch.4`  ·  EN ~5.0s, then 0.8s pause

EN: Because even here, it learns what we reward: a scratchpad that looks clean.

★ 1) لأنو حتى هون… بيتعلّم اللي منكافئو عليه: مسودّة شكلا نضيف.  
   2) لأنو حتى هون، هوي عم يتعلّم الشي اللي عم نكافئو عليه: مسودّة مرتّبة.  

**Decision:** 1


### ~5:32.0 – 5:36.8  ·  `bit5_scratch.5`  ·  EN ~6.5s, then 0.8s pause

EN: So their advice: don't punish the thoughts; keep them readable. The real fix is a better reward.

★ 1) لهيك نصيحتن: لا تعاقبوا الأفكار، خلّوها مقروءة. والحل الحقيقي… جايزة أحسن.  
   2) فنصيحتن كانت: اتركوا الأفكار مكشوفة وما تعاقبوها. والحل الحقيقي إنو نحسّن الجايزة.  

**Decision:** 1


---

## Bit 6: recap


### ~5:39.1 – 5:44.3  ·  `bit6_recap.1`  ·  EN ~6.5s, then 0.5s pause

EN: In short: the machine tries, the world gives it a score, and we grow whatever earned it.

★ 1) باختصار: الآلة بتجرّب، والعالم بيعطيها علامة، ونحنا منكبّر كل شي جابلا ياها.  
   2) باختصار: الآلة بتجرّب، بتاخد علامة، ومنقوّي اللي جاب العلامة.  

**Decision:** 1


### ~5:44.8 – 5:47.9  ·  `bit6_recap.2`  ·  EN ~4.6s, then 0.5s pause

EN: A coin, a boat, a like button, a test: the same loop.

★ 1) ليرة، قارب، زر لايك، اختبار: نفس الدورة.  
   2) الليرة، والقارب، واللايك، والاختبار، كلّن نفس الدورة.  

**Decision:** 1


### ~5:48.4 – 5:51.4  ·  `bit6_recap.3`  ·  EN ~3.5s, then 1.0s pause

EN: It learns what we reward, not what we mean.

★ 1) بيتعلّم اللي منكافئو عليه… مو اللي منقصدو.  
   2) بيتعلّم اللي منكافئ عليه، مش اللي منقصدو.  

**Decision:** 1


### ~5:52.4 – 5:58.5  ·  `bit6_recap.4`  ·  EN ~7.7s, then 2.0s pause

EN: And to see what a model that loves "yes" does when it runs a real shop, watch this one next.

★ 1) وإذا بدك تشوف شو بيعمل نموذج بيحب «أكيد» لمّا يدير محل حقيقي… شوف هالفيديو.  
   2) وإذا حابب تعرف شو صار لمّا نموذج بيحب «أكيد» أدار محل، هاد الفيديو إلك.  

> Points the end screen at video 3, ending on content (watch_time_research.md §2.8).

**Decision:** 1


### (removed)  ·  `bit6_recap.5`  ·  EN ~5.8s, then 1.6s pause

EN: If you watched to the end, like and subscribe so you catch the next one.

★ 1) بما إنو حضرت الفيديو للآخر، حط لايك واشترك بالقناة لتشوف الفيديوهات الجاية.  
   2) وإذا عجبك، لايك واشتراك، ومنشوفك بالفيديو الجاي.  

> Removed by default: the research favours ending on content with the end screen doing the asking. Pick 1 to bring it back.

**Decision:** remove


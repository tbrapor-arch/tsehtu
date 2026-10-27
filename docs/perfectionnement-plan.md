# Part 2: 進修 Tsìn-siu (Perfectionnement), spec and handover

State on 28 Oct 2026: **P1–P49 are published** (P36–P49 on 28 Oct). Next batch: P50–P56 (P56 = review).
The second wave started at P36 (see 'Size' below).

## Batch 1 (P1–P7)
| # | genre | title | new words | lines |
|---|---|---|---|---|
| P1 | dialogue | 頂港有名聲，下港上出名 (north/south teasing) | 29 | 21 |
| P2 | tale | 天公疼戇人 (woodcutter, jar of gold, greedy rich man) | 43 | 25 |
| P3 | letter | 惜花連盆，疼囝連孫 (A-má's letter: garden, health, A-bîng's wedding in October, visit to Taipei) | 44 | 26 |
| P4 | essay | 火金蛄去佗位矣？ (newspaper column: village childhood, fireflies) | 44 | 26 |
| P5 | interview | 一錢，二緣，三媠，四少年 (radio interview with a matchmaker) | 45 | 30 |
| P6 | play | 大摒掃 (cleaning Sam's flat before A-má's visit; cockroach, rat, broken bottle) | 40 | 33 |
| P7 | review | 復習 (A-má and A-kong at Sam's flat; recombines P1–P6) | 0 | 29 |

New words ran a little above 40 in P2–P5 (vocabulary is the goal); dialogue length stayed within 20–33.

## Batch 2 (P8–P14)
| # | genre | title | new words | lines |
|---|---|---|---|---|
| P8 | news | 甘蔗無雙頭甜 (TV news: cold wave, sugarcane prices, temple burglary, drunk driver) | 44 | 27 |
| P9 | dialogue | 囝婿是半子 (A-bîng and Bí-lîng's street wedding banquet in Tainan; 四句聯) | 37 | 31 |
| P10 | article | 白話字的故事 (history of Pe̍h-uē-jī: missionaries, 1885 church newspaper, ban, Tâi-lô 2006) | 42 | 26 |
| P11 | document | 千金買厝，萬金買厝邊 (notice board in Sam's block: rules and residents' notes) | 36 | 21 |
| P12 | song | 碼頭的燈塔 (original lyrics in 1960s style: waiting on the quay) | 27 | 22 |
| P13 | story | 上尾一班車 (ghost story: last bus, cemetery stop, 收驚) | 27 | 26 |
| P14 | review | 復習 (cold night at Sam's: news, neighbours, wedding, POJ, ghost story) | 0 | 29 |

Story threads to pick up: A-má's promise to show A-tshun and A-ióng the fireflies in Tainan next summer (P7);
A-ióng still owes Sam a bottle (P6–P7); Sam's upstairs neighbour, the old man who sings all night (P11, P14);
Sam is still single (P9). Genres not used yet: speech, interview again, letter again, play again; Mazu, 土地公 and
the 普渡 are covered (P8, P11, P13), so prefer other cultural topics next.
Facts in P10 checked on 21 Oct 2026: church newspaper founded by Barclay in Tainan in 1885, Taiwan's first printed
newspaper, still weekly as 台灣教會公報; Mackay landed at Tamsui on 9 Mar 1872 and pulled thousands of teeth; POJ
New Testament confiscated in 1975 (the paper itself dropped POJ in 1969 under the ban); Tâi-lô announced by the
Ministry of Education on 7 Nov 2006 (the note first said October; corrected).

## What was decided with the user
- **Spirit:** an Assimil *Perfectionnement* volume. It is used only for ideas and counts; nothing from the
  `reference/` scan leaves that folder.
  - Longer lessons and varied genres: dialogue, article, letter, interview, tale, speech, essay, document, song, news, play.
  - Registers, slang (marked as such), set phrases and proverbs as titles, humour and culture.
  - The goal is **more vocabulary**, not a fixed thematic plan.
- **Layout:** variant A, "a second notebook".
  - On the Lessons tab, after the grid of 100, a double rule, then a cover card (進修, Part 2) and a grid of tiles P1–P70.
  - Lesson page eyebrow: `進修 N`, plus ` · Genre` when the lesson is not a dialogue.
- **Numbering:** restarts at 1.
  - Files `course/perfectionnement/NN.yaml` with `id: N`. The build turns that into internal id `100 + N`.
- **Size:** 70 lessons. Every 7th is a review. Second wave from P36, which redoes P(N−35) and stays within part 2.
- **Length:** up to the longest lessons of the reference volume. Its longest lessons have about 26 numbered
  sentences, many of them long, so aim for **20–30 lines**.
  - New words: about 30–40 per lesson; reviews have none.
- **Exercises:** as in the reference volume, two exercises of **5 items each** (translate ×5, fill the gap ×5).
- **Control rules:** the user allows relaxing them when that improves the lessons. It must never cost quality.
  - Still mandatory: 0 lint errors, `make test`, real MOE Hàn-jī and readings, `source: moe` only for exact MOE examples.

## File format (differences from base lessons)
- `genre:` (key from `GENRES` in `app/index.template.html`; default `dialogue`).
- `speaker:` may be left out or empty for prose genres. Only the line number is shown then.
- Everything else is the same as `course/lessons/_template.yaml`: notes, `new_words`, two exercises, `audio: []`.
- Cast so far: Sam back in Taipei; A-ióng (Taipei colleague, says gún, teases); A-tshun (Chiayi colleague).
  - The base course's family (A-kong and A-má in Tainan, A-hun, A-bîng) can return.
  - Prose genres don't need the cast at all.

## Method: start from the words, not from a theme
1. `python3 -I tools/coverage.py` lists frequent words not yet taught. `lint` and `coverage` already scan `course/perfectionnement/`.
2. Pick 40–60 untaught words. Group them by what can share a scene. Then choose a theme and a genre that hold 30–40 of them naturally.
3. Verify every candidate in one pass with `tools/lookup.py`: reading, MOE Hàn-jī, meaning. Then write only from verified words.
4. Look for an MOE proverb or example containing the lesson's key word, for a title or a line (`source: moe`).
5. Plan 7 lessons at a time. The 7th is a review that recombines the six, with no new words.

P1 was written the other way, theme first; its words were checked afterwards. From P2 on, use the order above.

## Batch 3 (P15–P21)
| # | genre | title | new words | lines |
|---|---|---|---|---|
| P15 | speech | 一枝草，一點露 (A-bîng's speech at A-kong's birthday banquet) | 32 | 23 |
| P16 | interview | 學師仔三年四個月 (Kim-hōng, Taiwanese-opera actress, 40 years in a troupe) | 25 | 25 |
| P17 | play | 阿勇對看 (A-ióng's blind date with Siok-tsing, an engineer; A-tshun and Sam spy) | 27 | 28 |
| P18 | letter | 寫予十冬後的家己 (Hūi-hūi, 15, writes to herself in ten years) | 35 | 22 |
| P19 | article | 地名的由來 (old place names: 打狗, 艋舺, 水返腳, 三角湧, 牛罵頭…; the 1920 renaming) | 21 | 21 |
| P20 | dialogue | 火金蛄轉來矣 (A-má's firefly outing near Tainan; A-ióng finally returns the bottle) | 28 | 27 |
| P21 | review | 復習 (back at A-má's: everyone recombines P15–P20) | 0 | 25 |

New words are lower than in batches 1–2 (21–35) because lessons 22–49 took 122 frequent words, and every 進修
word was checked with `wordcheck.py` against all lessons. Story threads now: A-ióng and Siok-tsing are together
(P17, P20); Hūi-hūi wants to be a writer (P18); A-má told Sam it's time he found a girlfriend (P20); A-tshun plans
to bring Hūi-hūi to the fireflies. Threads closed: the bottle (P6 → P20), the fireflies promise (P7 → P20).
Continuity note: lesson 5 (untouchable) says A-kong is ninety, lesson 98 says he apprenticed at eighteen fifty years
ago, and 進修 7 says fifty years of marriage. 進修 15 avoids giving his age; keep doing so.
Genres used so far: dialogue ×3, tale, letter ×2, essay, interview ×2, play ×2, news, article ×2, document, song,
story, speech. Still unused: a second song or news, a recipe-style document, a debate, a diary.

## Batch 4 (P22–P28)
| # | genre | title | new words | lines |
|---|---|---|---|---|
| P22 | diary | 阿勇的日記 (A-ióng's week: meeting Siok-tsing's parents, her father a stern retired headmaster; jealousy over his cousin) | 51 | 26 |
| P23 | tale | 龜佮兔仔走標 (A-má tells Hūi-hūi Aesop's tortoise and hare, and fox and crow) | 48 | 26 |
| P24 | interview | 食緊挵破碗 (Sam interviewed by local radio after the 10 km of the Lukang Marathon, 15 Nov 2026) | 51 | 31 |
| P25 | news | 鸚哥嘛會講台語 (TV news: coastal fog, delayed trains, low reservoirs, cabbage prices, phones at school, new road, a parrot) | 55 | 24 |
| P26 | document | 冬節愛挲圓仔 (A-má's recipe card for solstice rice balls, with customs) | 44 | 23 |
| P27 | debate | 城市抑是草地？ (Hūi-hūi's class debate, town vs country, with her classmate A-kia̍t) | 45 | 28 |
| P28 | review | 復習 (solstice at Sam's flat; A-ióng proposes to Siok-tsing over a bowl of rice balls) | 0 | 28 |

The user asked (27 Oct) to keep new words high: 44–55 per lesson here, all checked against every lesson with a
fresh `untaught.py` list. Two genres were added to `GENRES` in `app/index.template.html`: `diary` and `debate`.
P24 was requested by the user, who runs the Lukang 10 km on 15 Nov 2026. Facts from the organisers' pages
(lohasnet.tw/Lukang2026, running.biji.co): Sunday 15 Nov, start and finish at 鹿港鎮立體育場, 42/21/10/5 km, 10 km starts
06:30 with a 2-hour limit and 2,500 places, local snacks and tea at aid stations, finisher medal, cooling towel,
chopsticks and a bottle of chicken essence for the 10 km. The 10 km route map was not reachable, so Sam's lines stay
vague about the route (old streets, temples; he does not run through 摸乳巷). **Sam's time (58 min) is a placeholder:
update line 23 of P24 with the user's real time after the race** if they ask.
Story threads now: A-ióng proposed to Siok-tsing at the solstice and she said yes (P28), but he still has to ask her
father, the headmaster (P22); Sam ran Lukang and wants to try the 21 km next year; Hūi-hūi wants to be a writer and
debates with A-kia̍t (P27). Readings to keep: 抑是 ia̍h-sī (8th tone), 買 bé (as in the base course), 摸乳巷
Bong-ling-hāng (lesson 66). Siok-tsing says guán; A-ióng says gún.
Genres used so far: add diary, debate, news ×2, document ×2, tale ×2, interview ×3.

## Batch 5 (P29–P35)
| # | genre | title | new words | lines |
|---|---|---|---|---|
| P29 | letter | 希望你會使成全我 (A-ióng asks headmaster Tân, Siok-tsing's father, for her hand) | 42 | 22 |
| P30 | play | 看命無褒，食水都無 (A-ióng's mother takes the couple to fortune teller Ông to pick the wedding date) | 38 | 28 |
| P31 | essay | 三代人，三款話 (magazine column: grandfather at a Japanese-era common school, father punished for Taigi, daughter learning it) | 40 | 24 |
| P32 | song | 出外人的批 (original lyrics: a young man in Taipei sings to his mother back home) | 31 | 24 |
| P33 | speech | 神明興、弟子窮 (temple chairman's speech at the Lantern Festival in A-kong's village) | 51 | 26 |
| P34 | story | 咱逐家攏有嫌疑 (Sam's building: food vanishes at night; retired detective Lîm; the culprit is A-ióng's cat 'Boss') | 36 | 26 |
| P35 | review | 復習 (A-ióng and Siok-tsing's wedding banquet; the eighth-floor neighbour sings P32's song) | 0 | 26 |

Each lesson also has the 3 extra exercise sentences (2 translate + 1 fill, not from the dialogue, at least 80 % of the
dialogue's median length) added with `tools/exercises.py`, as for P1–P28.
Story threads now: A-ióng and Siok-tsing are married (wedding on the 8th day of the 3rd lunar month, chosen by Master
Ông); they live with three cats ('Boss' and Siok-tsing's two); the singing neighbour on the eighth floor came to Taipei
from the countryside (P32, P34, P35); Uncle Lîm on the third floor is a retired detective (P34). A-kong's village temple
worships the Royal Lords (王爺, P33).
Facts kept general on purpose: P31 gives no years except where certain (common schools from 1898; 國民學校 1941–1968);
the end of classical Chinese teaching and the punishments for speaking Taigi are told as family memories.
刑事 is used for 'police detective' (Japanese 刑事 keiji); the MOE gives only the legal sense, as the note says.
Song lessons naturally carry fewer new words (31 in P32).

## Batch 6 (P36–P42)
| # | genre | title | new words | lines |
|---|---|---|---|---|
| P36 | dialogue | 筋骨攏生鉎去矣 (Sam joins a running club by the Tamsui; meets Siù-lân 秀蘭, a physiotherapist; twisted ankle; they swap numbers) | 39 | 26 |
| P37 | document | 租厝的契約 (A-ióng and Siok-tsing's lease from Mrs Ông, with Siok-tsing's and A-ióng's notes in the margin) | 44 | 23 |
| P38 | tale | 虎姑婆 (the tiger aunt) | 35 | 27 |
| P39 | interview | 藥補不如食補 (Siù-lân's grandfather Mr N̂g, Chinese doctor, interviewed by Hūi-hūi) | 31 | 27 |
| P40 | letter | 阿公跋倒 (A-má's letter, written by A-bîng: A-kong's fall, hip operation, wheelchair) | 29 | 24 |
| P41 | play | 耳機 (Sam's first night-market date with Siù-lân; A-ióng coaches him through an earphone) | 34 | 33 |
| P42 | review | 復習 (summer in Tainan: Sam brings Siù-lân to meet A-kong and A-má) | 0 | 27 |

## Batch 7 (P43–P49)
| # | genre | title | new words | lines |
|---|---|---|---|---|
| P43 | essay | 出山彼工 (magazine column: a grandmother's funeral in Chiayi and how funerals are changing) | 42 | 22 |
| P44 | speech | 會使去投稿矣 (Hūi-hūi, 16, wins first prize with her essay 〈火金蛄的光〉) | 30 | 26 |
| P45 | dialogue | 𠢕眩船的人愛食眩船藥仔 (ferry from Pòo-tē to Má-king, Penghu; A-ióng seasick; dolphins) | 28 | 26 |
| P46 | document | 澎湖三日的行程 (A-ióng's itinerary for Penghu, with tips) | 36 | 21 |
| P47 | story | 林投姊 (Tainan ghost story, A-kong's version) | 23 | 25 |
| P48 | interview | 轉去作田 (radio interview: Bîng-tsì 明志, A-kia̍t's cousin, ex-engineer turned organic rice farmer near Chiayi) | 30 | 25 |
| P49 | review | 復習 (October harvest at Bîng-tsì's farm; Penghu tans, Hūi-hūi's next essay, Sister Pandanus, the funeral) | 0 | 27 |

Each lesson has the 3 extra exercise sentences (`tools/exercises.py`), as before.
Story threads now: Sam and Siù-lân are dating and A-kong approves (P41, P42); A-kong broke his hip in early summer and
walks with a stick (P40); A-ióng and Siok-tsing rent a flat from Mrs Ông with their three cats (P37); Hūi-hūi won a
writing prize (P44) and is writing about Bîng-tsì's farm (P49); the four friends went to Penghu in late July (P45, P46);
A-bîng has a daughter. Sam's Lukang race time in P24 (58 min) is a placeholder until the real race on 15 Nov.
New-word counts dipped in this batch (23–44, mean 33); aim back at about 40 in P50–P56.
Words used undeclared in core lessons and declared here (倒反 P44, 頭拄仔 P45, 響 P47) were kept as new words, since they had no card before.

## Lessons 22–49 were lengthened (27 Oct 2026)
122 frequent words that no lesson had used are now taught in lessons 22–49 (`docs/lessons-22-49-lengthening.md`
lists them). Don't declare them again in 進修 lessons; refer to them as "(lesson N)". Always take candidate words
from a fresh `python3 -I tools/untaught.py`, check each with `tools/wordcheck.py`, and run
`tools/taught_later.py 115 135` (進修 15–35) before publishing. Then `python3 -I tools/fresh.py 22 23 …`: for each
進修 lesson, words in its lines that no earlier lesson uses or declares and that are missing from its new_words (names and
numbers are fine; declare the rest), plus new_words already declared or used earlier. A review must show nothing.

## Checks per batch
- `python3 -I tools/lint.py course/perfectionnement/NN.yaml` (0 errors) and `make test`.
- No duplicate `new_words`: every Hàn-jī must be absent from earlier `new_words`, base course included.
  - P1 had two duplicates, 𤆬 (lesson 12) and 熱情 (lesson 92); both are fixed.
- "(lesson N)" / "(進修 N)" references in notes must point to the lesson that declares the word: `python3 -I tools/xrefs.py`
  (also reports duplicate `new_words` in 進修 lessons). The checker looks at the Hàn-jī just before the parenthesis,
  so put the reference right after the declared word, not after a phrase.
- Candidate words, in one pass: `python3 -I tools/candidates.py 參詳 好額人 … ex=1` (MOE readings, meanings, one
  example, and whether a lesson already declares the word).
- English on every card: after `build_app.py`, `app/dist/english-auto.txt` must be empty. Add any word listed there
  (names, compounds, words used but not in `new_words`) to `course/glosses_en.tsv` with a gloss that fits the lesson.
- One Hàn-jī = one declaration, whatever the reading: 照 tsiò (P12) was dropped from `new_words` because lesson 29
  declares 照 tsiàu; explain the new reading in a note instead. `xrefs.py` keys on Hàn-jī only.
- Review lessons must not bring in new words: check each word of the review against earlier `new_words` (P14 first
  drafts had 鬼, 愛人, 攬, 離經…; 鬼 was then declared in P13).
- Proverbs that are MOE *headwords* (一錢，二緣，三媠，四少年; 惜花連盆，疼囝連孫) are not in the example table, so
  they can't carry `source: moe`; quote them unaltered and say "a proverb from the MOE dictionary" in the note.
  A line that contains an MOE example plus other words is split so the example stands alone with `source: moe`.
- Language QC (cheap, run on every batch): `python3 -I tools/qc_readings.py FILES` flags character/syllable pairs
  MOE never attests; `python3 -I tools/qc_glosses.py FILES` lists glosses that don't match MOE meanings, to read by eye.
  Also read the Hàn-jī of each dialogue once, looking for Mandarin calques (早安, 彼平 for 彼爿…).
- `python3.12 -I tools/build_app.py`. Then take a phone-size Playwright screenshot of the part-2 home (`#part2`) and of the new lessons (`#lesson-10N`).
  - Click every token: P1 has 375 tokens, all with a card.
- `tools/smoke.py` loops over every lesson, P lessons included, and is slow. Run it once in the background before merging.

## Status of decisions
- Exercises: 5 + 5 (decided 20 Oct 2026). Publishing: P1 published with the part-2 section on 20 Oct 2026.
- To do: describe part 2 in `design-decisions.md`.
- P2–P7 published on 20 Oct 2026 at the user's request. Smoke run on 進修 lessons only: 0 problems.
- P8–P14 (21 Oct 2026): lint 0 errors, `make test` passes, QC clean, `english-auto.txt` empty after adding glosses.
  `tools/smoke.py` fixed the same day: the tone drill is reached through `#drills` (Practice tab), and the page
  checks now cover themes, grammar, drills, bridge, podcast, video and settings. Full run on 21 Oct 2026 (114 lessons): 0 problems, about 19 minutes.
- Language QC pass on 20 Oct 2026 (all 100 lessons + P1): 6 lessons fixed (54, 67, 68, 73, 85, 93); no other
  unattested readings, no Mandarin function words, no inconsistent readings across lessons.

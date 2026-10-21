# Part 2: 進修 Tsìn-siu (Perfectionnement), spec and handover

State on 21 Oct 2026: **P1–P7 are published**; **P8–P14 are written** on branch `perfectionnement-p8-p14`
(not yet merged into `main`, so not on the site). Next batch: P15–P21 (P21 = review).

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
Facts in P10 (Barclay 1885, Mackay 1872, 1970s Bible confiscation, Tâi-lô October 2006) were written from general
knowledge; worth a check against a source if the user wants it.

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
  The smoke script's lesson loop passes for P8–P14, but `tools/smoke.py` then times out waiting for `#tones`: the
  tone drill moved into the Practice tab (20 Oct), so the script's later steps need updating.
- Language QC pass on 20 Oct 2026 (all 100 lessons + P1): 6 lessons fixed (54, 67, 68, 73, 85, 93); no other
  unattested readings, no Mandarin function words, no inconsistent readings across lessons.

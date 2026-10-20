# Part 2: 進修 Tsìn-siu (Perfectionnement), spec and handover

State on 20 Oct 2026: the app section is built and P1 is written and published (`course/perfectionnement/01.yaml`).
Next: P2–P7 (P7 = review).

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
- "(lesson N)" references in notes must point to the lesson that declares the word.
  - Check with a short script over all `new_words`. The scratch scripts from the 20 Oct session are not in the repo.
- Language QC (cheap, run on every batch): `python3 -I tools/qc_readings.py FILES` flags character/syllable pairs
  MOE never attests; `python3 -I tools/qc_glosses.py FILES` lists glosses that don't match MOE meanings, to read by eye.
  Also read the Hàn-jī of each dialogue once, looking for Mandarin calques (早安, 彼平 for 彼爿…).
- `python3.12 -I tools/build_app.py`. Then take a phone-size Playwright screenshot of the part-2 home (`#part2`) and of the new lessons (`#lesson-10N`).
  - Click every token: P1 has 375 tokens, all with a card.
- `tools/smoke.py` loops over every lesson, P lessons included, and is slow. Run it once in the background before merging.

## Status of decisions
- Exercises: 5 + 5 (decided 20 Oct 2026). Publishing: P1 published with the part-2 section on 20 Oct 2026.
- To do: describe part 2 in `design-decisions.md`.
- Language QC pass on 20 Oct 2026 (all 100 lessons + P1): 6 lessons fixed (54, 67, 68, 73, 85, 93); no other
  unattested readings, no Mandarin function words, no inconsistent readings across lessons.

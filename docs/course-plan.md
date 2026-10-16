# Course plan: waves, stages, lessons 64–100

Decisions of 16 Oct 2026, from the audit of lessons 1–63 and a measured vocabulary coverage run.

## Terms
- **First wave**: all 100 lessons, each new (listen, read, understand). There is no `phase` field any more.
- **Second wave**: from lesson 50, finishing lesson N brings back lesson N−49, read in English first and said in Taigi.
  It never adds words to the review deck.
- **Active mode**: the toolbar switch (EN → Taigi) that any lesson can use.
- **Reviews** (7, 14, …, 98) have no new material. Because 49 = 7 × 7, a review's second wave is triggered by a review
  (56↔7, 63↔14, …, 98↔49), so it keeps its consolidation role. `nextWave()` includes reviews.
- Only lessons 1–51 get a second wave (N ≤ 100). Lessons 52–100 do not.
- The course ends: review 14 (lesson 98), then lessons 99–100 (their waves redo lessons 50 and 51).

## Stages (observed; lessons 1–63)
| Block | Lines | New words | Chars/line | Chars/dialogue |
|---|---|---|---|---|
| 1–6 | 8.3 | 17.3 | 9.6 | 80 |
| 8–25 | 7.4 | 11.5 | 10.5 | 78 |
| 26–49 | 7.5 | 13.4 | 13.5 | 102 |
| 51–63 | 15 | 14.5 | 16.8 | 253 |

A = 1–25 (31 of 39 grammar sheets first appear here). B = 26–49. Lessons 50–100 are dense (the jump is at 50–51, not 76).
Stage C (76–100) is defined by content: formal and written register, literary readings, narrative and discourse
connectors, proverbs. No grammar sheet is new after lesson 53.

## Coverage (core vocabulary: 4,265 words; measured with `tools/coverage.py` after lessons 1–63 and the Health theme)
Top 100: 99 % · top 300: 90 % · top 500: 85 % · top 1,000: 72 % · top 2,000: 53 % · whole core: 36 % (1,526).
Of the 274 top-1,000 words still missing, 236 share their characters with Mandarin (a pronunciation job); 9 are hard:
總是, 娘仔, 落, 搤, 坐, 無愛, 查某人, 摃, 礪.
Targets for lessons 64–100 (32 new lessons, 5 reviews, about 15 new words each): top 300 ≥ 97 %, top 1,000 ≥ 95 %,
top 2,000 ≈ 60 %, whole core ≈ 47 %. Check with `python3 tools/coverage.py` (after `make db`).

## Lessons 64–100
`course/syllabus.yaml` holds the topic (`focus`) and, for each new lesson, a `plan:` with the gaps to fill. Rules:
- Dialogues 15–18 lines until about 84, then 18–20; never more than 20. Reviews about 10 lines.
- 14–16 new words per lesson, never a word already declared new in an earlier lesson (37 words were declared twice
  in lessons 1–63; do not add to that).
- A sandhi or pronunciation note every 3–4 lessons (none since lesson 5 in lessons 1–63).
- Rare structures to place and recycle: 咧欲, 仔 á sandhi, 枝 本 逝, 囉 哩, 上蓋, 連…嘛, 毋管, 袂輸, 毋但, 因為/所以, 予 passive,
  有夠, 若是. Missing frequent words to place early: 就, 最, 雖然, 但是, 別人, 學生, 看見, 本, 後來.
- Exercises stay as they are: translate and fill the gap.
- Story: the characters are a backdrop. Sam stays with A-má in Tainan from lesson 51 (see its setting). Lessons 90, 92
  and 100 (leaving Tainan, back in Taipei, farewell party) are not written yet; keep them consistent with that.

## Titles
Lesson files win over the syllabus where they differ: 29 Riding a scooter, 39 Seeing the doctor; 34 is now "A typhoon is
coming" and 61 "Learning to cook braised pork rice" in both.

# Course content

Audience: English-speaking learners who already read Traditional Chinese and speak Mandarin at around B2 / HSK 5.
The course leans on that: words with the same characters as Mandarin are learned as pronunciation, and teaching time
goes to false friends, Taigi-only words, colloquial readings, tone sandhi and grammar words.

## Shape
- Short daily lessons: a dialogue, notes, two small exercises.
- Every 7th lesson is a review lesson with no new material.
- First wave: lessons 1-100, each new (listen, read, understand). Second wave: from lesson 50, finishing lesson N
  brings back lesson N-49 (reviews included: a review's wave is triggered by a review), read in English first and
  said in Taigi. Lessons 52-100 get no second wave of their own. See `docs/course-plan.md`.

## Priority
Coverage of vocabulary and structures comes first; the recurring characters (Sam, A-bîng and family) are only a
backdrop, and lessons may stand alone. `make coverage` shows how much of the core vocabulary the lessons cover and
lists the most frequent words not yet taught, to pick from when writing the next lessons.

## Rules for content
1. Everything here is original. No sentences, dialogues, storylines or notes from published courses.
2. Romanisation is Tâi-lô only (MOE system). Characters follow the MOE dictionary's recommended Hàn-jī.
3. Every word in a dialogue must be found in `data/build/taigi.db` (checked by `make lint`).
4. A sentence copied from the MOE dictionary is marked `source: moe` and is not edited.

## Lesson file format (`lessons/NNN.yaml`)
See `lessons/_template.yaml`. Check lessons with `make lint`.

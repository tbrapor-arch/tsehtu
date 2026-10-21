# Project notes (state as of 20 Oct 2026)

Migrated from a long Claude Project conversation. In that conversation lessons were written with four Assimil
course files as a model for pacing and structure only (kept in the git-ignored `reference/`).

## Status
- **Lessons:** all 100 written (`course/lessons/`), following `course/syllabus.yaml`. Lesson 0 is
  `000-reading-tailo.md`. Review lessons: 7, 14, …, 98.
- **Part 2, 進修 Perfectionnement** (in progress): 70 longer lessons in varied genres, P1–P7 published. Spec, method and handover: `docs/perfectionnement-plan.md`.
- **Themes:** four domains done: `health` (Body and health, 212 words), `food` (128), `home` (160), `clothing` (49); draft domain for every core word in `docs/themes-classification-draft.tsv`. The Themes part of Practice is to become a thematic vocabulary dictionary: `docs/themes-taxonomy.md`.
- **Coverage** (after lesson 100): top 100: 100 %, top 300: 97 %, top 1,000: 88 % (72 % after 63). The plan's 95 % target for the top 1,000 was not reached. Plan for lessons 64–100: `docs/course-plan.md`.
- **Grammar sheets:** 39 structures in 7 groups (`course/grammar.yaml`).
- **App tabs:** Lessons, Practice (溫習: Vocabulary by theme, Grammar, Drills = tone changes + Bridge, Cards; merged 20 Oct 2026), Podcast, Video, Settings, plus a hidden
  Exam tab that exists only when this device's token can read the private repo.
- **Audio:** MOE headword and example recordings are fetched at build time by the workflow. Native-speaker
  recordings: tooling done (`record.html`, `tools/import_recordings.py`), **no clips imported yet**.
- **Podcast tab:** 《隔壁 ê 戇人》, show notes from the RSS feed, audio streamed from SoundOn.
- **Video tab:** 《市井豪門》 (FTV drama, official YouTube uploads), episodes listed in `course/video.yaml` (EP1 so far),
  played in YouTube's embedded player. Transcripts are private. See `docs/video.md`.

## Repository rules
- Public repo: no exam papers, answers, recordings, transcripts, tokens or text derived from the ministry's exam
  material or from podcast audio; those live in the private repo.
- `reference/` (Assimil files, git-ignored): only counts and pacing ideas may leave it, never text or storylines.
- Never commit generated data (`data/raw`, `data/build`, `app/dist`, `*.db`) or ministry audio.
- MOE dictionary text is CC BY-ND: quote unaltered, mark copied lines `source: moe`. Maryknoll/Embree glosses
  (non-commercial) never go into `course/`. `course/audio/` clips belong to the speaker.
- A push to `main` rebuilds and deploys the site. The Taigi is not native-checked.

## Writing lessons (fast loop)
Format `course/lessons/_template.yaml`; rules `course/README.md`, `docs/course-plan.md`. Per lesson:
`python3 -I tools/lint.py course/lessons/NNN.yaml` (0 errors; W/I warnings tolerated) and `make test`.
`make app` (Python 3.12) before a push. `tools/smoke.py` is a full regression run (clicks every token of every
lesson, no single-lesson option, slow): run it in the background after app/template changes, not per lesson.
Workflow that keeps cost down: plan a batch of lessons together, verify all candidate words with
`tools/lookup.py` in one pass, then draft dialogue only from verified words. Cross-references such as
"(lesson 40)" in notes must point to the lesson that declares the word in `new_words`; check them with a script
before committing. Language QC: `tools/qc_readings.py` and `tools/qc_glosses.py` (see `docs/perfectionnement-plan.md`) (lessons 64–76 had many guessed numbers, fixed on 20 Oct 2026).

## Decisions (why)
- Mandarin B2 learner: same-character words are taught as pronunciation; time goes to false friends and Taigi-only words.
- 100 lessons, review every 7th, second wave from 50, two exercises per lesson (`course/pacing.md`).
- Notebook look, always white, night mode manual (`design-decisions.md`).
- Progress stays in the browser; optional sync through a secret gist.
- Native-speaker clips are committed to `course/audio/lessons/` (git ignore has an exception for them).
- Build fails soft: MOE audio and the podcast feed are optional, the site deploys without them.
- Every word card has English (`tools/english.py`): words not in `new_words` get a gloss from `course/glosses_en.tsv`;
  new words that fall back to automatic English are listed by `make app` (`app/dist/english-auto.txt`).
  Course English is matched on characters + reading (fixed 21 Oct 2026: homophones took each other's English).

## Open items
- Classify the vocabulary for Themes (in Practice), starting with a pilot domain. Optional: a native-speaker pass over lessons 64–100 (written 16–20 Oct 2026, not native-checked).
- Record lessons with a native speaker; lines she flags go to `course/audio/flags.yaml`.
- Sync/exam token expires about 12 Nov 2026 (30-day token); see `docs/sync-and-private-module.md`.
- The podcast feed URL is hard-coded in `tools/fetch_podcast.py` and also in the private repo's tools. Change all copies together.
- Not run since the wave/phase change: `tools/smoke.py` (lint, sandhi tests and `make app` were, after every batch up to lesson 100).
- Story 64–100: Sam stays several months in Tainan (51 said 'a few weeks'; 90 acknowledges it ran long), A-hun moves to Taipei (82–84), Sam returns to Taipei (90–92), colleague A-tshun (92–98), A-bîng's engagement (99), New Year's Eve reunion in Tainan (100). The A-kong/A-hun family surname is 林 Lîm (lessons 52, 98).

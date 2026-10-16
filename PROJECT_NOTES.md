# Project notes (state as of 16 Oct 2026)

Migrated from a long Claude Project conversation. In that conversation lessons were written with four Assimil
course files as a model for pacing and structure only (kept in the git-ignored `reference/`).

## Status
- **Lessons:** 1–63 written (`course/lessons/`), 64–100 planned as titles in `course/syllabus.yaml`. Lesson 0 is
  `000-reading-tailo.md`. Review lessons: 7, 14, …, 63 so far.
- **Themes:** one (`health`). The app is built for several.
- **Grammar sheets:** 39 structures in 7 groups (`course/grammar.yaml`).
- **App tabs:** Lessons, Themes, Grammar, Review (includes Bridge and tone drill), Podcast, Settings, plus a hidden
  Exam tab that exists only when this device's token can read the private repo.
- **Audio:** MOE headword and example recordings are fetched at build time by the workflow. Native-speaker
  recordings: tooling done (`record.html`, `tools/import_recordings.py`), **no clips imported yet**.
- **Podcast tab:** 《隔壁 ê 戇人》, show notes from the RSS feed, audio streamed from SoundOn.

## Decisions (why)
- Mandarin B2 learner: same-character words are taught as pronunciation; time goes to false friends and Taigi-only words.
- 100 lessons, review every 7th, second wave from 50, two exercises per lesson (`course/pacing.md`).
- Notebook look, always white, night mode manual (`design-decisions.md`).
- Progress stays in the browser; optional sync through a secret gist.
- Native-speaker clips are committed to `course/audio/lessons/` (git ignore has an exception for them).
- Build fails soft: MOE audio and the podcast feed are optional, the site deploys without them.

## Open items
- Write lessons 64–100 and more themes; fit the grammar-inventory stages A/B/C to real lessons.
- Record lessons with a native speaker; lines she flags go to `course/audio/flags.yaml`.
- Sync/exam token expires about 12 Nov 2026 (30-day token); see `docs/sync-and-private-module.md`.
- The podcast feed URL is hard-coded in `tools/fetch_podcast.py` and also in the private repo's tools. Change all copies together.
- `tools/smoke.py` and the lesson dialogue lengths have not been re-checked since the lessons 57–63 were added.

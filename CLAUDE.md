# Tsheh-tû (冊櫥) — instructions for Claude

A Taiwanese (Taigi) course in English for Mandarin speakers (about B2 / HSK 5), with a vocabulary database and a
reader app. Public repo: https://github.com/tbrapor-arch/tsehtu. Start with `PROJECT_NOTES.md` for the current state.

## Hard rules
- **Public repo.** Never add exam papers, answers, recordings, transcripts, tokens, or any text derived from the
  ministry's exam material or from podcast audio. All of that lives in the separate private repo. This repo may say
  only, generically, that an optional private module is loaded at run time (see `docs/sync-and-private-module.md`).
- **`reference/` is git-ignored** (it holds the Assimil course files). From it only ideas and counts may leave the
  folder (lesson counts, pacing, which topic appears when). Never sentences, dialogues, notes, characters,
  storylines or audio. Lesson content is original.
- **Do not commit, push or publish unless asked.** A push to `main` rebuilds and deploys the public site.
- Do not commit generated data (`data/raw`, `data/build`, `app/dist`, `*.db`) or ministry audio.
- Do not alter MOE dictionary text (CC BY-ND): quote it unaltered, mark copied lines `source: moe`.
- `course/audio/` recordings belong to the speaker, used with permission in this app only (not CC BY-SA).
- Maryknoll/Embree glosses (non-commercial) never go into `course/`.

## Commands (Python 3.9+ for the database, lint and tests; `tools/build_app.py` needs 3.12, as in CI. The Makefile uses `python3 -I`)
`make db` (downloads pinned sources, builds `data/build/taigi.db`) · `make lint` · `make test` (tone sandhi) ·
`make coverage` (what to teach next) · `make app` (writes `app/dist/index.html`) ·
`python3 tools/smoke.py` (needs Playwright). `make db` and the audio/podcast fetches use the network.

## Writing lessons
Rules are in `course/README.md`, `course/pacing.md`, `course/grammar-inventory.md`; the file format is
`course/lessons/_template.yaml`. In short:
- Waves: all 100 lessons are the first wave; from lesson 50 the second wave redoes N−49 (reviews included). There is no `phase` field. See `docs/course-plan.md` for stages, targets and the plan for lessons 64–100.
- Lesson `NNN.yaml`: dialogue (Hàn-jī + Tâi-lô + English), notes, new words, two exercises (translate, fill the gap).
- Tâi-lô only, MOE Hàn-jī. Every word must exist in the database: run `make lint` (and `make test`) before finishing.
- Every 7th lesson is a review; lessons 50+ get a second wave (N ↔ N−49). Dialogues 8–10 lines early, 15–20 later.
- Vocabulary and structures come first; Sam, A-bîng and family are only a backdrop. Pick content with `make coverage`.
- Spend note space on false friends, Taigi-only words, colloquial readings, tone sandhi and grammar words.
- The Taigi is not native-checked. Do not claim it is.

## Where things are
`course/` content · `tools/` build and checks · `app/index.template.html` the whole app (one file) ·
`design-decisions.md` look and app structure · `docs/themes-taxonomy.md` plan for the Themes dictionary · `ATTRIBUTION.md` / `LICENSE-CONTENT.md` licences · `docs/` references.

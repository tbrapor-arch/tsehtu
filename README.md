# 冊櫥 Tsheh-tû

A Taiwanese (Taigi / 台語) course in English for people who already speak Mandarin, with an open vocabulary database
behind it. Romanisation: **Tâi-lô**, the Ministry of Education system.

## Layout
```
course/        lessons, themes, syllabus (YAML), original content — CC BY-SA 4.0
app/           reader app template; `make app` writes app/dist/index.html
tools/         database build + lookup scripts — MIT
data/fetch.sh  downloads open data sources at pinned commits (nothing committed)
data/build/    generated: taigi.db, core_vocab.csv (git-ignored)
reference/     your local, git-ignored reference material
```

## Build the database
Needs Python 3.9+ and git.
```sh
make db                 # → data/build/taigi.db, data/build/core_vocab.csv
make lookup W=喜歡       # Mandarin or Taigi characters
make lookup W=khuann3   # Tâi-lô, numeric or with diacritics; no tone = any tone
```
`make db-nc` also adds English glosses from two non-commercial dictionaries (Maryknoll, Embree). Those builds must
not be used commercially.

## Writing and checking lessons
```sh
make lint               # every word in course/lessons/*.yaml and course/themes/*.yaml must exist in the database
make test               # tone sandhi engine tests
make coverage           # how much of the core vocabulary the lessons cover, and what to teach next
make app                # build the reader app: app/dist/index.html, one self-contained page
python3 tools/sandhi.py "Guá sī | Huat-kok-lâng."   # spoken tones for a line
```
Start with `course/README.md`, `course/syllabus.yaml`, `course/grammar-inventory.md` and
`course/lessons/000-reading-tailo.md`.

## The app
`make app` writes `app/dist/index.html`, one self-contained page (works offline, progress kept in the browser).
On every push to `main`, `.github/workflows/pages.yml` rebuilds everything, adds the MOE headword recordings
(`tools/fetch_audio.py`) and publishes the site on GitHub Pages. One-time setup: Settings › Pages › Source:
GitHub Actions. `python3 tools/smoke.py` clicks through every lesson in a phone-sized browser (needs Playwright).

## Native-speaker recordings
`record.html` (published with the site: https://tbrapor-arch.github.io/tsehtu/record.html) lets a speaker record
the dialogues line by line on a phone; clips stay in her browser until she sends a zip. Import it with
`python3 tools/import_recordings.py file.zip` (silence trimmed, loudness evened out, MP3 in `course/audio/lessons/`),
then commit. The recordings are used with the speaker's permission in this app only: they are not under the
course licence (see `LICENSE-CONTENT.md`). The name shown in the app is `voice` in `course/audio/recordings.yaml`.

## What the database gives you
- ~140k headwords from the MOE dictionary, iTaigi, 台華線頂對照典 and the 1956 basic sentences
- MOE definitions, example sentences with Mandarin translations, regional variants
- word frequency from a 1.5M-word written corpus, with homophones split by character alignment
- for each word: the Mandarin equivalent you probably know, its HSK level, and whether it is a same-character
  cognate, a false friend (`same-chars-diff-use`), or a Taigi-only word (`different`)
- `v_core`: a ranked list of ~4,300 core words

See `tools/schema.sql` for tables and `ATTRIBUTION.md` for sources and licences.

## Licences
Code: MIT (`LICENSE`). Course content: CC BY-SA 4.0 (`LICENSE-CONTENT.md`). Data sources keep their own licences
(`ATTRIBUTION.md`); they are downloaded, not redistributed.

# Tsheh-tû (冊櫥) — design decisions

## Look
- **Default: "Notebook" (cahier d'élève), matched to mockup B.** White paper with a light blue 24px grid, red margin
  line, cobalt blue ink #2347B5 (Tâi-lô above the characters, eyebrows), red pen #D23F38 for speaker labels and false
  friends, yellow marker #FFD84D for highlights. Dialogue lines are written straight on the page (no cards); word and
  note cards are boxy with a 2px border and a blue offset shadow. Hàn-jī in **Iansui**, Tâi-lô in **Noto Sans** (full
  Latin Extended + combining marks: ē, a̍ never break), UI labels in **Atkinson Hyperlegible**.
- **Always white**, whatever the phone's dark mode. Night mode is a manual switch in Settings (dark paper, light ink).
- **Kept as option: "Rose".** Blush #FFF0F3 ground, rounded white cards, raspberry #C93466 accent, Nunito + Noto Sans TC.
- Rejected: "Night market" (dark plum, neon pink/orange, chat bubbles).

## Rare characters
Characters missing from common fonts (𠢕 𪜶 𨑨 𤆬 𬦰 …) are embedded at build time from Plangothic (OFL), subset to
what the app uses.

## App structure
Tabs: **Lessons** (home = grid of the 100 planned lessons, Mainichi-style; review every 7th; the 63 written so far, the
rest greyed with their planned title) · **Practice 溫習** (one tab since 20 Oct 2026, to keep the phone bar to five tabs: the due count and "Review all due"
on top, then a switch Cards · Themes · Grammar · Drills; the tab reopens the part used last. Cards: segmented by lesson
and theme group, cloze cards in the lesson sentence, Leitner 1/3/7/16/35 days; a card session always runs on `#review`.
Themes: thematic vocabulary, "Le Mot et l'Idée" structure, numbered groups + a short text. Grammar: the sheets.
Drills: tone-change practice and the **Bridge** trial; old routes `#themes`, `#grammar`, `#bridge` still work) · **Podcast** (see `docs/podcast.md`) · **Video** (Taigi drama in YouTube's player, `docs/video.md`) ·
**Settings** (look, night mode, accent + regional tables, sync). A hidden **Exam** tab appears only on devices with
access to an optional private module (`docs/sync-and-private-module.md`). No "Today" tab.

## Lesson page
Toolbar: active mode (EN → Taigi), script (漢字 + Tâi-lô / Tâi-lô / 漢字), spoken tones, English. Notes open as pop-ups
from the numbers under each line (previous / next); the full list is folded at the bottom. Then New words, Practice,
and a Pronunciation section listing the lesson's words that have other common readings (pick the one to display).

## Word card
Header (characters, Tâi-lô, close button) stays visible while scrolling. Order: label (Taigi only / false friend…),
English, Mandarin equivalents with pinyin and English (CC-CEDICT), MOE definitions (Chinese, unaltered: CC BY-ND),
example, pronunciation choices, "Around Taiwan" table (folded), parts, add to review.

**English on every card** (`tools/english.py`, also used by the private module for podcast transcripts and exam
texts): the lesson/theme `new_words` English, else `course/glosses_en.tsv` (short glosses written for the course from
the MOE meanings), else automatic: Maryknoll (only in `make db-nc` builds), the CC-CEDICT English of the Mandarin
equivalent, or the parts joined with "+". Automatic English shows its source in small print under it. `make app`
prints the count per source and lists automatic ones in `app/dist/english-auto.txt`: add those to the TSV.

Progress, deck and preferences are stored in the browser only (per device).

## Conveniences (from Mainichi)
- **Lessons home:** "Next lesson" card (Start / Resume, done today, streak), a second-wave card when one is due,
  lesson tiles marked ✓ and with a small **2** once their second wave is done, a dated **journal** (folded).
- **Lesson bar** (stays at the top): back, "Lesson N · title", previous / next (also ← → keys). Section chips:
  Dialogue, Notes, New words, Practice, Pronunciation.
- **Second wave** has its own page (`#wave-N`): English shown, "Show Taigi" per line or all at once, mark as done.
  It no longer switches every lesson into active mode. Reviews have a second wave too (a review's wave is triggered by a review).
- **End of lesson:** mark as done (dated; new words go to review), undo, next lesson.
- **Script modes:** 漢字 + Tâi-lô · Tâi-lô on tap (first tap shows the reading, second opens the card) · Tâi-lô · 漢字.
- **Practice** accepts tone numbers (bue7 = buē). **New words:** copy for Anki (tab-separated).
- **Review:** keys space / 1 / 2; score counts words remembered the first time and lists the missed ones.
- **Word card:** ▶ Listen (MOE recording, when the site was built with audio); tapping outside closes it.
- **Settings:** save / load a progress file (to move progress between devices), review audio on / off.
- Back to the lesson grid returns to where you were.

## Learning tools added (no native speaker needed)
- **Grammar** (文法, in Practice): 39 structures from `course/grammar.yaml`; each sheet lists every course line that uses it
  (found by a pattern at build time), so new lessons add examples by themselves.
- **Tone-change practice** (Practice › Drills): words from the lessons, written form shown, pick the spoken form; wrong
  options are typical mistakes (no change, last syllable changed too, wrong new tone). Rule-based (`tools/sandhi.py`).
- **Recordings**: headwords and MOE example sentences (▶ on the word card), fetched at build time by the GitHub
  workflow. Dialogue lines: ▶ plays the words one by one (dictionary tones, not connected speech).
- **Sync**: on the hosted app, progress can be kept in a secret GitHub gist (token with Gists read/write only,
  stored in the browser). Merge: earliest finish dates, latest review of each card.

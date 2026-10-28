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
on top, then a switch Vocabulary (themes) · Grammar · Drills · Cards; the tab reopens the part used last. Cards: segmented by lesson
and theme group, cloze cards in the lesson sentence, Leitner 1/3/7/16/35 days; a card session always runs on `#review`.
Themes: thematic vocabulary, "Le Mot et l'Idée" structure, numbered groups + a short text. Grammar: the sheets.
Drills: tone-change practice and the **Bridge** trial; old routes `#themes`, `#grammar`, `#bridge` still work) · **Podcast** (see `docs/podcast.md`) · **Video** (Taigi drama in YouTube's player, `docs/video.md`) · **Music** (Taigi songs, official music videos in the same player, `docs/music.md`) ·
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
The `new_words` English is matched on **characters + reading**, not on the reading alone: a homophone must never
take another word's English (until 21 Oct 2026 it did: 闊 khuah showed 渴's "thirsty", 講 kóng 管's "tube", 的 ê 鞋's
"shoe" — 60 cards). The course English is stored per (characters, reading) pair, so 踮 tiàm 'stay at' and 店 tiàm 'shop' each keep
their own (a second pass on 21 Oct 2026 fixed 52 more cards). The reading alone is used only for a romanised word.
After changing `tools/english.py`, diff every card's `gloss` before/after a `make app` build.
A word's card is taken from a dictionary entry only if that entry writes the word with the same characters (or
variant forms: 臺/台, 脣/唇, 份/分…, `cards.VARIANT_PAIRS`). Before 28 Oct 2026 any entry with the same sound could be
taken (扇 sì got 四's card, 爸 pa 巴's, 第四 地勢's): a word with no entry of its own now gets a card built from its
characters instead.

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
- **Word card:** ▶ Listen (MOE recording, when the site was built with audio); tapping outside closes it; on a
  phone, swiping it down closes it too (drag from the top of the card: past 90 px or a quick flick closes, else it
  springs back).
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

## One word card everywhere (27 Oct 2026)
- **Shared builder** `tools/cards.py`: the lessons and the private module (podcast, drama, songs, books, exam texts)
  build their word cards with the same code, so a word has the same card wherever it is tapped.
- **Same cut**: a transcript line is cut by its own Tâi-lô words, as a lesson line is; only a line whose Hàn-jī and
  Tâi-lô do not line up (and texts without Tâi-lô: exam questions, books) is cut by the dictionary.
- **Compound line**: a card of two or more characters shows the dictionary words it is made of, each with its English
  (fewest pieces, then the most frequent words: 紅菜頭 = 紅 + 菜頭). A character found only inside words lists them.
- **Other splits**: the card of a tapped word offers the other dictionary words starting on the same character
  (毋過 / 毋), as chips; "a word" here means an MOE word, since the other dictionaries list phrases (真好, 我欲) as words.

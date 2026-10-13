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
Tabs: **Lessons** (home = grid of the 100 lessons, Mainichi-style; review every 7th; unwritten ones greyed with their
planned title) · **Themes** (thematic vocabulary, "Le Mot et l'Idée" structure: numbered groups + a short text) ·
**Review** (segmented by lesson and theme group; cloze cards in the lesson sentence; Leitner 1/3/7/16/35 days) ·
**Bridge** (trial: guess the Taigi reading of a Mandarin character, with the sound rules) · **Settings** (look, night
mode, accent + regional tables). No "Today" tab.

## Lesson page
Toolbar: active mode (EN → Taigi), script (漢字 + Tâi-lô / Tâi-lô / 漢字), spoken tones, English. Notes open as pop-ups
from the numbers under each line (previous / next); the full list is folded at the bottom. Then New words, Practice,
and a Pronunciation section listing the lesson's words that have other common readings (pick the one to display).

## Word card
Header (characters, Tâi-lô, close button) stays visible while scrolling. Order: label (Taigi only / false friend…),
English, Mandarin equivalents with pinyin and English (CC-CEDICT), MOE definitions (Chinese, unaltered: CC BY-ND),
example, pronunciation choices, "Around Taiwan" table (folded), parts, add to review.

Progress, deck and preferences are stored in the browser only (per device).

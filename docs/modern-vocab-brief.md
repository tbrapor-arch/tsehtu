# Brief: modern vocabulary themes beyond MOE (for a new conversation)

Written 3 Nov 2026 at the end of 進修 (P1–P70 published). Paste "Read claude/modern-vocab-brief.md and start" into a
new conversation in this project.

## Goal
Add a few thematic vocabulary sheets for everyday modern life that the course lacks, taking words from **iTaigi** when
the MOE dictionary has no entry. User's words: "quelques fiches de vocabulaire moderne courant (téléphone, travail,
administration), en prenant les mots d'iTaigi quand le MOE ne les a pas."

## Why
Coverage after 進修: 94 % of the top 1,000 MOE core words, 87 % of the top 3,000. The gaps left are literary words and
modern ones MOE simply doesn't have (phones and apps, office work, banks, forms, transport cards, mahjong…). The 進修
batches hit this wall: several planned themes (mahjong rules, a cold-wave bulletin, the future of Taigi) were dropped
for lack of MOE words.

## Where it fits in the app
- Themes (Practice tab), files `course/themes/NN-id.yaml`. Seven domains exist: 01 people, 02 health, 03 food,
  04 home, 05 clothing, 06 nature, 07 places. Format: `id`, `title {en, hanji, tailo}`, `intro`, `sections:` each with
  `n`, `title`, `words: [{hanji, tailo, en, zh}]`, optional short `text` lines. See `docs/themes-taxonomy.md`
  (16 planned domains; 09 Work, money, business, 10 Education, language, media and 11 Society, law, politics are
  still to do; the taxonomy currently puts iTaigi out of scope, so this brief extends it).
- Repo tbrapor-arch/tsehtu; build `python3.12 -I tools/build_app.py`; checks `python3 -I tools/lint.py` (0 errors),
  `make test`; English on every card (`app/dist/english-auto.txt` must be empty of the new words → `course/glosses_en.tsv`).
- Database `data/build/taigi.db`, table `entry` with `source` in moe (27k), itaigi (20k), taihoa (88k), tgb (5k).
  iTaigi entries have Hàn-jī + Tâi-lô but often several competing forms: pick the most voted / most attested form.

## Suggested first sheets (each about 40–60 words, sections of about 10)
1. Phone and internet: 手機仔, 充電, 網路, 密碼, 訊息, 下載, 截圖…
2. Work and office: 上班, 開會, 請假, 加班, 薪水, 老闆/頭家, 履歷, 面試…
3. Administration and bank: 申請, 表格, 簽名, 身份證, 戶口, 帳戶, 轉帳, 繳費, 郵局…
4. Transport and city services: 悠遊卡, 捷運, 公車, 停車, 罰單…
Choose words a learner hears daily; MOE form first when it exists, iTaigi otherwise, and mark the source in the sheet.

## Open questions for the user
- New domain files (e.g. 09-work.yaml) or one "modern life" file?
- Should a sheet get a short text or dialogue, as in health sections 1–4?
- How to show an iTaigi-sourced word (small badge on the card?).

## Rules carried over from 進修
Linguistic quality first; check every reading against the source; English gloss on every word; one Hàn-jī = one
card across the course; push to a `wip-…` branch after each sheet and keep a progress file, so an interrupted session
can resume (user's standing request).

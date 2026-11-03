# Modern vocabulary sheets: progress

Brief: project doc `claude/modern-vocab-brief.md`. Branch `wip-modern-vocab`, pushed after each sheet; merged to main at the end.

## Decisions (user, 3 Nov 2026)
- Sheets go into the taxonomy domains: phone and internet → `10-media.yaml` (id `media`), work and bank → `09-work.yaml`
  (id `work`), administration and post → `11-society.yaml` (id `society`), transport and city services → new sections
  in `07-places.yaml`. Each domain file will later also take its core MOE words.
- Every group (section) ends with a short text that reuses its words.
- A word MOE lacks is taken from iTaigi and marked `source: itaigi` in the YAML; the app shows a small "iTaigi" badge
  after the Hàn-jī in the theme lists (the word card already names the source dictionary).

## Rules
- MOE form first; iTaigi only when MOE has no entry. No word from 台華線頂 or the 1956 sentences alone.
- iTaigi has no vote counts in the ChhoeTaigi export: when it gives competing forms, take the one with the most rows
  (or a reading that agrees with MOE's reading of the same characters, e.g. 上傳 tsiūnn-thuân like MOE 上網
  tsiūnn-bāng), and leave the word out when the forms are a toss-up (截圖 tsia̍t-tôo / tsue̍h-tôo).
- One word in one theme only: words already in another theme file stay there (手機仔 and 電腦 are in 04 home).
- `tools/lint.py` checks `source: itaigi` words against iTaigi (E if not an iTaigi entry, W if MOE has the Hàn-jī).

## Sheets
1. Phone and internet — `10-media.yaml` sections 1–5, 44 words (11 from iTaigi), texts in every section. DONE
2. Work and office — `09-work.yaml` sections 1–4, 40 words (1 iTaigi). DONE
3. Administration, bank and post — `09-work.yaml` sections 5–6 (bank, paying; 22 words, 1 iTaigi) + `11-society.yaml` sections 1–3 (forms, district office, post; 25 words, 1 iTaigi). DONE. Left out: 身分證 (only in 台華線頂), 填 (MOE 填 thiām means "sink money", not "fill in").
4. Transport and city services — `07-places.yaml` sections 9–11 (MRT and buses, the road, city services), 36 words (5 iTaigi). DONE

All four sheets done 3 Nov 2026: 167 words, 19 from iTaigi; merged to main. Left out as toss-ups or missing from
MOE and iTaigi: 截圖, 身分證, 填 (fill in), 便利商店 (three competing iTaigi forms), 提款機, 安全帽, 鍵盤.

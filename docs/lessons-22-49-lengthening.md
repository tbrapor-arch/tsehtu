# Lessons 22–49 lengthened (27 Oct 2026): handover

## Why
The user read lessons 1–21 (keep them untouched) and found that the length curve jumped from 7–8 lines (lessons
22–49) straight to 15 lines (lesson 51). Assimil-style courses climb gradually (8, 10, 12…). So lines were added to
lessons 22–49, published straight to `main` as the user asked.

## What was decided with the user
- **Lessons 1–21 are not touched.**
- **Target curve:** 22–27 → 10 lines, 29–34 → 10–11, 36–41 → 11–12, 43–48 → 13–14; reviews 28, 35, 42, 49 → 7–9.
- **Lines are added at the end** of the dialogue (the scene continues); the last added line is the richest,
  "complicated" one. Existing lines were left alone.
- **New words: only words never used anywhere in the course** (base lessons, 進修, themes, exercises) and never
  declared: aim for 4–5 per lesson (3–7 in practice; 122 in all). Reviews add none and only recombine.
- Everything else in the added lines must already be taught by that lesson (no word from a later lesson).

## Result
| Lesson | Lines | Words added to `new_words` |
|---|---|---|
| 22 | 8 → 10 | 觀音 有時 心事 希望 毋才 |
| 23 | 8 → 10 | 正月 初一 姊夫 外家 掃地 大姊 |
| 24 | 8 → 10 | 一般 暫時 勉強 請假 |
| 25 | 7 → 10 | 頂頭 拄拄 西爿 方向 淡薄 |
| 26 | 7 → 10 | 時常 唸歌 歌仔 欣賞 做伴 |
| 27 | 7 → 10 | 竟然 忍耐 只好 電風 何必 |
| 28 | 4 → 7 | — |
| 29 | 7 → 11 | 路頭 勻勻仔 設使 萬萬 醫 |
| 30 | 8 → 11 | 現金 卡 號碼 百萬 外面 |
| 31 | 7 → 10 | 尪仔 可愛 蝴蝶 快活 |
| 32 | 7 → 11 | 兄弟 老實 熱心 好意 做人 人情 |
| 33 | 8 → 11 | 感激 糊塗 失禮 原本 果然 |
| 34 | 8 → 11 | 烏暗 西北雨 大水 腰 |
| 35 | 5 → 8 | — |
| 36 | 8 → 12 | 風景 沙埔 蝦仔 海底 清水 |
| 37 | 8 → 12 | 將軍 英雄 奸臣 專門 出手 出頭 |
| 38 | 8 → 12 | 料理 本錢 大約 豐富 |
| 39 | 7 → 11 | 痛苦 愛睏 確實 傷害 程度 |
| 40 | 7 → 11 | 勞力 田園 種作 闊 一寡仔 犧牲 功勞 |
| 41 | 8 → 12 | 冤枉 後悔 憂悶 安慰 解決 |
| 42 | 5 → 8 | — |
| 43 | 8 → 13 | 愛情 心愛 難得 鴛鴦 欣羨 參加 |
| 44 | 8 → 14 | 夾 疼痛 飫 |
| 45 | 8 → 14 | 樹林 羊仔 田螺 冬天 山頭 烏雲 |
| 46 | 8 → 14 | 比較 信心 半價 隨便 價值 |
| 47 | 7 → 13 | 計較 不得已 臨時 加班 證明 照實 討厭 |
| 48 | 7 → 13 | 冤仇 疼惜 溶 提早 |
| 49 | 5 → 9 | — |
Other changes made on the way: lesson 37 line 12 reading 布袋戲 pòo-tē-hì; lesson 43 同事 kept as tông-sū (the
lesson's own reading); about 60 entries added to `course/glosses_en.tsv` so that `app/dist/english-auto.txt` is
empty again (it had 35 single-character fallbacks from other work).

## Consequences for future lessons (read this before writing 進修 lessons)
- **The 122 words above are now taught early.** Never declare them again in 進修 `new_words`; in notes, refer to
  them as "(lesson N)" with the lesson in the table. `tools/xrefs.py` catches duplicate Hàn-jī and wrong references.
- **The pool of never-taught frequent words is smaller.** Get it fresh each time with `python3 -I tools/untaught.py`
  (never from an older list): it reads every lesson, theme and exercise.

## How it was done (tools now in the repo)
- `tools/untaught.py [TOP]`: frequent core words never used or declared anywhere (default top 3000).
- `tools/wordcheck.py 觀音=Kuan-im …`: where a word is first used and first declared.
- `tools/taught_later.py A B`: words in lessons A..B used before the lesson that declares them (進修 N = 100 + N).
  Homophones give false hits (kah 甲/佮, khì 去/氣, numbers); a few old hits remain in the original lines
  (曝 used in 36 and 45 but declared in 進修 11; 挽 in 40 / 進修 10; 大人 in 37 / lesson 75).
- `tools/extend_lessons.py ADDITIONS.yaml`: appends lines, notes, `new_words` and exercise items to base lessons,
  keeping each file's YAML style (22–28 are block style, 29+ flow style).
- Checks run per batch: `lint.py` (0 errors), `make test`, `qc_readings.py`, `qc_glosses.py` (read by eye),
  `xrefs.py`, `taught_later.py`, `build_app.py` with an empty `english-auto.txt`, `smoke.py` on the batch.

## Things that went wrong and were caught
- Words I thought were early were declared late: 阿姊 (72), 歡喜 (63), 知影 (57), 一定 (52), 身體 (50), 笑 (50),
  毋管 (52), 明年 (99), 順紲 (66), 外口 (34), 司機 (進修 8). Always run `taught_later.py`, don't trust intuition.
- Words not in the MOE dictionary can't go in `new_words` (lint error or warning): 相報, 好料, 為著, 迷路, 母仔囝
  (MOE: 母仔囝 bú-á-kiánn), 挾 (MOE writes 夾 ngeh).
- One Hàn-jī = one declaration whatever the reading (`xrefs.py` keys on Hàn-jī).

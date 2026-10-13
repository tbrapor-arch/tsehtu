# Data sources and attribution

None of these datasets are stored in this repository. `make data` downloads them at pinned commits into
`data/raw/` (git-ignored), and `make db` builds `data/build/taigi.db` locally.

| Dataset | Rights holder / maintainer | Licence | How it is used |
|---|---|---|---|
| 教育部臺灣台語常用詞辭典 — *Dictionary of Frequently-Used Taiwanese Taigi* | Ministry of Education, Taiwan (中華民國教育部). Data via [g0v/moedict-data-twblg](https://github.com/g0v/moedict-data-twblg) and [ChhoeTaigi](https://github.com/ChhoeTaigi/ChhoeTaigiDatabase) | [CC BY-ND 3.0 TW](https://creativecommons.org/licenses/by-nd/3.0/tw/) | Reference for Hàn-jī, Tâi-lô readings, definitions and example sentences. Entries and sentences are reproduced unaltered; lessons are written independently. |
| 教育部臺灣台語常用詞辭典 — headword recordings (`sutiau-mp3.zip`) | Ministry of Education, Taiwan, [download page](https://sutian.moe.edu.tw/zh-hant/siongkuantsuguan/) | [CC BY-ND 3.0 TW](https://creativecommons.org/licenses/by-nd/3.0/tw/) (as stated for the dictionary; the download page gives no separate licence for the audio) | Fetched at build time by the GitHub workflow; only the recordings of words used in the app are published with the site, copied unaltered. Not stored in this repo. |
| iTaigi 華台對照典 | iTaigi contributors, via ChhoeTaigi | [CC0](https://creativecommons.org/publicdomain/zero/1.0/) | Mandarin → Taigi equivalents |
| 台華線頂對照典 | Iûⁿ Ún-giân (楊允言), via ChhoeTaigi | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | Mandarin equivalents |
| 台灣白話基礎語句 (1956) | via ChhoeTaigi | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | Basic sentences, Mandarin/English glosses |
| Maryknoll 台英辭典 (1976), Embree 台英辭典 (1973) | Maryknoll Language Service Center; Bernard L. M. Embree; via ChhoeTaigi | [CC BY-NC-SA 3.0 TW](https://creativecommons.org/licenses/by-nc-sa/3.0/tw/) | **Off by default.** English glosses only with `make db-nc`, for non-commercial builds. Not used in `course/`. |
| 教育部臺灣閩南語字詞頻調查工作 (2009) | Iûⁿ Ún-giân et al., via [Taiwanese-Corpus](https://github.com/Taiwanese-Corpus/Ungian_2009_KIPsupin) | none stated | Read at build time to count word frequencies. No text is stored or redistributed. |
| CC-CEDICT, via [cedict-json](https://www.npmjs.com/package/cedict-json) | MDBG and CC-CEDICT contributors | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | Pinyin and English for the Mandarin equivalents in the app's word cards |
| Plangothic (遍黑體), via [@free-fonts/plangothic](https://www.npmjs.com/package/@free-fonts/plangothic) | Plangothic Project | [SIL OFL 1.1](https://openfontlicense.org) | Glyphs for rare Taigi characters, subset and embedded in the app |
| complete-hsk-vocabulary | Yanis Zafirópulos ([drkameleon](https://github.com/drkameleon/complete-hsk-vocabulary)) | MIT | HSK levels of Mandarin equivalents |

Romanisation throughout is the Ministry of Education's 臺灣台語羅馬字拼音方案 (Tâi-lô).

## Podcast tab
《隔壁 ê 戇人》 (Keh-piah ê gōng-lâng), a Taigi podcast by 欸緒利, 阿尹 and 阿莉莎, hosted by SoundOn. The app shows the
episode notes from the show's public RSS feed (titles, chapters, the hosts' 臺語補給站 word lists) and plays the
audio from SoundOn's own URLs. No audio is copied or re-hosted; all rights stay with the hosts.

## Font for Tâi-lô
Noto Sans (Google, SIL Open Font License 1.1), subset to Latin and the combining marks, embedded in the app so that tone marks such as m̄, a̍ and o͘ sit on their letter: `app/fonts/tailo-noto-sans.woff2`.

# Lessons › 台語字 (Taigi-only characters), 17 Nov 2026

The page `#jitai` (switch "Lessons | 台語字" at the top of the Lessons tab) and Practice › Characters show **one list**:
`DATA.chars`, built by `tools/taigi_chars.py`, same order, same groups of 25. Practice is for flashcards; 台語字 is for
reading, with examples. Each links to the other (group by group).

## The list
- Selection: `taigi_chars.select()` (MOE headword characters in no HSK word, absent or nearly absent from CC-CEDICT
  words, outside Big5 level 1, or MOE-created; with a ranked word; not a name only). The private repo imports the same
  function (`tools/taigi_only.py`, `tools/chars_queue.py`): never copy it.
- HSK-variant fix (17 Nov 2026): a HSK row marked "variant of" no longer counts when a standard sibling row exists
  (挵 for 弄, 摃 for 扛, 桮 for 杯…). It freed 摃 挵 嬭 舖 桮 蹔 闇 鍼 噁 裌, appended as #626–635.
- **Order pinned** in `course/chars_order.txt` (owner's rule): the build stops if a pinned character drops out, and
  appends any new one after the last (with a message). Never reorder or delete a line; append new characters only.
- After the list, `extra:` in `course/chars_examples.yaml`: characters Mandarin also writes but Taigi uses its own way
  (啥 箍 夯 啉 攢…, `DATA.charsx`), never numbered with the list. Chosen from the characters of the owner's books
  (register) that the selection rejects and whose MOE entry says the Taigi use differs from Mandarin (`cognate`
  different / same characters, different use), plus 啥.

## A row
Character (tap: its card) and readings; English meaning; "Mandarin" + the card's Mandarin equivalent (tappable, pinyin
from the shared table); the most common word and up to two more (word cards); [private module: "In your books"];
the public example; "Also in Lesson N" when a long lesson line gave way; a folded "Dictionary example".

## The example (`course/chars_examples.yaml`, one entry per character)
- `lesson: [id, n]`: a course line reading the character as listed (lessons 1–100 first, then 進修, then 文學).
  A line over 24 syllables gives way to the MOE sentence (`also:` keeps the link). `moe2:` = an MOE sentence shown
  folded under it.
- `moe: {word, hanji}` + `en:`: an MOE example of a headword reading the character as listed (sentences before
  phrases; proverbs keep an explanation in the English). Hàn-jī/Tâi-lô/Mandarin come from the database unaltered
  (CC BY-ND); the English is ours, labelled "English: Tsheh-tû".
- `created: {hanji, tailo, en}` + `conf:`: written for the list where nothing else exists; every word an MOE word
  with that reading; labelled "written for this list · not checked by a native speaker".
- `reading_only: true`: the MOE gives only the reading (no definition, no word that has one).
- `also_read: {r, word}`: a reading added to the listed ones when an MOE word attests it (嘓 kho̍k in 嘓魚).
Vulgar characters are shown like the others (owner).

## English meaning
Chain: the 文學 lesson's `chars:` English → `course/glosses_en.tsv` (character + listed reading; the section
"Lessons › 台語字 character meanings": short glosses translated from the MOE definition of the character or of its
main word, column 4 `moe-sense`, `moe-sense?` when unsure) → the character's card English when written for Taigi.
The TSV line also gives the character's own word card its English.

## Checks
`python3 -I tools/lint.py course/chars_examples.yaml` (also in the full lint): every listed character has an entry
and exactly one public example kind; lesson lines exist and read it as listed; MOE examples are the database's text
and their headword reads it as listed; written sentences line up and use MOE words only; `en` present; the pin.
`tools/smoke.py` has a pass over every group of the page.

## Adding characters (from the owner's books)
Private repo: `tools/chars_queue.py` (end of `build_exam.py`) lists book characters the selection accepts but the list
lacks; `--scaffold` appends them to `chars_order.txt` and writes stubs here. Fill `en:` / `created:` and the meaning in
`glosses_en.tsv`, then `make lint && make app`. Only the character, its reading and dictionary data come from that
side: never a book sentence.

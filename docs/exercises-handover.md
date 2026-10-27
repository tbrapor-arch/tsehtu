# Exercises: added sentences — handover (27 Oct 2026)

## What was done
Every lesson (1–100 and 進修 P1–P21, 121 in all) got **2 new "What does it mean?" sentences** (`exercises.translate`)
and **1 new "Fill the gap"** (`exercises.fill`), appended after the existing ones. The owner asked for sentences
**not taken from the lesson**: the older exercises often copied dialogue lines. Dialogues, notes and word lists were
not touched (the owner has read lessons 1–21 and likes them as they are).

Commits: `5bbd64a` (lessons 1–100) and the next one (進修 P1–P21, tool, this file). Not checked by a native speaker.

## Owner's rule for the next batches: sentences as long as the lesson's own
New sentences must **read like the lesson's sentences, including their length**: aim at the median length of the
lesson's dialogue lines, and never below 80 % of it. The batches of 27 Oct are too short from lesson 22 on:

| lessons | dialogue lines (median, syllables) | older exercises | sentences added 27 Oct |
|---|---|---|---|
| 1–21 | 7.9 | 5.8 | 8.3 |
| 22–49 | 12.7 | 6.9 | 8.5 |
| 50–100 | 15.7 | 9.1 | 9.0 |
| P1–P21 | 21.5 | 10.6 | 10.3 |

So from lesson 22 on: two clauses joined (…，毋過… / 因為…，所以… / 若…，就… / …了後，…), a time or place phrase,
a reason or a consequence, the way the dialogue lines are built. `tools/exercises.py check` now refuses a sentence
shorter than 80 % of the median ("TOO SHORT"). The 27 Oct sentences of lessons 22+ were not lengthened yet: ask the
owner before replacing them.

## Tool: `tools/exercises.py`
```
python3 tools/exercises.py brief 22 30      # new words, dialogue (Hàn-jī), existing exercises; P1 = 101
python3 tools/exercises.py check b.txt      # checks only
python3 tools/exercises.py apply b.txt      # checks, then appends to the lesson files
python3 -I tools/lint.py                    # 0 errors expected (I/W "treated as a name", "not a dictionary word
                                            #   (each syllable is)" for numbers and reduplications are normal)
```
Batch file, one sentence per line, ` | ` between fields:
```
30 | T | Guá beh khì gîn-hâng niá-tsînn. | 我欲去銀行領錢。 | I'm going to the bank to withdraw money.
30 | F | Í-āu guá ē ___ tsú-tsia̍h. | 以後我會___煮食。 | ka-kī | 家己 | From now on I'll cook for myself.
P5 | T | …                                     (P5 = 進修 5)
```
Checks: not a dialogue line nor an existing exercise; every word already met by that lesson (in the dialogues, new
words or exercises of that lesson and earlier ones: rewrite with known words when it says "words not met"); a gap in
both lines; the length rule above. The tool writes items in each file's own YAML style (block, or flow `- {…}`
indented 4: lessons 29–39 and others) and checks the file still parses.

## Conventions met while writing (follow the lessons, not memory)
- 阮 is **guán** in this course (not gún); 向 in 向西爿 is **ǹg**; 毋捌 **m̄ bat**, 毋知 **m̄ tsai**, 毋肯 **m̄ khíng**
  (two words); 會記得 is not in the early lessons, use 毋通袂記得 **m̄-thang bē-kì-tit**.
- Final particles and neutral tone as in the dialogues: **--ah** (矣), **--bô** (無 at the end of a question),
  **--leh** (咧), **pháinn--khì--ah**, **sit--tiāu**, **khioh--tio̍h**, **tńg--lâi**.
- Lines are cut by their Tâi-lô words, so hyphenation decides the word cards: copy the hyphenation the lesson uses
  (tsia̍t-ūn-tsām, tsia̍h-pn̄g, tshài-thâu-thng, ta̍k-kang).
- Before checking, grep the lesson for a phrase's spelling: `grep -h -A1 "hanji: …" course/lessons/0NN.yaml`.

## Ideas left
- Lengthen the 27 Oct sentences of lessons 22–100 and P1–P21 to the dialogue length (owner to confirm).
- A native speaker's pass over all exercises, old and new.

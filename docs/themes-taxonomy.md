# Themes (Practice tab): thematic vocabulary dictionary (design, not yet implemented)

Goal: every word of the vocabulary database can be found by subject in Themes (Practice tab). This is separate from the
course progression (which situations the lessons cover).

## Current state
- The database has no subject field: `entry` has `kind`, `cognate`, `core`, ranks; `sense.pos` is the part of speech.
  The source CSVs only carry a part-of-speech column.
- One domain is done, as a pilot: `course/themes/02-health.yaml` (id `health`) is now "Body and health" (10 sections, 212 words, 195 of them
  core words). Sections 1–4 are the original theme with their texts, extended; sections 5–10 (head and face, body and limbs,
  inside the body, the body's needs, build and impairments, birth and death) are word lists without a text yet. The theme id
  stays `health`, so review progress on sections 1–4 is kept. Themes shows one card per theme file, so one file per domain
  works without changing the app.
- Three more domains, word lists without texts yet: `03-food.yaml` (03 Food and drink, 8 sections, 128 words),
  `04-home.yaml` (04 Home and everyday objects, 7 sections, 160 words), `05-clothing.yaml` (05 Clothing and looks,
  4 sections, 49 words). Files are named `NN-id.yaml` by domain number so the cards follow the domain order;
  the id inside the file is what the app and review progress use.
- Three more (27 Oct 2026): `01-people.yaml` (01 People and family, 9 sections, 242 words, with a family-names
  section that also takes in the surnames Haiku left as `?`), `06-nature.yaml` (06 Nature, weather, animals and plants,
  10 sections, 281 words), `07-places.yaml` (07 Places, transport and directions, 8 sections, 233 words). Moved out:
  本 to 08, 和尚 to 12, 礪 to 14c; 草地 (countryside) from 06 to 07. Left as `?`: the readings 馬 ma, 貓 bâ, 種 tsiòng. Colours (色, 青) went to 15 with the other colours; farm tools, weapons, 筆, 宮 and 菜店 left 04/03.
- `docs/themes-classification-draft.tsv`: a first domain (01–16) for every core word, from a Haiku pass in 16 batches
  (Oct 2026), then a second pass splitting domain 14 into 14a–14h. Columns: domain, sub, confidence H/M/L, note,
  reviewed. Measured on the pilot: about 94% of the words Haiku put in 02 belong there, and about 97% of the domain's
  words were found. 124 words are `?`, mostly words with no MOE definition. Rows with `reviewed=yes` were checked by hand.
  For a finished domain, its theme file wins over this draft.

## Scope
1. Core words (4,265): complete, each in exactly one category.
2. Other MOE words (about 18,000), later. Proverbs (4,750, `kind = proverb`) form their own category.
3. The other sources (iTaigi, 台華線頂, 1956 sentences) are out of scope.

## Categories (two levels: 16 domains, then 100–120 subcategories of about 40 words)
1 People and family · 2 Body and health · 3 Food and drink · 4 Home and everyday objects · 5 Clothing and appearance ·
6 Nature, weather, animals, plants · 7 Places, transport, directions · 8 Time, numbers, measures · 9 Work, money, business ·
10 Education, language, media · 11 Society, law, politics · 12 Festivals, religion, customs · 13 Feelings, character, mind ·
14 Actions and events · 15 Qualities and states · 16 Function words (pronouns, particles, negation, questions).

## Rules
- One primary category per word; optional `see_also`. A polysemous word follows its main sense; exceptions are noted.
- Storage in content files, not in the database (which is rebuilt from pinned sources): `course/themes/taxonomy.yaml`
  (categories) and one assignment file per domain. `health.yaml` becomes the subcategories of "Body and health", keeping its texts.
- A lint check: every core word has exactly one category, no unknown ids, and the unclassified list is printed.

## Method
Pre-classify by rules (MOE definition, Mandarin equivalent, part of speech), then review in batches of about 270 words per
domain (about 16 batches for the core). Start with one pilot domain (Body and health) to test the taxonomy before the rest.

## Interface
Domain grid → subcategory → word list, with filters (core / all, taught in a lesson ✓, frequency, word type), search, add to review.

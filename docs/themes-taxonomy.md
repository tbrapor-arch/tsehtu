# Themes tab: thematic vocabulary dictionary (design, not yet implemented)

Goal: every word of the vocabulary database can be found by subject in the Themes tab. This is separate from the
course progression (which situations the lessons cover).

## Current state
- The database has no subject field: `entry` has `kind`, `cognate`, `core`, ranks; `sense.pos` is the part of speech.
  The source CSVs only carry a part-of-speech column.
- One theme exists, `course/themes/health.yaml` (4 numbered sections, 42 words, a short text per section). The tab shows a
  grid of themes, then a page per theme with "add to review"; Review can be filtered by theme section.

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

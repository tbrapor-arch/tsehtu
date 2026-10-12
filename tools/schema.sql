CREATE TABLE source(id TEXT PRIMARY KEY, name TEXT, year TEXT, license TEXT, commercial_ok INT, note TEXT);

-- One row per headword per source. Romanisation is always Tâi-lô (MOE system).
CREATE TABLE entry(
  id INTEGER PRIMARY KEY,
  source TEXT REFERENCES source(id),
  src_id TEXT,
  hanji TEXT,             -- Hàn-jī as written by the source (MOE recommended characters for source='moe')
  tailo TEXT,             -- Tâi-lô with tone diacritics
  tailo_alt TEXT,         -- full alternative readings string if the source gave several
  tkey TEXT,              -- normalised numeric key, tones 1/4 unmarked: 'tsit8-e5'
  toneless TEXT,
  kind TEXT,              -- word | proverb | other
  wenbai TEXT,            -- MOE single-character reading layer: literary | colloquial | vulgar/common | substitute-char
  moe_type INT,
  english TEXT,
  -- learner layers (filled by enrich.py)
  freq INT,               -- token count in 2009 MOE written corpus (by tkey)
  freq_rank INT,
  mandarin_best TEXT,     -- most HSK-relevant Mandarin equivalent
  hsk_old INT, hsk_new INT,
  cognate TEXT,           -- same | partial | different | n/a (Hàn-jī vs Mandarin equivalent)
  core INT                -- 1 if in core learner list
);
CREATE INDEX entry_tkey ON entry(tkey);
CREATE INDEX entry_hanji ON entry(hanji);
CREATE INDEX entry_toneless ON entry(toneless);

CREATE TABLE sense(id INTEGER PRIMARY KEY, entry_id INT, ord INT, pos TEXT, definition_zh TEXT);
CREATE INDEX sense_entry ON sense(entry_id);

CREATE TABLE example(id INTEGER PRIMARY KEY, entry_id INT, sense_id INT, source TEXT,
  hanji TEXT, tailo TEXT, poj TEXT, mandarin TEXT, english TEXT);
CREATE INDEX example_entry ON example(entry_id);

CREATE TABLE mandarin(entry_id INT, word TEXT, source TEXT);
CREATE INDEX mandarin_word ON mandarin(word);
CREATE INDEX mandarin_entry ON mandarin(entry_id);

CREATE TABLE variant(entry_id INT, tailo TEXT, tkey TEXT, kind TEXT);
CREATE TABLE relation(entry_id INT, other_id INT, rel TEXT);
CREATE TABLE dialect(hanji TEXT, place TEXT, tailo TEXT, kind TEXT);

CREATE TABLE corpus_freq(tkey TEXT PRIMARY KEY, count INT, docs INT);
CREATE TABLE syllable_freq(syllable TEXT PRIMARY KEY, count INT);

CREATE TABLE hsk(trad TEXT, simp TEXT, pinyin TEXT, old_level INT, new_level INT, english TEXT,
  PRIMARY KEY(trad, pinyin));
CREATE INDEX hsk_trad ON hsk(trad);

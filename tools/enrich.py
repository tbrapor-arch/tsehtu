"""Add learner layers to taigi.db: frequency, Mandarin best equivalent, HSK level, cognate class, English gloss."""
import sqlite3
import sys

con = sqlite3.connect(sys.argv[1])
cur = con.cursor()

# 1. corpus frequency
# MOE words get homophone-split counts from freq_align.py; other sources get the raw count of their reading
cur.execute("UPDATE entry SET freq = (SELECT count FROM corpus_freq c WHERE c.tkey = entry.tkey) "
            "WHERE source != 'moe' OR freq IS NULL")
cur.execute('UPDATE entry SET freq = 0 WHERE freq IS NULL')

# 2. HSK lookup
hsk = {}
for trad, old, new in cur.execute('SELECT trad, old_level, new_level FROM hsk'):
    o, n = hsk.get(trad, (None, None))
    o = min([x for x in (o, old) if x is not None], default=None)
    n = min([x for x in (n, new) if x is not None], default=None)
    hsk[trad] = (o, n)

mand = {}
for eid, w in cur.execute('SELECT entry_id, word FROM mandarin'):
    mand.setdefault(eid, []).append(w)

updates = []
for eid, hanji in cur.execute('SELECT id, hanji FROM entry').fetchall():
    words = mand.get(eid, [])
    best, bo, bn = None, None, None
    for w in words:
        o, n = hsk.get(w, (None, None))
        score = (o or n or 99)
        if best is None or score < (bo or bn or 99):
            best, bo, bn = w, o, n
    if best is None and words:
        best = words[0]
    # cognate class: does the Taigi Hàn-jī spelling already exist as Mandarin?
    if not hanji:
        cog = 'n/a'
    elif hanji in words or (hanji in hsk and (not words or hanji == best)):
        cog = 'same'
    elif hanji in hsk:
        cog = 'same-chars-diff-use'   # characters form a Mandarin word, but the gloss differs: possible false friend
    elif best and set(hanji) & set(best):
        cog = 'partial'
    elif best:
        cog = 'different'
    else:
        cog = 'n/a'
    if not words and hanji in hsk:
        bo, bn = hsk[hanji]
    updates.append((best, bo, bn, cog, eid))
cur.executemany('UPDATE entry SET mandarin_best=?, hsk_old=?, hsk_new=?, cognate=? WHERE id=?', updates)

# 3. English gloss for MOE entries borrowed from Maryknoll/Embree (same tkey; prefer same Hàn-jī)
eng = {}
for src in ('embree', 'maryknoll'):  # maryknoll last = preferred
    for tk, h, en in cur.execute('SELECT tkey, hanji, english FROM entry WHERE source=? AND english IS NOT NULL', (src,)):
        eng[(tk, h)] = en
        eng.setdefault((tk, None), en)
upd = []
moe_tk = {}
for (tk,) in cur.execute("SELECT tkey FROM entry WHERE source='moe'"):
    moe_tk[tk] = moe_tk.get(tk, 0) + 1
for eid, tk, h in cur.execute("SELECT id, tkey, hanji FROM entry WHERE source='moe'").fetchall():
    # exact Hàn-jī match, or romanisation-only match when the reading is unambiguous in MOE
    en = eng.get((tk, h)) or (eng.get((tk, None)) if moe_tk[tk] == 1 else None)
    if en:
        upd.append((en[:400], eid))
cur.executemany('UPDATE entry SET english=? WHERE id=?', upd)
print('MOE entries with English gloss:', len(upd))

# 4. core list: top 4000 MOE words by frequency + MOE words whose Mandarin equivalent is HSK<=3
#    (needs freq_align.py to have run first)
cur.execute('UPDATE entry SET core=NULL')
cur.execute("""UPDATE entry SET core=1 WHERE source='moe' AND kind='word'
               AND (freq_rank <= 4000 OR (hsk_old <= 3 AND freq >= 5))""")

# 5. views
cur.executescript("""
DROP VIEW IF EXISTS v_mandarin_to_taigi;
CREATE VIEW v_mandarin_to_taigi AS
  SELECT m.word AS mandarin, h.old_level AS hsk_old, h.new_level AS hsk_new,
         e.hanji, e.tailo, e.source, e.freq, e.cognate, e.id AS entry_id
  FROM mandarin m JOIN entry e ON e.id = m.entry_id
  LEFT JOIN (SELECT trad, min(old_level) old_level, min(new_level) new_level FROM hsk GROUP BY trad) h ON h.trad = m.word;
DROP VIEW IF EXISTS v_core;
CREATE VIEW v_core AS
  SELECT freq_rank, hanji, tailo, wenbai, mandarin_best, hsk_old, hsk_new, cognate, english, freq,
         (SELECT group_concat(pos || '：' || definition_zh, ' | ') FROM sense s WHERE s.entry_id = e.id) AS definition_zh,
         id AS entry_id
  FROM entry e WHERE core = 1
    AND id = (SELECT min(id) FROM entry d WHERE d.source='moe' AND d.core=1 AND d.hanji=e.hanji AND d.tkey=e.tkey)
  ORDER BY freq_rank;
""")
con.commit()
for row in cur.execute("SELECT cognate, count(*) FROM entry WHERE core=1 GROUP BY 1"):
    print(row)
print('core', cur.execute('SELECT count(*) FROM entry WHERE core=1').fetchone())

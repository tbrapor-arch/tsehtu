"""Disambiguate corpus frequency between homophones.

Aligns Hàn-jī/Han-lo text with its romanisation (1 CJK char or 1 roman syllable = 1 syllable)
in two places: the 2009 MOE corpus (Han-lo + full POJ pairs) and MOE dictionary example sentences.
Counts (hanji_word, tkey) pairs, then splits each tkey's corpus count across homophone entries.
"""
import glob
import json
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tailo import key  # noqa: E402

ROOT, DB = sys.argv[1], sys.argv[2]
CJK = r'[㐀-鿿\U00020000-\U0003ffff豈-﫿]'
UNIT_RE = re.compile(CJK + r"|[A-Za-zÀ-ɏ̀-ͯḀ-ỿⁿ]+[0-9]?")
pair = Counter()


def units(text):
    # roman syllables separated by '-' count individually
    return UNIT_RE.findall(text.replace('-', ' '))


def align(hanlo, roman, poj):
    words = [w for w in re.split(r'\s+', roman) if key(w, poj=poj)]
    keys = [key(w, poj=poj) for w in words]
    nsyl = sum(len(k.split('-')) for k in keys)
    u = units(hanlo)
    if len(u) != nsyl:
        return 0
    i = 0
    for k in keys:
        n = len(k.split('-'))
        seg = u[i:i + n]
        i += n
        if all(re.match(CJK, x) for x in seg):
            pair[(''.join(seg), k)] += 1
    return 1


ok = tot = 0
for f in glob.glob(os.path.join(ROOT, 'Ungian_2009_KIPsupin/JSON格式資料/**/*.json'), recursive=True):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    for art in d.get('資料', []):
        for p in art.get('段', []):
            if len(p) < 2:
                continue
            # align sentence by sentence when sentence counts agree, else whole paragraph
            hs = re.split(r'(?<=[。！？!?])', p[0])
            rs = re.split(r'(?<=[.!?])\s', p[1])
            if len(hs) == len(rs):
                for h, r in zip(hs, rs):
                    tot += 1
                    ok += align(h, r, True)
            else:
                tot += 1
                ok += align(p[0], p[1], True)
print('corpus segments aligned', ok, '/', tot)

con = sqlite3.connect(DB)
ok = tot = 0
for h, t in con.execute("SELECT hanji, tailo FROM example WHERE source='moe'"):
    tot += 1
    ok += align(h, t, False)
print('MOE examples aligned', ok, '/', tot)

con.execute('DROP TABLE IF EXISTS pair_freq')
con.execute('CREATE TABLE pair_freq(hanji TEXT, tkey TEXT, count INT, PRIMARY KEY(hanji,tkey))')
con.executemany('INSERT INTO pair_freq VALUES (?,?,?)', [(h, k, c) for (h, k), c in pair.items()])

# split tkey frequency across MOE homophones
groups = defaultdict(list)
for eid, h, k in con.execute("SELECT id, hanji, tkey FROM entry WHERE source='moe' AND kind='word'"):
    groups[k].append((eid, h))
corpus = dict(con.execute('SELECT tkey, count FROM corpus_freq'))
upd = []
for k, ents in groups.items():
    total = corpus.get(k, 0)
    w = [pair.get((h, k), 0) for _, h in ents]
    s = sum(w)
    for (eid, h), wi in zip(ents, w):
        if len(ents) == 1:
            share = 1.0
        elif s == 0:
            share = 1.0 / len(ents) * 0.5   # unknown: penalise, can't tell which homophone
        else:
            share = (wi + 0.1) / (s + 0.1 * len(ents))
        upd.append((int(round(total * share)), wi, eid))
con.execute('ALTER TABLE entry ADD COLUMN pair_count INT') if 'pair_count' not in \
    [r[1] for r in con.execute('PRAGMA table_info(entry)')] else None
con.executemany('UPDATE entry SET freq=?, pair_count=? WHERE id=?', upd)
ids = [r[0] for r in con.execute("SELECT id FROM entry WHERE source='moe' AND kind='word' "
                                  "ORDER BY freq DESC, pair_count DESC, length(tkey)")]
con.execute("UPDATE entry SET freq_rank=NULL")
con.executemany('UPDATE entry SET freq_rank=? WHERE id=?', [(i + 1, e) for i, e in enumerate(ids)])
con.commit()

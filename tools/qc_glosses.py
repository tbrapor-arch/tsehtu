"""List new_words whose English gloss shares no word with the MOE/HSK English, with the MOE Mandarin
definition beside it, for a quick human check of meanings. Usage: python3 -I tools/qc_glosses.py FILE.yaml ..."""
import sys, re, glob, sqlite3
import os; HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import yaml
from tailo import key
c = sqlite3.connect(os.path.join(os.path.dirname(HERE), 'data/build/taigi.db'))
STOP = set('a an the of to in on be is it one s or and for with someone something sth sb up out off'.split())
def toks(s): return {w for w in re.findall(r'[a-z]+', (s or '').lower()) if w not in STOP and len(w) > 2}
n = shown = 0
for f in sys.argv[1:]:
    d = yaml.safe_load(open(f)); lid = ('P' if 'perf' in f else '') + str(d['id'])
    for w in d.get('new_words') or []:
        n += 1
        r = c.execute("select id, english, mandarin_best from entry where source='moe' and hanji=? and tkey=?", (w['hanji'], key(w['tailo']))).fetchone()
        if not r: continue
        eid, eng, mb = r
        hsk = c.execute("select english from hsk where trad=?", (mb or '',)).fetchone()
        ref = (eng or '') + ' ' + (hsk[0] if hsk else '')
        if toks(w['en']) & toks(ref): continue
        dz = ' / '.join(x for x, in c.execute("select definition_zh from sense where entry_id=? order by ord limit 2", (eid,)))
        shown += 1
        print(f"{lid} {w['hanji']} [{w['en']}] ≈{mb or ''} :: {dz[:70]}")
print('checked', n, 'shown', shown, file=sys.stderr)

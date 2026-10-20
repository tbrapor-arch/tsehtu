"""Flag character/syllable pairs in lessons that no MOE entry or example attests (TONE: right syllable,
wrong tone; READ: reading unknown for that character). Usage: python3 -I tools/qc_readings.py FILE.yaml ..."""
import sys, re, glob, sqlite3, collections
import os; HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import yaml
from tailo import key
from lint import words, units, CJK
con = sqlite3.connect(os.path.join(os.path.dirname(HERE), 'data/build/taigi.db'))
rd = collections.defaultdict(set)      # char -> syllable keys (with tone)
def add(h, t):
    k = key(t)
    if not k: return
    syl = [s for s in re.split(r'[- ]+', k) if s]
    u = [c for c in h if re.match(CJK, c)]
    if len(u) == len(syl):
        for c, s in zip(u, syl): rd[c].add(s)
for h, t in con.execute("SELECT hanji, tailo FROM entry WHERE source='moe' AND hanji!=''"): add(h, t)
for h, t in con.execute("SELECT hanji, tailo FROM example WHERE source='moe'"):
    hh = ''.join(c for c in h if re.match(CJK, c)); tt = [k for _, k, _, _ in words(t) if k]
    add(hh, '-'.join(tt))
try:
    for h, t in con.execute("SELECT hanji, tailo FROM variant"): add(h, t)
except Exception: pass
strip = lambda s: re.sub(r'\d', '', s)
out = collections.Counter(); where = collections.defaultdict(list)
files = sys.argv[1:]
for f in files:
    d = yaml.safe_load(open(f))
    lid = ('P' if 'perf' in f else '') + str(d['id'])
    items = [(l.get('hanji',''), l.get('tailo','')) for l in d.get('dialogue') or []]
    items += [(w['hanji'], w['tailo']) for w in d.get('new_words') or []]
    for kind, its in (d.get('exercises') or {}).items():
        for it in its or []:
            h, t = it.get('hanji',''), it.get('tailo','')
            if '___' in t: t = t.replace('___', it.get('answer','')); h = h.replace('___', it.get('answer_hanji',''))
            items.append((h, t))
    for h, t in items:
        ws = [k for _, k, _, _ in words(t) if k]
        syl = [s for k in ws for s in k.split('-')]
        u = units(h)
        if len(u) != len(syl): continue
        for c, s in zip(u, syl):
            if not re.match(CJK, c) or c not in rd: continue
            if s in rd[c]: continue
            kind = 'TONE' if strip(s) in {strip(x) for x in rd[c]} else 'READ'
            out[(kind, c, s)] += 1; where[(kind, c, s)].append(lid)
for (kind, c, s), n in sorted(out.items(), key=lambda x: (x[0][0], x[0][1])):
    print(kind, c, s, 'MOE:', '/'.join(sorted(rd[c]))[:60], 'in', ','.join(sorted(set(where[(kind,c,s)])))[:50])

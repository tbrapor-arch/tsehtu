"""Check candidate words for a new lesson in one pass: MOE readings, definitions, an example, and whether a
lesson already declares the word in new_words.

  python3 -I tools/candidates.py 參詳 好額人 金金看 ex=1
"""
import sys, glob, sqlite3, yaml
import os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
con = sqlite3.connect(root + '/data/build/taigi.db')
decl = {}
for f in sorted(glob.glob(root + '/course/lessons/[0-9]*.yaml')) + sorted(glob.glob(root + '/course/perfectionnement/[0-9]*.yaml')):
    d = yaml.safe_load(open(f, encoding='utf-8'))
    lab = ('P' if 'perf' in f else '') + str(d['id'])
    for w in d.get('new_words') or []:
        decl.setdefault(w['hanji'], lab)
ex_n = int(dict(a.split('=') for a in sys.argv[1:] if '=' in a).get('ex', '1'))
for h in [a for a in sys.argv[1:] if '=' not in a]:
    rows = con.execute("SELECT id, tailo, freq_rank, tailo_alt FROM entry WHERE source='moe' AND hanji=?", (h,)).fetchall()
    tag = f'  [DECLARED {decl[h]}]' if h in decl else ''
    if not rows:
        print(f'!! {h}: not in MOE{tag}')
        continue
    for eid, t, rk, alt in rows:
        defs = ' | '.join(d[:60] for (d,) in con.execute('SELECT definition_zh FROM sense WHERE entry_id=? ORDER BY ord', (eid,)))
        print(f'{h} {t} #{rk}{tag}  {defs[:200]}')
        for eh, et in con.execute("SELECT hanji, tailo FROM example WHERE entry_id=? AND source='moe' LIMIT ?", (eid, ex_n)):
            print(f'     ex: {eh} / {et}')

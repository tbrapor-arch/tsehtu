"""How much of the core vocabulary the written lessons already cover.

  python3 tools/coverage.py            # summary + the most frequent core words not yet taught
"""
import glob
import os
import sqlite3
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lint import words  # noqa: E402

ROOT = os.path.dirname(HERE)
con = sqlite3.connect(os.path.join(ROOT, 'data/build/taigi.db'))

seen = set()
files = (sorted(glob.glob(os.path.join(ROOT, 'course/lessons/[0-9]*.yaml'))) + sorted(glob.glob(os.path.join(ROOT, 'course/perfectionnement/[0-9]*.yaml')))) + \
    sorted(glob.glob(os.path.join(ROOT, 'course/themes/*.yaml')))
for f in files:
    d = yaml.safe_load(open(f, encoding='utf-8'))
    lines = [l['tailo'] for l in d.get('dialogue', [])]
    for sec in d.get('sections', []):
        lines += [w['tailo'] for w in sec['words']] + [t['tailo'] for t in sec.get('text', [])]
    for t in lines:
        for _, k, _, _ in words(t):
            seen.add(k)
            seen.update(k.split('-'))

core = con.execute("SELECT v.freq_rank, v.hanji, v.tailo, e.tkey, v.mandarin_best, v.cognate "
                   "FROM v_core v JOIN entry e ON e.id = v.entry_id ORDER BY v.freq_rank").fetchall()
for top in (100, 300, 1000):
    part = [r for r in core if r[0] <= top]
    got = sum(1 for r in part if r[3] in seen)
    print(f'top {top:>4} core words: {got}/{len(part)} covered ({100 * got // max(1, len(part))}%)')
print('\nMost frequent core words not yet in any lesson or theme (Taigi-only and false friends first):')
missing = [r for r in core if r[3] not in seen and r[0] <= int(sys.argv[1] if len(sys.argv) > 1 else 400)]
missing.sort(key=lambda r: (r[5] not in ('different', 'same-chars-diff-use'), r[0]))
for r in missing[:40]:
    print(f'  #{r[0]:<4} {r[1]} {r[2]}  ({r[4] or "?"}, {r[5]})')

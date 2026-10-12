"""Look up a word in taigi.db by Hàn-jī, Mandarin, Tâi-lô (diacritics or numeric) or English.

  python3 lookup.py taigi.db 喜歡        # Mandarin or Taigi Hàn-jī
  python3 lookup.py taigi.db khuann3     # Tâi-lô numeric (tones 1/4 optional)
  python3 lookup.py taigi.db khuànn      # Tâi-lô with diacritics
  python3 lookup.py taigi.db -e "to like"
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tailo import key, toneless  # noqa: E402

db, *args = sys.argv[1:]
con = sqlite3.connect(db)
eng = args[0] == '-e'
q = args[1] if eng else args[0]
SRC_ORDER = "CASE source WHEN 'moe' THEN 0 WHEN 'itaigi' THEN 1 WHEN 'tgb' THEN 2 WHEN 'taihoa' THEN 3 ELSE 4 END"

if eng:
    rows = con.execute(f"SELECT id FROM entry WHERE source='moe' AND english LIKE ? ORDER BY freq DESC LIMIT 15",
                       (f'%{q}%',)).fetchall()
elif any('㐀' <= c <= '鿿' or ord(c) > 0x20000 for c in q):
    rows = con.execute(f"""SELECT id FROM entry WHERE hanji=? AND source IN ('moe','itaigi','tgb','taihoa')
                           UNION SELECT entry_id FROM mandarin WHERE word=?""", (q, q)).fetchall()
else:
    k = key(q)
    col = 'toneless' if not any(ch.isdigit() for ch in k) and k == toneless(key(q)) and q.isascii() else 'tkey'
    rows = con.execute(f"SELECT id FROM entry WHERE {col}=? AND source IN ('moe','itaigi','tgb','taihoa')",
                       (k if col == 'tkey' else toneless(k),)).fetchall()

ids = [r[0] for r in rows]
if not ids:
    print('no match')
    sys.exit()
res = con.execute(f"""SELECT id, source, hanji, tailo, freq, freq_rank, wenbai, mandarin_best, hsk_old, hsk_new,
                     cognate, english FROM entry WHERE id IN ({','.join('?' * len(ids))})
                     ORDER BY {SRC_ORDER}, freq DESC LIMIT 25""", ids).fetchall()
for (eid, src, h, t, f, rk, wb, mb, ho, hn, cog, en) in res:
    mands = [m for (m,) in con.execute('SELECT DISTINCT word FROM mandarin WHERE entry_id=?', (eid,))]
    print(f"[{src}] {h or ''}  {t}   freq={f} rank={rk or '-'} {('('+wb+')') if wb else ''}")
    if mands:
        print(f"   華語: {'、'.join(mands[:8])}   best={mb} HSK old={ho} new={hn}  cognate={cog}")
    if en:
        print(f"   EN: {en[:120]}")
    if src == 'moe':
        for pos, d in con.execute('SELECT pos, definition_zh FROM sense WHERE entry_id=? ORDER BY ord', (eid,)):
            print(f"   【{pos}】{d}")
        for hz, tl, md in con.execute("SELECT hanji, tailo, mandarin FROM example WHERE entry_id=? LIMIT 3", (eid,)):
            print(f"     例 {hz} | {tl} | {md}")

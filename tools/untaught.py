"""Frequent core words never used anywhere in the course (base lessons, 進修, themes, exercises) and never declared.

  python3 -I tools/untaught.py [TOP]        # default TOP=3000: frequency rank limit
  (tools/wordcheck.py tells where a given word is first used or declared.)
"""
import sys, glob, sqlite3, yaml, re
import os
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, root+'/tools')
from lint import words
con=sqlite3.connect(root+'/data/build/taigi.db')
seen=set(); declh=set()
for f in glob.glob(root+'/course/lessons/[0-9]*.yaml')+glob.glob(root+'/course/perfectionnement/[0-9]*.yaml')+glob.glob(root+'/course/themes/*.yaml'):
    d=yaml.safe_load(open(f))
    lines=[l['tailo'] for l in d.get('dialogue',[]) or []]
    for sec in d.get('sections',[]) or []: lines+=[w['tailo'] for w in sec['words']]+[t['tailo'] for t in sec.get('text',[])]
    for ex in (d.get('exercises') or {}).values():
        lines+=[e['tailo'] for e in ex]
    for t in lines:
        for _,k,_,_ in words(t): seen.add(k)
    for w in d.get('new_words') or []: declh.add(w['hanji'])
top=int(sys.argv[1]) if len(sys.argv)>1 and sys.argv[1].isdigit() else 3000
rows=con.execute("SELECT v.freq_rank,v.hanji,v.tailo,e.tkey,v.mandarin_best,v.cognate,e.id FROM v_core v JOIN entry e ON e.id=v.entry_id WHERE v.freq_rank<=? ORDER BY v.freq_rank",(top,)).fetchall()
for rk,h,t,k,mb,cog,eid in rows:
    if k in seen or h in declh: continue
    if len(h)==1 and cog=='same': continue
    d=con.execute("select definition_zh from sense where entry_id=? order by ord limit 1",(eid,)).fetchone()
    print(f"{rk}\t{h}\t{t}\t{mb}\t{cog[:4]}\t{(d[0] if d else '')[:28]}")

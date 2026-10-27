"""Where is each word first used and first declared? Labels: N = base lesson, PN = 進修, T… = theme.

  python3 -I tools/wordcheck.py 觀音=Kuan-im 拄拄=tú-tú
"""
import sys, glob, yaml
import os
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, root+'/tools')
from lint import words
from tailo import key
seen={}; decl={}
for f in sorted(glob.glob(root+'/course/lessons/[0-9]*.yaml'))+sorted(glob.glob(root+'/course/perfectionnement/[0-9]*.yaml'))+glob.glob(root+'/course/themes/*.yaml'):
    d=yaml.safe_load(open(f)); lab=('P' if 'perf' in f else 'T' if 'themes' in f else '')+str(d['id'])
    lines=[l['tailo'] for l in d.get('dialogue',[]) or []]
    for sec in d.get('sections',[]) or []: lines+=[w['tailo'] for w in sec['words']]+[t['tailo'] for t in sec.get('text',[])]
    for ex in (d.get('exercises') or {}).values(): lines+=[e['tailo'] for e in ex]
    for t in lines:
        for _,k,_,_ in words(t): seen.setdefault(k,lab)
    for w in d.get('new_words') or []: decl.setdefault(w['hanji'],lab)
for a in sys.argv[1:]:
    h,t=a.split('=')
    k=key(t)
    print(f"{h} {t}: used={seen.get(k,'-')} declared={decl.get(h,'-')}")

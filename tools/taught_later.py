"""Words used before they are taught: for lessons A..B, list words in dialogue and exercise lines whose first
declaration (or, if never declared, first use) is in a LATER lesson. 進修 N counts as 100 + N.
Some hits are homophones (kah 甲/佮, khì 去/氣); read the list, don't trust it blindly.

  python3 -I tools/taught_later.py 22 49
  python3 -I tools/taught_later.py 115 121     # 進修 15–21
"""
import sys, glob, yaml
import os
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, root+'/tools')
from lint import words
from tailo import key
first={}  # tkey -> lesson number of first declaration (by tailo key of new_words)
firstuse={}
docs={}
for f in sorted(glob.glob(root+'/course/lessons/[0-9]*.yaml'))+sorted(glob.glob(root+'/course/perfectionnement/[0-9]*.yaml')):
    d=yaml.safe_load(open(f)); n=d['id']+(100 if 'perf' in f else 0); docs[n]=d
    for w in d.get('new_words') or []:
        k=key(w['tailo']); first.setdefault(k,n)
    for l in d.get('dialogue',[]) or []:
        for _,k,_,_ in words(l['tailo']): firstuse.setdefault(k,n)
A,B=int(sys.argv[1]),int(sys.argv[2])
for n in range(A,B+1):
    d=docs[n]; out=set()
    texts=[l['tailo'] for l in d['dialogue']]+[e['tailo'] for ex in d['exercises'].values() for e in ex]
    for t in texts:
        for surf,k,_,_ in words(t):
            fd=first.get(k)
            if fd and fd>n: out.add(f"{surf}(decl {fd})")
            elif not fd and firstuse.get(k,0)>n: out.add(f"{surf}(used {firstuse[k]})")
    if out: print(n, ' '.join(sorted(out)))

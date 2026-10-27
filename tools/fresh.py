"""python3 -I tools/fresh.py NN [NN...]: for 進修 lesson NN, list (a) words in lines that no earlier lesson uses or declares and that
are not in its new_words; (b) new_words already declared earlier (hanji) or used earlier (key)."""
import sys, glob, yaml, os
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, root+'/tools')
from lint import words
from tailo import key
docs={}
for f in sorted(glob.glob(root+'/course/lessons/[0-9]*.yaml'))+sorted(glob.glob(root+'/course/perfectionnement/[0-9]*.yaml')):
    d=yaml.safe_load(open(f)); docs[d['id']+(100 if 'perf' in f else 0)]=d
themes=[yaml.safe_load(open(f)) for f in glob.glob(root+'/course/themes/*.yaml')]
for a in sys.argv[1:]:
    n=100+int(a); d=docs[n]
    seen=set(); declh={}; 
    for m,e in docs.items():
        if m>=n: continue
        for l in e.get('dialogue') or []:
            for _,k,_,_ in words(l['tailo']): seen.add(k)
        for ex in (e.get('exercises') or {}).values():
            for x in ex:
                for _,k,_,_ in words(x['tailo']): seen.add(k)
        for w in e.get('new_words') or []: seen.add(key(w['tailo'])); declh.setdefault(w['hanji'],m)
    own={key(w['tailo']) for w in d.get('new_words') or []}
    unk=[]
    for l in d['dialogue']+[x for ex in d['exercises'].values() for x in ex]:
        for s,k,_,cap in words(l['tailo']):
            if k not in seen and k not in own and s not in unk: unk.append(s)
    print(f"P{a}: {len(d.get('new_words') or [])} new_words, {len(d['dialogue'])} lines")
    print("  undeclared new:", ' '.join(unk))
    for w in d.get('new_words') or []:
        if w['hanji'] in declh: print(f"  DUP {w['hanji']} declared in {declh[w['hanji']]}")
        elif key(w['tailo']) in seen: print(f"  used-before {w['hanji']} {w['tailo']}")

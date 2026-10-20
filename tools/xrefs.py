"""Part-2 checks across all lessons: duplicate new_words (reported for 進修 lessons only) and
"(lesson N)" / "(進修 N)" references in 進修 notes that don't point to the lesson declaring the word.

  python3 -I tools/xrefs.py
"""
import glob, os, re, sys, yaml
root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
files = sorted(glob.glob(f'{root}/course/lessons/[0-9]*.yaml')) + sorted(glob.glob(f'{root}/course/perfectionnement/[0-9]*.yaml'))
decl = {}   # hanji -> label
dups = []
docs = []
for f in files:
    d = yaml.safe_load(open(f, encoding='utf-8'))
    lab = ('P' if 'perf' in f else '') + str(d['id'])
    docs.append((lab, d))
    for w in d.get('new_words') or []:
        h = w['hanji']
        if h in decl:
            dups.append((h, decl[h], lab))
        else:
            decl[h] = lab
dups = [d for d in dups if d[2].startswith('P')]
for h, a, b in dups:
    print(f'DUP {h}: {a} and {b}')
bad = 0
for lab, d in docs:
    if not lab.startswith('P'):
        continue
    for n in d.get('notes') or []:
        t = n['text']
        for m in re.finditer(r'\((lesson|進修)\s*(\d+)\)', t):
            ref = ('P' if m.group(1) == '進修' else '') + m.group(2)
            before = t[:m.start()]
            hz = re.findall(r'[㐀-鿿\U00020000-\U0003ffff]+', before)
            if not hz:
                continue
            w = hz[-1]
            got = decl.get(w)
            if got != ref:
                bad += 1
                print(f'XREF {lab} ref {n["ref"]}: {w} says {ref}, declared in {got}')
print(f'{len(dups)} duplicates, {bad} xref mismatches')

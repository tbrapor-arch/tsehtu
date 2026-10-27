"""Append dialogue lines, notes, new_words and exercise items to base lessons, keeping each file's YAML style.
Usage: python3 -I tools/extend_lessons.py ADDITIONS.yaml
ADDITIONS: {lesson_id: {lines: [...], notes: [...], new_words: [...], translate: [...], fill: [...]}}
"""
import json, sys, yaml

import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
q = lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, str) else str(v)
ORDER = {'line': ['n', 'speaker', 'hanji', 'tailo', 'en', 'zh', 'groups', 'source'],
         'note': ['ref', 'topic', 'text'], 'nw': ['tailo', 'hanji', 'en'],
         'tr': ['tailo', 'hanji', 'en'], 'fill': ['tailo', 'hanji', 'answer', 'answer_hanji', 'en']}


def item(d, kind, flow, indent):
    keys = [k for k in ORDER[kind] if k in d]
    if flow:
        return ' ' * indent + '- {' + ', '.join(f'{k}: {q(d[k])}' for k in keys) + '}\n'
    out = ' ' * indent + '- ' + f'{keys[0]}: {q(d[keys[0]])}\n'
    for k in keys[1:]:
        out += ' ' * indent + f'  {k}: {q(d[k])}\n'
    return out


def insert_before(s, marker, text):
    i = s.index(marker)
    return s[:i + 1] + text + s[i + 1:]


adds = yaml.safe_load(open(sys.argv[1], encoding='utf-8'))
for lid, a in adds.items():
    path = f'{ROOT}/course/lessons/{int(lid):03d}.yaml'
    s = open(path, encoding='utf-8').read()
    flow = '{n:' in s
    ind = 2 if flow else 0
    eind = 4 if flow else 2
    d0 = yaml.safe_load(s)
    last = d0['dialogue'][-1]['n']
    for i, l in enumerate(a.get('lines', [])):
        assert l['n'] == last + 1 + i, (lid, l['n'])
    s = insert_before(s, '\nnotes:', ''.join(item(l, 'line', flow, ind) for l in a.get('lines', [])))
    s = insert_before(s, '\nnew_words:', ''.join(item(n, 'note', flow, ind) for n in a.get('notes', [])))
    if a.get('new_words'):
        nw = ''.join(item(w, 'nw', flow, ind) for w in a['new_words'])
        if '\nnew_words: []' in s:
            s = s.replace('\nnew_words: []', '\nnew_words:\n' + nw.rstrip('\n'))
        else:
            s = insert_before(s, '\nexercises:', nw)
    if a.get('translate'):
        s = insert_before(s, '\n  fill:', ''.join(item(t, 'tr', flow, eind) for t in a['translate']))
    if a.get('fill'):
        s = insert_before(s, '\naudio:', ''.join(item(t, 'fill', flow, eind) for t in a['fill']))
    yaml.safe_load(s)  # still valid
    open(path, 'w', encoding='utf-8').write(s)
    print('ok', lid, len(a.get('lines', [])), 'lines', len(a.get('new_words', [])), 'words')

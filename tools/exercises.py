"""Add exercise sentences to lessons, with the checks used on 27 Oct 2026 (2 "What does it mean?" + 1 "Fill the gap"
per lesson, new sentences, not from the dialogue). See docs/exercises-handover.md.

  python3 tools/exercises.py brief 22 30            compact view of lessons 22-30 (P1 = 101): new words, dialogue, exercises
  python3 tools/exercises.py check batch.txt        check a batch without writing
  python3 tools/exercises.py apply batch.txt        check, then append the items to the lesson files (in each file's style)
  then: python3 -I tools/lint.py

Batch file: one sentence per line, fields separated by ' | ' (# starts a comment):
  <id> | T | tailo | hanji | en
  <id> | F | tailo with ___ | hanji with ___ | answer | answer Hàn-jī | en          (id: 30, or P5 for 進修 5)
Checks: not a dialogue line (nor an existing exercise); every word already met by that lesson (dialogues, new words and
exercises of this and earlier lessons); a gap in both lines; LENGTH: each sentence at least 80 % of the median length
(in syllables) of the lesson's dialogue lines, so new sentences read like the lesson's own.
"""
import json
import os
import re
import statistics
import sys
import unicodedata

import yaml

import glob  # noqa: E402
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from lint import words  # noqa
from tailo import key  # noqa


def files():
    """[(lesson id, path)] in course order: 1-100 then P1.. as 101.."""
    out = [(int(os.path.basename(f)[:3]), f) for f in sorted(glob.glob(ROOT + '/course/lessons/[0-9]*.yaml'))]
    out += [(100 + int(os.path.basename(f)[:2]), f) for f in sorted(glob.glob(ROOT + '/course/perfectionnement/[0-9]*.yaml'))]
    return out


def keys_of(tailo):
    return {k for _, k, _, _ in words(tailo or '') if k}


def lesson_keys(d):
    ks = set()
    for ln in d.get('dialogue') or []:
        ks |= keys_of(ln.get('tailo'))
    for w in d.get('new_words') or []:
        ks |= keys_of(w.get('tailo'))
        ks.add(key(w.get('tailo', '')))
    for items in (d.get('exercises') or {}).values():
        for it in items or []:
            t = it.get('tailo') or ''
            ks |= keys_of(t.replace('___', it.get('answer', '')))
    return ks


SYL = re.compile(r"[A-Za-zÀ-ɏ̀-ͯⁿ]+")


def syllables(t):
    return len(SYL.findall((t or "").replace("___", "x")))


def brief(lo, hi):
    for i, f in files():
        if not lo <= i <= hi:
            continue
        d = yaml.safe_load(open(f, encoding='utf-8'))
        print(f"## {i} {d['title']['hanji']} · {d['title']['en']} | {d.get('setting','')[:90]}")
        print('NEW:', '; '.join(f"{w['hanji']} {w['tailo']}={w.get('en','')}" for w in d.get('new_words') or []))
        print('DLG:', ' / '.join(ln['hanji'] for ln in d['dialogue']))
        ex = d.get('exercises') or {}
        print('EX:', ' / '.join(it['hanji'] for k in ex for it in ex[k] or []))


def run(path, check_only):
    # batch file: one sentence per line, fields separated by ' | ':  <id> | T | tailo | hanji | en   or
    #   <id> | F | tailo with ___ | hanji with ___ | answer | answer Hàn-jī | en      (id: 30 or P5; # starts a comment)
    B = {}
    for row in open(path, encoding='utf-8'):
        row = row.strip()
        if not row or row.startswith('#'):
            continue
        c = [x.strip() for x in row.split(' | ')]
        e = B.setdefault(c[0], {'t': []})
        if c[1] == 'T':
            assert len(c) == 5, row
            e['t'].append(c[2:])
        else:
            assert len(c) == 7, row
            e['f'] = c[2:]
    F = files()
    known = {}
    acc = set()
    for i, f in F:
        d = yaml.safe_load(open(f, encoding='utf-8'))
        acc |= lesson_keys(d)
        known[i] = set(acc)
    norm = lambda s: re.sub(r'[\s，。！？、,.!?「」"“”]', '', unicodedata.normalize('NFC', s))
    q = lambda s: json.dumps(s, ensure_ascii=False)
    problems = 0
    for sid, it in B.items():
        i = int(str(sid).lstrip('P')) + (100 if str(sid).startswith('P') else 0)
        f = dict(F)[i]
        d = yaml.safe_load(open(f, encoding='utf-8'))
        dl = {norm(ln['hanji']) for ln in d['dialogue']}
        med = statistics.median(syllables(ln['tailo']) for ln in d['dialogue'])
        sents = [(t[0], t[1]) for t in it['t']] + [(it['f'][0].replace('___', it['f'][2]), it['f'][1].replace('___', it['f'][3]))]
        old = [x['hanji'] for k in (d.get('exercises') or {}) for x in d['exercises'][k] or []]
        for tl, h in sents:
            if norm(h) in dl or any(norm(h) in x or x in norm(h) for x in dl if len(x) > 6):
                print(f'{sid}: COPIES THE DIALOGUE: {h}'); problems += 1
            if norm(h) in {norm(o.replace('___', '')) for o in old}:
                print(f'{sid}: same as an existing exercise: {h}'); problems += 1
            if syllables(tl) < 0.8 * med:
                print(f'{sid}: TOO SHORT ({syllables(tl)} syllables, the dialogue lines have {med:g}): {tl}'); problems += 1
            new = keys_of(tl) - known[i]
            if new:
                print(f'{sid}: words not met by lesson {sid}: {sorted(new)} in {tl}')
        if '___' not in it['f'][0] or '___' not in it['f'][1]:
            print(f'{sid}: fill without ___'); problems += 1
        if check_only:
            continue
        src = open(f, encoding='utf-8').read().split('\n')
        ti = src.index('  translate:'); fi = src.index('  fill:')
        end = next((j for j in range(fi + 1, len(src)) if src[j] and not src[j].startswith(' ')), len(src))
        while src[end - 1] == '':
            end -= 1
        ft = it['f']
        if src[ti + 1].startswith('    - {'):     # this file writes its items in flow style, indented 4
            fill = ['    - {' + f'tailo: {q(ft[0])}, hanji: {q(ft[1])}, answer: {q(ft[2])}, answer_hanji: {q(ft[3])}, en: {q(ft[4])}' + '}']
            tr = ['    - {' + f'tailo: {q(t[0])}, hanji: {q(t[1])}, en: {q(t[2])}' + '}' for t in it['t']]
        else:
            ind = '    ' if src[ti + 1].startswith('    - ') else '  '
            fill = [f'{ind}- tailo: {q(ft[0])}', f'{ind}  hanji: {q(ft[1])}', f'{ind}  answer: {q(ft[2])}', f'{ind}  answer_hanji: {q(ft[3])}', f'{ind}  en: {q(ft[4])}']
            tr = [x for t in it['t'] for x in (f'{ind}- tailo: {q(t[0])}', f'{ind}  hanji: {q(t[1])}', f'{ind}  en: {q(t[2])}')]
        src = src[:fi] + tr + src[fi:end] + fill + src[end:]
        open(f, 'w', encoding='utf-8').write('\n'.join(src))
        yaml.safe_load(open(f, encoding='utf-8'))   # still valid YAML
    print('problems:', problems)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'brief':
        brief(int(sys.argv[2]), int(sys.argv[3]))
    elif cmd in ('check', 'apply'):
        run(sys.argv[2], cmd == 'check')
    else:
        print(__doc__)

"""Tone-change practice items, built from the course's new words.

For each word of 2–3 syllables whose spoken form differs from the written one (tone sandhi), the learner sees the
written Tâi-lô and picks how it is said. Wrong options are typical mistakes: no change at all, changing the last
syllable too, or a wrong new tone on the first syllable. Words with 仔 á, neutral tone (--) or the 阿 prefix are
left out (their rules are special). Southern 5→3 is not used.
"""
import random
import re

from sandhi import change, parse, render, sandhi

NAMES = {'1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '7': '7', '8': '8'}


def _syls(t):
    return [s for s in t.split('-') if s]


def _form(syls):
    return '-'.join(syls)


def item(hanji, tailo, en, lesson):
    t = tailo.strip()
    if '--' in t or ' ' in t or not re.fullmatch(r"[A-Za-zÀ-ɏḀ-ỿ̀-ͯ-]+", t):
        return None
    syls = _syls(t)
    if not 2 <= len(syls) <= 3 or any(parse(s)[0] in ('a',) and parse(s)[1] == '2' for s in syls[1:]):
        return None
    if parse(syls[0])[0] == 'a' and parse(syls[0])[1] == '1':
        return None
    spoken = sandhi(t, 'word')[0]
    if spoken == t:
        return None
    parsed = [parse(s) for s in syls]
    # distractor 1: written form unchanged; 2: last syllable changed as well; 3: wrong new tone on the first syllable
    all_changed = [render(*change(b, tn)[:2], cap) for b, tn, cap in parsed]
    b0, t0, c0 = parsed[0]
    nb, nt = change(b0, t0)
    wrong = [x for x in '1235 7 8'.replace(' ', '') if x not in (t0, nt)]
    if is_checked_base(nb):
        wrong = [x for x in wrong if x in '48'] or ['4']
    else:
        wrong = [x for x in wrong if x not in '48']
    rnd = random.Random(t)
    w3 = render(nb, rnd.choice(wrong), c0) if wrong else None
    opts = {spoken, t, _form(all_changed), _form([w3] + _syls(spoken)[1:]) if w3 else t}
    opts = [o for o in opts if o]
    if len(opts) < 3:
        return None
    steps = []
    for i, (b, tn, cap) in enumerate(parsed):
        if i < len(parsed) - 1:
            sb, st = change(b, tn)
            why = 'drops -h' if b.endswith('h') and not sb.endswith('h') else ''
            steps.append(f'{render(b, tn, cap)} (tone {tn}) → {render(sb, st, cap)} (tone {st}){", " + why if why else ""}')
        else:
            steps.append(f'{render(b, tn, cap)} keeps tone {tn}: last syllable of the group')
    return {'h': hanji, 't': t, 's': spoken, 'en': en, 'l': lesson, 'opts': sorted(opts, key=lambda o: rnd.random()), 'why': steps}


def is_checked_base(b):
    return bool(re.search(r'[ptkh]$', b)) and not b.endswith('ng')


def build(lessons):
    seen, out = set(), []
    for L in lessons:
        for w in L['new_words']:
            it = item(w['hanji'], w['tailo'], w.get('en') or '', L['id'])
            if it and it['t'] not in seen:
                seen.add(it['t'])
                out.append(it)
    return out

"""Check lesson files against the vocabulary database.

  python3 tools/lint.py [lesson.yaml ...]      (default: course/lessons/[0-9]*.yaml)

Checks
  E  invalid Tâi-lô syllable or impossible tone (e.g. a -p/-t/-k/-h syllable with tone 2)
  E  word not found in any dictionary (MOE, iTaigi, 台華線頂, 1956 basic sentences)
  W  compound not in a dictionary, but every syllable is a known word
  W  Hàn-jī differ from the MOE dictionary's spelling for that reading
  W  Hàn-jī and Tâi-lô have different syllable counts (cannot align)
  E  line marked `source: moe` is not an exact MOE example sentence
  E  new_words entry not in the MOE dictionary with that Hàn-jī + reading
  E  missing required fields
Exit code 1 if any E.
"""
import glob
import os
import re
import sqlite3
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from tailo import key  # noqa: E402

ROOT = os.path.dirname(HERE)
DB = os.path.join(ROOT, 'data/build/taigi.db')
CJK = r'[㐀-鿿\U00020000-\U0003ffff豈-﫿]'
UNIT_RE = re.compile(CJK + r"|[A-Za-zÀ-ɏ̀-ͯḀ-ỿⁿ]+[0-9]?")
INITIALS = ['tsh', 'ts', 'ph', 'th', 'kh', 'ng', 'p', 'b', 'm', 't', 'n', 'l', 'k', 'g', 'h', 's', 'j', '']
FINALS = set('''a ah ai aih ainn ainnh ak am an ang ann annh ap at au auh aunn aunnh e eh en enn ennh i ia iah iak
iam ian iang iann iannh iap iat iau iauh iaunn ih ik im in ing inn innh io ioh iok iong ionn ip it iu iuh iunn iunnh
m mh ng ngh o oh ok om ong onn onnh oo ooh op u ua uah uai uainn uainnh uan uang uann uat ue ueh uh ui uinn uinnh
un ut'''.split())
PUNCT = ".,!?;:'\"「」『』、。，！？；：()（）…—–“”‘’"


def load_db():
    con = sqlite3.connect(DB)
    keys = set()
    pairs = {}
    for h, k, src in con.execute("SELECT hanji, tkey, source FROM entry WHERE source IN ('moe','itaigi','taihoa','tgb') "
                                 "AND tkey != ''"):
        keys.add(k)
        if src == 'moe' and h:
            pairs.setdefault(k, set()).add(h)
    for (k,) in con.execute('SELECT tkey FROM variant'):
        keys.add(k)
    moe_ex = {(h, t) for h, t in con.execute("SELECT hanji, tailo FROM example WHERE source='moe'")}
    return keys, pairs, moe_ex


def valid_syllable(s):
    """s: numeric syllable as produced by key(), e.g. 'tsit8'."""
    m = re.match(r'^([a-z]+?)([0-9]?)$', s)
    body, tone = m.group(1), m.group(2)
    for ini in INITIALS:
        if body.startswith(ini):
            fin = body[len(ini):]
            if fin in FINALS or (ini in ('m', 'ng') and fin == ''):
                break
    else:
        return f'not a Tâi-lô syllable: {s}'
    checked = body[-1] in 'ptkh' and not body.endswith('ng')
    if checked and tone not in ('', '8', '9'):
        return f'{s}: a syllable ending in -{body[-1]} can only have tone 4 or 8'
    if not checked and tone == '8':
        return f'{s}: tone 8 is only for syllables ending in -p/-t/-k/-h'
    return None


def words(tailo):
    """Split a Tâi-lô line into (surface, key, neutral) word parts. 'khì--bô' -> khì, bô(neutral)."""
    out = []
    sentence_start = True
    for raw in tailo.split():
        w = raw.strip(PUNCT)
        first = sentence_start
        sentence_start = bool(re.search(r'[.!?。！？：:]["」』”]*$', raw))
        if not w:
            sentence_start = sentence_start or first
            continue
        parts = w.split('--')
        for j, p in enumerate(parts):
            p = p.strip('-' + PUNCT)
            if p:
                out.append((p, key(p), j > 0, first and j == 0))
    return out


def units(text):
    return UNIT_RE.findall(text.replace('-', ' '))


def lint(path, keys, pairs, moe_ex):
    msgs = []

    def m(level, where, text):
        msgs.append((level, f'{os.path.relpath(path, ROOT)}:{where}: {level} {text}'))

    try:
        d = yaml.safe_load(open(path, encoding='utf-8'))
    except yaml.YAMLError as e:
        m('E', 0, f'YAML error: {e}')
        return msgs
    for f in ('id', 'title', 'dialogue', 'notes', 'new_words'):
        if f not in d:
            m('E', 0, f'missing field: {f}')

    def check_line(where, hanji, tailo, sentence_start=True):
        ws = words(tailo)
        for surf, k, neutral, first in ws:
            if not k:
                if re.search(r'[A-Za-z]', surf):
                    m('E', where, f'cannot read "{surf}"')
                continue
            for s in k.split('-'):
                err = valid_syllable(s)
                if err:
                    m('E', where, err)
            if k in keys:
                continue
            if surf[0].isupper() and not first:
                m('I', where, f'"{surf}" treated as a name')
                continue
            if all(s in keys for s in k.split('-')):
                m('W', where, f'"{surf}" not a dictionary word (each syllable is)')
            else:
                m('E', where, f'"{surf}" not found in any dictionary')
        if not hanji:
            return
        u = units(hanji)
        nsyl = sum(len(k.split('-')) for _, k, _, _ in ws if k)
        if len(u) != nsyl:
            m('W', where, f'Hàn-jī has {len(u)} syllables, Tâi-lô has {nsyl}: cannot align')
            return
        i = 0
        for surf, k, _, _ in ws:
            if not k:
                continue
            n = len(k.split('-'))
            seg = ''.join(u[i:i + n])
            i += n
            if not re.match(CJK, seg[:1]) or k not in pairs:
                continue
            if seg not in pairs[k]:
                m('W', where, f'{seg} {surf}: MOE writes this reading as {"/".join(sorted(pairs[k]))}')

    for line in d.get('dialogue', []) or []:
        n = line.get('n', '?')
        for f in ('hanji', 'tailo', 'en'):
            if not line.get(f):
                m('E', f'line {n}', f'missing {f}')
        check_line(f'line {n}', line.get('hanji', ''), line.get('tailo', ''))
        g = line.get('groups')
        if g and re.sub(r'\s*\|\s*', ' ', g).strip() != (line.get('tailo') or '').strip():
            m('E', f'line {n}', 'groups must equal tailo with | added between tone groups')
        if line.get('source') == 'moe' and (line.get('hanji'), line.get('tailo')) not in moe_ex:
            m('E', f'line {n}', 'marked source: moe but not an exact MOE example')
    for w in d.get('new_words', []) or []:
        k = key(w.get('tailo', ''))
        h = w.get('hanji')
        if k not in pairs or (h and h not in pairs[k]):
            alt = '/'.join(sorted(pairs.get(k, []))) or 'none'
            lvl = 'W' if k in keys else 'E'
            m(lvl, 'new_words', f'{h} {w.get("tailo")} not in MOE with these Hàn-jī (MOE: {alt})')
    # exercises: any item with a `tailo` field is checked; `___` is filled with `answer`
    for kind, items in (d.get('exercises') or {}).items():
        for j, it in enumerate(items or []):
            t = it.get('tailo')
            if t:
                full = t.replace('___', it.get('answer', '')) if '___' in t else t
                h = it.get('hanji')
                if h and '___' in h:
                    h = h.replace('___', it.get('answer_hanji', ''))
                check_line(f'exercises.{kind}[{j}]', h, full)
    return msgs


def lint_theme(path, keys, pairs, moe_ex):
    """Theme files: every word and every text sentence is checked like a dialogue line."""
    d = yaml.safe_load(open(path, encoding='utf-8'))
    fake = {'id': d.get('id'), 'title': d.get('title'), 'notes': [], 'new_words': [], 'dialogue': []}
    for sec in d.get('sections', []):
        for j, w in enumerate(sec.get('words', [])):
            fake['dialogue'].append({'n': f"{sec['n']}.w{j + 1}", 'hanji': w['hanji'], 'tailo': w['tailo'], 'en': w.get('en')})
            fake['new_words'].append({'tailo': w['tailo'], 'hanji': w['hanji']})
        for j, t in enumerate(sec.get('text', [])):
            fake['dialogue'].append({'n': f"{sec['n']}.t{j + 1}", **t})
    tmp = path + '.lint.tmp'
    yaml.safe_dump(fake, open(tmp, 'w', encoding='utf-8'), allow_unicode=True)
    try:
        return [(lv, t.replace(os.path.basename(tmp), os.path.basename(path))) for lv, t in lint(tmp, keys, pairs, moe_ex)]
    finally:
        os.remove(tmp)


def main():
    files = sys.argv[1:] or ((sorted(glob.glob(os.path.join(ROOT, 'course/lessons/[0-9]*.yaml'))) + sorted(glob.glob(os.path.join(ROOT, 'course/perfectionnement/[0-9]*.yaml'))))
                             + sorted(glob.glob(os.path.join(ROOT, 'course/themes/*.yaml'))))
    keys, pairs, moe_ex = load_db()
    errors = 0
    for f in files:
        fn = lint_theme if 'themes' in os.path.normpath(f).split(os.sep) else lint
        for level, text in fn(f, keys, pairs, moe_ex):
            print(text)
            errors += level == 'E'
    print(f'{len(files)} file(s), {errors} error(s)')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()

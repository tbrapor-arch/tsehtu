"""Check (Hàn-jī, Tâi-lô) pairs against the dictionary database and print a short list of suspects.

  python3 -I tools/verify_words.py words.tsv            # Hàn-jī <TAB> Tâi-lô [<TAB> label], one pair per line
  python3 -I tools/verify_words.py < words.tsv          # the same from stdin
  python3 -I tools/verify_words.py --kaic PATH          # a prep-book list (YAML: sections[].entries[] with n, h, t)
  python3 -I tools/verify_words.py --hanlo PATH         # a JSON table {Tâi-lô: Hàn-jī} (or a list of [Hàn-jī, Tâi-lô])
  python3 -I tools/verify_words.py --lessons            # the course's own new_words (lessons, 進修, 文學)
  options: --db PATH (default data/build/taigi.db), --all (list every suspect, not the first 60 of each class)

Readings are compared by key (tools/tailo.py: tones as numbers, hyphens, spaces and -- alike). Accepted readings of a
Hàn-jī: MOE (main readings, 又唸作 / 俗唸作 / 合音唸作, and the entries the ministry lists under it as 異用字; also
the ministry's current table kautian.ods when it is in data/raw/moe-audio), then iTaigi and 台華線頂對照典 (by Hàn-jī),
then 台灣白話基礎語句 (no Hàn-jī: a reading heard there is only mentioned). Notation understood in the Tâi-lô:
forms of the Hàn-jī joined with ／ and their readings with ' / ' (in the same order), whole-word alternatives with
'/' or '、' (kenn/kinn, huânn、kônn), alternatives for one syllable or part (gōo/ngóo-sî = gōo-sî or ngóo-sî,
bô-bué/bé-hāng, ke-kuè/kue-kè = ke-kuè or kue-kè), one reading per character with '、' (甲乙丙: kah、it、piánn),
and marks in brackets such as (文) or (白), which are ignored.

Classes, most serious first:
  1 reading differs from MOE       MOE has the Hàn-jī, none of the given readings is MOE's (both shown)
  2 only the tone differs          the same syllables as an MOE reading, other tones or a checked tone (gia̍h / giah)
  3 Hàn-jī in no dictionary        with the characters whose given syllable no dictionary has for them
  4 only in a non-MOE source       iTaigi / 台華 have the Hàn-jī, MOE does not
  5 lower severity                 an alternative after / that MOE does not give; or the reading matches MOE only once
                                   hyphens, spaces or the neutral-tone mark -- are ignored
Nothing here changes any file: it only prints.
"""
import collections
import itertools
import json
import os
import re
import sqlite3
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from tailo import key, toneless  # noqa: E402

CJK = re.compile(r'[㐀-䶿一-鿿豈-﫿\U00020000-\U0003ffff]')
SEP = re.compile(r'(--|-|\s+)')
CLASSES = [('differs', 'reading differs from MOE'), ('tone', 'only the tone differs (likely a typo)'),
           ('nodict', 'Hàn-jī in no dictionary'), ('nonmoe', 'only in a non-MOE source'),
           ('minor', 'lower severity (alternative not in MOE; hyphen / space / -- only)')]


def nfc(s):
    return unicodedata.normalize('NFC', str(s or '')).strip()


def clean(t):
    return re.sub(r'[(（][^()（）]*[)）]', '', nfc(t)).strip()


# ---------------------------------------------------------------- the dictionary
class Dict:
    def __init__(self, path):
        con = sqlite3.connect(path)
        self.moe = collections.defaultdict(dict)       # Hàn-jī -> {key: surface}
        self.other = collections.defaultdict(lambda: collections.defaultdict(dict))  # Hàn-jī -> source -> {key: surface}
        self.tgb = set()                               # keys heard in tgb (no Hàn-jī there)
        self.surf = collections.defaultdict(set)       # (Hàn-jī, key) -> every MOE spelling (tsò-lâng and tsò--lâng)
        ent = {}
        for eid, src, h, t, ta in con.execute("SELECT id, source, hanji, tailo, tailo_alt FROM entry "
                                              "WHERE tailo != '' AND kind != 'xref'"):
            h = nfc(h)
            for x in re.split(r'/', ta or t):
                k = key(x)
                if not k:
                    continue
                if src == 'moe':
                    self.moe[h].setdefault(k, nfc(x))
                    self.surf[(h, k)].add(re.sub(r'\s+', '-', nfc(x).lower()))
                    ent[eid] = h
                elif src == 'tgb':
                    self.tgb.add(k)
                elif h:
                    self.other[h][src].setdefault(k, nfc(x))
        for eid, t in con.execute('SELECT entry_id, tailo FROM variant'):
            if eid in ent and key(t):
                self.moe[ent[eid]].setdefault(key(t), nfc(t))
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'alt_hanji' in tables:      # 異用字: the word written with other characters (儂 for 人)
            for eid, h in con.execute('SELECT entry_id, hanji FROM alt_hanji'):
                if eid in ent:
                    for k, s in list(self.moe[ent[eid]].items()):
                        self.moe[nfc(h)].setdefault(k, s)
        try:                           # the ministry's current table, when it is there
            import sutian
            T = sutian.sheets()
        except Exception:
            T = None
        if T:
            ids = {}
            for r in T['詞目']:
                h = re.sub(r'【[^】]*】', '', r['漢字']).strip()
                ids[r['詞目id']] = h
                for x in re.split(r'[/／]', re.sub(r'【[^】]*】', '', r['羅馬字'])):
                    if key(x):
                        self.moe[h].setdefault(key(x), nfc(x))
            for sheet in ('又唸作', '俗唸作', '合音唸作'):
                for r in T[sheet]:
                    for x in re.split(r'[/／、]', r['羅馬字']):
                        if key(x) and r['詞目id'] in ids:
                            self.moe[ids[r['詞目id']]].setdefault(key(x), nfc(x))
            for r in T['異用字']:
                h = ids.get(r['詞目id'])
                if h:
                    for k, s in list(self.moe[h].items()):
                        self.moe[nfc(r['異用字'])].setdefault(k, s)
        self.moe = dict(self.moe)

    def char_ok(self, ch, k):
        """Does any dictionary read this character with this syllable (any tone)?"""
        tl = toneless(k)
        pools = [self.moe.get(ch, {})] + list(self.other.get(ch, {}).values())
        return any(toneless(x) == tl for p in pools for x in p)


# ---------------------------------------------------------------- the notation
def syls(s):
    return [x for x in SEP.split(s) if x and not SEP.fullmatch(x)]


def expand(s, n):
    """Readings a string with / alternatives stands for. n: number of characters (None if unknown)."""
    s = s.strip()
    out = set()
    if '/' not in s:
        return {s}
    # (a) alternatives per syllable: bô-bué/bé-hāng, jîm/lîm/jīm/līm
    parts = SEP.split(s)
    opts = [p.split('/') if '/' in p else [p] for p in parts]
    for combo in itertools.islice(itertools.product(*opts), 256):
        out.add(''.join(combo))
    # (b) whole pieces, the shorter completed from the other: gōo/ngóo-sî, ke-kuè/kue-kè, hīnn/hī-àng-á
    pieces = s.split('/')
    for i in range(len(pieces) - 1):
        left, right = pieces[i], pieces[i + 1]
        out.update({left, right})
        if n:
            ls, rs = syls(left), syls(right)
            if len(ls) < n and len(rs) >= n - len(ls):
                tail = SEP.split(right)
                # keep the right piece's separators: take its last (n - len(ls)) syllables
                k = n - len(ls)
                idx = [j for j, x in enumerate(tail) if x and not SEP.fullmatch(x)]
                if k and len(idx) >= k:
                    j = idx[-k]
                    out.add(left + (tail[j - 1] if j > 0 else '-') + ''.join(tail[j:]))
            if len(rs) < n and len(ls) >= n - len(rs):
                head = SEP.split(left)
                k = n - len(rs)
                idx = [j for j, x in enumerate(head) if x and not SEP.fullmatch(x)]
                if k and len(idx) >= k:
                    j = idx[k - 1]
                    out.add(''.join(head[:j + 1]) + (head[j + 1] if j + 1 < len(head) else '-') + right)
    if n:
        good = {x for x in out if len(syls(x)) == n}
        out = good or out
    return out


def pairs_of(h, t):
    """(Hàn-jī form, [reading strings], [raw alternative pieces]) for one list entry."""
    h, t = nfc(h), clean(t)
    forms = [x.strip() for x in re.split(r'／', h) if x.strip()]
    groups = [x.strip() for x in re.split(r'\s+/\s+|／', t) if x.strip()]
    if len(forms) == len(groups):
        todo = list(zip(forms, [[g] for g in groups]))
    else:
        todo = [(f, groups) for f in forms]
    out = []
    for f, gs in todo:
        chars = CJK.findall(f)
        n = len(chars) if chars and len(chars) == len(f) else None
        alts = []
        for g in gs:
            parts = [p.strip() for p in g.split('、') if p.strip()]
            if n and n > 1 and len(parts) == n and all(len(syls(p.split('/')[0])) == 1 for p in parts):
                for c, p in zip(chars, parts):       # one reading per character: 甲乙丙丁 kah、it、piánn、ting
                    out.append((c, [p]))
                continue
            alts.extend(parts)
        if alts:
            out.append((f, alts))
    return out


# ---------------------------------------------------------------- checking
def sub_of(k, whole):
    a, b = k.split('-'), whole.split('-')
    return any(b[i:i + len(a)] == a for i in range(len(b) - len(a) + 1))


def check(D, label, h, readings):
    """-> (class, message) or None when the pair is fine."""
    if not h or '□' in h or '?' in h or not CJK.search(h):
        return ('skip', None)
    n = len(h) if all(CJK.match(c) for c in h) else None
    cands = {}
    for r in readings:
        for x in expand(r, n):
            if key(x):
                cands[key(x)] = x
    given = ' / '.join(readings)
    moe = D.moe.get(h, {})
    other = D.other.get(h, {})
    head = f'{label}\t{h}\t{given}'
    if not cands:
        return ('skip', None)
    if moe:
        hit = [k for k in cands if k in moe]
        if hit:
            notes = []
            pieces = [p.strip(' -') for r in readings for p in r.split('/')] if any('/' in r for r in readings) else []
            for p in pieces:
                kp = key(p)
                if kp and not any(sub_of(kp, k) for k in hit):
                    notes.append(f'alternative "{p}" not in MOE')
            for k in hit:   # same key, other hyphenation or neutral-tone mark
                a = re.sub(r'\s+', '-', cands[k].lower())
                b = re.sub(r'\s+', '-', moe[k].lower())
                if a != b and a not in D.surf.get((h, k), ()):
                    notes.append(f'written "{cands[k]}", MOE "{moe[k]}"')
                    break
            if notes:
                return ('minor', f'{head}\t' + '; '.join(notes) + f'\tMOE: {" / ".join(sorted(set(moe.values())))}')
            return None
        tl = {toneless(k) for k in moe}
        also = sorted(src for src, d in other.items() if any(k in d for k in cands))
        extra = f'\t(also in {", ".join(also)})' if also else ''
        if any(toneless(k) in tl for k in cands):
            return ('tone', f'{head}\tMOE: {" / ".join(sorted(set(moe.values())))}{extra}')
        return ('differs', f'{head}\tMOE: {" / ".join(sorted(set(moe.values())))}{extra}')
    if other:
        found = {src: d for src, d in other.items() if any(k in d for k in cands)}
        if found:
            return ('nonmoe', f'{head}\tin {", ".join(sorted(found))}')
        return ('nonmoe', f'{head}\tin {", ".join(sorted(other))} with another reading: '
                          + ' / '.join(sorted({s for d in other.values() for s in d.values()}))[:120])
    bad = []
    if n:      # the reading that the characters explain best
        for k, surf in cands.items():
            ss = syls(surf)
            if len(ss) != n:
                continue
            b = [f'{c} {x}' for c, x in zip(h, ss) if not D.char_ok(c, key(x))]
            if not bad or len(b) < len(bad):
                bad = b
            if not b:
                break
    tg = ' (reading heard in 台灣白話基礎語句)' if any(k in D.tgb for k in cands) else ''
    return ('nodict', f'{head}\t' + (('no dictionary reads (in any tone): ' + ', '.join(bad)) if bad else 'each character has its syllable somewhere') + tg)


# ---------------------------------------------------------------- inputs
def from_tsv(lines):
    for i, ln in enumerate(lines, 1):
        ln = ln.rstrip('\n')
        if not ln.strip() or ln.startswith('#'):
            continue
        f = ln.split('\t')
        if len(f) >= 2:
            yield (f[2] if len(f) > 2 else f'line {i}'), f[0], f[1]


def from_kaic(path):
    import yaml
    d = yaml.safe_load(open(path, encoding='utf-8'))
    for s in d.get('sections') or []:
        for e in s.get('entries') or []:
            if e.get('h') and e.get('t'):
                yield f"#{e.get('n')}", str(e['h']), str(e['t'])


def from_hanlo(path):
    d = json.load(open(path, encoding='utf-8'))
    items = d.items() if isinstance(d, dict) else ((t, h) for h, t in d)
    for t, h in items:
        if isinstance(h, str) and isinstance(t, str) and not t.startswith('_'):
            yield t, h, t


def from_lessons():
    import glob
    import yaml
    for sub, tag in (('lessons', 'L'), ('perfectionnement', 'P'), ('literature', '文')):
        for f in sorted(glob.glob(os.path.join(ROOT, 'course', sub, '[0-9]*.yaml'))):
            d = yaml.safe_load(open(f, encoding='utf-8')) or {}
            lid = f"{tag}{os.path.basename(f).split('.')[0].split('-')[0].lstrip('0') or '0'}"
            for w in d.get('new_words') or []:
                if w.get('hanji') and w.get('tailo'):
                    yield lid, str(w['hanji']), str(w['tailo'])


def main(argv):
    db = argv[argv.index('--db') + 1] if '--db' in argv else os.path.join(ROOT, 'data/build/taigi.db')
    if not os.path.exists(db):
        sys.exit(f'no database at {db} (make db)')
    rest = [a for i, a in enumerate(argv) if not a.startswith('--') and (i == 0 or argv[i - 1] not in ('--db', '--kaic', '--hanlo'))]
    if '--kaic' in argv:
        src, what = from_kaic(argv[argv.index('--kaic') + 1]), argv[argv.index('--kaic') + 1]
    elif '--hanlo' in argv:
        src, what = from_hanlo(argv[argv.index('--hanlo') + 1]), argv[argv.index('--hanlo') + 1]
    elif '--lessons' in argv:
        src, what = from_lessons(), 'course new_words'
    elif rest:
        src, what = from_tsv(open(rest[0], encoding='utf-8')), rest[0]
    else:
        src, what = from_tsv(sys.stdin), 'stdin'
    D = Dict(db)
    res = collections.defaultdict(list)
    total = 0
    for label, h, t in src:
        total += 1
        seen = set()
        for form, readings in pairs_of(h, t):
            r = check(D, label, form.replace('--', ''), readings) if '--' in form else check(D, label, form, readings)
            if '--' in form and r and r[0] in ('nodict', 'skip') and len(readings) == 1:
                # a Hàn-lô span with neutral-tone parts (逐--的 jiok--ê, --的--（honn）): each part on its own
                hp, tp = form.split('--'), readings[0].split('--')
                if len(hp) == len(tp):
                    worst = None
                    for j, (x, y) in enumerate(zip(hp, tp)):
                        x = re.sub(r'（[^）]*）', '', x)
                        if CJK.search(x) and key(y):
                            rr = check(D, label, x, ['--' + y if j else y])
                            rank = [c for c, _ in CLASSES].index(rr[0]) if rr and rr[0] in dict(CLASSES) else 99
                            if rr and (worst is None or rank < worst[0]):
                                worst = (rank, rr)
                            elif worst is None:
                                worst = (99, None)
                    r = worst[1] if worst else ('skip', None)
            if r and r[1] and r[1] not in seen:
                seen.add(r[1])
                res[r[0]].append(r[1])
            elif r:
                res[r[0]].append(None)
    limit = None if '--all' in argv else 60
    print(f'# verify_words: {what}: {total} entries checked against {os.path.relpath(db, ROOT)}')
    print('# ' + ', '.join(f'{name}: {len(res[c])}' for c, name in CLASSES) + f', skipped (□ ? or no Hàn-jī): {len(res["skip"])}')
    print('# label\tHàn-jī\tgiven\tdictionary')
    for c, name in CLASSES:
        if not res[c]:
            continue
        print(f'\n## {name} ({len(res[c])})')
        for m in res[c][:limit]:
            print(m)
        if limit and len(res[c]) > limit:
            print(f'… {len(res[c]) - limit} more (--all)')


if __name__ == '__main__':
    main(sys.argv[1:])

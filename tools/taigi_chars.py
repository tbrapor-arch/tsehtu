"""Taigi-only characters: the characters written Taigi uses and Mandarin (almost) never does, as a study list
(Practice › Characters).

A character is listed when it appears in an MOE Taigi headword, is in no HSK word, and either
  - only: no CC-CEDICT word of two or more characters uses it and it is outside Big5 level 1, or it is one of the
    MOE's own created characters (x-造字.csv: 𪜶 𠢕 𤆬 𨑨 𢯾 𬦰 …), or
  - mostly: one to three rare CC-CEDICT words use it, outside Big5 level 1 (恁 囡 戇 踅 庄 …: Mandarin knows it, barely).
Sorted by the best MOE frequency rank of a word that uses it: the top of the list is what a page most likely holds.
Characters met only in headwords taken in from the ministry's current table (no rank, see tools/freq_align.py) come
after all the others, by corpus frequency, so that the existing list and its groups of 25 never move.
Each character gets its reading(s), up to three example words (word cards) and the first lesson that uses it.
"""
import collections
import csv
import os
import re

from tailo import key

HAN = re.compile(r'[㐀-鿿\U00020000-\U0003ffff]')


def _lvl1(ch):
    try:
        v = int.from_bytes(ch.encode('big5'), 'big')
    except Exception:
        return False
    return 0xA440 <= v <= 0xC67E


def good(card):
    """English that was written for this Taigi word, not borrowed from Mandarin or pieced together."""
    return bool(card.get('gloss')) and not re.match(r'(mandarin|parts)', card.get('gloss_src') or '')


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The list's order, pinned (owner's rule, 17 Nov 2026): one character per line, in list order. Groups of 25 follow the
# order, so a character never moves or changes group. A newly qualifying character is appended after the last one
# (and should be added at the end of this file, with its entry in course/chars_examples.yaml); a pinned character
# that no longer qualifies stops the build.
ORDER = os.path.join(ROOT, 'course/chars_order.txt')


def pinned(path=ORDER):
    if not os.path.exists(path):
        return []
    return [ln.strip() for ln in open(path, encoding='utf-8') if ln.strip() and not ln.startswith('#')]


def hsk_chars(con):
    """Characters of HSK words. The HSK table also lists variant traditional forms as words of their own (挵 for 弄,
    摃 for 扛, 桮 for 杯, 闇 for 暗…): a row marked 'variant of' is left out when another row of the same simplified word
    and pinyin is not a variant (fixed 17 Nov 2026: it wrongly kept out 摃 挵 嬭 舖 桮 蹔 闇 鍼 噁 裌)."""
    rows = con.execute('select trad, simp, pinyin, english from hsk').fetchall()
    by = collections.defaultdict(list)
    for r in rows:
        by[(r[1], r[2])].append(r)
    var = lambda r: 'variant of' in (r[3] or '')
    return set(''.join(r[0] for r in rows if not (var(r) and any(o[0] != r[0] and not var(o) for o in by[(r[1], r[2])]))))


def select(con, cedict, zz_path):
    """The selection, shared with the private repo (tools/chars_queue.py, tools/taigi_only.py) so lists cannot drift.
    Returns (use, accepted, rejected): use = {ch: MOE facts}, accepted = {ch: 'only'|'mostly'},
    rejected = {ch: reason} for every other MOE headword character."""
    mw = collections.Counter()
    for t in cedict or {}:          # english.load_cedict(): {traditional: entry}
        if len(t) > 1:
            for ch in set(t):
                if HAN.match(ch):
                    mw[ch] += 1
    hsk = hsk_chars(con)
    zz = set()
    if os.path.exists(zz_path):
        zz = {row['對應字'] for row in csv.DictReader(open(zz_path, encoding='utf-8'))}
    use = {}
    has_added = 'added' in [r[1] for r in con.execute('PRAGMA table_info(entry)')]
    for h, t, rk, new, shared, fq in con.execute(
            "select hanji, tailo, freq_rank, " + ("coalesce(added, 0)" if has_added else "0") + ", kind = 'shared', "
            "coalesce(freq, 0) "
            "from entry where source='moe' and hanji is not null and tailo is not null and tailo != '' and kind != 'xref' "
            "order by case when freq_rank>0 then freq_rank else 999999 end, length(hanji)"):
        t = t.split('/')[0].strip()
        for ch in set(h):
            if not HAN.match(ch):
                continue
            u = use.setdefault(ch, {'rank': 999999, 'words': [], 'read': [], 'late': -1, 'newread': []})
            if rk and rk > 0:
                u['rank'] = min(u['rank'], rk)
            if new or shared:   # unranked (tools/freq_align.py): listed after the ranked characters
                u['late'] = max(u['late'], fq)
            if h == ch:
                # the older export's readings; a reading from the ministry's table only if there is none
                if t not in u['read'] and not new:
                    u['read'].append(t)
                elif new and t not in u['newread']:
                    u['newread'].append(t)
            elif len(u['words']) < 6 and 2 <= len(h) <= 4 and all(w[0] != h for w in u['words']):
                u['words'].append((h, t))
    accepted, rejected = {}, {}
    for ch, u in use.items():
        if ch in hsk:
            rejected[ch] = 'in an HSK word (Mandarin writes it)'
            continue
        if ch in zz or (mw[ch] == 0 and not _lvl1(ch)):
            tier = 'only'
        elif mw[ch] <= 3 and not _lvl1(ch):
            tier = 'mostly'
        else:
            rejected[ch] = f'Mandarin writes it ({mw[ch]} CC-CEDICT words' + (', Big5 level 1)' if _lvl1(ch) else ')')
            continue
        if not u['read']:
            u['read'] = u['newread']
        late = u['rank'] >= 999999 and ch not in zz and u['late'] >= 0
        u['_late'] = late
        if u['rank'] >= 999999 and ch not in zz and not late:
            rejected[ch] = 'no word with a frequency rank (too rare to teach)'
            continue
        if u['read'] and all(r[:1].isupper() for r in u['read']) and not u['words']:
            rejected[ch] = 'a surname or place name only'
            continue
        accepted[ch] = tier
    return use, accepted, rejected


def build(con, cedict, zz_path, lookup, lessons, cards):
    use, accepted, _ = select(con, cedict, zz_path)
    first = {}
    for L in sorted(lessons, key=lambda x: x['id']):
        for ln in L['lines']:
            for ch in ln['hanji']:
                first.setdefault(ch, L['id'])
    out = []
    for ch, tier in accepted.items():
        u = use[ch]
        late = u['_late']
        self_id = lookup(ch, key(u['read'][0])) if u['read'] else None
        had = set(cards)
        words = [wid for wid in (lookup(h, key(t)) for h, t in u['words']) if wid]
        # examples with English written for them first (Maryknoll, course), then a Mandarin or pieced-together gloss;
        # the order by frequency is kept inside each kind
        ranked = sorted(words, key=lambda w: not good(cards[w]))
        words = ranked[:3]
        for w in ranked[3:]:
            if w not in had and w not in words:
                del cards[w]      # looked up only to compare: no card for it
        read = u['read'][:3]
        if not read and words:    # the character only in compounds: its syllable in the first example
            h, t = u['words'][0]
            syl = re.split(r'[- ]+', t.replace('--', '-'))
            if len(syl) == len(h):
                read = [syl[h.index(ch)].lower()]
        out.append({'c': ch, 'tier': tier, 'r': read, 'rank': u['rank'] if u['rank'] < 999999 else None,
                    'id': self_id, 'w': words, 'L': first.get(ch), '_late': -u['late'] if late else None})
    out.sort(key=lambda x: (x['_late'] is not None, x['_late'] or 0, x['rank'] or 999999, x['c']))
    for x in out:
        del x['_late']
    return pin(out)


def pin(out, order=None):
    """Put the list in the pinned order (course/chars_order.txt); characters not pinned yet go after, in their own order."""
    order = pinned() if order is None else order
    if not order:
        return out
    by = {x['c']: x for x in out}
    gone = [c for c in order if c not in by]
    if gone:
        raise SystemExit(f'taigi_chars: pinned characters no longer selected: {" ".join(gone)} (course/chars_order.txt; '
                         'the list never loses or moves a character: fix the selection, do not edit the pin)')
    new = [x for x in out if x['c'] not in set(order)]
    if new:
        print(f'taigi_chars: {len(new)} new characters appended after #{len(order)}: {"".join(x["c"] for x in new)} '
              '(add them at the end of course/chars_order.txt, with entries in course/chars_examples.yaml)')
    return [by[c] for c in order] + new


# ---- Lessons › 台語字: an English meaning, the Mandarin counterpart and a public example for every listed character
# (course/chars_examples.yaml, docs/taigi-chars.md). The yaml says which example each character gets:
#   lesson: [lesson id, line n]   a course line (copied with its tokens at build time; `also` = a line given way to)
#   moe: {word, hanji}            an MOE example, found by its headword and Hàn-jī; Tâi-lô and Mandarin are copied from
#                                 the database unaltered (CC BY-ND); `en` is ours, shown labelled as such
#   created: {hanji, tailo, en}   written for the list (every word an MOE word), "not checked by a native speaker"
#   reading_only: true            the MOE gives only the reading (no definition, no word that has one)
#   moe2: {word, hanji}           an MOE sentence shown folded under a lesson line ("Dictionary example")
# `extra:` (same shape, plus `r`, the reading) = characters Mandarin also writes but Taigi uses its own way, shown
# after the list; they are never numbered with it.
EXAMPLES = os.path.join(ROOT, 'course/chars_examples.yaml')
SENT_END = re.compile(r'[。？！!?]["」』”]?$')


def load_examples(path=EXAMPLES):
    import yaml
    return yaml.safe_load(open(path, encoding='utf-8')) if os.path.exists(path) else {}


def moe_example(con, word, hanji):
    """(Hàn-jī, Tâi-lô, Mandarin) of an MOE example of the headword `word`, exactly as in the database, or None."""
    return con.execute("SELECT x.hanji, x.tailo, x.mandarin FROM example x JOIN entry e ON e.id = x.entry_id "
                       "WHERE x.source = 'moe' AND e.source = 'moe' AND e.hanji = ? AND x.hanji = ? "
                       "ORDER BY x.id LIMIT 1", (word, hanji)).fetchone()


PUNCT = re.compile(r'[.,!?;:"“”‘’「」『』、。，！？；：()（）…—–\[\]]')


def _syl(t):
    return [s for s in re.split(r'[\s\-]+', PUNCT.sub(' ', t.lower())) if s]


def read_as(ch, hanji, tailo, readings):
    """True when `ch` in hanji is read with one of `readings` (tones ignored); hanji and tailo must line up."""
    hs = HAN.findall(hanji)
    ss = _syl(tailo)
    if len(hs) != len(ss):
        return False
    want = {re.sub(r'\d', '', key(r)) for r in readings}
    return any(c == ch and re.sub(r'\d', '', key(s)) in want for c, s in zip(hs, ss))


def word_reading(con, word, ch):
    """The readings of `ch` inside the MOE headword `word` (its syllable at that position)."""
    out = set()
    for (t,) in con.execute("SELECT tailo FROM entry WHERE source='moe' AND hanji=? AND tailo != ''", (word,)):
        for alt in t.split('/'):
            ss = _syl(alt)
            hs = HAN.findall(word)
            if len(ss) == len(hs):
                out |= {s for c, s in zip(hs, ss) if c == ch}
    return out


def extra_rows(con, cedict, zz_path, lookup, lessons, cards, ex=None):
    """The rows of the group after the list: characters Mandarin also writes but Taigi uses its own way (啉 啥 夯 箍…)."""
    ex = load_examples() if ex is None else ex
    X = ex.get('extra') or {}
    if not X:
        return []
    use, _, _ = select(con, cedict, zz_path)
    first = {}
    for L in sorted(lessons, key=lambda x: x['id']):
        for ln in L['lines']:
            for c in ln['hanji']:
                first.setdefault(c, L['id'])
    out = []
    for ch, e in X.items():
        r = e['r']
        u = use.get(ch) or {'words': [], 'rank': 999999}
        want = re.sub(r'\d', '', key(r))
        ws = []
        for h, t in u['words']:   # the words where the character has this reading
            ss = _syl(t)
            if len(ss) == len(h) and any(c == ch and re.sub(r'\d', '', key(s)) == want for c, s in zip(h, ss)):
                wid = lookup(h, key(t))
                if wid and len(ws) < 3:
                    ws.append(wid)
        out.append({'c': ch, 'tier': 'shared', 'r': [r], 'rank': u['rank'] if u['rank'] < 999999 else None,
                    'id': lookup(ch, key(r)), 'w': ws, 'L': first.get(ch)})
    return out


def attach(con, rows, lessons, tokenize, written, cards, ex=None, section='chars'):
    """Give each row of DATA.chars (or of the extra group) its meaning `en`, Mandarin `zh` [word, pinyin], and its public
    example `ex` (+ `also`, `ex2`, or `ro` for reading only). Stops on an example the database or the lessons lack."""
    ex = load_examples() if ex is None else ex
    Y = ex.get(section) or {}
    LB = {L['id']: L for L in lessons}
    lit = {}
    for L in sorted(lessons, key=lambda x: x['id']):
        for c in L.get('chars') or []:
            lit.setdefault((c['c'], re.sub(r'\d', '', key(c['tailo']))), c['en'])
    errs = []

    def line(ref, ch):
        L = LB.get(ref[0])
        i = next((i for i, ln in enumerate(L['lines']) if ln['n'] == ref[1]), None) if L else None
        if i is None:
            errs.append(f'{ch}: lesson line {ref} not found')
            return None
        if ch not in L['lines'][i]['hanji']:
            errs.append(f'{ch}: lesson line {ref} does not contain it')
        return [ref[0], i]

    def moe(m, ch, en=None):
        r = moe_example(con, m['word'], m['hanji'])
        if not r:
            errs.append(f"{ch}: MOE example not in the database: {m['word']} / {m['hanji']}")
            return None
        h, t, zh = r
        o = {'k': 'm', 'h': h, 't': t, 'zh': zh or '', 'hw': m['word'], 'tk': tokenize(h, t)}
        if not SENT_END.search(h.strip()):
            o['p'] = 1   # a phrase, not a sentence
        if en:
            o['en'] = en
        return o

    for x in rows:
        ch = x['c']
        e = Y.get(ch)
        k0 = re.sub(r'\d', '', key(x['r'][0])) if x['r'] else ''
        en = lit.get((ch, k0)) or (written.get((ch, key(x['r'][0]))) if x['r'] else None)
        card = cards.get(x['id']) if x.get('id') else None
        if not en and card and good(card):
            en = card['gloss']
        if en:
            x['en'] = en
        if card and card.get('mand'):
            m = card['mand'][0]
            x['zh'] = [m['w'], m.get('py', '')]
        if not e:
            errs.append(f'{ch}: no entry in course/chars_examples.yaml ({section})')
            continue
        if e.get('also_read'):   # a reading an MOE word attests (嘓 kho̍k in 嘓魚)
            ar = e['also_read']
            if ar['r'] in word_reading(con, ar['word'], ch) or any(
                    re.sub(r'\d', '', key(ar['r'])) == re.sub(r'\d', '', key(s)) for s in word_reading(con, ar['word'], ch)):
                if ar['r'] not in x['r']:
                    x['r'] = x['r'] + [ar['r']]
            else:
                errs.append(f"{ch}: also_read {ar['r']} not attested by the MOE word {ar['word']}")
        if e.get('reading_only'):
            x['ro'] = 1
        elif e.get('lesson'):
            ref = line(e['lesson'], ch)
            if ref:
                x['ex'] = {'k': 'l', 'l': ref}
        elif e.get('moe'):
            o = moe(e['moe'], ch, e.get('en'))
            if o:
                x['ex'] = o
        elif e.get('created'):
            c = e['created']
            x['ex'] = {'k': 'c', 'h': c['hanji'], 't': c['tailo'], 'en': c['en'], 'tk': tokenize(c['hanji'], c['tailo'])}
        else:
            errs.append(f'{ch}: no public example and not reading_only')
        if e.get('also'):
            ref = line(e['also'], ch)
            if ref:
                x['also'] = ref
        if e.get('moe2'):
            o = moe(e['moe2'], ch, e.get('en2'))
            if o:
                x['ex2'] = o
    if errs:
        raise SystemExit('course/chars_examples.yaml:\n  ' + '\n  '.join(errs))
    return rows


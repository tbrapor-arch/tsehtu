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


def build(con, cedict, zz_path, lookup, lessons, cards):
    mw = collections.Counter()
    for t in cedict or {}:          # english.load_cedict(): {traditional: entry}
        if len(t) > 1:
            for ch in set(t):
                if HAN.match(ch):
                    mw[ch] += 1
    hsk = set(''.join(r[0] for r in con.execute('select trad from hsk')))
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
    first = {}
    for L in sorted(lessons, key=lambda x: x['id']):
        for ln in L['lines']:
            for ch in ln['hanji']:
                first.setdefault(ch, L['id'])
    out = []
    for ch, u in use.items():
        if ch in hsk:
            continue
        if ch in zz or (mw[ch] == 0 and not _lvl1(ch)):
            tier = 'only'
        elif mw[ch] <= 3 and not _lvl1(ch):
            tier = 'mostly'
        else:
            continue
        if not u['read']:
            u['read'] = u['newread']
        late = u['rank'] >= 999999 and ch not in zz and u['late'] >= 0
        if u['rank'] >= 999999 and ch not in zz and not late:
            continue          # no word with a frequency rank: too rare to teach
        if u['read'] and all(r[:1].isupper() for r in u['read']) and not u['words']:
            continue          # a surname or place name only
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
    return out

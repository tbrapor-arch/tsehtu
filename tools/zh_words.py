"""Mandarin text -> tappable words, each with its pinyin and CC-CEDICT senses: ONE implementation for the app and the
private module (the 華語 · Mandarin sheet: `zhLine()` in app/index.template.html).

How it works
  * A Mandarin text is cut into words by `segment()`: in each run of Han characters, the cut with the lowest total
    cost, a word costing 10, or 9 when it is an HSK word (complete-hsk-vocabulary); among equal cuts, the one whose
    first word is longest (then the same rule for the rest). Words are CC-CEDICT words of up to 8 characters; a
    character CC-CEDICT lacks stays plain text. Integer costs, no frequencies: the browser repeats the exact same cut.
  * Nothing is stored per text. The build collects the words its texts use into one table, `Lexicon.table()`:
    {word: "pinyin<TAB>English" lines, the shown reading first, '*' in front for an HSK word}, shipped once
    (DATA.zh in the app page, exam/zh.json in the private module). The app cuts a text again in the browser with the same rule
    against that table: as every word of the build's cut is in the table and the table holds only CC-CEDICT words,
    the browser finds the same cut (`check()` runs the browser's rule here and counts any difference).
  * Pinyin of a word (the sheet's heading): for a single character, a few fixed readings (SINGLE: 著 zhe, 得 de…);
    for a longer word its HSK reading; else pypinyin's reading; each only when CC-CEDICT has it; else the first
    CC-CEDICT reading (names last). One reading per word, not per sentence: 的 is de everywhere.

    import zh_words
    L = zh_words.Lexicon()
    L.add('首、腦袋。')          # every Mandarin text the page shows (definitions, translations…)
    DATA['zh'] = L.table()               # {word: entry}
    zh_words.check(texts, DATA['zh'])  # -> number of texts the browser would cut differently (0)

Data: data/raw/cedict (CC-CEDICT, CC BY-SA 4.0, MDBG) and data/raw/complete-hsk-vocabulary (MIT), both fetched by
`make data`; CEDICT=path/to/cedict.json (or a cedict_ts.u8 / cedict.txt) to use another copy. pypinyin is optional.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CEDICT = os.environ.get('CEDICT') or os.path.join(ROOT, 'data/raw/cedict/package/cedict.json')
HSK = os.path.join(ROOT, 'data/raw/complete-hsk-vocabulary/complete.min.json')
HAN_CLASS = '㐀-鿿豈-﫿\U00020000-\U0003134f'   # same class as ZH_HAN in the app
HAN = re.compile(f'[{HAN_CLASS}]')
RUN = re.compile(f'([{HAN_CLASS}]+)')
MAXN = 8          # longest word looked up
COST, COST_HSK = 10, 9
SENSES = 4        # readings shown on the sheet
SKIP = ('CL:',)   # CC-CEDICT English items left out (measure words: long and of little use here)
TONES = {'a': 'āáǎàa', 'e': 'ēéěèe', 'i': 'īíǐìi', 'o': 'ōóǒòo', 'u': 'ūúǔùu', 'ü': 'ǖǘǚǜü'}

_ced = _hsk = None


def marks(numbered):
    """CC-CEDICT 'zhong1 guo2' -> 'zhōng guó'"""
    out = []
    for syl in numbered.split():
        m = re.fullmatch(r'([A-Za-zü:]+)([1-5])', syl.replace('u:', 'ü').replace('U:', 'Ü'))
        if not m:
            out.append(syl)
            continue
        b, t = m.group(1), int(m.group(2)) - 1
        low = b.lower()
        i = low.find('a') if 'a' in low else low.find('e') if 'e' in low else low.find('ou') if 'ou' in low \
            else max(low.rfind(v) for v in 'iouü')
        if i < 0:
            out.append(b)
            continue
        mk = TONES[low[i]][t]
        out.append(b[:i] + (mk.upper() if b[i].isupper() else mk) + b[i + 1:])
    return ' '.join(out)


def cedict():
    """{traditional: [[pinyin with marks, [English…]], …]}, Han-only words, in the dictionary's order"""
    global _ced
    if _ced is None:
        _ced = {}
        if not os.path.exists(CEDICT):
            print('zh_words: no CC-CEDICT at', CEDICT, '(make data): Mandarin stays plain text')
            return _ced
        if CEDICT.endswith('.json'):
            rows = ((e['traditional'], e['pinyin'], e['english']) for e in json.load(open(CEDICT, encoding='utf-8')))
        else:   # the original text format: 中國 中国 [Zhong1 guo2] /China/…/   (or shujia's tab-separated copy)
            def parse():
                for line in open(CEDICT, encoding='utf-8'):
                    if line.startswith('#'):
                        continue
                    m = re.match(r'(\S+) \S+ \[([^]]*)\] /(.*)/\s*$', line)
                    if m:
                        yield m.group(1), m.group(2), m.group(3).split('/')
                    elif '\t' in line:
                        t, _, p, en = (line.rstrip('\n').split('\t') + ['', '', ''])[:4]
                        yield t, p, en.split('/')
            rows = parse()
        for t, p, en in rows:
            if t and all(HAN.match(c) for c in t) and len(t) <= MAXN:
                _ced.setdefault(t, []).append([marks(p), [g for g in en if g and not g.startswith(SKIP)]])
    return _ced


def hsk():
    """{traditional: pinyin} for the HSK words (complete-hsk-vocabulary)"""
    global _hsk
    if _hsk is None:
        _hsk = {}
        if os.path.exists(HSK):
            for e in json.load(open(HSK, encoding='utf-8')):
                for f in e['f']:
                    _hsk.setdefault(f['t'], f['i']['y'])
    return _hsk


def available():
    return bool(cedict())


def cost(w):
    return COST_HSK if w in hsk() else COST


def cut_run(cs, known, costof):
    """one run of Han characters (a list of characters) -> list of words. The browser's zhCut() is the same."""
    n = len(cs)
    best, step = [0] * (n + 1), [1] * (n + 1)
    for i in range(n - 1, -1, -1):
        b = None
        for k in range(min(MAXN, n - i), 0, -1):          # longest first: an equal cost keeps the longer word
            w = ''.join(cs[i:i + k])
            if k == 1 or known(w):
                c = (costof(w) if known(w) else COST) + best[i + k]
                if b is None or c < b:
                    b, step[i] = c, k
        best[i] = b
    out, i = [], 0
    while i < n:
        out.append(''.join(cs[i:i + step[i]]))
        i += step[i]
    return out


def segment(text, known=None, costof=None):
    """Mandarin text -> [str | [word]]: a list holds a word that has a CC-CEDICT entry (tappable), plain strings the
    rest (punctuation, Latin, characters CC-CEDICT lacks); neighbouring plain strings are merged."""
    ced = cedict()
    known = known or (lambda w: w in ced)
    costof = costof or cost
    out = []
    def put(s):
        if out and isinstance(out[-1], str):
            out[-1] += s
        else:
            out.append(s)
    for i, part in enumerate(RUN.split(text or '')):
        if not part:
            continue
        if i % 2 == 0:
            put(part)
            continue
        for w in cut_run(list(part), known, costof):
            if known(w):
                out.append([w])
            else:
                put(w)
    return out


# a single character alone in a Mandarin sentence: its usual reading there, where pypinyin's default is another one
SINGLE = {'著': 'zhe', '得': 'de', '地': 'de', '嗎': 'ma', '呢': 'ne', '吧': 'ba', '個': 'ge', '麼': 'me'}


def _syls(p):
    return p.lower().split()


def _base(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', s) if not unicodedata.combining(c)).replace('u\u0308', 'ü')


def _same(ced, want):
    """a CC-CEDICT reading (syllables) and a wanted one: equal, a neutral tone in CC-CEDICT matching any tone"""
    if len(ced) != len(want):
        return False
    return all(a == b or (_base(a) == a and _base(b) == a) for a, b in zip(ced, want))


def pinyin_of(w):
    """the reading shown for a word, and its CC-CEDICT readings in display order (that reading first, names last)"""
    es = cedict().get(w) or []
    want = []
    if len(w) == 1 and w in SINGLE:
        want.append([SINGLE[w]])
    try:
        from pypinyin import pinyin as pp, Style
        py = [x[0] for x in pp(w, style=Style.TONE)]
    except ImportError:
        py = None
    if len(w) > 1 and w in hsk():
        want.append(_syls(hsk()[w]))
    if py:
        want.append([x.lower() for x in py])
    order = sorted(range(len(es)), key=lambda i: es[i][0][:1].isupper())   # names (capitalised) last, else as listed
    pick = next((i for f in want for i in order if _same(_syls(es[i][0]), f)), order[0] if order else None)
    if pick is None:
        return '', []
    rest = [i for i in order if i != pick]
    return es[pick][0].replace(' ', ''), [es[i] for i in [pick] + rest]


class Lexicon:
    """the words a set of texts uses, with what the sheet shows"""
    def __init__(self):
        self.words = set()

    def add(self, text):
        for t in segment(text):
            if isinstance(t, list):
                self.words.add(t[0])
        return self

    def table(self):
        """{word: entry}; entry = the readings, one per line, 'pinyin<TAB>English' (the shown reading first, names
        last), with a leading '*' when the word costs COST_HSK. The sheet's heading is the first pinyin, spaces removed."""
        out = {}
        for w in sorted(self.words):
            es = pinyin_of(w)[1]
            senses = {}
            for p, en in es:        # the same reading listed twice (two entries): one line
                if p in senses or len(senses) < SENSES:
                    senses[p] = senses.get(p, []) + en
            out[w] = ('*' if cost(w) == COST_HSK else '') + '\n'.join(p + '\t' + '; '.join(en) for p, en in senses.items())
        return out


def browser_cut(text, table):
    """what the app does with a table (zhCut in app/index.template.html), for check()"""
    known = lambda w: w in table
    costof = lambda w: COST_HSK if table[w][:1] == '*' else COST
    return segment(text, known, costof)


def check(texts, table):
    """number of texts the browser would cut differently from the build (should be 0)"""
    bad = 0
    for t in texts:
        if browser_cut(t, table) != segment(t):
            bad += 1
            if bad <= 5:
                print('zh_words: browser cut differs:', t[:60])
    return bad


def tokens(text, zc):
    """Former API (prep-book build until Nov 2026): [str | [word, pinyin]], zc collects {word: [[pinyin, English]…]}"""
    out = []
    for t in segment(text):
        if isinstance(t, list):
            py, es = pinyin_of(t[0])
            zc.setdefault(t[0], [[p, '/'.join(en)] for p, en in es[:SENSES]])
            out.append([t[0], py])
        else:
            out.append(t)
    return out


if __name__ == '__main__':   # python3 -I tools/zh_words.py 首、腦袋。  -> the cut and the pinyin
    import sys
    for s in sys.argv[1:] or ['你把事情搞到這種地步才要我來善後，不會太過份了嗎？']:
        print(' / '.join(t[0] + ' ' + pinyin_of(t[0])[0] if isinstance(t, list) else repr(t) for t in segment(s)))

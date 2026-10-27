"""Word cards and line segmentation, shared by the app (tools/build_app.py) and the private module's build (podcast,
drama, songs, books, exam texts), so that a word gets the same card everywhere and lines are cut the same way.

    import cards
    cards.init(con, english.English(con, ...))   # once; cards.dictionary then fills up as words are looked up
    cards.lookup('毋過', 'm-koh')                 # -> card id '毋過|m-koh'
    cards.tokenize(hanji, tailo, groups)          # a line cut by its own Tâi-lô words (the course's rule)
    cards.tokenize(hanji, tailo, fallback=True)   # same, or by the dictionary when the Tâi-lô does not line up

Each word token carries `x`: the other ways the line can be cut at that word (dictionary words starting on the same
character, longest first, the token's own word included), shown on the card as "Other splits". Each card of two or
more characters carries `comp`: the word cut into the longest dictionary words it contains (勞動法 -> 勞動 + 法), shown
as its composition line.
"""
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lint import UNIT_RE, CJK, words  # noqa: E402
from sandhi import sandhi  # noqa: E402
from variants import Variants  # noqa: E402
import english  # noqa: E402
import sutian  # noqa: E402

SOURCES = ('moe', 'itaigi', 'taihoa', 'tgb')
dictionary = {}
con = VARIANTS = SUTIAN = ENGLISH = None
CEDICT = {}
HEAD = set()        # (Hàn-jī, key): what counts as a word for splits and compositions (see init)
FREQ = {}           # (Hàn-jī, key) -> corpus frequency of MOE words, to choose between cuts
BEST = {}           # Hàn-jī -> key of its usual MOE reading (colloquial first, then most frequent)
EXTRA = {}          # Hàn-jī -> key, taihoa words the MOE lacks (2-4 characters written as one word)
MAX = 5


def init(connection, eng=None, ced=None, table=None):
    """Set the database and the English source. `eng` can be set later (cards.ENGLISH = ...) before the first lookup."""
    global con, VARIANTS, SUTIAN, ENGLISH, CEDICT
    con = connection
    VARIANTS = Variants(con)
    SUTIAN = table if table is not None else sutian.load()
    CEDICT = ced if ced is not None else english.load_cedict()
    ENGLISH = eng
    HEAD.clear()
    # MOE words (the other sources list many phrases as words: 真好, 我欲), and single characters from any source
    HEAD.update(con.execute("SELECT hanji, tkey FROM entry WHERE source = 'moe' AND kind IN ('word', 'other') "
                            "AND tkey != '' AND tailo NOT LIKE '% %' AND length(hanji) <= 6"))
    HEAD.update(con.execute(f"SELECT hanji, tkey FROM entry WHERE source IN {SOURCES} AND kind != 'xref' "
                            "AND tkey != '' AND length(hanji) = 1"))
    FREQ.clear()
    for h, k, f in con.execute("SELECT hanji, tkey, max(freq) FROM entry WHERE source = 'moe' AND freq IS NOT NULL GROUP BY 1, 2"):
        FREQ[(h, k)] = f or 0
    BEST.clear()
    for h, k in con.execute("SELECT hanji, tkey FROM entry WHERE source='moe' AND kind != 'xref' AND tailo != '' "
                            "ORDER BY (wenbai='colloquial') DESC, freq DESC"):
        BEST.setdefault(h, k)
    EXTRA.clear()
    for h, k in con.execute("SELECT hanji, tkey FROM entry WHERE source = 'taihoa' AND kind = 'word' AND tailo != '' "
                            "AND tailo NOT LIKE '% %' AND length(hanji) BETWEEN 2 AND 4 ORDER BY freq DESC"):
        if h not in BEST:
            EXTRA.setdefault(h, k)


def is_han(s):
    return bool(s) and all(re.match(CJK, c) for c in s)


# ---- Mandarin glosses: pinyin + English for the Mandarin equivalents (CC-CEDICT, CC BY-SA 4.0)
def _py_marks(num):
    marks = {'a': 'āáǎà', 'e': 'ēéěè', 'i': 'īíǐì', 'o': 'ōóǒò', 'u': 'ūúǔù', 'ü': 'ǖǘǚǜ'}
    out = []
    for syl in num.replace('u:', 'ü').split():
        m = re.match(r'^([a-zü]+)([1-5])$', syl.lower())
        if not m:
            out.append(syl)
            continue
        base, t = m.group(1), int(m.group(2))
        if t == 5:
            out.append(base)
            continue
        idx = base.find('a') if 'a' in base else base.find('e') if 'e' in base else base.find('ou') if 'ou' in base \
            else max(base.rfind(v) for v in 'iouü')
        out.append(base[:idx] + marks[base[idx]][t - 1] + base[idx + 1:])
    return ' '.join(out)


def mandarin_gloss(word):
    e = CEDICT.get(word)
    if e:
        en = '; '.join(g for g in e['english'] if not g.startswith(('variant of', 'old variant', 'CL:')))[:90]
        return {'w': word, 'py': _py_marks(e['pinyin']), 'en': en}
    try:
        from pypinyin import pinyin, Style
        return {'w': word, 'py': ' '.join(x[0] for x in pinyin(word, style=Style.TONE)), 'en': ''}
    except ImportError:
        return {'w': word, 'py': '', 'en': ''}


def lookup(seg, k):
    """Dictionary card for one word (Hàn-jī segment + key)."""
    did = f'{seg}|{k}'
    if did in dictionary:
        return did
    rows = con.execute("""SELECT id, source, hanji, tailo, cognate, mandarin_best, hsk_old, hsk_new, freq_rank, wenbai, src_id
                          FROM entry WHERE tkey=? AND source IN ('moe','itaigi','taihoa','tgb') AND kind != 'xref'
                          ORDER BY (hanji=?) DESC, source='moe' DESC, freq DESC LIMIT 1""", (k, seg)).fetchall()
    card = {'hanji': seg, 'tkey': k}
    eid = dh = None
    if rows:
        eid, src, h, t, cog, mb, ho, hn, rank, wb, sid = rows[0]
        dh = h
        mand = [w for (w,) in con.execute('SELECT DISTINCT word FROM mandarin WHERE entry_id=? LIMIT 6', (eid,))]
        card.update(source=src, dict_hanji=h, tailo=t, cognate=cog, mandarin=mand, hsk=ho or hn, rank=rank,
                    mand=[mandarin_gloss(w) for w in mand[:4]], wenbai=wb)
        alts = VARIANTS.alts(seg, t, eid if src == 'moe' else None)
        if alts:
            card['alts'] = alts
        dia = VARIANTS.dialect_rows(seg, t)
        if dia:
            card['dialect'] = dia
        if src == 'moe':
            rid = sutian.word(SUTIAN, h, t)
            if rid:
                card['moe_id'] = rid
            card['senses'] = [{'pos': p, 'def': d} for p, d in con.execute(
                'SELECT pos, definition_zh FROM sense WHERE entry_id=? ORDER BY ord LIMIT 4', (eid,))]
            ex = con.execute("SELECT hanji, tailo, mandarin FROM example WHERE entry_id=? AND length(hanji)>3 "
                             "ORDER BY id LIMIT 1", (eid,)).fetchone()
            if ex:
                card['example'] = {'hanji': ex[0], 'tailo': ex[1], 'mandarin': ex[2]}
                leku = sutian.example(SUTIAN, ex[0])
                if leku:
                    card['example']['leku'] = leku
    else:
        syls = k.split('-')
        chars = UNIT_RE.findall(seg)
        card['parts'] = [lookup(c, s) for c, s in zip(chars, syls)] if len(syls) > 1 and len(chars) == len(syls) else []
    comp = compose(seg, k)
    if comp:
        card['comp'] = comp
    # last resort for the English: the pieces' English joined (the parts of a course compound, else its composition)
    parts = [(dictionary[p].get('gloss'), dictionary[p].get('gloss_src')) for p in card.get('parts') or comp or []]
    en, en_src = ENGLISH.gloss(seg, k, eid, dh, parts)
    if not en and len(seg) == 1:     # a character met only inside words: its own CC-CEDICT meaning
        en, en_src = english.cedict_en(CEDICT, seg), f'mandarin:{seg}'
    if en:
        card['gloss'] = en
        if en_src not in ('course', 'written'):
            card['gloss_src'] = en_src
    dictionary[did] = card
    return did


def compose(seg, k):
    """A word of two or more characters cut into the dictionary words it contains (never itself): fewest pieces, then
    the most frequent words (紅菜頭 -> 紅 + 菜頭, not 紅菜 + 頭; 勞動法 -> 勞動 + 法; 毋過 -> 毋 + 過). Card ids, or None
    when the word's characters and syllables do not line up."""
    chars, syls = UNIT_RE.findall(seg), k.split('-')
    n = len(chars)
    if n < 2 or n != len(syls) or not is_han(seg):
        return None
    best = [(0, 0, [])] + [None] * n          # per position: (pieces, -frequency, [(word, key)])
    for i in range(n):
        if best[i] is None:
            continue
        for m in range(1, min(n - i, MAX, n - 1) + 1):
            w, kk = ''.join(chars[i:i + m]), '-'.join(syls[i:i + m])
            if m > 1 and (w, kk) not in HEAD:
                continue
            c = (best[i][0] + 1, best[i][1] - (FREQ.get((w, kk), 0) if m > 1 else 0), best[i][2] + [(w, kk)])
            if best[i + m] is None or c[:2] < best[i + m][:2]:
                best[i + m] = c
    out = []
    for w, kk in best[n][2]:
        pid = lookup(w, kk)
        pc = dictionary[pid]
        if not pc.get('gloss') and len(pc.setdefault('in', [])) < 4 and f'{seg}|{k}' not in pc['in']:   # a bound character: the words it is in
            pc['in'].append(f'{seg}|{k}')
        out.append(pid)
    return out


def _alts(units, sylk, gaps, p, own):
    """Dictionary words starting at unit p (the line's own syllables give their reading), longest first."""
    out = []
    for m in range(MAX, 0, -1):
        if p + m > len(units) or any(gaps[p:p + m - 1]):
            continue
        w, kk = ''.join(units[p:p + m]), '-'.join(sylk[p:p + m])
        if not is_han(w) or not kk:
            continue
        if (w, kk) in HEAD or f'{w}|{kk}' == own:
            out.append(lookup(w, kk))
    return out if len(out) > 1 else None


def tokenize(hanji, tailo, groups=None, fallback=False):
    """Align a line into display tokens: {w: word} or {p: punctuation} items. The line is cut by its own Tâi-lô words
    (hyphens and spaces). If the Hàn-jī and Tâi-lô do not line up, the line stays one untappable token, or with
    `fallback`, it is cut by the dictionary instead (dict_tokens)."""
    ws = words(tailo)
    spoken = sandhi(groups or tailo, 'phrase')[0]
    spoken_ws = words(spoken)
    spans = list(UNIT_RE.finditer(hanji))
    nsyl = sum(len(k.split('-')) for _, k, _, _ in ws if k)
    if len(spans) != nsyl or len(spoken_ws) != len(ws):
        return dict_tokens(hanji, tailo) if fallback else [{'w': {'h': hanji, 't': tailo, 's': spoken, 'id': None}}]
    units = [m.group() for m in spans]
    gaps = [bool(hanji[spans[j].end():spans[j + 1].start()].strip()) for j in range(len(spans) - 1)] + [True]
    sylk = [s for _, k, _, _ in ws if k for s in k.split('-')]
    pos = 0
    si = 0
    out = []
    for (surf, k, neutral, _), (ssurf, _, _, _) in zip(ws, spoken_ws):
        if not k:
            continue
        n = len(k.split('-'))
        seg_spans = spans[si:si + n]
        p = si
        si += n
        start, end = seg_spans[0].start(), seg_spans[-1].end()
        if start > pos:
            out.append({'p': hanji[pos:start]})
        seg = hanji[start:end]
        prefix = '--' if neutral else ''
        is_cjk = bool(re.match(CJK, seg[:1]))
        w = {'h': seg, 't': prefix + surf, 's': prefix + ssurf, 'id': lookup(seg, k) if is_cjk else None}
        x = _alts(units, sylk, gaps, p, w['id']) if is_cjk else None
        if x:
            w['x'] = x
        out.append({'w': w})
        pos = end
    if pos < len(hanji):
        out.append({'p': hanji[pos:]})
    return out


def _toneless(t):
    t = re.sub(r'[\u0300-\u036f]', '', unicodedata.normalize('NFD', (t or '').lower()))
    return [x for x in re.split(r'[^a-z]+', t) if x]


def dict_tokens(text, tailo=None):
    """Cut a Hàn-jī text by the dictionary: MOE words, longest first, up to 5 characters, each with its usual MOE reading;
    where that leaves single characters, a taihoa word written as one word (霸道 pà-tō) whose reading is heard in the
    line's Tâi-lô (when given). For texts without a Tâi-lô that lines up (exam questions, songs, unsure transcript lines)."""
    chars = list(text)
    cut = []          # (start, length, key) of each dictionary word
    i = 0
    while i < len(chars):
        if not re.match(CJK, chars[i]):
            i += 1
            continue
        for n in range(MAX, 0, -1):
            w = ''.join(chars[i:i + n])
            if len(w) == n and is_han(w) and w in BEST:
                cut.append((i, n, BEST[w]))
                i += n
                break
        else:
            cut.append((i, 1, None))
            i += 1
    heard = ' %s ' % ' '.join(_toneless(tailo)) if tailo else None
    ones = {cut[j][0] for j in range(len(cut)) if cut[j][1] == 1}
    merged = {}
    for j, (s, n, k) in enumerate(cut):
        if n != 1 or s in merged:
            continue
        for m in range(4, 1, -1):
            w = ''.join(chars[s:s + m])
            if w in EXTRA and all(s + q in ones for q in range(m)) and (
                    heard is None or ' %s ' % ' '.join(_toneless(EXTRA[w].replace('-', ' '))) in heard):
                merged[s] = (m, EXTRA[w])
                for q in range(1, m):
                    merged[s + q] = None
                break
    words_ = []
    for s, n, k in cut:
        if s in merged:
            if merged[s] is None:
                continue
            n, k = merged[s]
        words_.append((s, n, k))
    out, pos = [], 0
    for s, n, k in words_:
        if s > pos:
            out.append({'p': ''.join(chars[pos:s])})
        h = ''.join(chars[s:s + n])
        if k:
            w = {'h': h, 'id': lookup(h, k)}
            x = []
            for m in range(n, 0, -1):     # never longer than the cut word: the app's longest match must cut the same
                sub = ''.join(chars[s:s + m])
                if len(sub) == m and is_han(sub) and (sub in BEST or sub in EXTRA):
                    x.append(lookup(sub, BEST.get(sub) or EXTRA[sub]))
            if len(x) > 1 and w['id'] in x:
                w['x'] = x
            out.append({'w': w})
        else:
            out.append({'p': h})
        pos = s + n
    if pos < len(chars):
        out.append({'p': ''.join(chars[pos:])})
    # untappable neighbours joined into one piece
    merged_out = []
    for t in out:
        if 'p' in t and merged_out and 'p' in merged_out[-1]:
            merged_out[-1]['p'] += t['p']
        else:
            merged_out.append(t)
    return merged_out

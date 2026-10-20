"""Build the reader app: course/ + database -> app/dist/index.html (one self-contained file).

  python3 tools/build_app.py
"""
import base64
from collections import Counter
import datetime
import glob
import io
import json
import os
import re
import sqlite3
import sys
import unicodedata

import markdown
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lint import UNIT_RE, CJK, words  # noqa: E402
from sandhi import sandhi  # noqa: E402
from tailo import key  # noqa: E402
from variants import Variants  # noqa: E402
import bridge  # noqa: E402
import english  # noqa: E402
import moe_examples  # noqa: E402
import sutian  # noqa: E402
import tone_drill  # noqa: E402
import podcast  # noqa: E402
MOE_EX = moe_examples.load()
# recording ids come from the ministry's own table (tools/sutian.py): the old entry numbers point to other words
SUTIAN = sutian.load()

ROOT = os.path.dirname(HERE)
con = sqlite3.connect(os.path.join(ROOT, 'data/build/taigi.db'))
VARIANTS = Variants(con)
dictionary = {}
glosses = {}  # tkey -> English gloss written for the course


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


CEDICT = english.load_cedict()
ENGLISH = None   # set once the course glosses are read (see '---- lessons')


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
    parts = [(dictionary[p].get('gloss'), dictionary[p].get('gloss_src')) for p in card.get('parts', [])]
    en, en_src = ENGLISH.gloss(seg, k, eid, dh, parts)
    if en:
        card['gloss'] = en
        if en_src not in ('course', 'written'):
            card['gloss_src'] = en_src
    dictionary[did] = card
    return did


def tokenize(hanji, tailo, groups):
    """Align a line into display tokens: {w: word} or {p: punctuation} items."""
    ws = words(tailo)
    spoken = sandhi(groups or tailo, 'phrase')[0]
    spoken_ws = words(spoken)
    spans = list(UNIT_RE.finditer(hanji))
    nsyl = sum(len(k.split('-')) for _, k, _, _ in ws if k)
    out = []
    if len(spans) != nsyl or len(spoken_ws) != len(ws):
        return [{'w': {'h': hanji, 't': tailo, 's': spoken, 'id': None}}]
    pos = 0
    si = 0
    for (surf, k, neutral, _), (ssurf, _, _, _) in zip(ws, spoken_ws):
        if not k:
            continue
        n = len(k.split('-'))
        seg_spans = spans[si:si + n]
        si += n
        start, end = seg_spans[0].start(), seg_spans[-1].end()
        if start > pos:
            out.append({'p': hanji[pos:start]})
        seg = hanji[start:end]
        prefix = '--' if neutral else ''
        is_cjk = bool(re.match(CJK, seg[:1]))
        out.append({'w': {'h': seg, 't': prefix + surf, 's': prefix + ssurf, 'id': lookup(seg, k) if is_cjk else None}})
        pos = end
    if pos < len(hanji):
        out.append({'p': hanji[pos:]})
    return out


def _in_big5(ch):
    try:
        ch.encode('cp950')
        return True
    except UnicodeEncodeError:
        return False


def tailo_font_css():
    """Noto Sans (OFL), subset to Latin + all combining marks, with its mark-positioning tables. The Google Fonts
    subsets leave out U+030D and U+0358 and the anchors for m̄ / n̄, so tone marks floated beside the letter."""
    p = os.path.join(ROOT, 'app/fonts/tailo-noto-sans.woff2')
    b64 = base64.b64encode(open(p, 'rb').read()).decode()
    return (f"@font-face{{font-family:'TailoSans';font-weight:400 800;font-display:swap;"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}")


def ext_font_css(text):
    """@font-face rules with only the glyphs of rare characters (not in Big5) used by the app, from Plangothic."""
    from fontTools import subset
    from fontTools.ttLib import TTFont
    rare = sorted({ch for ch in text if (0x3400 <= ord(ch) <= 0x9fff or ord(ch) >= 0x20000 or 0xf900 <= ord(ch) <= 0xfaff)
                   and not _in_big5(ch)})
    fdir = os.path.join(ROOT, 'data/raw/plangothic/package/fonts')
    chunks = {}
    for ch in rare:
        base = ord(ch) & ~0xff
        for plane in ('P1', 'P2'):
            p = os.path.join(fdir, f'Plangothic{plane}-400-{base:06x}.woff2')
            if os.path.exists(p):
                chunks.setdefault(p, []).append(ord(ch))
                break
    css = []
    for p, cps in chunks.items():
        font = TTFont(p)
        have = [c for c in cps if c in font.getBestCmap()]
        if not have:
            continue
        sub = subset.Subsetter(subset.Options(flavor='woff2', layout_features=[], name_IDs=['*']))
        sub.populate(unicodes=have)
        sub.subset(font)
        font.flavor = 'woff2'
        buf = io.BytesIO()
        font.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        rng = ','.join(f'U+{c:X}' for c in have)
        css.append(f"@font-face{{font-family:'TaigiExt';font-display:swap;src:url(data:font/woff2;base64,{b64}) "
                   f"format('woff2');unicode-range:{rng};}}")
    print(f'embedded {sum(len(c) for c in chunks.values())} rare characters in {len(css)} font chunks')
    return '\n'.join(css)


# ---- lessons
lesson_files = sorted(glob.glob(os.path.join(ROOT, 'course/lessons/[0-9]*.yaml')))
# Part 2 (進修, Perfectionnement): course/perfectionnement/NN.yaml with id N, stored in the app as 100 + N
perf_files = sorted(glob.glob(os.path.join(ROOT, 'course/perfectionnement/[0-9]*.yaml')))
theme_files = sorted(glob.glob(os.path.join(ROOT, 'course/themes/*.yaml')))
for f in lesson_files + perf_files:
    for w in yaml.safe_load(open(f, encoding='utf-8')).get('new_words', []) or []:
        if w.get('en'):
            glosses[key(w['tailo'])] = w['en']
for f in theme_files:
    for sec in yaml.safe_load(open(f, encoding='utf-8'))['sections']:
        for w in sec['words']:
            glosses.setdefault(key(w['tailo']), w.get('en'))
ENGLISH = english.English(con, {k: v for k, v in glosses.items() if v}, CEDICT)

lessons = []
for f in lesson_files + perf_files:
    d = yaml.safe_load(open(f, encoding='utf-8'))
    if f in perf_files:
        d['id'] = 100 + d['id']
    lines = []
    for ln in d['dialogue']:
        lines.append({'n': ln['n'], 'speaker': ln.get('speaker') or '', 'en': ln['en'], 'zh': ln.get('zh'),
                      'tailo': ln['tailo'], 'hanji': ln['hanji'],
                      'spoken': sandhi(ln.get('groups') or ln['tailo'], 'phrase')[0],
                      'tokens': tokenize(ln['hanji'], ln['tailo'], ln.get('groups'))})
    new_words = [{'tailo': w['tailo'], 'hanji': w['hanji'], 'en': w.get('en'), 'id': lookup(w['hanji'], key(w['tailo']))}
                 for w in d.get('new_words') or []]
    ex = [dict(it, kind=kind) for kind, items in (d.get('exercises') or {}).items() for it in items or []]
    lessons.append({'id': d['id'], 'title': d['title'], 'review': d.get('review', False), 'genre': d.get('genre', 'dialogue'),
                    'setting': d.get('setting', ''), 'lines': lines, 'notes': d.get('notes') or [],
                    'new_words': new_words, 'exercises': ex})

# ---- themes (thematic vocabulary)
themes = []
for f in theme_files:
    t = yaml.safe_load(open(f, encoding='utf-8'))
    secs = []
    for sec in t['sections']:
        ws = [dict(w, id=lookup(w['hanji'], key(w['tailo']))) for w in sec['words']]
        text = [{'en': x['en'], 'tailo': x['tailo'], 'hanji': x['hanji'],
                 'tokens': tokenize(x['hanji'], x['tailo'], x.get('groups'))} for x in sec.get('text', [])]
        secs.append({'n': sec['n'], 'title': sec['title'], 'words': ws, 'text': text})
    themes.append({'id': t['id'], 'title': t['title'], 'intro': t.get('intro', ''), 'sections': secs,
                   'notes': t.get('notes') or []})

# ---- accents page: a few characters that show the main regional splits
ACCENT_SETS = [
    ('e / ue', 'Taipei and Lukang say -ue where Tainan and Yilan say -e (and the reverse for some words).',
     [('雞', 'chicken'), ('火', 'fire'), ('鞋', 'shoe'), ('糜', 'rice porridge')]),
    ('i / u / ir', 'One vowel, three pronunciations: -i in the south, -u in Taipei, -ir (a central vowel) in Lukang and Kinmen.',
     [('豬', 'pig'), ('魚', 'fish'), ('箸', 'chopsticks')]),
    ('enn / inn', 'Nasal -enn in the south and Yilan, -inn in the north.',
     [('生', 'raw; be born'), ('青', 'green')]),
    ('eh / ueh / erh', 'The “want” word 欲 changes vowel across the island.',
     [('欲', 'want to')]),
    ('pronouns', '阮 “we / I” is guán in the south and gún in the north; many speakers use both.',
     [('阮', 'we (not you)')]),
]
accents = []
for name, expl, chars in ACCENT_SETS:
    rows = []
    for ch, en in chars:
        r = con.execute("SELECT tailo FROM entry WHERE source='moe' AND hanji=? AND kind='word' AND tailo!='' "
                        "ORDER BY (wenbai='colloquial') DESC, freq DESC LIMIT 1", (ch,)).fetchone()
        if not r:
            continue
        dia = VARIANTS.dialect_rows(ch, r[0])
        if dia:
            rows.append({'char': ch, 'en': en, 'std': r[0], 'places': dia[0]['places']})
    if rows:
        accents.append({'name': name, 'expl': expl, 'rows': rows})

lesson0 = markdown.markdown(open(os.path.join(ROOT, 'course/lessons/000-reading-tailo.md'), encoding='utf-8').read(),
                            extensions=['tables', 'fenced_code'])
syllabus = yaml.safe_load(open(os.path.join(ROOT, 'course/syllabus.yaml'), encoding='utf-8'))['lessons']
# ---- audio: MOE recordings of the headwords. tools/fetch_audio.py puts them in app/dist/audio/w/<MOE id>.mp3
# (run by the GitHub workflow; the MOE site cannot be reached from everywhere). Cards get a ▶ only if the file is there.
AUDIO = os.path.join(ROOT, 'app/dist/audio/w')
os.makedirs(os.path.join(ROOT, 'app/dist'), exist_ok=True)
# Words with no recording of their own (cards from iTaigi / 台華, MOE words the ministry's table doesn't match, words
# the course builds itself). 1) The ministry recorded the same Hàn-jī with the same reading: that is the word's own
# recording, used everywhere. 2) Otherwise the word is cut into the fewest recorded pieces (sub-words, then single
# syllables with the same reading), played one after the other by the line player (`moe_seq`).
REC_KEY = {}
for _hk, _sid in ((SUTIAN or {}).get('w') or {}).items():
    _h, _, _t = _hk.partition('|')
    REC_KEY.setdefault(f'{_h}|{key(_t)}', _sid)


def rec_id(h, k):
    if not k:
        return None
    h = sutian._h(h)
    return REC_KEY.get(f'{h}|{k}') or (REC_KEY.get(f"{h.replace('台', '臺')}|{k}") if '台' in h else None)


def rec_pieces(seg, k):
    """[(id or None, syllables)] covering the word: most syllables recorded first, then fewest pieces."""
    chars, syls = UNIT_RE.findall(seg), k.split('-')
    if len(chars) != len(syls):
        return []
    n = len(syls)
    best = [(0, 0, [])] + [None] * n            # (unrecorded syllables, pieces, plan) for the first i syllables
    for i in range(n):
        if best[i] is None:
            continue
        miss, cnt, plan = best[i]
        for j in range(i + 1, min(n, i + 4) + 1):
            rid = rec_id(''.join(chars[i:j]), '-'.join(syls[i:j]))
            if rid is None and j > i + 1:
                continue
            cand = (miss + (0 if rid else 1), cnt + 1, plan + [(rid, j - i)])
            if best[j] is None or cand[:2] < best[j][:2]:
                best[j] = cand
    return best[n][2]


n_same = n_seq = 0
for c in dictionary.values():
    if c.get('moe_id') or not c.get('tkey'):
        continue
    rid = rec_id(c['hanji'], c['tkey'])
    if rid:
        c['moe_id'] = rid
        n_same += 1
        continue
    plan = rec_pieces(c['hanji'], c['tkey'])
    if any(r for r, _ in plan):
        c['moe_seq'] = [r for r, _ in plan if r]
        c['seq_full'] = all(r for r, _ in plan)
        n_seq += 1
need = sorted({c['moe_id'] for c in dictionary.values() if c.get('moe_id')}
              | {r for c in dictionary.values() for r in c.get('moe_seq', [])}, key=int)
open(os.path.join(ROOT, 'app/dist/audio-needed.txt'), 'w').write('\n'.join(need) + '\n')
need_ex = sorted({c['example']['leku'] for c in dictionary.values() if c.get('example', {}).get('leku')})
open(os.path.join(ROOT, 'app/dist/audio-needed-examples.txt'), 'w').write('\n'.join(need_ex) + '\n')
have_ex = 0
for c in dictionary.values():
    lk = c.get('example', {}).get('leku')
    if lk and os.path.exists(os.path.join(ROOT, 'app/dist/audio/s', lk + '.mp3')):
        c['example']['audio'] = f'audio/s/{lk}.mp3'
        have_ex += 1
have = 0
for c in dictionary.values():
    if c.get('moe_id') and os.path.exists(os.path.join(AUDIO, c['moe_id'] + '.mp3')):
        c['audio'] = f"audio/w/{c['moe_id']}.mp3"
        have += 1
for c in dictionary.values():
    seq = [f'audio/w/{r}.mp3' for r in c.pop('moe_seq', []) if os.path.exists(os.path.join(AUDIO, r + '.mp3'))]
    full = c.pop('seq_full', False)
    if seq and not c.get('audio'):
        c['audio_seq'] = seq
        if not full:
            c['seq_part'] = True     # some syllables have no recording at all
# ---- report: every word a dialogue line plays (or skips) without a recording of its own
#      app/dist/audio-missing.txt: cause, Hàn-jī, Tâi-lô, times used, lessons (P1 = 進修 1)
_miss = {}


def _lid(L):
    return f"P{L['id'] - 100}" if L['id'] > 100 else str(L['id'])


_tok_total = 0
for L in lessons:
    for ln in L['lines']:
        for t in ln['tokens']:
            w = t.get('w')
            if not w:
                continue
            _tok_total += 1
            c = dictionary.get(w['id']) if w.get('id') else None
            if c and c.get('audio'):
                continue
            if not w.get('id'):
                cause = 'line not split into words' if len(ln['tokens']) == 1 else 'no card'
            elif c.get('audio_seq'):
                cause = 'pieces (some syllables silent)' if c.get('seq_part') else 'pieces'
            elif c.get('moe_id') or c.get('moe_seq'):
                cause = 'recording not downloaded'
            elif c.get('source') == 'moe':
                cause = 'MOE word, no id in the ministry table'
            elif c.get('source'):
                cause = f"{c['source']} word, not recorded by MOE"
            else:
                cause = 'course compound, not recorded by MOE'
            k = (cause, w['h'], w['t'])
            e = _miss.setdefault(k, [0, []])
            e[0] += 1
            if _lid(L) not in e[1]:
                e[1].append(_lid(L))
_by_cause = Counter()
for (cause, _, _), (cnt, _) in _miss.items():
    _by_cause[cause] += cnt
with open(os.path.join(ROOT, 'app/dist/audio-missing.txt'), 'w', encoding='utf-8') as f:
    f.write('# words played by a dialogue ▶ without their own recording (cause, Hàn-jī, Tâi-lô, uses, lessons)\n')
    for (cause, h, tl), (cnt, ls) in sorted(_miss.items(), key=lambda x: (x[0][0], -x[1][0])):
        f.write(f"{cause}\t{h}\t{tl}\t{cnt}\t{','.join(ls[:6])}{f' +{len(ls) - 6}' if len(ls) > 6 else ''}\n")
print(f'line audio: {_tok_total} word tokens; own recording found for {n_same} non-MOE cards, pieces for {n_seq}; '
      f'without own recording: ' + ', '.join(f'{k} {v}' for k, v in _by_cause.most_common()))
if os.environ.get('GITHUB_ACTIONS') and have:
    print(f'::notice title=Line audio::{_tok_total} word tokens in lessons; {sum(_by_cause.values())} without their own '
          f'recording: ' + ' | '.join(f'{k} {v}' for k, v in _by_cause.most_common()))
    for cause, _ in _by_cause.most_common(6):
        top = sorted(((cnt, h, tl, ls) for (c_, h, tl), (cnt, ls) in _miss.items() if c_ == cause), reverse=True)[:25]
        print(f'::notice title=No recording: {cause}::' + ' · '.join(f'{h} {tl} ×{cnt} ({ls[0]})' for cnt, h, tl, ls in top))
# ---- grammar sheets: every course line that uses each structure (course/grammar.yaml)
grammar = yaml.safe_load(open(os.path.join(ROOT, 'course/grammar.yaml'), encoding='utf-8'))['groups']
for g in grammar:
    for it in g['items']:
        rh = re.compile(it['han']) if it.get('han') else None
        rt = re.compile(it['tl']) if it.get('tl') else None
        refs = []
        for L in lessons:
            for i, ln in enumerate(L['lines']):
                if (rh and rh.search(ln['hanji'])) or (rt and rt.search(ln['tailo'].lower())):
                    refs.append([L['id'], i])
        it['refs'] = refs
        it.pop('han', None); it.pop('tl', None)
# ---- podcast (data/raw/podcast/feed.xml, fetched by tools/fetch_podcast.py): episode notes + vocabulary linked to cards
show = podcast.load()
if show:
    for ep in show['episodes']:
        for v in ep['vocab']:
            if v['h'] and v['t']:
                k = key(v['t'])
                if con.execute("SELECT 1 FROM entry WHERE tkey=? AND source IN ('moe','itaigi','taihoa','tgb') LIMIT 1", (k,)).fetchone():
                    v['id'] = lookup(v['h'], k)
# ---- video (course/video.yaml): shows on their broadcaster's own YouTube channel; ids and titles only
VIDEO = os.path.join(ROOT, 'course/video.yaml')
video = yaml.safe_load(open(VIDEO, encoding='utf-8')) if os.path.exists(VIDEO) else {'shows': []}
data = {'podcast': show, 'video': video, 'tones': tone_drill.build(lessons), 'grammar': grammar, 'syllabus': syllabus, 'lessons': lessons, 'themes': themes, 'accents': accents, 'bridge': bridge.build(con, 160),
        'dict': dictionary, 'lesson0': lesson0, 'built': datetime.date.today().isoformat()}

# ---- native-speaker recordings of the dialogues: course/audio/lessons/L057-03.mp3 (tools/import_recordings.py)
REC = os.path.join(ROOT, 'course/audio/lessons')
REC_META = os.path.join(ROOT, 'course/audio/recordings.yaml')
rec_meta = yaml.safe_load(open(REC_META, encoding='utf-8')) if os.path.exists(REC_META) else {}
n_rec = 0
for L in lessons:
    for ln in L['lines']:
        cid = f"L{L['id']:03d}-{ln['n']:02d}"
        if os.path.exists(os.path.join(REC, cid + '.mp3')):
            ln['audio'] = f'audio/lessons/{cid}.mp3'
            sp = rec_meta.get('voice') or (rec_meta.get('clips') or {}).get(cid, {}).get('speaker')
            if sp:
                ln['voice'] = sp
            n_rec += 1
data['recorded'] = n_rec
tpl = open(os.path.join(ROOT, 'app/index.template.html'), encoding='utf-8').read()
tpl = tpl.replace('/*__FONTS__*/', tailo_font_css() + '\n' + ext_font_css(json.dumps(data, ensure_ascii=False)))
payload = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
os.makedirs(os.path.join(ROOT, 'app/dist'), exist_ok=True)
out = os.path.join(ROOT, 'app/dist/index.html')
open(out, 'w', encoding='utf-8').write(unicodedata.normalize('NFC', tpl.replace('/*__DATA__*/null', payload)))
# recording page for native speakers (app/dist/record.html): the dialogue lines only
rtpl = open(os.path.join(ROOT, 'app/record.template.html'), encoding='utf-8').read()
rdata = {'voice': rec_meta.get('voice', 'native speaker'), 'lessons': [{'id': L['id'], 'title': L['title'], 'lines': [{k: ln[k] for k in ('n', 'speaker', 'hanji', 'tailo', 'en')} for ln in L['lines']]} for L in lessons]}
rjson = json.dumps(rdata, ensure_ascii=False)
rtpl = rtpl.replace('/*__FONTS__*/', tailo_font_css() + '\n' + ext_font_css(rjson)).replace('/*__DATA__*/null', rjson.replace('</', '<\\/'))
open(os.path.join(ROOT, 'app/dist/record.html'), 'w', encoding='utf-8').write(unicodedata.normalize('NFC', rtpl))
_src = Counter((c.get('gloss_src') or ('written/course' if c.get('gloss') else 'none')).split(':')[0] for c in dictionary.values())
print('English on word cards:', ', '.join(f'{k} {v}' for k, v in _src.most_common()))
open(os.path.join(ROOT, 'app/dist/english-auto.txt'), 'w', encoding='utf-8').write(''.join(
    f"{c['hanji']}\t{c.get('tailo') or c['tkey']}\t{c.get('gloss_src') or 'none'}\t{c.get('gloss') or ''}\n"
    for c in dictionary.values() if c.get('gloss_src') or not c.get('gloss')))
print(out, f'{len(lessons)} lessons, {len(dictionary)} dictionary cards, {have}/{len(need)} with audio, {have_ex}/{len(need_ex)} examples with audio, {n_rec} recorded lines, {len(show['episodes']) if show else 0} podcast episodes, {os.path.getsize(out) // 1024} KB')

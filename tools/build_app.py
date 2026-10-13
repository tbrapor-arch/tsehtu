"""Build the reader app: course/ + database -> app/dist/index.html (one self-contained file).

  python3 tools/build_app.py
"""
import base64
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
import moe_examples  # noqa: E402
import tone_drill  # noqa: E402
MOE_EX = moe_examples.load()

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


CEDICT = {}
_ced = os.path.join(ROOT, 'data/raw/cedict/package/cedict.json')
if os.path.exists(_ced):
    for e in json.load(open(_ced, encoding='utf-8')):
        if e['pinyin'][:1].isupper():      # proper names: keep only if nothing else
            CEDICT.setdefault(e['traditional'], e)
        elif e['traditional'] not in CEDICT or CEDICT[e['traditional']]['pinyin'][:1].isupper():
            CEDICT[e['traditional']] = e


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
    card = {'hanji': seg, 'tkey': k, 'gloss': glosses.get(k)}
    if rows:
        eid, src, h, t, cog, mb, ho, hn, rank, wb, sid = rows[0]
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
            card['moe_id'] = sid
            card['senses'] = [{'pos': p, 'def': d} for p, d in con.execute(
                'SELECT pos, definition_zh FROM sense WHERE entry_id=? ORDER BY ord LIMIT 4', (eid,))]
            ex = con.execute("SELECT hanji, tailo, mandarin FROM example WHERE entry_id=? AND length(hanji)>3 "
                             "ORDER BY id LIMIT 1", (eid,)).fetchone()
            if ex:
                card['example'] = {'hanji': ex[0], 'tailo': ex[1], 'mandarin': ex[2]}
                where = moe_examples.find(MOE_EX, sid, ex[0])
                if where:
                    card['example']['leku'] = f'{sid}-{where[0]}-{where[1]}'
    else:
        syls = k.split('-')
        chars = UNIT_RE.findall(seg)
        card['parts'] = [lookup(c, s) for c, s in zip(chars, syls)] if len(syls) > 1 and len(chars) == len(syls) else []
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
theme_files = sorted(glob.glob(os.path.join(ROOT, 'course/themes/*.yaml')))
for f in lesson_files:
    for w in yaml.safe_load(open(f, encoding='utf-8')).get('new_words', []) or []:
        if w.get('en'):
            glosses[key(w['tailo'])] = w['en']
for f in theme_files:
    for sec in yaml.safe_load(open(f, encoding='utf-8'))['sections']:
        for w in sec['words']:
            glosses.setdefault(key(w['tailo']), w.get('en'))

lessons = []
for f in lesson_files:
    d = yaml.safe_load(open(f, encoding='utf-8'))
    lines = []
    for ln in d['dialogue']:
        lines.append({'n': ln['n'], 'speaker': ln['speaker'], 'en': ln['en'], 'zh': ln.get('zh'),
                      'tailo': ln['tailo'], 'hanji': ln['hanji'],
                      'spoken': sandhi(ln.get('groups') or ln['tailo'], 'phrase')[0],
                      'tokens': tokenize(ln['hanji'], ln['tailo'], ln.get('groups'))})
    new_words = [{'tailo': w['tailo'], 'hanji': w['hanji'], 'en': w.get('en'), 'id': lookup(w['hanji'], key(w['tailo']))}
                 for w in d.get('new_words') or []]
    ex = [dict(it, kind=kind) for kind, items in (d.get('exercises') or {}).items() for it in items or []]
    lessons.append({'id': d['id'], 'title': d['title'], 'phase': d['phase'], 'review': d.get('review', False),
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
need = sorted({c['moe_id'] for c in dictionary.values() if c.get('moe_id')}, key=int)
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
data = {'tones': tone_drill.build(lessons), 'grammar': grammar, 'syllabus': syllabus, 'lessons': lessons, 'themes': themes, 'accents': accents, 'bridge': bridge.build(con, 160),
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
tpl = tpl.replace('/*__FONTS__*/', ext_font_css(json.dumps(data, ensure_ascii=False)))
payload = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
os.makedirs(os.path.join(ROOT, 'app/dist'), exist_ok=True)
out = os.path.join(ROOT, 'app/dist/index.html')
open(out, 'w', encoding='utf-8').write(unicodedata.normalize('NFC', tpl.replace('/*__DATA__*/null', payload)))
# recording page for native speakers (app/dist/record.html): the dialogue lines only
rtpl = open(os.path.join(ROOT, 'app/record.template.html'), encoding='utf-8').read()
rdata = {'voice': rec_meta.get('voice', 'native speaker'), 'lessons': [{'id': L['id'], 'title': L['title'], 'lines': [{k: ln[k] for k in ('n', 'speaker', 'hanji', 'tailo', 'en')} for ln in L['lines']]} for L in lessons]}
rjson = json.dumps(rdata, ensure_ascii=False)
rtpl = rtpl.replace('/*__FONTS__*/', ext_font_css(rjson)).replace('/*__DATA__*/null', rjson.replace('</', '<\\/'))
open(os.path.join(ROOT, 'app/dist/record.html'), 'w', encoding='utf-8').write(unicodedata.normalize('NFC', rtpl))
print(out, f'{len(lessons)} lessons, {len(dictionary)} dictionary cards, {have}/{len(need)} with audio, {have_ex}/{len(need_ex)} examples with audio, {n_rec} recorded lines, {os.path.getsize(out) // 1024} KB')

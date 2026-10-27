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
from lint import UNIT_RE  # noqa: E402
from sandhi import sandhi  # noqa: E402
from tailo import key  # noqa: E402
from variants import Variants  # noqa: E402
import bridge  # noqa: E402
import cards  # noqa: E402
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
glosses = {}  # tkey -> English gloss written for the course


# ---- word cards and line segmentation: tools/cards.py (shared with the private module's build)
CEDICT = english.load_cedict()
cards.init(con, None, CEDICT, SUTIAN)   # English is set once the course glosses are read (see '---- lessons')
dictionary = cards.dictionary
lookup, tokenize, mandarin_gloss = cards.lookup, cards.tokenize, cards.mandarin_gloss


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
ENGLISH = cards.ENGLISH = english.English(con, {k: v for k, v in glosses.items() if v}, CEDICT)

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
SOUND = {}                       # reading -> a recording of exactly that sound (main reading of its entry only)
_seen = set()
for _hk, _sid in ((SUTIAN or {}).get('w') or {}).items():
    _h, _, _t = _hk.partition('|')
    _k = key(_t)
    REC_KEY.setdefault(f'{_h}|{_k}', _sid)
    if _sid not in _seen and _k:   # 'ē/uē': only the first reading is the one recorded in <id>.mp3
        SOUND.setdefault(_k, _sid)
    _seen.add(_sid)


def rec_id(h, k):
    if not k:
        return None
    h = sutian._h(h)
    return REC_KEY.get(f'{h}|{k}') or (REC_KEY.get(f"{h.replace('台', '臺')}|{k}") if '台' in h else None)


def rec_pieces(seg, k):
    """[(id or None, syllables, by_sound)] covering the word. Pieces are recordings of the same Hàn-jī with the same
    reading, or, failing that, any recording with exactly the same sound (a homophone: identical in citation form).
    Most syllables recorded first, then fewest pieces, then fewest homophones. `seg` None: romanised text, sound only."""
    syls = k.split('-')
    chars = UNIT_RE.findall(seg) if seg else None
    if chars is not None and len(chars) != len(syls):
        chars = None
    n = len(syls)
    best = [(0, 0, 0, [])] + [None] * n
    for i in range(n):
        if best[i] is None:
            continue
        miss, cnt, snd, plan = best[i]
        for j in range(i + 1, min(n, i + 4) + 1):
            kk = '-'.join(syls[i:j])
            rid = rec_id(''.join(chars[i:j]), kk) if chars else None
            by_sound = False
            if rid is None:
                rid, by_sound = SOUND.get(kk), True
            if rid is None and j > i + 1:
                continue
            cand = (miss + (0 if rid else 1), cnt + 1, snd + (1 if rid and by_sound else 0),
                    plan + [(rid, j - i, rid is not None and by_sound)])
            if best[j] is None or cand[:3] < best[j][:3]:
                best[j] = cand
    return best[n][3]


n_same = n_seq = n_tok = 0
for c in dictionary.values():
    if c.get('moe_id') or not c.get('tkey'):
        continue
    rid = rec_id(c['hanji'], c['tkey'])
    if rid:
        c['moe_id'] = rid
        n_same += 1
        continue
    plan = rec_pieces(c['hanji'], c['tkey'])
    if any(r for r, _, _ in plan):
        c['moe_seq'] = [r for r, _, _ in plan if r]
        c['seq_full'] = all(r for r, _, _ in plan)
        c['seq_sound'] = any(b for _, _, b in plan)
        n_seq += 1
# romanised words inside a Hàn-jī line (the sounds a dialogue talks about: ke / kue, ti / tu, káu / kàu / kâu…):
# no card, so the token itself carries the recordings of that exact sound (w['as'])
for L in lessons:
    for ln in L['lines']:
        if len(ln['tokens']) == 1:
            continue
        for t in ln['tokens']:
            w = t.get('w')
            if w and not w.get('id') and key(w['t']):
                plan = rec_pieces(None, key(w['t']))
                if any(r for r, _, _ in plan):
                    w['as_ids'] = [r for r, _, _ in plan if r]
                    w['as_full'] = all(r for r, _, _ in plan)
                    n_tok += 1
need = sorted({c['moe_id'] for c in dictionary.values() if c.get('moe_id')}
              | {r for c in dictionary.values() for r in c.get('moe_seq', [])}
              | {r for L in lessons for ln in L['lines'] for t in ln['tokens'] for r in (t.get('w') or {}).get('as_ids', [])},
              key=int)
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
    sound = c.pop('seq_sound', False)
    if seq and not c.get('audio'):
        c['audio_seq'] = seq
        if not full:
            c['seq_part'] = True     # some syllables have no recording at all
        if sound:
            c['seq_sound'] = True    # some pieces are homophones (same sound, other characters)
for L in lessons:
    for ln in L['lines']:
        for t in ln['tokens']:
            w = t.get('w')
            if w and 'as_ids' in w:
                ids, full = w.pop('as_ids'), w.pop('as_full')
                seq = [f'audio/w/{r}.mp3' for r in ids if os.path.exists(os.path.join(AUDIO, r + '.mp3'))]
                if seq:
                    w['as'] = seq
                    if not full:
                        w['as_part'] = True
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
                cause = ('line not split into words' if len(ln['tokens']) == 1 else
                         'romanised, same sound (some syllables silent)' if w.get('as_part') else
                         'romanised, same sound' if w.get('as') else 'no card, no recording of that sound')
            elif c.get('audio_seq'):
                cause = ('pieces (some syllables silent)' if c.get('seq_part') else
                         'pieces, some by same sound' if c.get('seq_sound') else 'pieces')
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
print(f'line audio: {_tok_total} word tokens; own recording found for {n_same} non-MOE cards, pieces for {n_seq} cards '
      f'and {n_tok} romanised words; '
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
# ---- music (course/music.yaml): songs on the artist's own YouTube channel; ids and titles only (lyrics are private)
MUSIC = os.path.join(ROOT, 'course/music.yaml')
music = yaml.safe_load(open(MUSIC, encoding='utf-8')) if os.path.exists(MUSIC) else {'albums': []}
data = {'podcast': show, 'video': video, 'music': music, 'tones': tone_drill.build(lessons), 'grammar': grammar, 'syllabus': syllabus, 'lessons': lessons, 'themes': themes, 'accents': accents, 'bridge': bridge.build(con, 160),
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

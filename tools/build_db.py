"""Build taigi.db: a Taiwanese (Tâi-lô) – Mandarin – English learner database.

Run: python3 -I build_db.py <data/raw dir> <out.db>
Non-commercial sources (Maryknoll, Embree English glosses) are only included when TAIGI_INCLUDE_NC=1.
"""
import csv
import glob
import json
import os
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tailo import key, toneless  # noqa: E402

ROOT, OUT = sys.argv[1], sys.argv[2]
INCLUDE_NC = os.environ.get('TAIGI_INCLUDE_NC') == '1'
MOE = os.path.join(ROOT, 'moedict-data-twblg/uni')
CHH = os.path.join(ROOT, 'ChhoeTaigiDatabase/ChhoeTaigiDatabase')

SOURCES = [
    # id, name, year, license, commercial_ok, note
    ('moe', '教育部臺灣台語常用詞辭典 (MOE Dictionary of Frequently-Used Taiwanese Taigi)', '2011+',
     'CC BY-ND 3.0 TW', 1, 'Official Tâi-lô reference. ND: quote verbatim with attribution, do not alter entries.'),
    ('itaigi', 'iTaigi 華台對照典', '2016+', 'CC0', 1, 'Crowd-sourced Mandarin→Taigi; good for modern words.'),
    ('taihoa', '台華線頂對照典 (Iûⁿ Ún-giân)', '2002+', 'CC BY-SA 4.0', 1, 'Large Taigi→Mandarin glossary.'),
    ('tgb', '台灣白話基礎語句 (1956)', '1956', 'CC BY-SA 4.0', 1,
     'Basic sentences with Mandarin + English. Old-fashioned in places.'),
    ('maryknoll', 'Maryknoll 台英辭典 (1976)', '1976', 'CC BY-NC-SA 3.0 TW', 0, 'English glosses. Non-commercial only.'),
    ('embree', 'Embree 台英辭典 (1973)', '1973', 'CC BY-NC-SA 3.0 TW', 0, 'English glosses. Non-commercial only.'),
    ('kip2009', '教育部臺灣閩南語字詞頻調查 corpus (2009)', '2009', 'no licence stated', 1,
     'Read at build time only to compute word counts; no text is stored or redistributed.'),
    ('hsk', 'complete-hsk-vocabulary (drkameleon)', '2024', 'MIT', 1, 'HSK levels for Mandarin equivalents.'),
]

POS = {r['詞性代號']: r['正確'] for r in csv.DictReader(open(os.path.join(MOE, '釋義.詞性對照.csv')))}
WENBAI = {'0': None, '1': 'literary', '2': 'colloquial', '3': 'vulgar/common', '4': 'substitute-char'}
ENTRY_TYPE = {'1': 'word', '2': 'word', '3': 'word', '5': 'proverb'}


def nfc(s):
    return unicodedata.normalize('NFC', s or '').strip()


def split_alts(s):
    return [x.strip() for x in re.split(r'[/、]', s or '') if x.strip()]


def strip_paren(s):
    return re.sub(r'\(.*?\)|（.*?）', '', s or '').strip()


def mandarin_list(s):
    s = nfc(s)
    return [x for x in (strip_paren(p) for p in re.split(r'[、,，;；/]', s)) if x]


db_path = OUT
if os.path.exists(db_path):
    os.remove(db_path)
con = sqlite3.connect(db_path)
con.executescript(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')).read())
con.executemany('INSERT INTO source VALUES (?,?,?,?,?,?)', SOURCES)

# ---------------------------------------------------------------- MOE
entries = {}
for r in csv.DictReader(open(os.path.join(MOE, '詞目總檔.csv'))):
    eid = int(r['主編碼'])
    hanji, tailo = nfc(r['詞目']), nfc(r['音讀'])
    first = tailo.split('/')[0].strip()
    con.execute('INSERT INTO entry(id,source,src_id,hanji,tailo,tailo_alt,tkey,toneless,kind,wenbai,moe_type) '
                'VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                (eid, 'moe', str(eid), hanji, first, tailo if '/' in tailo else None, key(first),
                 toneless(key(first)), ENTRY_TYPE.get(r['屬性'], 'other'), WENBAI.get(r['文白屬性']), int(r['屬性'])))
    entries[eid] = (hanji, first)
next_id = max(entries) + 1

for r in csv.DictReader(open(os.path.join(MOE, '釋義.csv'))):
    con.execute('INSERT INTO sense(id,entry_id,ord,pos,definition_zh) VALUES (?,?,?,?,?)',
                (int(r['釋義總序號']), int(r['主編碼']), int(r['釋義順序']), POS.get(r['詞性代號']), nfc(r['釋義'])))

for r in csv.DictReader(open(os.path.join(MOE, '例句.csv'))):
    hz, tl, md = nfc(r['例句']), nfc(r['例句標音']), nfc(r['華語翻譯'])
    con.execute('INSERT INTO example(entry_id,sense_id,source,hanji,tailo,mandarin,english) VALUES (?,?,?,?,?,?,NULL)',
                (int(r['主編碼']), None, 'moe', hz, tl, md))

for r in csv.DictReader(open(os.path.join(MOE, '又音.csv'))):
    kinds = {'1': 'also read', '2': 'colloquially read', '3': 'contracted'}
    for alt in split_alts(r['又音']):
        con.execute('INSERT INTO variant(entry_id,tailo,tkey,kind) VALUES (?,?,?,?)',
                    (int(r['主編碼']), nfc(alt), key(alt), kinds.get(r['又音類型(1.又唸作 2.俗唸作 3.合音唸作)'])))

for fn, rel in (('近義詞對應.csv', 'synonym'), ('反義詞對應.csv', 'antonym')):
    col = '近義詞對應' if rel == 'synonym' else '反義詞對應'
    for r in csv.DictReader(open(os.path.join(MOE, fn))):
        try:
            con.execute('INSERT INTO relation(entry_id,other_id,rel) VALUES (?,?,?)', (int(r['主編碼']), int(r[col]), rel))
        except ValueError:
            pass

# dialect variation (pronunciation) by place
for r in csv.DictReader(open(os.path.join(MOE, '語音方言差.csv'))):
    for place in ('鹿港', '三峽', '臺北', '宜蘭', '臺南', '高雄', '金門', '馬公', '新竹', '臺中'):
        con.execute('INSERT INTO dialect(hanji,place,tailo,kind) VALUES (?,?,?,?)',
                    (nfc(r['字目']), place, nfc(r[place]), 'pronunciation'))
for r in csv.DictReader(open(os.path.join(MOE, '詞彙方言差.csv'))):
    for place in ('鹿港', '三峽', '臺北', '宜蘭', '臺南', '高雄', '金門', '馬公', '新竹', '臺中'):
        con.execute('INSERT INTO dialect(hanji,place,tailo,kind) VALUES (?,?,?,?)',
                    (nfc(r['詞目']), place, nfc(r[place]), 'lexical'))

# ---- MOE Mandarin equivalents (對應華語) come via ChhoeTaigi's copy of the MOE dictionary
by_hk = defaultdict(list)
by_h = defaultdict(list)
for eid, (h, t) in entries.items():
    by_hk[(h, key(t))].append(eid)
    by_h[h].append(eid)
matched = 0
chh_by_h = defaultdict(list)
for r in csv.DictReader(open(os.path.join(CHH, 'ChhoeTaigi_KauiokpooTaigiSutian.csv'), encoding='utf-8-sig')):
    h = nfc(r['HanLoTaibunKip'])
    k = key(r['KipUnicode'])
    chh_by_h[h].append(r)
    # fill readings missing from the moedict export (mostly 屬性=3 entries)
    for eid in by_h.get(h, []):
        if not entries[eid][1] and k:
            t = nfc(strip_paren(r['KipUnicode']))
            con.execute('UPDATE entry SET tailo=?, tkey=?, toneless=? WHERE id=?', (t, k, toneless(k), eid))
            entries[eid] = (h, t)
            by_hk[(h, k)].append(eid)
    ids = by_hk.get((h, k)) or (by_h.get(h) if len(by_h.get(h, [])) == 1 else None)
    if not ids:
        continue
    matched += 1
    for m in mandarin_list(r['HoaBun']):
        for eid in ids:
            con.execute('INSERT INTO mandarin(entry_id,word,source) VALUES (?,?,?)', (eid, m, 'moe'))
con.execute("UPDATE entry SET kind='xref' WHERE source='moe' AND tailo=''")  # synonym/dialect cross-refs without reading
print('MOE entries', len(entries), 'with Mandarin equivalents matched', matched)


# ---------------------------------------------------------------- other dictionaries
def add_entry(source, src_id, hanji, tailo, mand=(), english=None, kind='word'):
    global next_id
    tailo = nfc(strip_paren(tailo))
    if not tailo:
        return None
    first = split_alts(tailo)[0] if '/' in tailo else tailo
    eid = next_id
    next_id += 1
    con.execute('INSERT INTO entry(id,source,src_id,hanji,tailo,tailo_alt,tkey,toneless,kind,english) '
                'VALUES (?,?,?,?,?,?,?,?,?,?)',
                (eid, source, str(src_id), nfc(hanji) or None, first, tailo if tailo != first else None,
                 key(first), toneless(key(first)), kind, english))
    for m in mand:
        con.execute('INSERT INTO mandarin(entry_id,word,source) VALUES (?,?,?)', (eid, m, source))
    return eid


def rows(fn):
    return csv.DictReader(open(os.path.join(CHH, fn), encoding='utf-8-sig'))


for r in rows('ChhoeTaigi_iTaigiHoataiTuichiautian.csv'):
    add_entry('itaigi', r['DictWordID'], r['HanLoTaibunKip'], r['KipUnicode'], mandarin_list(r['HoaBun']))
for r in rows('ChhoeTaigi_TaihoaSoanntengTuichiautian.csv'):
    add_entry('taihoa', r['DictWordID'], r['HanLoTaibunKip'], r['KipUnicode'], mandarin_list(r['HoaBun']))
if INCLUDE_NC:
    print('including non-commercial sources (Maryknoll, Embree)')
    for r in rows('ChhoeTaigi_MaryknollTaiengSutian.csv'):
        add_entry('maryknoll', r['DictWordID'], r['HoaBun'], r['KipUnicode'], (), nfc(r['EngBun']))
    for r in rows('ChhoeTaigi_EmbreeTaiengSutian.csv'):
        add_entry('embree', r['DictWordID'], r['HoaBun'], r['KipUnicode'], (), nfc(r['EngBun']))
else:
    con.execute("DELETE FROM source WHERE id IN ('maryknoll','embree')")
for r in rows('ChhoeTaigi_TaioanPehoeKichhooGiku.csv'):
    eid = add_entry('tgb', r['DictWordID'], None, r['KipUnicode'], mandarin_list(r['HoaBun']), nfc(r['EngBun']))
    if eid and r['LekuPoj']:
        # TGB examples are POJ only; keep POJ text and key-normalised Tâi-lô
        tl = [x for x in r['LekuPoj'].split('/')]
        en = r['LekuEngbun'].replace('\\', '/').split('/')
        zh = r['LekuHoabun'].split('/')
        for i, s in enumerate(tl):
            con.execute('INSERT INTO example(entry_id,source,hanji,tailo,poj,mandarin,english) VALUES (?,?,?,?,?,?,?)',
                        (eid, 'tgb', None, None, nfc(s), nfc(zh[i]) if i < len(zh) else None,
                         nfc(en[i]) if i < len(en) else None))
con.commit()

# ---------------------------------------------------------------- frequency from the 2009 MOE corpus
freq = Counter()
syl = Counter()
docs = Counter()
for f in glob.glob(os.path.join(ROOT, 'Ungian_2009_KIPsupin/JSON格式資料/**/*.json'), recursive=True):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    seen = set()
    for art in d.get('資料', []):
        for pair in art.get('段', []):
            if len(pair) < 2:
                continue
            for tok in re.split(r'\s+', pair[1]):
                k = key(tok, poj=True)
                if not k:
                    continue
                freq[k] += 1
                seen.add(k)
                for s in k.split('-'):
                    syl[s] += 1
    for k in seen:
        docs[k] += 1
con.executemany('INSERT INTO corpus_freq(tkey,count,docs) VALUES (?,?,?)',
                [(k, c, docs[k]) for k, c in freq.items() if c >= 2])
con.executemany('INSERT INTO syllable_freq(syllable,count) VALUES (?,?)', syl.items())
print('corpus tokens', sum(freq.values()), 'types', len(freq))

# ---------------------------------------------------------------- HSK
hsk = json.load(open(os.path.join(ROOT, 'complete-hsk-vocabulary/complete.min.json')))
for e in hsk:
    lv = e['l']
    old = min([int(x[1:]) for x in lv if x.startswith('o')] or [None], key=lambda v: v or 99)
    new = min([int(x[1:]) for x in lv if x.startswith('n')] or [None], key=lambda v: v or 99)
    for form in e['f']:
        con.execute('INSERT OR IGNORE INTO hsk(trad,simp,pinyin,old_level,new_level,english) VALUES (?,?,?,?,?,?)',
                    (form['t'], e['s'], form['i']['y'], old, new, '; '.join(form['m'])[:300]))
con.commit()
con.close()

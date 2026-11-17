"""Which MOE recording belongs to which word: the ministry's own table (kautian.ods from sutian.moe.edu.tw).

The recordings in sutiau-mp3.zip / leku-mp3.zip are named after the ids of the current online dictionary
(sutian.moe.edu.tw), which are NOT the entry numbers of the older data (ChhoeTaigi / moedict-twblg) the course
database is built from. kautian.ods gives, for each headword, its Hàn-jī, romanisation and recording file name, and
for each example sentence its text and recording file name. Downloaded by tools/fetch_audio.py --table.
"""
import json
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ODS = os.path.join(ROOT, 'data/raw/moe-audio/kautian.ods')
CACHE = os.path.join(ROOT, 'data/raw/moe-audio/kautian.json')
PUNCT = re.compile(r'[，。！？、：；「」『』　 ,.!?;:"\'()（）【】\-]')


def _h(s):
    s = re.sub(r'【[^】]*】', '', str(s))
    return PUNCT.sub('', unicodedata.normalize('NFC', s))


def _t(s):
    s = re.sub(r'【[^】]*】', '', unicodedata.normalize('NFC', str(s)))
    return re.sub(r'[\s\-]+', '-', s.lower().strip(' .?!,-'))


def load():
    """{'w': {hanji|tailo: id}, 'h': {hanji: [ids]}, 'x': {sentence: file}} or None if the table is not there."""
    if os.path.exists(CACHE) and (not os.path.exists(ODS) or os.path.getmtime(CACHE) >= os.path.getmtime(ODS)):
        return json.load(open(CACHE, encoding='utf-8'))
    if not os.path.exists(ODS):
        return None
    import pandas as pd
    sheets = pd.read_excel(ODS, engine='odf', sheet_name=['詞目', '例句'], dtype=str)
    w, h, x = {}, {}, {}
    for _, r in sheets['詞目'].iterrows():
        f = str(r['羅馬字音檔檔名'] or '')
        m = re.match(r'^(\d+)\(\d+\)$', f)
        if not m:
            continue
        sid = m.group(1)
        hj = _h(r['漢字'])
        for tl in re.split(r'[/／]', str(r['羅馬字'])):     # 'ē/uē': one entry, several readings
            w.setdefault(f'{hj}|{_t(tl)}', sid)
        h.setdefault(hj, []).append(sid)
    for _, r in sheets['例句'].iterrows():
        f = str(r['音檔檔名'] or '')
        if re.match(r'^\d+-\d+-\d+$', f):
            x.setdefault(_h(r['漢字']), f)
    d = {'w': w, 'h': h, 'x': x}
    json.dump(d, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
    return d


SHEETS = ['詞目', '義項', '例句', '又唸作', '俗唸作', '合音唸作', '異用字', '詞彙比較']
SHEETS_CACHE = os.path.join(ROOT, 'data/raw/moe-audio/kautian-sheets.json')


def sheets(ods=ODS):
    """The table's sheets that tools/build_db.py takes in, as {sheet: [row dict, …]} (cells as NFC text, '' when
    empty), or None if the table is not there or cannot be read (the build then goes on without it)."""
    cache = SHEETS_CACHE if ods == ODS else None
    if cache and os.path.exists(cache) and (not os.path.exists(ods) or os.path.getmtime(cache) >= os.path.getmtime(ods)):
        return json.load(open(cache, encoding='utf-8'))
    if not os.path.exists(ods):
        return None
    try:
        import pandas as pd
        raw = pd.read_excel(ods, engine='odf', sheet_name=SHEETS, dtype=str)
    except Exception as e:      # missing odfpy/pandas, a renamed sheet, a truncated download
        print('kautian.ods not read:', e)
        return None
    out = {}
    for name, df in raw.items():
        df = df.fillna('')
        out[name] = [{k: unicodedata.normalize('NFC', str(v)).strip() for k, v in r.items()} for r in df.to_dict('records')]
    if cache:
        json.dump(out, open(cache, 'w', encoding='utf-8'), ensure_ascii=False)
    return out


def word(table, hanji, tailo):
    """Recording id of a headword, by Hàn-jī and romanisation (or by Hàn-jī alone when that is unambiguous)."""
    if not table:
        return None
    hj = _h(hanji)
    sid = table['w'].get(f'{hj}|{_t(tailo)}')
    if sid:
        return sid
    ids = table['h'].get(hj) or []
    return ids[0] if len(ids) == 1 else None


def example(table, sentence):
    return table['x'].get(_h(sentence)) if table else None

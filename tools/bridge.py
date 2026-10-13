"""Mandarin → Taigi reading bridge (proof of concept).

For characters a Mandarin speaker knows (HSK ≤ 4), build quiz items: the character and its pinyin,
the MOE Taigi reading(s), three plausible wrong options, and the sound correspondences that explain
the right answer. Used by build_app.py.

    python3 tools/bridge.py 30      # print 30 items
"""
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sandhi import parse, render  # noqa: E402

PY_TONE = {'̄': 1, '́': 2, '̌': 3, '̀': 4}
PY_INITIALS = ['zh', 'ch', 'sh', 'b', 'p', 'm', 'f', 'd', 't', 'n', 'l', 'g', 'k', 'h', 'j', 'q', 'x', 'r', 'z', 'c',
               's', 'y', 'w']
TL_INITIALS = ['tsh', 'ts', 'ph', 'th', 'kh', 'ng', 'p', 'b', 'm', 't', 'n', 'l', 'k', 'g', 'h', 's', 'j']


def py_parse(py):
    d = unicodedata.normalize('NFD', py.lower())
    tone = 5
    base = ''
    for ch in d:
        if ch in PY_TONE:
            tone = PY_TONE[ch]
        elif unicodedata.category(ch) != 'Mn':
            base += ch
    ini = next((i for i in PY_INITIALS if base.startswith(i)), '')
    return ini, base[len(ini):], tone


def tl_parse(syl):
    base, tone, _ = parse(syl)
    ini = next((i for i in TL_INITIALS if base.startswith(i)), '')
    fin = base[len(ini):]
    if ini == 'ng' and not fin:
        ini, fin = '', 'ng'
    if ini == 'm' and not fin:
        ini, fin = '', 'm'
    return base, ini, fin, tone


def rules(py, tl):
    """Correspondences that link this pinyin syllable to this Taigi syllable."""
    pi, pf, pt = py_parse(py)
    base, ti, tf, tt = tl_parse(tl)
    out = []
    spelling = {'b': 'p', 'd': 't', 'g': 'k', 'z': 'ts', 'p': 'ph', 't': 'th', 'k': 'kh', 'c': 'tsh'}
    if pi in spelling and ti == spelling[pi]:
        out.append(f'Spelling: pinyin {pi}- is written {ti}- in Tâi-lô (same sound family).')
    if pi in ('w', 'm') and ti == 'b':
        out.append('Mandarin w- / m- ↔ Taigi b- (文 bûn, 無 bô, 米 bí).')
    if pi == 'r' and ti in ('j', 'l'):
        out.append('Mandarin r- ↔ Taigi j- (or l- in colloquial words: 人 jîn / lâng).')
    if pi == 'f' and ti == 'h':
        out.append('Mandarin f- ↔ Taigi h- in literary readings (分 hun, 飛 hui).')
    if pi == 'f' and ti in ('p', 'ph'):
        out.append('Mandarin f- ↔ Taigi p- / ph- in colloquial readings: Taigi kept the older sound (飛 pue, 分 pun).')
    if pi in ('zh', 'ch', 'sh') and ti in ('ts', 'tsh', 's'):
        out.append('Mandarin zh / ch / sh ↔ Taigi ts / tsh / s (no retroflex sounds in Taigi).')
    if pi in ('zh', 'ch') and ti in ('t', 'th'):
        out.append('Mandarin zh / ch ↔ Taigi t / th: an older pronunciation kept in Taigi (茶 tê, 長 tn̂g, 竹 tik).')
    if pi in ('j', 'q', 'x') and ti in ('k', 'kh', 'h', 'g'):
        out.append('Mandarin j / q / x ↔ Taigi k / kh / h: these come from old k-sounds (家 ka, 去 khì, 香 hiong).')
    if pi in ('j', 'q', 'x') and ti in ('ts', 'tsh', 's'):
        out.append('Mandarin j / q / x ↔ Taigi ts / tsh / s: these come from old ts-sounds.')
    if pi in ('', 'y', 'w') and ti in ('g', 'ng'):
        out.append('No initial in Mandarin ↔ Taigi g- / ng-: Taigi kept an old ng- sound (五 gōo / ngóo, 雅 ngá).')
    if pf.endswith('n') and not pf.endswith('ng') and tf.endswith('m'):
        out.append('Mandarin -n ↔ Taigi -m: Mandarin merged -m into -n (三 sam, 心 sim, 甘 kam).')
    if tf[-1:] in ('p', 't', 'k'):
        out.append(f'Short "entering tone" syllable: Mandarin lost the final stop, Taigi keeps -{tf[-1]} (十 tsa̍p, 六 la̍k, 骨 kut).')
    elif tf.endswith('h') and not tf.endswith('nnh'):
        out.append('Colloquial -h: the syllable is cut short by a glottal stop (食 tsia̍h).')
    if 'nn' in tf:
        out.append('-nn: a nasal vowel, typical of colloquial readings (三 sann, 生 senn).')
    checked = tf[-1:] in ('p', 't', 'k', 'h') and not tf.endswith('ng')
    if not checked:
        tone_rule = {(1, '1'): 'Mandarin tone 1 ↔ Taigi tone 1 (high level).',
                     (1, '7'): 'Mandarin tone 1 ↔ here Taigi tone 7 (mid level); tone 1 would be more usual.',
                     (2, '5'): 'Mandarin tone 2 ↔ Taigi tone 5 (rising): the usual match.',
                     (3, '2'): 'Mandarin tone 3 ↔ Taigi tone 2 (high falling): the usual match.',
                     (3, '7'): 'Mandarin tone 3 ↔ Taigi tone 7: happens when the old initial was voiced.',
                     (4, '3'): 'Mandarin tone 4 ↔ Taigi tone 3 (low falling): old voiceless initial.',
                     (4, '7'): 'Mandarin tone 4 ↔ Taigi tone 7 (mid level): old voiced initial.'}.get((pt, tt))
        if tone_rule:
            out.append(tone_rule)
    else:
        out.append(f'Checked syllable: tone {tt} ({"low, short" if tt == "4" else "high, short"}). '
                   + ('Mandarin tone 2 often ↔ Taigi tone 8.' if tt == '8' and pt == 2 else ''))
    return out


LOOKALIKE = {1: '7', 2: '2', 3: '2', 4: '3'}   # pinyin mark → the Tâi-lô tone that looks the same


def distractors(py, tl):
    base, _, tf, tt = tl_parse(tl)
    _, _, pt = py_parse(py)
    checked = tf[-1:] in ('p', 't', 'k', 'h') and not tf.endswith('ng')
    opts = []
    if checked:
        opts.append(render(base, '8' if tt == '4' else '4'))
        stripped = base[:-1]
        opts.append(render(stripped, LOOKALIKE.get(pt, '1')))
        opts.append(render(stripped, '5' if pt != 2 else '7'))
    else:
        trap = LOOKALIKE.get(pt)
        for t in ([trap] if trap and trap != tt else []) + ['5', '2', '3', '7', '1']:
            if t != tt and render(base, t) not in opts:
                opts.append(render(base, t))
    out = []
    for o in opts:
        if o != tl and o not in out:
            out.append(o)
    return out[:3]


def build(con, limit=160):
    rows = con.execute("""
      SELECT e.id, e.hanji, e.tailo, e.wenbai, e.freq, h.pinyin, coalesce(h.old_level, h.new_level) lv
      FROM entry e JOIN hsk h ON h.trad = e.hanji
      WHERE e.source = 'moe' AND length(e.hanji) = 1 AND e.kind = 'word' AND e.tailo != ''
        AND e.tailo NOT LIKE '--%' AND coalesce(e.wenbai, '') != 'substitute-char'
        AND coalesce(h.old_level, h.new_level) <= 4
        AND h.english NOT LIKE 'surname%' AND h.pinyin = lower(h.pinyin)
      ORDER BY e.freq DESC""").fetchall()
    by_char = {}
    for eid, h, t, wb, f, py, lv in rows:
        d = by_char.setdefault(h, {'char': h, 'pinyins': [], 'level': lv, 'readings': {}, 'freq': 0})
        if py not in d['pinyins']:
            d['pinyins'].append(py)
        d['readings'].setdefault(t, wb)
        d['freq'] = max(d['freq'], f)
    items = []
    for h, d in sorted(by_char.items(), key=lambda kv: -kv[1]['freq']):
        reads = d['readings']
        # pick the (pinyin, reading) pair the correspondences explain best; literary readings win ties
        _, d['pinyin'], target = max(((len(rules(py, t)) + (0.5 if wb == 'literary' else 0), py, t)
                                      for py in d['pinyins'] for t, wb in reads.items()), key=lambda x: x[0])
        rs = rules(d['pinyin'], target)
        if not rs:
            continue
        others = [{'tailo': t, 'layer': wb} for t, wb in reads.items() if t != target]
        ex = con.execute("""SELECT hanji, tailo FROM entry WHERE source='moe' AND kind='word' AND length(hanji) = 2
                            AND instr(hanji, ?) > 0 AND freq > 0 ORDER BY freq DESC LIMIT 12""", (h,)).fetchall()
        ex = [(eh, et) for eh, et in ex if unicodedata.normalize('NFC', target.lower()) in
              [unicodedata.normalize('NFC', s.lower()) for s in re.split(r'[-\s]', et)]][:2]
        mand = con.execute('SELECT english FROM hsk WHERE trad=? AND pinyin=?', (h, d['pinyin'])).fetchone()
        items.append({'char': h, 'pinyin': d['pinyin'], 'level': d['level'], 'answer': target,
                      'layer': reads[target], 'others': others, 'options': distractors(d['pinyin'], target),
                      'rules': rs, 'examples': [{'hanji': a, 'tailo': b} for a, b in ex],
                      'meaning': (mand[0].split(';')[0] if mand else '')})
        if len(items) >= limit:
            break
    return items


if __name__ == '__main__':
    import sqlite3
    con = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/build/taigi.db'))
    for it in build(con, int(sys.argv[1]) if len(sys.argv) > 1 else 25):
        print(it['char'], it['pinyin'], '→', it['answer'], it['layer'] or '', '| wrong:', ' / '.join(it['options']))
        for r in it['rules']:
            print('   ·', r)

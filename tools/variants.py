"""Pronunciation variants for the reader app.

Two sources from the MOE dictionary:
  - 又音 (alternative readings of a word: 咧 teh / leh, 阮 guán / gún), table `variant`
  - 語音方言差 (how 400+ characters are read in 10 places), table `dialect`, kind='pronunciation'

`alts(hanji, tailo, entry_id)` returns the readings a learner could switch to, each labelled
('also said', or a region for the accent presets). `dialect_rows(hanji, tailo)` returns per-character place tables.
"""
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tailo import key, toneless  # noqa: E402

PRESETS = {'taipei': '臺北', 'tainan': '臺南'}
PRESET_NAME = {'taipei': 'North (Taipei)', 'tainan': 'South (Tainan)'}
SHOW = ['臺北', '臺南', '宜蘭', '鹿港', '金門']
KIND_EN = {'also read': 'also said', 'colloquially read': 'colloquially', 'contracted': 'contracted form'}


def _clean(r):
    r = re.sub(r'\(.*?\)|（.*?）', '', r or '')
    return [unicodedata.normalize('NFC', x.strip()) for x in r.split(';') if x.strip()]


def _same(a, b):
    # 'or' only marks how a southern o sounds; the standard spelling already covers it
    return toneless(key(a)).replace('or', 'o') == toneless(key(b)).replace('or', 'o')


class Variants:
    def __init__(self, con):
        self.con = con
        self.groups = {}   # char -> [ {place: [readings]} ], one dict per CSV row
        rows = con.execute("SELECT rowid, hanji, place, tailo FROM dialect WHERE kind='pronunciation' ORDER BY rowid")
        cur, last = None, None
        for _, h, place, t in rows:
            if place == '鹿港' or h != last:   # rows were stored in the CSV's column order, starting at 鹿港
                cur = {}
                self.groups.setdefault(h, []).append(cur)
            cur[place] = _clean(t)
            last = h

    def _group(self, char, syl):
        tl = toneless(key(syl))
        for g in self.groups.get(char, []):
            if any(toneless(key(r)) == tl for rs in g.values() for r in rs):
                return g
        return None

    def alts(self, hanji, tailo, entry_id=None):
        out = []
        seen = {unicodedata.normalize('NFC', tailo)}
        if entry_id:
            for t, kind in self.con.execute('SELECT tailo, kind FROM variant WHERE entry_id=?', (entry_id,)):
                t = unicodedata.normalize('NFC', t)
                if t not in seen:
                    seen.add(t)
                    out.append({'t': t, 'label': KIND_EN.get(kind, kind or 'also said')})
        prefix = '--' if tailo.startswith('--') else ''
        syls = [s for s in re.split(r'-+', tailo.lstrip('-')) if s]
        chars = re.findall(r'[㐀-鿿\U00020000-\U0003ffff]', hanji or '')
        if len(chars) == len(syls) and syls:
            for preset, place in PRESETS.items():
                new, changed = [], False
                for ch, sy in zip(chars, syls):
                    g = self._group(ch, sy)
                    r = (g or {}).get(place, [])
                    if r and not _same(r[0], sy):
                        new.append(r[0])
                        changed = True
                    else:
                        new.append(sy)
                if changed:
                    t = prefix + '-'.join(new)
                    same = next((o for o in out if o['t'] == t), None)
                    if same:
                        same['label'] += ' · ' + PRESET_NAME[preset]
                        same.setdefault('presets', []).append(preset)
                    else:
                        out.append({'t': t, 'label': PRESET_NAME[preset], 'presets': [preset]})
        return out

    def dialect_rows(self, hanji, tailo):
        syls = [s for s in re.split(r'-+', tailo.lstrip('-')) if s]
        chars = re.findall(r'[㐀-鿿\U00020000-\U0003ffff]', hanji or '')
        rows = []
        if len(chars) != len(syls):
            return rows
        for ch, sy in zip(chars, syls):
            g = self._group(ch, sy)
            if g:
                vals = {p: ' / '.join(g.get(p, [])) for p in SHOW}
                if len(set(vals.values())) > 1:
                    rows.append({'char': ch, 'places': vals})
        return rows

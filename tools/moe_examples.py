"""Where each MOE example sentence sits in its entry: (sense number, position), for the recordings in leku-mp3.zip,
which are named <entry id>-<sense>-<position>.mp3.

Reads the current MOE dictionary text from ChhoeTaigiDatabase (ChhoeTaigi_KauiokpooTaigiSutian.csv, column
KaisoehHanLoKip): '1.【數】數目。例：一蕊花　tsi̍t luí hue(一朵花)。2.【形】…例：紅嬰仔…'.
"""
import csv
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, 'data/raw/ChhoeTaigiDatabase/ChhoeTaigiDatabase/ChhoeTaigi_KauiokpooTaigiSutian.csv')
SENSE = re.compile(r'(?<![0-9])([0-9]+)\.【')
ITEM = re.compile(r'(.+?)\(([^()]*)\)')
PUNCT = '，。！？、：；「」『』　 '


def _norm(s):
    # rare characters (𪜶 …) are private-use code points in this source: leave them out on both sides
    return ''.join(ch for ch in s if ch not in PUNCT and not ('\ue000' <= ch <= '\uf8ff') and ord(ch) < 0x20000)


def _han(item):
    """Hàn-jī part of '紅嬰仔哭甲一身軀汗。Âng-enn-á…' or '一蕊花　tsi̍t luí hue'."""
    m = re.match(r'[^A-Za-zÀ-ɏḀ-ỿ]+', item.strip('、　 '))
    return _norm(m.group(0)) if m else ''


def _items(region):
    """Split an example list: items end at '、' once their romanisation has started, or at ')' before a new Hàn-jī."""
    items, cur, depth, latin = [], '', 0, False
    for i, ch in enumerate(region):
        if ch in '(（':
            depth += 1
        elif ch in ')）':
            depth = max(0, depth - 1)
            cur += ch
            nxt = region[i + 1:i + 2]
            if depth == 0 and nxt and ('㐀' <= nxt <= '鿿' or ord(nxt) > 0x20000):
                items.append(cur); cur, latin = '', False
            continue
        if depth == 0 and ch == '、' and latin:
            items.append(cur); cur, latin = '', False
            continue
        if depth == 0 and re.match(r'[A-Za-zÀ-ɏḀ-ỿ]', ch):
            latin = True
        cur += ch
    if cur.strip('。　 '):
        items.append(cur)
    return [x for x in items if _han(x)]


def load():
    """{entry id: [(sense, position, hanji), …]}"""
    out = {}
    if not os.path.exists(CSV):
        return out
    with open(CSV, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            text = row.get('KaisoehHanLoKip') or ''
            if '例：' not in text:
                continue
            marks = list(SENSE.finditer(text))
            parts = [(int(m.group(1)), text[m.end():marks[i + 1].start() if i + 1 < len(marks) else len(text)])
                     for i, m in enumerate(marks)] or [(1, text)]
            exs = []
            for sense, seg in parts:
                if '例：' not in seg:
                    continue
                region = re.split(r'　\[|\[[近反]\]', seg.split('例：', 1)[1])[0]
                for pos, it in enumerate(_items(region), 1):
                    exs.append((sense, pos, _han(it)))
            if exs:
                out[row['DictWordID']] = exs
    return out


def find(index, entry_id, hanji):
    """(sense, position) of `hanji` among the examples of entry `entry_id`, or None."""
    h = _norm(hanji)
    for sense, pos, eh in index.get(str(entry_id), []):
        if eh and eh == h:
            return sense, pos
    return None


if __name__ == '__main__':
    idx = load()
    print(len(idx), 'entries with examples;', sum(len(v) for v in idx.values()), 'examples')
    for k in ('1', '2', '3', '4'):
        print(k, idx.get(k))

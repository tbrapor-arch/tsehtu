"""Tâi-lô / POJ normalisation helpers.

key(s): canonical matching key for a romanised word, e.g. 'Tsi̍t-ê' -> 'tsit8-e5'.
Tones 1 and 4 are left unmarked so keys from Unicode and from numeric input agree.
"""
import re
import unicodedata

TONE_MARKS = {
    '́': '2',  # acute
    '̀': '3',  # grave
    '̂': '5',  # circumflex
    '̌': '6',  # caron (rare)
    '̄': '7',  # macron
    '̍': '8',  # vertical line above
    '̋': '9',  # double acute
}
SYL_RE = re.compile(r"[a-zA-Z̀-ͯⁿᴺ]+[0-9]?")


def _syl_uni_to_num(syl):
    d = unicodedata.normalize('NFD', syl)
    tone = ''
    out = []
    for ch in d:
        if ch in TONE_MARKS:
            tone = TONE_MARKS[ch]
        elif ch == '͘':  # POJ o͘
            out.append('o')
        elif ch == 'ⁿ':  # POJ superscript n (nasal)
            out.append('nn')
        elif unicodedata.category(ch) == 'Mn':
            continue
        else:
            out.append(ch)
    s = ''.join(out).lower()
    m = re.match(r'^([a-z]+)([0-9])$', s)
    if m:  # already numeric
        s, tone = m.group(1), m.group(2)
    if tone in ('1', '4'):
        tone = ''
    return s + tone


def poj_to_tailo_plain(s):
    """POJ (toneless or numeric, lowercase) syllable -> Tâi-lô spelling."""
    s = s.replace('chh', 'tsh').replace('ch', 'ts')
    s = re.sub(r'oa(?=[a-z]*)', 'ua', s)
    s = re.sub(r'oe', 'ue', s)
    s = re.sub(r'ou', 'oo', s)
    s = re.sub(r'eng', 'ing', s)
    s = re.sub(r'ek', 'ik', s)
    return s


def key(s, poj=False):
    if not s:
        return ''
    s = unicodedata.normalize('NFC', s)
    s = re.sub(r'\(.*?\)|（.*?）', '', s)
    s = s.replace('--', '-').replace(' ', '-')
    if poj:
        # POJ numeric capital N = nasal
        s = re.sub(r'(?<=[a-zA-Z])N', 'nn', s)
    syls = []
    for raw in re.split(r'[-\s]+', s):
        raw = raw.strip(".,!?;:'\"「」『』、。，！？；：()（）")
        if not raw:
            continue
        num = _syl_uni_to_num(raw)
        if not re.match(r'^[a-z]+[0-9]?$', num):
            continue
        if poj:
            base = re.match(r'^([a-z]+)([0-9]?)$', num)
            num = poj_to_tailo_plain(base.group(1)) + base.group(2)
        syls.append(num)
    return '-'.join(syls)


def toneless(k):
    return re.sub(r'[0-9]', '', k)


if __name__ == '__main__':
    for t in ['Tsi̍t', 'tsi̍t(替)', 'Âng-enn-á', 'khuànn-i-sing', 'tsit8', 'a-a-hau2']:
        print(t, key(t))
    for t in ['chhiu2--nih', 'khoaN3', 'sin-the2', 'Chiau3-li2', 'goe7-seng2', 'chit-ma2', 'chêng-chhah']:
        print(t, key(t, poj=True))

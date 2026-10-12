"""Tone sandhi for Tâi-lô (rule-based, general/northern Taiwanese by default).

Inside a tone group every syllable except the last takes its sandhi tone:

    unchecked   1→7   2→1   3→2   5→7 (south: 5→3)   7→3
    checked     4 (-p -t -k) → 8      4 (-h) → 2, -h dropped
                8 (-p -t -k) → 3      8 (-h) → 3, -h dropped

Tone groups end at punctuation, at a manual `|`, and before `--`. A syllable written after `--` is
neutral (light) tone; the syllable before `--` keeps its citation tone.

Two ways to mark groups:
  sandhi('tsia̍h-pn̄g')                  word mode: each hyphenated word is its own group
  sandhi('Guá beh khì | Tâi-pak.', 'phrase')   phrase mode: spaces don't end a group, `|` and punctuation do

The prefix 阿 a- (A-bîng, a-má) keeps its tone.

Not modelled (flagged in `notes`): the special sandhi before 仔 á, triple adjectives (âng-âng-âng),
and the many lexical exceptions. Treat output as a teaching aid, not ground truth.

    python3 tools/sandhi.py "Guá beh khì | Tâi-pak."      prints citation / spoken lines
    python3 tools/sandhi.py --test
"""
import re
import sys
import unicodedata

MARK = {'2': '́', '3': '̀', '5': '̂', '7': '̄', '8': '̍', '9': '̋'}
FROM_MARK = {v: k for k, v in MARK.items()}
UNCHECKED = {'1': '7', '2': '1', '3': '2', '5': '7', '7': '3'}
UNCHECKED_SOUTH = dict(UNCHECKED, **{'5': '3'})


def parse(syl):
    """'Tsia̍h' -> ('tsiah', '8', True)  (base lowercase, tone, capitalised)."""
    d = unicodedata.normalize('NFD', syl)
    tone = ''
    base = []
    for ch in d:
        if ch in FROM_MARK:
            tone = FROM_MARK[ch]
        elif unicodedata.category(ch) != 'Mn':
            base.append(ch)
    b = ''.join(base)
    cap = b[:1].isupper()
    b = b.lower()
    if not tone:
        tone = '4' if is_checked(b) else '1'
    return b, tone, cap


def is_checked(base):
    return bool(re.search(r'[ptkh]$', base)) and not base.endswith('ng')


def render(base, tone, cap=False):
    """('tsiah', '8') -> 'tsia̍h'. Mark goes on a > oo/o > e > (iu→u, ui→i) > i/u > syllabic m/ng."""
    s = base
    if tone in MARK:
        idx = None
        for pat in ('a', 'oo', 'o', 'e'):
            if pat in s:
                idx = s.index(pat)
                break
        if idx is None:
            if 'iu' in s:
                idx = s.index('iu') + 1
            elif 'ui' in s:
                idx = s.index('ui') + 1
            else:
                for v in 'iu':
                    if v in s:
                        idx = s.index(v)
                        break
        if idx is None:
            m = re.search(r'ng|m', s)
            idx = m.start() if m else 0
        s = s[:idx + 1] + MARK[tone] + s[idx + 1:]
    s = unicodedata.normalize('NFC', s)
    return s[:1].upper() + s[1:] if cap else s


def change(base, tone, south=False):
    """Return (new_base, new_tone) for a non-final syllable."""
    if is_checked(base):
        if base.endswith('h'):
            return base[:-1], {'4': '2', '8': '3'}.get(tone, tone)
        return base, {'4': '8', '8': '3'}.get(tone, tone)
    return base, (UNCHECKED_SOUTH if south else UNCHECKED).get(tone, tone)


TOKEN_RE = re.compile(r"(--|-|\||[\s]+|[.,!?;:，。！？；：「」『』、()（）…\"“”]+)")


def sandhi(text, mode='word', south=False):
    """Return (spoken_text, notes). spoken_text keeps the input's punctuation and spacing (minus `|`)."""
    tokens = [t for t in TOKEN_RE.split(text) if t != '']
    # classify tokens: syllable or separator
    syl_idx = [i for i, t in enumerate(tokens) if not TOKEN_RE.fullmatch(t)]
    out = list(tokens)
    notes = []
    neutral = False
    for n, i in enumerate(syl_idx):
        base, tone, cap = parse(tokens[i])
        # what separates this syllable from the next one?
        nxt = syl_idx[n + 1] if n + 1 < len(syl_idx) else None
        between = ''.join(tokens[i + 1:nxt]) if nxt is not None else '<end>'
        group_ends = (
            nxt is None
            or '--' in between
            or '|' in between
            or re.search(r'[.,!?;:，。！？；：「」『』、()（）…"“”]', between)
            or (mode == 'word' and re.search(r'\s', between))
        )
        prefix_a = base == 'a' and tone == '1' and between == '-'   # 阿 a- prefix keeps its tone
        if not neutral and not group_ends and not prefix_a:
            nb, nt = change(base, tone, south)
            out[i] = render(nb, nt, cap)
            nxt_base = parse(tokens[nxt])[0] if nxt is not None else ''
            if nxt_base == 'a' and parse(tokens[nxt])[1] == '2':
                notes.append(f'{tokens[i]}: before 仔 á special sandhi applies (not modelled)')
        # neutral tone applies to the syllables after '--' up to the next space/punct
        if '--' in between:
            neutral = True
        elif re.search(r'[\s|.,!?;:，。！？；：]', between):
            neutral = False
    spoken = ''.join(t for t in out if t != '|')
    spoken = re.sub(r'\s{2,}', ' ', spoken).strip()
    return spoken, notes


TESTS = [
    # (input, mode, expected)
    ('tsia̍h-pn̄g', 'word', 'tsià-pn̄g'),          # 8h -> 3, h dropped
    ('tshù-lāi', 'word', 'tshú-lāi'),           # 3 -> 2
    ('kha-tshiú', 'word', 'khā-tshiú'),         # 1 -> 7
    ('hó-tsia̍h', 'word', 'ho-tsia̍h'),           # 2 -> 1
    ('lâng-kheh', 'word', 'lāng-kheh'),         # 5 -> 7
    ('pīng-iú', 'word', 'pìng-iú'),             # 7 -> 3
    ('tsit-tsām', 'word', 'tsi̍t-tsām'),         # 4 ptk -> 8
    ('to̍k-tshù', 'word', 'tòk-tshù'),          # 8 ptk -> 3
    ('beh-khì', 'word', 'bé-khì'),              # 4h -> 2, h dropped
    ('Lí hó.', 'word', 'Lí hó.'),               # separate words, word mode: no change
    ('Lí hó.', 'phrase', 'Li hó.'),             # one group
    ('Lí beh khì--bô?', 'phrase', 'Li bé khì--bô?'),  # syllable before -- keeps tone, bô neutral
    ('Guá beh khì | Tâi-pak.', 'phrase', 'Gua bé khì Tāi-pak.'),
    ('Tâi-uân', 'word', 'Tāi-uân'),
    ('Guá kiò A-bîng.', 'phrase', 'Gua kió A-bîng.'),   # 阿 prefix unchanged
    ('Tâi-uân', 'word south', 'Tài-uân'),
]


def run_tests():
    bad = 0
    for text, mode, exp in TESTS:
        south = mode.endswith('south')
        got, _ = sandhi(text, mode.split()[0], south)
        ok = unicodedata.normalize('NFC', got) == unicodedata.normalize('NFC', exp)
        bad += not ok
        print(('ok  ' if ok else 'FAIL'), f'{text!r} [{mode}] -> {got!r}' + ('' if ok else f'  expected {exp!r}'))
    print(f'{len(TESTS) - bad}/{len(TESTS)} passed')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    if sys.argv[1:2] == ['--test']:
        run_tests()
    text = ' '.join(a for a in sys.argv[1:] if not a.startswith('--'))
    mode = 'word' if '--word' in sys.argv else 'phrase'
    spoken, notes = sandhi(text, mode, '--south' in sys.argv)
    print('citation:', text.replace(' | ', ' '))
    print('spoken:  ', spoken)
    for n in notes:
        print('note:    ', n)

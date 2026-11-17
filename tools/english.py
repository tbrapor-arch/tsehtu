"""English for the word cards: one gloss for every word, with where it came from.

Order (first one found wins):
  1. course    English written in the lessons' and themes' `new_words` (passed in by build_app.py)
  2. written   course/glosses_en.tsv: short glosses written for the course, checked against the MOE meanings
  3. maryknoll Maryknoll/Embree gloss borrowed by tools/enrich.py (only in databases built with `make db-nc`;
               non-commercial licence)
  4. mandarin  CC-CEDICT English of the word's Mandarin equivalent in the database (`mandarin:<word>`)
  5. parts     glosses of the syllables/characters joined with " + " (numbers, names, compounds not in the dictionaries)

Used by tools/build_app.py and by the private module's build (podcast transcripts, exam texts), so a word gets the
same English everywhere. `python3 -I tools/english.py` lists course and theme words that still rely on 3–5.
"""
import csv
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WRITTEN = os.path.join(ROOT, 'course/glosses_en.tsv')
CEDICT_JSON = os.path.join(ROOT, 'data/raw/cedict/package/cedict.json')
SKIP = ('variant of', 'old variant', 'CL:', 'used in ', 'see ', 'also written', 'abbr. for', 'surname ')


def _key(tailo):
    from tailo import key
    return key(tailo)


def load_cedict(path=CEDICT_JSON):
    ced = {}
    if os.path.exists(path):
        for e in json.load(open(path, encoding='utf-8')):
            if e['pinyin'][:1].isupper():      # proper names: keep only if nothing else
                ced.setdefault(e['traditional'], e)
            elif e['traditional'] not in ced or ced[e['traditional']]['pinyin'][:1].isupper():
                ced[e['traditional']] = e
    return ced


def cedict_en(ced, word, limit=90):
    e = ced.get(word)
    if not e:
        return ''
    gs = [re.sub(r'\s*\(CL:[^)]*\)', '', g) for g in e['english'] if not g.startswith(SKIP)]
    return '; '.join(g for g in gs if g)[:limit]


def load_written(path=WRITTEN):
    """{(hanji, tkey): English}. Lines starting with # are comments; columns: hanji, tâi-lô, English."""
    out = {}
    if os.path.exists(path):
        for row in csv.reader(open(path, encoding='utf-8'), delimiter='\t'):
            if not row or row[0].startswith('#') or len(row) < 3 or not row[2].strip():
                continue
            out[(row[0].strip(), _key(row[1].strip()))] = row[2].strip()
    return out


def course_glosses(root=ROOT):
    """{tkey: English} from the lessons' (base, part 2 進修 and part 3 文學) and themes' new_words, as build_app.py
    reads them."""
    import glob
    import yaml
    out = {}
    for f in sorted(glob.glob(os.path.join(root, 'course/lessons/[0-9]*.yaml'))) + \
            sorted(glob.glob(os.path.join(root, 'course/perfectionnement/[0-9]*.yaml'))) + \
            sorted(glob.glob(os.path.join(root, 'course/literature/[0-9]*.yaml'))):
        for w in yaml.safe_load(open(f, encoding='utf-8')).get('new_words') or []:
            if w.get('en'):
                out[_key(w['tailo'])] = w['en']
    for f in sorted(glob.glob(os.path.join(root, 'course/themes/*.yaml'))):
        for sec in yaml.safe_load(open(f, encoding='utf-8'))['sections']:
            for w in sec['words']:
                if w.get('en'):
                    out.setdefault(_key(w['tailo']), w['en'])
    return out


HAN = re.compile(r'[\u3400-\u9fff\U00020000-\U0003ffff]')


def course_pairs(root=ROOT):
    """({(Hàn-jī, tkey): English}, {tkey: set of Hàn-jī}) for the course's new words: lessons and 進修 (last wins),
    then themes, then 文學 (first wins). Two words with the same reading but other
    characters (踮 / 店 tiàm) each keep their own English."""
    import glob
    import yaml
    pairs, hanji = {}, {}
    for f in sorted(glob.glob(os.path.join(root, 'course/lessons/[0-9]*.yaml'))) + \
            sorted(glob.glob(os.path.join(root, 'course/perfectionnement/[0-9]*.yaml'))):
        for w in yaml.safe_load(open(f, encoding='utf-8')).get('new_words') or []:
            if w.get('en') and w.get('hanji'):
                k = _key(w['tailo'])
                pairs[(w['hanji'], k)] = w['en']
                hanji.setdefault(k, set()).add(w['hanji'])
    for f in sorted(glob.glob(os.path.join(root, 'course/themes/*.yaml'))):
        for sec in yaml.safe_load(open(f, encoding='utf-8'))['sections']:
            for w in sec['words']:
                if w.get('en') and w.get('hanji'):
                    k = _key(w['tailo'])
                    pairs.setdefault((w['hanji'], k), w['en'])
                    hanji.setdefault(k, set()).add(w['hanji'])
    # the 文學 lessons last: their own words (so that their English never reaches a homophone by its reading alone);
    # a word the lessons or themes already gloss keeps that gloss
    for f in sorted(glob.glob(os.path.join(root, 'course/literature/[0-9]*.yaml'))):
        for w in yaml.safe_load(open(f, encoding='utf-8')).get('new_words') or []:
            if w.get('en') and w.get('hanji'):
                k = _key(w['tailo'])
                pairs.setdefault((w['hanji'], k), w['en'])
                hanji.setdefault(k, set()).add(w['hanji'])
    return pairs, hanji


class English:
    def __init__(self, con, course=None, ced=None):
        self.con = con
        self.course = course if course is not None else course_glosses()   # {tkey: English} (+ {(Hàn-jī, tkey): English})
        self.course_pair, self.course_hanji = course_pairs()   # {(Hàn-jī, tkey): English}, {tkey: {Hàn-jī}}
        self.written = load_written()
        self.ced = ced if ced is not None else load_cedict()
        cols = [r[1] for r in con.execute('PRAGMA table_info(entry)')]
        self.has_en = 'english' in cols

    def _course(self, hanji, k, dict_hanji=None):
        """The course's English for this word. Matched on Hàn-jī + reading when the course says which characters it
        means; a bare reading only matches a word written the same way, or written without characters, so that a
        homophone (闊 khuah) never takes another word's English (渴 khuah, thirsty)."""
        en = self.course_pair.get((hanji, k)) or (dict_hanji and self.course_pair.get((dict_hanji, k)))
        if en:
            return en
        hs = self.course_hanji.get(k)
        if k in self.course and (not hs or (not HAN.search(hanji or '') and len(hs) == 1)):
            return self.course[k]   # a word the course writes without characters, or a romanised word
        return None

    def gloss(self, hanji, k, eid=None, dict_hanji=None, parts=(), cognate=None):
        """(English, source) for a word; ('', None) if nothing is known. `parts` = [(English, source), …].
        `cognate`: the dictionary's comparison with Mandarin (same-chars-diff-use: the same characters mean something
        else in Mandarin, so CC-CEDICT's entry for the characters is not used)."""
        en = self._course(hanji, k, dict_hanji)
        if en:
            return en, 'course'
        en = self.written.get((hanji, k)) or (dict_hanji and self.written.get((dict_hanji, k)))
        if en:
            return en, 'written'
        if eid is not None:   # one entry id, or several (the same word in other dictionaries), first one first
            eids = eid if isinstance(eid, (list, tuple)) else [eid]
            if self.has_en:
                for i in eids:
                    r = self.con.execute('SELECT english FROM entry WHERE id=?', (i,)).fetchone()
                    if r and r[0]:
                        return _tidy(r[0]), 'maryknoll'
            for i in eids:
                for (w,) in self.con.execute('SELECT DISTINCT word FROM mandarin WHERE entry_id=?', (i,)):
                    en = cedict_en(self.ced, w)
                    if en:
                        return en, 'mandarin:' + w
        # a word of two or more characters no Taigi dictionary glosses, written as Mandarin writes it (某種, 工作者):
        # CC-CEDICT's entry for the whole word, before its pieces joined; never for one character (too ambiguous) or a
        # false friend
        if cognate != 'same-chars-diff-use':
            for w in dict.fromkeys(x for x in (hanji, dict_hanji) if x and len(x) > 1 and all(HAN.match(ch) for ch in x)):
                en = cedict_en(self.ced, w)
                if en:
                    return en, 'mandarin:' + w
        if parts and all(p and p[0] for p in parts):
            return ' + '.join(_first(p[0]) for p in parts), 'parts'
        return '', None


def _first(en):
    """First sense only, for joining parts: 'to put; to place' -> 'to put'. A character gloss written for Lessons ›
    台語字 names the word it comes from ('eye (in 目睭 ba̍k-tsiu)', 'in 虼蚤 ka-tsáu: flea'): that part is dropped here."""
    first = re.split(r'[;,]', en)[0].strip()
    first = re.sub(r'^in \S+ [^:]+: ', '', first)
    return re.sub(r'\s*\(in [^)]*\)$', '', first).strip() or first


def _tidy(en):
    """Maryknoll glosses run on and are cut mid-sentence: keep whole comma/semicolon items, at most ~80 characters."""
    items, out = re.split(r'(?<=[,;])\s+', en.strip()), ''
    for it in items:
        if len(out) + len(it) > 80 and out:
            break
        out += (' ' if out else '') + it
    return out.rstrip(',; ')


if __name__ == '__main__':      # quick check: python3 -I tools/english.py 啉 lim
    import sqlite3
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    con = sqlite3.connect(os.path.join(ROOT, 'data/build/taigi.db'))
    E = English(con)
    print(f'{len(E.written)} written glosses, {len(E.course)} course glosses')
    if len(sys.argv) == 3:
        h, k = sys.argv[1], _key(sys.argv[2])
        r = con.execute("SELECT id FROM entry WHERE tkey=? AND source='moe' ORDER BY (hanji=?) DESC", (k, h)).fetchone()
        print(E.gloss(h, k, r[0] if r else None, h))

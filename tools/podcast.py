"""Parse the podcast feed (data/raw/podcast/feed.xml) into episodes for the app.

Each episode: number, title, date, duration, audio URL (SoundOn), cover, intro text, chapters
(`00:05 Taigi text（Mandarin）` -> seconds, text, zh), vocabulary from the 「🌟 臺語補給站」 section
(`漢字 tâi-lô ➡️ explanation`), corrections (「📌 本集勘誤」). Footer lines (links, hosting) are dropped.
"""
import email.utils
import os
import re
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEED = os.path.join(ROOT, 'data/raw/podcast/feed.xml')
NS = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd', 'content': 'http://purl.org/rss/1.0/modules/content/'}
TS = re.compile(r'^\(?(\d{1,2}(?::\d{2}){1,2})\)?\s*[-–—:：]?\s*(.+)$')
LATIN = r"[A-Za-zÀ-ɏḀ-ỿ̀-ͯ'-]"
HEADER = re.compile(r'^(?:[^\w\s]|[☀-➿]|️)+\s*(.+)$')


def secs(t):
    s = 0
    for p in t.split(':'):
        s = s * 60 + int(p)
    return s


def split_zh(text):
    """'第四季欲結束矣！（第四季要結束了！）' -> ('第四季欲結束矣！', '第四季要結束了！')"""
    m = re.match(r'^(.*?)\s*[（(]([^（()）]*)[)）]\s*$', text)
    return (m.group(1).strip(), m.group(2).strip()) if m and m.group(1).strip() else (text.strip(), '')


def vocab_items(line):
    """One line may hold several words: '薪水 sin-suí、步調 pōo-tiāu', or a labelled list
    '地名大雜燴：歐洲 Au-tsiu、法國 Huat-kok'. The explanation after ➡️ goes with each word of the line."""
    head, arrow, expl = line.partition('➡')
    label = ''
    m = re.match(r'^([^：:A-Za-z]{1,12})[：:]\s*(.+)$', head)
    if m and '、' in m.group(2):
        label, head = m.group(1).strip(), m.group(2)
    parts = [x for x in re.split(r'\s*、\s*(?=[^、]*[A-Za-z])', head) if x.strip()] if '、' in head else [head]
    out = []
    for part in parts:
        v = vocab_line(part + (arrow + expl if arrow else ''))
        if v:
            if label:
                v['group'] = label
            out.append(v)
    return out


def vocab_line(line):
    """'行禮 kiânn-lé ➡️ 鞠躬、作揖' -> {h, t, en}; romanisation alternatives after '/' are kept in `alt`."""
    head, _, expl = line.partition('➡')
    expl = expl.lstrip('️ ').strip()
    head = head.strip(' ・•-–*')
    m = re.match(rf'^([^A-Za-zÀ-ɏḀ-ỿ]*?)\s*({LATIN}+(?:\s+{LATIN}+)*(?:\s*/\s*{LATIN}+(?:\s+{LATIN}+)*)*)\s*$', head)
    if m:
        h, rom = m.group(1).strip(), m.group(2).strip()
    else:
        h, rom = head, ''
    alts = [r.strip() for r in rom.split('/') if r.strip()]
    if not h and not alts:
        return None
    return {'h': h, 't': alts[0] if alts else '', 'alt': alts[1:], 'en': expl}


def parse_description(text):
    lines = [l.strip() for l in text.replace('\r', '').split('\n')]
    intro, chapters, vocab, fixes, other = [], [], [], [], []
    section = 'intro'
    for l in lines:
        if not l:
            continue
        if re.fullmatch(r'[＿_—\-=~]{3,}', l):
            section = 'other'
            continue
        if '臺語補給站' in l or '台語補給站' in l:
            section = 'vocab'
            continue
        if '勘誤' in l and len(l) < 20:
            section = 'fix'
            continue
        if re.search(r'Instagram|合作邀請|翻新時間|Hosting provided|soundon\.fm|《隔壁', l, re.I) or re.match(r'https?://', l):
            section = 'footer'
            continue
        m = TS.match(l)
        if m and section in ('intro', 'chapters', 'other'):
            t, zh = split_zh(m.group(2))
            chapters.append({'s': secs(m.group(1)), 't': t, 'zh': zh})
            section = 'chapters'
            continue
        if section == 'vocab':
            vs = vocab_items(l) if '➡' in l or re.search(LATIN + '{2,}', l) else []
            if vs:
                vocab.extend(vs)
            elif vocab:
                vocab[-1]['en'] = (vocab[-1]['en'] + ' ' + l).strip()
            continue
        if section == 'fix':
            fixes.append(l)
            continue
        if section == 'intro':
            intro.append(l)
        elif section not in ('footer',):
            other.append(l)
    return {'intro': intro, 'chapters': chapters, 'vocab': vocab, 'fixes': fixes, 'other': other}


def load():
    if not os.path.exists(FEED):
        return None
    root = ET.parse(FEED).getroot()
    ch = root.find('channel')
    show = {'title': (ch.findtext('title') or '').strip(), 'author': (ch.findtext('itunes:author', namespaces=NS) or '').strip(),
            'image': (ch.find('itunes:image', NS).get('href') if ch.find('itunes:image', NS) is not None else ''),
            'link': (ch.findtext('link') or '').strip(), 'episodes': []}
    for it in ch.findall('item'):
        enc = it.find('enclosure')
        if enc is None:
            continue
        title = (it.findtext('title') or '').strip()
        num = re.search(r'EP\s*(\d+)', title, re.I)
        dur = (it.findtext('itunes:duration', namespaces=NS) or '0').strip()
        dur = secs(dur) if ':' in dur else int(float(dur or 0))
        date = it.findtext('pubDate') or ''
        try:
            date = email.utils.parsedate_to_datetime(date).date().isoformat()
        except (TypeError, ValueError):
            date = ''
        desc = it.findtext('itunes:summary', namespaces=NS) or it.findtext('description') or ''
        desc = re.sub(r'<[^>]+>', '', desc)
        img = it.find('itunes:image', NS)
        ep = {'n': int(num.group(1)) if num else None, 'title': title, 'date': date, 'dur': dur, 'url': enc.get('url'),
              'img': img.get('href') if img is not None else '', 'guid': (it.findtext('guid') or enc.get('url')).strip()}
        ep.update(parse_description(desc))
        show['episodes'].append(ep)
    return show

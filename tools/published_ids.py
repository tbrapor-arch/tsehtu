"""Add the word-card ids of a built page to app/published-card-ids.txt (never removes any).

    python3 tools/published_ids.py [app/dist/index.html]

Run it on the page that is being published (after `make app`), and commit the file with the change: every later build
keeps a card for each listed id (tools/build_app.py), so a word saved on a device or opened from the private module
never stops opening when an example list or a lesson changes."""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE = os.path.join(ROOT, 'app', 'published-card-ids.txt')
HEAD = ('# Every word-card id the published page has had: tools/build_app.py keeps a card for each, so a saved word or\n'
        '# a link from the private module never stops opening. Add ids (tools/published_ids.py), never remove any.\n')


def ids_of(page):
    s = open(page, encoding='utf-8').read()
    m = re.search(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', s, re.S)
    return set(json.loads(m.group(1))['dict'])


def main():
    page = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'app', 'dist', 'index.html')
    old = {l.strip() for l in open(FILE, encoding='utf-8') if l.strip() and not l.startswith('#')} if os.path.exists(FILE) else set()
    new = ids_of(page)
    open(FILE, 'w', encoding='utf-8').write(HEAD + ''.join(i + '\n' for i in sorted(old | new)))
    print(f'{FILE}: {len(old | new)} ids ({len(new - old)} added)')


if __name__ == '__main__':
    main()

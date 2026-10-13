"""Copy the MOE headword recordings the app needs into app/dist/audio/w/<MOE id>.mp3.

  python3 tools/fetch_audio.py [zip-or-url]

The recordings come from 教育部《臺灣台語常用詞辭典》 (sutiau-mp3.zip, licence CC BY-ND 3.0 TW: copied as they are,
not edited). The list of ids comes from `make app` (app/dist/audio-needed.txt). Inside the zip a headword's file is
named `<id>(<n>).mp3`, n = reading number; the main reading (1) is used. Run `make app` again afterwards.
"""
import os
import re
import shutil
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'https://sutian.moe.edu.tw/media/senn/sutiau-mp3.zip'
CACHE = os.path.join(ROOT, 'data/raw/moe-audio/sutiau-mp3.zip')
OUT = os.path.join(ROOT, 'app/dist/audio/w')

src = sys.argv[1] if len(sys.argv) > 1 else URL
if src.startswith('http'):
    if not os.path.exists(CACHE):
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        print('downloading', src)
        req = urllib.request.Request(src, headers={'User-Agent': 'tsehtu-build (+https://github.com/tbrapor-arch/tsehtu)'})
        with urllib.request.urlopen(req, timeout=600) as r, open(CACHE + '.part', 'wb') as f:
            shutil.copyfileobj(r, f, 1 << 20)
        os.replace(CACHE + '.part', CACHE)
    src = CACHE
need = set(open(os.path.join(ROOT, 'app/dist/audio-needed.txt')).read().split())
os.makedirs(OUT, exist_ok=True)
NAME = re.compile(r'(?:^|/)(\d+)(?:\((\d+)\))?\.mp3$', re.I)
best = {}   # id -> (reading number, zip member)
with zipfile.ZipFile(src) as z:
    names = z.namelist()
    print(len(names), 'files in the zip, e.g.', names[:3])
    for n in names:
        m = NAME.search(n)
        if m and m.group(1) in need:
            k = int(m.group(2) or 1)
            if m.group(1) not in best or k < best[m.group(1)][0]:
                best[m.group(1)] = (k, n)
    for i, (_, n) in best.items():
        with z.open(n) as r, open(os.path.join(OUT, i + '.mp3'), 'wb') as f:
            shutil.copyfileobj(r, f)
print(f'{len(best)} of {len(need)} recordings copied to {os.path.relpath(OUT, ROOT)}')
if not best:
    sys.exit('no recordings matched: check the file names printed above')

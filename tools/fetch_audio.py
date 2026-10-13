"""Copy the MOE recordings the app needs into app/dist/audio/.

  python3 tools/fetch_audio.py [words.zip examples.zip]     (default: download both from the MOE site)

Recordings from 教育部《臺灣台語常用詞辭典》, licence CC BY-ND 3.0 TW: copied as they are, not edited.
- headwords (sutiau-mp3.zip): `<id>(<n>).mp3`, n = reading number, the main reading (1) is used
  -> app/dist/audio/w/<id>.mp3; list from app/dist/audio-needed.txt
- example sentences (leku-mp3.zip): `<id>-<sense>-<position>.mp3`
  -> app/dist/audio/s/<same name>; list from app/dist/audio-needed-examples.txt (see tools/moe_examples.py)
Both lists are written by `make app`; run `make app` again afterwards.
"""
import os
import re
import shutil
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://sutian.moe.edu.tw/media/senn/'
CACHE = os.path.join(ROOT, 'data/raw/moe-audio')
DIST = os.path.join(ROOT, 'app/dist')


def get(name, given=None):
    if given:
        return given
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        os.makedirs(CACHE, exist_ok=True)
        print('downloading', BASE + name)
        req = urllib.request.Request(BASE + name, headers={'User-Agent': 'tsehtu-build (+https://github.com/tbrapor-arch/tsehtu)'})
        with urllib.request.urlopen(req, timeout=900) as r, open(path + '.part', 'wb') as f:
            shutil.copyfileobj(r, f, 1 << 20)
        os.replace(path + '.part', path)
    return path


def extract(zpath, need, pattern, out, key):
    """Copy members whose name matches `pattern` and whose key(match) is in `need` to out/<key>.mp3."""
    os.makedirs(out, exist_ok=True)
    best = {}
    with zipfile.ZipFile(zpath) as z:
        names = z.namelist()
        print(len(names), 'files in', os.path.basename(zpath), 'e.g.', names[:3])
        for n in names:
            m = pattern.search(n)
            if m:
                k, rank = key(m)
                if k in need and (k not in best or rank < best[k][0]):
                    best[k] = (rank, n)
        for k, (_, n) in best.items():
            with z.open(n) as r, open(os.path.join(out, k + '.mp3'), 'wb') as f:
                shutil.copyfileobj(r, f)
    print(f'{len(best)} of {len(need)} copied to {os.path.relpath(out, ROOT)}')
    return len(best)


args = sys.argv[1:]
need_w = set(open(os.path.join(DIST, 'audio-needed.txt')).read().split())
n = extract(get('sutiau-mp3.zip', args[0] if args else None), need_w,
            re.compile(r'(?:^|/)(\d+)(?:\((\d+)\))?\.mp3$', re.I), os.path.join(DIST, 'audio/w'),
            lambda m: (m.group(1), int(m.group(2) or 1)))
ex_list = os.path.join(DIST, 'audio-needed-examples.txt')
if os.path.exists(ex_list):
    need_s = set(open(ex_list).read().split())
    try:
        extract(get('leku-mp3.zip', args[1] if len(args) > 1 else None), need_s,
                re.compile(r'(?:^|/)(\d+-\d+-\d+)\.mp3$', re.I), os.path.join(DIST, 'audio/s'),
                lambda m: (m.group(1), 0))
    except Exception as e:   # the sentence recordings are a bonus: never fail the build for them
        print('example recordings skipped:', e)
if not n:
    sys.exit('no headword recordings matched: check the file names printed above')

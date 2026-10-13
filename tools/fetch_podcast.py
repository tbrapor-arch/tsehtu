"""Download the RSS feed of the Taigi podcast shown in the app's Podcast tab.

  python3 tools/fetch_podcast.py            -> data/raw/podcast/feed.xml

The show: 隔壁 ê 戇人 (Keh-piah ê gōng-lâng), by 欸緒利, 阿尹 and 阿莉莎, hosted by SoundOn. The app only shows the
episode notes from the feed and plays the audio from SoundOn's own URLs; nothing is re-hosted. Run by the GitHub
workflow before `make app` (the site cannot be reached from everywhere; without the feed the tab is just empty).
"""
import os
import shutil
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEED = 'https://feeds.soundon.fm/podcasts/62a8ab2c-2b72-49e6-aaf9-d4e2b342354d.xml'
OUT = os.path.join(ROOT, 'data/raw/podcast/feed.xml')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
req = urllib.request.Request(FEED, headers={'User-Agent': 'tsehtu-build (+https://github.com/tbrapor-arch/tsehtu)'})
with urllib.request.urlopen(req, timeout=120) as r, open(OUT + '.part', 'wb') as f:
    shutil.copyfileobj(r, f)
os.replace(OUT + '.part', OUT)
print('feed saved:', os.path.relpath(OUT, ROOT), os.path.getsize(OUT) // 1024, 'KB')

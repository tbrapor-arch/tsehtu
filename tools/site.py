"""Turn app/dist into an installable web app in _site/ (used by the GitHub workflow).

  python3 tools/site.py [out-dir]

Adds a proper <head> (home-screen icon, full-screen launch without browser bars, theme colour), the manifest,
the icons, the offline service worker, and the recordings if app/dist/audio exists.
"""
import hashlib
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, '_site'))
PWA = os.path.join(ROOT, 'app/pwa')
DIST = os.path.join(ROOT, 'app/dist')

body = open(os.path.join(DIST, 'index.html'), encoding='utf-8').read()
build = hashlib.sha1(body.encode()).hexdigest()[:10]
head = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="A Taiwanese (Taigi) course in English for people who speak Mandarin.">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" sizes="192x192" href="icon-192.png?v=2">
<link rel="apple-touch-icon" href="apple-touch-icon.png?v=2">
<meta name="theme-color" content="#FCFCF8">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="冊櫥">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<style>html,body{margin:0;padding:0}*{box-sizing:border-box}</style>
</head><body>
'''
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(head + body + '\n</body></html>\n')
for f in os.listdir(PWA):
    if f == 'sw.js':
        open(os.path.join(OUT, f), 'w').write(open(os.path.join(PWA, f)).read().replace('__BUILD__', build))
    else:
        shutil.copy(os.path.join(PWA, f), OUT)
if os.path.exists(os.path.join(DIST, 'record.html')):
    shutil.copy(os.path.join(DIST, 'record.html'), OUT)
REC = os.path.join(ROOT, 'course/audio/lessons')
if os.path.isdir(REC):
    shutil.copytree(REC, os.path.join(OUT, 'audio/lessons'), dirs_exist_ok=True)
if os.path.isdir(os.path.join(DIST, 'audio')):
    shutil.copytree(os.path.join(DIST, 'audio'), os.path.join(OUT, 'audio'), dirs_exist_ok=True)
open(os.path.join(OUT, '.nojekyll'), 'w').close()
print(f'{os.path.relpath(OUT, ROOT)}: installable site, build {build}')

"""Import a zip sent from the recording page (record.html) into the course.

  python3 tools/import_recordings.py tshehtu-recordings-….zip [--force]

For each clip: trims the silence at both ends, evens out the loudness, converts to mono MP3
-> course/audio/lessons/L057-03.mp3, and records speaker and date in course/audio/recordings.yaml.
An existing clip is kept unless --force. Lines the speaker flagged (⚑) are listed at the end and saved in
course/audio/flags.yaml, so the text can be corrected.
"""
import json
import os
import subprocess
import sys
import tempfile
import zipfile

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'course/audio/lessons')
META = os.path.join(ROOT, 'course/audio/recordings.yaml')
FLAGS = os.path.join(ROOT, 'course/audio/flags.yaml')
FILTER = ('silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.12,areverse,'
          'silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.25,areverse,'
          'loudnorm=I=-18:TP=-2:LRA=9,apad=pad_dur=0.15')


def convert(src, dst):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-af', FILTER, '-ac', '1', '-ar', '32000',
                    '-c:a', 'libmp3lame', '-b:a', '64k', dst], check=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    force = '--force' in sys.argv
    if not args:
        sys.exit(__doc__)
    os.makedirs(OUT, exist_ok=True)
    meta = yaml.safe_load(open(META, encoding='utf-8')) if os.path.exists(META) else {}
    meta.setdefault('speakers', {})
    meta.setdefault('clips', {})
    flags = yaml.safe_load(open(FLAGS, encoding='utf-8')) if os.path.exists(FLAGS) else {}
    done = kept = 0
    for path in args:
        with zipfile.ZipFile(path) as z, tempfile.TemporaryDirectory() as tmp:
            man = json.loads(z.read('manifest.json'))
            if man.get('app') != 'tshehtu-recordings':
                sys.exit(f'{path}: not a Tsheh-tû recordings zip')
            sp = man['speaker']
            meta['speakers'][sp] = {'use': man.get('use') or man.get('consent'), 'since': man.get('startedAt') or man.get('consentAt')}
            for c in man['clips']:
                if c.get('flag'):
                    flags[c['id']] = {'speaker': sp, 'hanji': c.get('hanji'), 'tailo': c.get('tailo'), 'note': c['flag']}
                if not c.get('file'):
                    continue
                dst = os.path.join(OUT, c['id'] + '.mp3')
                if os.path.exists(dst) and not force:
                    kept += 1
                    continue
                src = os.path.join(tmp, c['file'])
                with open(src, 'wb') as f:
                    f.write(z.read(c['file']))
                convert(src, dst)
                meta['clips'][c['id']] = {'speaker': sp, 'recorded': c.get('recordedAt', '')[:10]}
                done += 1
    yaml.safe_dump(meta, open(META, 'w', encoding='utf-8'), allow_unicode=True, sort_keys=True)
    if flags:
        yaml.safe_dump(flags, open(FLAGS, 'w', encoding='utf-8'), allow_unicode=True, sort_keys=True)
    print(f'{done} clip(s) imported, {kept} already there (use --force to replace)')
    for k, v in sorted(flags.items()):
        print(f'  ⚑ {k}  {v["hanji"]}  —  {v["note"]}')


if __name__ == '__main__':
    main()

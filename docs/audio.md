# Audio

## MOE recordings (headwords and example sentences)
Ministry of Education, CC BY-ND 3.0 TW: copied unaltered, never stored in git.
1. `python3 tools/fetch_audio.py --table` downloads the ministry's id table `kautian.ods` (needed first: the old
   entry numbers point to other words; see `tools/sutian.py`).
2. `make app` writes the lists `app/dist/audio-needed*.txt`.
3. `python3 tools/fetch_audio.py` downloads `sutiau-mp3.zip` (words) and `leku-mp3.zip` (sentences) and copies only
   the needed files to `app/dist/audio/{w,s}/`. Then `make app` again so cards get their ▶ button.
The workflow does all this and carries on without sound if the MOE site is unreachable.

## Native-speaker recordings
- `record.html` (published with the site) lets a speaker record dialogue lines on a phone and send a zip.
- `python3 tools/import_recordings.py file.zip [--force]` (needs ffmpeg) trims silence, normalises loudness, writes mono
  64 kbit/s MP3 to `course/audio/lessons/L057-03.mp3`, records speaker and date in `course/audio/recordings.yaml`,
  and saves flagged lines in `course/audio/flags.yaml`.
- These clips are **committed** (`.gitignore` has an exception for `course/audio/lessons/*.mp3`). They are not under the
  course licence: used with the speaker's permission in this app only (`LICENSE-CONTENT.md`).

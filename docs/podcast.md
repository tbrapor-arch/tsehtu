# Podcast tab

Show: 《隔壁 ê 戇人》 (Keh-piah ê gōng-lâng), hosted on SoundOn. Rights stay with the hosts; nothing is copied or re-hosted.

- `tools/fetch_podcast.py` saves the RSS feed to `data/raw/podcast/feed.xml` (git-ignored). The workflow runs it
  before `make app` with `continue-on-error`; without the feed the tab shows an empty message.
- `tools/podcast.py` parses each item: `00:05 Taigi text（Mandarin）` lines become chapters; the 「臺語補給站」 section
  (`漢字 tâi-lô ➡️ explanation`, also several words per line and labelled groups) becomes the word list; 「勘誤」 lines
  become corrections; links and footers are dropped. `tools/fixtures/podcast-sample.xml` is a test sample.
- `build_app.py` links word-list entries to dictionary cards when the Tâi-lô exists in the database.
- The player (`app/index.template.html`, podcast section) plays from SoundOn's URL: chapters, A/B loop, resume
  position, floating controls when the player is scrolled away.
- Machine transcripts of episodes are not part of this repo (private).

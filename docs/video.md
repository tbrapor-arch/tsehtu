# Video tab

Shows published free by their broadcaster on its own YouTube channel. First show: 《市井豪門》 Billionaire Story
(FTV 民視, 2022–23, 281 episodes of about 1 h 20 min, channel @FTVDRAMA). Rights stay with the broadcaster; nothing is
copied or re-hosted.

- `course/video.yaml`: per show `id`, `title`, `en`, `by`, `channel`, `total`, `about`, and the episodes that are listed
  (`n`, YouTube `video` id, `title`, `dur` in seconds). An episode is added when it is worked on (市井豪門 EP1–2, 願望 EP1 so far); the tab appears only
  when at least one show is listed. `build_app.py` copies the file into the app data as `video`.
- Routes: `#video` (list, with progress), `#vid-<show>-<n>` (episode).
- Player: YouTube IFrame API (`youtube-nocookie.com`), loaded only when an episode page opens; needs the internet.
  Own controls under the picture: back 5 s, play, forward 10 s, speed (0.75 / 1 / 1.25), A–B loop. The position is
  saved in the browser every 4 s (`vid` in local storage) and resumed; an episode counts as watched at 97 %. Playing
  a video pauses the podcast.
- Layout: on screens 1100 px and wider, two columns (picture, controls and notes on the left, staying in place;
  transcript on the right, `#vidside`). Narrower, one column, and once the player is scrolled up out of view the
  picture floats at the top of the screen (× puts it back until the player has been seen again).
- The on-screen subtitles are Mandarin wording, not the Taigi said.
- Hook for the private module (same pattern as the podcast): it can override `showVideo` / `showVideoEp`, read
  `vidTime()`, call `vidSeek(t, play)`, put a transcript in `#vidside`, and use `vidInset()` (height hidden by the floating picture). Machine transcripts of episodes are
  not part of this repo.

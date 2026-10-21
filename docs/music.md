# Music tab

Taigi songs played from the artist's own YouTube channel (official music videos), in the same embedded player as the
Video tab. First album: 《樹枝孤鳥》 Lonely Tree, Lonely Bird (伍佰 & China Blue, 1998). Rights stay with the artist
and label; nothing is copied or re-hosted, and no lyrics are kept in this repo.

- `course/music.yaml`: per album `id`, `title`, `en`, `by`, `year`, `channel`, `about`, and its songs (`n` = track
  number on the album, YouTube `video` id, `title`, `en`, optional `dur`, optional `key` = name of the private lyrics
  file). The tab appears only when at least one album is listed. `build_app.py` copies the file into the app data as
  `music`. Songs without an official music video are not listed yet.
- Routes: `#music` (album list), `#mus-<album>-<n>` (song). Progress and position share the Video tab's `vid` store
  (keys `mus-<album>-<n>`).
- Player page: `vidPage(S, ep, o)` is shared with the Video tab (`showVideoEp` and `showSong` only pass their labels,
  back route and notes).
- Hook for the private module, as for the drama: it can override `showMusic` / `showSong` and put the lyrics in
  `#vidside`. The private repo times the lyrics by forced alignment (Demucs + MMS), so the highlight follows each
  sung syllable; doubtful lines can be re-timed on the device.

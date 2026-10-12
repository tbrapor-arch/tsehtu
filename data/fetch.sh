#!/bin/sh
# Download the open data sources into data/raw at pinned commits.
# Nothing in data/raw is committed to this repo (see .gitignore and ATTRIBUTION.md).
set -e
cd "$(dirname "$0")"
mkdir -p raw
fetch() { # name url commit
  if [ ! -d "raw/$1/.git" ]; then
    git clone --quiet --filter=blob:none "$2" "raw/$1"
  fi
  git -C "raw/$1" fetch --quiet --depth 1 origin "$3" 2>/dev/null || true
  git -C "raw/$1" -c advice.detachedHead=false checkout --quiet "$3"
  echo "ok  $1 @ $(git -C "raw/$1" rev-parse --short HEAD)"
}
fetch moedict-data-twblg       https://github.com/g0v/moedict-data-twblg.git              4626bfcfccd6087496d14aac702b5e8a6a82e974
fetch ChhoeTaigiDatabase       https://github.com/ChhoeTaigi/ChhoeTaigiDatabase.git       b33c6a1fcc2d11a2962e76b6055d528d11677c3b
fetch Ungian_2009_KIPsupin     https://github.com/Taiwanese-Corpus/Ungian_2009_KIPsupin.git 9dc2c0bc516e731ff2ed7ee56f04b0dcf12bcac3
fetch complete-hsk-vocabulary  https://github.com/drkameleon/complete-hsk-vocabulary.git  7ac65bf1a6387d35f1ade478906172a19311c7f9

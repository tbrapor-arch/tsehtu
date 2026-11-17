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

# Plangothic (SIL OFL 1.1) webfont chunks: glyphs for Taigi-only characters (𠢕, 𪜶, 𨑨…) that
# common Chinese fonts lack. build_app.py embeds only the glyphs the app uses.
if [ ! -d raw/plangothic/package ]; then
  mkdir -p raw/plangothic
  (cd raw/plangothic && npm pack @free-fonts/plangothic@1.0.0 --silent >/dev/null && tar xzf free-fonts-plangothic-1.0.0.tgz)
fi
echo "ok  plangothic @ 1.0.0"

# CC-CEDICT (CC BY-SA 4.0) as JSON: pinyin and English for the Mandarin equivalents shown in the app.
if [ ! -f raw/cedict/package/cedict.json ]; then
  mkdir -p raw/cedict
  (cd raw/cedict && npm pack cedict-json@1.3.20251213 --silent >/dev/null && tar xzf cedict-json-1.3.20251213.tgz)
fi
echo "ok  cedict-json @ 1.3.20251213"

# jieba's dictionary and idf weights (MIT, fxsjy/jieba at a pinned commit): word frequencies to cut Mandarin texts
# into words (tools/zh_words.py). Checked against their SHA-256.
JIEBA=67fa2e36e72f69d9134b8a1037b83fbb070b9775
mkdir -p raw/jieba
for f in dict.txt:7197c3211ddd98962b036cdf40324d1ea2bfaa12bd028e68faa70111a88e12a8 \
         analyse/idf.txt:501b70ec56c34d90f3f590f1918ca4b1bd617d5b46cd99bd6d17c7de6e4f80ed; do
  n=${f%%:*}; h=${f##*:}; out=raw/jieba/$(basename "$n")
  if [ ! -f "$out" ] || ! echo "$h  $out" | sha256sum -c --quiet - 2>/dev/null; then
    curl -sSfL -o "$out" "https://raw.githubusercontent.com/fxsjy/jieba/$JIEBA/jieba/$n"
    echo "$h  $out" | sha256sum -c --quiet -
  fi
done
echo "ok  jieba @ $(echo $JIEBA | cut -c1-7)"

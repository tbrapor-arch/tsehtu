# Porting ledger

tsehtu is the lead app. Fixes and improvements land here first, then get ported to the other apps one by one.

## Rules

1. One change per commit. Never mix a portable fix with Taigi-only content or styling.
2. Prefix portable commits with `[port]` in the commit message.
   Example: `[port] fix audio not resuming after screen lock`
3. Add a row to the ledger below for every `[port]` commit.
4. Port in batches (weekly, or when you next open that app), not after every commit.
5. Port with the prompt in `PORTING_PROMPT.md`, test in the target app, then update the ledger.

## Status codes

- `todo`  not ported yet
- `done`  ported and tested (add the target commit hash if useful)
- `skip`  deliberately not ported (say why in Notes)
- `n/a`   the feature does not exist in that app

## List pending ports

```bash
git log --oneline --grep='^\[port\]'
```

## Ledger

Rename or remove columns to match your repos.

| Date | tsehtu commit | Change | pyue | sy-zy | Hkka | reader | chengyu-classical | arabe | Notes |
|------|---------------|--------|------|-------|------|--------|-------------------|-------|-------|
| 2026-11-17 | `ccd8497`, `64e0aa3` | Mandarin words, second version: jieba-frequency cut (integer score per word in `DATA.zh`, same DP in `zhCut`), readings per sentence (`DATA.zhx` exceptions, `data-r`), sheet with the reading here on top and other readings below; `zhAdd({qt, w, x})` for a private module's extra words | todo | todo | todo | todo | todo | todo | Needs data/raw/jieba (data/fetch.sh) and pypinyin; port after 3754579; `rule()` is Mandarin-only, the same in every app |
| 2026-11-17 | `3754579` | Mandarin text tappable everywhere: one cut + word table at build (`tools/zh_words.py`, `DATA.zh`), one renderer `zhLine()` + delegated handler opening the 華語 · Mandarin sheet (pinyin + CC-CEDICT, back to the card) | todo | todo | todo | todo | todo | todo | Needs CC-CEDICT + complete-hsk-vocabulary in data/raw; for Hkka/pyue the Hakka reader's per-page copy can be replaced; check where Mandarin is shown in each app |
| 2026-11-10 | `348aebb` | Pages reached from Practice (Characters) and the old accents link map to a tab in `currentTab()`, so a redrawn tab bar keeps its highlight | todo | todo | todo | todo | todo | todo | Only applies where the app has a hash-to-tab mapping like `currentTab()`; check every route has an entry |

## Structural differences to remember

Keep a short note per app on where it differs from tsehtu, so ports go faster next time.

- **pyue**:
- **sy-zy**:
- **Hkka**:
- **reader**:
- **chengyu-classical** (one shared app, both features): 
- **arabe**: right-to-left text. Public engine, private content: the same public/private split as the other apps.

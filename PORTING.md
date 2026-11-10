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
| 2026-11-10 | `348aebb` | Pages reached from Practice (Characters) and the old accents link map to a tab in `currentTab()`, so a redrawn tab bar keeps its highlight | todo | todo | todo | todo | todo | todo | Only applies where the app has a hash-to-tab mapping like `currentTab()`; check every route has an entry |

## Structural differences to remember

Keep a short note per app on where it differs from tsehtu, so ports go faster next time.

- **pyue**:
- **sy-zy**:
- **Hkka**:
- **reader**:
- **chengyu-classical** (one shared app, both features): 
- **arabe**: right-to-left text. Public engine, private content: the same public/private split as the other apps.

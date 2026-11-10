# Porting prompt for Claude Code

Run this from inside the **target** app's repo. Replace the two placeholders.

## 1. Get the diff from tsehtu

```bash
git -C ../tsehtu show <COMMIT_HASH> > /tmp/port.diff
```

For several commits at once:

```bash
git -C ../tsehtu show <HASH1> <HASH2> <HASH3> > /tmp/port.diff
```

## 2. Prompt

```
I maintain several language-course apps that started from the same structure
but have drifted apart. tsehtu (Taigi) is the lead app; this repo is another
app in the family.

The file /tmp/port.diff contains a change made in tsehtu. Port the same change
to this repo.

Rules:
- Port the intent of the change, not the literal lines. File names, folder
  layout and function names here may differ; find the equivalent code first.
- Do not touch anything language-specific: romanisation, tone handling,
  fonts, content files, glossary data. If the diff includes Taigi-specific
  parts, leave them out and tell me.
- Do not refactor or tidy unrelated code. Smallest change that achieves the
  same behaviour.
- If the feature the diff modifies does not exist here, stop and tell me
  instead of building it.
- If something in this repo makes the change risky or ambiguous, stop and ask.

Before editing, tell me in a few lines:
1. what the tsehtu change does,
2. which files here are the equivalents,
3. anything you will skip and why.

Then make the change, run the build/tests if there are any, and finish with a
one-line commit message starting with "port(tsehtu <COMMIT_HASH>):".
```

## 3. After

- Test the change in the app.
- Update the row in tsehtu's `PORTING.md` (`done`, `skip` or `n/a`).
- If the port revealed a structural difference, add it to the notes section of the ledger.

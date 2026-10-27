# Sync between devices, and the optional private module

## Sync
App: https://tbrapor-arch.github.io/tsehtu/ (Settings › Sync between devices; hosted app only).
1. GitHub › Settings › Developer settings › Fine-grained tokens › Generate. Name `tsehtu sync`; set an expiry and a reminder.
2. Account permissions › **Gists: Read and write**. Nothing else is needed for sync alone.
3. Paste the token on each device and press Connect. The app finds or creates a secret gist `tshehtu-progress.json`
   and merges when it opens and a few seconds after each change. Merge: earliest finish date per lesson, latest review per card.
4. The token stays in that browser and goes only to GitHub. Expired token: Settings shows "token refused"; make a new one.
5. Backup without GitHub: Settings › Save / Load progress file.

## Optional private module (generic)
The app can load an extra module from a private GitHub repo. The tab appears only on a device whose saved token can
read that repo; nothing of the module is in this repo or in the published page. For that use the token also needs
**Contents: Read** on the private repo (a token for sync alone is not enough).
Loader contract (`Exam` object in `app/index.template.html`): the repo's `exam/index.json` lists files with content
hashes; `app.css` and `app.js` are fetched through the GitHub API, cached in the browser by hash (works offline), and
`window.ExamModule.init(loader)` / `.route(hash)` are called. `app/pwa/sw.js` leaves `api.github.com` alone.
Keep this document generic: do not describe the module's content here.

## Content Security Policy
`tools/site.py` puts a CSP in the published page: only the page's own inline script (by hash, recomputed at each
build), `blob:` scripts (the module), YouTube's player API and GitHub's API are allowed. The module must therefore not
rely on `eval`, inline `<script>` or `on…=` attributes. A new outside source (script, API, frame) has to be added to
the list in `tools/site.py`, or the browser refuses it.

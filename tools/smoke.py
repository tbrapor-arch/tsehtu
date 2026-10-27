"""Click through the built app in a phone-sized browser and report problems.

  python3 tools/smoke.py [app/dist/index.html] [--shots DIR]

Checks: JS errors, horizontal overflow, every lesson renders, every word token and new-word chip opens a card,
every note opens, exercises answer, review session runs, themes / bridge / settings render.
"""
import os
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith('--') and sys.argv[i - 1] != '--shots']
PAGE = os.path.abspath(args[0] if args else os.path.join(ROOT, 'app/dist/index.html'))
SHOTS = sys.argv[sys.argv.index('--shots') + 1] if '--shots' in sys.argv else None
problems = []


def p(msg):
    problems.append(msg)
    print('PROBLEM', msg)


def overflow(page, where):
    w = page.evaluate('document.documentElement.scrollWidth - window.innerWidth')
    if w > 1:
        bad = page.evaluate('''() => [...document.querySelectorAll('#main *')].filter(e => e.getBoundingClientRect().right > window.innerWidth + 1
            && !e.closest('.vwrap,.tw,pre')).slice(0, 3).map(e => e.tagName + '.' + e.className + ' ' + (e.textContent || '').slice(0, 30))''')
        p(f'{where}: page scrolls sideways by {w}px {bad}')


with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2)
    page.on('pageerror', lambda e: p(f'JS error: {e}'))
    page.on('console', lambda m: m.type == 'error' and 'fonts.g' not in m.text and 'ERR_' not in m.text and p(f'console: {m.text}'))
    page.route('**/fonts.googleapis.com/**', lambda r: r.abort())
    page.route('**/fonts.gstatic.com/**', lambda r: r.abort())
    page.goto('file://' + PAGE)
    page.wait_for_selector('.lgrid')
    overflow(page, 'lessons')
    if SHOTS:
        os.makedirs(SHOTS, exist_ok=True)
        page.screenshot(path=f'{SHOTS}/lessons.png')
    ids = page.evaluate('DATA.lessons.map(l => l.id)')
    for lid in ids:
        page.evaluate(f"location.hash = 'lesson-{lid}'")
        page.wait_for_selector('.lines')
        overflow(page, f'lesson {lid}')
        n_lines = page.evaluate(f'DATA.lessons.find(l => l.id === {lid}).lines.length')
        if page.locator('.sent').count() != n_lines:
            p(f'lesson {lid}: {page.locator(".sent").count()} lines shown, {n_lines} in data')
        # every token opens a card with content
        toks = page.locator('.lines .tok')
        for i in range(toks.count()):
            t = toks.nth(i)
            t.click()
            if i == 0:
                page.wait_for_timeout(350)
            ok = page.evaluate("document.getElementById('sheet').classList.contains('open') && document.querySelector('#sheet .wc-h') !== null")
            if not ok:
                p(f'lesson {lid}: token {i} "{t.inner_text()}" did not open a card')
            # the close button must stay visible after scrolling the sheet
            if i == 0:
                page.evaluate("document.getElementById('sheet').scrollTop = 9999")
                vis = page.evaluate("(() => { const r = document.querySelector('#sheet .x').getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight; })()")
                if not vis:
                    p(f'lesson {lid}: close button scrolled out of view')
            page.keyboard.press('Escape')
        unknown = page.evaluate("[...document.querySelectorAll('.lines .tok')].filter(t => { const w = TOKS[t.dataset.tok]; return !w.id; }).map(t => t.textContent)")
        if unknown:
            print(f'  lesson {lid}: words without a card: {unknown}')
        chips = page.locator('[data-word]')
        for i in range(chips.count()):
            chips.nth(i).click()
            if not page.evaluate("document.querySelector('#sheet.open .wc-gloss, #sheet.open .wc-sec') !== null"):
                p(f'lesson {lid}: new word {i} card is empty')
            page.keyboard.press('Escape')
        notes = page.locator('.under [data-note]')
        for i in range(notes.count()):
            notes.nth(i).click()
            if not page.evaluate("document.querySelector('#sheet.open .note-body') !== null"):
                p(f'lesson {lid}: note button {i} did not open')
            page.keyboard.press('Escape')
        # exercises: show answer, then type the answer and check
        for f in page.locator('form[data-ex]').all():
            k = f.get_attribute('data-ex')
            ans = page.evaluate(f'DATA.lessons.find(l => l.id === {lid}).exercises[{k}].answer')
            f.locator('input').fill(ans)
            f.locator('button[type=submit]').click()
            if 'ok' not in (page.locator(f'#fb-{k}').get_attribute('class') or ''):
                p(f'lesson {lid}: exercise {k} rejects its own answer "{ans}"')
        if SHOTS and lid in (1, 50):
            page.evaluate('window.scrollTo(0,0)')
            page.screenshot(path=f'{SHOTS}/lesson{lid}.png')
    # finish a lesson, review
    page.evaluate("location.hash = 'lesson-1'")
    page.wait_for_selector('#mark')
    page.click('#mark')
    page.evaluate("location.hash = 'review'")
    page.wait_for_selector('.segs')
    overflow(page, 'review')
    # 'Review N' only shows when cards are due; marking a lesson no longer fills the deck, so fall back to 'Practise all'
    due = page.locator('[data-study="L1"][data-mode="due"]')
    (due if due.count() else page.locator('[data-study="L1"][data-mode="all"]')).click()
    for _ in range(40):
        if page.locator('#flip').count():
            page.click('#flip')
        elif page.locator('#good').count():
            page.click('#good')
        else:
            break
    if not page.locator('text=Done').count() and not page.locator('text=好勢').count():
        p('review session did not finish')
    page.evaluate("location.hash = 'lessons'")
    page.wait_for_selector('.nextcard')
    if '2' not in page.locator('.nextcard .nc-n').inner_text():
        p('home: next lesson card does not point to lesson 2 after finishing lesson 1')
    if not page.locator('.journal li').count():
        p('home: journal is empty after finishing a lesson')
    page.evaluate("location.hash = 'wave-1'")
    page.wait_for_selector('[data-tw]')
    if page.locator('.nlink').count():
        p('wave page shows note buttons')
    page.click('#show-all')
    if page.locator('[data-tw]').count():
        p('wave: Show all the Taigi left lines hidden')
    page.click('#mark')
    if page.evaluate("(JSON.parse(localStorage.getItem('tshehtu:prefs')) || {}).active"):
        p('wave turned on active mode for every lesson')
    page.evaluate("location.hash = 'lesson-2'")
    page.wait_for_selector('#dlg')
    if page.locator('.en.act').count():
        p('lesson 2 opens in active mode after doing a wave')
    if 'SamSam' in page.inner_text('#dlg'):
        p('names are written twice')
    f = page.locator('form[data-ex]').first
    if f.count():
        k = f.get_attribute('data-ex')
        ans = page.evaluate(f'DATA.lessons.find(l => l.id === 2).exercises[{k}].answer')
        num = page.evaluate(f'toneKey({ans!r})').replace(' ', '-')
        f.locator('input').fill(num)
        f.locator('button[type=submit]').click()
        if 'ok' not in (page.locator(f'#fb-{k}').get_attribute('class') or ''):
            p(f'exercise rejects tone numbers "{num}" for "{ans}"')
    page.keyboard.press('ArrowRight')
    page.wait_for_timeout(150)
    if page.evaluate('location.hash') != '#lesson-3':
        p('ArrowRight does not go to the next lesson')
    # grammar sheets
    page.evaluate("location.hash = 'grammar'")
    page.wait_for_selector('.gitem')
    overflow(page, 'grammar')
    n_items = page.locator('.gitem').count()
    for gi in range(n_items):
        page.evaluate("location.hash = 'grammar'")
        page.wait_for_selector('.gitem')
        page.locator('.gitem').nth(gi).click()
        page.wait_for_selector('.lbar')
        overflow(page, f'grammar sheet {gi}')
        if page.locator('.lines .tok').count():
            page.locator('.lines .tok').first.click()
            if not page.evaluate("document.getElementById('sheet').classList.contains('open')"):
                p(f'grammar sheet {gi}: word does not open')
            page.keyboard.press('Escape')
    # tone practice (Practice tab, Drills): answer 10, check the end screen
    page.click('.tab[data-tab=review]')
    page.evaluate("location.hash = 'drills'")
    page.wait_for_selector('#tones')
    page.click('#tones')
    for _ in range(10):
        page.wait_for_selector('[data-topt]')
        page.locator('[data-topt]').first.click()
        page.click('#tnext')
    if not page.locator('#again10').count():
        p('tone practice did not reach its end screen')
    page.evaluate("location.hash = 'lessons'")
    for h in ('themes', 'grammar', 'drills', 'bridge', 'podcast', 'video', 'settings', 'lesson-0'):
        page.evaluate(f"location.hash = '{h}'")
        page.wait_for_timeout(150)
        overflow(page, h)
        if SHOTS:
            page.screenshot(path=f'{SHOTS}/{h}.png')
    for t in page.evaluate('DATA.themes.map(t => t.id)'):
        page.evaluate(f"location.hash = 'theme-{t}'")
        page.wait_for_selector('.vtable')
        overflow(page, 'theme ' + t)
    page.evaluate("location.hash = 'bridge'")
    page.wait_for_selector('.opt')
    page.click('.opt')
    if not page.locator('.explain').count():
        p('bridge: answering shows no explanation')
    b.close()

print(f'\n{len(problems)} problem(s)')
sys.exit(1 if problems else 0)

// Offline support for the installed app. The page itself: network first (new lessons arrive as soon as you are
// online), the copy in the cache when offline. Recordings, icons and fonts: cache first, kept once played or loaded.
const VERSION = '__BUILD__';
const SHELL = 'tshehtu-shell-' + VERSION, MEDIA = 'tshehtu-media-2';
const PRECACHE = ['./', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'apple-touch-icon.png'];
const ROOT = new URL('./', self.registration.scope).pathname;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => (k.startsWith('tshehtu-shell-') && k !== SHELL) || (k.startsWith('tshehtu-media-') && k !== MEDIA)).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

// a cached recording answers the byte range the player asks for (Safari plays audio only from 206 range replies)
async function ranged(req, res) {
  const m = /^bytes=(\d*)-(\d*)$/.exec(req.headers.get('range') || '');
  if (!m || res.status !== 200) return res;
  const buf = await res.arrayBuffer(), size = buf.byteLength;
  let start = m[1] === '' ? Math.max(0, size - +m[2]) : +m[1];
  let end = m[1] !== '' && m[2] !== '' ? Math.min(+m[2], size - 1) : size - 1;
  if (start >= size || start > end) return new Response(null, { status: 416, headers: { 'Content-Range': `bytes */${size}` } });
  return new Response(buf.slice(start, end + 1), { status: 206, statusText: 'Partial Content', headers: {
    'Content-Type': res.headers.get('Content-Type') || 'audio/mpeg', 'Content-Range': `bytes ${start}-${end}/${size}`,
    'Content-Length': String(end - start + 1), 'Accept-Ranges': 'bytes' } });
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (req.mode === 'navigate') {
    // only the app page itself becomes the offline copy (not record.html, nor an error page)
    const app = url.origin === location.origin && (url.pathname === ROOT || url.pathname === ROOT + 'index.html');
    e.respondWith(fetch(req).then(r => {
      if (app && r.ok) { const copy = r.clone(); e.waitUntil(caches.open(SHELL).then(c => c.put('./', copy))); }
      return r;
    }).catch(() => caches.match(app ? './' : req).then(hit => hit || caches.match('./'))));
    return;
  }
  if (url.hostname === 'api.github.com') return;   // private exam files: the page caches those itself
  const audio = url.origin === location.origin && /\/audio\/.*\.mp3$/.test(url.pathname);
  if (audio) {   // kept whole under its URL (a range request would only give part of it), then cut to the range asked
    e.respondWith(caches.open(MEDIA).then(async c => {
      let hit = await c.match(url.href);
      if (!hit) {
        const r = await fetch(url.href);
        if (r.status !== 200) return r;
        e.waitUntil(c.put(url.href, r.clone()));
        hit = r;
      }
      return ranged(req, hit);
    }).catch(() => fetch(req)));
    return;
  }
  const media = /fonts\.(googleapis|gstatic)\.com$/.test(url.hostname) || /\.png$/.test(url.pathname);
  if (media) {
    e.respondWith(caches.open(MEDIA).then(c => c.match(req).then(hit => hit || fetch(req).then(r => { if (r.status === 200 || r.type === 'opaque') e.waitUntil(c.put(req, r.clone())); return r; }))));
  }
});

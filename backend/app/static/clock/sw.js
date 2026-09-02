// Service worker for Apex Clock.
//
// Caches the shell only — never a punch. Queueing punches offline would mean
// trusting a device-supplied timestamp, which is the easiest attendance fraud
// there is; the server stamps every punch with its own clock, so a punch that
// cannot reach the server simply has not happened yet.
const SHELL = 'apex-clock-shell-v5';
const ASSETS = ['./', './index.html', './manifest.webmanifest'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(SHELL).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== SHELL).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  // API traffic is always live. Serving a cached punch response would tell an
  // employee they had clocked in when they had not.
  if (url.pathname.startsWith('/api/')) return;
  e.respondWith(caches.match(e.request).then((hit) => hit || fetch(e.request)));
});

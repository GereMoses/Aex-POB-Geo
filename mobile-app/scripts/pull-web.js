/**
 * Copy the clock page out of the backend into the Capacitor web root.
 *
 * The same page is served at /clock/ for browser pilots and packaged here for
 * the store build, so there is one UI to maintain rather than two that drift
 * apart.
 */
const fs = require('fs');
const path = require('path');

const SRC = path.resolve(__dirname, '../../backend/app/static/clock');
const DST = path.resolve(__dirname, '../www');
const FILES = ['index.html', 'app.css', 'app.js', 'config.js',
               'manifest.webmanifest', 'icon-192.png', 'icon-512.png'];

fs.mkdirSync(DST, { recursive: true });
for (const f of FILES) {
  const from = path.join(SRC, f);
  if (!fs.existsSync(from)) {
    console.error(`missing: ${from}`);
    process.exit(1);
  }
  fs.copyFileSync(from, path.join(DST, f));
}
// The service worker belongs to the browser build only. Inside the app the
// assets are already local, and a stale cache would be a way to pin an old
// build on a handset.
fs.rmSync(path.join(DST, 'sw.js'), { force: true });
// Point the packaged app at a real backend. Inside Capacitor the page is
// served from a local scheme, so location.origin is not the server and the
// address has to be baked in. Set APEX_API_BASE when building.
const apiBase = process.env.APEX_API_BASE || '';
if (apiBase) {
  const cfg = path.join(DST, 'config.js');
  fs.writeFileSync(cfg, `window.APEX_API_BASE = ${JSON.stringify(apiBase)};\n`);
  console.log(`API base set to ${apiBase}`);
} else {
  console.warn('APEX_API_BASE not set — the packaged app will have no backend to talk to.');
}
console.log(`copied ${FILES.length} files into www/`);

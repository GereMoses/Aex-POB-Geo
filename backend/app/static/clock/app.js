'use strict';
// Inside the native shell the page is served locally, so its own origin is not
// the backend; config.js supplies the real address there.
//
// A saved override wins over the baked-in value. The installed app hard-codes
// whatever address it was built against, so without this a server that moves
// leaves every handset needing a reinstall — the override lets a supervisor
// retype the address instead.
function apiBase() {
  let saved = '';
  try { saved = localStorage.getItem('apex.api') || ''; } catch (e) { /* private mode */ }
  return (saved || window.APEX_API_BASE || '').replace(/\/$/, '') || location.origin;
}
let API = apiBase();
const $ = (id) => document.getElementById(id);
const state = { token: null, sites: [], fix: null, buffer: [], pendingDirection: null,
                photo: null, employee: null, refreshTimer: null,
                noticeIsAssignment: false };

/* ── Geometry, mirroring the server so the button and the server agree ────── */
const R = 6371008.8;
function haversine(a, b, c, d) {
  const t = Math.PI / 180, p1 = a * t, p2 = c * t;
  const dp = p2 - p1, dl = (d - b) * t;
  const x = Math.sin(dp / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(x));
}
function nearest(fix, sites) {
  let best = null;
  for (const s of sites) {
    if (s.latitude == null) continue;
    const out = Math.max(0, haversine(fix.lat, fix.lng, s.latitude, s.longitude) - (s.radius_m || 0));
    if (!best || out < best.out) best = { site: s, out };
  }
  return best;
}
function likelyPasses(fix, site, out) {
  if (!site || out == null) return false;
  const acc = fix.acc ?? 0;
  if (acc > (site.gps_accuracy_max_m ?? 100)) return false;
  return out <= Math.min(acc, site.accuracy_buffer_cap_m ?? 50);
}

/* ── API ──────────────────────────────────────────────────────────────────── */
async function api(path, opts = {}) {
  const res = await fetch(API + path, {
    method: opts.method || 'GET',
    headers: {
      ...(opts.form ? { 'Content-Type': 'application/x-www-form-urlencoded' }
                    : { 'Content-Type': 'application/json' }),
      ...(state.token ? { Authorization: 'Bearer ' + state.token } : {}),
    },
    body: opts.form ? new URLSearchParams(opts.form).toString()
        : opts.body ? JSON.stringify(opts.body) : undefined,
  });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const detail = data && data.detail;
    const err = new Error(
      detail && typeof detail === 'object' ? detail.message
      : typeof detail === 'string' ? detail : 'Request failed (' + res.status + ')');
    err.status = res.status;
    err.reason = detail && detail.reason;
    throw err;
  }
  return data;
}

/* ── Location ─────────────────────────────────────────────────────────────── */
function watchLocation() {
  // Same secure-context rule applies to location.
  if (!window.isSecureContext) {
    return showNotice(
      'This page must be opened over HTTPS for location and camera to work. '
      + 'Ask your administrator for the secure address.', true);
  }
  if (!navigator.geolocation) {
    return showNotice('This browser cannot read your location. Use the Apex Clock app.', true);
  }
  navigator.geolocation.watchPosition(
    (pos) => {
      const c = pos.coords;
      state.fix = {
        lat: c.latitude, lng: c.longitude, acc: c.accuracy,
        // null, never 0 — the server treats an exact zero as a spoofing
        // sentinel, because real satellite fixes never land on it.
        alt: Number.isFinite(c.altitude) ? c.altitude : null,
        ts: new Date(pos.timestamp).toISOString(),
      };
      state.buffer.push({ ...state.fix, at: Date.now() });
      state.buffer = state.buffer.filter((f) => f.at > Date.now() - 5 * 60 * 1000);
      render();
    },
    (err) => showNotice(err.code === 1
      ? (isNative()
          ? 'Location permission was refused. Allow it for Apex Clock in your '
            + 'phone settings, then reopen the app.'
          : 'Location permission was refused. Allow it in your browser settings, '
            + 'then reload.')
      : 'Could not read your location. Move outside and try again.', true),
    { enableHighAccuracy: true, maximumAge: 0, timeout: 20000 },
  );
}

/* ── Rendering ────────────────────────────────────────────────────────────── */
function showNotice(msg, disable = false) {
  const n = $('notice');
  n.textContent = msg;
  n.classList.toggle('hide', !msg);
  if (disable) setEnabled(false);
}

function render() {
  const box = $('status');
  if (!state.fix) return;
  const near = nearest(state.fix, state.sites);
  if (!near) {
    box.className = 'card warn';
    box.innerHTML = '<div class="headline">No warehouse nearby</div>'
      + '<div class="muted">You are not close to a warehouse you are assigned to.</div>';
    setEnabled(false);
    return;
  }
  const ready = likelyPasses(state.fix, near.site, near.out);
  const dist = fmtDist(near.out);
  box.className = 'card ' + (ready ? 'ok' : 'warn');
  box.innerHTML =
    '<div class="site">' + esc(near.site.name) + '</div>'
    + '<div class="headline">' + (ready ? 'You are at the warehouse' : dist + ' outside the boundary') + '</div>'
    + '<div class="muted">' + (ready
        ? 'Location accurate to about ' + Math.round(state.fix.acc) + ' m'
        : 'Move closer to the warehouse to clock in.') + '</div>'
    // The exact target, so somebody who cannot get in can see precisely where
    // the app expects them to be rather than guessing.
    + '<div class="coords">Clock-in point '
      + coord(near.site.latitude) + ', ' + coord(near.site.longitude)
      + ' &middot; within ' + near.site.radius_m + ' m</div>'
    + '<div class="coords">You are at '
      + coord(state.fix.lat) + ', ' + coord(state.fix.lng)
      + ' &middot; \u00b1' + Math.round(state.fix.acc) + ' m</div>';
  setEnabled(ready);
  state.current = near.site;
  renderAssignments();
}

function esc(v) {
  return String(v == null ? '' : v).replace(/[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function coord(v) { return (v == null || isNaN(v)) ? '\u2014' : Number(v).toFixed(5); }
function fmtDist(m) {
  return m >= 1000 ? (m / 1000).toFixed(1) + ' km' : Math.round(m) + ' m';
}

/* Who is signed in — name and employee number. */
function renderWho() {
  const e = state.employee;
  if (!e) return $('whoami').classList.add('hide');
  $('whoName').textContent = e.name || e.emp_code;
  $('whoId').textContent = e.department
    ? e.emp_code + ' \u00b7 ' + e.department : e.emp_code;
  $('whoami').classList.remove('hide');
}

/* Every warehouse the employee may clock in at, with its exact coordinates,
   permitted radius, and how far away they currently are. */
function renderAssignments() {
  const wrap = $('assigned');
  const list = $('assignedList');
  if (!state.sites.length) return wrap.classList.add('hide');

  list.innerHTML = state.sites.map((site) => {
    let d = null;
    if (state.fix && site.latitude != null && site.longitude != null) {
      d = haversine(state.fix.lat, state.fix.lng, site.latitude, site.longitude)
          - (site.radius_m || 0);
    }
    const inside = d !== null && d <= 0;
    return '<div class="site-row' + (inside ? ' here' : '') + '">'
      + '<div class="nm">' + esc(site.name)
        + (site.is_primary ? ' \u00b7 main' : '') + '</div>'
      + '<div class="co">' + coord(site.latitude) + ', ' + coord(site.longitude)
        + ' \u00b7 within ' + (site.radius_m || 0) + ' m</div>'
      + '<div class="dd">' + (d === null ? 'Waiting for your location\u2026'
          : inside ? '<b>You are inside this boundary</b>'
                   : '<i>' + fmtDist(d) + ' away</i>') + '</div>'
      + '</div>';
  }).join('');
  wrap.classList.remove('hide');
}
function setEnabled(on) { $('clockIn').disabled = !on; $('clockOut').disabled = !on; }

/* ── Photo capture ────────────────────────────────────────────────────────── */
async function takePhoto() {
  // Camera and location are both gated behind a secure context. Served over
  // plain HTTP on a LAN address the browser removes these APIs entirely, and
  // the failure is silent unless we say so — worth naming precisely, because
  // "it does not work on my phone" is otherwise very hard to diagnose.
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    throw new Error(
      'The camera needs a secure connection. Open this page over HTTPS '
      + '(or on the device itself via localhost) and try again.');
  }
  const stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 640 } },
    audio: false,
  });
  const cam = $('cam');
  cam.srcObject = stream;
  await cam.play();

  // play() resolves when playback starts, which is before the first frame has
  // decoded — videoWidth is still 0 at that point, and drawing then yields an
  // empty image. Wait for real dimensions.
  await new Promise((ready) => {
    if (cam.videoWidth > 0) return ready();
    const t = setInterval(() => {
      if (cam.videoWidth > 0) { clearInterval(t); ready(); }
    }, 50);
    setTimeout(() => { clearInterval(t); ready(); }, 4000);
  });

  $('photoWrap').classList.remove('hide');
  $('controls').classList.add('hide');

  return new Promise((resolve, reject) => {
    const stop = () => stream.getTracks().forEach((t) => t.stop());
    $('capture').onclick = () => {
      const vw = cam.videoWidth;
      const vh = cam.videoHeight;
      if (!vw || !vh) {
        stop();
        $('photoWrap').classList.add('hide');
        $('controls').classList.remove('hide');
        return reject(new Error('The camera did not produce an image. Try again.'));
      }

      // The whole frame, not a centre crop. Face detection needs the head plus
      // surrounding context; cropping to a square zooms in on someone already
      // close to the camera and can cut the top of the head off, at which point
      // no detector will find a face at all.
      const longest = Math.max(vw, vh);
      const scale = Math.min(1, 720 / longest);
      const c = $('shot');
      c.width = Math.round(vw * scale);
      c.height = Math.round(vh * scale);
      c.getContext('2d').drawImage(cam, 0, 0, c.width, c.height);

      const data = c.toDataURL('image/jpeg', 0.85).split(',')[1] || '';
      stop();
      $('photoWrap').classList.add('hide');
      $('controls').classList.remove('hide');

      // A blank or truncated capture must not be sent: it would be stored as an
      // unreadable file and quietly leave the punch waiting on a review that
      // can never resolve.
      if (data.length < 2000) {
        return reject(new Error('The photo did not save properly. Try again.'));
      }
      resolve(data);
    };
    $('cancelPhoto').onclick = () => {
      stop();
      $('photoWrap').classList.add('hide');
      $('controls').classList.remove('hide');
      resolve(null);
    };
  });
}

/* ── Punch ────────────────────────────────────────────────────────────────── */
async function punch(direction) {
  showNotice('');
  if (!state.fix) return;
  setEnabled(false);
  try {
    let photo = null;
    if (state.current && state.current.require_selfie) {
      photo = await takePhoto();
      if (!photo) { render(); return; }
    }

    const recent = state.buffer.filter((f) => f.at > Date.now() - 15000);
    const trail = [];
    let last = 0;
    for (const f of state.buffer) {
      if (f.at - last >= 15000) { trail.push({ latitude: f.lat, longitude: f.lng, timestamp: f.ts }); last = f.at; }
    }

    const native = await nativeIntegrity();
    const res = await api('/api/v1/mobile/' + (direction === 'IN' ? 'check-in' : 'check-out'), {
      method: 'POST',
      body: {
        location: { latitude: state.fix.lat, longitude: state.fix.lng,
                    accuracy: state.fix.acc, altitude: state.fix.alt, timestamp: state.fix.ts },
        samples: recent.map((f) => ({ latitude: f.lat, longitude: f.lng, accuracy: f.acc, timestamp: f.ts })),
        approach_path: trail,
        selfie_base64: photo,
        // The server scores browser punches differently: a page cannot run
        // Play Integrity, App Attest or mock-location detection, so it must
        // not be able to pass itself off as the native app.
        client_type: native ? 'NATIVE' : 'PWA',
        device: native
          ? { ...native, app_version: 'app-1.0.0', device_id: deviceId() }
          : { platform: 'web', app_version: 'pwa-1.0.0',
              device_id: deviceId(), attestation_verdict: 'UNAVAILABLE' },
      },
    });
    const r = $('receipt');
    r.className = 'card ok';
    r.innerHTML = '<div class="headline">' + res.message + '</div>'
      + '<div class="muted">' + new Date(res.timestamp).toLocaleTimeString() + '</div>'
      + (res.photo_pending_review ? '<div class="muted">Your photo will be checked by your supervisor.</div>' : '');
  } catch (e) {
    if (e.status === 401) return signOut();
    // The server writes refusal messages for the employee; show them as-is
    // rather than inventing wording for a rule the client did not evaluate.
    showNotice(e.message);
  } finally {
    render();
  }
}

/* ── Native integrity ─────────────────────────────────────────────────────── */
/**
 * Collect device integrity signals when running inside the native shell.
 *
 * The same page runs in a browser and in the Capacitor app. In a browser none
 * of these APIs exist, so the punch is sent as a PWA and the server scores it
 * accordingly. In the app the native plugin answers, the punch is sent as
 * NATIVE, and it carries the attestation a browser could never produce.
 */
function isNative() {
  return !!(window.Capacitor && window.Capacitor.isNativePlatform
            && window.Capacitor.isNativePlatform());
}

async function nativeIntegrity() {
  if (!isNative()) return null;
  const plugin = window.Capacitor.Plugins && window.Capacitor.Plugins.ApexIntegrity;
  if (!plugin) return null;
  try {
    const [signals, attest] = await Promise.all([
      plugin.getSignals().catch(() => ({})),
      plugin.requestAttestation().catch(() => ({ token: 'UNAVAILABLE' })),
    ]);
    return {
      platform: window.Capacitor.getPlatform(),
      is_mock_location: !!signals.isMockLocationEnabled,
      is_rooted: !!signals.isCompromised,
      is_emulator: !!signals.isEmulator,
      attestation_verdict: attest.token || 'UNAVAILABLE',
    };
  } catch (e) {
    // Never let an integrity failure stop a punch — the server decides what a
    // missing signal is worth, and refusing here would strand somebody at the
    // gate over a plugin fault.
    return null;
  }
}

function deviceId() {
  let id = localStorage.getItem('apex.device');
  if (!id) { id = 'pwa-' + Math.random().toString(36).slice(2) + Date.now().toString(36);
             localStorage.setItem('apex.device', id); }
  return id;
}

/* ── Session ──────────────────────────────────────────────────────────────── */
async function signIn() {
  $('loginErr').classList.add('hide');

  // Authenticating and loading the employee's sites are separate failures and
  // must read differently. An administrator account signs in perfectly well but
  // has no employee record, so the sites call 403s — reporting that as "could
  // not sign in" sends people off checking a password that was never wrong.
  let res;
  try {
    res = await api('/api/v1/auth/login', {
      method: 'POST', form: { username: $('u').value.trim(), password: $('p').value },
    });
  } catch (e) {
    $('loginErr').textContent = e.status === 429
      ? 'Too many attempts. Wait a few minutes and try again.'
      : (e.message || 'Could not sign in. Check your employee code and password.');
    $('loginErr').classList.remove('hide');
    return;
  }

  state.token = res.access_token;
  localStorage.setItem('apex.token', state.token);

  try {
    await start();
  } catch (e) {
    state.token = null;
    localStorage.removeItem('apex.token');
    $('loginErr').textContent = e.status === 403
      ? 'That account is signed in, but it is not an employee account, so it cannot '
        + 'clock in. Use your own employee code — an administrator sign-in belongs '
        + 'in the web console.'
      : (e.message || 'Signed in, but your warehouses could not be loaded.');
    $('loginErr').classList.remove('hide');
  }
}
function signOut() {
  state.token = null;
  state.employee = null;
  state.sites = [];
  if (state.refreshTimer) { clearInterval(state.refreshTimer); state.refreshTimer = null; }
  $('whoami').classList.add('hide');
  $('assigned').classList.add('hide');
  localStorage.removeItem('apex.token');
  $('app').classList.add('hide');
  $('login').classList.remove('hide');
}
async function start() {
  await loadSites();
  $('login').classList.add('hide');
  $('app').classList.remove('hide');
  watchLocation();
  checkEnrolment();
  startSiteRefresh();
}

/*
 * Pull the assignment list and fence coordinates from the server.
 *
 * This used to run only at sign-in, so an administrator moving a fence or
 * reassigning somebody had no effect until that person signed out and back in —
 * the app went on measuring against the old coordinates and reported them
 * kilometres outside a boundary they were standing in.
 */
async function loadSites() {
  const res = await api('/api/v1/mobile/my-sites');
  state.sites = res.sites || [];
  state.employee = res.employee || null;
  renderWho();
  if (!state.sites.length) {
    showNotice('You are not assigned to a warehouse. Contact your supervisor.', true);
  } else if (state.noticeIsAssignment) {
    showNotice('');
  }
  state.noticeIsAssignment = !state.sites.length;
  renderAssignments();
  if (state.fix) render();
  return state.sites;
}

/*
 * Keep the fences current while the app is open: on a timer, and immediately
 * whenever the app comes back to the foreground — which is when somebody who
 * was just told "your warehouse has changed" will look at it.
 */
function startSiteRefresh() {
  if (state.refreshTimer) clearInterval(state.refreshTimer);
  const refresh = () => { if (state.token) loadSites().catch(() => {}); };
  state.refreshTimer = setInterval(refresh, 60000);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') refresh();
  });
  window.addEventListener('online', refresh);
}

/* ── Face registration ────────────────────────────────────────────────────── */

/*
 * Without a reference photo nothing can be compared against the punch selfie,
 * so every punch lands in the review queue and the attendance record proves
 * location but not identity. Offer the one-off registration up front rather
 * than leaving supervisors to chase it later.
 */
async function checkEnrolment() {
  try {
    const st = await api('/api/v1/mobile/face/status');
    if (st && st.can_self_enrol) $('enrolPrompt').classList.remove('hide');
  } catch (e) {
    // Never let this block clocking in — it is an enhancement, not a gate.
  }
}

async function enrolFace() {
  const btn = $('enrolNow');
  btn.disabled = true;
  try {
    const photo = await takePhoto();
    if (!photo) { btn.disabled = false; return; }
    $('enrolMsg').textContent = 'Saving your photo…';
    await api('/api/v1/mobile/face/enrol', {
      method: 'POST',
      body: { photo_base64: 'data:image/jpeg;base64,' + photo },
    });
    $('enrolPrompt').classList.add('hide');
    showNotice('Your photo has been registered.', false);
    setTimeout(() => $('notice').classList.add('hide'), 4000);
  } catch (e) {
    $('enrolMsg').textContent =
      (e && e.message) ? e.message : 'That photo could not be used. Try again.';
    btn.disabled = false;
  }
}

$('signin').onclick = signIn;
$('p').addEventListener('keydown', (e) => e.key === 'Enter' && signIn());
$('signout').onclick = signOut;
/* Manual refresh: pull the assignment list and fences again and re-read the
   position, so somebody told "your warehouse has changed" can see it without
   killing the app. The 60-second timer still runs; this is for impatience. */
async function manualRefresh() {
  const btn = $('refresh');
  const original = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Refreshing\u2026';
  try {
    await loadSites();
    // Ask for a fresh fix too — a cached one can be minutes old.
    if (navigator.geolocation) {
      await new Promise((done) => navigator.geolocation.getCurrentPosition(
        (pos) => {
          const c = pos.coords;
          state.fix = { lat: c.latitude, lng: c.longitude, acc: c.accuracy,
                        alt: Number.isFinite(c.altitude) ? c.altitude : null,
                        ts: new Date(pos.timestamp).toISOString() };
          render();
          done();
        },
        () => done(),
        { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }));
    }
    btn.textContent = 'Updated';
    setTimeout(() => { btn.textContent = original; btn.disabled = false; }, 1200);
  } catch (e) {
    btn.textContent = original;
    btn.disabled = false;
    showNotice(e.message || 'Could not refresh. Check your connection.');
  }
}

/* Server address — used when the backend moves and the installed app still
   points at the old one. */
function showServerNow() {
  let saved = '';
  try { saved = localStorage.getItem('apex.api') || ''; } catch (e) {}
  $('serverNow').textContent = 'Currently using ' + API + (saved ? ' (saved)' : ' (built in)');
  $('serverUrl').value = saved;
}
$('serverToggle').onclick = () => {
  const box = $('serverBox');
  box.classList.toggle('hide');
  if (!box.classList.contains('hide')) showServerNow();
};
$('serverSave').onclick = () => {
  const v = $('serverUrl').value.trim().replace(/\/$/, '');
  if (v && !/^https:\/\//i.test(v)) {
    $('loginErr').textContent = 'The address must start with https:// — the camera '
      + 'and location will not work otherwise.';
    $('loginErr').classList.remove('hide');
    return;
  }
  try { v ? localStorage.setItem('apex.api', v) : localStorage.removeItem('apex.api'); } catch (e) {}
  API = apiBase();
  $('loginErr').classList.add('hide');
  showServerNow();
};
$('serverReset').onclick = () => {
  try { localStorage.removeItem('apex.api'); } catch (e) {}
  API = apiBase();
  showServerNow();
};

$('refresh').onclick = manualRefresh;

/* Let people confirm a password they were handed on paper. */
$('pwToggle').onclick = () => {
  const f = $('p');
  const shown = f.type === 'text';
  f.type = shown ? 'password' : 'text';
  $('pwToggle').textContent = shown ? 'Show' : 'Hide';
  $('pwToggle').setAttribute('aria-label', shown ? 'Show password' : 'Hide password');
  f.focus();
};

$('enrolNow').onclick = enrolFace;
$('enrolLater').onclick = () => $('enrolPrompt').classList.add('hide');
$('clockIn').onclick = () => punch('IN');
$('clockOut').onclick = () => punch('OUT');

// The "install the app" note is meaningless once you are in the app.
if (isNative()) {
  const note = $('browserNote');
  if (note) note.classList.add('hide');
}

if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});
state.token = localStorage.getItem('apex.token');
if (state.token) start().catch(signOut);

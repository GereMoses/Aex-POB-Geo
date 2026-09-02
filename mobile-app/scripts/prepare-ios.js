#!/usr/bin/env node
/**
 * Apply the Apex-specific iOS configuration that `npx cap add ios` does not.
 *
 * Run after `npx cap add ios` (and after any `npx cap sync ios`, which can
 * regenerate parts of the project). Everything here is idempotent.
 *
 * Three things matter:
 *
 *  1. Usage-description strings. iOS kills the app the instant it touches the
 *     camera or location without one, and App Store review rejects the binary
 *     outright. The wording is what the employee sees in the permission
 *     dialog, so it explains the purpose rather than naming the API.
 *
 *  2. Location is requested WHEN IN USE only. The app reads position while the
 *     clock screen is open and never in the background; asking for "always"
 *     would be a larger privacy ask than the product needs and invites review
 *     questions we would have no good answer to.
 *
 *  3. The integrity plugin is compiled in. Capacitor discovers plugins in the
 *     app target, so the Swift/ObjC pair has to be copied into it.
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const APP_DIR = path.join(ROOT, 'ios', 'App');
const PLIST = path.join(APP_DIR, 'App', 'Info.plist');
const NATIVE = path.join(ROOT, 'native', 'ios');

if (!fs.existsSync(PLIST)) {
  console.error('Info.plist not found — run `npx cap add ios` first.');
  process.exit(1);
}

/* ── 1. Permission strings ─────────────────────────────────────────────────── */
const USAGE = {
  NSCameraUsageDescription:
    'Apex Clock takes a photo when you clock in so your supervisor can confirm it is you.',
  NSLocationWhenInUseUsageDescription:
    'Apex Clock checks you are at your assigned warehouse before allowing a clock-in. '
    + 'Your location is only read while the app is open.',
  NSPhotoLibraryAddUsageDescription:
    'Used only if you choose to save a copy of your clock-in photo.',
};

let plist = fs.readFileSync(PLIST, 'utf8');
let added = 0;
for (const [key, text] of Object.entries(USAGE)) {
  if (plist.includes(`<key>${key}</key>`)) continue;
  plist = plist.replace(
    /<dict>/,
    `<dict>\n\t<key>${key}</key>\n\t<string>${text}</string>`
  );
  added += 1;
}

/* Background location is deliberately NOT requested. If a previous run or a
   plugin added the background mode, strip it — shipping it unused is the kind
   of thing that stalls review. */
plist = plist.replace(
  /\s*<key>UIBackgroundModes<\/key>\s*<array>[\s\S]*?<\/array>/,
  ''
);

fs.writeFileSync(PLIST, plist);
console.log(`  Info.plist: ${added} usage description(s) added, background modes cleared`);

/* ── 2. Integrity plugin into the app target ───────────────────────────────── */
const target = path.join(APP_DIR, 'App');
let copied = 0;
for (const f of ['ApexIntegrityPlugin.swift', 'ApexIntegrityPlugin.m']) {
  const src = path.join(NATIVE, f);
  if (!fs.existsSync(src)) continue;
  const dst = path.join(target, f);
  const incoming = fs.readFileSync(src);
  if (!fs.existsSync(dst) || !fs.readFileSync(dst).equals(incoming)) {
    fs.writeFileSync(dst, incoming);
    copied += 1;
  }
}
console.log(`  integrity plugin: ${copied} file(s) copied into the app target`);

/* ── 3. App icon ───────────────────────────────────────────────────────────── */
const icon = path.join(NATIVE, 'assets', 'AppIcon-1024.png');
const iconSet = path.join(APP_DIR, 'App', 'Assets.xcassets', 'AppIcon.appiconset');
if (fs.existsSync(icon) && fs.existsSync(iconSet)) {
  fs.copyFileSync(icon, path.join(iconSet, 'AppIcon-512@2x.png'));
  console.log('  app icon: Apex mark installed (1024x1024, no alpha)');
}


/* ── 4. Compile the plugin into the App target ─────────────────────────────────
   Copying the files into the folder is not enough: Xcode compiles what the
   target's Sources build phase lists, and Capacitor discovers plugins by
   scanning the compiled binary for CAP_PLUGIN registrations. Doing this by
   hand in Xcode is a step that gets forgotten on every fresh clone, and the
   failure is silent — the app builds, the bridge simply reports no such
   plugin at runtime and every integrity signal comes back empty. */
const xcode = require('xcode');
const PBX = path.join(APP_DIR, 'App.xcodeproj', 'project.pbxproj');

if (!fs.existsSync(PBX)) {
  console.log('  target wiring: skipped (no project.pbxproj)');
} else {
  const proj = xcode.project(PBX);
  proj.parseSync();

  const unquote = (v) => String(v || '').replace(/^"|"$/g, '');

  // The App target, not the Pods targets.
  let targetUuid = null;
  const natives = proj.pbxNativeTargetSection();
  for (const [uuid, t] of Object.entries(natives)) {
    if (t && typeof t === 'object' && unquote(t.name) === 'App') { targetUuid = uuid; break; }
  }

  // Capacitor's template leaves this group unnamed — it is identified by its
  // path, so a lookup by name silently finds nothing.
  const groupKey = proj.findPBXGroupKey({ name: 'App' })
                || proj.findPBXGroupKey({ path: 'App' });

  // Which of our files does the project already reference?
  const refs = proj.pbxFileReferenceSection();
  const present = new Set(
    Object.values(refs)
      .filter((r) => r && typeof r === 'object')
      .map((r) => path.basename(unquote(r.path)))
  );

  if (!targetUuid || !groupKey) {
    console.log('  target wiring: SKIPPED — could not locate the App '
              + `${!targetUuid ? 'target' : 'group'}; add the plugin manually.`);
  } else {
    let wired = 0;
    for (const f of ['ApexIntegrityPlugin.swift', 'ApexIntegrityPlugin.m']) {
      if (!fs.existsSync(path.join(target, f))) continue;
      if (present.has(f)) continue;
      proj.addSourceFile(f, { target: targetUuid }, groupKey);
      wired += 1;
    }
    if (wired) {
      fs.writeFileSync(PBX, proj.writeSync());
      console.log(`  target wiring: ${wired} plugin file(s) added to the App target`);
    } else {
      console.log('  target wiring: already in the App target');
    }
  }
}

console.log('\n  Ready. Open with: npx cap open ios');

# Apex Clock — geofenced time clock for warehouse staff

React Native app for iOS and Android. Employees clock in and out from their own
phones over mobile data; a punch is refused unless the device is inside the
fence of a warehouse the employee is assigned to.

Backed by the geofence engine in `backend/app/services/geofence_service.py`.
See `docs/GEOFENCE_DEPLOYMENT.md` for the server side.

---

## What it does

- Signs in with the employee number
- Watches location **only while the clock screen is open**
- Shows fence status live, and disables the button when outside
- Captures a front-camera selfie where the site requires one
- Sends a burst of fixes and an approach trail so the server can detect spoofing
- Collects device integrity signals and a platform attestation

## What it deliberately does not do

- **No background location.** The button reads position when the screen is
  open, and at no other time. Continuous tracking would give nicer approach
  trails at the cost of asking warehouse staff for "Always Allow", tracking
  them off-shift, and defending that in app review.
- **No offline queue.** Punches require connectivity, which is what lets the
  server stamp them with its own clock. Offline queues accept a device-supplied
  time, which is the easiest attendance fraud there is.
- **No gallery access for the selfie.** Front camera only. A photo chosen from
  the camera roll would defeat the control entirely.

---

## Building

```bash
cd mobile
npm install
```

Set `API_BASE_URL` in `src/config.js` (or wire it to a Gradle product flavour /
Xcode xcconfig for per-environment builds).

### Android

```bash
npx react-native run-android
```

Two manual steps the generated project needs:

1. Add the Play Integrity dependency and register the native package — see
   `android/app/build.gradle.additions`.
2. Set `CLOUD_PROJECT_NUMBER` in `ApexIntegrityModule.kt` to the Google Cloud
   project number linked to this app in Play Console. Until then attestation
   resolves `UNAVAILABLE` and the server falls back to the local signals.

`android/app/src/main/AndroidManifest.xml` here contains the permission set;
merge it into the generated manifest.

### iOS

```bash
cd ios && pod install && cd ..
npx react-native run-ios
```

1. Add `ApexIntegrity.swift` and `ApexIntegrity.m` to the Xcode target.
2. Merge `ios/Info.plist.additions` into `Info.plist` — the usage strings are
   what the employee reads in the permission prompt, and vague wording is both
   an App Review risk and the reason staff decline.
3. Enable the **App Attest** capability on the App ID.

**Distribution:** for 500+ sites, Apple Business Manager custom app
distribution is a cleaner path than the public App Store — no public listing,
and managed rollout to a known workforce.

---

## Structure

```
src/
  config.js                     base URL, sampling windows
  api/client.js                 authenticated fetch, keystore token
  api/punchPayload.js           the wire contract, extracted so it is testable
  auth/AuthContext.jsx          session state
  location/geo.js               fence maths, mirrors the server exactly
  location/useLocationTracker.js foreground watch, burst + approach buffers
  integrity/integrity.js        device signals, native bridge
  camera/selfie.js              front-camera capture
  screens/                      Login, Clock
  components/                   FenceStatus, PunchButton
android/.../ApexIntegrityModule.kt   mock location, root, emulator, Play Integrity
ios/.../ApexIntegrity.swift          jailbreak heuristics, App Attest
```

`location/geo.js` reimplements the server's fence maths so the button and the
server agree — staff must never be told they are inside the fence and then
refused. It is a convenience, never a control: the server revalidates every
punch and its answer is the only one that counts.

---

## Three rules that matter

1. **Altitude is `null` when unavailable, never `0`.** The server reads an
   exact zero as a spoofing sentinel, because real GNSS essentially never
   reports it. `useLocationTracker` already normalises this — preserve the
   behaviour if you touch that file.
2. **Send at least 3 samples.** Below that the server skips the drift check and
   the punch is weaker evidence.
3. **Show the server's rejection message verbatim.** Those strings are written
   for the employee and are deliberately vague about *how far* outside the
   fence they are — telling somebody "you are 340m away" is a free calibration
   tool for anyone probing the boundary.

---

## Testing

```bash
npx eslint src index.js --ext .js,.jsx
```

`geo.js` was verified against the running backend: for the same coordinates the
client computed 8884m outside the fence and the server independently computed
8884m. The payload builder was posted to a live API and exercised the accepted,
missing-photo, outside-fence, mock-location and null-altitude paths.

---

## Not done

- **Timesheet history screen.** The server exposes the data; there is no screen.
- **Push notifications** for shift reminders.
- **Biometric app lock** (Face ID / fingerprint to open the app).
- **Never run on a physical device.** This environment has no Android SDK or
  Xcode, so the JavaScript is linted and logic-tested, and the native modules
  are written but uncompiled. Expect the usual first-build wiring work.

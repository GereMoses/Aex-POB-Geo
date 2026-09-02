# Apex Clock — native app

Real iOS and Android builds of the employee clock, wrapping the same page that
is served at `/clock/` for browser pilots.

One UI, two shells. `scripts/pull-web.js` copies the page out of
`backend/app/static/clock/` at build time, so there is no second codebase to
drift out of step.

## Why native at all

The browser build is genuinely useful — it needs no app store and installs to a
home screen — but a web page cannot run Play Integrity, App Attest,
mock-location detection or root checks. Those APIs are native-only.

That difference is not cosmetic. It is the whole anti-spoofing story, and the
server knows which client it is talking to: every punch carries `client_type`,
and the same page reports `PWA` in a browser and `NATIVE` inside this shell.
Two policy settings govern the difference:

- `allow_pwa_punches` — off refuses browser punches outright
- `risk_pwa_client` — a standing risk score for punches with no attestation

Pilot with the risk at 0. Once this app is distributed, raise it or switch the
flag off and the browser closes as a spoofing route, with no redeploy.

## Building — Android

The whole toolchain lives in a container, so no Android SDK is needed locally
and your JDK version does not decide whether the build works:

```bash
cd mobile-app
docker build -f Dockerfile.build -t apex-clock-build ..
docker run --rm -v "$PWD/dist:/out" apex-clock-build
```

The APK lands in `dist/`. A signed release is the same command with
`assembleRelease` and a keystore configured.

That command has been run end to end from a clean image: 16m44s, 198 Gradle
tasks, `BUILD SUCCESSFUL`. The APK it produced is the one in
`dist/apex-clock-debug.apk` — `ng.apexpob.clock`, 7.0MB, minSdk 23,
targetSdk 35, with the integrity plugin compiled in. Install with
`adb install dist/apex-clock-debug.apk`, or copy it to a handset and open it
with unknown sources allowed.

**It is a debug build**: unsigned for release, and it talks to whatever
`API_BASE_URL` points at. Set that before putting it on anyone's phone.

### In Android Studio instead

```bash
npm install && npm run sync
npx cap open android
```

Then apply the two steps below, which the container build does for you.

### The two manual steps

1. Copy `native/android/ApexIntegrityPlugin.kt` into
   `android/app/src/main/java/ng/apexpob/clock/` and register it in
   `MainActivity`:

   ```java
   registerPlugin(ApexIntegrityPlugin.class);
   ```

2. Add to `android/app/build.gradle`:

   ```gradle
   apply plugin: 'kotlin-android'
   implementation 'com.google.android.play:integrity:1.4.0'
   ```

   and set `CLOUD_PROJECT_NUMBER` in the plugin to the Google Cloud project
   number linked to this app in Play Console. Left at zero, attestation
   resolves `UNAVAILABLE` and the server falls back to the local signals.

Permissions baked into the APK: `INTERNET`, `ACCESS_FINE_LOCATION`,
`ACCESS_COARSE_LOCATION`, `CAMERA`. **Not** `ACCESS_BACKGROUND_LOCATION` — the
app reads position only while the clock screen is open.

### iOS — needs Xcode

Xcode is not installed on the machine this was built on (only Command Line
Tools), and it is a ~15GB App Store install requiring an Apple ID, so no iOS
build has been produced. Once Xcode is present:

```bash
npm install && npm run sync
npx cap add ios && npx cap open ios
```

Then:

1. Add `native/ios/ApexIntegrityPlugin.swift` and `.m` to the Xcode target.
2. Merge the usage strings from `../mobile/ios/Info.plist.additions`. These are
   what the employee reads in the permission prompt, so they say plainly what
   is collected and when — vague wording is both an App Review risk and the
   reason staff decline.
3. Enable the **App Attest** capability on the App ID.

**Distribution:** at 500+ sites, Apple Business Manager custom app distribution
is cleaner than the public App Store — no public listing, managed rollout to a
known workforce.

## Configuration

`API_BASE_URL` in `www/app.js` (sourced from
`backend/app/static/clock/app.js`) must point at the backend. It defaults to
`location.origin`, which is right for the browser build and wrong for the
packaged app — set it explicitly before a store build.

## The HTTPS requirement

Location and camera are both gated behind a secure context. Served over plain
HTTP on a LAN address the browser removes those APIs entirely and the failure
is silent. The page now detects this and says so, but the fix is TLS.

This matters for pilot testing: `http://192.168.x.x:8898/clock/` **will not
work** on a phone. Use the HTTPS address, or test on the machine itself where
`localhost` counts as secure.

## What is not done

- **iOS has never been compiled.** Xcode is not installed. The Swift plugin is
  written but unbuilt.
- **The APK has never run on a handset.** It builds, packages correctly and
  contains the plugin, but no emulator or device was available to launch it on.
  Expect first-run work around the runtime permission prompts.
- `CLOUD_PROJECT_NUMBER` is still zero, so Play Integrity resolves
  `UNAVAILABLE` until you set it.
- No push notifications for shift reminders.
- No timesheet history screen — the server exposes the data, the app has no
  view for it.
- No biometric app lock.

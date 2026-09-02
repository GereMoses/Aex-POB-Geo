# Testing the Apex Clock on a real phone

## Why not an emulator

This machine is an Intel Mac and Docker has no `/dev/kvm`, so an Android
emulator cannot run in a container here. It could be installed natively
alongside Android Studio, but a real handset is the better test anyway: GPS
behaviour under a warehouse roof, actual accuracy figures and the runtime
permission prompts are exactly what an emulator cannot tell you.

## Why not Expo Go

Expo Go loads a JavaScript bundle onto a phone in seconds and is excellent for
UI iteration. It cannot help here, for one decisive reason: **it can only run
the native modules bundled into Expo Go itself.** The `ApexIntegrity` plugin —
Play Integrity, App Attest, mock-location and root detection — is custom native
code, so under Expo Go it simply would not exist.

The app would fall back to reporting itself as an untrusted client, and the
anti-spoofing that distinguishes this product from every competitor would go
untested. That is the same blind spot the browser build has.

Getting custom native code onto a device with Expo requires a development
build, which is the same work as the APK already produced — with no advantage.

Neither project here is an Expo project in any case: `mobile-app/` is
Capacitor and `mobile/` is bare React Native, so `npx expo start` will not run
either of them.

## What to test with

`dist/apex-clock-lan.apk` — built against `https://192.168.0.235:8443`, with
the demo server's certificate trusted.

## Setup

1. **Put the phone on the same Wi-Fi as this Mac.**

2. **Check the server is reachable** — open `https://192.168.0.235:8443/clock/`
   in the phone's browser. A certificate warning is expected there; the app
   itself trusts the certificate and will not warn.

3. **Install the APK.** Either:

   ```bash
   adb install mobile-app/dist/apex-clock-lan.apk
   ```

   or copy it to the phone and open it, allowing installation from unknown
   sources.

4. **Sign in** as `CL001` / `Demo1234!`.

## What to check

**Permissions.** The app should ask for location once, and camera only when a
photo is first required. It must never ask for background location — if it
does, something has been added to the manifest that should not be there.

**Fence status.** Standing away from the Ikeja coordinates
(6.6018, 3.3515) it should say how far outside you are and keep the buttons
disabled. The fence is 250m, so walking towards those coordinates should flip
it to "You are at the warehouse".

To test somewhere convenient instead, move the fence to where you actually are:
in the admin UI, **Geofenced Attendance → Warehouse fences → Ikeja**, click
your location on the map, save.

**A real punch.** With the photo requirement on, the camera should open,
capture, and the punch should complete with a receipt.

**Then check the server agreed** — in **Exceptions**, the punch should appear
with `client_type = NATIVE`, a GPS drift figure in metres, and a face verdict.
`NATIVE` is the important one: it proves the integrity plugin loaded. If it
says `PWA`, the plugin did not register.

**The spoofing checks, which is the point of all this:**

- Install a fake-GPS app from Play, enable it in Developer Options, set a
  location far away, and try to clock in. Expect a refusal citing mock
  location.
- Try from home, well outside the fence. Expect `OUTSIDE_FENCE`.
- Clock in indoors, deep inside a building. This is the one that decides the
  `gps_accuracy_max_m` setting — note what accuracy the phone reports.

**Battery.** Leave the clock screen open for ten minutes and check the drain.
Location is foreground-only, so it should be modest; if it is not, the sampling
interval needs raising.

## Known limitations of this build

- Debug build, unsigned for release.
- `CLOUD_PROJECT_NUMBER` is zero, so Play Integrity resolves `UNAVAILABLE` and
  attestation is not really being tested. Set it from Play Console to exercise
  that path.
- The certificate trust is pinned to `192.168.0.235`. A different network means
  rebuilding with a new address and certificate.
- iOS is untested — Xcode is not installed.

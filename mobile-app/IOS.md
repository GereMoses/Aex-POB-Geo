# Apex Clock — iOS build

The iOS app is the same web app the Android build wraps: one HTML/CSS/JS
codebase in `backend/app/static/clock/`, wrapped by Capacitor, plus a small
Swift plugin for device integrity. Nothing about the clock-in logic is
platform-specific.

## What you need

| | |
|---|---|
| macOS | any recent version |
| **Xcode** | required — a full install, not Command Line Tools (~15 GB from the App Store) |
| CocoaPods | see below — `brew install cocoapods` builds from source and takes hours on this machine |
| Apple Developer account | $99/year — required to run on a real device or ship |

`xcodebuild` is what actually compiles the app, and it only exists inside a full
Xcode install. `xcode-select -p` must point at `/Applications/Xcode.app/...`,
not `/Library/Developer/CommandLineTools`. If it points at the latter after
installing Xcode:

```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

### Installing CocoaPods

`brew install cocoapods` had no bottle here and started compiling llvm, rust and
cmake from source. The macOS system ruby (2.6) cannot install CocoaPods either —
`ffi`, `securerandom` and `zeitwerk` all now require ruby 3.0+.

What worked was Homebrew's own vendored ruby, which is already on disk:

```bash
PR=/usr/local/Homebrew/Library/Homebrew/vendor/portable-ruby/current/bin
export GEM_HOME="$HOME/.gem-apex4" PATH="$HOME/.gem-apex4/bin:$PR:$PATH"
"$PR/gem" install cocoapods --no-document      # CocoaPods 1.17, about a minute
```

Keep that `GEM_HOME`/`PATH` exported in any shell that runs `cap add ios` or
`pod install`. A real Xcode install brings its own ruby and makes this moot.

## Build

```bash
cd mobile-app
npm install

# Bake in the server address. Without this the app has no backend to talk to.
export APEX_API_BASE=https://your-apex-server

npm run ios:add      # first time only — creates ios/ and applies our config
npm run ios          # thereafter: sync web assets, re-apply config, open Xcode
```

Until Xcode is installed, `npm run ios` and `npm run ios:add` both end with
`pod install - failed! ... xcodebuild requires Xcode`. That is expected: the pods
themselves resolve and install, and only CocoaPods' final build-settings probe
needs `xcodebuild`. The web assets are copied before that point, so the project
stays current.

Note also that `npm run sync` is deliberately pinned to `cap sync android`.
Bare `cap sync` walks every platform present, so once `ios/` existed it put the
whole Android release build behind an Xcode install. Use `npm run sync:ios` for
the iOS side.

`scripts/prepare-ios.js` runs automatically and is idempotent. It does three
things Capacitor does not:

1. **Adds the usage-description strings.** iOS terminates the app the moment it
   touches the camera or location without one, and review rejects the binary.
2. **Requests location "when in use" only**, and strips any background location
   mode. The app reads position while the clock screen is open and never in the
   background — asking for more than that invites review questions we would have
   no good answer to.
3. **Copies the integrity plugin** into the app target and installs the icon.

### In Xcode

`prepare-ios.js` now adds the Swift/ObjC plugin pair to the **App** target for
you by editing `project.pbxproj`, so there is no drag-and-drop step. Verify it
stuck: the two `ApexIntegrityPlugin` files should appear under *Build Phases →
Compile Sources*.

What still has to be done by hand, because it is tied to your Apple account:

1. Set the signing team under **Signing & Capabilities**.
2. Add the **App Attest** capability if you want hardware attestation.

## Signing and distribution

Same three routes as any iOS app:

- **TestFlight** — the sensible way to get it onto testers' phones. Up to 100
  internal testers, no per-device registration, and it handles updates.
- **Ad-hoc** — each device's UDID registered manually. Painful past a handful.
- **App Store** — full review. Expect questions about location and biometrics;
  see below.

Archive from Xcode (`Product → Archive`), then distribute.

## What differs from Android

**App Attest replaces Play Integrity.** `ApexIntegrityPlugin.swift` already
implements it. It needs the App Attest capability enabled on the App ID, and
the server verifies the assertion. Like the Android side, this is the one
integrity signal a modified app cannot simply omit its way past.

**There is no mock-location setting to read.** iOS gives away less than Android.
Jailbreak detection is heuristic, and `isSimulator()` is compile-time.

**Simulated-location detection is NOT yet implemented.** `getSignals` returns a
hardcoded `isMockLocationEnabled: false` on iOS. The signal that would carry it,
`CLLocation.sourceInformation.isSimulatedBySoftware` (iOS 15+), is not read by
anything: the app gets its position from the stock Capacitor Geolocation plugin,
which does not surface `sourceInformation`. Closing this means adding a native
method that takes its own fix, plus a JS call site shared with Android and the
PWA — see *Known gap* below.

**Consequence for policy today:** an iPhone never reports `is_mock_location`, so
a `block_mock_location` rule is Android-only. iPhone spoofing is currently
caught only by the indirect signals — GPS drift, altitude, approach-path
teleport, impossible travel, clock skew and device fingerprint — plus App Attest
and the jailbreak heuristics, since the usual iOS location-spoofing routes
require either a jailbreak or a tethered Mac.

## App Store review — what they will ask

Two things in this app attract questions:

- **Location.** Be explicit that it is used only to confirm the employee is at
  their assigned workplace at the moment they clock in, is read only while the
  app is open, and is not tracked in the background. The usage string already
  says this.
- **Face photos.** The app captures a selfie at clock-in and compares it against
  an enrolled reference. Apple will want to know what is stored and for how
  long. The honest answer: a 512-float embedding that cannot be reverted to an
  image, plus the photo itself on a private volume, subject to the retention
  policy configured in the console.

For a workforce app distributed to one company's staff, **Apple Business
Manager / custom app distribution** avoids public review entirely and is
usually the better route than the public App Store.

## Known gap — simulated location

To close it, three things have to change together:

1. **Native.** A `getLocationIntegrity` method on `ApexIntegrityPlugin` that
   takes a one-shot `CLLocationManager` fix and returns
   `sourceInformation.isSimulatedBySoftware`, guarded by `#available(iOS 15,*)`.
2. **JS.** A call site in `backend/app/static/clock/app.js`, feature-detected —
   the same file ships to Android and to the browser, where the method does not
   exist.
3. **Server.** Fold the result into the composite risk score in `mobile.py`
   alongside the Android `is_mock_location` signal.

None of it can be compiled or tested without Xcode, which is why it is written
down rather than guessed at.

## Current state

Done, and verified as far as the toolchain allows:

- `ios/` Xcode project generated, CocoaPods 1.17 integrated (all Capacitor pods
  resolved, `Pods-App` support files present)
- permission strings in `Info.plist`; `UIBackgroundModes` absent
- integrity plugin **compiled into the App target** — confirmed present in the
  Sources build phase, and the wiring is idempotent
- icon installed: 1024×1024, `hasAlpha: no`
- server URL baked into `App/public/config.js`
- bundle id `ng.apexpob.clock`, deployment target iOS 14.0

**Not done, and not doable on this machine:** compile, sign, archive, distribute.
`xcodebuild` requires a full Xcode install; only Command Line Tools are present.
No `.ipa` exists yet, and iOS has no sideloading equivalent to an APK — the
routes are TestFlight, Apple Business Manager or the App Store, all of which
need Xcode plus a paid Apple Developer account.

Until then, iPhone users can use the browser version at `/clock/` — Add to Home
Screen in Safari. It is the same app minus the native integrity signals.

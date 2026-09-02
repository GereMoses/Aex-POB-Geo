# Running the app on the Android emulator

The Android SDK is installed at `~/Library/Android/sdk` (~6GB) and an emulator
called `apex_test` is configured. Everything below assumes these on your PATH:

```bash
export ANDROID_HOME="$HOME/Library/Android/sdk"
export PATH="$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"
```

Add those two lines to `~/.zshrc` to avoid repeating them.

## Start the emulator

```bash
emulator -avd apex_test -no-audio -no-boot-anim
```

It takes a minute or two on first boot. Leave the terminal open — closing it
stops the emulator. Add `-no-window` to run it invisibly (useful for scripted
testing, useless for looking at).

Check it is up:

```bash
adb devices          # expect: emulator-5554   device
```

## Install the app

```bash
adb install -r mobile-app/dist/apex-clock-lan.apk
```

`-r` reinstalls over an existing copy and keeps its data. Then launch it from
the emulator's app drawer, or:

```bash
adb shell am start -n ng.apexpob.clock/.MainActivity
```

Sign in as **CL001** / **Demo1234!**

## Give it a location

The app will not enable its buttons without one. The emulator takes
**longitude first**:

```bash
adb emu geo fix 3.35162 6.60195      # the Ikeja gate
adb emu geo fix 3.3792 6.5244        # ~9km away, outside the fence
```

Send it two or three times a few seconds apart — the app wants several fixes
before it will punch, so that it can check whether the position drifts the way
a real one does.

You can also use the emulator's own **⋯ → Location** panel.

## What you will see, and why

**Every punch from the emulator is refused with "Mock location is enabled on
this device."**

That is correct, not a fault. `adb emu geo fix` feeds position through
Android's mock-location provider — exactly what a fake-GPS app does — and the
app is built to refuse it. It is a live demonstration of the anti-spoofing
working.

It also means **the emulator cannot produce an accepted punch.** For that you
need a real handset with real satellite GPS. What the emulator is good for is
everything else: layout, sign-in, permission prompts, the camera flow, fence
distance display, and the refusal paths.

## Useful commands

```bash
adb logcat -c                                    # clear the log
adb logcat | grep -i "Capacitor/Console"         # the app's console output
adb exec-out screencap -p > shot.png             # screenshot
adb uninstall ng.apexpob.clock                   # remove the app
adb emu kill                                     # stop the emulator
```

## Checking the server agreed

Open the admin UI at <https://192.168.0.235:8443/pob-system/geofence> (accept
the certificate warning) and go to **Exceptions**. Each attempt appears with:

- `client_type` — **NATIVE** means the integrity plugin loaded. If it says
  `PWA`, the plugin failed to register and nothing else about the test is
  meaningful.
- the refusal reason, GPS accuracy, drift and sample count.

## If the app cannot reach the server

The APK is built against `https://192.168.0.235:8443` with that server's
certificate trusted. If this Mac's address changes, rebuild:

```bash
cd mobile-app
docker build --build-arg APEX_API_BASE="https://<new-ip>:8443" \
  -f Dockerfile.build -t apex-clock-build ..
docker run --rm -e APEX_API_BASE="https://<new-ip>:8443" \
  -v "$PWD/dist:/out" apex-clock-build
```

and regenerate the certificate for the new address — the old one names the old
IP, and Android checks that.

## Tidying up

```bash
adb emu kill
rm -rf ~/Library/Android ~/.android/avd/apex_test.avd ~/.android/avd/apex_test.ini
```

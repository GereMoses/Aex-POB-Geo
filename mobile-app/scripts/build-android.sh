#!/usr/bin/env bash
# Generate the Android project, wire in the native plugin, and build an APK.
set -euo pipefail

cd /src/mobile-app
npm install --silent --no-audit --no-fund
node scripts/pull-web.js

[ -d android ] || npx cap add android
npx cap sync android

PKG_DIR=android/app/src/main/java/ng/apexpob/clock
cp native/android/ApexIntegrityPlugin.kt "$PKG_DIR/"

# Certificate trust for a pilot server on the local network. Skipped when the
# resources are absent, so a production build is unaffected.
if [ -d native/android/res ]; then
  mkdir -p android/app/src/main/res/raw android/app/src/main/res/xml
  cp -R native/android/res/. android/app/src/main/res/
fi

# Capacitor discovers plugins registered on the activity.
cat > "$PKG_DIR/MainActivity.java" <<'JAVA'
package ng.apexpob.clock;

import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(android.os.Bundle savedInstanceState) {
        // Registered before super so the bridge sees it during initialisation.
        registerPlugin(ApexIntegrityPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
JAVA

python3 - <<'PY'
import pathlib
p = pathlib.Path("android/app/build.gradle"); s = p.read_text()
if "kotlin-android" not in s:
    s = s.replace("apply plugin: 'com.android.application'",
                  "apply plugin: 'com.android.application'\napply plugin: 'kotlin-android'")
if "play:integrity" not in s:
    s = s.replace("dependencies {",
                  "dependencies {\n    implementation 'com.google.android.play:integrity:1.4.0'\n"
                  "    implementation 'org.jetbrains.kotlin:kotlin-stdlib:1.9.24'", 1)
p.write_text(s)

p = pathlib.Path("android/build.gradle"); s = p.read_text()
if "kotlin-gradle-plugin" not in s:
    s = s.replace("dependencies {",
                  "dependencies {\n        classpath 'org.jetbrains.kotlin:kotlin-gradle-plugin:1.9.24'", 1)
p.write_text(s)

# Location and camera. ACCESS_BACKGROUND_LOCATION is deliberately absent: the
# app reads position only while the clock screen is open.
p = pathlib.Path("android/app/src/main/AndroidManifest.xml"); s = p.read_text()
if pathlib.Path("android/app/src/main/res/xml/network_security_config.xml").exists() \
        and "networkSecurityConfig" not in s:
    s = s.replace("<application", '<application android:networkSecurityConfig='
                  '"@xml/network_security_config"', 1)
if "ACCESS_FINE_LOCATION" not in s:
    s = s.replace('<uses-permission android:name="android.permission.INTERNET" />',
                  '<uses-permission android:name="android.permission.INTERNET" />\n'
                  '    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />\n'
                  '    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />\n'
                  '    <uses-permission android:name="android.permission.CAMERA" />')
p.write_text(s)
PY

cd android
./gradlew "${1:-assembleDebug}" --no-daemon
find app/build/outputs/apk -name "*.apk" -exec cp {} /out/ \; 2>/dev/null || true
ls -la /out 2>/dev/null || echo "mount a volume at /out to collect the APK"

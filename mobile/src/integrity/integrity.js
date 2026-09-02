/**
 * Device integrity signals sent alongside every punch.
 *
 * Everything here is self-reported and therefore untrusted: a patched build
 * can lie about any of it. That is why the server treats a *positive* signal
 * as actionable but never treats absence as proof of anything, and why
 * attestation matters most — its verdict is signed by Google or Apple, not by
 * this app.
 */
import { NativeModules, Platform } from 'react-native';
import DeviceInfo from 'react-native-device-info';
import { APP_VERSION, PLATFORM } from '../config';

const { ApexIntegrity } = NativeModules;

/**
 * A stable per-install identifier.
 *
 * Not a hardware id: those need privileged permissions on Android and are
 * unavailable on iOS. This is enough to spot one handset punching for several
 * employees, which is the thing device fingerprinting is actually for here.
 */
async function deviceId() {
  try {
    return await DeviceInfo.getUniqueId();
  } catch {
    return null;
  }
}

/**
 * Ask the platform to vouch for this app and device.
 *
 * Android returns a Play Integrity token, iOS an App Attest assertion. The
 * server records the verdict; a hard FAIL blocks the punch outright.
 * Attestation needs the network, so a failure to obtain one is reported as
 * UNAVAILABLE rather than FAIL — otherwise a weak signal at the warehouse gate
 * would look identical to a tampered device.
 */
async function attestation() {
  if (!ApexIntegrity?.requestAttestation) return 'UNAVAILABLE';
  try {
    const verdict = await ApexIntegrity.requestAttestation();
    return verdict || 'UNAVAILABLE';
  } catch {
    return 'UNAVAILABLE';
  }
}

export async function collectIntegrity({ sawMockProvider = false } = {}) {
  const [id, verdict, native] = await Promise.all([
    deviceId(),
    attestation(),
    ApexIntegrity?.getSignals
      ? ApexIntegrity.getSignals().catch(() => ({}))
      : Promise.resolve({}),
  ]);

  let isEmulator = false;
  try {
    isEmulator = await DeviceInfo.isEmulator();
  } catch {
    isEmulator = false;
  }

  return {
    device_id: id,
    platform: PLATFORM,
    app_version: APP_VERSION,
    // Two independent sources: the location provider's own mock flag observed
    // during tracking, and the native check for a selected mock-location app.
    is_mock_location: Boolean(sawMockProvider || native.isMockLocationEnabled),
    is_rooted: Boolean(native.isCompromised),
    is_emulator: Boolean(isEmulator || native.isEmulator),
    attestation_verdict: verdict,
  };
}

/**
 * Signals worth warning the employee about before they try to punch, so they
 * are not left staring at a refusal they cannot interpret.
 */
export function blockingHint(integrity) {
  if (integrity.is_mock_location) {
    return Platform.OS === 'android'
      ? 'Mock location is switched on. Turn it off in Developer Options to clock in.'
      : 'A simulated location was detected. Disconnect any location tools and try again.';
  }
  if (integrity.is_emulator) {
    return 'This app must run on a real phone, not an emulator.';
  }
  if (integrity.attestation_verdict === 'FAIL') {
    return 'This device failed its security check. Contact your supervisor.';
  }
  return null;
}

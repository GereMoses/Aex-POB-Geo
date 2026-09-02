/**
 * Foreground location tracking for the punch screen.
 *
 * Deliberately foreground-only. Continuous background tracking would give
 * nicer approach trails, but it means asking warehouse staff for "Always
 * Allow" location, tracking them outside work hours, and defending that in
 * app review. The client asked us to stop clock-in fraud, not to build a
 * surveillance product — so the watch starts when the punch screen opens and
 * stops when it closes.
 *
 * The buffer it accumulates serves both server-side checks:
 *   - the burst (fixes from the last few seconds) feeds the drift test
 *   - the trail (fixes over several minutes) feeds the approach test
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { Platform, PermissionsAndroid } from 'react-native';
import Geolocation from 'react-native-geolocation-service';
import { APPROACH_WINDOW_MS, BURST_WINDOW_MS } from '../config';

export const PermissionState = {
  PENDING: 'PENDING',
  GRANTED: 'GRANTED',
  DENIED: 'DENIED',
  BLOCKED: 'BLOCKED',
};

async function requestPermission() {
  if (Platform.OS === 'ios') {
    const result = await Geolocation.requestAuthorization('whenInUse');
    if (result === 'granted') return PermissionState.GRANTED;
    return result === 'disabled' || result === 'restricted'
      ? PermissionState.BLOCKED
      : PermissionState.DENIED;
  }
  const granted = await PermissionsAndroid.request(
    PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
    {
      title: 'Location needed to clock in',
      message:
        'Apex Clock confirms you are at your warehouse when you clock in and out. '
        + 'Your location is only read at that moment.',
      buttonPositive: 'Allow',
    },
  );
  if (granted === PermissionsAndroid.RESULTS.GRANTED) return PermissionState.GRANTED;
  return granted === PermissionsAndroid.RESULTS.NEVER_ASK_AGAIN
    ? PermissionState.BLOCKED
    : PermissionState.DENIED;
}

/**
 * Normalise a platform fix into the shape the server expects.
 *
 * Altitude is passed through as null when the platform has none. Sending 0
 * would be read as a spoofing sentinel — real GNSS essentially never reports
 * exactly zero — and would flag honest punches.
 */
function normalise(position) {
  const c = position.coords;
  const hasAltitude =
    typeof c.altitude === 'number' && Number.isFinite(c.altitude);
  return {
    latitude: c.latitude,
    longitude: c.longitude,
    accuracy: c.accuracy ?? null,
    altitude: hasAltitude ? c.altitude : null,
    // Android exposes whether a fix came from a mock provider; iOS does not,
    // and is covered by the integrity module instead.
    mocked: position.mocked === true,
    timestamp: new Date(position.timestamp ?? Date.now()).toISOString(),
    at: position.timestamp ?? Date.now(),
  };
}

export function useLocationTracker(active) {
  const [permission, setPermission] = useState(PermissionState.PENDING);
  const [position, setPosition] = useState(null);
  const [error, setError] = useState(null);
  const [sawMockProvider, setSawMockProvider] = useState(false);
  const buffer = useRef([]);
  const watchId = useRef(null);

  useEffect(() => {
    let cancelled = false;
    if (!active) return undefined;

    (async () => {
      const state = await requestPermission();
      if (cancelled) return;
      setPermission(state);
      if (state !== PermissionState.GRANTED) return;

      watchId.current = Geolocation.watchPosition(
        (raw) => {
          const fix = normalise(raw);
          // A single mocked fix is remembered for the session: a spoofing app
          // toggled off just before the punch should not erase the evidence.
          if (fix.mocked) setSawMockProvider(true);
          const cutoff = Date.now() - APPROACH_WINDOW_MS;
          buffer.current = [...buffer.current, fix].filter((f) => f.at >= cutoff);
          setPosition(fix);
          setError(null);
        },
        (err) => setError(err.message),
        {
          accuracy: { android: 'high', ios: 'best' },
          enableHighAccuracy: true,
          distanceFilter: 0,
          interval: 3000,
          fastestInterval: 2000,
          showLocationDialog: true,
          forceRequestLocation: true,
        },
      );
    })();

    return () => {
      cancelled = true;
      if (watchId.current != null) {
        Geolocation.clearWatch(watchId.current);
        watchId.current = null;
      }
    };
  }, [active]);

  /** Fixes from the last few seconds — the server's drift sample. */
  const getBurst = useCallback(() => {
    const cutoff = Date.now() - BURST_WINDOW_MS;
    return buffer.current
      .filter((f) => f.at >= cutoff)
      .map(({ latitude, longitude, accuracy, timestamp }) => ({
        latitude,
        longitude,
        accuracy,
        timestamp,
      }));
  }, []);

  /**
   * The approach trail, thinned to one fix every ~15s.
   *
   * The server only needs enough points to see whether movement was
   * continuous; sending every fix would bloat the punch payload on a
   * connection that is often poor to begin with.
   */
  const getApproachPath = useCallback(() => {
    const out = [];
    let lastAt = 0;
    for (const f of buffer.current) {
      if (f.at - lastAt >= 15000) {
        out.push({
          latitude: f.latitude,
          longitude: f.longitude,
          timestamp: f.timestamp,
        });
        lastAt = f.at;
      }
    }
    return out;
  }, []);

  return {
    permission,
    position,
    error,
    sawMockProvider,
    getBurst,
    getApproachPath,
  };
}

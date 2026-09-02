/**
 * Runtime configuration.
 *
 * The base URL is baked per build rather than typed by the employee: a
 * warehouse worker should never be in a position to point the clock at the
 * wrong server, and a mistyped host would silently fail every punch.
 */
import { Platform } from 'react-native';

// Replace at build time (Gradle productFlavors / Xcode xcconfig), or edit here
// for a development build.
export const API_BASE_URL = 'https://pob.continental-logistics.example';

export const APP_VERSION = '1.0.0';
export const PLATFORM = Platform.OS;

// How long a fix may sit in the buffer before it stops counting towards the
// approach trail. Long enough to cover a walk from the car park, short enough
// that yesterday's positions never leak into today's punch.
export const APPROACH_WINDOW_MS = 5 * 60 * 1000;

// The burst used for the server's drift check is taken from fixes captured in
// this window immediately before the punch.
export const BURST_WINDOW_MS = 15 * 1000;

// The server needs at least three fixes before the drift signal means
// anything; below that it skips the check entirely.
export const MIN_BURST_SAMPLES = 3;

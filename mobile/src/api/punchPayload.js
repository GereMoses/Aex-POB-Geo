/**
 * Builds the punch body sent to the server.
 *
 * Extracted from the screen so the exact wire shape can be tested against the
 * API without rendering anything — this payload is the contract between the
 * app and the geofence engine, and a silent shape change here would show up
 * as unexplained rejections at the gate.
 */

/**
 * @param position    normalised fix (latitude, longitude, accuracy, altitude, timestamp)
 * @param samples     burst of fixes for the server's drift check
 * @param approachPath thinned trail for the server's approach check
 * @param integrity   device integrity signals
 * @param selfieBase64 photo, or null where the site does not require one
 */
export function buildPunchPayload({
  position,
  samples = [],
  approachPath = [],
  integrity,
  selfieBase64 = null,
}) {
  if (!position) throw new Error('Cannot build a punch without a location fix');

  return {
    location: {
      latitude: position.latitude,
      longitude: position.longitude,
      accuracy: position.accuracy ?? null,
      // Null, never 0. The server reads an exact zero as a spoofing sentinel
      // because real GNSS essentially never reports it, so a handset that uses
      // 0 to mean "unknown" would have honest punches flagged.
      altitude: typeof position.altitude === 'number' ? position.altitude : null,
      // Evidence only — the server stamps the punch with its own clock.
      timestamp: position.timestamp,
    },
    samples,
    approach_path: approachPath,
    device: integrity,
    selfie_base64: selfieBase64,
  };
}

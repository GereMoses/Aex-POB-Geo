/**
 * Distance helpers, mirroring the server's geofence maths.
 *
 * This exists so the punch button can show fence status before the employee
 * taps it. It is a convenience, never a control: the server recomputes every
 * punch and its answer is the only one that counts. Keeping the formula
 * identical means the button and the server agree, so staff are not told they
 * are inside the fence and then refused.
 */

const EARTH_RADIUS_M = 6371008.8;

export function haversineM(lat1, lon1, lat2, lon2) {
  const toRad = (d) => (d * Math.PI) / 180;
  const p1 = toRad(lat1);
  const p2 = toRad(lat2);
  const dp = p2 - p1;
  const dl = toRad(lon2 - lon1);
  const a =
    Math.sin(dp / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
  return 2 * EARTH_RADIUS_M * Math.asin(Math.sqrt(a));
}

/** Metres beyond a site's fence: 0 when inside, positive when outside. */
export function metresOutsideFence(position, site) {
  if (!site || site.latitude == null || position == null) {
    return null;
  }
  const centreDistance = haversineM(
    position.latitude,
    position.longitude,
    site.latitude,
    site.longitude,
  );
  return Math.max(0, centreDistance - (site.radius_m ?? 0));
}

/**
 * Nearest assigned site, and how far outside its fence the device is.
 *
 * Employees who cover several warehouses are checked against all of them, the
 * same way the server does, so the screen names the site they are actually at.
 */
export function nearestSite(position, sites) {
  if (!position || !sites?.length) {
    return { site: null, metresOutside: null };
  }
  let best = null;
  for (const site of sites) {
    const metresOutside = metresOutsideFence(position, site);
    if (metresOutside == null) continue;
    if (!best || metresOutside < best.metresOutside) {
      best = { site, metresOutside };
    }
  }
  return best ?? { site: null, metresOutside: null };
}

/**
 * Whether a punch is likely to be accepted.
 *
 * Applies the same accuracy allowance as the server, including its cap — so
 * the button does not light up on a wildly inaccurate fix the server will
 * reject anyway.
 */
export function willLikelyPass(position, site, metresOutside) {
  if (!site || metresOutside == null || !position) return false;
  const accuracy = position.accuracy ?? 0;
  if (accuracy > (site.gps_accuracy_max_m ?? 100)) return false;
  const allowance = Math.min(accuracy, site.accuracy_buffer_cap_m ?? 50);
  return metresOutside <= allowance;
}

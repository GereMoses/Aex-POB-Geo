/**
 * Backend address.
 *
 * Left empty for the browser build, which is served by the backend itself and
 * so can use its own origin. The packaged app has no such luxury — inside
 * Capacitor the page is served from a local scheme, so the build writes the
 * real address in here.
 */
window.APEX_API_BASE = '';

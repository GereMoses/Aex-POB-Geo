/**
 * Authenticated client for the Apex POB API.
 *
 * Tokens live in the platform keystore rather than AsyncStorage: a punch token
 * identifies an employee to an attendance system, and on a rooted handset
 * AsyncStorage is a world-readable file.
 */
import * as Keychain from 'react-native-keychain';
import { API_BASE_URL } from '../config';

const TOKEN_SERVICE = 'apex.pob.token';

let cachedToken = null;

export async function saveToken(token) {
  cachedToken = token;
  await Keychain.setGenericPassword('token', token, {
    service: TOKEN_SERVICE,
    accessible: Keychain.ACCESSIBLE.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
  });
}

export async function loadToken() {
  if (cachedToken) return cachedToken;
  const stored = await Keychain.getGenericPassword({ service: TOKEN_SERVICE });
  cachedToken = stored ? stored.password : null;
  return cachedToken;
}

export async function clearToken() {
  cachedToken = null;
  await Keychain.resetGenericPassword({ service: TOKEN_SERVICE });
}

export class ApiError extends Error {
  constructor(message, { status, reason } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.reason = reason;
  }
}

async function request(path, { method = 'GET', body, form, timeoutMs = 20000 } = {}) {
  const token = await loadToken();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: {
        'Content-Type': form
          ? 'application/x-www-form-urlencoded'
          : 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: form
        ? Object.entries(form)
            .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
            .join('&')
        : body
          ? JSON.stringify(body)
          : undefined,
      signal: controller.signal,
    });
  } catch (err) {
    // A punch that never reached the server must not look like a rejection —
    // the employee needs to know to move and retry, not that they were refused.
    throw new ApiError(
      err.name === 'AbortError'
        ? 'The server did not respond. Check your signal and try again.'
        : 'No connection. Move to where you have signal and try again.',
      { status: 0, reason: 'NETWORK' },
    );
  } finally {
    clearTimeout(timer);
  }

  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;

  if (!response.ok) {
    if (response.status === 401) {
      await clearToken();
      throw new ApiError('Your session has expired. Sign in again.', {
        status: 401,
        reason: 'UNAUTHENTICATED',
      });
    }
    // A refused punch carries {reason, message} inside detail. The message is
    // written for the employee, so it is surfaced verbatim.
    const detail = payload?.detail;
    if (detail && typeof detail === 'object') {
      throw new ApiError(detail.message || 'Could not clock in.', {
        status: response.status,
        reason: detail.reason,
      });
    }
    throw new ApiError(
      typeof detail === 'string' ? detail : `Request failed (${response.status})`,
      { status: response.status },
    );
  }
  return payload;
}

export const api = {
  // The backend's login route is an OAuth2PasswordRequestForm, so credentials
  // go form-encoded. Posting JSON here returns a 422 with no useful message.
  login: (username, password) =>
    request('/api/v1/auth/login', {
      method: 'POST',
      form: { username, password },
    }),
  mySites: () => request('/api/v1/mobile/my-sites'),
  punch: (direction, payload) =>
    request(`/api/v1/mobile/${direction === 'IN' ? 'check-in' : 'check-out'}`, {
      method: 'POST',
      body: payload,
    }),
};

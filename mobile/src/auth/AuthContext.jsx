import { createContext, useContext, useEffect, useMemo, useState, useCallback } from 'react';
import { api, saveToken, loadToken, clearToken, ApiError } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  const [restoring, setRestoring] = useState(true);

  useEffect(() => {
    loadToken()
      .then(setToken)
      .catch(() => setToken(null))
      .finally(() => setRestoring(false));
  }, []);

  const signIn = useCallback(async (username, password) => {
    const result = await api.login(username, password);
    const issued = result?.access_token || result?.token;
    if (!issued) throw new ApiError('Sign-in did not return a session.');
    await saveToken(issued);
    setToken(issued);
  }, []);

  const signOut = useCallback(async () => {
    await clearToken();
    setToken(null);
  }, []);

  // The client clears the stored token on any 401, so an expired session
  // surfaces here as a sign-out rather than leaving the app in a state where
  // every punch silently fails.
  const handleUnauthenticated = useCallback(() => setToken(null), []);

  const value = useMemo(
    () => ({ token, restoring, signIn, signOut, handleUnauthenticated }),
    [token, restoring, signIn, signOut, handleUnauthenticated],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}

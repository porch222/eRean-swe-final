import { createContext, useCallback, useContext, useEffect, useState } from 'react';

import { clearTokens, getAccess, getRefresh, setTokens } from '../api/client';
import { fetchMe, login as apiLogin, logout as apiLogout } from '../api/resources';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function restore() {
      if (!getAccess()) {
        setLoading(false);
        return;
      }
      const result = await fetchMe();
      if (result.ok) setUser(result.data);
      else clearTokens();
      setLoading(false);
    }
    restore();
  }, []);

  useEffect(() => {
    const onLogout = () => setUser(null);
    window.addEventListener('erean:logout', onLogout);
    return () => window.removeEventListener('erean:logout', onLogout);
  }, []);

  const loginUser = useCallback(async (username, password) => {
    const result = await apiLogin(username, password);
    if (!result.ok) return result;

    setTokens(result.data.access, result.data.refresh);

    setUser(result.data.user);
    return result;
  }, []);

  const logoutUser = useCallback(async () => {
    const refresh = getRefresh();
    if (refresh) await apiLogout(refresh);
    clearTokens();
    setUser(null);
  }, []);

  const value = { user, setUser, loading, loginUser, logoutUser };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>');
  return context;
}

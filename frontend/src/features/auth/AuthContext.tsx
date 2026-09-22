import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../../services/api';
import type { AuthResponse, User } from '../../types/api';

type AuthContextValue = {
  token: string | null;
  user: User | null;
  loading: boolean;
  setSession: (value: AuthResponse) => void;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // Access tokens live in memory only. Durable authentication is held in HttpOnly cookies.
  // Browser authentication is cookie-only. The API may still return a bearer
  // token for non-browser clients, but the React app never persists or reuses it.
  const token: string | null = null;
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const clearSession = useCallback(() => {
    setUser(null);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api<void>('/auth/logout', { method: 'POST', skipAuthRefresh: true });
    } finally {
      clearSession();
    }
  }, [clearSession]);

  const setSession = useCallback((value: AuthResponse) => {
    setUser(value.user);
  }, []);

  useEffect(() => {
    let active = true;
    api<User>('/auth/me')
      .then((me) => { if (active) setUser(me); })
      .catch(() => { if (active) clearSession(); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [clearSession]);

  const value = useMemo(() => ({ token, user, loading, setSession, logout }), [token, user, loading, setSession, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../../services/api';
import type { AuthResponse, User } from '../../types/api';

const TOKEN_KEY = 'stuskilllink_access_token';
const USER_KEY = 'stuskilllink_user';

type AuthContextValue = {
  token: string | null;
  user: User | null;
  loading: boolean;
  setSession: (value: AuthResponse) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem(USER_KEY);
    return stored ? (JSON.parse(stored) as User) : null;
  });
  const [loading, setLoading] = useState(Boolean(token));

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const setSession = useCallback((value: AuthResponse) => {
    localStorage.setItem(TOKEN_KEY, value.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(value.user));
    setToken(value.access_token);
    setUser(value.user);
  }, []);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    api<User>('/auth/me', { token })
      .then((me) => {
        localStorage.setItem(USER_KEY, JSON.stringify(me));
        setUser(me);
      })
      .catch(logout)
      .finally(() => setLoading(false));
  }, [logout, token]);

  const value = useMemo(() => ({ token, user, loading, setSession, logout }), [token, user, loading, setSession, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}

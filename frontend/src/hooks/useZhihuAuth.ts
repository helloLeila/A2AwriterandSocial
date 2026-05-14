import { useCallback, useEffect, useState } from 'react';
import type { ZhihuOAuthUser } from '../types';

interface AuthState {
  loggedIn: boolean;
  user?: ZhihuOAuthUser;
  loading: boolean;
}

export function useZhihuAuth() {
  const [auth, setAuth] = useState<AuthState>({
    loggedIn: false,
    loading: true,
  });

  const refresh = useCallback(async () => {
    try {
      const res = await fetch('/api/auth/zhihu/me', {
        credentials: 'same-origin',
      });
      const data = await res.json();
      setAuth({
        loggedIn: Boolean(data.logged_in),
        user: data.user as ZhihuOAuthUser | undefined,
        loading: false,
      });
    } catch {
      setAuth({ loggedIn: false, loading: false });
    }
  }, []);

  const login = useCallback(() => {
    window.location.href = '/api/auth/zhihu/login';
  }, []);

  const logout = useCallback(async () => {
    await fetch('/api/auth/zhihu/logout', {
      method: 'POST',
      credentials: 'same-origin',
    });
    setAuth({ loggedIn: false, loading: false });
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    ...auth,
    login,
    logout,
    refresh,
  };
}

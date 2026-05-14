import { useCallback, useEffect, useState } from 'react';
import type { ZhihuOAuthUser } from '../types';
import { mockZhihuUser } from '../mocks/demoData';

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
    // 静态模式：直接返回 mock 用户
    await new Promise((r) => setTimeout(r, 300));
    setAuth({
      loggedIn: true,
      user: mockZhihuUser as ZhihuOAuthUser,
      loading: false,
    });
  }, []);

  const login = useCallback(() => {
    // 静态模式：直接设为已登录
    setAuth({
      loggedIn: true,
      user: mockZhihuUser as ZhihuOAuthUser,
      loading: false,
    });
  }, []);

  const logout = useCallback(async () => {
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

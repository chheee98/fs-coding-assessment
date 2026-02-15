'use client';

import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { useRouter } from 'next/navigation';
import { useQueryClient } from '@tanstack/react-query';
import { authApi } from '@/lib/api/auth';
import { clearAuthStorage } from '@/lib/api/client';
import type { LoginFormData, RegisterFormData } from '@/lib/schemas/auth';

interface AuthUser {
  id: string;
  username: string;
}

interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginFormData) => Promise<void>;
  register: (credentials: RegisterFormData) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount: restore auth state from localStorage
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const username = localStorage.getItem('username');
    if (token && username) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setUser({ id: payload.sub, username });
      } catch {
        clearAuthStorage();
      }
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(
    async (credentials: LoginFormData) => {
      const data = await authApi.login(credentials);
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('username', credentials.username);
      const payload = JSON.parse(atob(data.access_token.split('.')[1]));
      setUser({ id: payload.sub, username: credentials.username });
      router.push('/todos');
    },
    [router]
  );

  const register = useCallback(
    async (credentials: RegisterFormData) => {
      await authApi.register(credentials);
      await login({
        username: credentials.username,
        password: credentials.password,
      });
    },
    [login]
  );

  const logout = useCallback(() => {
    clearAuthStorage();
    queryClient.clear();
    setUser(null);
    router.push('/login');
  }, [queryClient, router]);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: !!user,
      isLoading,
      login,
      register,
      logout,
    }),
    [user, isLoading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

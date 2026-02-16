import type { AuthToken, User } from '@/types/auth';
import type { LoginFormData, RegisterFormData } from '@/lib/schemas/auth';
import { api } from '@/lib/api/client';

export const authApi = {
  login: async (credentials: LoginFormData): Promise<AuthToken> => {
    const { data } = await api.post<AuthToken>('/auth/login', credentials);
    return data;
  },

  register: async (credentials: RegisterFormData): Promise<User> => {
    const { data } = await api.post<User>('/auth/register', credentials);
    return data;
  },

  getMe: async (): Promise<User> => {
    const { data } = await api.get<User>('/users/me');
    return data;
  },
};

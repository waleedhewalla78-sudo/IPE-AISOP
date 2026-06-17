import api from '@/lib/api';
import type { LoginRequest, LoginResponse, UserInfo } from '../types';

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await api.post<{ success: boolean; data: LoginResponse }>(
    '/api/v1/auth/login',
    data,
  );
  return response.data.data;
}

export async function getCurrentUser(): Promise<UserInfo> {
  const response = await api.get<{ success: boolean; data: UserInfo }>(
    '/api/v1/auth/me',
  );
  return response.data.data;
}

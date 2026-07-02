import api from '@/lib/api';
import type { LoginRequest, LoginResponse, UserInfo } from '../types';

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await api.post<{ success: boolean; data: LoginResponse }>(
    '/api/v1/auth/login',
    data,
  );
  const tokens = response.data.data;
  localStorage.setItem('access_token', tokens.access_token);
  localStorage.setItem('refresh_token', tokens.refresh_token);
  return tokens;
}

export async function refreshSession(refreshToken: string): Promise<LoginResponse> {
  const response = await api.post<{ success: boolean; data: LoginResponse }>(
    '/api/v1/auth/refresh',
    { refresh_token: refreshToken },
  );
  return response.data.data;
}

export async function logoutSession(): Promise<void> {
  try {
    await api.post('/api/v1/auth/logout');
  } catch {
    // ignore — client clears tokens regardless
  }
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

export async function getAuthInfo(): Promise<{
  mode: string;
  keycloak_url: string;
  keycloak_realm: string;
  keycloak_client_id: string;
}> {
  const response = await api.get('/api/v1/auth/info');
  return response.data.data;
}

export async function getCurrentUser(): Promise<UserInfo> {
  const response = await api.get<{ success: boolean; data: UserInfo }>(
    '/api/v1/auth/me',
  );
  return response.data.data;
}

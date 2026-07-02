import { useDispatch, useSelector } from 'react-redux';
import type { RootState } from '@/store/store';
import { setCredentials, logout } from '../store/authSlice';
import type { LoginRequest } from '../types';
import * as authService from '../services/authService';
import { getAuthMode, logoutKeycloak, userFromKeycloakToken } from '../keycloak';

export function useAuth() {
  const dispatch = useDispatch();
  const { user, isAuthenticated, token } = useSelector(
    (state: RootState) => state.auth,
  );

  const login = async (data: LoginRequest) => {
    const response = await authService.login(data);
    const profile = await authService.getCurrentUser();
    dispatch(
      setCredentials({
        user: profile,
        token: response.access_token,
        refreshToken: response.refresh_token,
      }),
    );
    return response;
  };

  const logoutUser = async () => {
    if (getAuthMode() === 'keycloak') {
      dispatch(logout());
      await logoutKeycloak();
      return;
    }
    await authService.logoutSession();
    dispatch(logout());
  };

  const syncKeycloakSession = (accessToken: string) => {
    dispatch(
      setCredentials({
        user: userFromKeycloakToken(accessToken),
        token: accessToken,
      }),
    );
  };

  return {
    user,
    isAuthenticated,
    token,
    login,
    logout: logoutUser,
    syncKeycloakSession,
    authMode: getAuthMode(),
  };
}

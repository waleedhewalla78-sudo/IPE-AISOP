import { useDispatch, useSelector } from 'react-redux';
import type { RootState } from '@/store/store';
import { setCredentials, logout } from '../store/authSlice';
import type { LoginRequest } from '../types';
import * as authService from '../services/authService';

export function useAuth() {
  const dispatch = useDispatch();
  const { user, isAuthenticated, token } = useSelector(
    (state: RootState) => state.auth,
  );

  const login = async (data: LoginRequest) => {
    const response = await authService.login(data);
    dispatch(setCredentials({ user: { id: '', email: data.email, full_name: '', role: 'planner', tenant_id: '' }, token: response.access_token }));
    return response;
  };

  const logoutUser = () => {
    dispatch(logout());
  };

  return { user, isAuthenticated, token, login, logout: logoutUser };
}

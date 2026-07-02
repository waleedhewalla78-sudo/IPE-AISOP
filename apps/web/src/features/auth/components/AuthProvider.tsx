import { useEffect, useState, type ReactNode } from 'react';
import { useDispatch } from 'react-redux';
import {
  fetchAuthInfo,
  getAuthMode,
  initKeycloakFromInfo,
  userFromKeycloakToken,
} from '@/features/auth/keycloak';
import { setCredentials } from '@/features/auth/store/authSlice';

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const dispatch = useDispatch();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const info = await fetchAuthInfo();
        if (info.mode === 'keycloak') {
          const authenticated = await initKeycloakFromInfo(info);
          if (authenticated) {
            const token = localStorage.getItem('access_token');
            if (token) {
              dispatch(
                setCredentials({
                  user: userFromKeycloakToken(token),
                  token,
                }),
              );
            }
          }
        }
      } catch {
        // fall back to local auth
      } finally {
        if (!cancelled) setReady(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [dispatch]);

  if (!ready) {
    return (
      <div className="flex h-screen items-center justify-center bg-ipe-surface text-ipe-muted">
        {getAuthMode() === 'keycloak' ? 'Connecting to SSO…' : 'Loading…'}
      </div>
    );
  }

  return <>{children}</>;
}

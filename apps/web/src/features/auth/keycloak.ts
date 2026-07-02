import type Keycloak from 'keycloak-js';

let keycloakInstance: Keycloak | null = null;
let authMode: 'local' | 'keycloak' = 'local';

export interface AuthInfo {
  mode: 'local' | 'keycloak';
  keycloak_url: string;
  keycloak_realm: string;
  keycloak_client_id: string;
}

export function getAuthMode(): 'local' | 'keycloak' {
  return authMode;
}

export function setAuthMode(mode: 'local' | 'keycloak'): void {
  authMode = mode;
}

export function getKeycloak(): Keycloak | null {
  return keycloakInstance;
}

export async function fetchAuthInfo(): Promise<AuthInfo> {
  const base = import.meta.env.VITE_API_BASE_URL ?? '';
  const res = await fetch(`${base}/api/v1/auth/info`);
  if (!res.ok) {
    return {
      mode: 'local',
      keycloak_url: '',
      keycloak_realm: 'ipe',
      keycloak_client_id: 'ipe-platform',
    };
  }
  const body = await res.json();
  const info = (body.data ?? body) as AuthInfo;
  setAuthMode(info.mode === 'keycloak' ? 'keycloak' : 'local');
  return info;
}

export async function initKeycloakFromInfo(info: AuthInfo): Promise<boolean> {
  if (info.mode !== 'keycloak' || !info.keycloak_url) {
    return false;
  }
  const { default: KeycloakCtor } = await import('keycloak-js');
  keycloakInstance = new KeycloakCtor({
    url: info.keycloak_url,
    realm: info.keycloak_realm,
    clientId: info.keycloak_client_id,
  });

  const authenticated = await keycloakInstance.init({
    onLoad: 'check-sso',
    pkceMethod: 'S256',
    checkLoginIframe: false,
    silentCheckSsoRedirectUri: `${window.location.origin}/silent-check-sso.html`,
  });

  keycloakInstance.onTokenExpired = () => {
    void keycloakInstance?.updateToken(30).then((refreshed) => {
      if (refreshed && keycloakInstance?.token) {
        localStorage.setItem('access_token', keycloakInstance.token);
      }
    });
  };

  if (authenticated && keycloakInstance.token) {
    localStorage.setItem('access_token', keycloakInstance.token);
    if (keycloakInstance.refreshToken) {
      localStorage.setItem('refresh_token', keycloakInstance.refreshToken);
    }
  }
  return authenticated;
}

export function loginWithKeycloak(redirectPath = '/planning/dashboard'): void {
  const redirectUri = `${window.location.origin}${redirectPath}`;
  void keycloakInstance?.login({ redirectUri });
}

export async function logoutKeycloak(): Promise<void> {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  if (keycloakInstance) {
    await keycloakInstance.logout({ redirectUri: `${window.location.origin}/login` });
  }
}

export async function refreshKeycloakToken(): Promise<string | null> {
  if (!keycloakInstance) return null;
  try {
    const refreshed = await keycloakInstance.updateToken(30);
    if ((refreshed || keycloakInstance.token) && keycloakInstance.token) {
      localStorage.setItem('access_token', keycloakInstance.token);
      return keycloakInstance.token;
    }
  } catch {
    return null;
  }
  return keycloakInstance.token ?? null;
}

export function userFromKeycloakToken(token: string) {
  const payload = JSON.parse(atob(token.split('.')[1] ?? '')) as Record<string, unknown>;
  const realmRoles =
    payload.realm_access && typeof payload.realm_access === 'object'
      ? ((payload.realm_access as { roles?: string[] }).roles ?? [])
      : [];
  const role =
    (payload.role as string) ||
    realmRoles.find((r) =>
      ['admin', 'planner', 'operator', 'manager', 'executive'].includes(r),
    ) ||
    'operator';
  return {
    id: String(payload.sub ?? ''),
    email: String(payload.email ?? payload.preferred_username ?? ''),
    full_name: String(payload.name ?? payload.preferred_username ?? ''),
    role: role as 'admin' | 'planner' | 'operator' | 'manager' | 'executive',
    tenant_id: String(
      Array.isArray(payload.tenant_id) ? payload.tenant_id[0] : payload.tenant_id ?? '',
    ),
  };
}

import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '@/features/auth/hooks/useAuth';
import {
  DEMO_ROLE_STORAGE_KEY,
  resolveDemoRole,
  writeDemoRole,
  type DemoRole,
} from '@/lib/demoRole';

export function useDemoRole() {
  const { user } = useAuth();
  const [role, setRoleState] = useState<DemoRole>(() => resolveDemoRole(user?.role));

  useEffect(() => {
    const sync = () => setRoleState(resolveDemoRole(user?.role));
    sync();
    window.addEventListener('storage', sync);
    return () => window.removeEventListener('storage', sync);
  }, [user?.role]);

  const setRole = useCallback((next: DemoRole) => {
    writeDemoRole(next);
    setRoleState(next);
    window.dispatchEvent(
      new StorageEvent('storage', { key: DEMO_ROLE_STORAGE_KEY, newValue: next }),
    );
  }, []);

  return { role, setRole };
}

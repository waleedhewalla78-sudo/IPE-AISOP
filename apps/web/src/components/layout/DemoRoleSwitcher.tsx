/**
 * Top-right demo role switcher (STREAM-4.1).
 */
import { useCallback, useEffect, useState } from 'react';
import {
  DEMO_ROLE_STORAGE_KEY,
  DEMO_ROLES,
  readDemoRole,
  resolveDemoRole,
  writeDemoRole,
  type DemoRole,
} from '@/lib/demoRole';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { t } from '@/lib/i18n';

export function DemoRoleSwitcher() {
  const { user } = useAuth();
  const [role, setRole] = useState<DemoRole>(() => resolveDemoRole(user?.role));

  useEffect(() => {
    setRole(resolveDemoRole(user?.role));
  }, [user?.role]);

  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === DEMO_ROLE_STORAGE_KEY) {
        setRole(resolveDemoRole(user?.role));
      }
    };
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, [user?.role]);

  const onChange = useCallback(
    (next: DemoRole) => {
      writeDemoRole(next);
      setRole(next);
      window.dispatchEvent(
        new StorageEvent('storage', { key: DEMO_ROLE_STORAGE_KEY, newValue: next }),
      );
    },
    [],
  );

  const override = readDemoRole();

  return (
    <label className="flex items-center gap-1.5 text-xs text-ipe-text-muted" data-testid="demo-role-switcher">
      <span className="hidden sm:inline">{t('demo.role', 'Role')}</span>
      <select
        className="rounded-md border border-ipe-border bg-ipe-surface-card px-2 py-1 text-xs font-medium text-ipe-text"
        value={role}
        onChange={(e) => onChange(e.target.value as DemoRole)}
        aria-label={t('demo.roleSwitch', 'Demo role')}
      >
        {DEMO_ROLES.map((r) => (
          <option key={r.id} value={r.id}>
            {r.label}
            {override === r.id ? ' *' : ''}
          </option>
        ))}
      </select>
    </label>
  );
}

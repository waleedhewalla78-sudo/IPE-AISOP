/**
 * Demo role override for Star Trans sprint (STREAM-4.1).
 * localStorage override does not change JWT auth — UX only.
 */
export type DemoRole = 'executive' | 'planner' | 'supervisor' | 'buyer';

export const DEMO_ROLE_STORAGE_KEY = 'ipe_demo_role';

export const DEMO_ROLES: { id: DemoRole; label: string }[] = [
  { id: 'executive', label: 'Executive' },
  { id: 'planner', label: 'Planner' },
  { id: 'supervisor', label: 'Supervisor' },
  { id: 'buyer', label: 'Buyer' },
];

export function readDemoRole(): DemoRole | null {
  try {
    const v = localStorage.getItem(DEMO_ROLE_STORAGE_KEY);
    if (v === 'executive' || v === 'planner' || v === 'supervisor' || v === 'buyer') return v;
  } catch {
    /* ignore */
  }
  return null;
}

export function writeDemoRole(role: DemoRole | null): void {
  try {
    if (role == null) localStorage.removeItem(DEMO_ROLE_STORAGE_KEY);
    else localStorage.setItem(DEMO_ROLE_STORAGE_KEY, role);
  } catch {
    /* ignore */
  }
}

/** Effective demo role: override → JWT role → planner default. */
export function resolveDemoRole(jwtRole?: string | null): DemoRole {
  const override = readDemoRole();
  if (override) return override;
  const r = (jwtRole ?? '').toLowerCase();
  if (r === 'executive' || r === 'manager') return 'executive';
  if (r === 'supervisor' || r === 'operator') return 'supervisor';
  if (r === 'buyer' || r === 'procurement') return 'buyer';
  return 'planner';
}

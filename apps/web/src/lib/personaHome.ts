/**
 * Persona derivation and default-home routing (Spec 039).
 *
 * JWT `role` is the authoritative source. `localStorage.ipe_persona` may override
 * the derived persona (lens only — does not change auth). The persona lens is a
 * UX preference, never an authorisation boundary.
 */

import { ROUTES } from './constants';

export type Role = 'admin' | 'planner' | 'operator' | 'manager' | 'executive' | 'supervisor' | 'buyer';

export type PersonaId =
  | 'CEO'
  | 'Ops'
  | 'Sales'
  | 'SC'
  | 'Material'
  | 'Production'
  | 'Frontline'
  | 'Finance'
  | 'Demand'
  | 'Scheduler';

export const PERSONA_STORAGE_KEY = 'ipe_persona';

/** All personas the given role is allowed to preview via the lens chip. */
export function allowedPersonasFor(role: Role | string | undefined | null): PersonaId[] {
  const r = (role ?? '').toLowerCase() as Role;
  switch (r) {
    case 'executive':
      return ['CEO', 'Finance'];
    case 'manager':
      return ['Ops', 'Sales', 'SC', 'Finance'];
    case 'planner':
      return ['Production', 'Material', 'Demand', 'Scheduler'];
    case 'buyer':
      return ['SC', 'Material'];
    case 'operator':
    case 'supervisor':
      return ['Frontline'];
    case 'admin':
      return [
        'CEO',
        'Ops',
        'Sales',
        'SC',
        'Material',
        'Production',
        'Finance',
        'Demand',
        'Scheduler',
        'Frontline',
      ];
    default:
      return ['Ops'];
  }
}

/** Default persona for a role when no override is set. */
export function defaultPersonaFor(role: Role | string | undefined | null): PersonaId {
  const r = (role ?? '').toLowerCase() as Role;
  switch (r) {
    case 'executive':
      return 'CEO';
    case 'manager':
      return 'Ops';
    case 'planner':
      return 'Production';
    case 'buyer':
      return 'Material';
    case 'operator':
    case 'supervisor':
      return 'Frontline';
    case 'admin':
      return 'Ops';
    default:
      return 'Ops';
  }
}

/**
 * Derive the effective persona from role + optional override. Override is
 * ignored when the role has no access to it (e.g. an operator cannot preview
 * `CEO`) — this keeps the lens honest to what the user is authorised to see.
 */
export function derivePersona(
  role: Role | string | undefined | null,
  override?: PersonaId | string | null,
): PersonaId {
  const allowed = allowedPersonasFor(role);
  if (override && allowed.includes(override as PersonaId)) {
    return override as PersonaId;
  }
  return defaultPersonaFor(role);
}

/** Default landing route for a persona (Spec 039 §Persona derivation). */
export function personaHome(persona: PersonaId): string {
  switch (persona) {
    case 'CEO':
    case 'Finance':
      return ROUTES.WORKSPACE;
    case 'Ops':
      return ROUTES.COMMAND_DASHBOARD;
    case 'Sales':
    case 'Demand':
      return ROUTES.PLANNING_DEMAND;
    case 'SC':
    case 'Material':
      return ROUTES.SUPPLY_PLANNING;
    case 'Production':
      return ROUTES.PLANNING_DASHBOARD;
    case 'Scheduler':
      return ROUTES.PLANNING_SCHEDULE;
    case 'Frontline':
      return ROUTES.SHOP_FLOOR;
    default:
      return ROUTES.WORKSPACE;
  }
}

/**
 * SSR-safe read of the persona override. Returns null when running outside a
 * browser or when nothing is stored.
 */
export function readPersonaOverride(): PersonaId | null {
  if (typeof window === 'undefined' || typeof window.localStorage === 'undefined') {
    return null;
  }
  try {
    const raw = window.localStorage.getItem(PERSONA_STORAGE_KEY);
    return raw ? (raw as PersonaId) : null;
  } catch {
    return null;
  }
}

export function writePersonaOverride(persona: PersonaId | null): void {
  if (typeof window === 'undefined' || typeof window.localStorage === 'undefined') return;
  try {
    if (persona === null) {
      window.localStorage.removeItem(PERSONA_STORAGE_KEY);
    } else {
      window.localStorage.setItem(PERSONA_STORAGE_KEY, persona);
    }
  } catch {
    // ignore write failures (private mode, quota, etc.)
  }
}

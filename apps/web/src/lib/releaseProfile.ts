/** Release profiles — controls hub visibility per deployment target */
export const RELEASE_PROFILE = (import.meta.env.VITE_RELEASE_PROFILE ?? 'full') as string;
export const IS_RELEASE1 = RELEASE_PROFILE === 'release1';
export const IS_RELEASE2 = RELEASE_PROFILE === 'release2';
/** Constrained R1/R2 profiles hide POST-R2 hubs (supply chain, shop floor, AI governance). */
export const IS_CONSTRAINED_RELEASE = RELEASE_PROFILE === 'release1' || RELEASE_PROFILE === 'release2';

export const RELEASE1_HUBS = ['planning', 'command-center', 'platform', 'copilot'] as const;
export const RELEASE2_HUBS = [...RELEASE1_HUBS, 'demand', 'scenarios'] as const;

/** Demand + Scenarios tabs visible in release2 and full profiles */
export const SHOW_R2_PLANNING_TABS = !IS_RELEASE1 || IS_RELEASE2;

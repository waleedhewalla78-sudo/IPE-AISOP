/** Release 1 profile — hides POST-R1 hubs (Copilot, supply network, etc.) */
export const RELEASE_PROFILE = import.meta.env.VITE_RELEASE_PROFILE ?? 'full';
export const IS_RELEASE1 = RELEASE_PROFILE === 'release1';

export const RELEASE1_HUBS = ['planning', 'command-center', 'platform'] as const;

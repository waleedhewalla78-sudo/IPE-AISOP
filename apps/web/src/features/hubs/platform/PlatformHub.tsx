import { HubShell } from '@/components/hubs/HubShell';
import { ROUTES } from '@/lib/constants';

const TABS = [
  { to: ROUTES.PLATFORM_ADMIN, label: 'Admin' },
  { to: ROUTES.PLATFORM_ONBOARDING, label: 'Onboarding' },
  { to: ROUTES.PLATFORM_MLOPS, label: 'MLOps' },
];

export function PlatformHub() {
  return (
    <HubShell
      title="Platform"
      subtitle="Tenant configuration and operations"
      tabs={TABS}
    />
  );
}

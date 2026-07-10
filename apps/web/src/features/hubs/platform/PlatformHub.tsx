import { HubShell } from '@/components/hubs/HubShell';
import { ROUTES } from '@/lib/constants';
import { t } from '@/lib/i18n';
import { IS_RELEASE1 } from '@/lib/releaseProfile';

const TABS = [
  { to: ROUTES.PLATFORM_ADMIN, label: 'Admin' },
  ...(IS_RELEASE1 ? [{ to: ROUTES.PLATFORM_ODOO_CONFIG, label: t('odooConfig.nav') }] : []),
  { to: ROUTES.PLATFORM_ONBOARDING, label: 'Onboarding' },
  { to: ROUTES.PLATFORM_MLOPS, label: 'MLOps' },
  { to: ROUTES.PLATFORM_OPS, label: 'Ops' },
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

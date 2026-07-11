import { HubShell } from '@/components/hubs/HubShell';
import { ROUTES } from '@/lib/constants';
import { t } from '@/lib/i18n';

/** Odoo connections visible in R1, R2, and full profiles (W1-05). */
const TABS = [
  { to: ROUTES.PLATFORM_ADMIN, label: 'Admin' },
  { to: ROUTES.PLATFORM_ODOO_CONFIG, label: t('admin.odoo.title', 'Odoo Connections') },
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

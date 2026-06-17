import { useSelector } from 'react-redux';
import type { RootState } from '@/store/store';

export function useTenant() {
  const tenantId = useSelector((state: RootState) => state.auth.user?.tenant_id);
  return { tenantId };
}

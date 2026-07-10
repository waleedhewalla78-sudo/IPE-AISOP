import api from '@/lib/api';
import type { OdooConfigEntity, OdooConfigListData, OdooConnectionTestResult } from './types';

export async function fetchOdooConfigEntities(): Promise<OdooConfigListData> {
  const res = await api.get('/api/v1/admin/odoo-config');
  return (res.data?.data ?? { entities: [], schema_version: 2 }) as OdooConfigListData;
}

export async function fetchOdooConfigEntity(entityKey: string): Promise<OdooConfigEntity | null> {
  const res = await api.get(`/api/v1/admin/odoo-config/${entityKey}`);
  if (!res.data?.success) return null;
  return res.data.data as OdooConfigEntity;
}

export async function fetchOdooConfigVersions(entityKey: string): Promise<OdooConfigEntity[]> {
  const res = await api.get(`/api/v1/admin/odoo-config/${entityKey}/versions`);
  return (res.data?.data?.versions ?? []) as OdooConfigEntity[];
}

export async function saveOdooConfig(
  payload: Partial<OdooConfigEntity> & { odoo_password?: string; expected_version?: number },
): Promise<OdooConfigEntity> {
  const res = await api.post('/api/v1/admin/odoo-config', {
    entity_key: payload.entity_key ?? 'primary',
    name: payload.name,
    odoo_url: payload.odoo_url,
    odoo_db: payload.odoo_db,
    odoo_username: payload.odoo_username,
    odoo_password: payload.odoo_password,
    enabled: payload.enabled,
    sync_interval_minutes: payload.sync_interval_minutes,
    field_mappings: payload.field_mappings,
    expected_version: payload.expected_version,
    change_summary: payload.change_summary,
  });
  return res.data.data as OdooConfigEntity;
}

export async function testOdooConfigConnection(
  payload: Partial<OdooConfigEntity> & { odoo_password?: string; entity_key?: string },
): Promise<OdooConnectionTestResult> {
  const res = await api.post('/api/v1/admin/odoo-config/test-connection', {
    entity_key: payload.entity_key,
    odoo_url: payload.odoo_url,
    odoo_db: payload.odoo_db,
    odoo_username: payload.odoo_username,
    odoo_password: payload.odoo_password,
  });
  return (res.data?.data ?? { connected: false }) as OdooConnectionTestResult;
}

export async function rollbackOdooConfig(entityKey: string, version: number): Promise<OdooConfigEntity> {
  const res = await api.post(`/api/v1/admin/odoo-config/${entityKey}/rollback/${version}`);
  return res.data.data as OdooConfigEntity;
}

/** ERP connection management API client (W1-05). */
import api from '@/lib/api';

export interface ErpConnection {
  id: string;
  display_name: string;
  host_url: string;
  database_name: string;
  username: string;
  erp_type: string;
  is_active: boolean;
  is_production: boolean;
  last_test_at: string | null;
  last_test_result: string | null;
  last_test_message: string | null;
  sync_interval_seconds: number;
  sync_enabled: boolean;
  api_protocol?: string;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ErpConnectionLog {
  id: string;
  action: string;
  result: string | null;
  details: Record<string, unknown> | null;
  performed_by: string | null;
  performed_at: string | null;
}

export interface ErpTestResult {
  result: 'success' | 'auth_failed' | 'unreachable' | 'timeout' | string;
  message: string;
  response_time_ms?: number | null;
  odoo_version?: string | null;
  databases_available?: string[] | null;
}

export type ErpConnectionPayload = {
  erp_type?: string;
  display_name: string;
  host_url: string;
  database_name: string;
  username: string;
  password?: string;
  is_production?: boolean;
  sync_interval_seconds?: number;
  sync_enabled?: boolean;
};

export async function listErpConnections(): Promise<ErpConnection[]> {
  const res = await api.get('/api/v1/erp/connections');
  return (res.data?.data ?? []) as ErpConnection[];
}

export async function createErpConnection(payload: ErpConnectionPayload): Promise<ErpConnection> {
  const res = await api.post('/api/v1/erp/connections', payload);
  return res.data.data as ErpConnection;
}

export async function updateErpConnection(
  id: string,
  payload: Partial<ErpConnectionPayload>,
): Promise<ErpConnection> {
  const res = await api.put(`/api/v1/erp/connections/${id}`, payload);
  return res.data.data as ErpConnection;
}

export async function deleteErpConnection(id: string): Promise<void> {
  await api.delete(`/api/v1/erp/connections/${id}`);
}

export async function testErpConnection(id: string): Promise<ErpTestResult> {
  const res = await api.post(`/api/v1/erp/connections/${id}/test`);
  return res.data.data as ErpTestResult;
}

export async function activateErpConnection(id: string): Promise<ErpConnection> {
  const res = await api.post(`/api/v1/erp/connections/${id}/activate`);
  return res.data.data as ErpConnection;
}

export async function syncErpConnectionNow(id: string): Promise<{ sync_run_id: string; status: string }> {
  const res = await api.post(`/api/v1/erp/connections/${id}/sync-now`);
  return res.data.data;
}

export async function fetchErpConnectionLogs(id: string, limit = 20): Promise<ErpConnectionLog[]> {
  const res = await api.get(`/api/v1/erp/connections/${id}/logs`, { params: { limit } });
  return (res.data?.data ?? []) as ErpConnectionLog[];
}

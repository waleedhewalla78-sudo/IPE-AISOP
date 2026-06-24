import api from '@/lib/api';
import type { CpmCascadeResult, GanttRow } from './types';

export interface ScheduleOptions {
  moIds?: string[];
  horizonHours?: number;
  strategy?: string;
  alpha?: number;
  beta?: number;
  capacityBufferPct?: number;
  overtimeAllowed?: boolean;
}

export interface MoVersionMap {
  [moId: string]: number;
}

function mapRowsFromAssignments(assignments: Record<string, unknown>[]): GanttRow[] {
  const moMap = new Map<string, GanttRow>();
  for (const a of assignments) {
    const moId = (a.mo_id as string) || 'default';
    if (!moMap.has(moId)) {
      moMap.set(moId, {
        mo_id: moId,
        mo_name: `MO-${moId.slice(0, 8)}`,
        operations: [],
      });
    }
    const row = moMap.get(moId)!;
    row.operations.push({
      id: (a.operation_id as string) || String(a.id),
      mo_id: moId,
      mo_name: row.mo_name,
      sequence: (a.sequence as number) || 0,
      work_center_id: a.work_center_id as string,
      work_center_name: (a.work_center_name as string) || (a.work_center_id as string),
      planned_start: Number(a.planned_start ?? a.start_minute ?? 0),
      planned_end: Number(a.planned_end ?? a.end_minute ?? 0),
      duration: a.duration as number,
      status: a.on_time === false ? 'delayed' : 'on_time',
    });
  }
  return Array.from(moMap.values());
}

export async function fetchActiveSchedule(): Promise<{ rows: GanttRow[]; moVersions: MoVersionMap }> {
  const res = await api.get('/api/v1/capacity/schedule/active');
  const rows = res.data?.data?.rows ?? [];
  const moVersions: MoVersionMap = {};
  for (const row of rows) {
    if (row.mo_version != null) {
      moVersions[row.mo_id] = row.mo_version;
    }
  }
  return {
    rows: rows.map((row: Record<string, unknown>) => ({
      mo_id: row.mo_id as string,
      mo_name: row.mo_name as string,
      approved: row.approved as boolean | undefined,
      operations: (row.operations as Record<string, unknown>[]).map(op => ({
        id: op.id as string,
        mo_id: op.mo_id as string,
        mo_name: op.mo_name as string,
        sequence: op.sequence as number,
        work_center_id: op.work_center_id as string,
        work_center_name: op.work_center_name as string,
        planned_start: op.planned_start as number,
        planned_end: op.planned_end as number,
        duration: op.duration as number,
        status: op.status as string,
        is_critical: op.is_critical as boolean | undefined,
        slack_minutes: op.slack_minutes as number | undefined,
      })),
    })),
    moVersions,
  };
}

export async function fetchSchedule(options: ScheduleOptions = {}): Promise<{
  rows: GanttRow[];
  moVersions: MoVersionMap;
  xaiExplanation: Record<string, unknown> | null;
  solverStatus: string;
}> {
  const body: Record<string, unknown> = {};
  if (options.moIds?.length) body.mo_ids = options.moIds;
  if (options.horizonHours) body.horizon_hours = options.horizonHours;
  if (options.strategy) body.strategy = options.strategy;
  if (options.alpha != null) body.alpha = options.alpha;
  if (options.beta != null) body.beta = options.beta;
  if (options.capacityBufferPct != null) body.capacity_buffer_pct = options.capacityBufferPct;
  if (options.overtimeAllowed != null) body.overtime_allowed = options.overtimeAllowed;

  const res = await api.post('/api/v1/capacity/schedule', body);
  const data = res.data?.data;
  const assignments = data?.schedule?.assignments ?? [];

  return {
    rows: mapRowsFromAssignments(assignments),
    moVersions: data?.mo_versions ?? {},
    xaiExplanation: data?.xai_explanation ?? null,
    solverStatus: data?.schedule?.solver_status ?? 'UNKNOWN',
  };
}

export async function approveSchedule(
  moIds: string[],
  expectedVersions?: MoVersionMap,
  approvedBy = 'planner',
): Promise<{ activated: string[]; failed: { mo_id: string; reason: string }[] }> {
  const res = await api.post('/api/v1/capacity/schedule/approve', {
    mo_ids: moIds,
    expected_versions: expectedVersions,
    approved_by: approvedBy,
  });
  if (res.data?.success === false && res.data?.error?.code === 'VERSION_CONFLICT') {
    throw new Error(res.data.error.message || 'Schedule version conflict — refresh and retry.');
  }
  const data = res.data?.data;
  return {
    activated: (data?.activated ?? []).map((a: { mo_id: string }) => a.mo_id),
    failed: data?.failed ?? [],
  };
}

export async function validateSchedule(moIds?: string[]): Promise<
  { mo_id: string; status: string; reasons: string[] }[]
> {
  const res = await api.post('/api/v1/capacity/validate', moIds?.length ? { mo_ids: moIds } : {});
  return res.data?.data?.validations ?? [];
}

export interface CpmCascadeRequest {
  mo_id: string;
  operation_id: string;
  delta_minutes: number;
  mode?: 'preview' | 'apply';
}

export async function previewCpmCascade(params: CpmCascadeRequest): Promise<CpmCascadeResult> {
  const res = await api.post('/api/v1/capacity/cpm/cascade', {
    mo_id: params.mo_id,
    operation_id: params.operation_id,
    delta_minutes: params.delta_minutes,
    mode: params.mode ?? 'preview',
  });
  if (res.data?.success === false) {
    throw new Error(res.data?.error?.message ?? 'CPM cascade preview failed');
  }
  return res.data?.data as CpmCascadeResult;
}

export async function applyCpmCascade(payload: {
  cascade_token?: string;
  operations?: CpmCascadeResult['operations'];
}): Promise<{ mo_ids: string[] }> {
  const res = await api.post('/api/v1/capacity/cpm/apply', payload);
  if (res.data?.success === false) {
    throw new Error(res.data?.error?.message ?? 'CPM apply failed');
  }
  const data = res.data?.data;
  return { mo_ids: data?.mo_ids ?? data?.affected_mo_ids ?? [] };
}

export async function downloadMsProjectExport(moIds?: string[]): Promise<void> {
  const res = await api.get('/api/v1/capacity/schedule/export/msproject', {
    params: moIds?.length ? { mo_ids: moIds.join(',') } : undefined,
    responseType: 'blob',
  });
  const blob = new Blob([res.data], { type: 'application/xml' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `ipe-schedule-${new Date().toISOString().slice(0, 10)}.xml`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

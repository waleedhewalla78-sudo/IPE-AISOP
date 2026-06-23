import api from '@/lib/api';

export interface ProjectPlanSummary {
  plan_code: string;
  plan_name: string;
  active_version_id: string | null;
  active_version_number: number | null;
  operation_count: number;
  updated_at: string | null;
}

export interface ProjectPlanVersion {
  id: string;
  version_number: number;
  is_active: boolean;
  file_name: string;
  file_size_bytes: number;
  row_count: number;
  uploaded_at: string | null;
  upload_notes: string | null;
}

export interface UploadProjectPlanResult {
  message: string;
  plan?: ProjectPlanSummary;
  version?: ProjectPlanVersion;
}

class ProjectPlanApiError extends Error {
  errors: string[];

  constructor(message: string, errors: string[] = []) {
    super(message);
    this.name = 'ProjectPlanApiError';
    this.errors = errors;
  }
}

export async function fetchProjectPlans(): Promise<ProjectPlanSummary[]> {
  const res = await api.get('/api/v1/capacity/project-plans');
  return res.data?.data?.plans ?? [];
}

export async function fetchPlanVersions(planCode: string): Promise<ProjectPlanVersion[]> {
  const res = await api.get(`/api/v1/capacity/project-plans/${encodeURIComponent(planCode)}/versions`);
  return res.data?.data?.versions ?? [];
}

export async function uploadProjectPlan(params: {
  file: File;
  mode: 'new' | 'update';
  planCode?: string;
  notes?: string;
}): Promise<UploadProjectPlanResult> {
  const form = new FormData();
  form.append('file', params.file);
  form.append('mode', params.mode);
  if (params.planCode) form.append('plan_code', params.planCode);
  if (params.notes) form.append('notes', params.notes);

  const res = await api.post('/api/v1/capacity/project-plans/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  if (!res.data?.success) {
    const err = res.data?.error;
    throw new ProjectPlanApiError(err?.message || 'Upload failed', res.data?.data?.errors ?? []);
  }
  return res.data.data as UploadProjectPlanResult;
}

export async function activatePlanVersion(planCode: string, versionId: string): Promise<{ message: string }> {
  const res = await api.post(
    `/api/v1/capacity/project-plans/${encodeURIComponent(planCode)}/versions/${versionId}/activate`,
  );
  if (!res.data?.success) {
    throw new ProjectPlanApiError(res.data?.error?.message || 'Activation failed');
  }
  return res.data.data;
}

export async function fetchProjectPlanSchedule(planCode: string) {
  const res = await api.get(`/api/v1/capacity/project-plans/${encodeURIComponent(planCode)}/schedule`);
  if (!res.data?.success) {
    throw new ProjectPlanApiError(res.data?.error?.message || 'Could not load plan schedule');
  }
  return res.data.data as {
    plan_code: string;
    version_number: number;
    rows: Array<{
      mo_id: string;
      mo_name: string;
      operations: Array<{
        id: string;
        mo_id: string;
        mo_name: string;
        sequence: number;
        work_center_id: string;
        work_center_name: string;
        planned_start: number;
        planned_end: number;
        duration: number;
        status: string;
        is_frozen?: boolean;
        is_disrupted?: boolean;
      }>;
    }>;
  };
}

export { ProjectPlanApiError };

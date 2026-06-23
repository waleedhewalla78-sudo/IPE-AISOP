import { useCallback, useEffect, useState } from 'react';
import { GanttChart } from './components/GanttChart';
import { ProjectPlanUpload } from './components/ProjectPlanUpload';
import { ScheduleControlPanel } from './components/ScheduleControlPanel';
import { ScheduleExplainPanel } from './components/ScheduleExplainPanel';
import { DigitalTwinPanel } from './components/DigitalTwinPanel';
import {
  approveSchedule,
  fetchActiveSchedule,
  fetchSchedule,
  type MoVersionMap,
  type ScheduleOptions,
} from './api';
import { fetchProjectPlanSchedule, fetchProjectPlans } from './api/projectPlans';
import type { GanttRow } from './types';

type ScheduleSource = 'solver' | 'uploaded';

export function SchedulePage() {
  const [rows, setRows] = useState<GanttRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [source, setSource] = useState<ScheduleSource>('solver');
  const [activePlanCode, setActivePlanCode] = useState<string>('');
  const [planOptions, setPlanOptions] = useState<string[]>([]);
  const [moVersions, setMoVersions] = useState<MoVersionMap>({});
  const [xaiExplanation, setXaiExplanation] = useState<Record<string, unknown> | null>(null);
  const [solverStatus, setSolverStatus] = useState<string>('');
  const [message, setMessage] = useState<string | null>(null);
  const [scheduleOptions, setScheduleOptions] = useState<ScheduleOptions>({});

  const loadSolverSchedule = useCallback(async (options?: ScheduleOptions, forceRegenerate = false) => {
    setLoading(true);
    setMessage(null);
    try {
      if (!forceRegenerate) {
        const active = await fetchActiveSchedule();
        if (active.rows.length > 0 && active.rows.some(r => r.approved)) {
          setRows(active.rows);
          setMoVersions(active.moVersions);
          setXaiExplanation(null);
          setSolverStatus('persisted');
          return;
        }
      }
      const opts = options ?? scheduleOptions;
      const data = await fetchSchedule(opts);
      setRows(data.rows);
      setMoVersions(data.moVersions);
      setXaiExplanation(data.xaiExplanation);
      setSolverStatus(data.solverStatus);
    } catch {
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [scheduleOptions]);

  const loadUploadedSchedule = useCallback(async (planCode: string) => {
    if (!planCode) {
      setRows([]);
      return;
    }
    setLoading(true);
    try {
      const data = await fetchProjectPlanSchedule(planCode);
      setRows(
        data.rows.map(row => ({
          mo_id: row.mo_id,
          mo_name: row.mo_name,
          operations: row.operations.map(op => ({
            id: op.id,
            mo_id: op.mo_id,
            mo_name: op.mo_name,
            sequence: op.sequence,
            work_center_id: op.work_center_id,
            work_center_name: op.work_center_name,
            planned_start: op.planned_start,
            planned_end: op.planned_end,
            duration: op.duration,
            status: op.status,
            is_frozen: op.is_frozen,
            is_disrupted: op.is_disrupted,
          })),
        })),
      );
    } catch {
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshPlans = useCallback(async () => {
    try {
      const plans = await fetchProjectPlans();
      const codes = plans.map(p => p.plan_code);
      setPlanOptions(codes);
      if (codes.length && !activePlanCode) {
        setActivePlanCode(codes[0]);
      }
    } catch {
      setPlanOptions([]);
    }
  }, [activePlanCode]);

  useEffect(() => {
    refreshPlans();
  }, [refreshPlans]);

  useEffect(() => {
    if (source === 'solver') {
      loadSolverSchedule();
    } else if (activePlanCode) {
      loadUploadedSchedule(activePlanCode);
    }
  }, [source, activePlanCode, loadSolverSchedule, loadUploadedSchedule]);

  const handleApprove = async (moIds: string[]) => {
    try {
      const result = await approveSchedule(moIds, moVersions);
      if (result.activated.length) {
        setMessage(`Approved ${result.activated.length} manufacturing order(s). Schedule persisted.`);
        setRows(prev =>
          prev.map(r =>
            result.activated.includes(r.mo_id) ? { ...r, approved: true } : r,
          ),
        );
        await loadSolverSchedule();
      }
      if (result.failed.length) {
        setMessage(`Some approvals failed: ${result.failed.map(f => f.reason).join(', ')}`);
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Approval failed');
    }
  };

  const handleRefresh = () => {
    if (source === 'solver') {
      loadSolverSchedule();
    } else {
      loadUploadedSchedule(activePlanCode);
    }
  };

  const handleControlApply = (options: ScheduleOptions) => {
    setScheduleOptions(options);
    loadSolverSchedule(options, true);
  };

  const handleUploadSuccess = async (planCode: string) => {
    setActivePlanCode(planCode);
    setSource('uploaded');
    await refreshPlans();
    await loadUploadedSchedule(planCode);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ipe-text">Schedule</h1>
          <p className="text-sm text-ipe-text-muted">
            Compare planned vs AI-suggested schedule, upload Excel project plans, and approve changes
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ProjectPlanUpload onUploadSuccess={handleUploadSuccess} />
          <button
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700"
            onClick={handleRefresh}
          >
            Refresh
          </button>
        </div>
      </div>

      {message && (
        <p className="text-sm rounded border border-blue-200 bg-blue-50 text-blue-800 px-3 py-2">{message}</p>
      )}

      <div className="flex flex-wrap items-center gap-4 rounded-lg border border-ipe-border bg-white p-3">
        <span className="text-sm font-medium text-ipe-text">View:</span>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="radio"
            name="schedule-source"
            checked={source === 'solver'}
            onChange={() => setSource('solver')}
          />
          AI / solver schedule
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="radio"
            name="schedule-source"
            checked={source === 'uploaded'}
            onChange={() => setSource('uploaded')}
          />
          Uploaded project plan
        </label>
        {source === 'uploaded' && (
          <select
            className="rounded border border-ipe-border px-3 py-1.5 text-sm"
            value={activePlanCode}
            onChange={e => setActivePlanCode(e.target.value)}
          >
            <option value="">Select plan...</option>
            {planOptions.map(code => (
              <option key={code} value={code}>
                {code}
              </option>
            ))}
          </select>
        )}
      </div>

      {source === 'solver' && (
        <>
          <ScheduleControlPanel onApply={handleControlApply} loading={loading} />
          <DigitalTwinPanel />
          <ScheduleExplainPanel
            explanation={xaiExplanation as Parameters<typeof ScheduleExplainPanel>[0]['explanation']}
            solverStatus={solverStatus}
          />
        </>
      )}

      <GanttChart rows={rows} loading={loading} onApprove={source === 'solver' ? handleApprove : undefined} />
    </div>
  );
}

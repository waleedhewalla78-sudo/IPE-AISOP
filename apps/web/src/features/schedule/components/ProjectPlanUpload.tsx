import { useCallback, useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import {
  activatePlanVersion,
  fetchPlanVersions,
  fetchProjectPlans,
  uploadProjectPlan,
  type ProjectPlanSummary,
  type ProjectPlanVersion,
} from '../api/projectPlans';

type UploadMode = 'new' | 'update';

interface Props {
  onUploadSuccess?: (planCode: string) => void;
}

export function ProjectPlanUpload({ onUploadSuccess }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<UploadMode>('new');
  const [plans, setPlans] = useState<ProjectPlanSummary[]>([]);
  const [selectedPlanCode, setSelectedPlanCode] = useState('');
  const [notes, setNotes] = useState('');
  const [fileName, setFileName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string; details?: string[] } | null>(null);
  const [versions, setVersions] = useState<ProjectPlanVersion[]>([]);
  const [activatingId, setActivatingId] = useState<string | null>(null);

  const loadPlans = useCallback(async () => {
    try {
      const list = await fetchProjectPlans();
      setPlans(list);
      if (!selectedPlanCode && list.length) {
        setSelectedPlanCode(list[0].plan_code);
      }
    } catch {
      setPlans([]);
    }
  }, [selectedPlanCode]);

  const loadVersions = useCallback(async (planCode: string) => {
    if (!planCode) {
      setVersions([]);
      return;
    }
    try {
      setVersions(await fetchPlanVersions(planCode));
    } catch {
      setVersions([]);
    }
  }, []);

  useEffect(() => {
    if (open) {
      loadPlans();
    }
  }, [open, loadPlans]);

  useEffect(() => {
    if (open && mode === 'update' && selectedPlanCode) {
      loadVersions(selectedPlanCode);
    }
  }, [open, mode, selectedPlanCode, loadVersions]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    setFileName(file?.name ?? '');
    setMessage(null);
  };

  const handleUpload = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) {
      setMessage({ type: 'error', text: 'Select an Excel (.xlsx) file first.' });
      return;
    }
    if (mode === 'update' && !selectedPlanCode) {
      setMessage({ type: 'error', text: 'Select an existing plan to update.' });
      return;
    }

    setUploading(true);
    setMessage(null);
    try {
      const result = await uploadProjectPlan({
        file,
        mode,
        planCode: mode === 'update' ? selectedPlanCode : undefined,
        notes: notes.trim() || undefined,
      });
      setMessage({ type: 'success', text: result.message });
      setNotes('');
      setFileName('');
      if (fileRef.current) fileRef.current.value = '';
      await loadPlans();
      if (result.plan?.plan_code) {
        setSelectedPlanCode(result.plan.plan_code);
        await loadVersions(result.plan.plan_code);
        onUploadSuccess?.(result.plan.plan_code);
      }
    } catch (err: unknown) {
      const e = err as { message?: string; errors?: string[] };
      setMessage({
        type: 'error',
        text: e.message || 'Upload failed',
        details: e.errors,
      });
    } finally {
      setUploading(false);
    }
  };

  const handleActivate = async (versionId: string) => {
    if (!selectedPlanCode) return;
    setActivatingId(versionId);
    try {
      const result = await activatePlanVersion(selectedPlanCode, versionId);
      setMessage({ type: 'success', text: result.message });
      await loadVersions(selectedPlanCode);
      onUploadSuccess?.(selectedPlanCode);
    } catch (err: unknown) {
      const e = err as { message?: string };
      setMessage({ type: 'error', text: e.message || 'Could not activate version' });
    } finally {
      setActivatingId(null);
    }
  };

  return (
    <>
      <Button type="button" variant="secondary" onClick={() => setOpen(v => !v)}>
        {open ? 'Hide Upload' : 'Upload Project Plan'}
      </Button>

      {open && (
        <Card className="p-4 space-y-4 border border-ipe-border">
          <div>
            <h2 className="text-lg font-semibold text-ipe-text">Excel Project Plan Upload</h2>
            <p className="text-sm text-ipe-text-muted">
              Upload a .xlsx file using the ProjectPlan schema. Previous versions are kept for rollback.
            </p>
          </div>

          <div className="flex flex-wrap gap-4">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="upload-mode"
                checked={mode === 'new'}
                onChange={() => setMode('new')}
              />
              Create new plan
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="upload-mode"
                checked={mode === 'update'}
                onChange={() => setMode('update')}
              />
              Update existing plan (new version)
            </label>
          </div>

          {mode === 'update' && (
            <div>
              <label className="block text-sm font-medium text-ipe-text mb-1">Existing plan</label>
              <select
                className="w-full max-w-md rounded border border-ipe-border px-3 py-2 text-sm"
                value={selectedPlanCode}
                onChange={e => setSelectedPlanCode(e.target.value)}
              >
                <option value="">Select plan...</option>
                {plans.map(p => (
                  <option key={p.plan_code} value={p.plan_code}>
                    {p.plan_code} — v{p.active_version_number ?? '?'} ({p.operation_count} ops)
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-ipe-text mb-1">Excel file (.xlsx)</label>
            <input
              ref={fileRef}
              type="file"
              accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              onChange={handleFileChange}
              className="block w-full text-sm"
            />
            {fileName && <p className="mt-1 text-xs text-ipe-text-muted">Selected: {fileName}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-ipe-text mb-1">Notes (optional)</label>
            <input
              type="text"
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="e.g. Q3 rebalance after material delay"
              className="w-full max-w-lg rounded border border-ipe-border px-3 py-2 text-sm"
            />
          </div>

          <div className="flex gap-2">
            <Button type="button" onClick={handleUpload} disabled={uploading}>
              {uploading ? 'Uploading...' : mode === 'new' ? 'Upload New Plan' : 'Upload New Version'}
            </Button>
            <a
              href="/api/v1/capacity/project-plans/schema"
              target="_blank"
              rel="noreferrer"
              className="text-sm text-blue-600 underline self-center"
            >
              View Excel schema
            </a>
          </div>

          {message && (
            <div
              className={`rounded p-3 text-sm ${
                message.type === 'success'
                  ? 'bg-green-50 text-green-800 border border-green-200'
                  : 'bg-red-50 text-red-800 border border-red-200'
              }`}
            >
              <p>{message.text}</p>
              {message.details?.length ? (
                <ul className="mt-2 list-disc pl-5">
                  {message.details.slice(0, 8).map(d => (
                    <li key={d}>{d}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          )}

          {mode === 'update' && versions.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-ipe-text mb-2">Version history</h3>
              <ul className="space-y-2 text-sm">
                {versions.map(v => (
                  <li
                    key={v.id}
                    className="flex flex-wrap items-center justify-between gap-2 rounded border border-ipe-border px-3 py-2"
                  >
                    <span>
                      v{v.version_number} — {v.file_name} ({v.row_count} rows)
                      {v.is_active ? ' • active' : ''}
                    </span>
                    {!v.is_active && (
                      <Button
                        type="button"
                        variant="secondary"
                        disabled={activatingId === v.id}
                        onClick={() => handleActivate(v.id)}
                      >
                        {activatingId === v.id ? 'Activating...' : 'Activate'}
                      </Button>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      )}
    </>
  );
}

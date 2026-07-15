import { useCallback, useEffect, useState } from 'react';
import api from '@/lib/api';
import { t } from '@/lib/i18n';

type WizardStatus = {
  current_phase: number;
  phases: Array<{
    phase: number;
    name: string;
    name_ar?: string;
    status: string;
    files: string[];
    files_uploaded?: number;
    files_remaining?: number;
  }>;
  agents_activated: string[];
  agents_pending: string[];
};

export function DataUploadCenterPage() {
  const [status, setStatus] = useState<WizardStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [fileType, setFileType] = useState('product_master');

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get('/api/v1/upload/wizard/status');
      setStatus(data);
    } catch {
      setMessage('Upload service unavailable — ensure upload-svc is running on :8120');
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function onUpload(file: File | null) {
    if (!file) return;
    setBusy(true);
    setMessage('');
    try {
      const form = new FormData();
      form.append('file', file);
      const { data: json } = await api.post(`/api/v1/upload/${fileType}`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setMessage(
        `Accepted ${json.result?.accepted ?? 0}/${json.result?.total_rows ?? 0} rows` +
          (json.result?.rejected ? ` · ${json.result.rejected} rejected` : ''),
      );
      await refresh();
    } catch (e) {
      setMessage(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function completePhase(phase: number) {
    setBusy(true);
    try {
      const { data } = await api.post(`/api/v1/upload/wizard/complete-phase/${phase}`, {});
      setMessage(data.message);
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="p-6 space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">{t('upload.title', 'Data Upload Center')}</h1>
        <p className="text-sm opacity-70 mt-1">
          {t('upload.subtitle', '5-phase onboarding wizard with live validation')}
        </p>
      </header>

      {status && (
        <div className="grid gap-3 md:grid-cols-5">
          {status.phases.map((p) => (
            <div key={p.phase} className="border border-black/10 p-3">
              <div className="text-xs uppercase tracking-wide opacity-60">Phase {p.phase}</div>
              <div className="font-medium">{p.name}</div>
              <div className="text-sm mt-2">{p.status}</div>
              <div className="text-xs mt-1 opacity-70">
                {(p.files_uploaded ?? 0)}/{p.files.length} files
              </div>
              {p.status === 'in_progress' && (
                <button
                  type="button"
                  className="mt-3 text-sm underline"
                  disabled={busy}
                  onClick={() => void completePhase(p.phase)}
                >
                  Complete phase
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      <section className="space-y-3 max-w-xl">
        <label className="block text-sm">
          File type
          <select
            className="mt-1 block w-full border border-black/20 px-2 py-1"
            value={fileType}
            onChange={(e) => setFileType(e.target.value)}
          >
            {(status?.phases.flatMap((p) => p.files) ?? ['product_master']).map((f) => (
              <option key={f} value={f}>
                {f}
              </option>
            ))}
          </select>
        </label>
        <input
          type="file"
          accept=".xlsx,.csv,.xlsm"
          disabled={busy}
          onChange={(e) => void onUpload(e.target.files?.[0] ?? null)}
        />
        {message && <p className="text-sm">{message}</p>}
      </section>

      {status && (
        <p className="text-sm opacity-70">
          Agents active: {status.agents_activated.join(', ') || 'none'} · Pending:{' '}
          {status.agents_pending.join(', ')}
        </p>
      )}
    </div>
  );
}

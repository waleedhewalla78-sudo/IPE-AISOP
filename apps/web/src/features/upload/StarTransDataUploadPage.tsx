/**
 * Star Trans Excel workbook upload — /admin/data/upload (STREAM-2.5)
 * Drag-drop / file picker → preview insert/fail → confirm commit.
 */
import { useCallback, useState } from 'react';
import { Upload, FileSpreadsheet, CheckCircle2, AlertTriangle } from 'lucide-react';
import api from '@/lib/api';
import { t } from '@/lib/i18n';
import { cn } from '@/lib/utils';

interface SheetPreview {
  sheet: string;
  insert: number;
  fail: number;
  skipped?: boolean;
  message?: string;
}

interface UploadResult {
  upload_id: string;
  file_name: string;
  valid: boolean;
  sheets_missing: string[];
  errors: string[];
  preview: {
    will_insert: number;
    will_fail: number;
    sheets: SheetPreview[];
  };
}

export function StarTransDataUploadPage() {
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [uploads, setUploads] = useState<UploadResult[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [commitResult, setCommitResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runUpload = useCallback(async (files: FileList | File[]) => {
    const list = Array.from(files).filter((f) => /\.xlsx?$/i.test(f.name));
    if (!list.length) {
      setError(t('upload.startrans.needXlsx', 'Please select one or more .xlsx files'));
      return;
    }
    setBusy(true);
    setError(null);
    setCommitResult(null);
    try {
      const form = new FormData();
      list.forEach((f) => form.append('files', f));
      const { data } = await api.post('/api/v1/data/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploads(data.uploads ?? []);
      setMessage(data.message ?? null);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        t('upload.startrans.failed', 'Upload failed');
      setError(String(detail));
      setUploads([]);
    } finally {
      setBusy(false);
    }
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      if (e.dataTransfer.files?.length) void runUpload(e.dataTransfer.files);
    },
    [runUpload],
  );

  const commit = async (uploadId: string, dryRun = false) => {
    setBusy(true);
    setError(null);
    try {
      const { data } = await api.post('/api/v1/data/upload/commit', {
        upload_id: uploadId,
        dry_run: dryRun,
      });
      setCommitResult(data);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        t('upload.startrans.commitFailed', 'Commit failed');
      setError(String(detail));
    } finally {
      setBusy(false);
    }
  };

  const totalInsert = uploads.reduce((s, u) => s + (u.preview?.will_insert ?? 0), 0);
  const totalFail = uploads.reduce((s, u) => s + (u.preview?.will_fail ?? 0), 0);

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4" data-testid="startrans-data-upload">
      <header>
        <h1 className="text-xl font-semibold text-ipe-text">
          {t('upload.startrans.title', 'Star Trans Data Upload')}
        </h1>
        <p className="mt-1 text-sm text-ipe-text-muted">
          {t(
            'upload.startrans.subtitle',
            'Upload IPE_Data_Template_StarTrans_v1.xlsx (24 sheets). Priority: Plants, Work Centers, Products, Materials, Customers, MOs. Preview rows, then confirm.',
          )}
        </p>
      </header>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={cn(
          'flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-14 transition-colors',
          dragging
            ? 'border-ipe-primary bg-ipe-primary/5'
            : 'border-ipe-border bg-ipe-surface-card',
        )}
      >
        <Upload className="h-10 w-10 text-ipe-text-muted" aria-hidden />
        <p className="text-sm text-ipe-text">
          {t('upload.startrans.drop', 'Drop .xlsx files here, or')}
        </p>
        <label className="cursor-pointer rounded-md bg-ipe-primary px-4 py-2 text-sm font-medium text-white">
          {t('upload.startrans.browse', 'Choose files')}
          <input
            type="file"
            accept=".xlsx,.xlsm"
            multiple
            className="hidden"
            disabled={busy}
            onChange={(e) => e.target.files && void runUpload(e.target.files)}
          />
        </label>
      </div>

      {error ? (
        <div className="flex items-start gap-2 rounded-lg border border-score-risk/40 bg-score-risk/10 p-3 text-sm text-score-risk">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      ) : null}

      {message ? (
        <div className="rounded-lg border border-ipe-border bg-ipe-surface-alt px-4 py-3 text-sm">
          <span className="font-medium">{message}</span>
          <span className="ml-2 text-ipe-text-muted">
            ({totalInsert} insert · {totalFail} fail)
          </span>
        </div>
      ) : null}

      {uploads.map((u) => (
        <section
          key={u.upload_id}
          className="rounded-xl border border-ipe-border bg-ipe-surface-card p-4"
        >
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <FileSpreadsheet className="h-5 w-5 text-ipe-primary" />
              <span className="font-medium">{u.file_name}</span>
              {u.valid ? (
                <CheckCircle2 className="h-4 w-4 text-score-excellent" />
              ) : (
                <AlertTriangle className="h-4 w-4 text-score-action" />
              )}
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={busy}
                className="rounded-md border border-ipe-border px-3 py-1.5 text-sm"
                onClick={() => void commit(u.upload_id, true)}
              >
                {t('upload.startrans.dryRun', 'Dry-run')}
              </button>
              <button
                type="button"
                disabled={busy || u.preview.will_insert === 0}
                className="rounded-md bg-ipe-primary px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
                onClick={() => void commit(u.upload_id, false)}
              >
                {t('upload.startrans.confirm', 'Confirm commit')}
              </button>
            </div>
          </div>

          {u.errors?.length ? (
            <ul className="mb-3 list-disc pl-5 text-xs text-score-action">
              {u.errors.map((e) => (
                <li key={e}>{e}</li>
              ))}
            </ul>
          ) : null}

          {u.sheets_missing?.length ? (
            <p className="mb-2 text-xs text-ipe-text-muted">
              Missing sheets: {u.sheets_missing.slice(0, 12).join(', ')}
              {u.sheets_missing.length > 12 ? '…' : ''}
            </p>
          ) : null}

          <div className="max-h-64 overflow-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-ipe-border text-ipe-text-muted">
                  <th className="py-1 pr-2">Sheet</th>
                  <th className="py-1 pr-2">Insert</th>
                  <th className="py-1">Fail</th>
                </tr>
              </thead>
              <tbody>
                {u.preview.sheets
                  .filter((s) => !s.skipped || s.insert + s.fail > 0)
                  .map((s) => (
                    <tr key={s.sheet} className="border-b border-ipe-border/50">
                      <td className="py-1 pr-2 font-mono">{s.sheet}</td>
                      <td className="py-1 pr-2">{s.insert}</td>
                      <td className="py-1">{s.fail}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}

      {commitResult ? (
        <div className="rounded-lg border border-score-excellent/30 bg-score-excellent/10 p-4 text-sm">
          <p className="font-medium">
            {t('upload.startrans.commitDone', 'Commit result')}: upserted{' '}
            {String(commitResult.upserted ?? 0)}, rejected {String(commitResult.rejected ?? 0)}
            {commitResult.dry_run ? ' (dry-run)' : ''}
          </p>
        </div>
      ) : null}
    </div>
  );
}

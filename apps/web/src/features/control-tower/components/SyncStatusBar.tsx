import { useEffect, useState } from 'react';
import { t } from '@/lib/i18n';
import api from '@/lib/api';

interface SyncStatus {
  last_sync?: {
    finished_at?: string;
    status?: string;
  } | null;
}

export function SyncStatusBar() {
  const [status, setStatus] = useState<SyncStatus | null>(null);

  useEffect(() => {
    api
      .get<{ success: boolean; data: SyncStatus }>('/api/v1/sync/status')
      .then((res) => setStatus(res.data.data))
      .catch(() => setStatus(null));
  }, []);

  const finished = status?.last_sync?.finished_at;
  const stale =
    !finished ||
    Date.now() - new Date(finished).getTime() > 30 * 60 * 1000;

  return (
    <div
      className={`rounded-md border px-3 py-2 text-sm ${
        stale ? 'border-amber-300 bg-amber-50' : 'border-green-300 bg-green-50'
      }`}
    >
      <span className="font-medium">{t('controlTower.lastSync')}:</span>{' '}
      {finished ? new Date(finished).toLocaleString() : '—'}{' '}
      <span className={stale ? 'text-amber-700' : 'text-green-700'}>
        ({stale ? t('controlTower.syncStale') : t('controlTower.syncOk')}
        {status?.last_sync?.status ? ` · ${status.last_sync.status}` : ''})
      </span>
    </div>
  );
}

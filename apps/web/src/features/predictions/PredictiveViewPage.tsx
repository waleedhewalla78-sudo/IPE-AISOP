import { useState } from 'react';
import api from '@/lib/api';
import { t } from '@/lib/i18n';

const SAMPLE_MO = '00000000-0000-4000-8000-000000000001';

export function PredictiveViewPage() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState('');

  async function load() {
    setError('');
    try {
      const { data: body } = await api.get(`/api/v1/feasibility/predict/${SAMPLE_MO}`);
      setData((body?.data || body) as Record<string, unknown>);
    } catch {
      setError('Predictive scoring unavailable');
    }
  }

  const predictions = (data?.predictions || {}) as Record<
    string,
    { score?: number; color?: string; primary_risk?: string }
  >;

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-end justify-between">
        <h1 className="text-2xl font-semibold">{t('predictions.title', 'Predictive Risk')}</h1>
        <button type="button" className="underline text-sm" onClick={() => void load()}>
          Load sample MO
        </button>
      </div>
      {error && <p className="text-sm">{error}</p>}
      {data && (
        <div className="space-y-3">
          <div className="text-sm">
            {t('predictions.today', 'Today')}: {(data.current as { score?: number })?.score} · Trend:{' '}
            {String(data.trend)}
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            {[3, 7, 14].map((h) => (
              <div key={h} className="border border-black/10 p-3">
                <div className="text-xs opacity-60">{t(`predictions.${h}days`, `+${h} days`)}</div>
                <div className="text-xl font-medium mt-1">{predictions[h]?.score ?? '—'}</div>
                <div className="text-sm mt-1">{predictions[h]?.color}</div>
                <div className="text-xs opacity-70 mt-2">{predictions[h]?.primary_risk}</div>
              </div>
            ))}
          </div>
          <p className="text-sm opacity-80">{String(data.recommended_action || '')}</p>
        </div>
      )}
    </div>
  );
}

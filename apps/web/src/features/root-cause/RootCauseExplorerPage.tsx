import { useState } from 'react';
import api from '@/lib/api';
import { t } from '@/lib/i18n';

const SAMPLE_MO = '00000000-0000-4000-8000-000000000001';

type ChainLevel = {
  level: number;
  description: string;
  cause_type: string;
  is_root_cause?: boolean;
};

export function RootCauseExplorerPage() {
  const [chain, setChain] = useState<ChainLevel[]>([]);
  const [recs, setRecs] = useState<Array<{ timeframe: string; action: string }>>([]);

  async function load() {
    const { data: body } = await api.get(`/api/v1/feasibility/root-cause/${SAMPLE_MO}`);
    const payload = body?.data || body;
    setChain(payload.chain || []);
    setRecs(payload.recommendations || []);
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-end justify-between">
        <h1 className="text-2xl font-semibold">{t('rootCause.title', 'Root Cause Explorer')}</h1>
        <button type="button" className="underline text-sm" onClick={() => void load()}>
          Analyze sample MO
        </button>
      </div>
      <ol className="space-y-2">
        {chain.map((level) => (
          <li key={level.level} className="border border-black/10 p-3">
            <div className="text-xs opacity-60">
              {t('rootCause.level', 'Level')} {level.level} · {t('rootCause.why', 'Why?')}
            </div>
            <div className="mt-1">{level.description}</div>
            {level.is_root_cause && (
              <div className="text-sm mt-2 font-medium">{t('rootCause.rootFound', 'Root cause')}</div>
            )}
          </li>
        ))}
      </ol>
      {recs.length > 0 && (
        <div>
          <h2 className="font-medium">{t('rootCause.recommendations', 'Recommendations')}</h2>
          <ul className="mt-2 space-y-1 text-sm">
            {recs.map((r) => (
              <li key={r.action}>
                <span className="opacity-60">{r.timeframe}:</span> {r.action}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

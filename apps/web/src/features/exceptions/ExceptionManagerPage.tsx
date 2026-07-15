import { useState } from 'react';
import api from '@/lib/api';
import { t } from '@/lib/i18n';

type ExceptionRow = {
  id?: string;
  title: string;
  severity: string;
  status: string;
  agent_id: string;
  ack_due_at?: string;
};

export function ExceptionManagerPage() {
  const [rows, setRows] = useState<ExceptionRow[]>([]);
  const [filter, setFilter] = useState('all');
  const [message, setMessage] = useState('');

  async function createSample() {
    const { data: body } = await api.post('/api/v1/exceptions', {
      agent_id: 'A2',
      exception_type: 'STOCKOUT_RISK',
      severity: 'high',
      title: 'Copper wire stockout in 5 days',
      description: 'RM-CW25 days of stock below lead time',
      entity_type: 'product',
    });
    const data = (body?.data || body) as ExceptionRow;
    setRows((prev) => [data, ...prev]);
    setMessage('Exception created');
  }

  async function acknowledge(row: ExceptionRow) {
    const { data: body } = await api.post('/api/v1/exceptions/acknowledge', {
      exception: row,
      user_id: 'planner',
    });
    const data = (body?.data || body) as ExceptionRow;
    setRows((prev) => prev.map((r) => (r === row || r.id === row.id ? data : r)));
  }

  const visible = rows.filter((r) => filter === 'all' || r.severity === filter);

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold">{t('exceptions.title', 'Exception Manager')}</h1>
          <p className="text-sm opacity-70 mt-1">{t('exceptions.slaRemaining', 'SLA countdown')}</p>
        </div>
        <button type="button" className="underline text-sm" onClick={() => void createSample()}>
          Create sample exception
        </button>
      </div>

      <select
        className="border border-black/20 px-2 py-1 text-sm"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
      >
        <option value="all">All</option>
        <option value="critical">{t('exceptions.critical', 'Critical')}</option>
        <option value="high">{t('exceptions.high', 'High')}</option>
        <option value="medium">{t('exceptions.medium', 'Medium')}</option>
      </select>

      {message && <p className="text-sm">{message}</p>}

      <ul className="space-y-2">
        {visible.map((row, idx) => (
          <li key={row.id || idx} className="border border-black/10 p-3 flex justify-between gap-4">
            <div>
              <div className="font-medium">{row.title}</div>
              <div className="text-xs opacity-70 mt-1">
                {row.agent_id} · {row.severity} · {row.status}
                {row.ack_due_at ? ` · ack due ${row.ack_due_at}` : ''}
              </div>
            </div>
            {row.status === 'open' && (
              <button type="button" className="text-sm underline" onClick={() => void acknowledge(row)}>
                {t('exceptions.acknowledge', 'Acknowledge')}
              </button>
            )}
          </li>
        ))}
        {visible.length === 0 && <li className="text-sm opacity-60">No exceptions yet</li>}
      </ul>
    </div>
  );
}

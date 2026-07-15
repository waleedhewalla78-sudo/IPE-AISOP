import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { t } from '@/lib/i18n';

type Agent = {
  agent_id: string;
  name: string;
  status: string;
  last_run: string | null;
};

export function AgentDashboardPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    api
      .get('/api/v1/agents/status')
      .then((res) => setAgents(res.data?.data?.agents || res.data?.agents || []))
      .catch(() => setError('Unable to load agent status'));
  }, []);

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">{t('agents.title', 'Agent Dashboard')}</h1>
      {error && <p className="text-sm">{error}</p>}
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {agents.map((a) => (
          <div key={a.agent_id} className="border border-black/10 p-4">
            <div className="text-xs opacity-60">{a.agent_id}</div>
            <div className="font-medium">{a.name}</div>
            <div className="mt-2 text-sm">
              {t('agents.healthy', a.status === 'healthy' ? 'Healthy' : a.status)}
            </div>
            <div className="text-xs opacity-60 mt-1">
              {t('agents.lastRun', 'Last run')}: {a.last_run || '—'}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

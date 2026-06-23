import { useState, useEffect } from 'react';

interface MLOpsModel {
  model_id: string;
  name: string;
  version: string;
  accuracy: number;
  last_trained: string;
  status: 'deployed' | 'staging' | 'retired';
  drift_psi: number;
}

interface MLOpsPageProps {
  tenantId: string;
}

export function MLOpsDashboard({ tenantId }: MLOpsPageProps) {
  const [models, setModels] = useState<MLOpsModel[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/v1/ml/models?tenant_id=${tenantId}`)
      .then(res => res.json())
      .then(data => {
        setModels(data.models || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [tenantId]);

  if (loading) return <div className="p-4">Loading MLOps Dashboard...</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">MLOps Dashboard</h1>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Total Models</div>
          <div className="text-3xl font-bold">{models.length}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Deployed</div>
          <div className="text-3xl font-bold text-green-600">
            {models.filter(m => m.status === 'deployed').length}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Avg Accuracy</div>
          <div className="text-3xl font-bold">
            {models.length ? (models.reduce((s, m) => s + m.accuracy, 0) / models.length * 100).toFixed(1) : 0}%
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Drift Alerts</div>
          <div className="text-3xl font-bold text-red-600">
            {models.filter(m => m.drift_psi > 0.25).length}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Model</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Version</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Accuracy</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Drift PSI</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Status</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Last Trained</th>
            </tr>
          </thead>
          <tbody>
            {models.map(m => (
              <tr key={m.model_id} className="border-t">
                <td className="px-4 py-3 font-medium">{m.name}</td>
                <td className="px-4 py-3">{m.version}</td>
                <td className="px-4 py-3">{(m.accuracy * 100).toFixed(1)}%</td>
                <td className="px-4 py-3">
                  <span className={m.drift_psi > 0.25 ? 'text-red-600 font-bold' : m.drift_psi > 0.1 ? 'text-yellow-600' : 'text-green-600'}>
                    {m.drift_psi.toFixed(3)}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-xs ${
                    m.status === 'deployed' ? 'bg-green-100 text-green-800' :
                    m.status === 'staging' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {m.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">{m.last_trained}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

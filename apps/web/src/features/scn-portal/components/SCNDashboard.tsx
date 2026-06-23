import { useState, useEffect } from 'react';
import api from '@/lib/api';

interface Supplier {
  id: string;
  name: string;
  score: number;
  leadTimeDays: number;
  defectRate: number;
  status: 'active' | 'inactive' | 'warning';
  tier: 1 | 2 | 3;
}

interface SCNDashboardProps {
  tenantId: string;
}

export function SCNDashboard({ tenantId }: SCNDashboardProps) {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/v1/supply-chain/suppliers', { params: { tenant_id: tenantId } })
      .then(res => {
        setSuppliers(res.data?.suppliers ?? []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [tenantId]);

  const activeSuppliers = suppliers.filter(s => s.status === 'active');
  const avgScore = suppliers.length
    ? suppliers.reduce((sum, s) => sum + s.score, 0) / suppliers.length
    : 0;

  if (loading) return <div className="p-4">Loading SCN Portal...</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Supply Chain Network Portal</h1>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Total Suppliers</div>
          <div className="text-3xl font-bold">{suppliers.length}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Active</div>
          <div className="text-3xl font-bold text-green-600">{activeSuppliers.length}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Avg Score</div>
          <div className="text-3xl font-bold">{avgScore.toFixed(1)}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">At Risk</div>
          <div className="text-3xl font-bold text-red-600">
            {suppliers.filter(s => s.score < 70).length}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Supplier</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Tier</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Score</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Lead Time</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Defect Rate</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Status</th>
            </tr>
          </thead>
          <tbody>
            {suppliers.map(s => (
              <tr key={s.id} className="border-t">
                <td className="px-4 py-3">{s.name}</td>
                <td className="px-4 py-3">Tier {s.tier}</td>
                <td className="px-4 py-3">
                  <span className={s.score >= 80 ? 'text-green-600' : s.score >= 60 ? 'text-yellow-600' : 'text-red-600'}>
                    {s.score}
                  </span>
                </td>
                <td className="px-4 py-3">{s.leadTimeDays} days</td>
                <td className="px-4 py-3">{(s.defectRate * 100).toFixed(1)}%</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-xs ${
                    s.status === 'active' ? 'bg-green-100 text-green-800' :
                    s.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {s.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

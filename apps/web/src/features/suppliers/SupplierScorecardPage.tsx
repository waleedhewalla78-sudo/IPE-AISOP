import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { t } from '@/lib/i18n';

type Supplier = {
  supplier_name: string;
  overall_score: number;
  on_time_pct: number;
  lead_time_trend: string;
  concentration_pct: number;
  recommendation?: string | null;
};

export function SupplierScorecardPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);

  useEffect(() => {
    api
      .get('/api/v1/material/suppliers/scorecard')
      .then((res) => {
        const payload = res.data?.data || res.data;
        setSuppliers(payload?.suppliers || []);
      })
      .catch(() => setSuppliers([]));
  }, []);

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">{t('supplier.scorecard', 'Supplier Scorecard')}</h1>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left border-b border-black/10">
            <th className="py-2">Supplier</th>
            <th>{t('supplier.reliability', 'Reliability')}</th>
            <th>OTD %</th>
            <th>{t('supplier.leadTimeTrend', 'Lead time trend')}</th>
            <th>{t('supplier.concentrationRisk', 'Concentration')}</th>
          </tr>
        </thead>
        <tbody>
          {suppliers.map((s) => (
            <tr key={s.supplier_name} className="border-b border-black/5">
              <td className="py-2">{s.supplier_name}</td>
              <td>{s.overall_score}</td>
              <td>{s.on_time_pct}</td>
              <td>{s.lead_time_trend}</td>
              <td>{s.concentration_pct}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Table, TableHead, TableRow, TableHeader, TableCell } from '@/components/ui/Table';
import api from '@/lib/api';
import type { MOWithConstraints, ResolutionScenario } from '@/types/cdm';

const SCENARIO_STATUSES: ResolutionScenario['status'][] = ['proposed', 'approved', 'rejected', 'expired'];

function parseScenarioStatus(status: unknown): ResolutionScenario['status'] {
  const value = String(status ?? 'proposed');
  return SCENARIO_STATUSES.includes(value as ResolutionScenario['status'])
    ? (value as ResolutionScenario['status'])
    : 'proposed';
}

function severityColor(severity: string): string {
  switch (severity) {
    case 'critical': return 'text-red-600 bg-red-50';
    case 'high': return 'text-orange-600 bg-orange-50';
    case 'medium': return 'text-yellow-600 bg-yellow-50';
    default: return 'text-green-600 bg-green-50';
  }
}

function constraintLabel(type: string): string {
  const labels: Record<string, string> = { material: 'Material', capacity: 'Capacity', labor: 'Labor', bom: 'BOM', demand: 'Demand' };
  return labels[type] ?? type;
}

export function ResolutionCenterPage() {
  const [selectedMo, setSelectedMo] = useState<MOWithConstraints | null>(null);
  const [scenarios, setScenarios] = useState<ResolutionScenario[]>([]);
  const [moList, setMoList] = useState<MOWithConstraints[]>([]);
  const [loading, setLoading] = useState(true);
  const [financial, setFinancial] = useState<{ cogm: number; revenue: number; margin: number } | null>(null);

  useEffect(() => {
    setLoading(true);
    api.get('/api/v1/resolution/scenarios')
      .then(res => {
        const scenariosData = (res.data?.data?.scenarios ?? []) as Record<string, unknown>[];
        const moMap = new Map<string, MOWithConstraints>();

        scenariosData.forEach((s: Record<string, unknown>) => {
          const moId = String(s.mo_id ?? '');
          if (!moMap.has(moId)) {
            moMap.set(moId, {
              id: moId,
              product_id: '',
              quantity: 0,
              planned_start: '',
              planned_end: '',
              feasibility_score: typeof s.business_score === 'number' ? Math.round(s.business_score * 100) : 50,
              status: 'delayed',
              created_at: '',
              delay_cause: null,
              delay_confidence: null,
              constraints: [],
            });
          }
        });

        setMoList(Array.from(moMap.values()));
        setScenarios(scenariosData.map((s: Record<string, unknown>) => ({
          id: String(s.id ?? ''),
          mo_id: String(s.mo_id ?? ''),
          strategy: String(s.strategy ?? ''),
          delivery_impact_days: typeof s.delivery_impact_days === 'number' ? s.delivery_impact_days : null,
          cost_impact: typeof s.cost_impact === 'number' ? s.cost_impact : null,
          business_score: typeof s.business_score === 'number' ? s.business_score : null,
          status: parseScenarioStatus(s.status),
          details: '',
        })));
      })
      .catch(() => {
        setMoList([]);
        setScenarios([]);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedMo) {
      setFinancial(null);
      return;
    }
    api.get('/api/v1/feasibility/queue')
      .then(async (res) => {
        const items = (res.data?.data ?? []) as Record<string, unknown>[];
        const match = items.find((item) => String(item.mo_id ?? item.erp_mo_id ?? '') === selectedMo.id);
        const productId = match?.product_id;
        if (!productId) {
          setFinancial(null);
          return;
        }
        const fin = await api.post('/api/v1/financial/project', {
          product_id: productId,
          quantity: Number(match?.quantity ?? 100),
          selling_price: 500,
        });
        const data = fin.data?.data;
        if (data) {
          setFinancial({
            cogm: Number(data.total_cost ?? 0),
            revenue: Number(data.revenue ?? 0),
            margin: Number(data.margin ?? 0),
          });
        }
      })
      .catch(() => setFinancial(null));
  }, [selectedMo]);

  useEffect(() => {
    if (!selectedMo) return;
    api.get('/api/v1/resolution/scenarios', { params: { mo_id: selectedMo.id } })
      .then(res => {
        const fetched = res.data?.data?.scenarios;
        if (fetched && fetched.length > 0) {
          setScenarios(fetched.map((s: Record<string, unknown>) => ({
            id: String(s.id ?? ''),
            mo_id: String(s.mo_id ?? ''),
            strategy: String(s.strategy ?? ''),
            delivery_impact_days: typeof s.delivery_impact_days === 'number' ? s.delivery_impact_days : null,
            cost_impact: typeof s.cost_impact === 'number' ? s.cost_impact : null,
            business_score: typeof s.business_score === 'number' ? s.business_score : null,
            status: parseScenarioStatus(s.status),
            details: '',
          })));
        }
      })
      .catch(() => {});
  }, [selectedMo]);

  const filteredScenarios = scenarios.filter(s => s.mo_id === selectedMo?.id);
  const unresolvedMos = moList.filter(m => m.status === 'delayed' || m.status === 'at_risk');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ipe-text">Resolution Center</h1>
        <p className="text-sm text-ipe-text-muted">Constrain resolution and scenario comparison</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <Card>
            <h3 className="mb-3 font-medium">Unresolved MOs ({loading ? '...' : unresolvedMos.length})</h3>
            <div className="overflow-x-auto">
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeader>MO ID</TableHeader>
                  <TableHeader>Feasibility</TableHeader>
                  <TableHeader>Cause</TableHeader>
                  <TableHeader />
                </TableRow>
              </TableHead>
              <tbody>
                {unresolvedMos.map((mo) => (
                  <TableRow
                    key={mo.id}
                    className={`cursor-pointer ${selectedMo?.id === mo.id ? 'bg-blue-50' : ''}`}
                    onClick={() => setSelectedMo(mo)}
                  >
                    <TableCell className="font-medium">{mo.id}</TableCell>
                    <TableCell>
                      <Badge variant={mo.feasibility_score && mo.feasibility_score >= 70 ? 'success' : mo.feasibility_score && mo.feasibility_score >= 50 ? 'warning' : 'danger'}>
                        {mo.feasibility_score}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-ipe-text-muted">{mo.delay_cause?.replace(/_/g, ' ')}</TableCell>
                    <TableCell>
                      <Button size="sm" variant="ghost">Select</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </tbody>
            </Table>
            </div>
            {!loading && unresolvedMos.length === 0 && <p className="text-sm text-ipe-text-muted">No unresolved MOs.</p>}
          </Card>

          {selectedMo && (
            <Card>
              <h3 className="mb-3 font-medium">Constraints &mdash; {selectedMo.id}</h3>
              <div className="space-y-3">
                {selectedMo.constraints.length > 0 ? selectedMo.constraints.map((c, i) => (
                  <div key={i} className="rounded-md border border-ipe-border p-3">
                    <div className="mb-1 flex items-center gap-2">
                      <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${severityColor(c.severity)}`}>
                        {c.severity}
                      </span>
                      <Badge variant="default">{constraintLabel(c.type)}</Badge>
                    </div>
                    <p className="text-sm text-ipe-text">{c.detail}</p>
                    {c.value !== null && (
                      <p className="mt-1 text-xs text-ipe-text-muted">Value: {c.value}</p>
                    )}
                  </div>
                )) : (
                  <p className="text-sm text-ipe-text-muted">No constraints data available for this MO.</p>
                )}
              </div>
              {selectedMo.delay_cause && (
                <div className="mt-3 rounded-md bg-ipe-surface-alt p-3">
                  <p className="text-xs font-medium text-ipe-text-muted">Classified Cause</p>
                  <p className="text-sm text-ipe-text">{selectedMo.delay_cause.replace(/_/g, ' ')}</p>
                  <p className="text-xs text-ipe-text-muted">Confidence: {((selectedMo.delay_confidence ?? 0) * 100).toFixed(0)}%</p>
                </div>
              )}
            </Card>
          )}
        </div>

        <div className="space-y-4">
          {selectedMo ? (
            <>
              <h3 className="text-lg font-medium text-ipe-text">
                Scenarios for {selectedMo.id}
                <span className="ml-2 text-sm font-normal text-ipe-text-muted">
                  ({filteredScenarios.length} proposed)
                </span>
              </h3>
              {financial && (
                <Card>
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 text-sm">
                    <div>
                      <p className="text-xs text-ipe-text-muted">COGM (baseline)</p>
                      <p className="font-semibold text-ipe-text">${financial.cogm.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-xs text-ipe-text-muted">Revenue at risk</p>
                      <p className="font-semibold text-red-600">${financial.revenue.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-xs text-ipe-text-muted">Margin</p>
                      <p className={`font-semibold ${financial.margin >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ${financial.margin.toLocaleString()}
                      </p>
                    </div>
                  </div>
                </Card>
              )}
              {filteredScenarios.length === 0 ? (
                <Card>
                  <p className="text-sm text-ipe-text-muted">No scenarios available for this MO.</p>
                </Card>
              ) : (
                filteredScenarios.map((sc) => (
                  <Card key={sc.id}>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="mb-2 flex items-center gap-2">
                          <h4 className="font-medium text-ipe-text">{sc.strategy}</h4>
                          <Badge variant={sc.status === 'approved' ? 'success' : sc.status === 'rejected' ? 'danger' : 'warning'}>
                            {sc.status}
                          </Badge>
                          {sc.business_score !== null && (
                            <span className="ml-auto text-sm font-semibold tabular-nums">
                              Score: {sc.business_score.toFixed(2)}
                            </span>
                          )}
                        </div>
                        <p className="mb-3 text-sm text-ipe-text">{sc.details}</p>
                        <div className="flex flex-wrap gap-4 text-xs text-ipe-text-muted">
                          {sc.delivery_impact_days !== null && (
                            <span className={sc.delivery_impact_days < 0 ? 'text-green-600' : 'text-red-600'}>
                              Delivery: {sc.delivery_impact_days > 0 ? '+' : ''}{sc.delivery_impact_days}d
                            </span>
                          )}
                          {sc.cost_impact !== null && (
                            <span className={sc.cost_impact > 0 ? 'text-red-600' : 'text-green-600'}>
                              Scenario cost: ${sc.cost_impact.toLocaleString()}
                            </span>
                          )}
                          {financial && (
                            <>
                              <span>COGM: ${financial.cogm.toLocaleString()}</span>
                              <span>Revenue: ${financial.revenue.toLocaleString()}</span>
                              <span>Margin: ${financial.margin.toLocaleString()}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="mt-3 flex gap-2 border-t border-ipe-border pt-3">
                      <Button size="sm" variant="primary">Approve</Button>
                      <Button size="sm" variant="ghost">Reject</Button>
                    </div>
                  </Card>
                ))
              )}
            </>
          ) : (
            <Card>
              <div className="flex flex-col items-center justify-center py-12">
                <p className="text-lg font-medium text-ipe-text-muted">Select an MO</p>
                <p className="mt-1 text-sm text-ipe-text-muted">Choose an unresolved MO from the left panel to view resolution scenarios.</p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

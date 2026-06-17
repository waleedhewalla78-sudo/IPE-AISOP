import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Table, TableHead, TableRow, TableHeader, TableCell } from '@/components/ui/Table';
import api from '@/lib/api';
import type { MOWithConstraints, ResolutionScenario } from '@/types/cdm';

const MOCK_MO_LIST: MOWithConstraints[] = [
  {
    id: 'MO-1001', product_id: 'PROD-A', quantity: 500, planned_start: '2026-07-01T08:00:00', planned_end: '2026-07-05T17:00:00',
    feasibility_score: 45, status: 'delayed', created_at: '2026-06-20T10:00:00',
    delay_cause: 'material_shortage', delay_confidence: 0.87,
    constraints: [
      { type: 'material', severity: 'critical', detail: 'Raw material X out of stock', value: 200 },
      { type: 'capacity', severity: 'high', detail: 'Assembly line 1 at 97% utilization', value: 97 },
    ],
  },
  {
    id: 'MO-1004', product_id: 'PROD-C', quantity: 300, planned_start: '2026-06-28T08:00:00', planned_end: '2026-07-02T17:00:00',
    feasibility_score: 33, status: 'delayed', created_at: '2026-06-18T09:00:00',
    delay_cause: 'supplier_delay', delay_confidence: 0.92,
    constraints: [
      { type: 'material', severity: 'critical', detail: 'Supplier ABC missed shipment, ETA +5 days', value: 5 },
      { type: 'labor', severity: 'medium', detail: '2 operators absent', value: 2 },
    ],
  },
  {
    id: 'MO-1008', product_id: 'PROD-D', quantity: 200, planned_start: '2026-06-30T08:00:00', planned_end: '2026-07-03T17:00:00',
    feasibility_score: 40, status: 'at_risk', created_at: '2026-06-22T14:00:00',
    delay_cause: 'capacity_overload', delay_confidence: 0.78,
    constraints: [
      { type: 'capacity', severity: 'critical', detail: 'Machining center fully booked', value: 100 },
      { type: 'bom', severity: 'low', detail: 'Alternative BOM available', value: null },
    ],
  },
];

const MOCK_SCENARIOS: ResolutionScenario[] = [
  {
    id: 'S-001', mo_id: 'MO-1001', strategy: 'Expedite supplier',
    delivery_impact_days: -2, cost_impact: 1500, business_score: 0.85, status: 'proposed',
    details: 'Pay supplier ABC expedite fee of $1,500 to deliver 3 days early',
  },
  {
    id: 'S-002', mo_id: 'MO-1001', strategy: 'Substitute material',
    delivery_impact_days: 0, cost_impact: 500, business_score: 0.72, status: 'proposed',
    details: 'Use approved substitute material X2 with minor process adjustment',
  },
  {
    id: 'S-003', mo_id: 'MO-1001', strategy: 'Reallocate capacity',
    delivery_impact_days: 0, cost_impact: 0, business_score: 0.64, status: 'proposed',
    details: 'Shift to Assembly line 2 with 2-day delay',
  },
  {
    id: 'S-004', mo_id: 'MO-1004', strategy: 'Split order',
    delivery_impact_days: 1, cost_impact: 800, business_score: 0.78, status: 'proposed',
    details: 'Produce 50% now, remaining 50% when supplier material arrives',
  },
  {
    id: 'S-005', mo_id: 'MO-1008', strategy: 'Overtime shift',
    delivery_impact_days: -1, cost_impact: 2000, business_score: 0.81, status: 'proposed',
    details: 'Add weekend overtime shift to clear machining backlog',
  },
];

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
  const [scenarios, setScenarios] = useState<ResolutionScenario[]>(MOCK_SCENARIOS);

  useEffect(() => {
    if (!selectedMo) return;
    api.get('/api/v1/resolution/scenarios', { params: { mo_id: selectedMo.id } })
      .then(res => {
        const fetched = res.data?.data?.scenarios;
        if (fetched && fetched.length > 0) {
          setScenarios(fetched.map((s: Record<string, unknown>) => ({
            id: s.id, mo_id: s.mo_id, strategy: s.strategy,
            delivery_impact_days: null, cost_impact: null,
            business_score: s.business_score, status: s.status,
            details: '',
          })));
        }
      })
      .catch(() => {
        setScenarios(MOCK_SCENARIOS.filter(s => s.mo_id === selectedMo.id));
      });
  }, [selectedMo]);

  const filteredScenarios = scenarios.filter(s => s.mo_id === selectedMo?.id);
  const unresolvedMos = MOCK_MO_LIST.filter(m => m.status === 'delayed' || m.status === 'at_risk');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ipe-text">Resolution Center</h1>
        <p className="text-sm text-ipe-text-muted">Constrain resolution and scenario comparison</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <Card>
            <h3 className="mb-3 font-medium">Unresolved MOs ({unresolvedMos.length})</h3>
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
            {unresolvedMos.length === 0 && <p className="text-sm text-ipe-text-muted">No unresolved MOs.</p>}
          </Card>

          {selectedMo && (
            <Card>
              <h3 className="mb-3 font-medium">Constraints &mdash; {selectedMo.id}</h3>
              <div className="space-y-3">
                {selectedMo.constraints.map((c, i) => (
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
                ))}
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
                        <div className="flex gap-4 text-xs text-ipe-text-muted">
                          {sc.delivery_impact_days !== null && (
                            <span className={sc.delivery_impact_days < 0 ? 'text-green-600' : 'text-red-600'}>
                              Delivery: {sc.delivery_impact_days > 0 ? '+' : ''}{sc.delivery_impact_days}d
                            </span>
                          )}
                          {sc.cost_impact !== null && (
                            <span className={sc.cost_impact > 0 ? 'text-red-600' : 'text-green-600'}>
                              Cost: ${sc.cost_impact.toLocaleString()}
                            </span>
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
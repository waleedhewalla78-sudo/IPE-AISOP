import { Card } from '@/components/ui/Card';
import { Table, TableHead, TableRow, TableHeader, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { DateCell } from '@/components/ui/DateCell';
import type { DemandSummary } from '../types';

interface DemandOverviewProps {
  demands: DemandSummary[];
}

const statusVariant = (status: string) => {
  switch (status) {
    case 'new': return 'warning';
    case 'confirmed': return 'success';
    case 'cancelled': return 'danger';
    default: return 'default';
  }
};

export function DemandOverview({ demands }: DemandOverviewProps) {
  if (demands.length === 0) {
    return (
      <Card>
        <h3 className="mb-2 font-medium">Demand Overview</h3>
        <p className="text-sm text-ipe-text-muted">No demands loaded.</p>
      </Card>
    );
  }

  return (
    <Card>
      <h3 className="mb-3 font-medium">Demand Overview ({demands.length})</h3>
      <Table>
        <TableHead>
          <TableRow>
            <TableHeader>Product</TableHeader>
            <TableHeader>Qty</TableHeader>
            <TableHeader>Required</TableHeader>
            <TableHeader>Type</TableHeader>
            <TableHeader>Priority</TableHeader>
            <TableHeader>Status</TableHeader>
          </TableRow>
        </TableHead>
        <tbody>
          {demands.map((d) => (
            <TableRow key={d.id}>
              <TableCell className="font-medium">{d.product_name}</TableCell>
              <TableCell>{d.quantity}</TableCell>
              <TableCell><DateCell value={d.required_date} /></TableCell>
              <TableCell><Badge variant="default">{d.demand_type}</Badge></TableCell>
              <TableCell>{d.priority_score?.toFixed(2) ?? '-'}</TableCell>
              <TableCell><Badge variant={statusVariant(d.status)}>{d.status}</Badge></TableCell>
            </TableRow>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}

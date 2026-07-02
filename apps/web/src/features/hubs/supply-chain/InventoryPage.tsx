import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Table, TableHead, TableRow, TableHeader, TableCell } from '@/components/ui/Table';
import api from '@/lib/api';

interface InventoryProduct {
  product_id?: string;
  product_name?: string;
  sku?: string;
  on_hand_qty?: number;
  uom?: string;
}

export function InventoryPage() {
  const [products, setProducts] = useState<InventoryProduct[]>([]);
  const [totalProducts, setTotalProducts] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await api.get('/api/v1/material/inventory-summary');
        const data = res.data?.data ?? {};
        const list = (data.products ?? data.finished_goods ?? data.items ?? []) as InventoryProduct[];
        setProducts(list);
        setTotalProducts(data.total_products ?? list.length);
      } catch {
        setProducts([]);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-ipe-border border-t-ipe-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <p className="text-sm text-ipe-text-muted">Finished goods on hand</p>
        <p className="text-2xl font-bold text-ipe-text">{totalProducts} SKUs</p>
      </Card>
      <Card>
        <Table>
          <TableHead>
            <TableRow>
              <TableHeader>Product</TableHeader>
              <TableHeader>SKU</TableHeader>
              <TableHeader>On hand</TableHeader>
            </TableRow>
          </TableHead>
          <tbody>
            {products.map((p, i) => (
              <TableRow key={p.product_id ?? p.sku ?? i}>
                <TableCell>{p.product_name ?? '—'}</TableCell>
                <TableCell>{p.sku ?? p.product_id ?? '—'}</TableCell>
                <TableCell>{p.on_hand_qty ?? '—'} {p.uom ?? ''}</TableCell>
              </TableRow>
            ))}
            {products.length === 0 && (
              <TableRow>
                <TableCell colSpan={3} className="text-center text-ipe-text-muted">
                  No inventory data
                </TableCell>
              </TableRow>
            )}
          </tbody>
        </Table>
      </Card>
    </div>
  );
}

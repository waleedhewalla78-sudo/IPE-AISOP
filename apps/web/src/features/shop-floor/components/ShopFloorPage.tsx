import { useState, useEffect, useRef } from 'react';
import api from '@/lib/api';

interface ShopFloorItem {
  id: string;
  mo_id: string;
  workcenter: string;
  status: 'in_progress' | 'pending' | 'completed' | 'on_hold';
  progress: number;
  operator: string;
  start_time: string;
}

interface ShopFloorPageProps {
  tenantId: string;
}

export function ShopFloorPage({ tenantId }: ShopFloorPageProps) {
  const [items, setItems] = useState<ShopFloorItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [pendingSync, setPendingSync] = useState(0);
  const scanInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  useEffect(() => {
    api.get('/api/v1/shop-floor/items', { params: { tenant_id: tenantId } })
      .then(res => {
        setItems(res.data?.items ?? []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [tenantId]);

  const handleBarcodeScan = (barcode: string) => {
    const item = items.find(i => i.mo_id === barcode || i.id === barcode);
    if (item) {
      setItems(prev => prev.map(i =>
        i.id === item.id
          ? { ...i, progress: Math.min(100, i.progress + 10), status: 'in_progress' as const }
          : i
      ));
      if (!isOnline) {
        setPendingSync(prev => prev + 1);
        localStorage.setItem('ipe_pending_sync', JSON.stringify([...items]));
      }
    }
  };

  if (loading) return <div className="p-4">Loading Shop Floor...</div>;

  const inProgress = items.filter(i => i.status === 'in_progress');
  const pending = items.filter(i => i.status === 'pending');

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Shop Floor PWA</h1>
        <div className="flex items-center gap-4">
          <span className={`px-3 py-1 rounded text-sm ${isOnline ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
            {isOnline ? 'Online' : 'Offline'}
          </span>
          {pendingSync > 0 && (
            <span className="px-3 py-1 rounded text-sm bg-yellow-100 text-yellow-800">
              {pendingSync} pending sync
            </span>
          )}
        </div>
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">Scan Barcode</label>
        <input
          ref={scanInputRef}
          type="text"
          className="w-full px-4 py-2 border rounded-lg"
          placeholder="Scan MO barcode or enter ID..."
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleBarcodeScan((e.target as HTMLInputElement).value);
              (e.target as HTMLInputElement).value = '';
            }
          }}
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div>
          <h2 className="text-lg font-semibold mb-3">In Progress ({inProgress.length})</h2>
          <div className="space-y-3">
            {inProgress.map(item => (
              <div key={item.id} className="bg-white rounded-lg shadow p-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium">{item.mo_id}</span>
                  <span className="text-sm text-gray-500">{item.workcenter}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${item.progress}%` }}
                  />
                </div>
                <div className="flex justify-between mt-2 text-sm text-gray-500">
                  <span>{item.operator}</span>
                  <span>{item.progress}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-3">Pending ({pending.length})</h2>
          <div className="space-y-3">
            {pending.map(item => (
              <div key={item.id} className="bg-white rounded-lg shadow p-4 border-l-4 border-yellow-400">
                <div className="flex justify-between items-center">
                  <span className="font-medium">{item.mo_id}</span>
                  <span className="text-sm text-gray-500">{item.workcenter}</span>
                </div>
                <div className="text-sm text-gray-500 mt-1">{item.operator}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

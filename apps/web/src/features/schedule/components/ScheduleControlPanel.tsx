import { useState } from 'react';
import type { ScheduleOptions } from '../api';

const STRATEGIES = [
  { id: 'hybrid', label: 'Hybrid (default)' },
  { id: 'edd', label: 'Earliest due date' },
  { id: 'throughput', label: 'Maximum throughput' },
  { id: 'revenue', label: 'Revenue focus' },
  { id: 'inventory', label: 'Inventory optimization' },
];

interface Props {
  onApply: (options: ScheduleOptions) => void;
  loading?: boolean;
}

export function ScheduleControlPanel({ onApply, loading }: Props) {
  const [strategy, setStrategy] = useState('hybrid');
  const [deliveryFocus, setDeliveryFocus] = useState(70);
  const [efficiencyFocus, setEfficiencyFocus] = useState(50);
  const [capacityBuffer, setCapacityBuffer] = useState(10);
  const [overtimeAllowed, setOvertimeAllowed] = useState(true);

  const handleRegenerate = () => {
    onApply({
      strategy,
      alpha: 1 - deliveryFocus / 100,
      beta: efficiencyFocus / 100,
      capacityBufferPct: capacityBuffer,
      overtimeAllowed,
    });
  };

  return (
    <div className="rounded-lg border border-ipe-border bg-white p-4 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-ipe-text">Optimization controls</h3>
        <button
          type="button"
          className="px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
          onClick={handleRegenerate}
          disabled={loading}
        >
          Regenerate schedule
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <label className="text-sm space-y-1">
          <span className="text-ipe-text-muted">Strategy</span>
          <select
            className="w-full rounded border border-ipe-border px-2 py-1.5"
            value={strategy}
            onChange={e => setStrategy(e.target.value)}
          >
            {STRATEGIES.map(s => (
              <option key={s.id} value={s.id}>{s.label}</option>
            ))}
          </select>
        </label>

        <label className="text-sm space-y-1">
          <span className="text-ipe-text-muted">Delivery focus ({deliveryFocus}%)</span>
          <input
            type="range"
            min={0}
            max={100}
            value={deliveryFocus}
            onChange={e => setDeliveryFocus(Number(e.target.value))}
            className="w-full"
          />
        </label>

        <label className="text-sm space-y-1">
          <span className="text-ipe-text-muted">Efficiency focus ({efficiencyFocus}%)</span>
          <input
            type="range"
            min={0}
            max={100}
            value={efficiencyFocus}
            onChange={e => setEfficiencyFocus(Number(e.target.value))}
            className="w-full"
          />
        </label>

        <label className="text-sm space-y-1">
          <span className="text-ipe-text-muted">Capacity buffer ({capacityBuffer}%)</span>
          <input
            type="range"
            min={0}
            max={20}
            step={5}
            value={capacityBuffer}
            onChange={e => setCapacityBuffer(Number(e.target.value))}
            className="w-full"
          />
        </label>
      </div>

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={overtimeAllowed}
          onChange={e => setOvertimeAllowed(e.target.checked)}
        />
        Allow overtime scheduling
      </label>
    </div>
  );
}

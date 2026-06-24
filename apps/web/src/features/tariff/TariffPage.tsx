import { TariffShockPanel } from './components/TariffShockPanel';

export function TariffPage() {
  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold text-ipe-text">Tariff Resilience</h1>
        <p className="text-sm text-ipe-text-muted">
          Simulate regional tariff shocks and review margin erosion with BOM substitute drafts
        </p>
      </div>
      <TariffShockPanel />
    </div>
  );
}

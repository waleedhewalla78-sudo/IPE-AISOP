/** Consistent number / percent formatting (STREAM-6.3). */
export function formatPercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—';
  const n = Number(value);
  if (Math.abs(n) >= 50) return `${Math.round(n)}%`;
  return `${n.toFixed(1)}%`;
}

export function formatNumber(value: number | null | undefined, digits = 0): string {
  if (value == null || Number.isNaN(value)) return '—';
  return Number(value).toFixed(digits);
}

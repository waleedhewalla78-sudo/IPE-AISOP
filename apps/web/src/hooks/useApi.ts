import { useState, useCallback } from 'react';
import api from '@/lib/api';
import type { APIResponse } from '@/types/api';

export function useApi<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async (params?: Record<string, unknown>) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<APIResponse<T>>(url, { params });
      if (response.data.success) {
        setData(response.data.data ?? null);
      } else {
        setError(response.data.error?.message ?? 'Unknown error');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed');
    } finally {
      setLoading(false);
    }
  }, [url]);

  return { data, loading, error, fetch };
}

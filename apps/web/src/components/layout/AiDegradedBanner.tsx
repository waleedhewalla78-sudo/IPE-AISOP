import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { getLocale, t } from '@/lib/i18n';

type AiStatus = {
  ollama_available?: boolean;
  show_amber_banner?: boolean;
  banner_message_en?: string;
  banner_message_ar?: string;
  degrade_mode?: boolean;
};

/**
 * Amber banner when Ollama is unreachable — Phase 8 Wave 1.
 * Core planning continues; narratives degrade to rule-based.
 */
export function AiDegradedBanner() {
  const [show, setShow] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    let cancelled = false;
    api
      .get('/api/v1/phase8/ai-status')
      .then((res) => {
        if (cancelled) return;
        const payload = res.data as { data?: AiStatus } | AiStatus;
        const data = (payload as { data?: AiStatus }).data ?? (payload as AiStatus);
        const flag = data?.show_amber_banner ?? !data?.ollama_available;
        if (flag) {
          setShow(true);
          const locale = getLocale();
          setMessage(
            locale === 'ar'
              ? data.banner_message_ar || t('ai.degradedBanner')
              : data.banner_message_en || t('ai.degradedBanner'),
          );
        }
      })
      .catch(() => {
        // If status endpoint unreachable, still hint degrade without crashing UI
        if (!cancelled) {
          setShow(true);
          setMessage(t('ai.degradedBanner'));
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!show) return null;

  return (
    <div
      role="status"
      className="border-b border-amber-300 bg-amber-50 px-4 py-2 text-sm text-amber-950"
      data-testid="ai-degraded-banner"
    >
      {message}
    </div>
  );
}

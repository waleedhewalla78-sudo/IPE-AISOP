import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { t } from '@/lib/i18n';

interface CopilotQueryData {
  intent?: string;
  response?: string;
  sources?: string[];
  agent_role?: string;
  follow_up_suggestions?: string[];
}

interface Message {
  role: 'user' | 'assistant';
  text: string;
  intent?: string;
  sources?: string[];
}

const ROLES = [
  { value: 'planner', labelKey: 'copilot.role.planner' },
  { value: 'manager', labelKey: 'copilot.role.manager' },
  { value: 'supervisor', labelKey: 'copilot.role.supervisor' },
  { value: 'executive', labelKey: 'copilot.role.executive' },
];

/** Kong upstream timeout for copilot LLM routes (seconds). */
const COPILOT_TIMEOUT_MS = 300_000;

function getApiBaseUrl(): string {
  return import.meta.env.DEV ? '' : (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000');
}

function parseJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const base64 = token.split('.')[1];
    return JSON.parse(atob(base64));
  } catch {
    return null;
  }
}

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const token = localStorage.getItem('access_token');
  if (token) {
    headers.Authorization = `Bearer ${token}`;
    const payload = parseJwtPayload(token);
    if (payload?.tenant_id) headers['X-Tenant-ID'] = String(payload.tenant_id);
  }
  return headers;
}

async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeoutMs: number = COPILOT_TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new Error('Copilot request timed out after 300 seconds. Try a shorter question or check LLM availability.');
    }
    throw err;
  } finally {
    window.clearTimeout(timer);
  }
}

export function CopilotPanel() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [role, setRole] = useState('planner');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [agentLabel, setAgentLabel] = useState('Production Planner');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const init = async () => {
      const token = localStorage.getItem('access_token');
      const payload = token ? parseJwtPayload(token) : null;
      const jwtRole = typeof payload?.role === 'string' ? payload.role : 'planner';
      setRole(jwtRole);
      try {
        const res = await fetchWithTimeout(`${getApiBaseUrl()}/api/v1/copilot/session`, {
          method: 'POST',
          headers: authHeaders(),
          body: JSON.stringify({ role: jwtRole }),
        });
        if (res.ok) {
          const body = await res.json() as { data?: { session_id?: string; agent?: string; follow_up_suggestions?: string[] } };
          setSessionId(body.data?.session_id ?? null);
          setAgentLabel(body.data?.agent ?? 'Copilot');
          setSuggestions(body.data?.follow_up_suggestions ?? []);
        }
      } catch {
        /* offline */
      }
    };
    void init();
  }, []);

  const submitQuery = async (q: string, activeRole: string): Promise<Message> => {
    const res = await fetchWithTimeout(`${getApiBaseUrl()}/api/v1/copilot/query`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ query: q, stream: false, session_id: sessionId, role: activeRole }),
    });

    if (!res.ok) {
      throw new Error(`Copilot request failed (${res.status})`);
    }

    const payload = await res.json() as { success?: boolean; data?: CopilotQueryData };
    const data = payload.data;
    if (data?.follow_up_suggestions?.length) {
      setSuggestions(data.follow_up_suggestions);
    }
    return {
      role: 'assistant',
      text: data?.response?.trim() || t('copilot.noResponse'),
      intent: data?.intent,
      sources: data?.sources,
    };
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const userMsg: Message = { role: 'user', text: query };
    setMessages((prev) => [...prev, userMsg]);
    const q = query;
    setQuery('');
    setLoading(true);

    try {
      const assistantMsg = await submitQuery(q, role);
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const message = err instanceof Error ? err.message : t('copilot.offline');
      setMessages((prev) => [...prev, {
        role: 'assistant',
        text: message.includes('timed out') ? message : t('copilot.offline'),
      }]);
    } finally {
      setLoading(false);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
    }
  };

  const onRoleChange = async (nextRole: string) => {
    setRole(nextRole);
    const match = ROLES.find((r) => r.value === nextRole);
    setAgentLabel(match ? t(match.labelKey) : nextRole);
    try {
      const res = await fetchWithTimeout(`${getApiBaseUrl()}/api/v1/copilot/session`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ role: nextRole }),
      });
      if (res.ok) {
        const body = await res.json() as { data?: { session_id?: string; follow_up_suggestions?: string[] } };
        setSessionId(body.data?.session_id ?? null);
        setSuggestions(body.data?.follow_up_suggestions ?? []);
      }
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="flex h-full flex-col space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-ipe-text">{t('copilot.title')}</h1>
          <p className="text-sm text-ipe-text-muted">{agentLabel} — {t('copilot.subtitle')}</p>
        </div>
        <label className="text-sm text-ipe-text-muted">
          {t('copilot.agentRole')}{' '}
          <select
            className="ms-2 rounded border border-ipe-border bg-white px-2 py-1 text-ipe-text"
            value={role}
            onChange={(e) => void onRoleChange(e.target.value)}
          >
            {ROLES.map((r) => (
              <option key={r.value} value={r.value}>{t(r.labelKey)}</option>
            ))}
          </select>
        </label>
      </div>

      {suggestions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {suggestions.slice(0, 3).map((s) => (
            <button
              key={s}
              type="button"
              className="rounded-full border border-ipe-border bg-ipe-surface-alt px-3 py-1 text-xs text-ipe-text hover:bg-white"
              onClick={() => setQuery(s)}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="flex-1 space-y-4 overflow-auto">
        {messages.length === 0 && (
          <Card>
            <p className="text-sm text-ipe-text-muted">{t('copilot.emptyHint')}</p>
          </Card>
        )}
        {messages.map((msg, i) => (
          <Card key={i} className={msg.role === 'user' ? 'ms-4 sm:ms-12' : 'me-4 sm:me-12'}>
            <div className="mb-1 flex items-center gap-2">
              <span className="text-sm font-medium text-ipe-text-muted">
                {msg.role === 'user' ? t('copilot.you') : t('copilot.assistant')}
              </span>
              {msg.intent && (
                <span className="rounded bg-ipe-surface-alt px-2 py-0.5 text-xs text-ipe-text-muted">
                  {msg.intent}
                </span>
              )}
            </div>
            <p className="mt-1 whitespace-pre-wrap text-sm text-ipe-text">{msg.text}</p>
            {msg.sources && msg.sources.length > 0 && (
              <p className="mt-1 text-xs text-ipe-text-muted">{t('copilot.sources')}: {msg.sources.join(', ')}</p>
            )}
          </Card>
        ))}
        {loading && (
          <Card className="me-4 sm:me-12">
            <p className="text-sm text-ipe-text-muted">{t('copilot.thinking')}</p>
          </Card>
        )}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t('copilot.placeholder')}
          className="flex-1"
          disabled={loading}
        />
        <Button type="submit" disabled={loading || !query.trim()}>
          {loading ? '...' : t('copilot.send')}
        </Button>
      </form>
    </div>
  );
}

import { useState, useRef, type FormEvent } from 'react';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

interface CopilotQueryData {
  intent?: string;
  response?: string;
  sources?: string[];
}

interface Message {
  role: 'user' | 'assistant';
  text: string;
  intent?: string;
  sources?: string[];
}

function getApiBaseUrl(): string {
  return import.meta.env.DEV ? '' : (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000');
}

export function CopilotPanel() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const submitQuery = async (q: string): Promise<Message> => {
    const token = localStorage.getItem('access_token');
    const res = await fetch(`${getApiBaseUrl()}/api/v1/copilot/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ query: q, stream: false }),
    });

    if (!res.ok) {
      throw new Error(`Copilot request failed (${res.status})`);
    }

    const payload = await res.json() as { success?: boolean; data?: CopilotQueryData };
    const data = payload.data;
    return {
      role: 'assistant',
      text: data?.response?.trim() || 'No response generated.',
      intent: data?.intent,
      sources: data?.sources,
    };
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const userMsg: Message = { role: 'user', text: query };
    setMessages(prev => [...prev, userMsg]);
    const q = query;
    setQuery('');
    setLoading(true);

    try {
      const assistantMsg = await submitQuery(q);
      setMessages(prev => [...prev, assistantMsg]);
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: 'Copilot is offline or could not reach the API. Check that Kong, nlp-svc, and mat-svc are running.',
      }]);
    } finally {
      setLoading(false);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
    }
  };

  return (
    <div className="flex h-full flex-col space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-ipe-text">Copilot</h1>
        <p className="text-sm text-ipe-text-muted">Ask questions about your production plan</p>
      </div>
      <div className="flex-1 space-y-4 overflow-auto">
        {messages.length === 0 && (
          <Card>
            <p className="text-sm text-ipe-text-muted">
              Ask about demand, material status, capacity, delays, feasibility, or resolution strategies.
            </p>
          </Card>
        )}
        {messages.map((msg, i) => (
          <Card key={i} className={msg.role === 'user' ? 'ml-4 sm:ml-12' : 'mr-4 sm:mr-12'}>
            <div className="mb-1 flex items-center gap-2">
              <span className="text-sm font-medium text-ipe-text-muted">
                {msg.role === 'user' ? 'You' : 'IPE Copilot'}
              </span>
              {msg.intent && (
                <span className="rounded bg-ipe-surface-alt px-2 py-0.5 text-xs text-ipe-text-muted">
                  {msg.intent}
                </span>
              )}
            </div>
            <p className="mt-1 text-sm text-ipe-text whitespace-pre-wrap">{msg.text}</p>
            {msg.sources && msg.sources.length > 0 && (
              <p className="mt-1 text-xs text-ipe-text-muted">Sources: {msg.sources.join(', ')}</p>
            )}
          </Card>
        ))}
        {loading && (
          <Card className="mr-4 sm:mr-12">
            <p className="text-sm text-ipe-text-muted">Thinking...</p>
          </Card>
        )}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Ask about your production..."
          className="flex-1"
          disabled={loading}
        />
        <Button type="submit" disabled={loading || !query.trim()}>
          {loading ? '...' : 'Send'}
        </Button>
      </form>
    </div>
  );
}

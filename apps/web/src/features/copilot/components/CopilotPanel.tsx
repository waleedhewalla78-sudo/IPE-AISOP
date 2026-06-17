import { useState, useRef, useEffect, type FormEvent } from 'react';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

interface SseChunk {
  token?: string;
  done?: boolean;
  intent?: string;
  sources?: string[];
}

interface Message {
  role: 'user' | 'assistant';
  text: string;
  intent?: string;
  sources?: string[];
}

function getApiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
}

export function CopilotPanel() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [streamingMeta, setStreamingMeta] = useState<{ intent?: string; sources?: string[] }>({});
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const submitStreaming = async (q: string) => {
    const controller = new AbortController();
    abortRef.current = controller;
    setStreamingText('');
    setStreamingMeta({});

    try {
      const token = localStorage.getItem('access_token');
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/api/v1/copilot/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ query: q, stream: true }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        throw new Error('Stream failed');
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const parsed = JSON.parse(line.slice(6)) as SseChunk;
            if (parsed.done) {
              setStreamingMeta({ intent: parsed.intent, sources: parsed.sources });
              break;
            }
            if (parsed.token) {
              setStreamingText(prev => prev + (parsed.token as string));
            }
          } catch {
            // skip malformed chunks
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === 'AbortError') return;
      setMessages(prev => [...prev, { role: 'assistant', text: 'Copilot is offline. Please try again later.' }]);
    } finally {
      abortRef.current = null;
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const userMsg: Message = { role: 'user', text: query };
    setMessages(prev => [...prev, userMsg]);
    const q = query;
    setQuery('');
    setLoading(true);

    await submitStreaming(q);

    if (!abortRef.current) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: streamingText,
        intent: streamingMeta.intent,
        sources: streamingMeta.sources,
      }]);
      setStreamingText('');
      setStreamingMeta({});
    }

    setLoading(false);
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
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
        {loading && !streamingText && (
          <Card className="mr-4 sm:mr-12">
            <p className="text-sm text-ipe-text-muted">Thinking...</p>
          </Card>
        )}
        {streamingText && (
          <Card className="mr-4 sm:mr-12">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-ipe-text-muted">IPE Copilot</span>
              {streamingMeta.intent && (
                <span className="rounded bg-ipe-surface-alt px-2 py-0.5 text-xs text-ipe-text-muted">
                  {streamingMeta.intent}
                </span>
              )}
            </div>
            <p className="mt-1 text-sm text-ipe-text whitespace-pre-wrap">{streamingText}<span className="animate-pulse">|</span></p>
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

import { useState, useRef, useEffect, type FormEvent } from 'react';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

interface ToolCall {
  type: 'tool_call';
  tool: string;
  input: Record<string, unknown>;
}

interface ToolResult {
  type: 'tool_result';
  tool: string;
  result: Record<string, unknown>;
}

interface AgentEvent {
  type: 'thinking' | 'tool_call' | 'tool_result' | 'response' | 'done';
  content?: string;
  tool?: string;
  input?: Record<string, unknown>;
  result?: Record<string, unknown>;
}

interface Message {
  role: 'user' | 'assistant';
  text: string;
  toolCalls?: ToolCall[];
  toolResults?: ToolResult[];
  hasSimulation?: boolean;
  scenarioId?: string;
}

function getApiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
}

export function CopilotChat() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [activeToolCalls, setActiveToolCalls] = useState<ToolCall[]>([]);
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
    setActiveToolCalls([]);

    const collectedToolCalls: ToolCall[] = [];
    const collectedToolResults: ToolResult[] = [];
    let finalResponse = '';
    let simScenarioId: string | undefined;

    try {
      const token = localStorage.getItem('access_token');
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/api/v1/copilot/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: q, stream: true }),
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
            const event: AgentEvent = JSON.parse(line.slice(6));

            if (event.type === 'tool_call' && event.tool) {
              const tc: ToolCall = { type: 'tool_call', tool: event.tool, input: event.input || {} };
              collectedToolCalls.push(tc);
              setActiveToolCalls(prev => [...prev, tc]);
            }

            if (event.type === 'tool_result' && event.tool) {
              const tr: ToolResult = { type: 'tool_result', tool: event.tool, result: event.result || {} };
              collectedToolResults.push(tr);
              if (event.tool === 'simulate_disruption' && event.result?.scenario_id) {
                simScenarioId = event.result.scenario_id as string;
              }
            }

            if (event.type === 'response' && event.content) {
              finalResponse = event.content;
              setStreamingText(event.content);
            }

            if (event.type === 'done') break;
          } catch {
            // skip malformed chunks
          }
        }
      }

      setMessages(prev => [...prev, {
        role: 'assistant',
        text: finalResponse,
        toolCalls: collectedToolCalls.length > 0 ? collectedToolCalls : undefined,
        toolResults: collectedToolResults.length > 0 ? collectedToolResults : undefined,
        hasSimulation: !!simScenarioId,
        scenarioId: simScenarioId,
      }]);
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === 'AbortError') return;
      setMessages(prev => [...prev, { role: 'assistant', text: 'Copilot is offline. Please try again later.' }]);
    } finally {
      abortRef.current = null;
      setStreamingText('');
      setActiveToolCalls([]);
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
    setLoading(false);
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
  };

  const renderToolCall = (tc: ToolCall, idx: number) => {
    const toolLabels: Record<string, string> = {
      get_order_status: 'Checking order status',
      get_resource_utilization: 'Checking resource utilization',
      simulate_disruption: 'Simulating disruption',
    };
    return (
      <div key={idx} className="mt-2 flex items-center gap-2 rounded bg-ipe-surface-alt p-2 text-xs">
        <span className="animate-spin text-ipe-accent">&#8634;</span>
        <span className="text-ipe-text-muted">{toolLabels[tc.tool] || tc.tool}</span>
        <span className="text-ipe-text-muted opacity-60">
          {JSON.stringify(tc.input)}
        </span>
      </div>
    );
  };

  const renderSimulationButton = (scenarioId: string) => (
    <div className="mt-3">
      <a
        href={`/scenarios/${scenarioId}`}
        className="inline-flex items-center gap-2 rounded bg-ipe-accent px-3 py-1.5 text-sm font-medium text-white hover:bg-ipe-accent/90"
      >
        <span>&#128202;</span>
        View Simulated Schedule
      </a>
    </div>
  );

  return (
    <div className="flex h-full flex-col space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-ipe-text">Planner Copilot</h1>
        <p className="text-sm text-ipe-text-muted">Ask questions, simulate disruptions, analyze capacity</p>
      </div>
      <div className="flex-1 space-y-4 overflow-auto">
        {messages.length === 0 && (
          <Card>
            <p className="text-sm text-ipe-text-muted">
              Try: "What happens if Work Center 3 goes down for 8 hours?" or "Check the status of Order #102"
            </p>
          </Card>
        )}
        {messages.map((msg, i) => (
          <Card key={i} className={msg.role === 'user' ? 'ml-4 sm:ml-12' : 'mr-4 sm:mr-12'}>
            <div className="mb-1 flex items-center gap-2">
              <span className="text-sm font-medium text-ipe-text-muted">
                {msg.role === 'user' ? 'You' : 'Planner Copilot'}
              </span>
            </div>
            {msg.toolCalls && msg.toolCalls.map((tc, j) => renderToolCall(tc, j))}
            <p className="mt-1 text-sm text-ipe-text whitespace-pre-wrap">{msg.text}</p>
            {msg.hasSimulation && msg.scenarioId && renderSimulationButton(msg.scenarioId)}
          </Card>
        ))}
        {loading && !streamingText && (
          <Card className="mr-4 sm:mr-12">
            <p className="text-sm text-ipe-text-muted">Thinking...</p>
            {activeToolCalls.map((tc, j) => renderToolCall(tc, j))}
          </Card>
        )}
        {streamingText && (
          <Card className="mr-4 sm:mr-12">
            <span className="text-sm font-medium text-ipe-text-muted">Planner Copilot</span>
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

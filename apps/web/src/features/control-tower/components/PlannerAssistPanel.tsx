import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { queryPlannerAssist } from '../api';

const SUGGESTIONS = [
  'Which manufacturing orders are at risk?',
  'What is the last Odoo sync status?',
  'Show proposed resolution scenarios',
  'Any capacity bottlenecks on the schedule?',
];

export function PlannerAssistPanel() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [intent, setIntent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runQuery(text: string) {
    const q = text.trim();
    if (!q) return;
    setLoading(true);
    setError(null);
    try {
      const res = await queryPlannerAssist(q);
      setAnswer(res.answer_markdown);
      setIntent(res.intent);
      setQuery(q);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Query failed');
      setAnswer(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="font-medium">Planner Copilot Lite</h3>
          <p className="text-xs text-ipe-text-muted">Structured answers — no GPU required</p>
        </div>
        {intent ? (
          <span className="rounded bg-ipe-surface-alt px-2 py-0.5 text-xs text-ipe-text-muted">{intent}</span>
        ) : null}
      </div>

      <div className="mb-3 flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            type="button"
            className="rounded-full border border-ipe-border px-2 py-1 text-xs text-ipe-text-muted hover:bg-ipe-surface-alt"
            onClick={() => runQuery(s)}
          >
            {s}
          </button>
        ))}
      </div>

      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          runQuery(query);
        }}
      >
        <input
          className="flex-1 rounded-md border border-ipe-border px-3 py-2 text-sm"
          placeholder="Ask about at-risk MOs, sync, scenarios…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button type="submit" size="sm" disabled={loading}>
          {loading ? '…' : 'Ask'}
        </Button>
      </form>

      {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}

      {answer ? (
        <pre className="mt-3 whitespace-pre-wrap rounded-md bg-ipe-surface-alt p-3 text-sm text-ipe-text">
          {answer}
        </pre>
      ) : null}
    </Card>
  );
}

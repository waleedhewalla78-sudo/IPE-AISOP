interface XAIExplanation {
  constraints?: string[];
  assumptions?: string[];
  confidence_score?: number;
  contributing_factors?: Record<string, number>;
}

interface Props {
  explanation: XAIExplanation | null;
  solverStatus?: string;
}

export function ScheduleExplainPanel({ explanation, solverStatus }: Props) {
  if (!explanation && !solverStatus) {
    return null;
  }

  return (
    <div className="rounded-lg border border-ipe-border bg-slate-50 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-ipe-text">Why this schedule?</h3>
        {solverStatus && (
          <span className="text-xs rounded-full bg-white px-2 py-0.5 border border-ipe-border">
            Solver: {solverStatus}
          </span>
        )}
      </div>

      {solverStatus === 'heuristic_fallback' && (
        <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2">
          Heuristic schedule — optimizer timed out. Manual review recommended.
        </p>
      )}

      {explanation?.confidence_score != null && (
        <p className="text-sm text-ipe-text-muted">
          Confidence: {Math.round(explanation.confidence_score * 100)}%
        </p>
      )}

      {explanation?.constraints && explanation.constraints.length > 0 && (
        <div>
          <p className="text-xs font-medium text-ipe-text-muted uppercase mb-1">Constraints applied</p>
          <ul className="text-sm list-disc pl-5 space-y-0.5">
            {explanation.constraints.map(c => (
              <li key={c}>{c.replace(/_/g, ' ')}</li>
            ))}
          </ul>
        </div>
      )}

      {explanation?.assumptions && explanation.assumptions.length > 0 && (
        <div>
          <p className="text-xs font-medium text-ipe-text-muted uppercase mb-1">Assumptions</p>
          <ul className="text-sm list-disc pl-5 space-y-0.5">
            {explanation.assumptions.map(a => (
              <li key={a}>{a.replace(/_/g, ' ')}</li>
            ))}
          </ul>
        </div>
      )}

      {explanation?.contributing_factors && Object.keys(explanation.contributing_factors).length > 0 && (
        <div>
          <p className="text-xs font-medium text-ipe-text-muted uppercase mb-1">Contributing factors</p>
          <div className="flex flex-wrap gap-2">
            {Object.entries(explanation.contributing_factors).map(([key, value]) => (
              <span key={key} className="text-xs bg-white border border-ipe-border rounded px-2 py-1">
                {key}: {typeof value === 'number' ? value.toFixed(2) : value}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

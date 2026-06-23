import { useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import {
  fetchComplianceKPIs,
  type ComplianceKPIs,
  type AuditLogEntry,
} from "../api";

const ACTION_COLORS: Record<string, string> = {
  APPROVE_SCHEDULE: "bg-green-100 text-green-800",
  RUN_SCENARIO: "bg-blue-100 text-blue-800",
  COST_OPTIMIZE: "bg-purple-100 text-purple-800",
  COPILOT_CHAT: "bg-amber-100 text-amber-800",
};

function KPICard({
  title,
  value,
  subtitle,
  color = "text-ipe-primary",
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: string;
}) {
  return (
    <Card>
      <div className="pb-2">
        <h3 className="text-sm font-medium text-ipe-muted">
          {title}
        </h3>
      </div>
      <div>
        <div className={`text-2xl font-bold ${color}`}>{value}</div>
        {subtitle && (
          <p className="text-xs text-ipe-muted mt-1">{subtitle}</p>
        )}
      </div>
    </Card>
  );
}

function AuditLogTable({ entries }: { entries: AuditLogEntry[] }) {
  if (entries.length === 0) {
    return (
      <p className="text-ipe-muted text-sm py-4">No audit log entries yet.</p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-ipe-border">
            <th className="text-left py-2 px-3 font-medium text-ipe-muted">
              Timestamp
            </th>
            <th className="text-left py-2 px-3 font-medium text-ipe-muted">
              Actor
            </th>
            <th className="text-left py-2 px-3 font-medium text-ipe-muted">
              Action
            </th>
            <th className="text-left py-2 px-3 font-medium text-ipe-muted">
              Entity
            </th>
            <th className="text-left py-2 px-3 font-medium text-ipe-muted">
              Rationale
            </th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry, i) => (
            <tr key={i} className="border-b border-ipe-border/50 hover:bg-ipe-surface">
              <td className="py-2 px-3 text-ipe-muted">
                {new Date(entry.timestamp).toLocaleString()}
              </td>
              <td className="py-2 px-3 font-mono text-xs">
                {entry.actor_id.slice(0, 8)}...
              </td>
              <td className="py-2 px-3">
                <Badge
                  className={
                    ACTION_COLORS[entry.action] || "bg-gray-100 text-gray-800"
                  }
                >
                  {entry.action}
                </Badge>
              </td>
              <td className="py-2 px-3">
                {entry.entity_type}:{entry.entity_id.slice(0, 8)}...
              </td>
              <td className="py-2 px-3 text-ipe-muted max-w-[200px] truncate">
                {entry.rationale || "-"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ComplianceDashboardPage() {
  const [data, setData] = useState<ComplianceKPIs | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchComplianceKPIs()
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ipe-primary" />
      </div>
    );
  }

  if (!data) return null;

  const { schedule_adherence, ai_decisions, cost_savings, recent_audit_log } =
    data;

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold text-ipe-text">
          Compliance & Audit Dashboard
        </h1>
        <p className="text-ipe-muted mt-1">
          Schedule adherence, AI decision audit, and procurement accuracy
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Schedule Adherence"
          value={
            schedule_adherence.adherence_pct !== null
              ? `${schedule_adherence.adherence_pct}%`
              : "N/A"
          }
          subtitle={`${schedule_adherence.on_time}/${schedule_adherence.completed} on time`}
          color={
            (schedule_adherence.adherence_pct ?? 0) >= 90
              ? "text-green-600"
              : (schedule_adherence.adherence_pct ?? 0) >= 70
                ? "text-amber-600"
                : "text-red-600"
          }
        />
        <KPICard
          title="AI Decisions"
          value={ai_decisions.total_ai_decisions}
          subtitle={`${ai_decisions.approvals} approvals, ${ai_decisions.scenario_runs} scenarios`}
        />
        <KPICard
          title="Cost Optimizations"
          value={cost_savings.total_schedules_optimized}
          subtitle={
            cost_savings.avg_total_cost > 0
              ? `Avg cost: $${cost_savings.avg_total_cost.toFixed(2)}`
              : "No data yet"
          }
          color="text-purple-600"
        />
        <KPICard
          title="Copilot Interactions"
          value={ai_decisions.copilot_interactions}
          subtitle="Total queries"
          color="text-amber-600"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <div className="mb-4">
            <h3 className="font-medium">AI Decision Breakdown</h3>
          </div>
          <div>
            <div className="space-y-3">
              {[
                { label: "Schedule Approvals", value: ai_decisions.approvals, color: "bg-green-500" },
                { label: "Scenario Runs", value: ai_decisions.scenario_runs, color: "bg-blue-500" },
                { label: "Cost Optimizations", value: ai_decisions.cost_optimizations, color: "bg-purple-500" },
                { label: "Copilot Interactions", value: ai_decisions.copilot_interactions, color: "bg-amber-500" },
              ].map((item) => (
                <div key={item.label} className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${item.color}`} />
                  <span className="text-sm text-ipe-muted flex-1">
                    {item.label}
                  </span>
                  <span className="text-sm font-medium">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>

        <Card>
          <div className="mb-4">
            <h3 className="font-medium">Adherence Summary</h3>
          </div>
          <div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-ipe-muted">Total MOs</span>
                <span className="font-medium">
                  {schedule_adherence.total_mos}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-ipe-muted">Completed</span>
                <span className="font-medium">
                  {schedule_adherence.completed}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-ipe-muted">On Time</span>
                <span className="font-medium text-green-600">
                  {schedule_adherence.on_time}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-ipe-muted">Late</span>
                <span className="font-medium text-red-600">
                  {schedule_adherence.completed - schedule_adherence.on_time}
                </span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <div className="mb-4">
          <h3 className="font-medium">Recent Audit Log</h3>
        </div>
        <div>
          <AuditLogTable entries={recent_audit_log} />
        </div>
      </Card>
    </div>
  );
}

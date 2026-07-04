#!/usr/bin/env python3
"""Generate IPE Phase 2 Grafana dashboard JSON files."""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "infrastructure" / "monitoring" / "grafana" / "dashboards"
DS = {"type": "prometheus", "uid": "prometheus"}


def base(title: str, uid: str, tags: list[str], panels: list, templating: list | None = None) -> dict:
    return {
        "annotations": {"list": []},
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 1,
        "links": [],
        "panels": panels,
        "refresh": "30s",
        "schemaVersion": 39,
        "tags": tags,
        "templating": {"list": templating or []},
        "time": {"from": "now-6h", "to": "now"},
        "timezone": "utc",
        "title": title,
        "uid": uid,
        "version": 1,
    }


def row(title: str, y: int, panel_id: int) -> dict:
    return {
        "id": panel_id,
        "type": "row",
        "title": title,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y},
        "collapsed": False,
        "panels": [],
    }


def prom_panel(
    panel_id: int,
    title: str,
    expr: str,
    panel_type: str,
    grid: dict,
    *,
    legend: str = "",
    unit: str = "",
    instant: bool = False,
    range_query: bool = True,
    extra: dict | None = None,
) -> dict:
    p: dict = {
        "id": panel_id,
        "title": title,
        "type": panel_type,
        "datasource": DS,
        "gridPos": grid,
        "targets": [
            {
                "expr": expr,
                "legendFormat": legend,
                "refId": "A",
                "instant": instant,
                "range": range_query,
            }
        ],
    }
    if unit:
        p["fieldConfig"] = {"defaults": {"unit": unit}}
    if extra:
        p.update(extra)
    return p


def multi_prom_panel(
    panel_id: int,
    title: str,
    targets: list[tuple[str, str]],
    panel_type: str,
    grid: dict,
    unit: str = "",
) -> dict:
    p: dict = {
        "id": panel_id,
        "title": title,
        "type": panel_type,
        "datasource": DS,
        "gridPos": grid,
        "targets": [
            {"expr": expr, "legendFormat": leg, "refId": chr(65 + i)}
            for i, (expr, leg) in enumerate(targets)
        ],
    }
    if unit:
        p["fieldConfig"] = {"defaults": {"unit": unit}}
    return p


def var_query(name: str, query: str, multi: bool = False, include_all: bool = True) -> dict:
    return {
        "name": name,
        "type": "query",
        "datasource": DS,
        "query": {"query": query, "refId": "StandardVariableQuery"},
        "refresh": 1,
        "includeAll": include_all,
        "multi": multi,
        "current": {},
    }


def build_api_overview() -> dict:
    pid = 1
    panels = []
    y = 0
    panels.append(row("Overview", y, pid)); pid += 1; y += 1
    panels.extend([
        prom_panel(pid, "Total RPS", "sum(rate(ipe_http_requests_total[5m]))", "stat", {"h": 4, "w": 6, "x": 0, "y": y}, unit="reqps"),
        prom_panel(pid + 1, "Error Rate %", "100 * sum(rate(ipe_http_requests_total{status_code=~\"5..\"}[5m])) / clamp_min(sum(rate(ipe_http_requests_total[5m])), 1e-9)", "stat", {"h": 4, "w": 6, "x": 6, "y": y}, unit="percent"),
        prom_panel(pid + 2, "P50 Latency", "histogram_quantile(0.50, sum(rate(ipe_http_request_duration_seconds_bucket[5m])) by (le))", "gauge", {"h": 4, "w": 4, "x": 12, "y": y}, unit="s"),
        prom_panel(pid + 3, "P95 Latency", "histogram_quantile(0.95, sum(rate(ipe_http_request_duration_seconds_bucket[5m])) by (le))", "gauge", {"h": 4, "w": 4, "x": 16, "y": y}, unit="s"),
        prom_panel(pid + 4, "P99 Latency", "histogram_quantile(0.99, sum(rate(ipe_http_request_duration_seconds_bucket[5m])) by (le))", "gauge", {"h": 4, "w": 4, "x": 20, "y": y}, unit="s"),
    ])
    pid += 5; y += 4
    panels.append(row("Traffic by Service", y, pid)); pid += 1; y += 1
    panels.extend([
        prom_panel(pid, "Per-Service RPS", "sum by (service) (rate(ipe_http_requests_total[5m]))", "barchart", {"h": 8, "w": 12, "x": 0, "y": y}, legend="{{ service }}", unit="reqps"),
        prom_panel(
            pid + 1,
            "Per-Service Error Rate",
            "sum by (service) (rate(ipe_http_requests_total{status_code=~\"5..\"}[5m])) / clamp_min(sum by (service) (rate(ipe_http_requests_total[5m])), 1e-9)",
            "heatmap",
            {"h": 8, "w": 12, "x": 12, "y": y},
            legend="{{ service }}",
            unit="percentunit",
        ),
    ])
    pid += 2; y += 8
    panels.append(row("Endpoints & Methods", y, pid)); pid += 1; y += 1
    panels.extend([
        prom_panel(
            pid,
            "Top 10 Slowest Endpoints (avg)",
            "topk(10, sum by (service, endpoint) (rate(ipe_http_request_duration_seconds_sum[5m])) / clamp_min(sum by (service, endpoint) (rate(ipe_http_request_duration_seconds_count[5m])), 1e-9))",
            "table",
            {"h": 8, "w": 14, "x": 0, "y": y},
            instant=True,
            range_query=False,
            unit="s",
        ),
        prom_panel(
            pid + 1,
            "Request Volume by Method",
            "sum by (method) (rate(ipe_http_requests_total[5m]))",
            "piechart",
            {"h": 8, "w": 10, "x": 14, "y": y},
            legend="{{ method }}",
        ),
    ])
    pid += 2; y += 8
    panels.append(row("Concurrency", y, pid)); pid += 1; y += 1
    panels.append(
        prom_panel(pid, "In-Flight Requests per Service", "sum by (service) (ipe_http_requests_in_flight)", "timeseries", {"h": 8, "w": 24, "x": 0, "y": y}, legend="{{ service }}")
    )
    return base("IPE API Overview", "ipe-api-overview", ["ipe", "phase2", "api"], panels)


def build_database_health() -> dict:
    svc = 'service=~"$service"'
    panels = []
    pid = 1
    y = 0
    panels.append(row("Connection Pool", y, pid)); pid += 1; y += 1
    panels.extend([
        multi_prom_panel(
            pid,
            "DB Pool: Size / Checked Out / Overflow",
            [
                (f"ipe_db_pool_size{{{svc}}}", "size {{service}}"),
                (f"ipe_db_pool_checked_out{{{svc}}}", "checked out {{service}}"),
                (f"ipe_db_pool_overflow{{{svc}}}", "overflow {{service}}"),
            ],
            "timeseries",
            {"h": 8, "w": 12, "x": 0, "y": y},
        ),
        prom_panel(
            pid + 1,
            "Query Duration P95 (HTTP proxy)",
            f"histogram_quantile(0.95, sum by (le, service) (rate(ipe_http_request_duration_seconds_bucket{{{svc}}}[5m])))",
            "timeseries",
            {"h": 8, "w": 12, "x": 12, "y": y},
            legend="{{ service }}",
            unit="s",
        ),
    ])
    pid += 2; y += 8
    panels.append(row("Database Activity", y, pid)); pid += 1; y += 1
    panels.extend([
        prom_panel(pid, "Active DB Connections (Postgres)", "sum(pg_stat_activity_count) by (datname)", "timeseries", {"h": 8, "w": 12, "x": 0, "y": y}, legend="{{ datname }}"),
        prom_panel(pid + 1, "Pool Utilization %", f"100 * ipe_db_pool_checked_out{{{svc}}} / clamp_min(ipe_db_pool_size{{{svc}}}, 1)", "timeseries", {"h": 8, "w": 12, "x": 12, "y": y}, legend="{{ service }}", unit="percent"),
    ])
    pid += 2; y += 8
    panels.append(row("Tables & Deadlocks", y, pid)); pid += 1; y += 1
    panels.extend([
        prom_panel(pid, "Top 10 Table Row Counts", "topk(10, pg_stat_user_tables_n_live_tup)", "table", {"h": 8, "w": 14, "x": 0, "y": y}, instant=True, range_query=False),
        prom_panel(pid + 1, "Deadlocks", "sum(rate(pg_stat_database_deadlocks[5m])) by (datname)", "timeseries", {"h": 8, "w": 10, "x": 14, "y": y}, legend="{{ datname }}"),
    ])
    return base(
        "IPE Database Health",
        "ipe-database-health",
        ["ipe", "phase2", "database"],
        panels,
        [var_query("service", "label_values(ipe_db_pool_size, service)", multi=True)],
    )


def build_kafka_health() -> dict:
    topic = 'topic=~"$topic"'
    group = 'consumergroup=~"$consumer_group"'
    panels = []
    pid = 1
    y = 0
    panels.append(row("Consumer Lag & Throughput", y, pid)); pid += 1; y += 1
    panels.extend([
        prom_panel(pid, "Consumer Lag (IPE + Kafka exporter)", f"max by (service, topic, consumer_group) (ipe_kafka_consumer_lag{{{topic}}}) or max by (consumergroup, topic) (kafka_consumergroup_lag{{{group},{topic}}})", "timeseries", {"h": 8, "w": 12, "x": 0, "y": y}, legend="{{ topic }} / {{ consumer_group }}"),
        multi_prom_panel(
            pid + 1,
            "Messages In / Out per Second",
            [
                ("sum(rate(kafka_topic_partition_current_offset[5m]))", "topic offset rate"),
                ("sum(rate(kafka_consumergroup_current_offset[5m]))", "consumer offset rate"),
            ],
            "timeseries",
            {"h": 8, "w": 12, "x": 12, "y": y},
            unit="ops",
        ),
    ])
    pid += 2; y += 8
    panels.append(row("Groups & Offsets", y, pid)); pid += 1; y += 1
    panels.extend([
        prom_panel(pid, "Consumer Group Status", f"kafka_consumergroup_lag{{{group},{topic}}}", "table", {"h": 8, "w": 12, "x": 0, "y": y}, instant=True, range_query=False),
        prom_panel(pid + 1, "Topic Partition Current Offset", f"kafka_topic_partition_current_offset{{{topic}}}", "timeseries", {"h": 8, "w": 12, "x": 12, "y": y}, legend="{{ topic }}-{{ partition }}"),
    ])
    pid += 2; y += 8
    panels.append(row("Producer Health", y, pid)); pid += 1; y += 1
    panels.append(
        prom_panel(
            pid,
            "Producer Success vs Failure (HTTP 5xx proxy)",
            "sum(rate(ipe_http_requests_total{status_code!~\"5..\"}[5m])) / clamp_min(sum(rate(ipe_http_requests_total[5m])), 1e-9)",
            "timeseries",
            {"h": 8, "w": 24, "x": 0, "y": y},
            unit="percentunit",
        )
    )
    return base(
        "IPE Kafka Health",
        "ipe-kafka-health",
        ["ipe", "phase2", "kafka"],
        panels,
        [
            var_query("topic", "label_values(ipe_kafka_consumer_lag, topic)", multi=True),
            var_query("consumer_group", "label_values(ipe_kafka_consumer_lag, consumer_group)", multi=True),
        ],
    )


def build_mdr_quality() -> dict:
    tenant = 'tenant_id=~"$tenant_id"'
    panels = []
    pid = 1
    y = 0
    panels.append(row("MDR Scores", y, pid)); pid += 1; y += 1
    panels.extend([
        prom_panel(
            pid,
            "MDR Composite Score",
            f"avg(ipe_mdr_composite_score{{{tenant}}})",
            "gauge",
            {"h": 8, "w": 6, "x": 0, "y": y},
            unit="percentunit",
            extra={"fieldConfig": {"defaults": {"min": 0, "max": 1, "thresholds": {"mode": "absolute", "steps": [{"color": "red", "value": None}, {"color": "yellow", "value": 0.7}, {"color": "green", "value": 0.85}]}}}},
        ),
        prom_panel(pid + 1, "BOM Score", f"avg(ipe_mdr_bom_score{{{tenant}}})", "gauge", {"h": 8, "w": 6, "x": 6, "y": y}, unit="percentunit"),
        prom_panel(pid + 2, "Routing Score", f"avg(ipe_mdr_routing_score{{{tenant}}})", "gauge", {"h": 8, "w": 6, "x": 12, "y": y}, unit="percentunit"),
        prom_panel(pid + 3, "Inventory Score", f"avg(ipe_mdr_inventory_score{{{tenant}}})", "gauge", {"h": 8, "w": 6, "x": 18, "y": y}, unit="percentunit"),
    ])
    pid += 4; y += 8
    panels.append(row("Trends", y, pid)); pid += 1; y += 1
    panels.append(
        prom_panel(pid, "MDR Composite Trend by Tenant", f"avg by (tenant_id) (ipe_mdr_composite_score{{{tenant}}})", "timeseries", {"h": 8, "w": 24, "x": 0, "y": y}, legend="{{ tenant_id }}", unit="percentunit")
    )
    pid += 1; y += 8
    panels.append(row("Quality & Feasibility", y, pid)); pid += 1; y += 1
    panels.extend([
        prom_panel(pid, "Data Quality Issues by Type", f"sum by (issue_type) (ipe_data_quality_issues_total{{{tenant}}})", "timeseries", {"h": 8, "w": 12, "x": 0, "y": y}, legend="{{ issue_type }}"),
        prom_panel(pid + 1, "Feasibility Pass Rate", f"sum(rate(ipe_feasibility_pass_total{{{tenant}}}[5m])) / clamp_min(sum(rate(ipe_feasibility_evaluations_total{{{tenant}}}[5m])), 1e-9)", "timeseries", {"h": 8, "w": 12, "x": 12, "y": y}, unit="percentunit"),
    ])
    return base(
        "IPE MDR Quality",
        "ipe-mdr-quality",
        ["ipe", "phase2", "business", "mdr"],
        panels,
        [var_query("tenant_id", "label_values(ipe_mdr_composite_score, tenant_id)", multi=True)],
    )


def build_business_kpis() -> dict:
    tenant = 'tenant_id=~"$tenant_id"'
    panels = []
    pid = 1
    y = 0
    panels.append(row("Manufacturing KPIs", y, pid)); pid += 1; y += 1
    panels.extend([
        prom_panel(pid, "MO Created Rate", f"sum(rate(ipe_manufacturing_orders_created_total{{{tenant}}}[5m]))", "stat", {"h": 4, "w": 8, "x": 0, "y": y}, unit="ops"),
        prom_panel(pid + 1, "MO Completed Rate", f"sum(rate(ipe_manufacturing_orders_completed_total{{{tenant}}}[5m]))", "stat", {"h": 4, "w": 8, "x": 8, "y": y}, unit="ops"),
        prom_panel(pid + 2, "OTD Rate %", f"100 * avg(ipe_otd_rate{{{tenant}}})", "gauge", {"h": 4, "w": 4, "x": 16, "y": y}, unit="percent"),
        prom_panel(pid + 3, "ROI %", f"100 * avg(ipe_roi_percent{{{tenant}}})", "gauge", {"h": 4, "w": 4, "x": 20, "y": y}, unit="percent"),
    ])
    pid += 4; y += 4
    panels.append(row("Operations", y, pid)); pid += 1; y += 1
    panels.extend([
        prom_panel(pid, "Feasibility Queue Size", f"sum(ipe_feasibility_queue_size{{{tenant}}})", "timeseries", {"h": 8, "w": 12, "x": 0, "y": y}),
        prom_panel(
            pid + 1,
            "Resolution Time Distribution",
            f"histogram_quantile(0.95, sum by (le) (rate(ipe_resolution_duration_seconds_bucket{{{tenant}}}[5m])))",
            "timeseries",
            {"h": 8, "w": 12, "x": 12, "y": y},
            unit="s",
        ),
    ])
    pid += 2; y += 8
    panels.append(row("Integration", y, pid)); pid += 1; y += 1
    panels.extend([
        prom_panel(pid, "Odoo Sync Errors (rate)", f"sum(rate(ipe_odoo_sync_errors_total{{{tenant}}}[5m]))", "stat", {"h": 4, "w": 8, "x": 0, "y": y}, unit="ops"),
        prom_panel(pid + 1, "Last Sync Age (seconds)", f"time() - max(ipe_odoo_last_sync_timestamp{{{tenant}}})", "stat", {"h": 4, "w": 8, "x": 8, "y": y}, unit="s"),
        prom_panel(pid + 2, "Active Tenants", "count(count by (tenant_id) (ipe_http_requests_total))", "stat", {"h": 4, "w": 8, "x": 16, "y": y}),
    ])
    return base(
        "IPE Business KPIs",
        "ipe-business-kpis",
        ["ipe", "phase2", "business"],
        panels,
        [var_query("tenant_id", "label_values(ipe_feasibility_queue_size, tenant_id)", multi=True)],
    )


def build_system_resources() -> dict:
    panels = []
    pid = 1
    y = 0
    panels.append(row("Host Resources", y, pid)); pid += 1; y += 1
    panels.extend([
        prom_panel(pid, "CPU Usage %", '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)', "timeseries", {"h": 8, "w": 8, "x": 0, "y": y}, unit="percent"),
        prom_panel(pid + 1, "Memory Usage %", "100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))", "timeseries", {"h": 8, "w": 8, "x": 8, "y": y}, unit="percent"),
        multi_prom_panel(
            pid + 2,
            "Disk I/O",
            [
                ("sum(rate(node_disk_read_bytes_total[5m]))", "read"),
                ("sum(rate(node_disk_written_bytes_total[5m]))", "write"),
            ],
            "timeseries",
            {"h": 8, "w": 8, "x": 16, "y": y},
            unit="Bps",
        ),
    ])
    pid += 3; y += 8
    panels.append(row("Network & Restarts", y, pid)); pid += 1; y += 1
    panels.extend([
        multi_prom_panel(
            pid,
            "Network I/O",
            [
                ("sum(rate(node_network_receive_bytes_total[5m]))", "rx"),
                ("sum(rate(node_network_transmit_bytes_total[5m]))", "tx"),
            ],
            "timeseries",
            {"h": 8, "w": 12, "x": 0, "y": y},
            unit="Bps",
        ),
        prom_panel(pid + 1, "Scrape Target Restarts (up flaps)", "changes(up[1h])", "timeseries", {"h": 8, "w": 12, "x": 12, "y": y}, legend="{{ job }} / {{ instance }}"),
    ])
    pid += 2; y += 8
    panels.append(row("Services", y, pid)); pid += 1; y += 1
    panels.extend([
        prom_panel(pid, "Docker / Service Targets", "up", "table", {"h": 8, "w": 14, "x": 0, "y": y}, instant=True, range_query=False),
        prom_panel(pid + 1, "Service Uptime (up ratio)", "avg by (job) (avg_over_time(up[6h]))", "timeseries", {"h": 8, "w": 10, "x": 14, "y": y}, legend="{{ job }}", unit="percentunit"),
    ])
    pid += 2; y += 8
    panels.append(row("Logs (future)", y, pid)); pid += 1; y += 1
    panels.append(
        prom_panel(
            pid,
            "Log Rate (placeholder — wire Loki datasource when enabled)",
            "sum(rate(ipe_http_requests_total[5m]))",
            "timeseries",
            {"h": 6, "w": 24, "x": 0, "y": y},
            legend="request proxy until Loki",
        )
    )
    return base("IPE System Resources", "ipe-system-resources", ["ipe", "phase2", "infra"], panels)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    dashboards = {
        "api-overview.json": build_api_overview(),
        "database-health.json": build_database_health(),
        "kafka-health.json": build_kafka_health(),
        "mdr-quality.json": build_mdr_quality(),
        "business-kpis.json": build_business_kpis(),
        "system-resources.json": build_system_resources(),
    }
    for name, body in dashboards.items():
        path = OUT / name
        path.write_text(json.dumps(body, indent=2), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()

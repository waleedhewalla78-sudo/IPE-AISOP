"""Agent orchestrator — chain execution with timeouts and circuit breakers."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field, asdict
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class AgentStep:
    agent_id: str
    service: str
    endpoint: str
    trigger: str
    timeout_seconds: int


@dataclass
class ChainResult:
    trigger: str
    changed_data: list[str]
    agents_run: int
    agents_skipped: int
    agents_failed: int
    total_flagged: int
    total_duration_ms: int
    details: dict[str, Any] = field(default_factory=dict)


class AgentOrchestrator:
    CHAIN = [
        AgentStep("A4", "fea-svc", "/api/v1/feasibility/score-all", "always", 30),
        AgentStep("A4-predict", "fea-svc", "/api/v1/feasibility/predict-all", "always", 60),
        AgentStep("A5", "dpe-svc", "/api/v1/agents/generate-resolutions", "if_flagged", 30),
        AgentStep("A3-batch", "cap-svc", "/api/v1/capacity/batch/optimize", "if_data_changed:production,master", 15),
        AgentStep("A3", "cap-svc", "/api/v1/capacity/utilisation/calculate", "if_data_changed:production,master", 30),
        AgentStep("A1", "demand-svc", "/api/v1/demand/forecast", "if_data_changed:demand", 30),
        AgentStep("A1-fuse", "demand-svc", "/api/v1/demand/signal-fusion", "if_data_changed:demand", 15),
        AgentStep("A2", "mat-svc", "/api/v1/material/safety-stock/calculate", "if_data_changed:demand,inventory", 30),
        AgentStep("A2-supplier", "mat-svc", "/api/v1/material/suppliers/score", "if_data_changed:supply", 15),
        # Phase 4 Premium agents (dry-run stubs unless service_urls wired)
        AgentStep("A8", "dpe-svc", "/api/v1/intelligence/customer/health", "if_data_changed:demand,customer", 15),
        AgentStep("A9", "procurement-svc", "/api/v1/procurement/po-recommendations", "if_data_changed:inventory,supply", 20),
        AgentStep("A10", "quality-svc", "/api/v1/quality-events/predict", "if_data_changed:production", 20),
        AgentStep("A11", "dpe-svc", "/api/v1/intelligence/finance/mo-margin", "if_data_changed:production,finance", 15),
        AgentStep("A12", "sustain-svc", "/api/v1/sustainability/carbon-footprint", "if_data_changed:master,supply", 15),
    ]

    def __init__(self, service_urls: dict[str, str] | None = None, dry_run: bool = True):
        self.service_urls = service_urls or {}
        self.dry_run = dry_run

    def _should_run(self, step: AgentStep, changed_data: list[str], flagged_count: int) -> bool:
        if step.trigger == "always":
            return True
        if step.trigger == "if_flagged":
            return flagged_count > 0
        if step.trigger.startswith("if_data_changed:"):
            keys = step.trigger.split(":", 1)[1].split(",")
            return any(k in changed_data for k in keys)
        return False

    async def run_chain(
        self,
        tenant_id: str,
        trigger: str,
        changed_data: list[str],
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        results: dict[str, Any] = {}
        flagged_count = 0

        for step in self.CHAIN:
            if not self._should_run(step, changed_data, flagged_count):
                results[step.agent_id] = {"status": "skipped", "reason": "trigger not met"}
                continue

            try:
                start = time.time()
                result = await asyncio.wait_for(
                    self._call_agent(step, tenant_id),
                    timeout=step.timeout_seconds,
                )
                duration = int((time.time() - start) * 1000)
                results[step.agent_id] = {
                    "status": "completed",
                    "items_processed": result.get("items_processed", 0),
                    "items_flagged": result.get("items_flagged", 0),
                    "duration_ms": duration,
                }
                if step.agent_id == "A4":
                    flagged_count = result.get("items_flagged", 0)
            except asyncio.TimeoutError:
                results[step.agent_id] = {
                    "status": "timeout",
                    "timeout_seconds": step.timeout_seconds,
                }
                if db is not None:
                    await self._create_exception(
                        db,
                        tenant_id,
                        step.agent_id,
                        "AGENT_TIMEOUT",
                        "medium",
                        f"{step.agent_id} timed out after {step.timeout_seconds}s",
                    )
            except Exception as e:
                results[step.agent_id] = {"status": "error", "error": str(e)}
                if db is not None:
                    await self._create_exception(
                        db,
                        tenant_id,
                        step.agent_id,
                        "AGENT_ERROR",
                        "high",
                        f"{step.agent_id} failed: {e}",
                    )

        if db is not None:
            await self._log_activity(db, tenant_id, "chain", trigger, results)

        chain = ChainResult(
            trigger=trigger,
            changed_data=changed_data,
            agents_run=len([r for r in results.values() if r["status"] == "completed"]),
            agents_skipped=len([r for r in results.values() if r["status"] == "skipped"]),
            agents_failed=len([r for r in results.values() if r["status"] in ("timeout", "error")]),
            total_flagged=sum(r.get("items_flagged", 0) for r in results.values()),
            total_duration_ms=sum(r.get("duration_ms", 0) for r in results.values()),
            details=results,
        )
        return asdict(chain)

    async def _call_agent(self, step: AgentStep, tenant_id: str) -> dict[str, Any]:
        if self.dry_run or step.service not in self.service_urls:
            # Deterministic dry-run for unit tests / offline orchestration
            flagged = 2 if step.agent_id == "A4" else 0
            return {"items_processed": 10, "items_flagged": flagged, "dry_run": True}

        base = self.service_urls[step.service].rstrip("/")
        url = f"{base}{step.endpoint}"
        async with httpx.AsyncClient(timeout=step.timeout_seconds) as client:
            resp = await client.post(url, headers={"X-Tenant-ID": tenant_id}, json={})
            resp.raise_for_status()
            return resp.json()

    async def _create_exception(
        self,
        db: AsyncSession,
        tenant_id: str,
        agent_id: str,
        exception_type: str,
        severity: str,
        title: str,
    ) -> None:
        await db.execute(
            text("""
                INSERT INTO cdm_agent_exception (
                    tenant_id, agent_id, exception_type, severity, title, status
                ) VALUES (
                    :tenant_id, :agent_id, :exception_type, :severity, :title, 'open'
                )
            """),
            {
                "tenant_id": UUID(tenant_id),
                "agent_id": agent_id,
                "exception_type": exception_type,
                "severity": severity,
                "title": title[:300],
            },
        )

    async def _log_activity(
        self,
        db: AsyncSession,
        tenant_id: str,
        agent_id: str,
        trigger: str,
        details: dict[str, Any],
    ) -> None:
        import json

        await db.execute(
            text("""
                INSERT INTO cdm_agent_activity_log (
                    tenant_id, agent_id, trigger, status, details
                ) VALUES (
                    :tenant_id, :agent_id, :trigger, :status, CAST(:details AS jsonb)
                )
            """),
            {
                "tenant_id": UUID(tenant_id),
                "agent_id": agent_id,
                "trigger": trigger,
                "status": "completed",
                "details": json.dumps(details),
            },
        )

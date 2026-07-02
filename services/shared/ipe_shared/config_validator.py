"""Startup configuration validator for IPE services.

Validates required environment variables at startup, warns on placeholder values,
and returns a ConfigReport with the status of each variable.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import StrEnum

logger = logging.getLogger(__name__)

PLACEHOLDER_VALUES = {
    "sk-ant-placeholder",
    "dev-only",
    "dev-only-change-in-production-min-32-chars-long!!",
    "test-hmac-secret-key",
    "CHANGE_ME",
    "CHANGE_ME_TO_A_RANDOM_SECRET_AT_LEAST_32_CHARS",
}

REQUIRED_VARS: list[str] = [
    "DATABASE_URL",
    "REDIS_URL",
]

OPTIONAL_RECOMMENDED: dict[str, str] = {
    "VAULT_ADDR": "HashiCorp Vault address",
    "KEYCLOAK_URL": "Keycloak URL (if AUTH_MODE=keycloak)",
    "KAFKA_BOOTSTRAP_SERVERS": "Kafka brokers (for event-driven features)",
    "JWT_PUBLIC_KEY_PATH": "Path to RS256 public key (or set IPE_JWT_SIGNING_MODE=hs256 for dev)",
}

OPTIONAL_WITH_DEFAULTS: dict[str, str] = {
    "ANTHROPIC_API_KEY": "sk-ant-placeholder",
    "SENTRY_DSN": "",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
    "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT": "",
    "OTEL_TRACING_ENABLED": "true",
    "OTEL_LOGGING_ENABLED": "true",
    "ENVIRONMENT": "development",
    "LOG_LEVEL": "DEBUG",
    "SERVICE_NAME": "unknown",
    "VERSION": "0.1.0",
}


class VarStatus(StrEnum):
    OK = "ok"
    MISSING = "missing"
    PLACEHOLDER = "placeholder"
    WARNING = "warning"


@dataclass
class VarReport:
    name: str
    status: VarStatus
    value_preview: str
    message: str = ""


@dataclass
class ConfigReport:
    required: list[VarReport] = field(default_factory=list)
    optional: list[VarReport] = field(default_factory=list)
    all_ok: bool = True

    @property
    def missing_required(self) -> list[VarReport]:
        return [r for r in self.required if r.status == VarStatus.MISSING]

    @property
    def placeholders(self) -> list[VarReport]:
        return [r for r in self.required + self.optional if r.status == VarStatus.PLACEHOLDER]

    def summary(self) -> str:
        lines = ["── Config Validation Report ──"]
        for r in self.required:
            detail = r.message or r.value_preview
            lines.append(f"  [REQUIRED] {r.name}: {r.status.value} — {detail}")
        for r in self.optional:
            detail = r.message or r.value_preview
            lines.append(f"  [OPTIONAL] {r.name}: {r.status.value} — {detail}")
        lines.append(f"  All OK: {self.all_ok}")
        return "\n".join(lines)


def _resolve_key(env_name: str) -> str | None:
    """Look up IPE_-prefixed and unprefixed keys."""
    val = os.environ.get(f"IPE_{env_name}")
    if val is not None:
        return val
    return os.environ.get(env_name)


def _is_placeholder(val: str) -> bool:
    stripped = val.strip()
    if stripped in PLACEHOLDER_VALUES:
        return True
    if stripped.startswith("sk-ant-placeholder"):
        return True
    if stripped == "dev-only":
        return True
    return stripped == "CHANGE_ME"


def _preview(val: str, max_len: int = 30) -> str:
    if len(val) <= max_len:
        return val
    return val[:max_len] + "..."


def validate_config() -> ConfigReport:
    """Validate all required and optional env vars.

    Returns:
        ConfigReport with per-variable status.

    Raises:
        ValueError: If any required variable is missing.
    """
    report = ConfigReport()

    for var in REQUIRED_VARS:
        val = _resolve_key(var)
        if val is None:
            report.required.append(VarReport(
                name=var,
                status=VarStatus.MISSING,
                value_preview="",
                message="Environment variable not set",
            ))
            report.all_ok = False
            continue

        if _is_placeholder(val):
            report.required.append(VarReport(
                name=var,
                status=VarStatus.PLACEHOLDER,
                value_preview=_preview(val),
                message=f"Value appears to be a placeholder: {val[:16]}...",
            ))
            report.all_ok = False
            logger.warning("Required env var %s has placeholder value", var)
            continue

        report.required.append(VarReport(
            name=var,
            status=VarStatus.OK,
            value_preview=_preview(val),
        ))

    _validate_jwt_keys(report)

    for var, desc in OPTIONAL_RECOMMENDED.items():
        val = _resolve_key(var)
        if val is None:
            if var == "JWT_PUBLIC_KEY_PATH" and _hs256_mode():
                continue
            report.optional.append(VarReport(
                name=var,
                status=VarStatus.WARNING,
                value_preview="",
                message=desc,
            ))
            logger.warning("[CONFIG] Recommended var not set: %s — %s", var, desc)
            continue
        report.optional.append(VarReport(
            name=var,
            status=VarStatus.OK,
            value_preview=_preview(val),
        ))

    for var, default in OPTIONAL_WITH_DEFAULTS.items():
        val = _resolve_key(var)
        if val is None:
            report.optional.append(VarReport(
                name=var,
                status=VarStatus.OK,
                value_preview=_preview(default),
                message=f"Not set — using default: {default}",
            ))
            continue

        if _is_placeholder(val):
            report.optional.append(VarReport(
                name=var,
                status=VarStatus.PLACEHOLDER,
                value_preview=_preview(val),
                message="Optional value appears to be a placeholder",
            ))
            logger.warning("Optional env var %s has placeholder value", var)
            continue

        report.optional.append(VarReport(
            name=var,
            status=VarStatus.OK,
            value_preview=_preview(val),
        ))

    missing = report.missing_required
    if missing:
        names = ", ".join(r.name for r in missing)
        raise ValueError(
            f"Missing required environment variables: {names}. "
            "Copy .env.template to .env and fill in real values."
        )

    logger.info("Configuration validation complete. All OK=%s", report.all_ok)
    return report


def _hs256_mode() -> bool:
    mode = (_resolve_key("JWT_SIGNING_MODE") or "rs256").lower()
    return mode in ("hs256", "hs")


def _validate_jwt_keys(report: ConfigReport) -> None:
    if _hs256_mode():
        return
    pub = _resolve_key("JWT_PUBLIC_KEY_PATH")
    if not pub:
        report.required.append(VarReport(
            name="JWT_PUBLIC_KEY_PATH",
            status=VarStatus.MISSING,
            value_preview="",
            message="Path to RS256 public key (or set IPE_JWT_SIGNING_MODE=hs256 for dev)",
        ))
        report.all_ok = False


def validate_config_fatal() -> ConfigReport:
    """Validate config and exit the process on missing required variables."""
    import sys

    missing_lines: list[str] = []
    for var in REQUIRED_VARS:
        if _resolve_key(var) is None:
            missing_lines.append(f"  {var} — required connection string")

    if not _hs256_mode() and not _resolve_key("JWT_PUBLIC_KEY_PATH"):
        missing_lines.append(
            "  JWT_PUBLIC_KEY_PATH — Path to RS256 public key (or set IPE_JWT_SIGNING_MODE=hs256)"
        )

    if missing_lines:
        print("[CONFIG] FATAL: Missing required environment variables:\n" + "\n".join(missing_lines))
        sys.exit(1)

    for var, desc in OPTIONAL_RECOMMENDED.items():
        if var == "JWT_PUBLIC_KEY_PATH" and _hs256_mode():
            continue
        if not _resolve_key(var):
            print(f"[CONFIG] WARNING: Recommended var not set: {var} — {desc}")

    try:
        return validate_config()
    except ValueError as exc:
        print(f"[CONFIG] FATAL: {exc}")
        sys.exit(1)

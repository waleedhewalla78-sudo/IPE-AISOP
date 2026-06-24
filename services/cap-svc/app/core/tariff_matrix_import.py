"""Parse simple CSV tariff matrix imports."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass


@dataclass
class TariffMatrixRow:
    region: str
    tariff_code: str
    tariff_pct: float
    effective_date: str | None = None


def parse_tariff_matrix_csv(content: str) -> list[TariffMatrixRow]:
    """Parse CSV with headers: region,tariff_code,tariff_pct[,effective_date]."""
    reader = csv.DictReader(io.StringIO(content.strip()))
    rows: list[TariffMatrixRow] = []
    for row in reader:
        region = (row.get("region") or "").strip()
        tariff_code = (row.get("tariff_code") or "").strip()
        if not region or not tariff_code:
            continue
        try:
            tariff_pct = float(row.get("tariff_pct") or 0)
        except ValueError:
            continue
        rows.append(
            TariffMatrixRow(
                region=region,
                tariff_code=tariff_code,
                tariff_pct=tariff_pct,
                effective_date=(row.get("effective_date") or "").strip() or None,
            )
        )
    return rows

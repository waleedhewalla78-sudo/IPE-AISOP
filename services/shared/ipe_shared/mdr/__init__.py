"""MDR (Master Data Readiness) scoring."""

from ipe_shared.mdr.engine import (
    BOM_COMPLETENESS_THRESHOLD,
    COMPOSITE_THRESHOLD,
    LEAD_TIME_ACCURACY_THRESHOLD,
    ROUTING_DEVIATION_THRESHOLD_PCT,
    build_remediation,
    calculate_mdr,
    detect_routing_deviation,
    format_mdr_response,
)

__all__ = [
    "BOM_COMPLETENESS_THRESHOLD",
    "COMPOSITE_THRESHOLD",
    "LEAD_TIME_ACCURACY_THRESHOLD",
    "ROUTING_DEVIATION_THRESHOLD_PCT",
    "build_remediation",
    "calculate_mdr",
    "detect_routing_deviation",
    "format_mdr_response",
]

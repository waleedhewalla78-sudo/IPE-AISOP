"""CPM cascade Prometheus metrics."""

from prometheus_client import Histogram

CPM_CASCADE_DURATION = Histogram(
    "cap_svc_cpm_cascade_duration_seconds",
    "Duration of CPM cascade operations in seconds",
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
)

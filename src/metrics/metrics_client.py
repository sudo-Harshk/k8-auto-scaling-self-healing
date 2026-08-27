"""Programmatic Prometheus client for a Kubernetes workload
(Day 6: podinfo. Day 18: parameterized for workload-v2 or any deployment
exposing `http_requests_total` and `http_request_duration_seconds_bucket`).

This module is the data source the rest of the AI pipeline (Faust stream processor,
River-ML models, decision engine) will consume.

Usage as a CLI (task doc verification command):

    python src/metrics/metrics_client.py

    # Override Prometheus URL (default http://host.docker.internal:9090 so docker
    # containers can reach a host kubectl port-forward):
    PROMETHEUS_URL=http://localhost:9090 python src/metrics/metrics_client.py

    # Day 18: override workload target via env vars:
    WORKLOAD_NAMESPACE=workload-v2 WORKLOAD_DEPLOYMENT=workload-v2 \
        PROMETHEUS_URL=http://localhost:9090 python src/metrics/metrics_client.py

Usage as a library:

    from src.metrics.metrics_client import PodinfoMetricsClient
    client = PodinfoMetricsClient("http://localhost:9090")
    metrics = client.get_current_metrics()
    # -> {"timestamp": "...", "cpu_cores": 0.013, "memory_bytes": 4.2e7,
    #    "request_rate_per_s": 1.4, "error_rate_per_s": 0.0,
    #    "current_replicas": 2, "available_replicas": 2}
"""
from __future__ import annotations

import math
import os
import logging
from datetime import datetime, timezone
from typing import Any

from prometheus_api_client import PrometheusConnect

LOG = logging.getLogger(__name__)

# Default URL assumes we are running inside a Docker container that needs to reach a
# host-side `kubectl port-forward`. Override with PROMETHEUS_URL when running on host.
DEFAULT_PROM_URL = os.environ.get("PROMETHEUS_URL", "http://host.docker.internal:9090")

# Day 18: workload target parameterized via env vars. Defaults preserve the
# Day 6-15 podinfo behavior.
WORKLOAD_NAMESPACE = os.environ.get("WORKLOAD_NAMESPACE", "podinfo")
WORKLOAD_DEPLOYMENT = os.environ.get("WORKLOAD_DEPLOYMENT", "podinfo")

# PromQL queries used throughout the project (locked here so every consumer agrees
# on what each metric means).
QUERIES = {
    # CPU usage in cores (rate of seconds spent executing per second).
    "cpu_cores":
        'sum(rate(container_cpu_usage_seconds_total{namespace="%s"}[1m]))' % WORKLOAD_NAMESPACE,
    # Resident memory in bytes (working set, excludes page cache).
    "memory_bytes":
        'sum(container_memory_working_set_bytes{namespace="%s"})' % WORKLOAD_NAMESPACE,
    # HTTP request rate per second across all podinfo replicas.
    "request_rate_per_s":
        'sum(rate(http_requests_total{namespace="%s"}[1m]))' % WORKLOAD_NAMESPACE,
    # HTTP error rate per second (5xx responses only) - the anomaly signal.
    "error_rate_per_s":
        'sum(rate(http_requests_total{namespace="%s",status=~"5.."}[1m]))' % WORKLOAD_NAMESPACE,
    # Configured replica count (spec.replicas).
    "current_replicas":
        'kube_deployment_spec_replicas{namespace="%s",deployment="%s"}'
        % (WORKLOAD_NAMESPACE, WORKLOAD_DEPLOYMENT),
    # Ready replica count (status.availableReplicas) - the value our operator reads
    # before scaling decisions.
    "available_replicas":
        'kube_deployment_status_replicas_available{namespace="%s",deployment="%s"}'
        % (WORKLOAD_NAMESPACE, WORKLOAD_DEPLOYMENT),
    # p95 request latency in milliseconds over the last 1m, from podinfo's
    # http_request_duration_seconds histogram. Added Day 6 for the feature vector;
    # additive only - existing keys are unchanged.
    "p95_latency_ms":
        'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket'
        '{namespace="%s"}[1m])) by (le)) * 1000' % WORKLOAD_NAMESPACE,
}


class PodinfoMetricsClient:
    """Thin wrapper around prometheus_api_client.PrometheusConnect.

    Specialised to the podinfo workload so the rest of the project imports one
    consistent client and one consistent set of PromQL queries (defined in QUERIES).
    """

    def __init__(self, url: str = DEFAULT_PROM_URL) -> None:
        self._prom = PrometheusConnect(url=url, disable_ssl=True)
        # Fail-fast: confirm Prometheus is reachable on construction.
        try:
            self._prom.check_prometheus_connection()
        except Exception as exc:  # pragma: no cover - surfaced to CLI
            raise RuntimeError(
                f"Cannot reach Prometheus at {url} "
                f"(is `kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring` running?): {exc}"
            ) from exc
        self._url = url

    @property
    def url(self) -> str:
        return self._url

    def query(self, promql: str) -> float:
        """Run a single instant PromQL query and return the scalar value.

        Returns 0.0 if Prometheus has no series yet (e.g. workload just scaled to zero
        and kube-state-metrics hasn't caught up). Never raises on missing data.
        """
        result = self._prom.custom_query(query=promql)
        if not result:
            return 0.0
        # Prometheus returns a list of (timestamp, value-string) pairs. We take the
        # first series and its latest value. histogram_quantile on an all-zero
        # histogram (e.g. idle, no requests in the window) yields NaN - map to 0.0
        # so downstream JSON stays valid and Faust accumulation never sees NaN.
        value = float(result[0]["value"][1])
        return 0.0 if math.isnan(value) else value

    def get_current_metrics(self) -> dict[str, Any]:
        """Return one snapshot of the podinfo workload metrics as a dict."""
        snapshot: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        for key, promql in QUERIES.items():
            try:
                snapshot[key] = self.query(promql)
            except Exception as exc:
                LOG.warning("query %s failed: %s", key, exc)
                snapshot[key] = None
        return snapshot


def _format_snapshot(snapshot: dict[str, Any]) -> str:
    """Pretty-print snapshot for the CLI verification command."""
    lines = []
    lines.append(f"Prometheus: ok")
    lines.append(f"timestamp          : {snapshot.get('timestamp')}")
    lines.append("")
    lines.append("Workload metrics (podinfo deployment, namespace=podinfo)")
    lines.append("-" * 64)
    fmt = "  {:<22} : {:>20}"
    for key in (
        "cpu_cores",
        "memory_bytes",
        "request_rate_per_s",
        "error_rate_per_s",
        "current_replicas",
        "available_replicas",
        "p95_latency_ms",
    ):
        v = snapshot.get(key)
        if v is None:
            v_str = "<query failed>"
        elif key == "memory_bytes":
            v_str = f"{v:>15.0f}  bytes ({v / (1024 ** 2):>6.1f} MiB)"
        else:
            v_str = f"{v!r}"
        lines.append(fmt.format(key, v_str))
    return "\n".join(lines)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    client = PodinfoMetricsClient()
    snapshot = client.get_current_metrics()
    print(_format_snapshot(snapshot))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
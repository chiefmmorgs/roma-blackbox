"""Metrics tracking for black-box monitoring"""

from abc import ABC, abstractmethod
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class AbstractMetrics(ABC):
    @abstractmethod
    def record_request(self, status: str, latency_ms: int, cost_cents: float):
        pass

    @abstractmethod
    def record_trace_strip(self):
        pass

    @abstractmethod
    def record_break_glass(self):
        pass

    @abstractmethod
    def record_pii_redaction(self, field: str):
        pass

    @abstractmethod
    def get_summary(self) -> Dict:
        pass


class NoOpMetrics(AbstractMetrics):
    def record_request(self, status: str, latency_ms: int, cost_cents: float):
        pass

    def record_trace_strip(self):
        pass

    def record_break_glass(self):
        pass

    def record_pii_redaction(self, field: str):
        pass

    def get_summary(self) -> Dict:
        return {}


class PrometheusMetrics(AbstractMetrics):
    def __init__(self):
        from prometheus_client import Counter, Histogram

        self.request_counter = Counter("roma_blackbox_requests_total", "Total requests", ["status"])
        self.latency_histogram = Histogram("roma_blackbox_latency_seconds", "Latency")
        self.cost_histogram = Histogram("roma_blackbox_cost_cents", "Cost")
        self.traces_stripped = Counter("roma_blackbox_traces_stripped_total", "Traces stripped")
        self.break_glass_counter = Counter(
            "roma_blackbox_break_glass_total", "Break-glass activations"
        )
        self.pii_redactions = Counter(
            "roma_blackbox_pii_redactions_total", "PII redactions", ["field"]
        )

    def record_request(self, status: str, latency_ms: int, cost_cents: float):
        self.request_counter.labels(status=status).inc()
        self.latency_histogram.observe(latency_ms / 1000.0)
        self.cost_histogram.observe(cost_cents)

    def record_trace_strip(self):
        self.traces_stripped.inc()

    def record_break_glass(self):
        self.break_glass_counter.inc()

    def record_pii_redaction(self, field: str):
        self.pii_redactions.labels(field=field).inc()

    def get_summary(self) -> Dict:
        return {"type": "prometheus", "endpoint": "/metrics"}


class InMemoryMetrics(AbstractMetrics):
    def __init__(self):
        self.requests = {"success": 0, "error": 0}
        self.latencies = []
        self.costs = []
        self.traces_stripped_count = 0
        self.break_glass_count = 0
        self.pii_redactions_by_field = {}

    def record_request(self, status: str, latency_ms: int, cost_cents: float):
        self.requests[status] = self.requests.get(status, 0) + 1
        self.latencies.append(latency_ms)
        self.costs.append(cost_cents)

    def record_trace_strip(self):
        self.traces_stripped_count += 1

    def record_break_glass(self):
        self.break_glass_count += 1

    def record_pii_redaction(self, field: str):
        self.pii_redactions_by_field[field] = self.pii_redactions_by_field.get(field, 0) + 1

    def get_summary(self) -> Dict:
        if not self.latencies:
            return {"requests": self.requests}
        return {
            "requests": self.requests,
            "latency_ms": {"mean": sum(self.latencies) / len(self.latencies)},
            "cost_cents": {"total": sum(self.costs)},
            "traces_stripped": self.traces_stripped_count,
            "break_glass_activations": self.break_glass_count,
            "pii_redactions": self.pii_redactions_by_field,
        }


def get_metrics(metrics_type: str = "noop") -> AbstractMetrics:
    if metrics_type == "noop":
        return NoOpMetrics()
    elif metrics_type == "prometheus":
        return PrometheusMetrics()
    elif metrics_type == "memory":
        return InMemoryMetrics()
    else:
        raise ValueError(f"Unknown metrics type: {metrics_type}")

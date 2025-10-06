"""Trace filtering and PII redaction"""

from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class TraceFilter:
    """Filters traces from agent results based on policy"""

    TRACE_KEYS = [
        "traces",
        "trace",
        "steps",
        "thoughts",
        "reasoning",
        "tool_calls",
        "tool_logs",
        "internal_state",
        "context",
        "intermediate_results",
        "debug_info",
        "execution_log",
    ]

    def __init__(self, policy):
        self.policy = policy

    def filter(self, data: Dict) -> Dict:
        if not self.policy.black_box:
            return data

        filtered = data.copy()
        for key in self.TRACE_KEYS:
            if key in filtered:
                del filtered[key]
                logger.debug(f"Stripped trace key: {key}")
        return filtered


class PIIRedactor:
    """Redacts PII from data"""

    REDACTED_VALUE = "***REDACTED***"

    def __init__(self, policy):
        self.policy = policy
        self.pii_fields_lower = [f.lower() for f in policy.pii_fields]

    def redact(self, data: Any) -> Any:
        if isinstance(data, dict):
            return self._redact_dict(data)
        elif isinstance(data, list):
            return [self.redact(item) for item in data]
        else:
            return data

    def _redact_dict(self, data: Dict) -> Dict:
        redacted = {}
        for key, value in data.items():
            if self._is_pii_field(key):
                redacted[key] = self.REDACTED_VALUE
                logger.debug(f"Redacted PII field: {key}")
            else:
                redacted[key] = self.redact(value)
        return redacted

    def _is_pii_field(self, field_name: str) -> bool:
        field_lower = field_name.lower()
        if field_lower in self.pii_fields_lower:
            return True
        for pii_field in self.pii_fields_lower:
            if pii_field in field_lower:
                return True
        return False

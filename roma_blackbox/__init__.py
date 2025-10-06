"""
roma-blackbox: Privacy-first monitoring for ROMA agents
"""

__version__ = "0.1.0"

from .wrapper import BlackBoxWrapper, BlackBoxResult
from .policy import Policy, STRICT_PRIVACY, DEVELOPMENT, PRODUCTION
from .storage import AbstractStorage, MemoryStorage, PostgreSQLStorage, JSONFileStorage
from .metrics import AbstractMetrics, PrometheusMetrics, InMemoryMetrics
from .filters import PIIRedactor, TraceFilter
from .attestation import AttestationGenerator

__all__ = [
    "BlackBoxWrapper",
    "BlackBoxResult",
    "Policy",
    "STRICT_PRIVACY",
    "DEVELOPMENT",
    "PRODUCTION",
    "AbstractStorage",
    "MemoryStorage",
    "PostgreSQLStorage",
    "JSONFileStorage",
    "AbstractMetrics",
    "PrometheusMetrics",
    "InMemoryMetrics",
    "PIIRedactor",
    "TraceFilter",
    "AttestationGenerator",
]

# Optional integrations
try:
    from . import integrations
except ImportError:
    integrations = None

# Enhanced PII detection
from .pii_patterns import EnhancedPIIRedactor, PIIPattern, redact_pii

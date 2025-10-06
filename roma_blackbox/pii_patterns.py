"""Enhanced PII detection patterns"""

import re
from typing import Dict, Any, List, Tuple


class PIIPattern:
    """Definition of a PII pattern with regex and replacement strategy"""

    def __init__(self, name: str, pattern: str, replacement: str = "[REDACTED]"):
        self.name = name
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.replacement = replacement


class EnhancedPIIRedactor:
    """Advanced PII redaction with support for multiple sensitive data types"""

    # Define patterns for various PII types
    PATTERNS = [
        # Email addresses
        PIIPattern("email", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]"),
        # US Social Security Numbers (SSN)
        PIIPattern("ssn", r"\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b", "[SSN]"),
        # Credit card numbers (major issuers)
        PIIPattern("credit_card", r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "[CREDIT_CARD]"),
        # Phone numbers (US format)
        PIIPattern(
            "phone",
            r"\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b",
            "[PHONE]",
        ),
        # IP addresses (IPv4)
        PIIPattern("ip_address", r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[IP_ADDRESS]"),
        # API keys and tokens (common patterns)
        PIIPattern(
            "api_key",
            r'\b(?:api[_-]?key|apikey|access[_-]?token|secret[_-]?key)["\s:=]+([A-Za-z0-9_\-]{20,})\b',
            "[API_KEY]",
        ),
        # AWS Access Keys
        PIIPattern("aws_key", r"\b(AKIA[0-9A-Z]{16})\b", "[AWS_KEY]"),
        # GitHub tokens (fixed pattern - 36+ chars after prefix)
        PIIPattern(
            "github_token",
            r"\b(ghp_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{82})\b",
            "[GITHUB_TOKEN]",
        ),
        # Generic secrets (Bearer tokens, etc)
        PIIPattern("bearer_token", r"\bBearer\s+([A-Za-z0-9\-._~+/]+=*)\b", "Bearer [TOKEN]"),
        # Cryptocurrency addresses (Bitcoin)
        PIIPattern("btc_address", r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b", "[BTC_ADDRESS]"),
        # Ethereum addresses (fixed - needs 0x prefix + 40 hex chars)
        PIIPattern("eth_address", r"\b0x[a-fA-F0-9]{40}\b", "[ETH_ADDRESS]"),
        # US Passport numbers
        PIIPattern("passport", r"\b[A-Z]{1,2}\d{6,9}\b", "[PASSPORT]"),
        # Driver's license (varies by state, this is a general pattern)
        PIIPattern("drivers_license", r"\b[A-Z]{1,2}\d{5,8}\b", "[DRIVERS_LICENSE]"),
    ]

    def __init__(self, custom_patterns: List[PIIPattern] = None):
        """Initialize with default patterns plus any custom ones"""
        self.patterns = self.PATTERNS.copy()
        if custom_patterns:
            self.patterns.extend(custom_patterns)

    def redact(self, data: Any) -> Any:
        """Recursively redact PII from data structures"""
        if isinstance(data, str):
            return self._redact_string(data)
        elif isinstance(data, dict):
            return {k: self.redact(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.redact(item) for item in data]
        elif isinstance(data, tuple):
            return tuple(self.redact(item) for item in data)
        return data

    def _redact_string(self, text: str) -> str:
        """Apply all PII patterns to a string"""
        result = text
        for pattern in self.patterns:
            result = pattern.pattern.sub(pattern.replacement, result)
        return result

    def scan(self, data: Any) -> Dict[str, List[str]]:
        """Scan data and return what PII types were found (without exposing values)"""
        findings = {}

        def scan_value(value: Any):
            if isinstance(value, str):
                for pattern in self.patterns:
                    matches = pattern.pattern.findall(value)
                    if matches:
                        if pattern.name not in findings:
                            findings[pattern.name] = []
                        findings[pattern.name].append(f"Found {len(matches)} instance(s)")
            elif isinstance(value, dict):
                for v in value.values():
                    scan_value(v)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    scan_value(item)

        scan_value(data)
        return findings


# Convenience function for quick redaction
def redact_pii(data: Any, custom_patterns: List[PIIPattern] = None) -> Any:
    """Quick function to redact PII from any data structure"""
    redactor = EnhancedPIIRedactor(custom_patterns)
    return redactor.redact(data)

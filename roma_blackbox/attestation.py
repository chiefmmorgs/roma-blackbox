"""Attestation generation for audit trails"""

import hashlib
import json
from datetime import datetime, UTC
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class AttestationGenerator:
    """Generates cryptographic attestations for agent executions"""

    def __init__(self, policy, code_sha: str):
        self.policy = policy
        self.code_sha = code_sha
        self._policy_hash = self._compute_policy_hash()

    def generate(
        self, request_id: str, input_hash: Optional[str] = None, output_hash: Optional[str] = None
    ) -> Dict:
        attestation = {
            "request_id": request_id,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        if self.policy.include_code_sha:
            attestation["code_sha"] = self.code_sha

        if self.policy.include_policy_hash:
            attestation["policy_hash"] = self._policy_hash

        attestation["policy_mode"] = "black_box" if self.policy.black_box else "full_trace"

        if input_hash:
            attestation["input_hash"] = input_hash
        if output_hash:
            attestation["output_hash"] = output_hash

        if self.policy.sign_attestations:
            attestation["signature"] = self._sign_attestation(attestation)

        return attestation

    def _compute_policy_hash(self) -> str:
        policy_str = json.dumps(self.policy.to_dict(), sort_keys=True)
        full_hash = hashlib.sha256(policy_str.encode()).hexdigest()
        return full_hash[:16]

    def _sign_attestation(self, attestation: Dict) -> str:
        return "UNSIGNED"  # Placeholder for signature implementation

"""Black-box wrapper for agent monitoring"""

import hashlib
import time
from typing import Any, Dict, Optional
from datetime import datetime, UTC
from dataclasses import dataclass

from .policy import Policy
from .filters import PIIRedactor, TraceFilter
from .pii_patterns import EnhancedPIIRedactor
from .storage import MemoryStorage, PostgreSQLStorage
from .metrics import InMemoryMetrics
from .attestation import AttestationGenerator

import logging

logger = logging.getLogger(__name__)


@dataclass
class BlackBoxResult:
    request_id: str
    status: str
    result: Any
    traces: Optional[list]
    latency_ms: int
    cost_cents: float
    input_hash: Optional[str]
    output_hash: Optional[str]
    attestation: Optional[Dict]


class BlackBoxWrapper:
    """Wraps an agent with privacy-preserving black-box monitoring"""

    def __init__(
        self,
        agent: Any,
        policy: Policy,
        storage: str = "memory",
        metrics: Optional[Any] = None,
        use_enhanced_pii: bool = True,
    ):
        self.agent = agent
        self.policy = policy
        self.use_enhanced_pii = use_enhanced_pii

        # Choose PII redactor based on flag
        if use_enhanced_pii:
            self.pii_redactor = EnhancedPIIRedactor()
        else:
            self.pii_redactor = PIIRedactor(policy)

        self.trace_filter = TraceFilter(policy)
        self.metrics = metrics or InMemoryMetrics()

        # Handle storage as string or object
        if isinstance(storage, str):
            if storage == "memory":
                self.storage = MemoryStorage()
            elif storage == "postgres":
                self.storage = PostgreSQLStorage()
            else:
                raise ValueError(f"Unknown storage backend: {storage}")
        else:
            # Storage is already an object
            self.storage = storage

        self.attestation_gen = AttestationGenerator(
            policy=policy,
            code_sha="fake_sha_for_demo",
        )

    async def run(
        self, request_id: str, task: str, payload: Optional[Dict[str, Any]] = None, **kwargs
    ) -> BlackBoxResult:
        start_time = time.time()
        payload = payload or {}
        is_break_glass = request_id in self.policy.break_glass_request_ids

        if is_break_glass:
            logger.info(f"🔓 Break-glass enabled for {request_id}")
            self.metrics.record_break_glass()

        try:
            redacted_input = self.pii_redactor.redact({"task": task, "payload": payload})
            input_hash = self._compute_hash(redacted_input) if self.policy.keep_hashes else None

            if hasattr(self.agent, "run"):
                try:
                    agent_result = await self.agent.run(task, **payload, **kwargs)
                except TypeError:
                    agent_result = await self.agent.run(task)
            else:
                raise AttributeError(f"Agent {type(self.agent)} has no run() method")

            result, traces, cost_cents = self._parse_agent_result(agent_result)

            if self.policy.black_box and not is_break_glass:
                traces = None
                self.metrics.record_trace_strip()

            output_hash = self._compute_hash(result) if self.policy.keep_hashes else None

            latency_ms = int((time.time() - start_time) * 1000)

            # Redact PII from result if enabled
            if self.use_enhanced_pii:
                result = self.pii_redactor.redact(result)

            await self.storage.store_outcome(
                {
                    "request_id": request_id,
                    "status": "success",
                    "input_hash": input_hash,
                    "output_hash": output_hash,
                    "latency_ms": latency_ms,
                    "cost_cents": cost_cents,
                    "created_at": datetime.now(UTC).isoformat(),
                }
            )

            self.metrics.record_request("success", latency_ms, cost_cents)

            attestation = None
            if self.policy.include_code_sha or self.policy.include_policy_hash:
                attestation = self.attestation_gen.generate(
                    request_id=request_id,
                    input_hash=input_hash,
                    output_hash=output_hash,
                )
                if is_break_glass:
                    attestation["break_glass"] = {
                        "enabled": True,
                        "reason": "Request ID in break_glass_request_ids",
                        "timestamp": datetime.now(UTC).isoformat(),
                    }

            return BlackBoxResult(
                request_id,
                "success",
                result,
                traces,
                latency_ms,
                cost_cents,
                input_hash,
                output_hash,
                attestation,
            )

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Agent execution failed: {e}")
            await self.storage.store_outcome(
                {
                    "request_id": request_id,
                    "status": "error",
                    "error": str(e),
                    "latency_ms": latency_ms,
                    "created_at": datetime.now(UTC).isoformat(),
                }
            )
            self.metrics.record_request("error", latency_ms, 0)

            return BlackBoxResult(
                request_id,
                "error",
                {"error": str(e)},
                None,
                latency_ms,
                0,
                None,
                None,
                {"error": str(e)},
            )

    def _parse_agent_result(self, agent_result: Any) -> tuple:
        if isinstance(agent_result, dict):
            result = agent_result.get("result", agent_result)
            traces = agent_result.get("traces")
            cost = agent_result.get("cost_cents", 0.0)
            return result, traces, cost
        return agent_result, None, 0.0

    def _compute_hash(self, data: Any) -> str:
        serialized = str(data).encode()
        return hashlib.sha256(serialized).hexdigest()

    async def get_outcome(self, request_id: str):
        """Retrieve stored outcome by request_id"""
        return await self.storage.get_outcome(request_id)

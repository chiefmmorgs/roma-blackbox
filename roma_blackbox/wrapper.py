"""BlackBoxWrapper - Main wrapper for ROMA agents"""

import time
import hashlib
import json
import logging
from typing import Any, Dict, Optional, Union
from datetime import datetime, UTC

from .policy import Policy
from .filters import TraceFilter, PIIRedactor
from .storage import get_storage, AbstractStorage
from .metrics import AbstractMetrics, get_metrics
from .attestation import AttestationGenerator

logger = logging.getLogger(__name__)


class BlackBoxResult:
    """Result from a black-box wrapped agent execution"""

    def __init__(
        self,
        request_id: str,
        status: str,
        result: Any,
        traces: Optional[Dict] = None,
        latency_ms: int = 0,
        cost_cents: float = 0.0,
        input_hash: Optional[str] = None,
        output_hash: Optional[str] = None,
        attestation: Optional[Dict] = None,
    ):
        self.request_id = request_id
        self.status = status
        self.result = result
        self.traces = traces
        self.latency_ms = latency_ms
        self.cost_cents = cost_cents
        self.input_hash = input_hash
        self.output_hash = output_hash
        self.attestation = attestation

    def to_dict(self) -> Dict:
        return {
            "request_id": self.request_id,
            "status": self.status,
            "result": self.result,
            "traces": self.traces,
            "latency_ms": self.latency_ms,
            "cost_cents": self.cost_cents,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "attestation": self.attestation,
        }


class BlackBoxWrapper:
    """Wraps any ROMA agent to add black-box monitoring"""

    def __init__(
        self,
        agent: Any,
        policy: Policy,
        storage: Union[str, AbstractStorage] = "memory",
        metrics: Optional[AbstractMetrics] = None,
        code_sha: Optional[str] = None,
    ):
        self.agent = agent
        self.policy = policy
        self.storage = get_storage(storage) if isinstance(storage, str) else storage
        self.metrics = metrics or get_metrics("noop")
        self.code_sha = code_sha or "unknown"

        self.trace_filter = TraceFilter(policy)
        self.pii_redactor = PIIRedactor(policy)
        self.attestation_gen = AttestationGenerator(policy, self.code_sha)

        logger.info(f"BlackBoxWrapper initialized (black_box={policy.black_box})")

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
            attestation = self.attestation_gen.generate(request_id, input_hash, output_hash)

            await self.storage.store_outcome(
                {
                    "request_id": request_id,
                    "input_hash": input_hash,
                    "output_hash": output_hash,
                    "status": "success",
                    "latency_ms": latency_ms,
                    "cost_cents": cost_cents,
                    "created_at": datetime.now(UTC).isoformat(),
                    "attestation": attestation,
                }
            )

            self.metrics.record_request("success", latency_ms, cost_cents)

            if is_break_glass:
                await self.storage.log_audit_event(
                    {
                        "request_id": request_id,
                        "action": "break_glass_enabled",
                        "reason": "Request ID in break_glass_request_ids",
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )

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
                    "latency_ms": latency_ms,
                    "cost_cents": 0,
                    "created_at": datetime.now(UTC).isoformat(),
                    "attestation": {"error": str(e)},
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
            cost = agent_result.get("cost", 0)
            if isinstance(cost, dict):
                cost = cost.get("total_cents", 0)
            return result, traces, float(cost)
        else:
            return agent_result, None, 0.0

    def _compute_hash(self, data: Any) -> str:
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    async def get_outcome(self, request_id: str) -> Optional[Dict]:
        return await self.storage.get_outcome(request_id)

    async def get_audit_log(self, request_id: str) -> list:
        return await self.storage.get_audit_log(request_id)

    def get_metrics_summary(self) -> Dict:
        return self.metrics.get_summary()

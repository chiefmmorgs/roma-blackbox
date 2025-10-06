"""Tests for roma-blackbox package"""

import asyncio
import pytest
from roma_blackbox import (
    BlackBoxWrapper,
    Policy,
    MemoryStorage,
    PIIRedactor,
    TraceFilter,
)


class MockAgent:
    """Mock agent for testing"""

    async def run(self, task: str, **kwargs):
        await asyncio.sleep(0.001)
        return {
            "result": {"output": f"Completed: {task}", "data": ["item1", "item2"]},
            "traces": {"planner": {"subtasks": ["step1", "step2"]}, "executor": {"executed": True}},
            "cost": 2.5,
        }


class TestBlackBoxWrapper:
    @pytest.mark.asyncio
    async def test_basic_execution(self):
        agent = MockAgent()
        policy = Policy(black_box=False)
        wrapper = BlackBoxWrapper(agent, policy, storage="memory")

        result = await wrapper.run(request_id="test_001", task="Test task")

        assert result.request_id == "test_001"
        assert result.status == "success"
        assert result.result is not None
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_black_box_strips_traces(self):
        agent = MockAgent()
        policy = Policy(black_box=True)
        wrapper = BlackBoxWrapper(agent, policy, storage="memory")

        result = await wrapper.run(request_id="test_002", task="Test task")

        assert result.status == "success"
        assert result.traces is None
        assert result.result is not None

    @pytest.mark.asyncio
    async def test_break_glass_shows_traces(self):
        agent = MockAgent()
        policy = Policy(black_box=True, break_glass_request_ids=["debug_001"])
        wrapper = BlackBoxWrapper(agent, policy, storage="memory")

        result1 = await wrapper.run(request_id="regular_001", task="Regular task")
        assert result1.traces is None

        result2 = await wrapper.run(request_id="debug_001", task="Debug task")
        assert result2.traces is not None

    @pytest.mark.asyncio
    async def test_input_output_hashing(self):
        agent = MockAgent()
        policy = Policy(black_box=True, keep_hashes=True)
        wrapper = BlackBoxWrapper(agent, policy, storage="memory")

        result = await wrapper.run(request_id="test_003", task="Test task")

        assert result.input_hash is not None
        assert result.output_hash is not None
        assert len(result.input_hash) == 64

    @pytest.mark.asyncio
    async def test_outcome_storage(self):
        agent = MockAgent()
        policy = Policy(black_box=True)
        storage = MemoryStorage()
        wrapper = BlackBoxWrapper(agent, policy, storage=storage)

        await wrapper.run(request_id="test_004", task="Test task")

        outcome = await wrapper.get_outcome("test_004")
        assert outcome is not None
        assert outcome["request_id"] == "test_004"
        assert outcome["status"] == "success"


class TestPIIRedactor:
    def test_redact_simple_pii(self):
        policy = Policy(pii_fields=["email", "wallet"])
        redactor = PIIRedactor(policy)

        data = {"email": "user@example.com", "wallet": "0x1234", "query": "balance"}
        redacted = redactor.redact(data)

        assert redacted["email"] == "***REDACTED***"
        assert redacted["wallet"] == "***REDACTED***"
        assert redacted["query"] == "balance"

    def test_redact_nested_pii(self):
        policy = Policy(pii_fields=["email"])
        redactor = PIIRedactor(policy)

        data = {"user": {"email": "user@example.com", "name": "John"}}
        redacted = redactor.redact(data)

        assert redacted["user"]["email"] == "***REDACTED***"
        assert redacted["user"]["name"] == "John"


class TestTraceFilter:
    def test_filter_removes_traces(self):
        policy = Policy(black_box=True)
        filter = TraceFilter(policy)

        data = {"result": "output", "traces": {"step1": "..."}, "thoughts": "reasoning"}
        filtered = filter.filter(data)

        assert "result" in filtered
        assert "traces" not in filtered
        assert "thoughts" not in filtered


class TestPolicy:
    def test_policy_defaults(self):
        policy = Policy()
        assert policy.black_box is True
        assert policy.keep_hashes is True
        assert "email" in policy.pii_fields

    def test_policy_validation(self):
        with pytest.raises(ValueError):
            Policy(max_cost_cents=-1)

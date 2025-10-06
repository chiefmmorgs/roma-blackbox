"""Basic usage example: Wrap a ROMA agent with black-box monitoring"""

import asyncio
from roma_blackbox import BlackBoxWrapper, Policy


class MockROMAAgent:
    """Mock ROMA agent. Replace with: from sentientresearchagent import SentientAgent"""

    async def run(self, task: str, **kwargs):
        return {
            "result": {"summary": f"Completed: {task}", "findings": ["Finding 1", "Finding 2"]},
            "traces": {
                "planner": {"subtasks": ["research", "analyze"]},
                "executor": {"steps": ["step1", "step2"]},
            },
            "cost": 2.5,
        }


async def main():
    print("=" * 60)
    print("ROMA Black-Box Wrapper - Basic Example")
    print("=" * 60)

    agent = MockROMAAgent()
    print("\n✓ ROMA agent created")

    policy = Policy(
        black_box=True, pii_fields=["email", "wallet", "ip"], break_glass_request_ids=["debug_001"]
    )
    print(f"✓ Policy defined (black_box={policy.black_box})")

    blackbox_agent = BlackBoxWrapper(
        agent=agent, policy=policy, storage="memory", code_sha="v1.0.0"
    )
    print("✓ Agent wrapped with black-box monitoring")

    print("\n" + "-" * 60)
    print("Example 1: Normal Request (Black-Box Mode)")
    print("-" * 60)

    result = await blackbox_agent.run(request_id="req_001", task="Research renewable energy trends")

    print(f"\nRequest ID: {result.request_id}")
    print(f"Status: {result.status}")
    print(f"Result: {result.result}")
    print(f"Traces: {result.traces}")
    print(f"Latency: {result.latency_ms}ms")
    print(f"Cost: ${result.cost_cents/100:.4f}")
    print(f"Input Hash: {result.input_hash[:16] if result.input_hash else 'None'}...")

    print("\n" + "-" * 60)
    print("Example 2: Request with PII (Auto-Redacted)")
    print("-" * 60)

    result_pii = await blackbox_agent.run(
        request_id="req_002",
        task="Check balance",
        payload={"email": "user@example.com", "wallet": "0x1234", "query": "balance"},
    )

    print(f"\nRequest ID: {result_pii.request_id}")
    print(f"Status: {result_pii.status}")
    print("PII redacted: email, wallet")

    print("\n" + "-" * 60)
    print("Example 3: Break-Glass Request (Full Traces)")
    print("-" * 60)

    result_debug = await blackbox_agent.run(request_id="debug_001", task="Debug issue")

    print(f"\nRequest ID: {result_debug.request_id}")
    print(f"Status: {result_debug.status}")
    print(f"Traces Available: {result_debug.traces is not None}")
    if result_debug.traces:
        print(f"Trace Keys: {list(result_debug.traces.keys())}")

    print("\n" + "-" * 60)
    print("Example 4: Retrieve Stored Outcome")
    print("-" * 60)

    stored = await blackbox_agent.get_outcome("req_001")
    print(f"\nStored outcome: {stored['status']}, {stored['latency_ms']}ms")

    metrics = blackbox_agent.get_metrics_summary()
    print(f"\nMetrics: {metrics}")

    print("\n" + "=" * 60)
    print("✓ All examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

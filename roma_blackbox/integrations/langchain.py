"""LangChain integration for roma-blackbox"""

from typing import Any, Dict, Optional, List
import asyncio
from roma_blackbox import BlackBoxWrapper, Policy


class LangChainWrapper:
    """Wraps LangChain agents/chains with black-box privacy controls.

    Intercepts LangChain execution to:
    - Strip intermediate reasoning steps
    - Redact PII from inputs/outputs
    - Filter tool calls and agent traces
    - Store only final outcomes

    Example:
        from langchain.agents import AgentExecutor
        from roma_blackbox.integrations import LangChainWrapper

        agent = AgentExecutor(...)
        wrapped = LangChainWrapper(agent, policy=Policy(black_box=True))
        result = wrapped.invoke({"input": "user query"})
    """

    def __init__(
        self,
        runnable: Any,
        policy: Optional[Policy] = None,
        storage: str = "memory",
        metrics: Optional[Any] = None,
    ):
        """Initialize LangChain wrapper.

        Args:
            runnable: LangChain Runnable (agent, chain, etc)
            policy: Privacy policy configuration
            storage: Storage backend for outcomes
            metrics: Metrics collector
        """
        self.runnable = runnable
        self.policy = policy or Policy(black_box=True)
        self.storage = storage
        self.metrics = metrics

        # Create mock agent for BlackBoxWrapper
        self._agent = MockLangChainAgent(runnable)
        self._wrapper = BlackBoxWrapper(
            self._agent,
            policy=self.policy,
            storage=storage,
            metrics=metrics,
        )

    def invoke(self, input: Dict[str, Any], config: Optional[Dict] = None, **kwargs) -> Any:
        """Execute with black-box privacy controls.

        Args:
            input: Input dict (e.g., {"input": "user query"})
            config: LangChain config
            **kwargs: Additional arguments

        Returns:
            Final output with traces stripped
        """
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # We're in a loop, so we need to create a task
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(
                    lambda: asyncio.run(self._run_async(input, config, **kwargs))
                ).result()
        except RuntimeError:
            # No event loop, safe to use asyncio.run()
            return asyncio.run(self._run_async(input, config, **kwargs))

    async def _run_async(self, input: Dict[str, Any], config: Optional[Dict] = None, **kwargs):
        """Internal async runner."""
        return await self._wrapper.run(
            request_id=input.get("request_id", "langchain_request"),
            task=str(input),
            input_data=input,
            config=config,
            **kwargs,
        )

    async def ainvoke(self, input: Dict[str, Any], config: Optional[Dict] = None, **kwargs) -> Any:
        """Async execution with privacy controls."""
        return await self._wrapper.run(
            request_id=input.get("request_id", "langchain_request"),
            task=str(input),
            input_data=input,
            config=config,
            **kwargs,
        )

    def batch(self, inputs: List[Dict[str, Any]], **kwargs) -> List[Any]:
        """Batch execution with privacy controls."""
        return [self.invoke(inp, **kwargs) for inp in inputs]

    def stream(self, input: Dict[str, Any], **kwargs):
        """Stream execution (returns final result only in black-box mode)."""
        # In black-box mode, we can't stream intermediate steps
        result = self.invoke(input, **kwargs)
        yield result


class MockLangChainAgent:
    """Internal adapter to make LangChain Runnable work with BlackBoxWrapper."""

    def __init__(self, runnable: Any):
        self.runnable = runnable

    async def run(self, task: str, input_data: Dict = None, config: Dict = None, **kwargs) -> Dict:
        """Execute LangChain runnable and capture traces."""
        try:
            # Execute the runnable
            result = self.runnable.invoke(input_data or {"input": task}, config=config)

            # Extract traces if present
            traces = []
            if isinstance(result, dict):
                if "intermediate_steps" in result:
                    # Convert intermediate_steps to string traces
                    steps = result.get("intermediate_steps", [])
                    for step in steps:
                        if isinstance(step, tuple) and len(step) == 2:
                            traces.append(f"{step[0]}: {step[1]}")
                        else:
                            traces.append(str(step))

            # Return structured result with traces (PLURAL - this is the fix!)
            return {
                "result": result,
                "traces": traces if traces else ["executed"],  # Changed from "trace" to "traces"
                "status": "success",
            }
        except Exception as e:
            return {
                "result": None,
                "traces": [f"Error: {str(e)}"],  # Changed from "trace" to "traces"
                "status": "error",
                "error": str(e),
            }

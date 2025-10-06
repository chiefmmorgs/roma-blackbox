"""Debug script to understand trace handling"""
import asyncio
from roma_blackbox import BlackBoxWrapper, Policy


class DebugAgent:
    async def run(self, task: str, **kwargs):
        return {
            "status": "success",
            "result": "test output",
            "trace": ["step1", "step2", "step3"],
        }


async def main():
    agent = DebugAgent()
    
    # Test with black_box=False
    wrapper = BlackBoxWrapper(agent, Policy(black_box=False), storage="memory")
    result = await wrapper.run(request_id="test", task="test task")
    
    print(f"black_box=False:")
    print(f"  result.status: {result.status}")
    print(f"  result.traces: {result.traces}")
    print(f"  result.result: {result.result}")
    print()
    
    # Test with black_box=True
    wrapper2 = BlackBoxWrapper(agent, Policy(black_box=True), storage="memory")
    result2 = await wrapper2.run(request_id="test2", task="test task")
    
    print(f"black_box=True:")
    print(f"  result.status: {result2.status}")
    print(f"  result.traces: {result2.traces}")
    print(f"  result.result: {result2.result}")


if __name__ == "__main__":
    asyncio.run(main())

"""Example: Using roma-blackbox with LangChain agents"""

from roma_blackbox import Policy
from roma_blackbox.integrations import LangChainWrapper


# Mock LangChain agent (in real use, this would be your actual LangChain agent)
class SimpleLangChainAgent:
    def invoke(self, input_dict, config=None):
        user_input = input_dict.get("input", "")
        return {
            "output": f"Response to: {user_input}",
            "intermediate_steps": [
                ("thought", "I need to process this"),
                ("action", "call_tool"),
                ("observation", "Got result"),
                ("thought", "Now I can respond"),
            ],
        }


def main():
    print("=== LangChain Integration Example ===\n")

    # Create a LangChain agent
    agent = SimpleLangChainAgent()

    # Wrap with black-box privacy
    wrapped_agent = LangChainWrapper(
        agent, policy=Policy(black_box=True, keep_hashes=True), storage="memory"
    )

    # Use it like normal LangChain
    print("1. Normal execution (traces hidden):")
    result = wrapped_agent.invoke({"input": "My email is user@example.com, book a flight"})
    print(f"Status: {result.status}")
    print(f"Has result: {result.result is not None}")
    print(f"Traces hidden: {result.traces is None or len(result.traces) == 0}")
    if result.input_hash:
        print(f"Input hash: {result.input_hash[:16]}...")
    print()

    # Non-black-box mode for debugging
    print("2. Non-black-box mode (traces visible):")
    wrapped_debug = LangChainWrapper(agent, policy=Policy(black_box=False), storage="memory")
    result = wrapped_debug.invoke(
        {
            "input": "Debug this request",
        }
    )
    print(f"Status: {result.status}")
    print(f"Traces visible: {result.traces is not None and len(result.traces) > 0}")
    if result.traces:
        print(f"Number of trace steps: {len(result.traces)}")


if __name__ == "__main__":
    main()

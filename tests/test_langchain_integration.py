"""Tests for LangChain integration"""

import pytest
from roma_blackbox import Policy
from roma_blackbox.integrations import LangChainWrapper


class MockLangChainRunnable:
    """Mock LangChain agent for testing"""

    def invoke(self, input_dict, config=None):
        return {
            "output": f"Processed: {input_dict.get('input', 'no input')}",
            "intermediate_steps": [
                ("thought", "I should search"),
                ("action", "search_tool"),
                ("observation", "Found results"),
            ],
        }


@pytest.mark.asyncio
async def test_langchain_wrapper_strips_traces():
    """Test that wrapper strips intermediate steps"""
    mock_agent = MockLangChainRunnable()

    # Wrap with black-box policy
    wrapped = LangChainWrapper(mock_agent, policy=Policy(black_box=True), storage="memory")

    # Use ainvoke for async tests
    result = await wrapped.ainvoke({"input": "test query"})

    # Should have result
    assert result.result is not None

    # Should NOT have traces in black-box mode
    assert result.traces is None or len(result.traces) == 0


@pytest.mark.asyncio
async def test_langchain_wrapper_preserves_result():
    """Test that actual result is preserved"""
    mock_agent = MockLangChainRunnable()

    wrapped = LangChainWrapper(mock_agent, storage="memory")
    result = await wrapped.ainvoke({"input": "test query"})

    # Result should contain the output
    assert result.result is not None
    assert result.status == "success"


@pytest.mark.asyncio
async def test_langchain_non_blackbox_preserves_traces():
    """Test non-black-box mode preserves traces"""
    mock_agent = MockLangChainRunnable()

    wrapped = LangChainWrapper(mock_agent, policy=Policy(black_box=False), storage="memory")

    result = await wrapped.ainvoke({"input": "test query"})

    # Non-black-box mode should preserve traces
    assert result.traces is not None
    assert len(result.traces) > 0

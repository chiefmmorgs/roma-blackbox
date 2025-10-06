Privacy-first monitoring for AI agent systems. Strip execution traces, redact PII, and maintain compliance while running multi-agent workflows.


roma-blackbox wraps your agents to:
- Hide internal execution traces (black-box mode)
- Redact PII from inputs/outputs (14 pattern types)
- Store only outcomes with cryptographic attestations
- Preserve results while protecting process

## Installation
```bash
pip install roma-blackbox
```
With optional features:
```bash
pip install roma-blackbox[langchain]  # LangChain integration
pip install roma-blackbox[all]        # Everything
```
Quick Start

Basic Usage
```python
from roma_blackbox import BlackBoxWrapper, Policy

# Your agent must have an async run() method
class MyAgent:
    async def run(self, task: str, **kwargs):
        return {
            "status": "success",
            "result": "some output",
            "traces": ["step1", "step2"]  # Will be stripped
        }

# Wrap it
wrapped = BlackBoxWrapper(
    MyAgent(),
    Policy(black_box=True),
    storage="memory"
)

# Use it
result = await wrapped.run(
    request_id="req_001",
    task="user query"
)

print(result.status)      # "success"
print(result.result)      # "some output"
print(result.traces)      # None (hidden in black-box mode)
```
With PII Redaction
```python
wrapped = BlackBoxWrapper(
    agent,
    Policy(black_box=True),
    storage="memory",
    use_enhanced_pii=True  # Enables PII redaction
)

result = await wrapped.run(
    request_id="req_002",
    task="Email user@example.com about order"
)

# result.result will have [EMAIL] instead of actual email
```
Integrating Your Agents

roma-blackbox doesn't automatically work with every agent. You need to write a thin adapter if your agents use different methods.

If Your Agent Uses .execute()
```python
import asyncio

class AgentAdapter:
    def __init__(self, your_agent):
        self.agent = your_agent
    
    async def run(self, task: str, **kwargs):
        # Convert sync to async
        result = await asyncio.to_thread(
            self.agent.execute, 
            **kwargs
        )
        
        return {
            "status": "success",
            "result": result,
            "traces": [f"Executed {self.agent.__class__.__name__}"]
        }

# Use it
adapter = AgentAdapter(your_agent)
wrapped = BlackBoxWrapper(adapter, Policy(black_box=True))
```
If Your Agent Is Async Already
```python
class AsyncAdapter:
    def __init__(self, your_agent):
        self.agent = your_agent
    
    async def run(self, task: str, **kwargs):
        result = await self.agent.your_method(**kwargs)
        return {"status": "success", "result": result}

wrapped = BlackBoxWrapper(AsyncAdapter(agent), Policy(black_box=True))
```
Multi-Agent Systems
```python
class OrchestratorAdapter:
    def __init__(self, planner, executor):
        self.planner = planner
        self.executor = executor
    
    async def run(self, task: str, **kwargs):
        plan = self.planner.plan(task)
        result = self.executor.execute(plan)
        
        return {
            "status": "success",
            "result": result,
            "traces": [
                f"Planned: {plan}",
                f"Executed: {result}"
            ]
        }
```
LangChain Integration
Built-in support for LangChain agents:
```python
from langchain.agents import create_openai_functions_agent
from roma_blackbox.integrations import LangChainWrapper

agent = create_openai_functions_agent(llm, tools, prompt)

wrapped = LangChainWrapper(
    agent,
    policy=Policy(black_box=True),
    storage="memory"
)

result = wrapped.invoke({"input": "book a flight to NYC"})
# Traces stripped, PII redacted, only outcome stored
```
Policy Configuration

```python
from roma_blackbox import Policy

policy = Policy(
    black_box=True,              # Hide traces
    keep_hashes=True,            # Store SHA256 hashes of I/O
    max_cost_cents=100.0,        # Cost limit per request
    request_timeout_seconds=300, # Timeout
    break_glass_request_ids=[],  # Override for debugging
)
```
PII Detection Patterns

Automatically redacts 14 types:

Email addresses → [EMAIL]

SSNs → [SSN]

Credit cards → [CREDIT_CARD]

Phone numbers → [PHONE]

IP addresses → [IP_ADDRESS]

API keys (AWS, GitHub, generic) → [API_KEY]

Crypto addresses (Bitcoin, Ethereum) → [BTC_ADDRESS]

And more...


**Custom Patterns**
```python
from roma_blackbox.pii_patterns import EnhancedPIIRedactor, PIIPattern

custom_pattern = PIIPattern(
    "employee_id",
    r'\bEMP-\d{6}\b',
    "[EMPLOYEE_ID]"
)

redactor = EnhancedPIIRedactor(custom_patterns=[custom_pattern])
```
Storage Backends
```python
# In-memory (default)
wrapped = BlackBoxWrapper(agent, policy, storage="memory")

# PostgreSQL
wrapped = BlackBoxWrapper(agent, policy, storage="postgres")
```
Examples
See examples/ directory:

basic_usage.py - Simple agent wrapping

langchain_example.py - LangChain integration

pii_detection_example.py - PII redaction demo

adapters/ - Adapter patterns for different agent types

Testing
```bash
pytest tests/ -v
```
Real-World Example
```python
# Your ROMA travel planning agent
class WeatherAgent:
    def execute(self, destination):
        # Makes API call to OpenWeatherMap
        return {"temp": 25, "condition": "sunny"}

# Adapt it
class WeatherAdapter:
    def __init__(self, agent):
        self.agent = agent
    
    async def run(self, task: str, destination=None):
        result = self.agent.execute(destination)
        return {
            "status": "success",
            "result": result,
            "traces": [f"API call to OpenWeatherMap for {destination}"]
        }

# Wrap it
wrapped = BlackBoxWrapper(
    WeatherAdapter(WeatherAgent()),
    Policy(black_box=True),
    storage="memory",
    use_enhanced_pii=True
)

# Use it
result = await wrapped.run(
    request_id="weather_001",
    task="Get weather",
    destination="Tokyo"
)
# Traces hidden, outcome stored, API keys protected
```
**Key Concepts**
Black-box mode: Agent execution details are hidden. Only inputs, outputs, and outcomes are preserved.

Break-glass: Override black-box mode for specific request IDs during debugging.

Attestations: Cryptographic proofs linking requests to code versions and policies.

Storage: Outcomes are stored (memory or PostgreSQL) for auditability without exposing traces.

W

FAQ

Q: Do I need to modify my existing agents?

A: Write a thin adapter (see examples above). 5-10 lines of code.

Q: Does it work with [framework X]?

A: If you can write an adapter that provides async run(), yes.

Q: What if my agent is synchronous?

A: Use asyncio.to_thread() in your adapter (see examples).

Q: Does it slow down my agents?

A: Adds ~10ms overhead for wrapping + storage. PII redaction adds ~1-5ms depending on data size.

Q: Can I disable PII redaction?

A: Yes: use_enhanced_pii=False in BlackBoxWrapper.

Contributing

Issues and PRs welcome at https://github.com/chiefmmorgs/roma-blackbox
